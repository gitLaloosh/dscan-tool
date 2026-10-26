"""Generate the target-side table of PYFA CORE section 'projected' (index.html, v2026.10.14.35 --
roadmap/turret-application-plan.md Phase 2a) from pyfa's own handlers.

    PYFA_SRC=/path/to/Pyfa python3 -I tools/gen_projected_table.py [index.html]          # diff
    PYFA_SRC=/path/to/Pyfa python3 -I tools/gen_projected_table.py [index.html] --write  # embed

pyfa's damage graph (graphs/data/fitDamageStats/calc/projected.py) reads three attributes of the TARGET
ship besides its speed and signature radius:
  * disallowOffensiveModifiers -- a ship with it set cannot be webbed or painted (getTackledSpeed /
    getSigRadiusMult return early);
  * stasisWebifierResistance / targetPainterResistance -- the attributes named by the webs' and painters'
    remoteResistanceID (eos/modifiedAttributeDict.py getResistanceAttrID): a web's multiplier m becomes
    (m - 1) * resistance + 1 (__calculateValue, extraMultipliers).
This records every pyfa handler that changes one of them on the ship, run in its carrier's own context:
hull ('ship'), module / rig / subsystem ('module'), skill ('skill', value at V), implant ('implant') and
booster ('booster').

Table (JSON between `const PROJ_TARGET_EFFECTS = ` and `;`):
  PROJ_TARGET_EFFECTS {effectId: [[attr, op, srcAttrId, perLevel, default, penaltyGroup], ...]}
    op 'boost' x(1+v/100) | 'mul' | 'add' | 'force'; srcAttrId = the carrier's attribute holding the value;
    perLevel 5 when pyfa passes skill= (the All 5 character); penaltyGroup when stackingPenalties=True.
  PROJ_TARGET_ATTRS {name: attributeId} and their SDE defaults in PROJ_TARGET_DEFAULTS.
A handler that filters, branches on a condition, or reads a pilot-dependent value fails the generator
(model it first).

Second table: the attacker's DRONES -- web and target painter drones (pyfa cache/projected.py getProjDroneData
reads each drone's modified speedFactor / signatureRadiusBonus, Drone.maxRange, Drone.falloff, maxVelocity and
radius) and, since v2026.10.14.40, every damage drone (calc/application.py getDroneMult also reads
trackingSpeed and optimalSigRadius). Every handler that modifies one of those on a drone, from every carrier
pyfa runs (hull, module / rig / subsystem, skill at V, implant, booster), with its filter as (any of skills)
AND (any of groups) on the drone, asserted exact against every published web / painter / damage drone:
  PROJ_DRONE_EFFECTS {effectId: [[attr, op, srcAttrId, perLevel, default, penaltyGroup, skills, groups], ...]}
  PROJ_DRONE_SKILL_ROWS [[skillId, attr, op, valueAtV, penaltyGroup, skills, groups], ...]
  PROJ_DRONE_ATTRS {name: attributeId} and their SDE defaults in PROJ_DRONE_DEFAULTS.
Third table (v2026.10.14.64): the attacker's FIGHTERS (getFighterAbilityMult's inputs), PROJ_FIGHTER_*; since
v2026.10.14.66 over every fighter (support squadrons launch too) with the squadron's own speed abilities
(PROJ_FIGHTER_SELF_EFFECTS). Since v2026.10.14.70 also the support abilities' attributes (FIGHTER_EWAR): webs go to
PYFA CORE projected (getProjFighterData's webFighters), neutralizers / ECM / warp disruption to the EWAR card.
"""
import sys, os, re, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pyfa_effects import *

ATTRS = ('disallowOffensiveModifiers', 'stasisWebifierResistance', 'targetPainterResistance')
attrId = {v['name']: int(k) for k, v in attrs.items()}
# v2026.10.14.64 (D5 fighters): getFighterAbilityMult multiplies a fighter ability's damage on a FIT by the target ship's
# attribute its {prefix}ResistanceID names (fighterAbilityAntiFighterMissileResistance, ...AntiCapitalMissileResistance):
# every id any published fighter carries, with pyfa's handlers on it (none today) and its SDE default.
_resIds = sorted({int(x['value']) for t, v in types.items() if v.get('published') and cat(t) == 87
                  for x in td.get(str(t), {}).get('dogmaAttributes', []) if attrs.get(str(x['attributeID']), {}).get('name', '').endswith('ResistanceID') and x['value']})
