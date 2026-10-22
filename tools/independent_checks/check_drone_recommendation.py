"""Drone recommendation check (v2026.10.14.25; backlog "drone recommendation regression coverage" -- the first
tests of droneRecommendation / sizeClassFromSignature / sizeClassFromGroup).

The rule, typed here independently from the comments and the owner's decisions (2026-10-13), not from the code:
  * Size tiers by the target's UNBOOSTED signature radius (an MWD is never assumed on; the owner):
      <= 90 m -> light | <= 200 -> medium | <= 335 -> medium, heavy | <= 5000 -> sentry, heavy | above -> sentry, heavy
    The first size is the pick.
  * Race by the fit's weakest damage type: EM Amarr, thermal Gallente, kinetic Caldari, explosive Minmatar.
  * Fit / Pilot Analyzer: target speed = with its Afterburner on if one is fitted (an AB doesn't bloom sig; the owner),
    else cruise speed (an MWD is never assumed). If that speed is above the pick's own travel speed
    (light 2800, medium 2016, heavy 1200, sentry 0 m/s) the alt is the first faster size that keeps up
    (heavy, medium, light order; light if none does), else no alt. A speed of 0 means no alt.
  * D-Scan (no fit, no speed): a sentry pick always gets the second size as its "won't sit still" alt.
  * A missing / zero signature falls back to the ship group's name bucket (GROUP_TIER).

Part 1: every golden fit's shown recommendation vs this rule, fed the tool's signatureRadius.base, speed and
weakest (each of those is compared with pyfa's handlers elsewhere: compare_fit_stats, compare_speed,
compare_resists). Part 2: the page's own functions over a grid of signatures x speeds x damage types, plus
the D-Scan path and the zero-signature fallback.

    PYFA_SRC=... python3 -I tools/independent_checks/check_drone_recommendation.py [index.html]   -> 'N mismatches'
"""
import sys, os, json, subprocess, tempfile
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
html = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
RACE = {'em': 'Amarr', 'therm': 'Gallente', 'kin': 'Caldari', 'exp': 'Minmatar'}
NAMES = {'Amarr': {'light': 'Acolyte', 'medium': 'Infiltrator', 'heavy': 'Praetor', 'sentry': 'Curator'},
         'Gallente': {'light': 'Hobgoblin', 'medium': 'Hammerhead', 'heavy': 'Ogre', 'sentry': 'Garde'},
         'Caldari': {'light': 'Hornet', 'medium': 'Vespa', 'heavy': 'Wasp', 'sentry': 'Warden'},
         'Minmatar': {'light': 'Warrior', 'medium': 'Valkyrie', 'heavy': 'Berserker', 'sentry': 'Bouncer'}}
TRAVEL = {'light': 2800, 'medium': 2016, 'heavy': 1200, 'sentry': 0}
def sizes_for_sig(sig):
    if sig <= 90: return ['light']
    if sig <= 200: return ['medium']
    if sig <= 335: return ['medium', 'heavy']
    if sig <= 5000: return ['sentry', 'heavy']
    return ['sentry', 'heavy']
def expected(weakest, sig, speed):
    line = NAMES[RACE[weakest]]; sizes = sizes_for_sig(sig); pick = sizes[0]
    alt = None
    if speed is None:                       # D-Scan path
        if pick == 'sentry': alt = sizes[1] if len(sizes) > 1 else 'heavy'
    elif speed > TRAVEL[pick]:
        order = ['sentry', 'heavy', 'medium', 'light']
        alt = next((s for s in order[order.index(pick) + 1:] if speed <= TRAVEL[s]), 'light')
    return (line[pick], pick), ((line[alt], alt) if alt else None)

bad = 0
# Part 1: golden fits
tmp = os.path.join(tempfile.mkdtemp(), 'd.json')
subprocess.run(['node', os.path.join(ROOT, 'regression_suite', 'dump_results.mjs'), html, tmp, 'drones,weakest,signatureRadius,speed,droneSpeedBasis'], check=True, stdout=subprocess.DEVNULL)
tool = json.load(open(tmp)); n1 = 0
for k, t in tool.items():
    if 'error' in t or not t.get('drones'): continue
    sp = t['speed']; speed = t.get('droneSpeedBasis')
    if speed is None:
        speed = sp['boosted'] if sp.get('propModType') == 'afterburner' else sp['secondaryBoosted'] if sp.get('secondaryPropModType') == 'afterburner' else sp['cruising']
    (pn, ps), alt = expected(t['weakest'], t['signatureRadius']['base'], speed)
    got = t['drones']; galt = got.get('alt')
    ok = got['primary']['name'] == pn and got['primary']['size'] == ps and ((galt is None and alt is None) or (galt and alt and galt['name'] == alt[0] and galt['size'] == alt[1]))
    n1 += 1
    if not ok:
        bad += 1; print(f"{k}: tool {got} expected {pn} ({ps}) alt {alt}  [sig {t['signatureRadius']['base']}, speed {speed}, {t['weakest']}]")
# Part 2: the functions themselves over a grid (Fit Analyzer path, D-Scan path, zero-signature fallback)
sigs = [38, 65, 89.99, 90, 90.01, 120, 199.9, 200, 200.5, 270, 335, 336, 400, 4999, 5000, 5001, 11500, 23397]
speeds = [None, 0, 1, 300, 1199.9, 1200, 1200.1, 2016, 2016.5, 2800, 2800.1, 5000]
cases = [[w, s, v] for w in RACE for s in sigs for v in speeds]
js = r"""
const fs = require('fs'); const vm = require('vm');
const code = [...fs.readFileSync(process.argv[1], 'utf8').matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');
const fakeEl = () => ({addEventListener(){}, get style(){return {};}, querySelectorAll(){return [];}, appendChild(){}, innerHTML: ''});
const sb = {fetch: async () => ({ok: false}), document: {getElementById: fakeEl, createElement: fakeEl}, console: {log(){}, warn(){}, error(){}}, Promise, Map, Set, Infinity, Math, JSON, Object, Array, Number, String};
vm.createContext(sb); vm.runInContext(code, sb);
const cases = JSON.parse(fs.readFileSync(0, 'utf8'));
const out = cases.map(([w, s, v]) => sb.droneRecommendation(w, sb.sizeClassFromSignature(s, 'Frigate').droneSizes, v === null ? undefined : v));
out.push({fallback: [sb.sizeClassFromSignature(0, 'Battleship').droneSizes, sb.sizeClassFromSignature(0, 'Capital Industrial Ship').droneSizes, sb.sizeClassFromSignature(0, 'Frigate').droneSizes]});
process.stdout.write(JSON.stringify(out));
"""
res = json.loads(subprocess.run(['node', '-e', js, html], input=json.dumps(cases), capture_output=True, text=True, check=True).stdout)
fb = res.pop()['fallback']
for (w, s, v), got in zip(cases, res):
    (pn, ps), alt = expected(w, s, v)
    galt = got.get('alt')
    ok = got['primary']['name'] == pn and ((galt is None and alt is None) or (galt and alt and galt['name'] == alt[0]))
    if not ok:
        bad += 1
        if bad < 25: print(f'grid {w} sig {s} speed {v}: tool {got} expected {pn} alt {alt}')
if fb != [['sentry', 'heavy'], ['sentry', 'heavy'], ['light']]:
    bad += 1; print(f'zero-signature fallback by group name: {fb}')
print(f'{bad} mismatches ({n1} golden fits, {len(cases)} grid cases, 3 fallback cases)')
