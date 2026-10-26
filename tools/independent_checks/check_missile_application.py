"""Missile ammo recommendation check (v2026.10.14.27, hand-tables P5).

Part 1 -- which skills change a missile's application, from pyfa's own handlers (recorder, every published
skill): must be exactly Guided Missile Precision (aoeCloudSize, aoeCloudSizeBonus x level) and Target
Navigation Prediction (aoeVelocity, aoeVelocityBonus x level), unpenalized, on charges requiring Missile
Launcher Operation. A pyfa or SDE change here fails the check.
Part 2 -- every golden fit's ranking recomputed here: each catalog missile's SDE explosion radius / velocity /
drf with those skills at V, the target's unrounded signature and speed (missileApplication.inputs: cruising =
base signature + cruise speed; boosted = the winning prop module's signature + boosted speed: an MWD's bloom, an
afterburner's base signature, since v2026.10.14.69), EVE's missile application formula
min(1, S/E, (S/E * Ve/Vt)^drf), applied DPS = raw damage / launcher cycle x application. The tool's whole
ordering, percentages and applied DPS must match.

    PYFA_SRC=... python3 -I tools/independent_checks/check_missile_application.py [index.html]   -> 'N mismatches'
"""
import sys, os, json, re, subprocess, tempfile, math
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, os.path.join(HERE, '..'))
from pyfa_effects import *
html = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
bad = 0
# Part 1
want = {'aoeCloudSize', 'aoeVelocity', 'aoeDamageReductionFactor'}
found = {}
for t, v in td.items():
    if str(t) not in types or cat(int(t)) != 16 or not types[str(t)].get('published'): continue
    for e in v.get('dogmaEffects', []):
        if e['effectID'] not in EFFECTS: continue
        calls, err = run(e['effectID'], 'skill', None, carrier=int(t), rich=True)
        if err: continue
        for coll, meth, a, kw in calls:
            if coll == 'modules' and len(a) > 2 and str(a[1]) in want and meth == 'filteredChargeBoost':
                found[(name(int(t)), str(a[1]))] = (repr(a[2]), kw.get('stackingPenalties'))
expect = {('Guided Missile Precision', 'aoeCloudSize'): ('(a:aoeCloudSizeBonus*LVL)', False),
          ('Target Navigation Prediction', 'aoeVelocity'): ('(a:aoeVelocityBonus*LVL)', False)}
if found != expect: bad += 1; print('skill handlers on missile application changed:', found)
def sattr(n, a): return {aname(x['attributeID']): x['value'] for x in td[str(T(n))]['dogmaAttributes']}[a]
RM = 1 + sattr('Guided Missile Precision', 'aoeCloudSizeBonus') * 5 / 100
VM = 1 + sattr('Target Navigation Prediction', 'aoeVelocityBonus') * 5 / 100
# Part 2
src = open(html).read()
cat_js = re.search(r'const MISSILE_AMMO_CATALOG = (\{.*?\n\});', src, re.S).group(1)
catalog = json.loads(re.sub(r"'", '"', re.sub(r'(\w+):', r'"\1":', re.sub(r"\s+", " ", cat_js))).replace('"T1"', '"T1"'))
def A(t): return {aname(x['attributeID']): x['value'] for x in td[str(t)]['dogmaAttributes']}
profiles = []
for cls, c in catalog.items():
    rof = A(c['launcherTypeId']).get('speed', 0) / 1000
    for tier, t in c['tiers'].items():
        a = A(t)
        dmg = sum(a.get(k, 0) for k in ('emDamage', 'thermalDamage', 'kineticDamage', 'explosiveDamage'))
        profiles.append({'name': cls if tier == 'T1' else f'{tier} {cls}', 'ev': a.get('aoeVelocity', 0) * VM, 'er': a.get('aoeCloudSize', 0) * RM,
                         'drf': a.get('aoeDamageReductionFactor', 1), 'raw': dmg / rof if rof else 0})
def frac(S, V, p):
    if p['er'] <= 0: return 1
    so = S / p['er']; vt = math.pow(so * (p['ev'] / V), p['drf']) if V > 0 else math.inf
    return min(1, so, vt)
def jsround(x): return math.floor(x + 0.5)   # the ranking's own values are tool-only and keep Math.round (DEVIATIONS.md)
def rank(S, V):
    out = []
    for p in profiles:
        pct = jsround(frac(S, V, p) * 1000) / 10
        out.append((p['name'], pct, jsround(p['raw'] * pct) / 100))
    return sorted(out, key=lambda r: -r[2])
tmp = os.path.join(tempfile.mkdtemp(), 'm.json')
subprocess.run(['node', os.path.join(ROOT, 'regression_suite', 'dump_results.mjs'), html, tmp, 'missileApplication'], check=True, stdout=subprocess.DEVNULL)
tool = json.load(open(tmp)); n = 0
for k, t in tool.items():
    ma = t.get('missileApplication')
    if not ma: continue
    if 'inputs' not in ma: bad += 1; print(f'{k}: no missileApplication.inputs (pre-v.27 build)'); continue
    for state in ('cruising', 'boosted'):
        inp = ma['inputs'][state]
        if inp is None:
            if ma[state] is not None: bad += 1; print(f'{k} {state}: tool ranks with no inputs')
            continue
        # v2026.10.14.69: the prop-on state is the winning prop module with its own signature -- an afterburner's is the
        # base signature (no bloom); an MWD's is its bloom, which can't be smaller
        if state == 'boosted' and inp.get('prop') == 'afterburner' and inp['sig'] != ma['inputs']['cruising']['sig']:
            bad += 1; print(f"{k}: afterburner prop-on signature {inp['sig']} != base {ma['inputs']['cruising']['sig']}")
        if state == 'boosted' and inp.get('prop') == 'mwd' and inp['sig'] < ma['inputs']['cruising']['sig']:
            bad += 1; print(f"{k}: MWD prop-on signature {inp['sig']} below base {ma['inputs']['cruising']['sig']}")
        exp = rank(inp['sig'], inp['speed']); got = [(r['name'], r['applicationPct'], r['appliedDps']) for r in ma[state]]
        n += 1
        # same values per missile; the order may differ only between exact ties
        if sorted(exp) != sorted(got) or [r[2] for r in exp] != [r[2] for r in got]:
            bad += 1; print(f'{k} {state}: tool {got[:3]} expected {exp[:3]}')
print(f'{bad} mismatches ({n} rankings; skills: explosion radius x{RM}, velocity x{VM})')