ATTRS = ATTRS + tuple(attrs[str(i)]['name'] for i in _resIds)
DEFAULT = {v['name']: v.get('defaultValue', 0.0) for v in attrs.values()}
OPS = {'boost': 'boost', 'multiply': 'mul', 'increase': 'add', 'force': 'force'}

def opname(meth):
    m = re.sub(r'ItemAttr$', '', meth)
    m = m[0].lower() + m[1:]
    if m not in OPS: raise AssertionError(f'unexpected operation {meth}')
    return OPS[m]
def penalty(kw): return str(kw.get('penaltyGroup', 'default')) if kw.get('stackingPenalties') is True else None
def value(expr):
    r = repr(expr)
    m = re.fullmatch(r"\(?a:(\w+)(\*1)?\)?", r)
    if m: return m.group(1), 1
    m = re.fullmatch(r"\(a:(\w+)\*LVL\)", r)
    if m: return m.group(1), 5
    raise AssertionError(f'unexpected value expression {r}')

def ctx_of(t):
    c = cat(t)
    if c == 6: return 'ship'
    if c in (7, 32): return 'module'
    if c == 16: return 'skill'
    if c == 20:
        a = {aname(x['attributeID']) for x in td.get(str(t), {}).get('dogmaAttributes', [])}
        return 'booster' if 'boosterness' in a else 'implant'
    return None

carriers = collections.defaultdict(set)
for t, v in td.items():
    if str(t) not in types: continue
    for e in v.get('dogmaEffects', []): carriers[e['effectID']].add(int(t))

def build():
    table, ctxs, skipped = {}, {}, collections.Counter()
    for eid in sorted(carriers):
        if eid not in EFFECTS: continue
        for ctx in sorted({ctx_of(t) for t in carriers[eid]} - {None}):
            carrier = next(t for t in sorted(carriers[eid]) if ctx_of(t) == ctx)
            calls, err = run(eid, ctx, None, carrier=carrier if ctx == 'skill' else None, rich=True)
            if err: continue   # not one of ours (the recorder can't run every handler); ours are asserted below
            rows = []
            for coll, meth, a, kw in calls:
                if coll != 'ship' or not a or str(a[0]) not in ATTRS: continue
                if any(c == 'cond' for c, *_ in calls): raise AssertionError(f'effect {eid}: conditional handler -- model it')
                src, lvl = value(a[1])
                if kw.get('skill'): lvl = 5
                row = [str(a[0]), opname(meth), attrId[src], lvl, DEFAULT.get(src, 0.0), penalty(kw)]
                if row not in rows: rows.append(row)
            if not rows: continue
            if str(eid) in table and table[str(eid)] != rows: raise AssertionError(f'effect {eid}: rows differ by context')
            table[str(eid)] = rows; ctxs.setdefault(str(eid), []).append(ctx)
    # every handler that names one of the attributes must have been recorded (no silent miss)
    src = open(os.path.join(PYFA_SRC, 'eos', 'effects.py')).read()
    for m in re.finditer(r'\nclass Effect(\d+)\(BaseEffect\):(.*?)(?=\nclass |\Z)', src, flags=re.S):
        eid, body = m.group(1), m.group(2)
        writes = [k for k in ATTRS if re.search(r"(boost|multiply|increase|force|preAssign)ItemAttr\(\s*'" + k + "'", body)]
        if writes and eid not in table:
            if int(eid) not in carriers: skipped[f'no SDE carrier: Effect{eid}'] += 1; continue
            raise AssertionError(f'Effect{eid} writes {writes} but was not recorded')
    return dict(sorted(table.items(), key=lambda kv: int(kv[0]))), ctxs, skipped

