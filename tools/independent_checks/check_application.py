"""Damage application (PYFA CORE application, v2026.10.14.34; roadmap/turret-application-plan.md Phase 1).

    PYFA_SRC=... python3 -I tools/independent_checks/check_application.py [index.html]   -> 'N mismatches'

pyfa's damage graph decides how much of each weapon's DPS lands: graphs/data/fitDamageStats/calc/application.py
(getApplicationPerKey and the per-weapon functions), eos/calc.py calculateRangeFactor and eos/utils/float.py
floatUnerr. This check runs those files UNMODIFIED (their eos / graphs / service imports are replaced by the
same pyfa files where they are plain Python, and by a stand-in for GraphSettings) on pyfa's own numbers for
every golden fit: the attributes and per-module DPS come from tools/pyfa_fit_oracle.py (pyfa's handlers), not
from the tool. The tool's side is its PYFA CORE application functions on its own estimate.application
(tools/independent_checks/application_grid.mjs). Compared, at every point of a grid of distance x both ships'
speeds and headings x target signature x lock range respected or ignored:
  * each weapon's multiplier (keyed weaponTypeId:chargeTypeId, identical weapons alike);
  * the applied DPS of the whole fit (sum of DPS x multiplier);
  * the inputs the multipliers don't cover: the attacker's radius and lock range.
Since v2026.10.14.40 also drones in space (getDroneMult; the fit's own resolved module states and drones, as
compare_fit_stats.py), with every drone input (DPS, maxVelocity, radius, Drone.maxRange / falloff, trackingSpeed,
optimalSigRadius) and a second grid for drone fits that also varies ignoreDCR and mobileDroneMode. Fighters are
left out on both sides (not ported yet). Tolerance 1e-6 relative (floatUnerr keeps
7 significant digits, so a value on a rounding edge may differ by one in the 7th digit).

It also exposes applied(fitId, **params) for writing golden pins from pyfa's side.
"""
import sys, os, re, json, math, subprocess, tempfile, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from pyfa_sde import PYFA_SRC, ename
from golden_oracle import oracle_for, GOLDEN
from compare_implants import is_weapon, _mult, DMG
from check_missile_range import pyfa_missile_range

# ---- pyfa's own code ----------------------------------------------------------------------------------------
SETTINGS = {'mobileDroneMode': 1, 'ignoreDCR': False, 'ignoreResists': True, 'ignoreLockRange': True, 'applyProjected': True}
class GraphSettings:   # service/settings.py stand-in: only .get() of the graph settings is used
    @classmethod
    def getInstance(cls): return cls
    @classmethod
    def get(cls, k): return SETTINGS[k]
class Attribute:       # used only for fighter resists (fighters are not checked)
    @classmethod
    def getInstance(cls): return None

def _exec(rel, ns, drop=()):
    src = open(os.path.join(PYFA_SRC, rel), encoding='utf-8').read()
    for pat in drop: src = re.sub(pat, '', src, flags=re.M)
    exec(compile(src, rel, 'exec'), ns)
    return ns
_float = _exec('eos/utils/float.py', {})
_calc = _exec('eos/calc.py', {})
_const = _exec('eos/const.py', {})
_sconst = _exec('service/const.py', {})
_gcalc = _exec('graphs/calc.py', {'GraphSettings': GraphSettings}, drop=[r'^from service\.settings import .*$'])
APP = _exec('graphs/data/fitDamageStats/calc/application.py', {
    'calculateRangeFactor': _calc['calculateRangeFactor'], 'FittingHardpoint': _const['FittingHardpoint'],
    'floatUnerr': _float['floatUnerr'], 'checkLockRange': _gcalc['checkLockRange'], 'checkDroneControlRange': _gcalc['checkDroneControlRange'],
    'Attribute': Attribute, 'GraphDpsDroneMode': _sconst['GraphDpsDroneMode'], 'GraphSettings': GraphSettings},
    drop=[r'^from (eos|graphs|service)\.\S+ import .*$'])
getApplicationPerKey = APP['getApplicationPerKey']
DroneMode = _sconst['GraphDpsDroneMode']
FH = _const['FittingHardpoint']

