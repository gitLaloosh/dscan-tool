"""Projected webs / painters / scrams (PYFA CORE projected, v2026.10.14.35; roadmap/turret-application-plan.md Phase 2a).

    PYFA_SRC=... python3 -I tools/independent_checks/check_projected.py [index.html]   -> 'N mismatches'

pyfa's damage graph applies the attacker's own webs, target painters, web / painter drones and warp scramblers
to the target by default (graph setting applyProjected). This check runs pyfa's files UNMODIFIED:
  graphs/data/fitDamageStats/calc/projected.py   getScramRange, getScrammables, getTackledSpeed, getSigRadiusMult
  graphs/data/fitDamageStats/cache/projected.py  ProjectedDataCache (what each web / painter / drone contributes)
  eos/modifiedAttributeDict.py getResistanceAttrID (lifted by ast), eos/calc.py, eos/utils/float.py, graphs/calc.py
on pyfa's own attribute values for both fits -- tools/pyfa_fit_oracle.py runs pyfa's handlers on the golden fit
with the tool's resolved module states and drones in space (inputs, as compare_fit_stats.py does); the target's
speed and signature radius with extra multipliers and without the scrammed modules come from the oracle's port of
getExtended / __calculateValue (pyfa_fit_oracle.Attrs.extended). The tool's side is its PYFA CORE projected
functions on its own estimate.application.projected and estimate.projectedTarget (projected_grid.mjs).
Compared for every attacker that has a web, painter, web / painter drone or scram (and every golden fit as the
target), over a grid of distance x the target's own speed (share of its top speed) x graph settings (lock range
respected or not, drone control range ignored or not, mobile drone mode):
  * the attacker's inputs (pyfa's webMods / tpMods / webDrones / tpDrones / webFighters / tpFighters and getScramRange);
    since v2026.10.14.70 the oracle launches the squadrons the tool launched, with the abilities the tool has on
    (estimate.fighterStates: inputs), so a support squadron's web (getProjFighterData) is compared too;
  * the target's untackled top speed and signature radius;
  * at every point, the tackled speed and the painted signature radius.
Tolerance 1e-6 relative (floatUnerr keeps 7 significant digits).
"""
import sys, os, re, ast, json, subprocess, tempfile, itertools, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from pyfa_sde import PYFA_SRC, ename, effs
from pyfa_fit_oracle import EFFECTS
from golden_oracle import oracle_for, GOLDEN

# ---- pyfa's own code ----------------------------------------------------------------------------------------
SETTINGS = {'mobileDroneMode': 1, 'ignoreDCR': False, 'ignoreResists': True, 'ignoreLockRange': True, 'applyProjected': True}
class GraphSettings:
    @classmethod
    def getInstance(cls): return cls
    @classmethod
    def get(cls, k): return SETTINGS[k]
def _exec(rel, ns, drop=()):
    src = open(os.path.join(PYFA_SRC, rel), encoding='utf-8').read()
    for pat in drop: src = re.sub(pat, '', src, flags=re.M)
    exec(compile(src, rel, 'exec'), ns)
    return ns
def _lift(rel, fname, ns):
    src = open(os.path.join(PYFA_SRC, rel), encoding='utf-8').read()
    node = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == fname)
    exec(compile(ast.Module(body=[node], type_ignores=[]), rel, 'exec'), ns)
    return ns[fname]
_float = _exec('eos/utils/float.py', {})
_calc = _exec('eos/calc.py', {})
_sconst = _exec('service/const.py', {})
_gcalc = _exec('graphs/calc.py', {'GraphSettings': GraphSettings}, drop=[r'^from service\.settings import .*$'])
PROJ = _exec('graphs/data/fitDamageStats/calc/projected.py', {
    'calculateRangeFactor': _calc['calculateRangeFactor'], 'floatUnerr': _float['floatUnerr'], 'checkLockRange': _gcalc['checkLockRange'],
    'checkDroneControlRange': _gcalc['checkDroneControlRange'], 'GraphDpsDroneMode': _sconst['GraphDpsDroneMode'], 'GraphSettings': GraphSettings},
    drop=[r'^from (eos|graphs|service)\.\S+ import .*$', r'^import math$'])
PROJ['math'] = __import__('math')
getResistanceAttrID = _lift('eos/modifiedAttributeDict.py', 'getResistanceAttrID', {'resistanceCache': {}})
class FitDataCache:   # graphs/data/base: a per-fit dict
    def __init__(s): s._data = {}
CACHE = _exec('graphs/data/fitDamageStats/cache/projected.py', {'getResistanceAttrID': getResistanceAttrID, 'FitDataCache': FitDataCache},
              drop=[r'^from (eos|graphs)\.\S+ import .*$'])
