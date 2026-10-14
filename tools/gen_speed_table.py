"""Generate the speed / agility / mass tables (index.html, PYFA CORE section 'speed-calc', since
v2026.10.14.8 -- hand-tables Phase 3) from pyfa's own handlers, the same way gen_resist_table.py
does resistances.

    PYFA_SRC=/path/to/Pyfa python3 -I tools/gen_speed_table.py [index.html]          # diff
    PYFA_SRC=/path/to/Pyfa python3 -I tools/gen_speed_table.py [index.html] --write  # embed

Tables (JSON between `const NAME = ` and `;`):
  SPEED_EFFECTS {effectId: [[target, attr, op, srcAttrId, perLevel, default, penaltyGroup,
                              skills, groups, cond], ...]}
      every hull / module / rig / subsystem handler on a ship's maxVelocity, agility or mass
      (target 'ship'), or on a fitted module's speedFactor / speedBoostFactor / massAddition
      (target 'module', filter = (any of skills) AND (any of groups) on the module, asserted exact).
      op: 'boost' x(1+v/100) | 'mul' | 'add' (pyfa increaseItemAttr, a pre-increase) | 'force'.
      srcAttrId: the carrier's attribute holding the value; null when the handler reads a SKILL
      (Effect1615: fit.character.getSkill) -- then `default` is that skill's value.
      perLevel: 5 when pyfa passes skill= (the All 5 character), else 1.
      penaltyGroup: pyfa's stacking group when stackingPenalties=True, else null.
      cond: null, {shipSkills: [ids]} (Effect1616: only when the HULL requires one of them) or
      {cloaked: true} (Black Ops / Helios / Cheetah: only while a SPEED_CLOAK_EFFECTS effect runs,
      pyfa fit.extraAttributes['cloaked']).
  SPEED_CLOAK_EFFECTS [effectIds] whose handler sets fit.extraAttributes['cloaked'] (active cloaks).
  SPEED_SKILL_ROWS [[skillId, target, attr, op, value, penaltyGroup, skills, groups, cond], ...]
      the same for skills (category 16), one row per carrying skill, value already at level V.
  SPEED_ATTRS {name: attributeId}
  SPEED_PROP_EFFECTS {effectId: 'mwd'|'afterburner'}: Effect6730 moduleBonusMicrowarpdrive /
      Effect6731 moduleBonusAfterburner, ported in the core (pyfaPropBoost). Their handler source is
      checked here against the version the port was written from.
Skipped and reported: missile velocity (charge rows: weapon-range-table), stasis webifier and other
non-propulsion speedFactor rows (EWAR, hand-tables P4), overheat ('self' rows), ship modes
(MODE_EFFECT_ROWS), implants / boosters / system effects (not modelled, DEVIATIONS.md).
"""
import sys, os, re, json, inspect, hashlib, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pyfa_effects import *
import pyfa_effects

SHIP_ATTRS = ('maxVelocity', 'agility', 'mass')
MODULE_ATTRS = ('speedFactor', 'speedBoostFactor', 'massAddition')
attrId = {v['name']: int(k) for k, v in attrs.items()}
DEFAULT = {v['name']: v.get('defaultValue', 0.0) for v in attrs.values()}
MODE_GROUP = 'Ship Modifiers'
PROP = {6730: 'mwd', 6731: 'afterburner'}
# sha256 of the two handlers' source when pyfaPropBoost was ported (pyfa v2.69.2): a change in pyfa
# makes this generator fail, so the port is re-checked instead of silently drifting.
PROP_SRC_SHA = {6730: None, 6731: None}
SRC_SHA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'speed_prop_effects.sha256')

def adict(t): return {aname(x['attributeID']): x['value'] for x in td.get(str(t), {}).get('dogmaAttributes', [])}
pub = [int(t) for t, v in types.items() if v.get('published')]
def sig(t): return (frozenset(reqs(t)), gname(t))
moduleReps = list({sig(t): t for t in pub if cat(t) == 7}.values())
def effs_of(t): return {e['effectID'] for e in td.get(str(t), {}).get('dogmaEffects', [])}
# modules whose speedFactor/speedBoostFactor/massAddition the speed calculation reads:
# propulsion modules (6730/6731) and armor plates (1959 armorReinforcerMassAdd)
SPEED_MODULES = {t for t in pub if cat(t) == 7 and effs_of(t) & {6730, 6731, 1959}}

