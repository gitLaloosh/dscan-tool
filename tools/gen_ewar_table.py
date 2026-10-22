"""Generate the EWAR tables (index.html, PYFA CORE section 'ewar-calc', since v2026.10.14.11 --
hand-tables Phase 4) from pyfa's own handlers, the same way gen_speed_table.py does speed.

    PYFA_SRC=/path/to/Pyfa python3 -I tools/gen_ewar_table.py [index.html] [--verbose]   # diff
    PYFA_SRC=/path/to/Pyfa python3 -I tools/gen_ewar_table.py [index.html] --write       # embed

What the EWAR / Misc card shows for a fitted warp scrambler / disruptor, stasis web / grappler, ECM,
sensor dampener, target painter, tracking / guidance disruptor, energy neutralizer or nosferatu is
that module's own modified attributes (EWAR_ATTRS: range, falloff, strength, amount, duration ...).
This records every handler that modifies one of them, from every carrier pyfa runs:
  hull (category 6), module / rig (7), subsystem (32), skill (16, value at level V) and a loaded
  charge (8: scripts, which modify their own module, 'self').
Tables (JSON between `const NAME = ` and `;`):
  EWAR_EFFECTS {effectId: [[target, attr, op, srcAttrId, perLevel, default, penaltyGroup, skills,
                             groups, cond], ...]}
      target 'module': every fitted module passing the filter (any of skills) AND (any of groups),
        asserted exact against every published module; 'self': the module carrying the effect (a
        script: the module the charge is loaded in; the value comes from the charge -- its MODIFIED
        value for a CHARGE_ATTR); 'charge' (v2026.10.14.26): the charge loaded in every module passing
        the filter (pyfa filteredChargeBoost), attr one of EWAR_CHARGE_ATTRS.
      op 'boost' x(1+v/100) | 'mul' | 'add' (pre-increase) | 'force'; perLevel 5 when pyfa passes
      skill=; penaltyGroup pyfa's stacking group when stackingPenalties=True, else null;
      cond null | {shipSkills: [...]} | {cloaked: true}, as in SPEED_EFFECTS.
  EWAR_SKILL_ROWS [[skillId, target, attr, op, valueAtV, penaltyGroup, skills, groups, cond], ...]
  EWAR_ATTRS {name: attributeId}
  EWAR_GROUPS [group names whose modules the card lists]
Skipped and reported: overheat ('self' rows of overheat handlers, not modelled), rows whose filter
reaches only non-EWAR modules (e.g. a propulsion module's speedFactor: speed-calc), ship modes
(MODE_EFFECT_ROWS), implants / boosters / system effects (not modelled, DEVIATIONS.md).
A handler error is a handler not recorded (LESSON #28): every one is listed, and the run fails if a
kept row depends on a filter that could not be evaluated.
"""
import sys, os, re, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pyfa_effects import *

EWAR_GROUPS = ['Warp Scrambler', 'Stasis Web', 'Stasis Grappler', 'ECM', 'Sensor Dampener', 'Target Painter',
               'Weapon Disruptor', 'Energy Neutralizer', 'Energy Nosferatu',
               # v2026.10.14.26 (Erik: "4. do it" -- bubbles and Command Bursts on the EWAR / Misc card)
               'Warp Disrupt Field Generator', 'Command Burst',
               # v2026.10.14.29 (Erik: "start on 1 and 2 together" -- effect-audit leftovers): the ECM Burst
               # (an area jam around the ship) and the Supercarriers' Burst Projectors (area web / neut / paint /
               # damp / disruption / ECM / bubble fields projected up to 200-500 km away)
               'Burst Jammer', 'Burst Projectors']
