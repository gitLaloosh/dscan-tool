"""Module states (v2026.10.13.20, module-state plan Phase 1). Hand-typed pyfa
rules with SDE values; nothing read from index.html.

pyfa rules used (eos/saveddata/module.py, eos/effects.py):
  * an 'active' effect runs only when the module is ACTIVE, a 'passive' one
    when it is ONLINE or ACTIVE, an 'offline' one always;
  * only ACTIVE modules use capacitor;
  * maxGroupActive / maxGroupOnline per group name (Propulsion Module 1 active;
    Command Burst 1 online / 1 active, +maxGangModules on command ships via
    Effect2251);
  * Bastion (Effect6658, active) sets activationBlocked on modules requiring
    Micro Jump Drive Operation;
  * Assault Damage Control: Effect2302 (passive) multiplies the ship's
    resonances by the module's own resonance attributes (penaltyGroup preMul);
    Effect7012 (active, runTime early) first forces those module attributes
    to resistanceMultiplier.
Defaults (plan section 3, the owner's D2/D3): siege family ACTIVE; MJD, cloak,
Signature Suppressor burst, Entosis Link ONLINE; Assault Damage Control
ONLINE (its active part is a short burst, same reasoning as D3).
"""
import sys, os, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indep_common import *

def stable(capacity, rechargeSec, drain):
    """EVE-client closed form (pyfa cap_stable_eve): stable when 4k <= 1,
    k = drain * tau / (2 * capacity), tau = rechargeTime / 5.
    This is the EVE closed form (pyfa cap_stable_eve). Since v2026.10.14.1 the tool shows
    pyfa's simulation instead (check_cap_sim.py); this value is the ring-hover figure."""
    tau = rechargeSec / 5
    k = drain * tau / (2 * capacity)
    return (1 - 4 * k) >= 0

CM = SK('Capacitor Management', 'capacitorCapacityBonus')
CSO = SK('Capacitor Systems Operation', 'capRechargeBonus')

# ---- A: Vargur -- Large Shield Booster II, Shield Boost Amplifier II, Large Micro Jump Drive, Bastion Module I
v, lsb, sba, mjd, bas = A('Vargur'), A('Large Shield Booster II'), A('Shield Boost Amplifier II'), A('Large Micro Jump Drive'), A('Bastion Module I')
LSC = SK('Ladar Sensor Compensation', 'sensorStrengthBonus')
hull = b(v['eliteBonusViolators2'] * 5)
def vargur(bastionActive, mjdActive):
    sens = v['scanLadarStrength'] * LSC * (pen([b(bas['scanLadarStrengthPercent'])]) if bastionActive else 1)
    amt = lsb['shieldBonus'] * hull * pen([b(sba['shieldBoostMultiplier'])] + ([b(bas['shieldBoostMultiplier'])] if bastionActive else []))
    cd = b(bas['bastionModeShieldBoosterCapDurationBonus']) if bastionActive else 1
    cyc = lsb['duration'] / 1000 * cd
    drain = lsb['capacitorNeed'] * SK('Shield Compensation', 'shieldBoostCapacitorBonus') * cd / cyc
    # v2026.10.14.1 (LESSON #20): pyfa averages over active cycle + moduleReactivationDelay (attr 669)
    if mjdActive: drain += mjd['capacitorNeed'] / (mjd['duration'] / 1000 * SK('Micro Jump Drive Operation', 'durationBonus') + mjd['moduleReactivationDelay'] / 1000)
    return round(sens, 2), round(amt / cyc, 1), round(drain, 3)
print('A Vargur default (Bastion active, MJD online): sensor, LSB HP/s, drain', vargur(True, False))
print('A Vargur {Bastion online, MJD active}:          ', vargur(False, True))
print('A Vargur {MJD active} -> refused (Bastion blocks MJD), same as default; activationBlockedStrenght', bas['activationBlockedStrenght'])

