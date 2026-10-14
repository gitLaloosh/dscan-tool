"""Missile flight range exactly as pyfa computes it (v2026.10.14.7), against the tool.

    PYFA_SRC=... python3 -I tools/independent_checks/check_missile_range.py [index.html]

Reference: pyfa's OWN code, not a re-derivation --
  * eos/saveddata/module.py Module.missileMaxRangeData is lifted unmodified from pyfa's source
    (ast: the function body as written) and executed on a stand-in module whose attributes come
    from tools/pyfa_fit_oracle.py (pyfa's effect handlers on the whole fit);
  * eos/utils/float.py floatUnerr is exec'd unmodified;
  * the displayed number is Module.maxRange's missile branch:
        lowerRange * (1 - higherChance) + higherRange * higherChance
    (gui/builtinViewColumns/maxRange.py shows that; its tooltip shows the two chances).

Every golden fit with a loaded missile launcher is compared with the tool's rangeEstimates
(travelDistanceM = the displayed range, travelLowerM / travelHigherM / travelHigherChancePct = the
tooltip). Ends with 'N mismatches' (must be 0).
"""
import sys, os, json, ast, math, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from pyfa_sde import PYFA_SRC, effs

def _load_pyfa():
    ns = {'math': math}
    exec(open(os.path.join(PYFA_SRC, 'eos', 'utils', 'float.py')).read(), ns)
    src = open(os.path.join(PYFA_SRC, 'eos', 'saveddata', 'module.py')).read()
    tree = ast.parse(src)
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'missileMaxRangeData')
    fn.decorator_list = []
    mod = ast.Module(body=[fn], type_ignores=[])
    exec(compile(mod, 'pyfa:module.py:missileMaxRangeData', 'exec'), ns)
    return ns['missileMaxRangeData'], ns['floatUnerr']
missileMaxRangeData, floatUnerr = _load_pyfa()

EFFECT_NAME = {int(k): v.get('effectName') for k, v in effs.items()}

class _Group:
    def __init__(self, n): self.name = n
class _Charge:
    def __init__(self, item):
        self.group = _Group(item.item.group.name)
        self.effects = {EFFECT_NAME.get(e) for e in item.item.effectIds}   # pyfa: Item.effects is keyed by effect name
class _Ship:
    def __init__(self, ship): self._s = ship
    def getModifiedItemAttr(self, k, default=0):
        v = self._s.get(k); return default if v is None else v
class _Owner:
    def __init__(self, ship): self.ship = _Ship(ship)
class StandIn:
    """What missileMaxRangeData reads from a pyfa Module: charge, owner.ship, getModifiedChargeAttr."""
    def __init__(self, fit, m):
        self._m = m; self.charge = _Charge(m.charge) if m.charge else None; self.owner = _Owner(fit.ship)
    def getModifiedChargeAttr(self, k, default=0):
        v = self._m.charge.get(k); return default if v is None else v

def pyfa_missile_range(fit, m):
    """(lowerRange, higherRange, higherChance, displayedMaxRange) or None -- pyfa's numbers."""
    d = missileMaxRangeData(StandIn(fit, m))
    if d is None: return None
    lo, hi, ch = d
    return lo, hi, ch, lo * (1 - ch) + hi * ch

def is_launcher(m): return m.item.group.name.startswith('Missile Launcher')

if __name__ == '__main__':
    from golden_oracle import oracle_for, GOLDEN
    ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
    html = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'index.html')
    G = json.load(open(GOLDEN))
    tmp = os.path.join(tempfile.mkdtemp(), 'r.json')
    subprocess.run(['node', os.path.join(ROOT, 'regression_suite', 'dump_results.mjs'), html, tmp, 'rangeEstimates'], check=True, stdout=subprocess.DEVNULL)
    tool = json.load(open(tmp))
    bad = checked = 0
    for k, f in G.items():
        est = [e for e in (tool.get(k, {}).get('rangeEstimates') or []) if e.get('kind') == 'missile']
        if not est: continue
        o = oracle_for(k)
        ref = {}
        for m in o.modules:
            if m.charge is not None and is_launcher(m) and m.state >= 2:
                r = pyfa_missile_range(o, m)
                if r: ref.setdefault((m.item.ID, m.charge.item.ID), r)
        for e in est:
            r = ref.get((e['weaponTypeId'], e['ammoTypeId']))
            checked += 1
            if r is None: print(f'{k}: no pyfa range for {e["weaponName"]} / {e["ammoName"]}'); bad += 1; continue
            lo, hi, ch, disp = r
            got = (e.get('travelDistanceM'), e.get('travelLowerM'), e.get('travelHigherM'), e.get('travelHigherChancePct'))
            want = (round(disp), round(lo), round(hi), round(ch * 100))
            if any(g is None or abs(g - w) > 1 for g, w in zip(got, want)):
                bad += 1; print(f'{k}: {e["ammoName"]}: pyfa {want} tool {got}')
    print(f'{bad} mismatches ({checked} missile range estimates)')