# ---- a pyfa-shaped fit from the oracle ----------------------------------------------------------------------
class _G:
    def __init__(s, n): s.name = n
class _I:
    def __init__(s, gi): s.ID = int(gi.ID); s.group = _G(gi.group.name); s.effects = {ename(e): None for e in gi.effectIds}
class _Mod:
    """The parts of eos Module the application functions read, over an oracle module (pyfa's handlers)."""
    def __init__(s, o, m, dps):
        s.m, s._dps = m, dps
        s.item = _I(m.item); s.charge = _I(m.charge.item) if m.charge is not None else None
        s.hardpoint = FH.TURRET if 'turretFitted' in s.item.effects else (FH.MISSILE if 'launcherFitted' in s.item.effects else FH.NONE)
        mr = pyfa_missile_range(o, m) if m.charge is not None else None
        s.missileMaxRangeData = tuple(mr[:3]) if mr else None
        s.isBreacher = False
        s.key = f'{s.item.ID}:{s.charge.ID if s.charge else ""}'
    def isDealingDamage(s): return s._dps > 0
    def getModifiedItemAttr(s, k, default=0): return s.m.getModifiedItemAttr(k, default)
    def getModifiedChargeAttr(s, k, default=0): return s.m.getModifiedChargeAttr(k, default)
    @property
    def maxRange(s):   # eos/saveddata/module.py Module.maxRange
        for a in ("maxRange", "shieldTransferRange", "powerTransferRange", "energyDestabilizationRange", "empFieldRange",
                  "ecmBurstRange", "warpScrambleRange", "cargoScanRange", "shipScanRange", "surveyScanRange"):
            v = s.getModifiedItemAttr(a)
            if v:
                return v
        if s.missileMaxRangeData is None: return None
        lo, hi, ch = s.missileMaxRangeData
        return lo * (1 - ch) + hi * ch
    @property
    def falloff(s):    # Module.falloff
        for a in ("falloffEffectiveness", "falloff", "shipScanFalloff"):
            v = s.getModifiedItemAttr(a)
            if v: return v

def module_dps(m):
    """Per-module DPS as compare_implants.oracle_values sums it (pyfa getDps, spool at max)."""
    g = m.item.group.name
    cyc = max(m.get('speed') or 0, m.get('duration') or 0) / 1000
    if not cyc: return 0
    if m.charge is not None and is_weapon(g):
        spool = (m.get('damageMultiplierBonusMax') or 0) if (m.get('damageMultiplierBonusPerCycle') or 0) else 0
        return sum(m.charge.get(a) or 0 for a in DMG) * _mult(m) * (1 + spool) / cyc
    if g == 'Smart Bomb':
        return sum(m.get(a) or 0 for a in DMG) / cyc
    return 0

def drone_dps(d):
    """pyfa Drone.getDps for the stack in space (as compare_implants.oracle_values sums it)."""
    cyc = (d.get('speed') or d.get('duration') or 0) / 1000
    return sum(d.get(a) or 0 for a in DMG) * _mult(d) * d.amountActive / cyc if cyc else 0
class _DroneApp:
    """eos Drone as getDroneMult reads it: modified attributes, Drone.maxRange, Drone.falloff (v2026.10.14.40)."""
    def __init__(s, d):
        s.d, s._dps = d, drone_dps(d); s.key = f'drone:{int(d.item.ID)}'
    def isDealingDamage(s): return s._dps > 0
    def getModifiedItemAttr(s, k, default=0):
        v = s.d.get(k); return v if v is not None else default
    @property
    def maxRange(s):   # eos/saveddata/drone.py Drone.maxRange
        for a in ("shieldTransferRange", "powerTransferRange", "energyDestabilizationRange", "empFieldRange", "ecmBurstRange", "maxRange", "ECMRangeOptimal"):
            v = s.getModifiedItemAttr(a)
            if v: return v
    @property
    def falloff(s):    # Drone.falloff
        for a in ("falloff", "falloffEffectiveness"):
            v = s.getModifiedItemAttr(a)
            if v: return v
