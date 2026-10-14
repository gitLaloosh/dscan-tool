"""Capacitor best case (v2026.10.13.27): the ring toggle is gone, the capacitor
figures are the best case of the RUNNING modules. Hand-typed pyfa rules, SDE values.

pyfa (eos/saveddata/fit.py capUsed / capDelta; module.py): an Ancillary Shield
Booster with a charge loaded uses no capacitor; without one it draws capacitorNeed
per cycle. Capacitor Booster injection is averaged over cycles + reload (see
check_capacitor.py for the reload rule). Skills (recorder-checked):
Shield Compensation (capacitorNeed of modules requiring Shield Operation),
Afterburner and Fuel Conservation (Afterburner cap need), Afterburner (duration)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indep_common import *

# ---- Hawk: Medium Ancillary Shield Booster (Navy Cap Booster 50) + 1MN Afterburner II
asb, ab, hawk = A('Medium Ancillary Shield Booster'), A('1MN Afterburner II'), A('Hawk')
ab_drain = ab['capacitorNeed'] * SK('Afterburner', 'capNeedBonus') * SK('Fuel Conservation', 'capNeedBonus') / (ab['duration'] / 1000 * SK('Afterburner', 'durationBonus'))
asb_drain = asb['capacitorNeed'] * SK('Shield Compensation', 'shieldBoostCapacitorBonus') / (asb['duration'] / 1000)
cap = hawk['capacitorCapacity'] * SK('Capacitor Management', 'capacitorCapacityBonus')
tau = hawk['rechargeRate'] / 1000 * SK('Capacitor Systems Operation', 'capRechargeBonus')
peak = 2.5 * cap / tau
print('Hawk ASB charged (default): drain', ab_drain, 'net', peak - ab_drain)
print('Hawk ASB out of charges: drain', ab_drain + asb_drain, 'net', peak - ab_drain - asb_drain, '(ASB alone', asb_drain, ')')
print('peak recharge', peak, 'capacity', cap)
