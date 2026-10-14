"""Speed, agility, mass and align time: every golden fit, the tool vs pyfa's own handlers
(tools/pyfa_fit_oracle.py) -- hand-tables Phase 3, v2026.10.14.8.

    PYFA_SRC=... python3 -I tools/independent_checks/compare_speed.py [index.html] [--verbose]

Oracle side (pyfa eos/saveddata/fit.py: maxSpeed = ship maxVelocity [capped by speedLimit];
alignTime = -ln(0.25) * agility * mass / 1e6), with the tool's default module states:
  cruise   every Propulsion Module online, not running
  boosted  each prop module type running alone (pyfa effects 6730 MWD / 6731 AB: mass +=
           massAddition, then maxVelocity boosted by speedFactor * speedBoostFactor / mass in the
           'postMul' stacking group), compared with the tool's afterburner / MWD figure
Each compared after the tool's rounding (speed m/s integer, align 0.1 s). Ends with
'N mismatches' (must be 0).
"""
import sys, os, json, math, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from golden_oracle import oracle_for, GOLDEN, td_mode
from pyfa_fit_oracle import OracleFit

MWD_EFFECT, AB_EFFECT = 6730, 6731
LN4 = -math.log(0.25)

def ship_speed(f):
    s = f.ship
    v = s.get('maxVelocity') or 0
    lim = s.get('speedLimit')
    return lim if lim and v > lim else v
def align(f):
    return LN4 * (f.ship.get('agility') or 0) * (f.ship.get('mass') or 0) / 1e6

def oracle_speed(fitId, mode=None):
    f0 = oracle_for(fitId, mode=mode)
    ship = int(f0.ship.item.ID)
    modeItem = f0.mode.item.ID if f0.mode else None
    mods = [(m.item.ID, {0: 'offline', 1: 'online', 2: 'active', 3: 'active'}[m.state], m.charge.item.ID if m.charge else None) for m in f0.modules]
    props = [i for i, m in enumerate(f0.modules) if {MWD_EFFECT, AB_EFFECT} & set(m.item.effectIds)]
    base = [((t, 'online', c) if i in props and s == 'active' else (t, s, c)) for i, (t, s, c) in enumerate(mods)]
    # v2026.10.14.12: the same implants / boosters as oracle_for (re-built fits must keep them)
    ib = dict(implants=[x.item.ID for x in f0.appliedImplants], boosters=[x.item.ID for x in f0.boosters])
    fc = OracleFit(ship, base, mode=modeItem, **ib).calculate()
    out = {'cruise': ship_speed(fc), 'align': align(fc), 'mass': fc.ship.get('mass'), 'agility': fc.ship.get('agility')}
    for i in props:
        if mods[i][1] == 'offline': continue
        mm = list(base); mm[i] = (mm[i][0], 'active', mm[i][2])
        fb = OracleFit(ship, mm, mode=modeItem, **ib).calculate()
        kind = 'mwd' if MWD_EFFECT in fb.modules[i].item.effectIds else 'afterburner'
        sp = ship_speed(fb)
        if kind not in out or sp > out[kind][0]: out[kind] = (sp, align(fb))
    return out

def tool_speed(r):
    sp, al = r.get('speed') or {}, r.get('alignTime') or {}
    out = {'cruise': sp.get('cruising'), 'align': al.get('base')}
    if sp.get('propModType'): out[sp['propModType']] = (sp.get('boosted'), al.get('boosted'))
    if sp.get('secondaryPropModType'): out[sp['secondaryPropModType']] = (sp.get('secondaryBoosted'), al.get('secondaryBoosted'))
    return out

def compare(o, t):
    d = []
    if t['cruise'] is None or abs(t['cruise'] - o['cruise']) > 1: d.append(f"cruise pyfa {o['cruise']:.2f} tool {t['cruise']}")
    if t['align'] is None or abs(t['align'] - o['align']) > 0.1: d.append(f"align pyfa {o['align']:.3f} tool {t['align']}")
    for k in ('afterburner', 'mwd'):
        if k in o or k in t:
            if k not in o or k not in t: d.append(f"{k} pyfa {o.get(k)} tool {t.get(k)}"); continue
            (os_, oa), (ts, ta) = o[k], t[k]
            if ts is None or abs(ts - os_) > 1 or ta is None or abs(ta - oa) > 0.1:
                d.append(f"{k} pyfa {os_:.2f}/{oa:.3f} tool {ts}/{ta}")
    return d

if __name__ == '__main__':
    ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
    html = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
    G = json.load(open(GOLDEN))
    tmp = os.path.join(tempfile.mkdtemp(), 's.json')
    subprocess.run(['node', os.path.join(ROOT, 'regression_suite', 'dump_results.mjs'), html, tmp, 'speed,alignTime'], check=True, stdout=subprocess.DEVNULL)
    tool = json.load(open(tmp))
    bad = 0
    for k in G:
        t = tool.get(k, {})
        if 'error' in t: print('TOOL ERROR', k, t['error']); bad += 1; continue
        try: o = oracle_speed(k)
        except Exception as ex: print('ORACLE ERROR', k, repr(ex)[:150]); bad += 1; continue
        d = compare(o, tool_speed(t))
        if d: bad += 1; print(f'{k}: ' + '; '.join(d))
    print(f'{bad} mismatches ({len(G)} fits)')
