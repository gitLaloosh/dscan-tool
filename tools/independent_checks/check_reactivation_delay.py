"""Reactivation delay in capacitor drain (v2026.10.14.1). Hand-typed pyfa rules, SDE values.

pyfa eos/saveddata/module.py getCycleParameters(): with reload not factored,
CycleInfo(activeTime = rawCycleTime, inactiveTime = reactivationDelay
(moduleReactivationDelay, attr 669)); capUse = capacitorNeed / averageTime where
averageTime = activeTime + inactiveTime. fit.__generateDrain() passes the same
fullCycleTime = cycleTime + reactivationTime to the cap simulator.
Modifiers of moduleReactivationDelay (tools/pyfa_effects.py recorder): Interceptor
role 8120 on Interdiction Nullifiers (shipBonusRole1), Command Destroyer roles
6845/7210 on Defender Launchers. Skills on the active cycle: Micro Jump Drive
Operation (MJD duration), Signature Masking (+5%/lvl durationHighisGood)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indep_common import *

mjd = A('Large Micro Jump Drive'); MJDO = SK('Micro Jump Drive Operation', 'durationBonus')
mjd_drain = mjd['capacitorNeed'] / (mjd['duration'] / 1000 * MJDO + mjd['moduleReactivationDelay'] / 1000)
lsb = A('Large Shield Booster II')
lsb_bastion_online = lsb['capacitorNeed'] * SK('Shield Compensation', 'shieldBoostCapacitorBonus') / (lsb['duration'] / 1000)
print('Vargur Bastion ONLINE + MJD ACTIVE: drain', lsb_bastion_online + mjd_drain, '(MJD', mjd_drain, ', was 87.33 without the delay)')

sup = A('Signature Radius Suppressor I'); SM = 1 + A('Signature Masking')['durationBonus'] * 5 / 100
sup_drain = sup['capacitorNeed'] / (sup['durationHighisGood'] / 1000 * SM + sup['moduleReactivationDelay'] / 1000)
print('Raven Suppressor ACTIVE: drain', sup_drain, '| Suppressor + MJD ACTIVE:', sup_drain + mjd_drain)

cr, nul = A('Crow'), A('Interdiction Nullifier II')
nul_drain = nul['capacitorNeed'] / (nul['durationHighisGood'] / 1000 * b(cr['shipBonusRole2']) + nul['moduleReactivationDelay'] / 1000 * b(cr['shipBonusRole1']))
print('Crow Nullifier: drain', nul_drain)

adc, eah = A('Assault Damage Control II'), A('EM Armor Hardener II')
eah_drain = eah['capacitorNeed'] / (eah['duration'] / 1000)
adc_drain = adc['capacitorNeed'] / (adc['duration'] / 1000 + adc['moduleReactivationDelay'] / 1000)
print('Rifter ADC ACTIVE + EM hardener: drain', eah_drain + adc_drain, '(ADC', adc_drain, ', duration', adc['duration'], ')')

w = A('Warp Core Stabilizer II')
wcs_old, wcs_new = w['capacitorNeed'] / (w['duration'] / 1000), w['capacitorNeed'] / ((w['duration'] + w['moduleReactivationDelay']) / 1000)
print('Warp Core Stabilizer II (active by default): drain', wcs_new, 'was', wcs_old, '-> caracal_constructed_sensor_boosters_scripts_wcs drops by', wcs_old - wcs_new)
print('crow_constructed_interceptor_nullifier_role_bonus: the Nullifier part drops from', nul['capacitorNeed'] / (nul['durationHighisGood'] / 1000 * b(cr['shipBonusRole2'])), 'to', nul_drain)
