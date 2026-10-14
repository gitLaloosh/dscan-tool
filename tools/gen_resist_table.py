"""Generate the resistance tables (index.html, PYFA CORE section 'resist-calc', since v2026.10.14.5)
from pyfa + SDE, the same way gen_hull_damage_table.py does firepower.

    PYFA_SRC=/path/to/Pyfa python3 -I tools/gen_resist_table.py [index.html]          # diff
    PYFA_SRC=/path/to/Pyfa python3 -I tools/gen_resist_table.py [index.html] --write  # embed

Tables written (JSON blobs between `const NAME = ` and `;`):
  RESIST_EFFECTS {effectId: [[target, attrId, op, srcAttrId, perLevel, default, penaltyGroup], ...]}
    every hull / module / charge / subsystem / Tactical Destroyer mode handler that changes a
    ship resonance (target 'ship'), or a resistance attribute on the module itself
    (target 'self': Assault Damage Control forces; target 'charge': a loaded script boosts its
    module, src read from the CHARGE).
    op: 'boost' x(1+v/100) | 'mul' x v | 'div' x 1/v | 'force' (pyfa forceItemAttr)
    perLevel: 5 when pyfa passes skill= (the All 5 character); penaltyGroup: pyfa's stacking
    group when stackingPenalties=True ('default', 'preMul', 'postMul', 'postDiv'), else null.
  RESIST_SKILL_MODULE_ROWS [[attrId, op, value, groups, skills], ...]
    skill handlers that change a FITTED MODULE's resistance attributes (Compensation skills),
    value already at level V, filter = (groups) AND (skills) on the module (asserted exact).
  RESIST_ATTRS {shield|armor|hull: {em, therm, kin, exp: [resonanceAttrId, maxAttrId]}}
  MODE_ITEMS {hullId: {modeKey: [modeTypeId, [effectIds], {attrId: value}]}} for every hull with
    modes (pyfa Ship.__getModeItems: Tactical Destroyers + Anhinga); the engine reads the selected
    mode's effects through RESIST_EFFECTS.
Skipped and reported: the Reactive Armor Hardener (4928; ported separately, runs late), overheat
effects (not modelled), effect beacons, implants/boosters, fighters, drones.
"""
import sys, os, re, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pyfa_effects import *

attrId = {v['name']: int(k) for k, v in attrs.items()}
DEFAULT = {v['name']: v.get('defaultValue', 0.0) for v in attrs.values()}
DMG = (('em', 'Em'), ('therm', 'Thermal'), ('kin', 'Kinetic'), ('exp', 'Explosive'))
RESONANCE = {}
for lay, pre in (('shield', 'shield'), ('armor', 'armor'), ('hull', '')):
    for d, n in DMG:
        RESONANCE[(pre + n) if pre else n.lower()] = None
RES_NAMES = {(n + 'DamageResonance') for n in RESONANCE}
BONUS_NAMES = {f'{x}DamageResistanceBonus' for x in ('em', 'thermal', 'kinetic', 'explosive')}
MODULE_RES_NAMES = RES_NAMES | {f'hull{n}DamageResonance' for _, n in DMG}   # DC / Bastion / ADC carry hull* copies
WATCH_SELF = MODULE_RES_NAMES | BONUS_NAMES
RAH_EFFECT = 4928

def resattr(lay, n): return (lay + n if lay != 'hull' else n.lower()) + 'DamageResonance'
RESIST_ATTRS = {}
for lay in ('shield', 'armor', 'hull'):
    RESIST_ATTRS[lay] = {}
    for d, n in DMG:
        a = resattr(lay, n); info = attrs[str(attrId[a])]
        RESIST_ATTRS[lay][d] = [attrId[a], info.get('maxAttributeID')]