DRONE_ATTRS = ('speedFactor', 'signatureRadiusBonus', 'maxVelocity', 'shieldTransferRange', 'powerTransferRange', 'empFieldRange',
               'ecmBurstRange', 'maxRange', 'ECMRangeOptimal', 'falloff', 'falloffEffectiveness', 'radius',
               'trackingSpeed', 'optimalSigRadius')   # v2026.10.14.40: + what getDroneMult reads for damage drones
DRONE_ATTRS = tuple(a for a in DRONE_ATTRS if a in attrId)   # energyDestabilizationRange is not an SDE attribute
def _effs(t): return {e['effectID'] for e in td.get(str(t), {}).get('dogmaEffects', [])}
DMG_ATTR_IDS = {114, 116, 117, 118}   # em / explosive / kinetic / thermal damage: pyfa Drone.dealsDamage
def _deals(t): return any(x['value'] > 0 for x in td.get(str(t), {}).get('dogmaAttributes', []) if x['attributeID'] in DMG_ATTR_IDS)
# v2026.10.14.40 (D5, drone damage application): web / painter drones AND every damage drone
projDrones = sorted(t for t, v in types.items() if v.get('published') and cat(t) == 18 and (_effs(t) & {6690, 6692} or _deals(t)))
projDrones = [int(t) for t in projDrones]
def _dsig(t): return (frozenset(reqs(t)), gname(t))
droneReps = list({_dsig(t): t for t in projDrones}.values())

def drone_filter(lam):
    REC.clear(); hits = []
    for t in droneReps:
        try:
            if lam(Probe(t)): hits.append(t)
        except Exception: pass
    rec = sorted(set(REC))
    if any(x[0] == 'skill?' for x in rec): raise AssertionError('filter tests the carrying skill -- pass carrier=')
    sk = sorted({skillId[x[1]] for x in rec if x[0] == 'skill' and x[1] in skillId}); gs = sorted({x[1] for x in rec if x[0] == 'eq'})
    calc = [t for t in droneReps if (not sk or any(x in reqs(t) for x in sk)) and (not gs or gname(t) in gs)]
    if set(calc) != set(hits): raise AssertionError(f'drone filter not expressible as skills AND groups ({sk}, {gs})')
    return sk or None, gs or None, hits