def fit_filter(lam):
    REC.clear(); hits = []
    for w in moduleReps:
        try:
            if lam(Probe(w)): hits.append(w)
        except Exception: pass
    rec = sorted(set(REC))
    if any(x[0] == 'skill?' for x in rec): raise AssertionError('filter tests the carrying skill -- pass carrier=')
    sk = sorted({skillId[x[1]] for x in rec if x[0] == 'skill' and x[1] in skillId}); gs = sorted({x[1] for x in rec if x[0] == 'eq'})
    calc = [w for w in moduleReps if (not sk or any(s in reqs(w) for s in sk)) and (not gs or gname(w) in gs)]
    if set(calc) != set(hits): raise AssertionError(f'filter not expressible as skills AND groups ({sk}, {gs})')
    return sk or None, gs or None, hits

def parse(expr):
    r = repr(expr)
    m = re.fullmatch(r"\(?a:(\w+)(\*1)?\)?", r)
    if m: return 'attr', m.group(1), 1
    m = re.fullmatch(r"\(a:(\w+)\*LVL\)", r)
    if m: return 'attr', m.group(1), 5
    m = re.fullmatch(r"k:([^:]+):(\w+)", r)
    if m: return 'skill', (m.group(1), m.group(2)), 1
    raise AssertionError(f'unexpected value expression {r}')

OPS = {'boost': 'boost', 'multiply': 'mul', 'increase': 'add', 'force': 'force'}
def opname(meth):
    m = re.sub(r'^filtered(Item|Charge)', '', meth); m = re.sub(r'ItemAttr$', '', m)
    m = m[0].lower() + m[1:]
    if m not in OPS: raise AssertionError(f'unexpected operation {meth}')
    return OPS[m]
def penalty(kw): return str(kw.get('penaltyGroup', 'default')) if kw.get('stackingPenalties') is True else None

carriersByEff = collections.defaultdict(set)
for t, v in td.items():
    if str(t) not in types: continue
    for e in v.get('dogmaEffects', []): carriersByEff[e['effectID']].add(int(t))

