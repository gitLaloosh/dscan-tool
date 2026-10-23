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
Drones and fighters are left out on both sides (D5: not ported yet). Tolerance 1e-6 relative (floatUnerr keeps
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

class _Src:
    def __init__(s, o):
        s.o = o
        s.mods = [_Mod(o, m, module_dps(m)) for m in o.modules if m.state >= 2 and module_dps(m) > 0]
        class _It: pass
        s.item = _It(); s.item.activeModulesIter = lambda: iter(s.mods); s.item.activeDronesIter = lambda: iter(())
        s.item.activeFightersIter = lambda: iter(()); s.item.maxTargetRange = o.ship.get('maxTargetRange')
        s.item.extraAttributes = {'droneControlRange': o.ship.get('droneControlRange') or 0}
        s.isFit = True
    def getRadius(s): return s.o.ship.get('radius')
class _Tgt:
    def __init__(s, r): s.r = r; s.isFit = False; s.isProfile = True
    def getRadius(s): return s.r

def pyfa_point(src, p):
    SETTINGS['ignoreLockRange'] = p['ignoreLockRange']
    am = getApplicationPerKey(src=src, tgt=_Tgt(p['tgtRadius']), atkSpeed=p['atkSpeed'], atkAngle=p['atkAngle'], distance=p['distance'],
                              tgtSpeed=p['tgtSpeed'], tgtAngle=p['tgtAngle'], tgtSigRadius=p['tgtSigRadius'])
    mults = {}
    for mod, v in am.items(): mults.setdefault(mod.key, v)
    return mults, sum(mod._dps * am.get(mod, 0) for mod in src.mods)

def applied(fitId, **p):
    """pyfa's applied DPS for a golden fit at one point (for golden pins). Defaults: pyfa's graph defaults."""
    q = dict(distance=0, atkSpeed=0, atkAngle=0, tgtSpeed=0, tgtAngle=0, tgtSigRadius=40, tgtRadius=50, ignoreLockRange=True); q.update(p)
    return pyfa_point(_Src(oracle_for(fitId)), q)

GRID = [dict(distance=d, atkSpeed=a, atkAngle=aa, tgtSpeed=ts, tgtAngle=ta, tgtSigRadius=sig, tgtRadius=40, ignoreLockRange=il)
        for d, a, aa, ts, ta, sig, il in itertools.product([0, 1000, 5000, 10000, 20000, 30000, 50000, 80000, 150000, 300000], [0, 250], [0, 90],
                                                          [0, 150, 500, 1500, 4000], [0, 45, 90], [25, 40, 120, 400, 2000], [True, False])]

def close(a, b): return abs(a - b) <= 1e-6 * max(1.0, abs(a), abs(b))

if __name__ == '__main__':
    ROOT = os.path.join(HERE, '..', '..')
    html = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
    G = json.load(open(GOLDEN))
    tmp = tempfile.mkdtemp(); dump = os.path.join(tmp, 'd.json')
    subprocess.run(['node', os.path.join(ROOT, 'regression_suite', 'dump_results.mjs'), html, dump, 'application', '-', ','.join(G)], check=True, stdout=subprocess.DEVNULL)
    apps = {k: v['application'] for k, v in json.load(open(dump)).items() if (v.get('application') or {}).get('weapons')}
    gin, gout = os.path.join(tmp, 'in.json'), os.path.join(tmp, 'out.json')
    json.dump({'fits': apps, 'grid': GRID}, open(gin, 'w'))
    subprocess.run(['node', os.path.join(HERE, 'application_grid.mjs'), html, gin, gout], check=True)
    tool = json.load(open(gout))
    bad = points = weapons = exact = compared = 0
    for k in G:
        o = oracle_for(k)
        src = _Src(o)
        if not src.mods and k not in apps: continue
        app = apps.get(k) or {'weapons': [], 'radius': None, 'lockRange': None}
        t = tool.get(k, {'mults': {}, 'total': [0] * len(GRID)})
        diffs = []
        if src.mods:
            if not close(app['radius'] or 0, src.getRadius()): diffs.append(f"radius tool {app['radius']} pyfa {src.getRadius()}")
            if not close(app['lockRange'] or 0, src.item.maxTargetRange): diffs.append(f"lockRange tool {app['lockRange']} pyfa {src.item.maxTargetRange}")
        keys = {m.key for m in src.mods}
        if keys != set(t['mults']): diffs.append(f"weapons tool {sorted(t['mults'])} pyfa {sorted(keys)}")
        weapons += len(keys)
        for i, p in enumerate(GRID):
            mults, total = pyfa_point(src, p); points += 1
            for key in keys:   # pyfa leaves a Vorton out of the map beyond lock range; its graph reads that as 0 (am.get(mod, 0))
                v = mults.get(key, 0); compared += 1
                tv = t['mults'].get(key, [None] * len(GRID))[i]
                if tv is None or not close(tv, v):
                    if len(diffs) < 8: diffs.append(f'{key} {p} tool {tv} pyfa {v}')
                elif tv == v: exact += 1
            if not close(t['total'][i], total) and len(diffs) < 8: diffs.append(f"applied DPS {p} tool {t['total'][i]} pyfa {total}")
        if diffs: bad += 1; print(f'{k}: ' + '; '.join(diffs))
    print(f'{weapons} weapon + charge pairs, {points} fit x grid points, {exact} of {compared} multipliers bit-identical')
    print(f'{bad} mismatches (golden fits with weapons vs pyfa getApplicationPerKey, grid of {len(GRID)})')