ProjectedDataCache = CACHE['ProjectedDataCache']
DroneMode = _sconst['GraphDpsDroneMode']

# ---- pyfa-shaped fits over the oracle -------------------------------------------------------------------------
class _Eff:
    """eos.gamedata.Effect: resistanceID (SDE resistanceAttributeID) and getattr() of the handler class."""
    def __init__(s, eid): s.ID = eid; s.name = ename(eid); s.resistanceID = effs.get(str(eid), {}).get('resistanceAttributeID'); s.type = getattr(EFFECTS.get(eid), 'type', None)
    def getattr(s, k): return getattr(EFFECTS.get(s.ID), k, None)
class _G:
    def __init__(s, n): s.name = n
class _I:
    def __init__(s, gi): s.ID = int(gi.ID); s.name = gi.name; s.group = _G(gi.group.name); s.effects = {ename(e): _Eff(e) for e in gi.effectIds}
class _Owner:
    def __init__(s, o): s.ship = _Attr(o.ship)
class _Attr:
    def __init__(s, it): s.it = it
    def getModifiedItemAttr(s, k, default=0):
        v = s.it.get(k); return v if v is not None else default
class _Mod(_Attr):
    """eos Module: item / charge effects, modified attributes, maxRange and falloff (eos/saveddata/module.py)."""
    def __init__(s, m, o):
        super().__init__(m); s.m = m; s.owner = _Owner(o)
        s.item = _I(m.item); s.charge = _I(m.charge.item) if m.charge is not None else None
    @property
    def maxRange(s):
        for a in ("maxRange", "shieldTransferRange", "powerTransferRange", "energyDestabilizationRange", "empFieldRange",
                  "ecmBurstRange", "warpScrambleRange", "cargoScanRange", "shipScanRange", "surveyScanRange"):
            v = s.getModifiedItemAttr(a)
            if v:
                if 'burst projector' in s.item.name.lower(): v -= s.owner.ship.getModifiedItemAttr("radius")
                return v
        return None
    @property
    def falloff(s):
        for a in ("falloffEffectiveness", "falloff", "shipScanFalloff"):
            v = s.getModifiedItemAttr(a)
            if v: return v
class _Drone(_Attr):
    """eos Drone: amountActive, maxRange and falloff (eos/saveddata/drone.py)."""
    def __init__(s, d):
        super().__init__(d); s.item = _I(d.item); s.amountActive = d.amountActive; s.charge = None
    @property
    def maxRange(s):
        for a in ("shieldTransferRange", "powerTransferRange", "energyDestabilizationRange", "empFieldRange", "ecmBurstRange", "maxRange", "ECMRangeOptimal"):
            v = s.getModifiedItemAttr(a)
            if v: return v
    @property
    def falloff(s):
        for a in ("falloff", "falloffEffectiveness"):
            v = s.getModifiedItemAttr(a)
            if v: return v
class _Ability:
    """eos FighterAbility: its effect (name, resistanceID, prefix via getattr)."""
    def __init__(s, eid): s.effect = _Eff(eid)
class _Fighter(_Attr):
    """eos Fighter (one squadron): amount, its item's effects, modified attributes."""
    def __init__(s, fi):
        super().__init__(fi); s.item = _I(fi.item); s.amount = fi.amount; s.active = sorted(fi.activeAbilities)
class _FitItem:
    def __init__(s, o):
        s.o = o; s.ID = id(o)
        s.mods = [_Mod(m, o) for m in o.modules if m.state >= 2]
        s.drones = [_Drone(d) for d in o.drones if d.amountActive > 0]
        s.fighters = [_Fighter(fi) for fi in o.fighters]
        s.ship = _Attr(o.ship)
        s.maxTargetRange = o.ship.get('maxTargetRange')
        s.extraAttributes = {'droneControlRange': o.ship.get('droneControlRange')}
    def activeModulesIter(s): return iter(s.mods)
    def activeDronesIter(s): return iter(s.drones)
    def activeFighterAbilityIter(s):
        # eos Fit.activeFighterAbilityIter: every ability switched on of every squadron in space (v2026.10.14.70: the
        # tool's launch and abilities, its fighterStates, are inputs here as in check_application.py)
        for fi in s.fighters:
            for e in fi.active: yield fi, _Ability(e)