def adict(t): return {aname(x['attributeID']): x['value'] for x in td.get(str(t), {}).get('dogmaAttributes', [])}
pub = [int(t) for t, v in types.items() if v.get('published')]
modules = [t for t in pub if cat(t) == 7]
def sig(t): return (frozenset(reqs(t)), gname(t))
moduleReps = list({sig(t): t for t in modules}.values())

def parse_value(expr):
    """'a:X' -> ('', X); '(1/a:X)' -> ('div', X); '(a:X*LVL)' -> ('lvl', X)."""
    r = repr(expr)
    m = re.fullmatch(r"\(?a:(\w+)(\*1)?\)?", r)
    if m: return '', m.group(1)
    m = re.fullmatch(r"\(1/a:(\w+)\)", r)
    if m: return 'div', m.group(1)
    m = re.fullmatch(r"\(a:(\w+)\*LVL\)", r)
    if m: return 'lvl', m.group(1)
    raise AssertionError(f'unexpected value expression {r}')

OPS = {'boostItemAttr': 'boost', 'multiplyItemAttr': 'mul', 'forceItemAttr': 'force'}
def penalty(kw):
    return str(kw.get('penaltyGroup', 'default')) if kw.get('stackingPenalties') is True else None

carriersByEff = collections.defaultdict(set)
for t, v in td.items():
    for e in v.get('dogmaEffects', []): carriersByEff[e['effectID']].add(int(t))
MODE_GROUP = 'Ship Modifiers'
CTX = {6: 'ship', 7: 'module', 32: 'module', 8: 'charge', 16: 'skill'}
table, skillRows, skipped, errors = {}, [], collections.Counter(), []
for eid in sorted(carriersByEff):
    if eid not in EFFECTS: continue
    cats = {cat(t) for t in carriersByEff[eid] if str(t) in types}
    isMode = any(gname(t) == MODE_GROUP for t in carriersByEff[eid] if str(t) in types)
    for c in sorted(cats):
        ctx = 'module' if isMode else CTX.get(c)
        calls, err = run(eid, ctx or 'module')
        if err: errors.append((eid, err)); continue
        for coll, meth, a, kw in calls:
            if coll in ('ship', 'self'):
                if not a or str(a[0]) not in (RES_NAMES if coll == 'ship' else WATCH_SELF): continue
                tgt, expr = str(a[0]), a[1]
            elif coll == 'modules' and meth.startswith('filteredItem') and len(a) > 2 and str(a[1]) in WATCH_SELF:
                tgt, expr = str(a[1]), a[2]
            else: continue
            if eid == RAH_EFFECT: skipped['Reactive Armor Hardener 4928 (ported separately: pyfaRahAverage)'] += 1; continue
            if 'overheat' in (getattr(EFFECTS[eid], 'type', ()) if isinstance(getattr(EFFECTS[eid], 'type', ()), tuple) else (getattr(EFFECTS[eid], 'type', None),)):
                skipped[f'overheat effect, not modelled: {ename(eid)}'] += 1; continue
            if not (isMode or c in (6, 7, 8, 16, 32)):
                skipped[f'carrier category {c} not modelled: {ename(eid)}'] += 1; continue
            how, src = parse_value(expr)
            if coll == 'modules':
                if c != 16: raise AssertionError(f'effect {eid}: non-skill handler changes a module resistance attribute -- model it')
                if how != 'lvl': raise AssertionError(f'skill effect {eid}: value {expr!r}')
                op = {'filteredItemBoost': 'boost', 'filteredItemMultiply': 'mul'}[meth]
                hits, rec = filter_hits(a[0], moduleReps)
                sk = sorted({skillId[x[1]] for x in rec if x[0] == 'skill' and x[1] in skillId}); gs = sorted({x[1] for x in rec if x[0] == 'eq'})
                calc = [t for t in moduleReps if (not sk or any(s in reqs(t) for s in sk)) and (not gs or gname(t) in gs)]
                if set(calc) != set(hits): raise AssertionError(f'skill effect {eid}: filter not expressible ({sk}, {gs})')
                carrier = sorted(t for t in carriersByEff[eid] if cat(t) == 16)
                for t in carrier:
                    v = adict(t).get(src, DEFAULT.get(src, 0.0)) * 5
                    row = [attrId[tgt], op, v, gs or None, sk or None]
                    if row not in skillRows: skillRows.append(row)
                continue
            op = OPS[meth]
            if how == 'div':
                if op != 'mul': raise AssertionError(f'effect {eid}: 1/x with {meth}')
                op = 'div'
            elif how == 'lvl': raise AssertionError(f'effect {eid}: LVL value outside a skill filter')
            target = 'ship' if coll == 'ship' else ('charge' if c == 8 else 'self')
            perLevel = 5 if kw.get('skill') else 1
            row = [target, attrId[tgt], op, attrId[src], perLevel, DEFAULT.get(src, 0.0), penalty(kw)]
            rows = table.setdefault(str(eid), [])
            if row not in rows: rows.append(row)