def build_drones():
    table, skillRows, byCtx, skipped = {}, [], {}, collections.Counter()
    for eid in sorted(carriers):
        if eid not in EFFECTS: continue
        for ctx in sorted({ctx_of(t) for t in carriers[eid]} - {None}):
            skillCarriers = sorted(t for t in carriers[eid] if ctx_of(t) == 'skill') if ctx == 'skill' else [None]
            for carrier in skillCarriers:
                def ev(coll, meth, a):
                    if not (coll == 'drones' and a and callable(a[0])): return None
                    try: return drone_filter(a[0])
                    except AssertionError as ex: return ('ERR', str(ex))
                calls, err = run(eid, ctx, ev, carrier=carrier, rich=True)
                if err: continue
                for coll, meth, a, kw in calls:
                    if coll != 'drones' or len(a) < 3 or str(a[1]) not in DRONE_ATTRS: continue
                    e = kw.get('_eval')
                    if e is None: raise AssertionError(f'effect {eid}: unfiltered drone call')
                    if e[0] == 'ERR': raise AssertionError(f'effect {eid}: {e[1]}')
                    sk, gs, hits = e
                    if not hits: continue
                    if 'Charge' in meth: raise AssertionError(f'effect {eid}: drone charge call')
                    if 'pyfa_effects.Any' in repr(a[2]): skipped[f'pilot-dependent value: {ename(eid)}'] += 1; continue
                    src, lvl = value(a[2])
                    if kw.get('skill'): lvl = 5
                    op = opname(re.sub(r'^filteredItem', '', meth) + 'ItemAttr')
                    if ctx == 'skill':
                        v = {aname(x['attributeID']): x['value'] for x in td.get(str(carrier), {}).get('dogmaAttributes', [])}.get(src, DEFAULT.get(src, 0.0)) * lvl
                        row = [carrier, str(a[1]), op, v, penalty(kw), sk, gs]
                        if row not in skillRows: skillRows.append(row)
                        continue
                    row = [str(a[1]), op, attrId[src], lvl, DEFAULT.get(src, 0.0), penalty(kw), sk, gs]
                    # implants / boosters keyed by context (Effect2013 is penalized on a rig, not on an implant)
                    key = f'{ctx}:{eid}' if ctx in ('implant', 'booster') else str(eid)
                    byCtx.setdefault((key, ctx), [])
                    if row not in byCtx[(key, ctx)]: byCtx[(key, ctx)].append(row)
                    rows = table.setdefault(key, [])
                    if row not in rows: rows.append(row)
    # every handler that touches one of the attributes on fit.drones must have been recorded (no silent miss)
    recorded = {int(k.split(':')[-1]) for k in table} | {e for e in carriers if any(r[0] in carriers[e] for r in skillRows)}
    src = open(os.path.join(PYFA_SRC, 'eos', 'effects.py')).read()
    pat = re.compile(r"fit\.drones\.filtered\w+\((?:[^()]|\([^()]*\))*?'(" + '|'.join(DRONE_ATTRS) + r")'", re.S)
    for m in re.finditer(r'\nclass Effect(\d+)\(BaseEffect\):(.*?)(?=\nclass |\Z)', src, flags=re.S):
        eid, body = int(m.group(1)), m.group(2)
        if not pat.search(body) or eid in recorded: continue
        if eid not in carriers: skipped[f'no SDE carrier: Effect{eid}'] += 1; continue
        hitsAny = False
        for ctx in sorted({ctx_of(t) for t in carriers[eid]} - {None}):
            calls, err = run(eid, ctx, None, carrier=next((t for t in sorted(carriers[eid]) if ctx_of(t) == 'skill'), None) if ctx == 'skill' else None, rich=True)
            if err: raise AssertionError(f'Effect{eid} touches a drone attribute but the recorder could not run it: {err}')
        skipped[f'touches a drone attribute, no web / painter / damage drone passes its filter: Effect{eid} {ename(eid)}'] += 1
    for eid in {e for e, _ in byCtx}:
        variants = {json.dumps(r) for (e, c), r in byCtx.items() if e == eid}
        if len(variants) > 1: raise AssertionError(f"effect {eid}: drone rows differ by context: {variants}")
    return dict(sorted(table.items(), key=lambda kv: (int(kv[0].split(':')[-1]), kv[0]))), sorted(skillRows), skipped

# v2026.10.14.64 (D5 fighters, the owner 2026-10-25 "let's tackle fighter damage application"): what pyfa's
# getFighterAbilityMult (graphs/data/fitDamageStats/calc/application.py) reads on a fighter, for each damage ability
# prefix: the squadron's maxVelocity and radius, the ability's range (RangeOptimal, else Range), RangeFalloff,
# explosion radius / velocity, damage reduction factor / sensitivity (either spelling) and ResistanceID. Every handler
# on fit.fighters that modifies one of them, from every carrier (hull, module / rig, skill at V, implant, booster),
# filter asserted as (any of skills) AND (any of groups) over every published fighter with a damage ability.
FIGHTER_PREFIXES = ('fighterAbilityAttackMissile', 'fighterAbilityMissiles')
# pyfa FighterAbility.attrPrefix is the effect's own `prefix`; bombs (fighterAbilityLaunchBomb) are off by default and
# not launched by the tool, so the table names the two missile-style damage abilities (asserted below).
def _fighter_ability_prefixes():
    out = {}
    for t, v in types.items():
        if not (v.get('published') and cat(t) == 87): continue
        for e in td.get(str(t), {}).get('dogmaEffects', []):
            cls = EFFECTS.get(e['effectID'])
            if cls is not None and getattr(cls, 'dealsDamage', False) and getattr(cls, 'prefix', None) != 'fighterAbilityLaunchBomb':
                out[ename(e['effectID'])] = cls.prefix
    if sorted(set(out.values())) != sorted(FIGHTER_PREFIXES): raise AssertionError(f'fighter damage abilities changed: {out}')
    return dict(sorted(out.items()))