class _Src:
    def __init__(s, o):
        s.o = o
        s.mods = [_Mod(o, m, module_dps(m)) for m in o.modules if m.state >= 2 and module_dps(m) > 0]
        s.drones = [_DroneApp(d) for d in o.drones if d.amountActive > 0 and drone_dps(d) > 0]   # v2026.10.14.40 (D5 drones)
        class _It: pass
        s.item = _It(); s.item.activeModulesIter = lambda: iter(s.mods); s.item.activeDronesIter = lambda: iter(s.drones)
        s.item.activeFightersIter = lambda: iter(()); s.item.maxTargetRange = o.ship.get('maxTargetRange')
        s.item.extraAttributes = {'droneControlRange': o.ship.get('droneControlRange') or 0}
        s.isFit = True
    def getRadius(s): return s.o.ship.get('radius')
class _Tgt:
    def __init__(s, r): s.r = r; s.isFit = False; s.isProfile = True
    def getRadius(s): return s.r

def pyfa_point(src, p):
    SETTINGS['ignoreLockRange'] = p['ignoreLockRange']
    SETTINGS['ignoreDCR'] = p.get('ignoreDCR', False); SETTINGS['mobileDroneMode'] = DroneMode(p.get('droneMode', 1))
    am = getApplicationPerKey(src=src, tgt=_Tgt(p['tgtRadius']), atkSpeed=p['atkSpeed'], atkAngle=p['atkAngle'], distance=p['distance'],
                              tgtSpeed=p['tgtSpeed'], tgtAngle=p['tgtAngle'], tgtSigRadius=p['tgtSigRadius'])
    mults = {}
    for mod, v in am.items(): mults.setdefault(mod.key, v)
    return mults, sum(mod._dps * am.get(mod, 0) for mod in src.mods) + sum(d._dps * am.get(d, 0) for d in src.drones)

def applied(fitId, **p):
    """pyfa's applied DPS for a golden fit at one point (for golden pins). Defaults: pyfa's graph defaults."""
    q = dict(distance=0, atkSpeed=0, atkAngle=0, tgtSpeed=0, tgtAngle=0, tgtSigRadius=40, tgtRadius=50, ignoreLockRange=True); q.update(p)
    return pyfa_point(_Src(oracle_for(fitId)), q)

GRID = [dict(distance=d, atkSpeed=a, atkAngle=aa, tgtSpeed=ts, tgtAngle=ta, tgtSigRadius=sig, tgtRadius=40, ignoreLockRange=il)
        for d, a, aa, ts, ta, sig, il in itertools.product([0, 1000, 5000, 10000, 20000, 30000, 50000, 80000, 150000, 300000], [0, 250], [0, 90],
                                                          [0, 150, 500, 1500, 4000], [0, 45, 90], [25, 40, 120, 400, 2000], [True, False])]

def close(a, b): return abs(a - b) <= 1e-6 * max(1.0, abs(a), abs(b))

DGRID = [dict(distance=d, atkSpeed=a, atkAngle=90, tgtSpeed=ts, tgtAngle=ta, tgtSigRadius=sig, tgtRadius=40, ignoreLockRange=il, ignoreDCR=dcr, droneMode=dm)
         for d, a, ts, ta, sig, il, dcr, dm in itertools.product([0, 5000, 15000, 30000, 45000, 60000, 70000, 90000, 150000], [0, 500, 3000],
                                                                [0, 500, 1500, 3000, 6000], [0, 90], [40, 400], [True, False], [False, True], [1, 2, 3])]

def tool_states(t):
    ms = (t.get('moduleStates') or {}).get('items') or []
    states = {str(it['typeId']): {'active': round(it['active']), 'online': round(it['online']), 'offline': round(it['offline'])} for it in ms}
    drones = [(it['typeId'], round(it['active'])) for it in ((t.get('droneStates') or {}).get('items') or []) if round(it['active']) > 0]
    return states, drones

