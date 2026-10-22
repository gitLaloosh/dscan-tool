"""Implants and boosters: every golden fit that carries any, the tool vs pyfa's own handlers
(tools/pyfa_fit_oracle.py) -- v2026.10.14.12, backlog "Fit Analyzer: implants/boosters from an EFT paste".

    PYFA_SRC=... python3 -I tools/independent_checks/compare_implants.py [index.html] [--verbose]

The oracle runs the whole fit with pyfa's handlers, implants and boosters included (fit.py order:
ship, boosters, implants, modules; booster side effects off, pyfa's default). Compared, unrounded
(estimate.exact), relative tolerance 1e-6:
  shieldHP / armorHP / hullHP          ship shieldCapacity / armorHP / hp
  capacitorCapacity                    ship capacitorCapacity
  capRechargeTimeSec / shieldRechargeTimeSec   ship rechargeRate / shieldRechargeRate, ms -> s
  sigBase                              ship signatureRadius (fits without a microwarpdrive: pyfa's
                                       number includes an active MWD's bloom, the tool's base does not)
  targetingRange / scanResolution      ship maxTargetRange / scanResolution
  sensorStrength                       the largest of the four ship scan strengths
  shieldRepHpPerSec / armorRepHpPerSec  sum over active local repairers (effect 4 shieldBoosting,
                                       27 armorRepair) of amount / cycle -- fits without amplifiers,
                                       ancillary repairers or the siege family
  cap drains                           capacitor.simInputs.best without injectors (an ancillary
                                       shield booster with charges uses none, as in pyfa): the set of
                                       distinct (int cycle ms, capacitorNeed) of the active modules --
                                       a set, because how many copies run is the module-state check's job
Since v2026.10.14.13 (Phase 2, weapons / drones):
  weaponDps        sum over active turrets / launchers with a charge of pyfa Module.getVolley / cycle:
                   (charge em+therm+kin+exp) x damageMultiplier (1 when absent) x (1 + damageMultiplierBonusMax,
                   the spool at maximum, only when damageMultiplierBonusPerCycle is set as in pyfa's
                   calculateSpoolup) / rawCycleTime
  smartbombDps     active Smart Bombs: their own damage / duration
  droneDps         pyfa Drone.getDps for the drones the tool has in space (passed to the oracle):
                   damage x damageMultiplier x amount / cycle
  droneControlRange  ship droneControlRange (pyfa extraAttributes, 20000 + increases)
  ranges           rangeEstimates, rounded like pyfa and the tool (Python round, ties to even): turret optimal / falloff (maxRange / falloff),
                   missile range = pyfa's own Module.missileMaxRangeData / maxRange (check_missile_range.py)
Speed, align, resistances and EWAR of the same fits are compared by compare_speed.py,
compare_resists.py and compare_ewar.py (golden_oracle passes the implants to the oracle for every check).
Ends with 'N mismatches' (must be 0).
"""
import sys, os, json, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from golden_oracle import oracle_for, implants_of, GOLDEN
from check_missile_range import pyfa_missile_range
DMG = ('emDamage', 'thermalDamage', 'kineticDamage', 'explosiveDamage')
def is_weapon(g): return g.endswith('Weapon') or g.startswith('Missile Launcher') or g == 'Vorton Projector'
# Python round(): ties to even on the exact value, as pyfa's display rounding and, since v2026.10.14.22,
# the tool's pyRound(). (Before v.22 this was floor(x + 0.5), the JavaScript Math.round way.)
def pyround(x): return round(x)

def _mult(item):
    """damageMultiplier, 1 only when the attribute is absent -- a real 0 (Triage Module II: drones deal no
    damage, droneDamageBonus -100%) stays 0. v2026.10.14.22: was `or 1`, which turned that 0 into 1."""
    v = item.get('damageMultiplier')
    return 1 if v is None else v
def close(a, b): return abs(a - b) <= 1e-6 * max(1.0, abs(a), abs(b))

