"""HP pools (v2026.10.13.14). Hand-typed pyfa rules, none stacking-penalized:
(base + flat adds) x skills x module/rig multipliers x rig drawbacks (x0.5 at
rigging V) x hull/role bonuses."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indep_common import *
SM = SK('Shield Management', 'shieldCapacityBonus'); HU = SK('Hull Upgrades', 'armorHpBonus'); ME = SK('Mechanics', 'hullHpBonus')
m=A('Megathron'); pl=A('1600mm Steel Plates II'); lem=A('Layered Energized Membrane II'); lc=A('Layered Coating II'); rb=A('Reinforced Bulkheads II'); pds=A('Power Diagnostic System II')
lse=A('Large Shield Extender II'); tri=A('Large Trimark Armor Pump II'); tb=A('Large Transverse Bulkhead II'); poly=A('Large Polycarbon Engine Housing I')
print('megathron role', {k:m.get(k) for k in ('battleshipPlateHPBonus','battleshipExtenderHPBonus','battleshipBulkheadHPModifierBonus')})
sh=(m['shieldCapacity']+lse['capacityBonus']*(1+m['battleshipExtenderHPBonus']/100))*SM*pds['shieldCapacityMultiplier']
ar=(m['armorHP']+pl['armorHPBonusAdd']*(1+m['battleshipPlateHPBonus']/100))*HU*lem['armorHPMultiplier']*lc['armorHPMultiplier']*(1+tri['armorHpBonus']/100)*(1+poly['drawback']*0.5/100)
hu=m['hp']*ME*(rb['structureHPMultiplier']+m['battleshipBulkheadHPModifierBonus'])*(1+tb['hullHpBonus']/100)
print('Megathron constructed (15921 / 25855 / 16758)', round(sh,1), round(ar,1), round(hu,1), 'mults', lem['armorHPMultiplier'], lc['armorHPMultiplier'], tri['armorHpBonus'], tb['hullHpBonus'], poly['drawback'], rb['structureHPMultiplier'])
g=A('Guardian'); mse=A('Medium Shield Extender II'); ifp=A('Medium Ionic Field Projector II')
sh=(g['shieldCapacity']+mse['capacityBonus'])*SM*(1+ifp['drawback']*0.5/100)
ar=(g['armorHP']+pl['armorHPBonusAdd']*(1+g['eliteBonusLogistics4']*5/100))*HU
print('Guardian constructed (2559 / 10886 / 2505)', round(sh,1), round(ar,1), round(g['hp']*ME,1))
