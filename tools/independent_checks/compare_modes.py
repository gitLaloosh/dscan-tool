"""Every golden fit on a hull with modes (Tactical Destroyers, Anhinga), in EVERY mode: the tool vs
pyfa's own handlers (pyfa_fit_oracle) on the stats a mode changes.

    PYFA_SRC=... python3 -I tools/independent_checks/compare_modes.py [index.html]

Stats (oracle side = pyfa attributes after every handler, with the tool's default module states):
  dps        weapon DPS: sum over weapons with a loaded charge of charge damage x module
             damageMultiplier (turrets) / cycle -- fits with drones/fighters/smartbombs are skipped
  targeting  ship maxTargetRange, capped at maximumRangeCap
  sensor     max of the four scan strengths
  sig        ship signatureRadius, propulsion modules not running
  cruise     ship maxVelocity, propulsion modules not running
  boosted    ship maxVelocity with the fit's propulsion module running (pyfa's AB/MWD effects)
  align      ln(4) x agility x mass / 1e6, propulsion modules not running
  ehp        uniform-pattern EHP
  shieldPeak passive shield regen peak, 2.5 x shieldCapacity / shieldRechargeRate
  armorRep   active armor repairers: armorDamageAmount / duration
  capDrains  every active module with a cap need: (duration or rate of fire + reactivation delay, capacitorNeed)
  range      each loaded weapon: turret optimal + falloff; missile range = pyfa's own
             Module.missileMaxRangeData / maxRange (check_missile_range.py; since v2026.10.14.7)
Each compared after the tool's display rounding. Ends with 'N mismatches' (must be 0). v2026.10.14.6."""
import sys, os, json, math, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from golden_oracle import oracle_for, resonances, GOLDEN, td_mode, implants_of
from pyfa_fit_oracle import OracleFit
from check_missile_range import pyfa_missile_range
from pyfa_sde import name, T, gname
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
html = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'index.html')
G = json.load(open(GOLDEN))

MODES = {}
for hull in ('Confessor', 'Svipul', 'Jackdaw', 'Hecate', 'Skua', 'Anhinga'):
    hid = int(T(hull))
    keys = [k for k in ('sharpshooter', 'defense', 'propulsion', 'primary', 'secondary', 'tertiary') if td_mode(hid, k)]
    MODES[hid] = keys
fits = [k for k, f in G.items() if int(f['shipTypeId']) in MODES]
PROP = ('Propulsion Module',)

def oracle_stats(fitId, modeKey):
    f = oracle_for(fitId, mode=td_mode(int(G[fitId]['shipTypeId']), modeKey))
    s = f.ship
    out = {}
    dps, ok = 0.0, True
    for m in f.modules:
        if m.state < 2: continue
        g = m.item.group.name
        if g in PROP or m.charge is None: continue
        if not (g.endswith('Weapon') or g.startswith('Missile Launcher')): continue
        dmg = sum(m.charge.get(a) or 0 for a in ('emDamage', 'thermalDamage', 'kineticDamage', 'explosiveDamage'))
        mult = m.get('damageMultiplier') if not g.startswith('Missile Launcher') else 1
        dps += dmg * (mult or 1) / (m.get('speed') / 1000)
    out['dps'] = round(dps)
    rng = []   # every weapon with a charge, fitted order: turret optimal/falloff, missile velocity x flight time
    for m in f.modules:
        g = m.item.group.name
        if m.charge is None or not (g.endswith('Weapon') or g.startswith('Missile Launcher')): continue
        if g.startswith('Missile Launcher'): rng.append(('travel', round(pyfa_missile_range(f, m)[3])))   # pyfa Module.maxRange (since v.7)
        else: rng.append(('optimal', round(m.get('maxRange'))), ); rng.append(('falloff', round(m.get('falloff'))))
    out['range'] = sorted(set(rng))
    out['shieldPeak'] = round(2.5 * s.get('shieldCapacity') / (s.get('shieldRechargeRate') / 1000))
    rep = sum(m.get('armorDamageAmount') / (m.get('duration') / 1000) for m in f.modules if m.state >= 2 and m.item.group.name == 'Armor Repair Unit')
    out['armorRep'] = round(rep) if rep else None
    # capacitor drains: every active module with a cap need -- pyfa fullCycleTime (duration or rate
    # of fire + reactivation delay) and capacitorNeed
    out['capDrains'] = sorted((round((m.get('duration') or m.get('speed')) + (m.get('moduleReactivationDelay') or 0)), round(m.get('capacitorNeed'), 3))
                              for m in f.modules if m.state >= 2 and (m.get('capacitorNeed') or 0) > 0)
    cap = s.item.attributes.get('maximumRangeCap')
    out['targeting'] = round(min(s.get('maxTargetRange'), cap) if cap else s.get('maxTargetRange'))
    out['sensor'] = round(max(s.get(a) or 0 for a in ('scanRadarStrength', 'scanLadarStrength', 'scanMagnetometricStrength', 'scanGravimetricStrength')), 1)
    r = resonances(f); hp = {'shield': s.get('shieldCapacity'), 'armor': s.get('armorHP'), 'hull': s.get('hp')}
    out['ehp'] = round(sum(hp[l] / (sum(r[l].values()) / 4) for l in r))
    # propulsion modules not running: re-run with every prop module online
    mods = [(m.item.ID, 'online' if m.item.group.name in PROP else ('active' if m.state == 2 else 'online' if m.state == 1 else 'offline'), m.charge.item.ID if m.charge else None) for m in f.modules]
    imps, boos = implants_of(G[fitId])   # v2026.10.14.12
    f0 = OracleFit(int(G[fitId]['shipTypeId']), mods, mode=td_mode(int(G[fitId]['shipTypeId']), modeKey), implants=imps, boosters=boos).calculate()
    out['sig'] = round(f0.ship.get('signatureRadius'))
    out['cruise'] = round(f0.ship.get('maxVelocity'))
    out['align'] = round(math.log(4) * f0.ship.get('agility') * f0.ship.get('mass') / 1e6, 1)
    props = [i for i, m in enumerate(mods) if GameName(m[0]) in PROP]
    if props:
        best = None
        for i in props:   # the tool shows the fastest single prop module running
            mm = list(mods); mm[i] = (mm[i][0], 'active', mm[i][2])
            v = OracleFit(int(G[fitId]['shipTypeId']), mm, mode=td_mode(int(G[fitId]['shipTypeId']), modeKey), implants=imps, boosters=boos).calculate().ship.get('maxVelocity')
            best = v if best is None or v > best else best
        out['boosted'] = round(best)
    return out

