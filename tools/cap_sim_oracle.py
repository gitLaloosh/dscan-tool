"""Run pyfa's OWN capacitor simulator (eos/capSim.py, unmodified) on drain lists.

    PYFA_SRC=/path/to/Pyfa python3 -I tools/cap_sim_oracle.py cases.json > results.json

capSim.py needs only the Python standard library, so it is imported straight from
the pyfa checkout -- the reference for the JS port capSimPyfa() in index.html.
Settings copied from pyfa eos/saveddata/fit.py Fit.__runCapSim(): stagger=True,
scale=False, t_max 6 h, reload = fit.factorReload (False by default),
optimize_repeats=True, startingCapacity = full capacitor. The displayed value is
Fit.simulateCap(): capState = (cap_stable_low + cap_stable_high) / (2 x capacity);
stable if > 0, shown as min(100, capState x 100) %, else sim.t / 1000 s.

cases.json: [{"id", "capacity", "rechargeMs", "drains": [[durationMs, capNeed,
clipSize, disableStagger, reloadMs, isInjector], ...]}, ...]
"""
import sys, os, json, importlib.util
PYFA = os.environ.get('PYFA_SRC') or sys.exit('set PYFA_SRC to a pyfa checkout')
spec = importlib.util.spec_from_file_location('capSim', os.path.join(PYFA, 'eos', 'capSim.py'))
capSim = importlib.util.module_from_spec(spec); spec.loader.exec_module(capSim)

out = []
for case in json.load(open(sys.argv[1])):
    drains = [tuple(d) for d in case['drains']]
    if not (case['capacity'] > 0 and case['rechargeMs'] > 0):   # trimmed record without capacitor attributes: pyfa would divide by zero
        out.append({'id': case['id'], 'skipped': 'no capacitor capacity/recharge'}); continue
    if not drains:
        out.append({'id': case['id'], 'stable': True, 'stablePct': 100, 'timeToEmptySec': None, 'eveStablePct': 100}); continue
    sim = capSim.CapSimulator()
    sim.init(drains)
    sim.capacitorCapacity = case['capacity']
    sim.capacitorRecharge = case['rechargeMs']
    sim.startingCapacity = case['capacity']
    sim.stagger = True; sim.scale = False; sim.t_max = 6 * 60 * 60 * 1000
    sim.reload = False; sim.optimize_repeats = True
    try:
        sim.run()
    except ValueError as ex:   # pyfa's max() over an empty injector list (see capSimPyfa comment)
        out.append({'id': case['id'], 'error': 'pyfa raised ' + repr(ex)}); continue
    capState = (sim.cap_stable_low + sim.cap_stable_high) / (2 * sim.capacitorCapacity)
    stable = capState > 0
    # Unrounded: Python's round() is round-half-even, JavaScript's Math.round is
    # half-up, so the comparison rounds both sides the JS way.
    out.append({'id': case['id'], 'stable': stable,
                'stablePct': min(100, capState * 100) if stable else None,
                'timeToEmptySec': None if stable else sim.t / 1000,
                'eveStablePct': min(100, sim.cap_stable_eve * 100)})
json.dump(out, sys.stdout)