FIGHTER_ABILITY_PREFIX = _fighter_ability_prefixes()
FIGHTER_ATTRS = ('maxVelocity', 'radius') + tuple(p + s for p in FIGHTER_PREFIXES for s in (
    'RangeOptimal', 'Range', 'RangeFalloff', 'ExplosionRadius', 'ExplosionVelocity', 'ReductionFactor', 'DamageReductionFactor',
    'ReductionSensitivity', 'DamageReductionSensitivity', 'ResistanceID'))
# v2026.10.14.66 (Fighter bay: squadrons and abilities you choose): the squadron's own speed abilities -- MWD, afterburner,
# evasive maneuvers, off by default -- boost its maxVelocity by these attributes when switched on (FIGHTER_SELF below).
FIGHTER_SPEED_BONUS = ('fighterAbilityMicroWarpDriveSpeedBonus', 'fighterAbilityAfterburnerSpeedBonus', 'fighterAbilityEvasiveManeuversSpeedBonus')
FIGHTER_ATTRS = FIGHTER_ATTRS + FIGHTER_SPEED_BONUS
# v2026.10.14.70 (fighter gaps delivery 2): what the support abilities read (pyfa Effect6435 / 6434 / 6437 / 6436 and
# cache/projected.py getProjFighterData): the web's speed penalty, optimal and falloff (applied, webFighters); the
# neutralizer's amount, ranges and cycle, the ECM's four strengths, ranges and cycle, the warp disruption's strength and
# range (shown on the EWAR card, not applied: the owner's "Webs applied, rest shown").
FIGHTER_EWAR = ('fighterAbilityStasisWebifierSpeedPenalty', 'fighterAbilityStasisWebifierOptimalRange', 'fighterAbilityStasisWebifierFalloffRange',
                'fighterAbilityStasisWebifierResistanceID',
                'fighterAbilityEnergyNeutralizerAmount', 'fighterAbilityEnergyNeutralizerOptimalRange', 'fighterAbilityEnergyNeutralizerFalloffRange',
                'fighterAbilityEnergyNeutralizerDuration', 'fighterAbilityEnergyNeutralizerResistanceID',
                'fighterAbilityECMStrengthGravimetric', 'fighterAbilityECMStrengthLadar', 'fighterAbilityECMStrengthMagnetometric', 'fighterAbilityECMStrengthRadar',
                'fighterAbilityECMRangeOptimal', 'fighterAbilityECMRangeFalloff', 'fighterAbilityECMDuration', 'fighterAbilityECMResistanceID',
                'fighterAbilityWarpDisruptionPointStrength', 'fighterAbilityWarpDisruptionRange', 'fighterAbilityWarpDisruptionDuration')
FIGHTER_ATTRS = FIGHTER_ATTRS + FIGHTER_EWAR
FIGHTER_ATTRS = tuple(a for a in FIGHTER_ATTRS if a in attrId)
FIGHTER_DMG = {attrId[p + d] for p in FIGHTER_PREFIXES for d in ('DamageEM', 'DamageTherm', 'DamageKin', 'DamageExp') if p + d in attrId}
def _fdeals(t): return any(x['value'] > 0 for x in td.get(str(t), {}).get('dogmaAttributes', []) if x['attributeID'] in FIGHTER_DMG)
dmgFighters = [int(t) for t in sorted(t for t, v in types.items() if v.get('published') and cat(t) == 87 and _fdeals(t))]
# v2026.10.14.66: the filters are asserted over every fighter with an ability pyfa implements (support fighters launch now)
FIGHTER_ABILITY_IDS = {e for e in EFFECTS if (effs.get(str(e), {}).get('effectName') or '').startswith('fighterAbility')}
allFighters = [int(t) for t in sorted(t for t, v in types.items() if v.get('published') and cat(t) == 87
               and any(e['effectID'] in FIGHTER_ABILITY_IDS for e in td.get(str(t), {}).get('dogmaEffects', [])))]
fighterReps = list({_dsig(t): t for t in allFighters}.values())

