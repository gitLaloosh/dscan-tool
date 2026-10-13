"""Rows added by the recorder audit of the older text-matched tables
(v2026.10.13.19, tools/audit_effect_tables.py). Hand-typed pyfa rules:
  * Triage Module (6581): remote rep cycle x(1 + siegeRemoteLogisticsDurationBonus/100),
    cap need unchanged -> drain x4.  Skills: Remote Armor Repair Systems (1030, also
    hits capital remote reps) and Capital Remote Armor Repair Systems (2354), -5%/lvl each.
  * Valravn / Naglfar FI (11373): capital local rep/boost amount +shipBonusDreadnoughtM1 x5.
  * Remote Hull Repair Systems skill (2979): -5%/lvl remote hull repairer cap need.
  * Bastion (6658): +100% sensor strength, penalized with Sensor Boosters/Signal Amps."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indep_common import *
crar, tri = A('Capital Remote Armor Repairer II'), A('Triage Module II')
skills = SK('Remote Armor Repair Systems', 'capNeedBonus') * SK('Capital Remote Armor Repair Systems', 'capNeedBonus')
base = 2 * crar['capacitorNeed'] * skills / (crar['duration'] / 1000)
print('Apostle 2x CRAR II, no triage (146.3)', round(base, 2))
print('Apostle 2x CRAR II + Triage II (585)', round(base / b(tri['siegeRemoteLogisticsDurationBonus']), 2))
csb = A('Capital Shield Booster II')
print('Valravn Capital Shield Booster II HP/s (1080)', round(csb['shieldBonus'] * b(A('Valravn')['shipBonusDreadnoughtM1'] * 5) / (csb['duration'] / 1000), 1))
rhr = A('Medium Remote Hull Repairer II')
print('Exequror Medium Remote Hull Repairer II drain (30.5)', round(rhr['capacitorNeed'] * SK('Remote Hull Repair Systems', 'capNeedBonus') / (rhr['duration'] / 1000), 2))
bas = A('Bastion Module I')
SC = SK('Gravimetric Sensor Compensation', 'sensorStrengthBonus')
for ship, key in (('Paladin', 'scanRadarStrength'), ('Kronos', 'scanMagnetometricStrength'), ('Golem', 'scanGravimetricStrength'), ('Vargur', 'scanLadarStrength')):
    pct = bas[key + 'Percent']
    print(f'{ship} + Bastion sensor strength', round(A(ship)[key] * SC * b(pct), 1))
