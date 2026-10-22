"""Every golden fit vs pyfa's own handlers (tools/pyfa_fit_oracle.py) -- v2026.10.14.22, golden-fit data refresh
step 3 ("pins with no independent source get re-derived").

    PYFA_SRC=... python3 -I tools/independent_checks/compare_fit_stats.py [index.html] [--verbose]

The same stats as compare_implants.py (HP pools, capacitor capacity / recharge, shield recharge, signature
without an MWD, targeting, scan resolution, sensor strength, local repair HP/s, module cap drains, weapon /
smartbomb / drone DPS, weapon ranges, drone control range), but over EVERY golden fit, with the oracle given
the tool's own resolved module states and drones in space (inputs, DEVIATIONS.md section 2: e.g. one prop
module running, the fastest), so only the calculation is compared. Speed / align, resistances, EWAR and modes
have their own checks (compare_speed / compare_resists / compare_ewar / compare_modes).

Cap drains: total cap need per cycle time over every running copy (what the cap simulation sees; the tool
averages a loaded crystal's cap-need modifier over identical turrets, which fire unstaggered, so per-module
values may differ while the total cannot). Tolerance 1e-6 relative for every field (until v2026.10.14.22 weaponDps and sensorStrength had 3e-4 for the
rounded stacking table; v.23 removed the table and v.22 fails at 1e-6). Drain cycle times compared to the millisecond (+-1: the tool and the
oracle truncate 3302.9999 differently). Fits listed in KNOWN are skipped with their reason.
Ends with 'N mismatches' (must be 0).
"""
import sys, os, json, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from golden_oracle import oracle_for, GOLDEN
from compare_implants import oracle_values, close

STACKING_TOL = {}  # v2026.10.14.23: the rounded stacking table is gone, every field compares at 1e-6
KNOWN = {}   # fitId: reason -- filled only with a stated, checked reason

def close_tol(a, b, tol): return abs(a - b) <= tol * max(1.0, abs(a), abs(b))

if __name__ == '__main__':
    ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
    html = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
    G = json.load(open(GOLDEN))
    fits = [k for k in G if k not in KNOWN]
    tmp = os.path.join(tempfile.mkdtemp(), 'f.json')
    subprocess.run(['node', os.path.join(ROOT, 'regression_suite', 'dump_results.mjs'), html, tmp, 'exact,capacitor,moduleStates,droneStates,rangeEstimates', '-', ','.join(fits)], check=True, stdout=subprocess.DEVNULL)
    tool = json.load(open(tmp))
    bad = checked = 0
    for k in fits:
        t = tool.get(k) or {}
        ms = (t.get('moduleStates') or {}).get('items') or []
        states = {str(it['typeId']): {'active': round(it['active']), 'online': round(it['online']), 'offline': round(it['offline'])} for it in ms}
        drones = [(it['typeId'], round(it['active'])) for it in ((t.get('droneStates') or {}).get('items') or []) if round(it['active']) > 0]
        o = oracle_for(k, states=states, drones=drones, group_limits=False)  # the tool's states already apply the hull's group-limit modifiers
        if o.errors or o.oracleGaps: print(f'{k}: ORACLE errors {o.errors} gaps {o.oracleGaps}'); bad += 1; continue
        ov = oracle_values(o); ex = t.get('exact') or {}
        diffs = []
        for f, want in ov.items():
            if f == 'ranges':
                got = []
                for r in t.get('rangeEstimates') or []:
                    if r.get('kind') == 'missile': got.append(('travel', r['travelDistanceM']))
                    else: got += [('optimal', r['optimalM']), ('falloff', r['falloffM'])]
                if sorted(set(got)) != want: diffs.append(f'ranges tool {sorted(set(got))} pyfa {want}')
                continue
            if f == 'drains':
                # Total cap need per cycle time, every running copy (pyfa Fit.__generateDrain): what the cap
                # simulation sees. An Ancillary Shield Booster the tool assumes loaded (capacitor.boosts,
                # source 'loaded' / 'cargo' / 'assumed' -- an input, DEVIATIONS.md) uses no cap there, as in
                # pyfa with charges; the oracle only knows charges listed in the fit, so those ASBs are left out.
                asb = {b['typeId'] for b in (t.get('capacitor') or {}).get('boosts', []) if b.get('kind') == 'asb' and b.get('source') != 'none'}  # v.24: 'none' = pasted fit without charges, runs on cap
                want = []
                for m in o.modules:
                    if m.state < 2 or int(m.item.typeID) in asb: continue
                    need = m.get('capacitorNeed') or 0
                    if need <= 0: continue
                    cyc = max(m.get(a) or 0 for a in ('speed', 'duration', 'durationHighisGood', 'durationSensorDampeningBurstProjector', 'durationTargetIlluminationBurstProjector', 'durationECMJammerBurstProjector', 'durationWeaponDisruptionBurstProjector')) + (m.get('moduleReactivationDelay') or 0)
                    want.append((int(cyc + 1e-6), need))
                def by_cycle(lst):
                    out = {}
                    for c, n in lst:
                        k = next((x for x in out if abs(x - c) <= 1), c); out[k] = out.get(k, 0) + n
                    return out
                g = by_cycle([(int(d[0]), d[1]) for d in (t.get('capacitor') or {}).get('simInputs', {}).get('best', []) if not d[5] and d[1] > 0])
                w = by_cycle(want)
                ok = len(g) == len(w) and all(any(abs(gc - wc) <= 1 and close(gn, wn) for wc, wn in w.items()) for gc, gn in g.items())
                if not ok: diffs.append(f'cap need per cycle tool {sorted((c, round(n, 4)) for c, n in g.items())} pyfa {sorted((c, round(n, 4)) for c, n in w.items())}')
                continue
            got = ex.get(f)
            tol = STACKING_TOL.get(f, 1e-6)
            if got is None or not close_tol(got, want, tol): diffs.append(f'{f} tool {got} pyfa {want}')
            elif '--verbose' in sys.argv: print(f'  {k} {f} {got:.6g} = pyfa')
        checked += 1
        if diffs: bad += 1; print(f'{k}: ' + '; '.join(diffs))
    print(f'{bad} mismatches ({checked} golden fits vs pyfa handlers; {len(KNOWN)} skipped with a stated reason)')