def collect(modAttrs, readers):
    """One pass over every carrier. modAttrs: module attributes to record modifiers for; readers[attr]:
    module types whose `attr` a speed handler reads (a module row is kept only if its filter hits one)."""
    table, skillRows, skipped, errors, lateEffects, byCtx, cloakEffects = {}, [], collections.Counter(), [], [], {}, set()
    for eid in sorted(carriersByEff):
        if eid not in EFFECTS or eid in PROP: continue
        cs = carriersByEff[eid]
        if all(gname(t) == MODE_GROUP for t in cs): continue
        cats = {cat(t) for t in cs}
        for c in sorted(cats & {6, 7, 16, 32}):
            ctx = {6: 'ship', 16: 'skill'}.get(c, 'module')
            skillCarriers = sorted(t for t in cs if cat(t) == 16) if c == 16 else [None]
            for carrier in skillCarriers:
                def ev(coll, meth, a):
                    if not (coll == 'modules' and a and callable(a[0]) and 'Charge' not in meth): return None
                    try: return fit_filter(a[0])
                    except AssertionError as ex: return ('ERR', str(ex))   # only fatal if a speed row uses it
                calls, err = run(eid, ctx, ev, carrier=carrier, rich=True)
                if err:
                    errors.append((eid, err)); continue
                shipSkills = None; cond = None
                for coll, meth, a, kw in calls:
                    if coll == 'cond' and meth == 'shipSkill':
                        shipSkills = sorted(set((shipSkills or []) + [skillId[a[0]]])); cond = {'shipSkills': shipSkills}; continue
                    if coll == 'cond' and meth == 'extra':
                        if a[0] != 'cloaked': raise AssertionError(f'effect {eid}: condition on extraAttributes[{a[0]!r}]')
                        cond = {'cloaked': True}; continue
                    if coll == 'extra':
                        if a[0] == 'cloaked': cloakEffects.add(eid)
                        elif a[0] == 'speedLimit': skipped[f"extraAttributes['speedLimit'] (pyfa Fit.maxSpeed reads the ship's speedLimit attribute instead, so it has no effect): {ename(eid)}"] += 1
                        else: raise AssertionError(f'effect {eid}: sets extraAttributes[{a[0]!r}]')
                        continue
                    if coll in ('ship',) and a and str(a[0]) in SHIP_ATTRS:
                        target, attr, expr, sk, gs = 'ship', str(a[0]), a[1], None, None
                    elif coll == 'modules' and len(a) > 2 and str(a[1]) in modAttrs:
                        if 'Charge' in meth: skipped[f'charge {a[1]} (weapon-range-table): {ename(eid)}'] += 1; continue
                        if kw['_eval'][0] == 'ERR': raise AssertionError(f'effect {eid}: {kw["_eval"][1]}')
                        sk, gs, hits = kw['_eval']
                        if not ({sig(t) for t in hits} & {sig(t) for t in readers[str(a[1])]}):   # hits are one type per (skills, group) signature
                            skipped[f'{a[1]} only on modules whose {a[1]} no speed handler reads (e.g. webs: EWAR, P4): {ename(eid)}'] += 1; continue
                        target, attr, expr = 'module', str(a[1]), a[2]
                    elif coll == 'self' and a and str(a[0]) in modAttrs:
                        skipped[f'self {a[0]} (overheat, not modelled): {ename(eid)}'] += 1; continue
                    else: continue
                    if getattr(EFFECTS[eid], 'runTime', 'normal') == 'late': lateEffects.append(eid)
                    kind, src, lvl = parse(expr)
                    op = opname(meth); pg = penalty(kw)
                    perLevel = 5 if (kw.get('skill') or lvl == 5) else 1
                    if c == 16:
                        if kind != 'attr': raise AssertionError(f'skill effect {eid}: value {expr!r}')
                        v = adict(carrier).get(src, DEFAULT.get(src, 0.0)) * perLevel
                        row = [carrier, target, attr, op, v, pg, sk, gs, cond]   # per skill: two skills may carry equal rows
                        if row not in skillRows: skillRows.append(row)
                        continue
                    if kind == 'skill':
                        sname, sattr = src
                        srcId, dflt = None, adict(skillId[sname]).get(sattr, DEFAULT.get(sattr, 0.0))
                    else:
                        srcId, dflt = attrId[src], DEFAULT.get(src, 0.0)
                    row = [target, attr, op, srcId, perLevel, dflt, pg, sk, gs, cond]
                    byCtx.setdefault((eid, ctx), [])
                    if row not in byCtx[(eid, ctx)]: byCtx[(eid, ctx)].append(row)
                    rows = table.setdefault(str(eid), [])
                    if row not in rows: rows.append(row)
    return table, skillRows, skipped, errors, lateEffects, byCtx, cloakEffects

# Pass 1: ship rows, and module rows on the propulsion attributes pyfa's MWD/AB effects read.
readers = {a: SPEED_MODULES for a in MODULE_ATTRS}
table, *_ = collect(set(MODULE_ATTRS), readers)
# Pass 2: also every module attribute a ship row reads from its module (a rig's 'drawback', a
# plate's massAddition, an Inertial Stabilizer's agilityMultiplier...) -- skills and hulls modify
# those too (e.g. the rigging skills halve rig drawbacks). LESSON #20: follow the value back to
# everything that changes it, not only to the handler that applies it.
for e, rows in table.items():
    carried = {t for t in carriersByEff[int(e)] if cat(t) in (7, 32)}
    for r in rows:
        if r[0] == 'ship' and r[3] is not None and carried:
            n = aname(r[3]); readers[n] = readers.get(n, set()) | carried