ATTR_NAMES = ['maxRange', 'falloffEffectiveness', 'warpScrambleStrength', 'speedFactor', 'signatureRadiusBonus',
              'maxTargetRangeBonus', 'scanResolutionBonus', 'energyNeutralizerAmount', 'powerTransferAmount', 'duration',
              'scanGravimetricStrengthBonus', 'scanLadarStrengthBonus', 'scanMagnetometricStrengthBonus', 'scanRadarStrengthBonus',
              'maxRangeBonus', 'falloffBonus', 'trackingSpeedBonus',
              'missileVelocityBonus', 'explosionDelayBonus', 'aoeVelocityBonus', 'aoeCloudSizeBonus',
              # v2026.10.14.26: Warp Disrupt Field Generator bubble radius; Command Burst strength and duration
              'warpScrambleRange', 'warfareBuff1Value', 'warfareBuff2Value', 'warfareBuff3Value', 'warfareBuff4Value', 'buffDuration',
              # v2026.10.14.29: Burst Jammer radius; Burst Projector field radius, field lifetime, warning delay and how
              # long a target stays affected (the four per-type durations)
              'ecmBurstRange', 'doomsdayAOERange', 'doomsdayAOEDuration', 'doomsdayWarningDuration',
              'durationECMJammerBurstProjector', 'durationTargetIlluminationBurstProjector',
              'durationSensorDampeningBurstProjector', 'durationWeaponDisruptionBurstProjector']
# v2026.10.14.26: CHARGE attributes modified by pyfa handlers (filteredChargeBoost: the filter tests the
# module the charge is loaded in). A Command Burst charge's warfareBuffNMultiplier, boosted by the
# Command Specialist skills, then multiplies the burst's warfareBuffNValue (charge effect 6737, 'self').
CHARGE_ATTR_NAMES = ['warfareBuff1Multiplier', 'warfareBuff2Multiplier', 'warfareBuff3Multiplier', 'warfareBuff4Multiplier']
attrId = {v['name']: int(k) for k, v in attrs.items()}
DEFAULT = {v['name']: v.get('defaultValue', 0.0) for v in attrs.values()}
MODE_GROUP = 'Ship Modifiers'

def adict(t): return {aname(x['attributeID']): x['value'] for x in td.get(str(t), {}).get('dogmaAttributes', [])}
pub = [int(t) for t, v in types.items() if v.get('published')]
def sig(t): return (frozenset(reqs(t)), gname(t))
moduleReps = list({sig(t): t for t in pub if cat(t) == 7}.values())
EWAR_MODULES = {t for t in pub if cat(t) == 7 and gname(t) in EWAR_GROUPS}
EWAR_SIGS = {sig(t) for t in EWAR_MODULES}
# charges an EWAR module can load (its chargeGroup1-5 attributes): the scripts
EWAR_CHARGE_GROUPS = {int(v) for t in EWAR_MODULES for k, v in adict(t).items() if re.fullmatch(r'chargeGroup\d', k) and v}
missing = sorted(set(EWAR_GROUPS) - {gname(t) for t in EWAR_MODULES})
# v2026.10.14.29: filters run on one module per (skills, group) signature PLUS every EWAR module. One representative
# is enough while a filter tests only skills and group, but Effect2982 also tests whether the module HAS an attribute
# (`getAttribute('durationECMJammerBurstProjector')`), and the seven Burst Projectors share one signature while each
# carries a different duration attribute: with one representative, four of Effect2982's five rows matched nothing.
FILTER_POOL = moduleReps + sorted(EWAR_MODULES - set(moduleReps))   # LESSON #28
if missing: raise AssertionError(f'no published module in groups {missing} -- group renamed?')

def fit_filter(lam, target=None, meth=''):
    REC.clear(); hits = []
    for w in FILTER_POOL:
        try:
            if lam(Probe(w)): hits.append(w)
        except Exception: pass
    rec = sorted(set(REC))
    if any(x[0] == 'skill?' for x in rec): raise AssertionError('filter tests the carrying skill -- pass carrier=')
    sk = sorted({skillId[x[1]] for x in rec if x[0] == 'skill' and x[1] in skillId}); gs = sorted({x[1] for x in rec if x[0] == 'eq'})
    ha = sorted({x[1] for x in rec if x[0] == 'hasattr'})
    calc0 = [w for w in FILTER_POOL if (not sk or any(s in reqs(w) for s in sk)) and (not gs or gname(w) in gs)]
    calc = [w for w in calc0 if all(adict(w).get(n) for n in ha)]
    if set(calc) != set(hits): raise AssertionError(f'filter not expressible as skills AND groups ({sk}, {gs}, has {ha})')
    # a base-attribute test (Effect2982 `getAttribute('duration')`) is dropped only when it changes
    # nothing for the EWAR modules; otherwise the row would need it as a condition
    if ha and {sig(w) for w in calc0} & EWAR_SIGS != {sig(w) for w in calc} & EWAR_SIGS:
        # v2026.10.14.29: Effect2982 (Burst Projector Operation) boosts each Burst Projector duration only on a
        # projector that HAS that attribute (pyfa #927: "otherwise we add attributes that don't belong"). When the
        # tested attribute is the one being boosted / multiplied and its SDE default is 0, a module without it stays
        # at 0 either way, so the test changes no value and is dropped. Anything else still fails.
        if not (ha == [target] and DEFAULT.get(target, 0.0) == 0 and re.search(r'(Boost|Multiply)$', meth)):
            raise AssertionError(f'filter tests base attributes {ha} that some EWAR modules lack -- model it')
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
def etype(eid):
    t = getattr(EFFECTS[eid], 'type', None)
    return (t,) if isinstance(t, str) else (t or ())

