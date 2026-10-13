"""Regenerate the module-state tables (index.html) from pyfa + SDE, and diff
them against the copies embedded in index.html.

    PYFA_SRC=/path/to/Pyfa python3 -I tools/gen_module_state_tables.py [index.html]

Module-state plan, Phase 1 (roadmap/module-state-toggles-plan.md).
pyfa's rules (eos/saveddata/module.py, v2.69.2):
  * calculateModifiedAttributes(): an effect runs when its handler type is
    'offline' (always), 'passive' (module ONLINE or higher), 'active'
    (ACTIVE or higher) or 'overheat' (OVERHEATED). Charge effects follow the
    same rule using the module's state. Effects with no handler never run.
  * isValidState(): ACTIVE needs the item to have an 'active' handler and
    activationBlocked == 0.
  * canHaveState(): at most maxGroupActive (attr 763) modules of one group
    name ACTIVE, at most maxGroupOnline (attr 978) ONLINE.
  * getProposedState(): subsystems are always ONLINE.

Tables produced (LESSONS_LEARNED.md #1: handlers are RUN, not regex-read):
  EFFECT_STATE_TYPE        effectId -> 'a' active | 'o' offline | 'h' overheat
                           (only effects carried by modules/charges/subsystems;
                           anything not listed is 'passive' or has no handler)
  GROUP_LIMIT_MOD_EFFECTS  effectId -> [[limit, op, srcAttrId|0, skills|null, groups|null, carrier], ...]
                           limit 'active'|'online'; op 'increase'|'force';
                           srcAttrId 0 means "skill level" (skills are at V);
                           carrier 'ship'|'module'|'skill' (where the effect sits)
  ACTIVATION_BLOCK_EFFECTS effectId -> [[srcAttrId, skills|null, groups|null], ...]
"""
import sys, json, re, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pyfa_effects import *

attrId = {v['name']: int(k) for k, v in attrs.items()}
pub = [int(t) for t, v in types.items() if v.get('published')]
modules = [t for t in pub if cat(t) == 7]
car = carriers()

def kind(eid):
    e = EFFECTS.get(eid)
    if not e: return None
    t = getattr(e, 'type', None)
    t = t if isinstance(t, tuple) else (t,)
    if 'active' in t: return 'a'
    if 'offline' in t: return 'o'
    if 'overheat' in t: return 'h'
    return None   # passive, gang-only or no type

state_type = {}
for eid, ts in sorted(car.items()):
    if not ({cat(t) for t in ts} & {7, 8, 32}): continue
    k = kind(eid)
    if k: state_type[str(eid)] = k

CTX = {6: 'ship', 7: 'module', 32: 'module', 16: 'skill'}
LIMIT = {'maxGroupActive': 'active', 'maxGroupOnline': 'online'}
limits, blocks, errors = {}, {}, []
for eid, ts in sorted(car.items()):
    if eid not in EFFECTS: continue
    for c in sorted({cat(t) for t in ts} & set(CTX)):
        def evaluate(coll, meth, a):
            # Evaluated at call time (LESSONS_LEARNED.md #16).
            if coll != 'modules' or len(a) < 3: return None
            if str(a[1]) not in LIMIT and str(a[1]) != 'activationBlocked': return None
            return filter_hits(a[0], modules)
        calls, err = run(eid, CTX[c], evaluate)
        if err: errors.append((eid, err)); continue
        for coll, meth, a, kw in calls:
            if coll != 'modules' or len(a) < 3 or not callable(a[0]): continue
            tgt = str(a[1])
            if tgt not in LIMIT and tgt != 'activationBlocked': continue
            hits, rec = kw['_eval']
            if not hits: continue
            sk = sorted({skillId[x[1]] for x in rec if x[0] == 'skill'})
            gs = sorted({x[1] for x in rec if x[0] == 'eq'})
            calc = [t for t in modules if (not sk or any(s in reqs(t) for s in sk)) and (not gs or gname(t) in gs)]
            assert set(calc) == set(hits), f'effect {eid}: filter not expressible as skills/groups -- handle by hand'
            v = repr(a[2])
            if v == 'LVL': src = 0
            else:
                m = re.fullmatch(r"\(?a:(\w+)(\*1)?\)?", v)
                assert m, f'effect {eid}: unexpected value expression {v}'
                src = attrId[m.group(1)]
            if tgt == 'activationBlocked':
                assert meth == 'filteredItemIncrease', (eid, meth)
                row = [src, sk or None, gs or None]
                blocks.setdefault(str(eid), [])
                if row not in blocks[str(eid)]: blocks[str(eid)].append(row)
            else:
                op = {'filteredItemIncrease': 'increase', 'filteredItemForce': 'force'}[meth]
                row = [LIMIT[tgt], op, src, sk or None, gs or None, CTX[c]]
                limits.setdefault(str(eid), [])
                if row not in limits[str(eid)]: limits[str(eid)].append(row)

print(f'EFFECT_STATE_TYPE: {len(state_type)} effects '
      f'({sum(v == "a" for v in state_type.values())} active, {sum(v == "o" for v in state_type.values())} offline, '
      f'{sum(v == "h" for v in state_type.values())} overheat)')
print(f'GROUP_LIMIT_MOD_EFFECTS: {len(limits)} effects; ACTIVATION_BLOCK_EFFECTS: {len(blocks)} effects')
for eid, rows in limits.items(): print('  limit', eid, ename(int(eid)), kind(int(eid)) or 'passive', rows)
for eid, rows in blocks.items(): print('  block', eid, ename(int(eid)), kind(int(eid)) or 'passive', rows)

html = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', 'index.html')
src = open(html).read() if os.path.exists(html) else ''
gen = {'EFFECT_STATE_TYPE': state_type, 'GROUP_LIMIT_MOD_EFFECTS': limits, 'ACTIVATION_BLOCK_EFFECTS': blocks}
for nm, table in gen.items():
    m = re.search(r'const ' + nm + r' = (\{.*?\});', src, re.S)
    if not m:
        print(f'\n{nm} not in {html} yet. Generated:\nconst {nm} = {json.dumps(table, separators=(",", ":"))};')
        continue
    cur = json.loads(m.group(1))
    print(f'{nm}: ' + ('index.html matches pyfa + SDE' if cur == table else 'DIFFERS from pyfa + SDE:'))
    if cur != table:
        for k in sorted(set(cur) | set(table), key=int):
            if cur.get(k) != table.get(k): print('   ', k, 'index.html:', cur.get(k), ' generated:', table.get(k))