table, skillRows, skipped, errors, lateEffects, byCtx, cloakEffects = collect(set(readers), readers)

# SPEED_EFFECTS is keyed by effect only: an effect run as a hull ('ship') and as a module must give the
# same rows (pyfa handlers can branch on context, e.g. stackingPenalties='skill' not in context).
for eid in {e for e, _ in byCtx}:
    variants = [json.dumps(r) for (e, c), r in byCtx.items() if e == eid]
    if len(set(variants)) > 1: raise AssertionError(f'effect {eid} gives different rows per carrier context -- key rows by context')
for e, err in errors: print('  handler error (not a speed effect?):', e, ename(e), err[:90]) if '--verbose' in sys.argv else None
# the prop-module handlers the core ports (pyfaPropBoost)
import ast
_esrc = open(os.path.join(PYFA_SRC, 'eos', 'effects.py')).read()
_cls = {n.name: ast.get_source_segment(_esrc, n) for n in ast.parse(_esrc).body if isinstance(n, ast.ClassDef)}
srcSha = {e: hashlib.sha256(_cls[f'Effect{e}'].encode()).hexdigest() for e in PROP}
known = json.load(open(SRC_SHA_FILE)) if os.path.exists(SRC_SHA_FILE) else None
if '--record-prop-source' in sys.argv:
    json.dump({str(k): v for k, v in srcSha.items()}, open(SRC_SHA_FILE, 'w'), indent=1); print('recorded', SRC_SHA_FILE)
elif known is None or any(known.get(str(e)) != srcSha[e] for e in PROP):
    raise SystemExit('pyfa Effect6730/6731 source changed (or no record): re-check pyfaPropBoost against it, then --record-prop-source')
if set(lateEffects): raise AssertionError(f'late-runtime speed effects besides the prop modules: {sorted(set(lateEffects))} -- order matters, model it')

table = dict(sorted(table.items(), key=lambda kv: int(kv[0])))
SPEED_ATTRS = {n: attrId[n] for n in sorted(set(SHIP_ATTRS + MODULE_ATTRS) | set(readers))}
print(f'SPEED_EFFECTS: {len(table)} effects, {sum(map(len, table.values()))} rows; SPEED_SKILL_ROWS: {len(skillRows)}; unrelated handler errors {len(errors)}')
for k, v in sorted(skipped.items()): print('  skipped:', k)
print('  rows by target:attr:op:penaltyGroup', dict(collections.Counter(f'{r[0]}:{r[1]}:{r[2]}:{r[6]}' for rows in table.values() for r in rows)))
if '--verbose' in sys.argv:
    for e, rows in table.items(): print(' ', e, ename(int(e)), rows)
    for r in skillRows: print('  skill', r)

html = next((x for x in sys.argv[1:] if not x.startswith('--')), os.path.join(os.path.dirname(__file__), '..', 'index.html'))
src = open(html).read(); uptodate = True
for tname, data in (('SPEED_EFFECTS', table), ('SPEED_SKILL_ROWS', skillRows), ('SPEED_ATTRS', SPEED_ATTRS), ('SPEED_PROP_EFFECTS', {str(k): v for k, v in PROP.items()}), ('SPEED_CLOAK_EFFECTS', sorted(cloakEffects))):
    m = re.compile(r'(const ' + tname + r' = )([\[{].*?[\]}]);\n', re.S).search(src)
    blob = json.dumps(data, separators=(',', ':'))
    if '--write' in sys.argv:
        if not m: sys.exit(tname + ' not found in ' + html)
        src = src[:m.start(2)] + blob + src[m.end(2):]; print('wrote', tname)
    elif m:
        same = json.loads(m.group(2)) == json.loads(blob); print(f'{tname} vs index.html:', 'same' if same else 'DIFFERENT'); uptodate &= same
    else: print(tname, 'not in index.html yet'); uptodate = False
if '--write' in sys.argv: open(html, 'w').write(src); print('into', html)
elif uptodate: print('index.html table is up to date with this pyfa/SDE.')