carriersByEff = collections.defaultdict(set)
for t, v in td.items():
    if str(t) not in types: continue
    for e in v.get('dogmaEffects', []): carriersByEff[e['effectID']].add(int(t))

modAttrs = set(ATTR_NAMES)
_EFF_SRC = open(os.path.join(PYFA_SRC, 'eos', 'effects.py')).read()
def src_only_read(attr):
    """True when every mention of the attribute in pyfa's effects.py is a read (getModified*Attr)."""
    total = len(re.findall(r"['\"]" + re.escape(attr) + r"['\"]", _EFF_SRC))
    reads = len(re.findall(r"getModified(?:Item|Charge)Attr\(\s*['\"]" + re.escape(attr) + r"['\"]", _EFF_SRC))
    return total > 0 and total == reads
table, skillRows, skipped, errors, late, byCtx = {}, [], collections.Counter(), [], [], {}
for eid in sorted(carriersByEff):
    if eid not in EFFECTS: continue
    cs = carriersByEff[eid]
    if all(gname(t) == MODE_GROUP for t in cs): continue
    for c in sorted({cat(t) for t in cs} & {6, 7, 8, 16, 32}):
        ctx = {6: 'ship', 16: 'skill'}.get(c, 'module')
        skillCarriers = sorted(t for t in cs if cat(t) == 16) if c == 16 else [None]
        for carrier in skillCarriers:
            def ev(coll, meth, a):
                if not (coll == 'modules' and a and callable(a[0])): return None
                try: return fit_filter(a[0], str(a[1]) if len(a) > 1 else None, meth)
                except AssertionError as ex: return ('ERR', str(ex))
            calls, err = run(eid, ctx, ev, carrier=carrier, rich=True)
            if err: errors.append((eid, c, err)); continue
            cond = None
            for coll, meth, a, kw in calls:
                if coll == 'cond' and meth == 'shipSkill':
                    cond = {'shipSkills': sorted(set((cond or {}).get('shipSkills', []) + [skillId[a[0]]]))}; continue
                if coll == 'cond' and meth == 'extra':
                    if a[0] != 'cloaked': raise AssertionError(f'effect {eid}: condition on extraAttributes[{a[0]!r}]')
                    cond = {'cloaked': True}; continue
                if coll == 'modules' and len(a) > 2 and 'Charge' in meth and str(a[1]) in CHARGE_ATTR_NAMES:
                    if kw['_eval'][0] == 'ERR': raise AssertionError(f'effect {eid}: {kw["_eval"][1]}')
                    sk, gs, hits = kw['_eval']
                    if not ({sig(t) for t in hits} & EWAR_SIGS):
                        skipped[f'charge {a[1]} only in non-EWAR modules: {ename(eid)}'] += 1; continue
                    target, attr, expr = 'charge', str(a[1]), a[2]
                elif coll == 'modules' and len(a) > 2 and str(a[1]) in modAttrs:
                    if 'Charge' in meth: skipped[f'charge {a[1]}: {ename(eid)}'] += 1; continue
                    if kw['_eval'][0] == 'ERR': raise AssertionError(f'effect {eid}: {kw["_eval"][1]}')
                    sk, gs, hits = kw['_eval']
                    if not ({sig(t) for t in hits} & EWAR_SIGS):
                        skipped[f'{a[1]} only on non-EWAR modules: {ename(eid)}'] += 1; continue
                    target, attr, expr = 'module', str(a[1]), a[2]
                elif coll == 'self' and a and str(a[0]) in modAttrs:
                    if 'overheat' in etype(eid): skipped[f'self {a[0]} (overheat, not modelled): {ename(eid)}'] += 1; continue
                    if c == 8 and not any(types[str(t)]['groupID'] in EWAR_CHARGE_GROUPS for t in cs if cat(t) == 8):
                        skipped[f'self {a[0]} from a charge no EWAR module loads: {ename(eid)}'] += 1; continue
                    if c in (7, 32) and not ({sig(t) for t in cs if cat(t) == 7} & EWAR_SIGS):
                        skipped[f'self {a[0]} on a non-EWAR module: {ename(eid)}'] += 1; continue
                    target, attr, expr, sk, gs = 'self', str(a[0]), a[1], None, None
                else: continue
                if 'pyfa_effects.Any' in repr(expr):   # e.g. Alliance Tournament hulls scaled by pilot security status
                    skipped[f'{attr} scaled by pilot security status (not on a killmail / EFT, DEVIATIONS.md): {ename(eid)}'] += 1; continue
                kind, src, lvl = parse(expr)
                op = opname(meth); pg = penalty(kw)
                # runTime early/late only matters when the result depends on order: a force, or a value
                # read from an attribute other handlers modify. Script boosts read the charge's own value.
                if getattr(EFFECTS[eid], 'runTime', 'normal') != 'normal':
                    # v2026.10.14.26: an early / late boost or multiply whose source attribute no handler ever
                    # writes is order-independent (boosts commute): Industrial Core burst rows, Laelaps WDFG sig
                    if op != 'force' and kind == 'attr' and src_only_read(src):
                        skipped[f'runTime {EFFECTS[eid].runTime} kept (source {src} is never modified, order-independent): {ename(eid)}'] += 1
                    elif op == 'force' or c != 8: late.append((eid, ename(eid)))
                    else: skipped[f'runTime {EFFECTS[eid].runTime} kept (script boost from the charge, order-independent): {ename(eid)}'] += 1
                perLevel = 5 if (kw.get('skill') or lvl == 5) else 1
                if c == 16:
                    if kind != 'attr': raise AssertionError(f'skill effect {eid}: value {expr!r}')
                    v = adict(carrier).get(src, DEFAULT.get(src, 0.0)) * perLevel
                    row = [carrier, target, attr, op, v, pg, sk, gs, cond]
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

