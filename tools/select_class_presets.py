"""Class presets for "Their damage on you" (turret-application-plan.md, Phase 2b decisions, 2026-10-23).

    PYFA_SRC=... python3 -I tools/select_class_presets.py out.json
    PYFA_SRC=... python3 -I tools/select_class_presets.py --check index.html   -> 'N mismatches' (update-check chain)

Until a ship is saved as My Ship, the chart uses a typical hull per class, treated as a fit. Rule (Erik: "yes",
"keep it"): published T1 hulls of the four empire races (covert exploration frigates left out), each with its
class's T2 MWD active and nothing else, run through pyfa's handlers at All V (tools/pyfa_fit_oracle.py); the real
hull nearest the class median of MWD speed and MWD signature (log distance) is the preset. Re-run after a game-data
update: a pick changes only when CCP rebalances hulls.
"""
import sys, math, json, statistics
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pyfa_sde as S
from pyfa_fit_oracle import OracleFit
grp = {S._en(v['groupName']): int(k) for k, v in S.groups.items() if v.get('categoryID') == 6}
MWD = {'Frigate': '5MN Microwarpdrive II', 'Destroyer': '5MN Microwarpdrive II', 'Cruiser': '50MN Microwarpdrive II',
       'Combat Battlecruiser': '50MN Microwarpdrive II', 'Battleship': '500MN Microwarpdrive II'}
EXPLORATION = {'Heron', 'Magnate', 'Imicus', 'Probe'}   # covert exploration frigates (scan bonuses, no combat role)
out = {}
for g, mwd in MWD.items():
    rows = []
    for k, v in S.types.items():
        if v.get('groupID') != grp[g] or not v.get('published') or v.get('techLevel') != 1: continue
        if v.get('raceID') not in (1, 2, 4, 8) or v.get('metaGroupID') not in (1, None): continue
        f = OracleFit(int(k), [(mwd, 'active')]).calculate()
        assert not f.errors and not f.oracleGaps, (S.name(k), f.errors, f.oracleGaps)
        rows.append({'hull': S.name(k), 'speed': f.ship.get('maxVelocity'), 'sig': f.ship.get('signatureRadius'), 'radius': f.ship.get('radius'),
                     'cruise': OracleFit(int(k), [(mwd, 'online')]).calculate().ship.get('maxVelocity'), 'sigBase': OracleFit(int(k), [(mwd, 'online')]).calculate().ship.get('signatureRadius')})
    for label, pool in (('all', rows), ('no exploration', [r for r in rows if r['hull'] not in EXPLORATION])):
        ms, mg = statistics.median(r['speed'] for r in pool), statistics.median(r['sig'] for r in pool)
        for r in pool: r['dist'] = math.hypot(math.log(r['speed'] / ms), math.log(r['sig'] / mg))
        best = sorted(pool, key=lambda r: r['dist'])
        print(f"{g} [{label}, {len(pool)} hulls] median MWD speed {ms:.0f} m/s, sig {mg:.0f} m -> " + ', '.join(f"{r['hull']} ({r['speed']:.0f} m/s, {r['sig']:.0f} m, d={r['dist']:.3f})" for r in best[:3]))
        if label == 'no exploration': out[g] = {'pick': best[0], 'median': [ms, mg], 'runnerUp': best[1], 'n': len(pool), 'hulls': sorted(r['hull'] for r in pool)}
if sys.argv[1] == '--check':
    # the page's DMG_CLASS_PRESETS must be today's picks (a CCP rebalance can move a class median)
    import re
    page = open(sys.argv[2], encoding='utf-8').read().split('const DMG_CLASS_PRESETS = [', 1)[1].split('];', 1)[0]
    have = {k: (h, p) for k, l, h, p in re.findall(r"\{key: '(\w+)', label: '([^']+)', hull: '([^']+)', prop: '([^']+)'\}", page)}
    KEY = {'Frigate': 'frigate', 'Destroyer': 'destroyer', 'Cruiser': 'cruiser', 'Combat Battlecruiser': 'battlecruiser', 'Battleship': 'battleship'}
    bad = 0
    for g, mwd in MWD.items():
        want = (out[g]['pick']['hull'], mwd); got = have.get(KEY[g])
        if got != want: bad += 1; print(f'{KEY[g]}: page {got}, today\'s pick {want}')
    if set(have) != set(KEY.values()): bad += 1; print(f'page classes {sorted(have)}')
    print(f'{bad} mismatches (DMG_CLASS_PRESETS vs the class-median rule on pyfa\'s handlers)')
else:
    json.dump(out, open(sys.argv[1], 'w'), indent=1)