def oracle_values(o):
    sh = o.ship.get
    v = {'shieldHP': sh('shieldCapacity'), 'armorHP': sh('armorHP'), 'hullHP': sh('hp'),
         'capacitorCapacity': sh('capacitorCapacity'), 'capRechargeTimeSec': sh('rechargeRate') / 1000,
         'shieldRechargeTimeSec': sh('shieldRechargeRate') / 1000,
         'targetingRange': sh('maxTargetRange'), 'scanResolution': sh('scanResolution'),
         'sensorStrength': max(sh(a) or 0 for a in ('scanRadarStrength', 'scanLadarStrength', 'scanMagnetometricStrength', 'scanGravimetricStrength'))}
    active = [m for m in o.modules if m.state >= 2]
    if not any(6730 in m.item.effectIds for m in active): v['sigBase'] = sh('signatureRadius')
    reps = {'shieldRepHpPerSec': (4, 'shieldBonus'), 'armorRepHpPerSec': (27, 'armorDamageAmount')}
    simple = not any(m.item.group.name in ('Shield Boost Amplifier', 'Siege Module') or {4936, 5275} & set(m.item.effectIds) for m in o.modules if m.state >= 1)
    for k, (eff, amt) in (reps.items() if simple else ()):
        v[k] = sum(m.get(amt) / (m.get('duration') / 1000) for m in active if eff in m.item.effectIds)
    drains = []
    for m in active:
        need = m.get('capacitorNeed') or 0
        if need <= 0: continue
        cyc = max(m.get('speed') or 0, m.get('duration') or 0, m.get('durationHighisGood') or 0) + (m.get('moduleReactivationDelay') or 0)
        drains.append((int(cyc + 1e-6), need))
    v['drains'] = sorted(drains)
    # Phase 2: weapons, smartbombs, drones, drone control range, weapon ranges
    wd = sd = 0.0; rng = []
    for m in active:
        g = m.item.group.name
        cyc = max(m.get('speed') or 0, m.get('duration') or 0) / 1000
        if m.charge is not None and is_weapon(g):
            # pyfa calculateSpoolup: no spool unless BOTH damageMultiplierBonusMax and ...PerCycle are set
            # (the SDE default of BonusMax is 0.5 on every item -- reading it alone gave every turret +50%)
            spool = (m.get('damageMultiplierBonusMax') or 0) if (m.get('damageMultiplierBonusPerCycle') or 0) else 0
            vol = sum(m.charge.get(a) or 0 for a in DMG) * _mult(m) * (1 + spool)
            wd += vol / cyc
            if g.startswith('Missile Launcher'): rng.append(('travel', pyround(pyfa_missile_range(o, m)[3])))
            else: rng += [('optimal', pyround(m.get('maxRange'))), ('falloff', pyround(m.get('falloff')))]
        elif g == 'Smart Bomb':
            sd += sum(m.get(a) or 0 for a in DMG) / cyc
    v['weaponDps'] = wd; v['smartbombDps'] = sd
    v['droneDps'] = sum(sum(d.get(a) or 0 for a in DMG) * _mult(d) * d.amountActive / ((d.get('speed') or d.get('duration')) / 1000) for d in o.drones if (d.get('speed') or d.get('duration')))  # mining / logistics drones have no damage cycle
    v['droneControlRange'] = o.ship.get('droneControlRange')
    v['ranges'] = sorted(set(rng))
    return v

if __name__ == '__main__':
    ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
    html = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
    G = json.load(open(GOLDEN))
    fits = [k for k in G if any(implants_of(G[k]))]
    from pyfa_sde import pyfa_removed_types
    REMOVED = pyfa_removed_types()
    tmp = os.path.join(tempfile.mkdtemp(), 'i.json')
    subprocess.run(['node', os.path.join(ROOT, 'regression_suite', 'dump_results.mjs'), html, tmp, 'exact,capacitor,implantsApplied,droneStates,rangeEstimates', '-', ','.join(fits) or 'none'], check=True, stdout=subprocess.DEVNULL)
    tool = json.load(open(tmp))
    bad = checked = 0
    for k in fits:
        t = tool.get(k) or {}
        imps, boos = implants_of(G[k])
        applied = sorted(x['id'] for x in (t.get('implantsApplied') or []))
        # pyfa's database has no expired event boosters (pyfa_sde.pyfa_removed_types, LESSON #32): neither applies them
        if applied != sorted(x for x in imps + boos if x not in REMOVED):
            print(f'{k}: tool applied {applied}, fit has {sorted(imps + boos)}'); bad += 1; continue
        drones = [(it['typeId'], round(it['active'])) for it in ((t.get('droneStates') or {}).get('items') or []) if round(it['active']) > 0]
        o = oracle_for(k, drones=drones)
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
                got = sorted({(int(d[0]), round(d[1], 6)) for d in (t.get('capacitor') or {}).get('simInputs', {}).get('best', []) if not d[5] and d[1] > 0})
                want = sorted({(c, round(n, 6)) for c, n in want})
                if len(got) != len(want) or any(g[0] != w[0] or not close(g[1], w[1]) for g, w in zip(got, want)):
                    diffs.append(f'cap drains tool {got} pyfa {want}')
                continue
            got = ex.get(f)
            if got is None or not close(got, want): diffs.append(f'{f} tool {got} pyfa {want}')
            elif '--verbose' in sys.argv: print(f'  {k} {f} {got:.6g} = pyfa')
        checked += 1
        if diffs: bad += 1; print(f'{k}: ' + '; '.join(diffs))
    print(f'{bad} mismatches ({checked} fits with implants or boosters)')