for eid in {e for e, _ in byCtx}:
    variants = [json.dumps(r) for (e, c), r in byCtx.items() if e == eid]
    if len(set(variants)) > 1: raise AssertionError(f'effect {eid} gives different rows per carrier context')
if late: raise AssertionError(f'non-normal runtime EWAR effects: {sorted(set(late))} -- order matters, model it')

table = dict(sorted(table.items(), key=lambda kv: int(kv[0])))
EWAR_ATTRS = {n: attrId[n] for n in ATTR_NAMES}
EWAR_CHARGE_ATTRS = {n: attrId[n] for n in CHARGE_ATTR_NAMES}
print(f'EWAR_EFFECTS: {len(table)} effects, {sum(map(len, table.values()))} rows; EWAR_SKILL_ROWS: {len(skillRows)}; handler errors {len(errors)}')
for k, v in sorted(skipped.items()): print('  skipped:', k) if '--verbose' in sys.argv else None
print('  skipped kinds:', dict(collections.Counter(k.split(':')[0] for k in skipped)))
print('  rows by target:attr:op:penaltyGroup', dict(collections.Counter(f'{r[0]}:{r[1]}:{r[2]}:{r[6]}' for rows in table.values() for r in rows)))
if '--verbose' in sys.argv:
    for e, rows in table.items(): print(' ', e, ename(int(e)), rows)
    for r in skillRows: print('  skill', name(r[0]), r[1:])
    for e, c, err in errors: print('  handler error:', e, ename(e), 'cat', c, err[:100])

html = next((x for x in sys.argv[1:] if not x.startswith('--')), os.path.join(os.path.dirname(__file__), '..', 'index.html'))
src = open(html).read(); uptodate = True
for tname, data in (('EWAR_EFFECTS', table), ('EWAR_SKILL_ROWS', skillRows), ('EWAR_ATTRS', EWAR_ATTRS), ('EWAR_CHARGE_ATTRS', EWAR_CHARGE_ATTRS), ('EWAR_GROUPS', EWAR_GROUPS)):
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