class _Fit:
    """graphs/wrapper.py SourceWrapper / TargetWrapper over an oracle fit."""
    isFit = True; isProfile = False
    def __init__(s, o): s.o = o; s.item = _FitItem(o)
    def getRadius(s): return s.o.ship.get('radius')
    def getMaxVelocity(s, extraMultipliers=None, ignoreAfflictors=()):
        if extraMultipliers or ignoreAfflictors: return s.o.ship.attrs.extended('maxVelocity', extraMultipliers, [a.m for a in ignoreAfflictors])
        return s.o.ship.get('maxVelocity')
    def getSigRadius(s, extraMultipliers=None, ignoreAfflictors=()):
        if extraMultipliers or ignoreAfflictors: return s.o.ship.attrs.extended('signatureRadius', extraMultipliers, [a.m for a in ignoreAfflictors])
        return s.o.ship.get('signatureRadius')

def pyfa_inputs(src):
    cache = ProjectedDataCache()
    webMods, tpMods = cache.getProjModData(src); webDrones, tpDrones = cache.getProjDroneData(src); webFighters, tpFighters = cache.getProjFighterData(src)
    return {'scramRange': PROJ['getScramRange'](src), 'webMods': webMods, 'tpMods': tpMods, 'webDrones': webDrones, 'tpDrones': tpDrones,
            'webFighters': webFighters, 'tpFighters': tpFighters}

def pyfa_point(src, tgt, inp, p):
    """getter.py _calculatePoint with applyProjected on: tackled speed, then the signature radius at that speed."""
    SETTINGS.update(ignoreLockRange=p['ignoreLockRange'], ignoreDCR=p['ignoreDCR'], mobileDroneMode=DroneMode(p['droneMode']))
    scrammables = PROJ['getScrammables'](tgt=tgt)
    d = p['distance']; cur = p['speedFrac'] * tgt.getMaxVelocity()
    speed = PROJ['getTackledSpeed'](src=src, tgt=tgt, currentUntackledSpeed=cur, srcScramRange=inp['scramRange'], tgtScrammables=scrammables,
                                    webMods=inp['webMods'], webDrones=inp['webDrones'], webFighters=inp['webFighters'], distance=d)
    sig = tgt.getSigRadius() * PROJ['getSigRadiusMult'](src=src, tgt=tgt, tgtSpeed=speed, srcScramRange=inp['scramRange'], tgtScrammables=scrammables,
                                                         tpMods=inp['tpMods'], tpDrones=inp['tpDrones'], tpFighters=inp['tpFighters'], distance=d)
    return speed, sig

GRID = [dict(distance=d, speedFrac=f, ignoreLockRange=il, ignoreDCR=idcr, droneMode=dm)
        for d, f, (il, idcr, dm) in itertools.product(
            [0, 1500, 5000, 9000, 10000, 12000, 13400, 16000, 20000, 30000, 45000, 80000, 150000],   # 13400: inside a Berserker SW-900 optimal only from the drone itself (optimal - attacker radius + drone radius)
            [0, 0.35, 1],
            [(True, False, 1), (False, False, 1), (True, True, 3), (True, False, 2)])]

def close(a, b):
    if a is None or b is None: return a == b
    return abs(a - b) <= 1e-6 * max(1.0, abs(a), abs(b))
def key_of(x, mobile):
    t = (round(x[0], 9), round(x[1], 6), round(x[2], 6), x[3], x[4])
    return t + ((round(x[5], 6), round(x[6], 6)) if mobile else ())

def tool_states(t):
    ms = (t.get('moduleStates') or {}).get('items') or []
    states = {str(it['typeId']): {'active': round(it['active']), 'online': round(it['online']), 'offline': round(it['offline'])} for it in ms}
    drones = [(it['typeId'], round(it['active'])) for it in ((t.get('droneStates') or {}).get('items') or []) if round(it['active']) > 0]
    return states, drones

def tool_fighters(t):
    """[(typeId, squadron size, active ability ids)] per squadron the tool launched (estimate.fighterStates: damage AND
    support squadrons, v2026.10.14.70)."""
    out = []
    for it in ((t.get('fighterStates') or {}).get('items') or []):
        out += [(it['typeId'], it['squadronSize'], [a['effectId'] for a in it.get('abilities') or [] if a.get('on')])] * int(it.get('active') or 0)
    return out