def GameName(t): return gname(int(t))

def tool_stats(r):
    return {'dps': r.get('dpsFixed'), 'targeting': r.get('targetingRange'), 'sensor': (r.get('sensorStrength') or {}).get('value'),
            'ehp': r.get('totalHP'), 'sig': (r.get('signatureRadius') or {}).get('base'), 'cruise': (r.get('speed') or {}).get('cruising'),
            'boosted': (r.get('speed') or {}).get('boosted'), 'align': (r.get('alignTime') or {}).get('base'),
            'shieldPeak': ((r.get('tankStyle') or {}).get('shield') or {}).get('passiveDps'),
            'armorRep': ((r.get('tankStyle') or {}).get('armor') or {}).get('sustainedDps'),
            'capDrains': sorted((round(d[0]), round(d[1], 3)) for d in (((r.get('capacitor') or {}).get('simInputs') or {}).get('withoutBoosts') or [])),
            'range': sorted({x for e in (r.get('rangeEstimates') or []) for x in
                             ([('travel', e['travelDistanceM'])] if e.get('kind') == 'missile' else [('optimal', e.get('optimalM')), ('falloff', e.get('falloffM'))])})}

FIELDS = 'dpsFixed,targetingRange,sensorStrength,totalHP,signatureRadius,speed,alignTime,rangeEstimates,tankStyle,capacitor,droneDps,fighterDps,fixedWeaponDps'
def compare(o, t):
    """Differences between oracle stats o and a tool result t (list of strings)."""
    ts = tool_stats(t)
    skipDps = (t.get('droneDps') or 0) + (t.get('fighterDps') or 0) + (t.get('fixedWeaponDps') or 0) > 0
    diffs = []
    for stat, ov in o.items():
        if stat == 'dps' and skipDps: continue
        tv = ts.get(stat)
        if tv is None and ov in (None, 0): continue
        if stat == 'capDrains':
            if len(tv) != len(ov) or any(abs(a[0] - b[0]) > 1 or abs(a[1] - b[1]) > 0.002 for a, b in zip(tv, ov)): diffs.append(f'capDrains pyfa {ov} tool {tv}')
            continue
        if stat == 'range':
            if len(tv or []) != len(ov) or any(a[0] != b[0] or abs(a[1] - b[1]) > 1 for a, b in zip(tv, ov)): diffs.append(f'range pyfa {ov} tool {tv}')
            continue
        tol = 1 if stat in ('dps', 'targeting', 'ehp', 'sig', 'cruise', 'boosted', 'shieldPeak', 'armorRep') else 0.1
        if tv is None or abs(tv - ov) > tol: diffs.append(f'{stat} pyfa {ov} tool {tv}')
    return diffs

def dump(html, modeKey, ids):
    tmp = os.path.join(tempfile.mkdtemp(), 'm.json')
    subprocess.run(['node', os.path.join(ROOT, 'regression_suite', 'dump_results.mjs'), html, tmp, FIELDS, modeKey, ','.join(ids)], check=True, stdout=subprocess.DEVNULL)
    return json.load(open(tmp))

def main():
    bad = 0
    for modeKey in ('sharpshooter', 'defense', 'propulsion', 'primary', 'secondary', 'tertiary'):
        ids = [k for k in fits if modeKey in MODES[int(G[k]['shipTypeId'])]]
        if not ids: continue
        tool = dump(html, modeKey, ids)
        for k in ids:
            t = tool[k]
            if 'error' in t: print('TOOL ERROR', k, modeKey, t['error']); bad += 1; continue
            diffs = compare(oracle_stats(k, modeKey), t)
            if diffs: bad += 1; print(f'{k} [{modeKey}]: ' + '; '.join(diffs))
    print(f'{bad} mismatches ({len(fits)} fits on mode hulls, every mode)')

if __name__ == '__main__': main()