# Modes: pyfa Ship.__getModeItems -- 'Ship Modifiers' items named like the hull, for Tactical
# Destroyers and the Anhinga; the first one is pyfa's default.
modeItems = {}
for t, v in types.items():
    g = groups[str(v['groupID'])]
    if g.get('categoryID') != 6: continue
    hn = name(int(t))
    if gname(int(t)) != 'Tactical Destroyer' and hn != 'Anhinga': continue
    ms = sorted(int(m) for m, mv in types.items() if gname(int(m)) == MODE_GROUP and name(int(m)).lower().startswith(hn.lower()))
    if not ms: continue
    modeItems[t] = {}
    for m in ms:
        key = name(m)[len(hn):].strip().lower().replace(' mode', '').strip()
        effs = [e['effectID'] for e in td.get(str(m), {}).get('dogmaEffects', [])]
        modeItems[t][key] = [m, effs, {str(a['attributeID']): a['value'] for a in td.get(str(m), {}).get('dogmaAttributes', [])}]

table = dict(sorted(table.items(), key=lambda kv: int(kv[0])))
print(f'RESIST_EFFECTS: {len(table)} effects, {sum(map(len, table.values()))} rows; RESIST_SKILL_MODULE_ROWS: {len(skillRows)}; '
      f'MODE_ITEMS: {len(modeItems)} hulls; unrelated handler errors {len(errors)}')
for k, v in sorted(skipped.items()): print('  skipped:', k)
byTarget = collections.Counter(r[0] + ':' + r[2] + ':' + str(r[6]) for rows in table.values() for r in rows)
print('  rows by target:op:penaltyGroup', dict(byTarget))

html = next((x for x in sys.argv[1:] if not x.startswith('--')), os.path.join(os.path.dirname(__file__), '..', 'index.html'))
src = open(html).read()
uptodate = True
for tname, data in (('RESIST_EFFECTS', table), ('RESIST_SKILL_MODULE_ROWS', skillRows), ('RESIST_ATTRS', RESIST_ATTRS), ('MODE_ITEMS', modeItems)):
    pat = re.compile(r'(const ' + tname + r' = )([\[{].*?[\]}]);\n', re.S)
    m = pat.search(src)
    blob = json.dumps(data, separators=(',', ':'))
    if '--write' in sys.argv:
        if not m: sys.exit(tname + ' not found in ' + html)
        src = src[:m.start(2)] + blob + src[m.end(2):]
        print('wrote', tname)
    elif m:
        same = json.loads(m.group(2)) == json.loads(blob)
        print(f'{tname} vs index.html:', 'same' if same else 'DIFFERENT')
        uptodate &= same
    else:
        print(tname, 'not in index.html yet'); uptodate = False
if '--write' in sys.argv: open(html, 'w').write(src); print('into', html)
elif uptodate: print('index.html table is up to date with this pyfa/SDE.')