# ---- B: Rifter -- Small Armor Repairer II, Damage Control II, 5MN Microwarpdrive II, 1MN Afterburner II
r, sar, mwd, ab = A('Rifter'), A('Small Armor Repairer II'), A('5MN Microwarpdrive II'), A('1MN Afterburner II')
capR = r['capacitorCapacity'] * CM * mwd['capacitorCapacityMultiplier']   # MWD capacity penalty: Effect58, passive (online)
recR = r['rechargeRate'] / 1000 * CSO
dMWD = mwd['capacitorNeed'] * SK('High Speed Maneuvering', 'capNeedBonus') / (mwd['duration'] / 1000)
dAB = ab['capacitorNeed'] * SK('Afterburner', 'capNeedBonus') * SK('Fuel Conservation', 'capNeedBonus') / (ab['duration'] / 1000 * SK('Afterburner', 'durationBonus'))
dSAR = sar['capacitorNeed'] / (sar['duration'] / 1000 * SK('Repair Systems', 'durationSkillBonus'))
print('B Rifter speedFactor MWD', mwd['speedFactor'], 'AB', ab['speedFactor'], '-> default primary active = MWD; cap', round(capR, 2), 'recharge s', recR)
for lbl, d in (('default {MWD, SAR active; AB online}', dMWD + dSAR), ('{AB active, MWD online}', dAB + dSAR),
               ('{AB active, MWD online, SAR offline}', dAB), ('{SAR offline} (MWD active)', dMWD)):
    print('   ', lbl, 'drain', round(d, 3), 'stable', stable(capR, recR, d))
print('    {1MN Afterburner II: active} alone -> refused: Propulsion Module maxGroupActive', mwd['maxGroupActive'])

# ---- C: Rifter -- Assault Damage Control II, EM Armor Hardener II
adc, hard = A('Assault Damage Control II'), A('EM Armor Hardener II')
hb = b(hard['emDamageResistanceBonus'])
def armorEm(adcState, hardOn):
    m = r['armorEmDamageResonance'] * (pen([hb]) if hardOn else 1)
    if adcState == 'online': m *= adc['armorEmDamageResonance']
    if adcState == 'active': m *= adc['resistanceMultiplier']
    return round((1 - m) * 100, 2)
def hullEm(adcState):
    m = r['emDamageResonance']
    if adcState == 'online': m *= adc['hullEmDamageResonance']
    if adcState == 'active': m *= adc['resistanceMultiplier']
    return round((1 - m) * 100, 2)
print('C Rifter armor EM resist %: default (ADC online, hardener active)', armorEm('online', True), 'hull EM', hullEm('online'))
print('   {EM Armor Hardener II: offline}', armorEm('online', False))
print('   {Assault Damage Control II: active}', armorEm('active', True), 'hull EM', hullEm('active'))
print('   {Assault Damage Control II: offline}', armorEm('offline', True), 'hull EM', hullEm('offline'))
dH, dA = hard['capacitorNeed'] / (hard['duration'] / 1000), adc['capacitorNeed'] / ((adc['duration'] + adc['moduleReactivationDelay']) / 1000)  # + reactivation delay, LESSON #20
print('   drain: default (hardener only)', round(dH, 3), '| ADC active', round(dH + dA, 3), '| hardener offline 0')

# ---- D/E: Command Burst group limits
acb, d, p = A('Armor Command Burst II'), A('Damnation'), A('Prophecy')
one = acb['capacitorNeed'] / (acb['duration'] / 1000)
print('D Prophecy 2x Armor Command Burst II: maxGroupOnline', acb['maxGroupOnline'], 'maxGroupActive', acb['maxGroupActive'], '-> 1 active, 1 offline; drain', round(one, 4))
lim = acb['maxGroupActive'] + d['maxGangModules']
print('E Damnation 3x Armor Command Burst II: limit', lim, '-> 2 active, 1 offline; drain', round(lim * one, 4))