if __name__ == '__main__':
    ROOT = os.path.join(HERE, '..', '..')
    html = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
    G = json.load(open(GOLDEN))
    tmp = tempfile.mkdtemp(); dump = os.path.join(tmp, 'd.json')
    subprocess.run(['node', os.path.join(ROOT, 'regression_suite', 'dump_results.mjs'), html, dump, 'application,projectedTarget,moduleStates,droneStates,fighterStates', '-', ','.join(G)], check=True, stdout=subprocess.DEVNULL)
    tool = json.load(open(dump))
    fits = {}
    def fit(k):
        if k not in fits:
            states, drones = tool_states(tool[k])
            fits[k] = _Fit(oracle_for(k, states=states, drones=drones, group_limits=False, fighters=tool_fighters(tool[k])))
        return fits[k]
    bad, notes = 0, []
    # attackers: every fit the tool OR pyfa sees a web / painter / web drone / scram on
    attackers, inputs = [], {}
    for k in G:
        o = fit(k).o
        if o.errors or o.oracleGaps: notes.append(f'{k}: ORACLE errors {o.errors} gaps {o.oracleGaps}'); bad += 1; continue
        inp = pyfa_inputs(fit(k)); inputs[k] = inp
        tp = ((tool[k].get('application') or {}).get('projected')) or {}
        has_pyfa = inp['scramRange'] is not None or any(inp[x] for x in ('webMods', 'tpMods', 'webDrones', 'tpDrones', 'webFighters', 'tpFighters'))
        has_tool = tp.get('scramRange') is not None or any(tp.get(x) for x in ('webMods', 'tpMods', 'webDrones', 'tpDrones', 'webFighters', 'tpFighters'))
        if not (has_pyfa or has_tool): continue
        attackers.append(k)
        diffs = []
        if not close(tp.get('scramRange'), inp['scramRange']): diffs.append(f"scramRange tool {tp.get('scramRange')} pyfa {inp['scramRange']}")
        if not close((tool[k].get('application') or {}).get('lockRange') or 0, fit(k).item.maxTargetRange): diffs.append('lockRange')
        if not close(tp.get('droneControlRange') or 0, fit(k).item.extraAttributes['droneControlRange']): diffs.append(f"droneControlRange tool {tp.get('droneControlRange')} pyfa {fit(k).item.extraAttributes['droneControlRange']}")
        for name, mobile in (('webMods', 0), ('tpMods', 0), ('webDrones', 1), ('tpDrones', 1), ('webFighters', 1), ('tpFighters', 1)):
            pk = sorted(key_of(tuple(x), mobile) for x in inp[name])
            tk = sorted(key_of((x['boost'], x['optimal'], x['falloff'], x['stackingGroup'], x['resAttrID']) + ((x['speed'], x['radius']) if mobile else ()), mobile) for x in tp.get(name) or [])
            if pk != tk: diffs.append(f'{name} tool {tk} pyfa {pk}')
        if diffs: bad += 1; notes.append(f'{k} (attacker inputs): ' + '; '.join(diffs))
    targets = [k for k in G if tool[k].get('projectedTarget')]
    missing = [k for k in G if not tool[k].get('projectedTarget')]
    if missing: notes.append(f'no projectedTarget (hull record without effects): {missing}')
    pairs = [(a, t) for a in attackers for t in targets if a in inputs and t in inputs]
    gin, gout = os.path.join(tmp, 'in.json'), os.path.join(tmp, 'out.json')
    json.dump({'apps': {a: tool[a]['application'] for a in attackers}, 'targets': {t: tool[t]['projectedTarget'] for t in targets},
               'pairs': pairs, 'grid': GRID}, open(gin, 'w'))
    subprocess.run(['node', os.path.join(HERE, 'projected_grid.mjs'), html, gin, gout], check=True)
    out = json.load(open(gout))
    for t in targets:
        tv, ts = out['targets'][t]
        pv, ps = fit(t).getMaxVelocity(), fit(t).getSigRadius()
        if not (close(tv, pv) and close(ts, ps)): bad += 1; notes.append(f'{t} (target): maxVelocity tool {tv} pyfa {pv}; signatureRadius tool {ts} pyfa {ps}')
    points = exact = changed = 0
    for a, t in pairs:
        src, tgt, inp = fit(a), fit(t), inputs[a]
        tp = out['points'][a + '|' + t]
        diffs = []
        for i, p in enumerate(GRID):
            ps, pg = pyfa_point(src, tgt, inp, p); points += 1
            ts, tg = tp[i]
            if not (close(ts, ps) and close(tg, pg)):
                if len(diffs) < 4: diffs.append(f'{p} speed tool {ts} pyfa {ps}; sig tool {tg} pyfa {pg}')
            elif ts == ps and tg == pg: exact += 1
            if ps != p['speedFrac'] * tgt.getMaxVelocity() or pg != tgt.getSigRadius(): changed += 1
        if diffs: bad += 1; notes.append(f'{a} -> {t}: ' + '; '.join(diffs))
    for n in notes[:40]: print(n)
    print(f'{len(attackers)} attackers x {len(targets)} targets, {points} points ({changed} where pyfa changes speed or signature), {exact} bit-identical')
    print(f'{bad} mismatches (attacker inputs, targets and pairs vs pyfa calc/projected.py, grid of {len(GRID)})')