def build_fighter_self():
    """pyfa eos/saveddata/fighter.py calculateModifiedAttributes runs each ACTIVE ability's handler on the squadron itself
    (context ('fighter',)); the ones with a local handler are the speed abilities. Each must be grouped (run once, not
    once per fighter) and boost only maxVelocity / signatureRadius by one of the squadron's own attributes, stacking-
    penalized in 'default' (asserted on pyfa's source). Signature radius isn't read by the damage graph on the attacker's
    side, so only maxVelocity rows are kept: {effectId: [['maxVelocity', 'boost', srcAttrId, penaltyGroup]]}."""
    src = open(os.path.join(PYFA_SRC, 'eos', 'effects.py')).read()
    out = {}
    for e in sorted(FIGHTER_ABILITY_IDS):
        cls = EFFECTS.get(e)
        if cls is None or 'handler' not in vars(cls) or getattr(cls, 'dealsDamage', False): continue
        body = re.search(r'\nclass Effect' + str(e) + r'\(BaseEffect\):(.*?)(?=\nclass |\Z)', src, re.S).group(1)
        if "'projected' not in context" in body: continue   # EWAR: runs only when projected (getProjFighterData's side)
        if getattr(cls, 'grouped', False) is not True: raise AssertionError(f'Effect{e}: local fighter ability not grouped -- model it')
        calls = re.findall(r"\w+\.(boost|multiply)ItemAttr\(\s*'(\w+)',\s*\w+\.getModifiedItemAttr\(\s*'(\w+)'\s*\),\s*stackingPenalties=True,\s*\*\*kwargs\)", body)
        allCalls = [c for c in re.findall(r'\.(\w+ItemAttr)\(', body) if c != 'getModifiedItemAttr']
        if len(allCalls) != len(calls) or not calls: raise AssertionError(f'Effect{e}: unexpected handler body -- model it')
        for op, tgt, srcAttr in calls:
            # the squadron's own signature radius and shield resonances (evasive maneuvers) aren't read by the damage graph
            if tgt == 'signatureRadius' or re.fullmatch(r'shield\w+DamageResonance', tgt): continue
            if (op, tgt) != ('boost', 'maxVelocity') or srcAttr not in FIGHTER_SPEED_BONUS: raise AssertionError(f'Effect{e}: {op} {tgt} by {srcAttr} -- model it')
            if tgt == 'maxVelocity': out.setdefault(str(e), []).append(['maxVelocity', 'boost', attrId[srcAttr], 'default'])
    if sorted(out) != sorted(str(e) for e in FIGHTER_ABILITY_IDS if ename(e) in ('fighterAbilityMicroWarpDrive', 'fighterAbilityAfterburner', 'fighterAbilityEvasiveManeuvers')):
        raise AssertionError(f'fighter speed abilities changed: {out}')
    return out

def fighter_filter(lam):
    REC.clear(); hits = []
    for t in fighterReps:
        try:
            if lam(Probe(t)): hits.append(t)
        except Exception: pass
    rec = sorted(set(REC))
    if any(x[0] == 'skill?' for x in rec): raise AssertionError('filter tests the carrying skill -- pass carrier=')
    sk = sorted({skillId[x[1]] for x in rec if x[0] == 'skill' and x[1] in skillId}); gs = sorted({x[1] for x in rec if x[0] == 'eq'})
    calc = [t for t in fighterReps if (not sk or any(x in reqs(t) for x in sk)) and (not gs or gname(t) in gs)]
    if set(calc) != set(hits): raise AssertionError(f'fighter filter not expressible as skills AND groups ({sk}, {gs})')
    return sk or None, gs or None, hits

