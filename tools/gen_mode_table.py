"""Generate MODE_EFFECT_ROWS (index.html, PYFA CORE section 'modes', since v2026.10.14.6): every
effect of every ship MODE item (Tactical Destroyers and the Anhinga; pyfa Ship.__getModeItems),
run through pyfa's own handlers, with the value already resolved from the mode item's SDE
attributes.

    PYFA_SRC=/path/to/Pyfa python3 -I tools/gen_mode_table.py [index.html]          # diff
    PYFA_SRC=/path/to/Pyfa python3 -I tools/gen_mode_table.py [index.html] --write  # embed

MODE_EFFECT_ROWS {hullId: {modeKey: [[coll, attr, mult, penaltyGroup, skills, skillsOn, groups, groupsOn], ...]}}
  coll   'ship' (the ship's own attribute) | 'module' (a fitted module's) | 'charge' (its loaded charge's)
  attr   pyfa attribute name
  mult   the multiplier pyfa applies (1/x for the 'PostDiv' handlers, 1+x/100 for boosts)
  penaltyGroup  pyfa's stacking group when stackingPenalties=True, else null. Penalized mode rows
         are 'postDiv' (one is 'default': the Anhinga Tertiary MJD reactivation bonus, penalized
         because a mode isn't the 'ship' context), and no other carrier (hull, module, rig,
         skill, subsystem, charge) is penalized in the same group on the same attribute --
         asserted below, and no two rows of one mode in one group match the same item -- so the
         engine multiplies them in directly: alone in its group, a
         penalized modifier is unpenalized (pyfa: the first entry of a group gets exp(0) = 1).
  skills / skillsOn, groups / groupsOn: the module filter as (any skill) AND (any group), checked
         on 'item' (the module) or 'charge'; null = no filter. Asserted exact on every pairing.
Resonance rows also appear in RESIST_EFFECTS (the resist calculation reads the mode item there)
and are skipped here.
"""
import sys, os, re, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pyfa_effects import *

MODE_GROUP = 'Ship Modifiers'
DEFAULT = {v['name']: v.get('defaultValue', 0.0) for v in attrs.values()}
RES = {(lay + n if lay else n.lower()) + 'DamageResonance' for lay in ('shield', 'armor', '') for n in ('Em', 'Thermal', 'Kinetic', 'Explosive')}
def adict(t): return {aname(x['attributeID']): x['value'] for x in td.get(str(t), {}).get('dogmaAttributes', [])}
pub = [int(t) for t, v in types.items() if v.get('published')]
def sig(t): return (frozenset(reqs(t)), gname(t))
def reps(pool): return list({sig(t): t for t in pool}.values())
moduleReps = reps([t for t in pub if cat(t) == 7])
chargeReps = reps([t for t in pub if cat(t) == 8])
launcherReps = reps([t for t in pub if cat(t) == 7 and gname(t).startswith('Missile Launcher')])
pairs = [(c, w) for c in chargeReps for w in launcherReps]

def fit_filter(isCharge, lam):
    REC.clear(); hits = []
    pool = pairs if isCharge else [(None, w) for w in moduleReps]
    for c, w in pool:
        p = Probe(w, c)
        try:
            if lam(p): hits.append((c, w))
        except Exception: pass
    rec = sorted(set(REC))
    if any(x[0] == 'skill?' for x in rec): raise AssertionError('filter tests the carrying skill')
    sk = sorted({skillId[x[1]] for x in rec if x[0] == 'skill' and x[1] in skillId}); gs = sorted({x[1] for x in rec if x[0] == 'eq'})
    for sOn in (('charge', 'item') if isCharge else ('item',)):
        for gOn in (('item', 'charge') if isCharge else ('item',)):
            calc = [(c, w) for c, w in pool
                    if (not sk or any(s in reqs(c if sOn == 'charge' else w) for s in sk))
                    and (not gs or gname(c if gOn == 'charge' else w) in gs)]
            if set(calc) == set(hits): return sk or None, sOn, gs or None, gOn
    raise AssertionError(f'filter not expressible as skills AND groups ({sk}, {gs})')

def parse(expr):
    r = repr(expr)
    m = re.fullmatch(r"\(1/a:(\w+)\)", r)
    if m: return 'div', m.group(1)
    m = re.fullmatch(r"\(?a:(\w+)(\*1)?\)?", r)
    if m: return 'val', m.group(1)
    raise AssertionError(f'unexpected value expression {r}')

# Every carrier pyfa runs besides modes, to check nothing else shares a mode's 'postDiv' group.
otherPostDiv = set()
for eid, ts in carriers().items():
    if eid not in EFFECTS or all(gname(t) == MODE_GROUP for t in ts): continue
    c = cat(next(iter(ts)))
    calls, err = run(eid, {6: 'ship', 16: 'skill', 8: 'charge'}.get(c, 'module'))
    for coll, meth, a, kw in calls or []:
        if kw.get('stackingPenalties') is True:
            otherPostDiv.add((str(a[0]) if coll in ('ship', 'self') else str(a[1]), str(kw.get('penaltyGroup', 'default'))))

