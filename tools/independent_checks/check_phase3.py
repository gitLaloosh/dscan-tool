"""Module states, plan Phase 3 (v2026.10.13.26): the special cases folded into
module states. Hand-typed pyfa rules (eos/effects.py handlers, run with
tools/pyfa_effects.py to confirm targets/penalties) with SDE values.

  * MJD 4921: ship signatureRadius boost signatureRadiusBonusPercent, NOT
    stacking-penalized. MJFG 6208 / capital MJFG 12126: penalized 'default'.
  * Signature Suppressor burst 8109: signatureRadius x
    signatureSuppressorSignatureRadiusBonusActive, penalized 'postMul' -- the
    same group as its passive x0.9 (8108).
  * Entosis Link 6063: scan*StrengthPercent, penalized (default group).
  * Networked Sensor Array 6567 / Integrated Sensor Array 12597: scanResolution
    boost (penalized), scan*StrengthPercent (penalized); 12597 also
    maxTargetRange x maxTargetRangeMultiplier (penalized), forces
    maximumRangeCap, and cuts capital local rep duration/capacitorNeed
    (unpenalized).
  * Targeting range cap: maxTargetRange's maxAttributeID is maximumRangeCap
    (797, default 300,000 m when the hull has none) -- pyfa
    modifiedAttributeDict.__calculateValue caps the value at it.
  * Triage 6581 / NSA 6567 ewCapacitorNeedBonus (+900,000,000% / +9,999,900%)
    on EWAR, webs and Propulsion Jamming modules: they can't run in-game, so
    the tool treats them as blocked (see history doc for the pyfa difference).
  * Triage 6581 droneDamageBonus -100% (penalized with Drone Damage
    Amplifiers): drones in space do no damage.
  * Module cycle time (pyfa Module.rawCycleTime): max(speed, duration,
    durationHighisGood, the four Burst Projector durations). Signature Masking
    (+5%/lvl durationHighisGood, Signature Suppressors) and the Interceptor
    nullification role bonus (+100% on Interdiction Nullifiers).
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indep_common import *

SA = SK('Signature Analysis', 'scanResolutionBonus'); LRT = SK('Long Range Targeting', 'maxTargetRangeBonus')
def SC(kind): return SK(kind + ' Sensor Compensation', 'sensorStrengthBonus')
def strength(ship):
    ks = {'Radar': 'scanRadarStrength', 'Ladar': 'scanLadarStrength', 'Magnetometric': 'scanMagnetometricStrength', 'Gravimetric': 'scanGravimetricStrength'}
    k = max(ks, key=lambda k: ship.get(ks[k], 0)); return k, ship[ks[k]]
RANGE_CAP_DEFAULT = attrs[str([k for k, v in attrs.items() if v['name'] == 'maximumRangeCap'][0])]['defaultValue']

# ---- F1 Raven: Signature Radius Suppressor I + Large MJD
r, sup, mjd = A('Raven'), A('Signature Radius Suppressor I'), A('Large Micro Jump Drive')
p_on, p_act = sup['signatureSuppressorSignatureRadiusBonusPassive'], sup['signatureSuppressorSignatureRadiusBonusActive']
mjdx = b(mjd['signatureRadiusBonusPercent'])
SM = 1 + A('Signature Masking')['durationBonus'] * 5 / 100
print('Raven default (suppressor + MJD online): sig', r['signatureRadius'] * p_on)
print('Raven suppressor ACTIVE: sig', r['signatureRadius'] * pen([p_on, p_act]),
      'drain', sup['capacitorNeed'] / (sup['durationHighisGood'] / 1000 * SM + sup['moduleReactivationDelay'] / 1000))  # + reactivation delay since v2026.10.14.1, LESSON #20
print('Raven MJD ACTIVE: sig', r['signatureRadius'] * p_on * mjdx)
print('Raven both ACTIVE: sig', r['signatureRadius'] * pen([p_on, p_act]) * mjdx)

# ---- F2 Vexor: Entosis Link II
v, ent = A('Vexor'), A('Entosis Link II'); k, s = strength(v)
print('Vexor default: sensor', s * SC(k), '| Entosis ACTIVE: sensor', s * SC(k) * pen([b(ent['scan%sStrengthPercent' % k])]),
      'drain', ent['capacitorNeed'] / (ent['duration'] / 1000))

# ---- F3 Nyx: Networked Sensor Array
n, nsa = A('Nyx'), A('Networked Sensor Array'); k, s = strength(n)
print('Nyx default: scanres', n['scanResolution'] * SA, 'sensor', s * SC(k))
print('Nyx NSA ACTIVE: scanres', n['scanResolution'] * SA * pen([b(nsa['scanResolutionBonus'])]),
      'sensor', s * SC(k) * pen([b(nsa['scan%sStrengthPercent' % k])]), 'drain', nsa['capacitorNeed'] / (nsa['duration'] / 1000))

# ---- F4 Thanatos: Integrated Sensor Array + Capital Armor Repairer II
t, isa, car = A('Thanatos'), A('Integrated Sensor Array'), A('Capital Armor Repairer II'); k, s = strength(t)
CRS = SK('Capital Repair Systems', 'durationSkillBonus')
cap0 = t['maximumRangeCap']
cyc0 = car['duration'] / 1000 * CRS
print('Thanatos default: range', min(t['maxTargetRange'] * LRT, cap0), 'scanres', t['scanResolution'] * SA, 'sensor', s * SC(k),
      'rep', car['armorDamageAmount'] / cyc0, 'drain', car['capacitorNeed'] / cyc0)
cyc1 = cyc0 * b(isa['siegeLocalLogisticsDurationBonus'])
print('Thanatos ISA ACTIVE: range', min(t['maxTargetRange'] * LRT * pen([isa['maxTargetRangeMultiplier']]), isa['maximumRangeCap']),
      'scanres', t['scanResolution'] * SA * pen([b(isa['scanResolutionBonus'])]), 'sensor', s * SC(k) * pen([b(isa['scan%sStrengthPercent' % k])]),
      'rep', car['armorDamageAmount'] / cyc1,
      'drain', car['capacitorNeed'] * b(isa['siegeLocalLogisticsCapacitorNeedBonus']) / cyc1 + isa['capacitorNeed'] / (isa['duration'] / 1000))

# ---- F5 Rokh: 3x Sensor Booster II + Targeting Range Script (range cap)
rk, sb, trs = A('Rokh'), A('Sensor Booster II'), A('Targeting Range Script')
m = b(sb['maxTargetRangeBonus'] * b(trs['maxTargetRangeBonusBonus']))
raw = rk['maxTargetRange'] * LRT * pen([m] * 3)
print('Rokh 3x SB II + range script: uncapped', raw, 'capped', min(raw, rk.get('maximumRangeCap', RANGE_CAP_DEFAULT)), '(cap', RANGE_CAP_DEFAULT, ')')

# ---- F6 Apostle: Triage Module II + Remote Sensor Dampener II + 5x Hobgoblin II
ap, tri, rsd, hob = A('Apostle'), A('Triage Module II'), A('Remote Sensor Dampener II'), A('Hobgoblin II')
DI = SK('Drone Interfacing', 'damageMultiplierBonus'); LDO = SK('Light Drone Operation', 'damageMultiplierBonus'); GDS = SK('Gallente Drone Specialization', 'damageMultiplierBonus')
hobdps = 5 * (hob['thermalDamage'] + hob['kineticDamage'] + hob['emDamage'] + hob['explosiveDamage']) * hob['damageMultiplier'] * DI * LDO * GDS / (hob['speed'] / 1000)
rsd_drain = rsd['capacitorNeed'] * SK('Sensor Linking', 'capNeedBonus') / (rsd['duration'] / 1000)
print('Apostle triage ACTIVE (default): dampener blocked -> drain', tri['capacitorNeed'], 'drones', hobdps * pen([b(tri['droneDamageBonus'])]),
      'scanres', ap['scanResolution'] * SA * pen([tri['scanResolutionMultiplier']]))
print('Apostle triage ONLINE: drain', rsd_drain, 'drones', hobdps, 'scanres', ap['scanResolution'] * SA)

# ---- F8 Crow: Interdiction Nullifier II (cycle time on durationHighisGood)
cr, nul = A('Crow'), A('Interdiction Nullifier II')
# + reactivation delay (Interceptor role1 -80%) since v2026.10.14.1, LESSON #20
print('Crow nullifier drain', nul['capacitorNeed'] / (nul['durationHighisGood'] / 1000 * b(cr['shipBonusRole2']) + nul['moduleReactivationDelay'] / 1000 * b(cr['shipBonusRole1'])))

# ---- F7 Revelation: 2x Quad Mega Pulse Laser II + Siege Module II set ONLINE
# The siege bonuses come only from its active effect (6582), so ONLINE must give
# the no-siege figures of check_required_skills.py's revelation().
from check_required_skills import revelation
print('Revelation siege ONLINE: = no siege', revelation('Quad Mega Pulse Laser II'))

# ---- F9 Nyx: Sensor Dampening Burst Projector (cycle on its own duration attribute)
bp = A('Sensor Dampening Burst Projector')
BPO = 1 + A('Burst Projector Operation')['projECMDurationBonus'] * 5 / 100
G4 = 1 + n['shipBonusSupercarrierG4'] * 5 / 100   # Effect6617, skill='Gallente Carrier'
print('Nyx Sensor Dampening Burst Projector drain', bp['capacitorNeed'] / (bp['durationSensorDampeningBurstProjector'] / 1000 * BPO * G4))

# ---- Existing golden vargur_constructed_states_bastion_online_mjd_active (Phase 1): MJD ACTIVE now blooms sig
print('Vargur MJD ACTIVE: sig', A('Vargur')['signatureRadius'] * b(A('Large Micro Jump Drive')['signatureRadiusBonusPercent']))
