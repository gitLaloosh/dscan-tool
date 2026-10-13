"""Local repairs (v2026.10.13.15). Hand-typed pyfa rules: amount x hull bonus
(x5, unpenalized) x pen[Aux Nano Pump rigs / Shield Boost Amplifiers]; cycle x
Repair Systems V (armor/hull). Passive regen peak = 2.5 x shield HP / recharge time."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indep_common import *
RS = SK('Repair Systems', 'durationSkillBonus')
h, lar, anp = A('Hyperion'), A('Large Armor Repairer II'), A('Large Auxiliary Nano Pump II')
amt = lar['armorDamageAmount'] * b(h['shipBonusGB2'] * 5) * pen([b(anp['repairBonus'])] * 2)
cyc = lar['duration'] / 1000 * RS
print('Hyperion (317 HP/s, 71.1 GJ/s)', round(2 * amt / cyc, 1), round(2 * lar['capacitorNeed'] / cyc, 1))
m, xl, sba = A('Maelstrom'), A('X-Large Shield Booster II'), A('Shield Boost Amplifier II')
pur, po = A('Large Core Defense Field Purger II'), A('Large Processor Overclocking Unit I')
amt = xl['shieldBonus'] * b(m['shipBonusMB'] * 5) * pen([b(sba['shieldBoostMultiplier'])] * 2)
print('Maelstrom booster (370 HP/s, 72 GJ/s)', round(amt / (xl['duration'] / 1000), 1),
      round(xl['capacitorNeed'] * SK('Shield Compensation', 'shieldBoostCapacitorBonus') / (xl['duration'] / 1000), 1))
shieldHP = m['shieldCapacity'] * SK('Shield Management', 'shieldCapacityBonus')
tau = m['shieldRechargeRate'] / 1000 * SK('Shield Operation', 'rechargeratebonus') * b(pur['rechargeratebonus']) * po['shieldRechargeRateMultiplier']
print('Maelstrom passive peak (19)', round(2.5 * shieldHP / tau, 1))