table, skipped = {}, collections.Counter()
for t, v in sorted(types.items(), key=lambda kv: int(kv[0])):
    if groups[str(v['groupID'])]['categoryID'] != 6: continue
    hn = name(int(t))
    if gname(int(t)) != 'Tactical Destroyer' and hn != 'Anhinga': continue
    ms = sorted(int(m) for m, mv in types.items() if gname(int(m)) == MODE_GROUP and name(int(m)).lower().startswith(hn.lower()))
    if not ms: continue
    for m in ms:
        key = name(m)[len(hn):].strip().lower().replace(' mode', '').strip()
        A = adict(m); rows = []
        for e in [x['effectID'] for x in td.get(str(m), {}).get('dogmaEffects', [])]:
            if e not in EFFECTS: skipped[f'not implemented in pyfa: {ename(e)}'] += 1; continue
            evals = {}
            def ev(coll, meth, a):
                return fit_filter('Charge' in meth, a[0]) if coll == 'modules' and a and callable(a[0]) else None
            calls, err = run(e, 'module', ev)
            if err: raise AssertionError(f'mode effect {e}: {err}')
            for coll, meth, a, kw in calls:
                if coll == 'ship':
                    attr, expr, filt = str(a[0]), a[1], (None, 'item', None, 'item')
                    if attr in RES: continue   # RESIST_EFFECTS
                    out = 'ship'
                elif coll == 'modules':
                    attr, expr, filt = str(a[1]), a[2], kw['_eval']
                    out = 'charge' if 'Charge' in meth else 'module'
                else: raise AssertionError(f'mode effect {e}: {coll}.{meth}')
                how, src = parse(expr)
                val = A.get(src, DEFAULT.get(src, 0.0))
                op = meth.replace('filtered', '').replace('Item', '').replace('Charge', '').replace('Attr', '')
                if op in ('multiply', 'Multiply'): mult = 1 / val if how == 'div' else val
                elif op in ('boost', 'Boost') and how == 'val': mult = 1 + val / 100
                else: raise AssertionError(f'mode effect {e}: {meth} {expr!r}')
                pg = str(kw.get('penaltyGroup', 'default')) if kw.get('stackingPenalties') is True else None
                if pg and (attr, pg) in otherPostDiv: raise AssertionError(f'mode effect {e}: another carrier also uses penalty group {pg} on {attr} -- pool them')
                rows.append([out, attr, mult, pg, *filt])
        # Two penalized rows of the SAME mode on the same attribute and group would stack-penalize
        # each other on an item both match: assert no published module/charge matches two of them.
        def hits(r):
            sk, sOn, gs, gOn = r[4:]
            pool = [x for x in pub if cat(x) == (8 if r[0] == 'charge' else 7)]
            return {x for x in pool if (not sk or any(q in reqs(x) for q in sk)) and (not gs or gname(x) in gs)}
        for i, a in enumerate(rows):
            for b in rows[i + 1:]:
                if a[3] and a[:2] == b[:2] and a[3] == b[3] and a[0] != 'ship' and hits(a) & hits(b):
                    raise AssertionError(f'{name(m)}: two penalized {a[1]} rows match the same item -- pool them')
                if a[3] and a[:2] == b[:2] and a[3] == b[3] and a[0] == 'ship':
                    raise AssertionError(f'{name(m)}: two penalized ship {a[1]} rows -- pool them')
        table.setdefault(t, {})[key] = rows

print(f'MODE_EFFECT_ROWS: {len(table)} hulls, {sum(len(r) for h in table.values() for r in h.values())} rows')
for h, modes in table.items():
    print(f'  {name(int(h))}: ' + '; '.join(f'{k} {len(r)}' for k, r in modes.items()))
for k, v in sorted(skipped.items()): print('  skipped:', k)

html = next((x for x in sys.argv[1:] if not x.startswith('--')), os.path.join(os.path.dirname(__file__), '..', 'index.html'))
src = open(html).read()
pat = re.compile(r'(const MODE_EFFECT_ROWS = )(\{.*?\});\n', re.S)
m = pat.search(src)
blob = json.dumps(table, separators=(',', ':'))
if '--write' in sys.argv:
    if not m: sys.exit('MODE_EFFECT_ROWS not found in ' + html)
    open(html, 'w').write(src[:m.start(2)] + blob + src[m.end(2):]); print('wrote MODE_EFFECT_ROWS into', html)
elif m:
    print('index.html table is up to date with this pyfa/SDE.' if json.loads(m.group(2)) == table else 'MODE_EFFECT_ROWS vs index.html: DIFFERENT')
else: print('MODE_EFFECT_ROWS not in index.html yet')
