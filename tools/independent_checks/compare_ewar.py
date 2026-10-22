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
v2026.10.14.26: Warp Disrupt Field Generator bubbleRadiusM = warpScrambleRange (103); Interdiction Sphere
Launcher bubbleRadiusM / lifetimeSec = the loaded probe's warpScrambleRange / explosionDelay; Command Burst
rangeM maxRange, buffDurationSec buffDuration (2535), and each buff's value = the burst's warfareBuffNValue
(pyfa's charge effect 6737 already multiplied it by the charge's multiplier, itself after the Command
Specialist skills).
v2026.10.14.29: Burst Jammer burstRadiusM = ecmBurstRange (142); Burst Projector fieldRadiusM / fieldDurationSec /
warningSec / affectedSec = doomsdayAOERange / doomsdayAOEDuration / doomsdayWarningDuration / the projector's
durationXBurstProjector, plus the field's strength (speed, neut amount, sig, damp, disruption, jam).
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
    # v2026.10.14.26: bubbles and Command Bursts
    if kind == 'bubble':
        out['rangeM'] = out['bubbleRadiusM'] = g('warpScrambleRange')
    if kind == 'sphere':
        c = m.charge
        out['rangeM'] = out['bubbleRadiusM'] = (c.get('warpScrambleRange') or 0.0) if c else 0.0
        out['lifetimeSec'] = ((c.get('explosionDelay') or 0.0) / 1000) if c else 0.0
    if kind == 'burst':
        out['buffDurationSec'] = g('buffDuration') / 1000
        for n in (1, 2, 3, 4): out[f'buff{n}'] = g(f'warfareBuff{n}Value')
    # v2026.10.14.29: ECM Burst radius ecmBurstRange (142); Burst Projector field radius doomsdayAOERange (2279), field
    # lifetime doomsdayAOEDuration (2280), warning doomsdayWarningDuration (2262), how long a target stays affected
    # (durationECMJammer / TargetIllumination / SensorDampening / WeaponDisruption BurstProjector, 2397-2400: a
    # projector has at most one of them), neut amount energyNeutralizerAmount
    if kind == 'burstJammer':
        out['rangeM'] = out['burstRadiusM'] = g('ecmBurstRange')
    if kind == 'projector':
        out['fieldRadiusM'] = g('doomsdayAOERange'); out['fieldDurationSec'] = g('doomsdayAOEDuration') / 1000
        out['warningSec'] = g('doomsdayWarningDuration') / 1000
        out['affectedSec'] = sum(g(a) for a in ('durationECMJammerBurstProjector', 'durationTargetIlluminationBurstProjector',
                                                'durationSensorDampeningBurstProjector', 'durationWeaponDisruptionBurstProjector')) / 1000
        out['capPerCycle'] = g('energyNeutralizerAmount')
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
                tool_vals = dict(e)
                for b in e.get('buffs') or []: tool_vals[f"buff{b['n']}"] = b['value']   # v.26: each buff vs the burst's warfareBuffNValue
                for f, tv in tool_vals.items():
                    if f in ov and isinstance(tv, (int, float)) and not isinstance(tv, bool) and not close(tv, ov[f]):
                        diffs.append(f'{f} tool {tv:.6g} pyfa {ov[f]:.6g}' + (f' (copy {i + 1}, charge {m.charge.item.name if m.charge else None})' if len(copies) > 1 else ''))
            checked += 1
            if diffs:
                bad += 1; print(f'{k}: {e["name"]}: ' + '; '.join(dict.fromkeys(diffs)))
    print(f'{bad} mismatches ({checked} EWAR module entries)')