def build_fighters():
    table, skillRows, byCtx, skipped = {}, [], {}, collections.Counter()
    for eid in sorted(carriers):
        if eid not in EFFECTS: continue
        for ctx in sorted({ctx_of(t) for t in carriers[eid]} - {None}):
            skillCarriers = sorted(t for t in carriers[eid] if ctx_of(t) == 'skill') if ctx == 'skill' else [None]
            for carrier in skillCarriers:
                def ev(coll, meth, a):
                    if not (coll == 'fighters' and a and callable(a[0])): return None
                    try: return fighter_filter(a[0])
                    except AssertionError as ex: return ('ERR', str(ex))
                calls, err = run(eid, ctx, ev, carrier=carrier, rich=True)
                if err: continue
                for coll, meth, a, kw in calls:
                    if coll != 'fighters' or len(a) < 3 or str(a[1]) not in FIGHTER_ATTRS: continue
                    e = kw.get('_eval')
                    if e is None: raise AssertionError(f'effect {eid}: unfiltered fighter call')
                    if e[0] == 'ERR': raise AssertionError(f'effect {eid}: {e[1]}')
                    sk, gs, hits = e
                    if not hits: continue
                    if 'Charge' in meth: raise AssertionError(f'effect {eid}: fighter charge call')
                    if 'pyfa_effects.Any' in repr(a[2]): raise AssertionError(f'effect {eid}: pilot-dependent value on a fighter -- model it')
                    src, lvl = value(a[2])
                    if kw.get('skill'): lvl = 5
                    op = opname(re.sub(r'^filteredItem', '', meth) + 'ItemAttr')
                    if ctx == 'skill':
                        v = {aname(x['attributeID']): x['value'] for x in td.get(str(carrier), {}).get('dogmaAttributes', [])}.get(src, DEFAULT.get(src, 0.0)) * lvl
                        row = [carrier, str(a[1]), op, v, penalty(kw), sk, gs]
                        if row not in skillRows: skillRows.append(row)
                        continue
                    row = [str(a[1]), op, attrId[src], lvl, DEFAULT.get(src, 0.0), penalty(kw), sk, gs]
                    key = f'{ctx}:{eid}' if ctx in ('implant', 'booster') else str(eid)
                    byCtx.setdefault((key, ctx), [])
                    if row not in byCtx[(key, ctx)]: byCtx[(key, ctx)].append(row)
                    rows = table.setdefault(key, [])
                    if row not in rows: rows.append(row)
    # every handler that touches one of the attributes on fit.fighters must have been recorded (no silent miss)
    recorded = {int(k.split(':')[-1]) for k in table} | {e for e in carriers if any(r[0] in carriers[e] for r in skillRows)}
    src = open(os.path.join(PYFA_SRC, 'eos', 'effects.py')).read()
    pat = re.compile(r"fit\.fighters\.filtered\w+\((?:[^()]|\([^()]*\))*?'(" + '|'.join(FIGHTER_ATTRS) + r")'", re.S)
    for m in re.finditer(r'\nclass Effect(\d+)\(BaseEffect\):(.*?)(?=\nclass |\Z)', src, flags=re.S):
        eid, body = int(m.group(1)), m.group(2)
        if eid in recorded: continue
        if not ({ctx_of(t) for t in carriers.get(eid, ())} - {None}):
            # e.g. Effect8114 systemPlasmaStorm (a wormhole / environment effect on fighter explosion radius): no hull,
            # module, skill, implant or booster carries it, and the tool models no system effects (DEVIATIONS.md)
            if re.search(r"fit\.fighters", body): skipped[f'environment effect, no fit carrier: Effect{eid} {ename(eid)}'] += 1
            continue
        loops = re.search(r"for attr in \(([^()]*)\):\s*fit\.fighters", body, re.S)
        if loops and any(f"'{a}'" in loops.group(0) for a in FIGHTER_ATTRS): raise AssertionError(f'Effect{eid} loops over a fighter attribute but was not recorded')
        if not pat.search(body): continue
        if eid not in carriers: skipped[f'no SDE carrier: Effect{eid}'] += 1; continue
        for ctx in sorted({ctx_of(t) for t in carriers[eid]} - {None}):
            calls, err = run(eid, ctx, None, carrier=next((t for t in sorted(carriers[eid]) if ctx_of(t) == 'skill'), None) if ctx == 'skill' else None, rich=True)
            if err: raise AssertionError(f'Effect{eid} touches a fighter attribute but the recorder could not run it: {err}')
        skipped[f'touches a fighter attribute, no damage fighter passes its filter: Effect{eid} {ename(eid)}'] += 1
    for eid in {e for e, _ in byCtx}:
        variants = {json.dumps(r) for (e, c), r in byCtx.items() if e == eid}
        if len(variants) > 1: raise AssertionError(f"effect {eid}: fighter rows differ by context: {variants}")
    # The squadron's own default abilities (pyfa Fighter.__init__) run no handler: a damage ability effect has none, and
    # the MWD / afterburner / evasive abilities that change maxVelocity are off by default (eos/saveddata/fighter.py).
    for t in dmgFighters:
        for e in td.get(str(t), {}).get('dogmaEffects', []):
            cls = EFFECTS.get(e['effectID'])
            if cls is not None and getattr(cls, 'dealsDamage', False) and 'handler' in vars(cls):
                raise AssertionError(f'damage ability Effect{e["effectID"]} has its own handler -- model it')
    return dict(sorted(table.items(), key=lambda kv: (int(kv[0].split(':')[-1]), kv[0]))), sorted(skillRows), skipped