if __name__ == '__main__':
    ROOT = os.path.join(HERE, '..', '..')
    html = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
    G = json.load(open(GOLDEN))
    tmp = tempfile.mkdtemp(); dump = os.path.join(tmp, 'd.json')
    subprocess.run(['node', os.path.join(ROOT, 'regression_suite', 'dump_results.mjs'), html, dump, 'application,moduleStates,droneStates', '-', ','.join(G)], check=True, stdout=subprocess.DEVNULL)
    dumped = json.load(open(dump))
    apps = {k: v['application'] for k, v in dumped.items() if (v.get('application') or {}).get('weapons') or (v.get('application') or {}).get('drones')}
    gin, gout = os.path.join(tmp, 'in.json'), os.path.join(tmp, 'out.json')
    json.dump({'fits': apps, 'grid': GRID, 'dgrid': DGRID}, open(gin, 'w'))
    subprocess.run(['node', os.path.join(HERE, 'application_grid.mjs'), html, gin, gout], check=True)
    tool = json.load(open(gout))
    bad = points = weapons = drones = exact = compared = dpoints = 0
    for k in G:
        # v2026.10.14.40: the tool's own resolved states and drones in space (inputs, as compare_fit_stats.py)
        states, dr = tool_states(dumped[k])
        o = oracle_for(k, states=states, drones=dr, group_limits=False)
        src = _Src(o)
        if not src.mods and not src.drones and k not in apps: continue
        app = apps.get(k) or {'weapons': [], 'drones': [], 'radius': None, 'lockRange': None}
        t = tool.get(k, {'mults': {}, 'total': [0] * len(GRID)})
        diffs = []
        if src.mods or src.drones:
            if not close(app['radius'] or 0, src.getRadius()): diffs.append(f"radius tool {app['radius']} pyfa {src.getRadius()}")
            if not close(app['lockRange'] or 0, src.item.maxTargetRange): diffs.append(f"lockRange tool {app['lockRange']} pyfa {src.item.maxTargetRange}")
        # drone inputs: DPS and every attribute getDroneMult reads
        td = {f"drone:{d['typeId']}": d for d in app.get('drones') or []}
        for pd in src.drones:
            x = td.get(pd.key)
            if x is None: diffs.append(f'{pd.key} not in the tool'); continue
            for name, tv, pv in (('dps', x['dps'], pd._dps), ('maxVelocity', x['speed'], pd.getModifiedItemAttr('maxVelocity')), ('radius', x['radius'], pd.getModifiedItemAttr('radius')),
                                 ('maxRange', x['optimal'], pd.maxRange or 0), ('falloff', x['falloff'], pd.falloff or 0), ('trackingSpeed', x['tracking'], pd.getModifiedItemAttr('trackingSpeed')),
                                 ('optimalSigRadius', x['optimalSigRadius'], pd.getModifiedItemAttr('optimalSigRadius'))):
                if not close(tv or 0, pv or 0): diffs.append(f'{pd.key} {name} tool {tv} pyfa {pv}')
        keys = {m.key for m in src.mods} | {d.key for d in src.drones}
        if keys != set(t['mults']): diffs.append(f"weapons / drones tool {sorted(t['mults'])} pyfa {sorted(keys)}")
        weapons += len(src.mods and {m.key for m in src.mods}); drones += len(src.drones)
        for grid, tt in ((GRID, t), (DGRID, t.get('drones'))):
            if grid is DGRID and not src.drones: continue
            if tt is None: diffs.append('no drone grid from the tool'); continue
            for i, p in enumerate(grid):
                mults, total = pyfa_point(src, p); points += 1; dpoints += grid is DGRID
                for key in keys:   # pyfa leaves a Vorton out of the map beyond lock range; its graph reads that as 0 (am.get(mod, 0))
                    v = mults.get(key, 0); compared += 1
                    tv = tt['mults'].get(key, [None] * len(grid))[i]
                    if tv is None or not close(tv, v):
                        if len(diffs) < 8: diffs.append(f'{key} {p} tool {tv} pyfa {v}')
                    elif tv == v: exact += 1
                if not close(tt['total'][i], total) and len(diffs) < 8: diffs.append(f"applied DPS {p} tool {tt['total'][i]} pyfa {total}")
        if diffs: bad += 1; print(f'{k}: ' + '; '.join(diffs))
    print(f'{weapons} weapon + charge pairs, {drones} drone types in space, {points} fit x grid points ({dpoints} on the drone grid), {exact} of {compared} multipliers bit-identical')
    print(f'{bad} mismatches (golden fits with weapons or drones vs pyfa getApplicationPerKey, grids of {len(GRID)} and {len(DGRID)})')
