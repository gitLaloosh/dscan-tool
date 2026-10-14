"""EWAR card values: every golden fit, the tool vs pyfa's own handlers (tools/pyfa_fit_oracle.py)
-- hand-tables Phase 4, v2026.10.14.11.

    PYFA_SRC=... python3 -I tools/independent_checks/compare_ewar.py [index.html] [--verbose]

For every fitted module the tool lists on the EWAR / Misc card (estimate.ewarModules), the oracle
runs the whole fit through pyfa's handlers (All V skills, hull, subsystems, rigs, other modules,
the ship mode, loaded scripts) and reads the module's modified attributes, exactly what pyfa shows
for the module:
  rangeM maxRange (54), falloffM falloffEffectiveness (2044), scramStrength warpScrambleStrength
  (105), speedBonusPct speedFactor (20), sigRadiusBonusPct signatureRadiusBonus (554),
  targetingRangeBonusPct maxTargetRangeBonus (309), scanResolutionBonusPct scanResolutionBonus (566),
  capPerCycle energyNeutralizerAmount (97) / powerTransferAmount (90) and capPerSec = that / duration
  (73) in seconds, jamStrength = the largest of the 4 ECM strengths (238-241), TD maxRangeBonus (351)
  / falloffBonus (349) / trackingSpeedBonus (767), GD missileVelocityBonus (547) / explosionDelayBonus
  (596) / aoeVelocityBonus (847) / aoeCloudSizeBonus (848).
Since v.11 the tool lists one entry per (module type, loaded script) and is compared with every copy
of that type carrying that script (before v.11: one entry per type, compared with every copy). Relative tolerance 1e-6 (both
sides unrounded). Ends with 'N mismatches' (must be 0).
"""
import sys, os, json, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from golden_oracle import oracle_for, GOLDEN

FIELDS = {'rangeM': 'maxRange', 'falloffM': 'falloffEffectiveness', 'scramStrength': 'warpScrambleStrength',
          'speedBonusPct': 'speedFactor', 'sigRadiusBonusPct': 'signatureRadiusBonus',
          'targetingRangeBonusPct': 'maxTargetRangeBonus', 'scanResolutionBonusPct': 'scanResolutionBonus',
          'opticalBonusPct': 'maxRangeBonus', 'falloffBonusPct': 'falloffBonus', 'trackingSpeedBonusPct': 'trackingSpeedBonus',
          'missileVelocityBonusPct': 'missileVelocityBonus', 'flightTimeBonusPct': 'explosionDelayBonus',
          'explosionVelocityBonusPct': 'aoeVelocityBonus', 'explosionRadiusBonusPct': 'aoeCloudSizeBonus'}
ECM = ('scanGravimetricStrengthBonus', 'scanLadarStrengthBonus', 'scanMagnetometricStrengthBonus', 'scanRadarStrengthBonus')

def oracle_values(m, kind):
    g = lambda k: m.get(k) or 0.0
    out = {f: g(a) for f, a in FIELDS.items()}
    out['jamStrength'] = max(g(a) for a in ECM)
    amount = g('energyNeutralizerAmount') if kind == 'neut' else g('powerTransferAmount')
    out['capPerCycle'] = amount
    dur = g('duration') / 1000
    out['capPerSec'] = amount / dur if dur > 0 else 0
    return out

def close(a, b): return abs(a - b) <= 1e-6 * max(1.0, abs(a), abs(b))

if __name__ == '__main__':
    ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
    html = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
    G = json.load(open(GOLDEN))
    tmp = os.path.join(tempfile.mkdtemp(), 'e.json')
    subprocess.run(['node', os.path.join(ROOT, 'regression_suite', 'dump_results.mjs'), html, tmp, 'ewarModules'], check=True, stdout=subprocess.DEVNULL)
    tool = json.load(open(tmp))
    bad = checked = 0
    for k in G:
        mods = (tool.get(k) or {}).get('ewarModules') or []
        if not mods: continue
        o = oracle_for(k)
        byName = {}
        for m in o.modules: byName.setdefault(m.item.name, []).append(m)
        for e in mods:
            copies = byName.get(e['name'], [])
            if 'script' in e:   # v.11+: one entry per (module type, script)
                copies = [m for m in copies if (m.charge.item.name if m.charge else None) == e['script']]
            if not copies: print(f'{k}: {e["name"]} (script {e.get("script")}) not in the oracle fit'); bad += 1; continue
            diffs = []
            for i, m in enumerate(copies):
                ov = oracle_values(m, e['kind'])
                for f, tv in e.items():
                    if f in ov and isinstance(tv, (int, float)) and not close(tv, ov[f]):
                        diffs.append(f'{f} tool {tv:.6g} pyfa {ov[f]:.6g}' + (f' (copy {i + 1}, charge {m.charge.item.name if m.charge else None})' if len(copies) > 1 else ''))
            checked += 1
            if diffs:
                bad += 1; print(f'{k}: {e["name"]}: ' + '; '.join(dict.fromkeys(diffs)))
    print(f'{bad} mismatches ({checked} EWAR module entries)')