if __name__ == '__main__':
    table, ctxs, skipped = build()
    print(f'PROJ_TARGET_EFFECTS: {len(table)} effects, {sum(map(len, table.values()))} rows')
    for e, rows in table.items(): print(' ', e, ename(int(e)), ctxs[e], rows)
    for k, v in sorted(skipped.items()): print('  skipped:', k)
    dtable, dskill, dskipped = build_drones()
    print(f'PROJ_DRONE_EFFECTS: {len(dtable)} effects, {sum(map(len, dtable.values()))} rows; PROJ_DRONE_SKILL_ROWS: {len(dskill)} (over {len(projDrones)} web / painter / damage drones)')
    for e, rows in dtable.items(): print(' ', e, ename(int(e.split(':')[-1])), rows)
    for r in dskill: print('  skill', name(r[0]), r[1:])
    for k, v in sorted(dskipped.items()): print('  skipped:', k)
    ftable, fskill, fskipped = build_fighters()
    print(f'PROJ_FIGHTER_EFFECTS: {len(ftable)} effects, {sum(map(len, ftable.values()))} rows; PROJ_FIGHTER_SKILL_ROWS: {len(fskill)} (over {len(dmgFighters)} damage fighters)')
    for e, rows in ftable.items(): print(' ', e, ename(int(e.split(':')[-1])), rows)
    for r in fskill: print('  skill', name(r[0]), r[1:])
    for k, v in sorted(fskipped.items()): print('  skipped:', k)
    html = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'index.html'))
    s = open(html, encoding='utf-8').read()
    new = {'PROJ_TARGET_EFFECTS': table, 'PROJ_TARGET_ATTRS': {n: attrId[n] for n in ATTRS},
           'PROJ_TARGET_DEFAULTS': {str(attrId[n]): DEFAULT.get(n, 0.0) for n in ATTRS},
           'PROJ_DRONE_EFFECTS': dtable, 'PROJ_DRONE_SKILL_ROWS': dskill, 'PROJ_DRONE_ATTRS': {n: attrId[n] for n in DRONE_ATTRS},
           'PROJ_DRONE_DEFAULTS': {str(attrId[n]): DEFAULT.get(n, 0.0) for n in DRONE_ATTRS},
           'PROJ_FIGHTER_EFFECTS': ftable, 'PROJ_FIGHTER_SKILL_ROWS': fskill, 'PROJ_FIGHTER_ATTRS': {n: attrId[n] for n in FIGHTER_ATTRS},
           'PROJ_FIGHTER_DEFAULTS': {str(attrId[n]): DEFAULT.get(n, 0.0) for n in FIGHTER_ATTRS},
           'PROJ_FIGHTER_ABILITY_PREFIX': FIGHTER_ABILITY_PREFIX, 'PROJ_FIGHTER_SELF_EFFECTS': build_fighter_self()}
    changed = False
    for k, v in new.items():
        m = re.search(r'const ' + k + r' = (.*?);\n', s)
        if not m: print(f'{k}: not in {html}'); changed = True; continue
        if json.loads(m.group(1)) != v:
            changed = True
            if '--write' in sys.argv: s = s[:m.start(1)] + json.dumps(v, separators=(',', ':')) + s[m.end(1):]
    if '--write' in sys.argv and changed:
        open(html, 'w', encoding='utf-8').write(s); print('index.html table written.')
    else:
        print('index.html table differs from this pyfa/SDE -- run with --write.' if changed else 'index.html table is up to date with this pyfa/SDE.')
