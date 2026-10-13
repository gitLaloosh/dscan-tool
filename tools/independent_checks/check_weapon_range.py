"""Weapon range (v2026.10.13.17). Hand-typed pyfa rules:
turret optimal = maxRange x ammo weaponRangeMultiplier x Sharpshooter V (Gunnery
weapons only) x hull/subsystem (unpenalized) x pen[modules, rigs, Bastion] x T3D
Sharpshooter Mode 1/attr1990; falloff likewise with Trajectory Analysis.
missile distance = maxVelocity x Missile Projection V x hull x pen[...] x
explosionDelay x Missile Bombardment V x pen[...]. Scripts scale the
Tracking/Guidance Computer's own bonus by (1 + script bonusBonus/100)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indep_common import *
SS = SK('Sharpshooter', 'rangeSkillBonus'); TA = SK('Trajectory Analysis', 'falloffBonus')
MP = SK('Missile Projection', 'speedFactor'); MB = SK('Missile Bombardment', 'maxFlightTimeBonus')
GUNNERY = int(T('Gunnery'))
def turret(w, ammo, hullOpt=1, hullFal=1, penOpt=(), penFal=(), extra=1):
    W, C = A(w), A(ammo)
    g = GUNNERY in reqs(T(w))
    o = W['maxRange'] * C.get('weaponRangeMultiplier', 1) * (SS if g else 1) * hullOpt * pen(list(penOpt)) * extra
    f = W.get('falloff', 0) * C.get('fallofMultiplier', 1) * (TA if g else 1) * hullFal * pen(list(penFal))
    return round(o), round(f)
def missile(ch, hullV=1, penV=(), penT=()):
    C = A(ch); return round(C['maxVelocity'] * MP * hullV * pen(list(penV)) * C['explosionDelay'] / 1000 * MB * pen(list(penT)))
te, tc = A('Tracking Enhancer II'), A('Tracking Computer II')
ors, tss = A('Optimal Range Script'), A('Tracking Speed Script')
bas = A('Bastion Module I')
lcm = A('Legion Offensive - Liquid Crystal Magnifiers')
print('Legion pyfa fit (16831/13564)', turret('Heavy Beam Laser II', 'Gleam M', hullOpt=b(lcm['subsystemBonusAmarrOffensive3'] * 5),
      penOpt=[b(te['maxRangeBonus']), b(tc['maxRangeBonus']), b(A('Medium Energy Locus Coordinator II')['maxRangeBonus'])],
      penFal=[b(te['falloffBonus']), b(tc['falloffBonus'])]))
tcs_r = b(tc['maxRangeBonus'] * b(tss['maxRangeBonusBonus'])); tcs_f = b(tc['falloffBonus'] * b(tss['falloffBonusBonus']))
print('Paladin (27818/15625)', turret('Mega Pulse Laser II', 'Conflagration L', hullOpt=b(A('Paladin')['shipBonusAB'] * 5),
      penOpt=[b(bas['maxRangeBonus']), tcs_r, tcs_r, b(A('Large Energy Locus Coordinator I')['maxRangeBonus'])], penFal=[b(bas['falloffBonus']), tcs_f, tcs_f]))
ftc = A('Federation Navy Tracking Computer')
fo = lambda s: b(ftc['maxRangeBonus'] * b(s['maxRangeBonusBonus'])); ff = lambda s: b(ftc['falloffBonus'] * b(s['falloffBonusBonus']))
print('Kronos (46132/65076)', turret('425mm Railgun II', 'Antimatter Charge L', hullFal=b(A('Kronos')['shipBonusGB2'] * 5),
      penOpt=[b(bas['maxRangeBonus']), fo(ors), fo(tss)], penFal=[b(bas['falloffBonus']), ff(ors), ff(tss)]))
print('Golem (82013)', missile('Inferno Javelin Torpedo', hullV=b(A('Golem')['shipBonusCB3'] * 5), penV=[b(bas['missileVelocityBonus'])]))
mgc, mps, mrs = A('Missile Guidance Computer II'), A('Missile Precision Script'), A('Missile Range Script')
print('Muninn (16875)', missile('Mjolnir Rage Heavy Assault Missile', penV=[b(mgc['missileVelocityBonus'] * b(mps['missileVelocityBonusBonus']))],
      penT=[b(mgc['explosionDelayBonus'] * b(mps['explosionDelayBonusBonus']))]))
print('Hawk (12656)', missile('Mjolnir Rage Rocket', hullV=b(A('Hawk')['eliteBonusGunship1'] * 5)))
print('Caracal (94331)', missile('Caldari Navy Mjolnir Heavy Missile', hullV=b(A('Caracal')['shipBonusCC2'] * 5)))
print('Confessor Sharpshooter (6563)', turret('Small Focused Pulse Laser II', 'Conflagration S', extra=1 / A('Confessor Sharpshooter Mode')['modeMaxRangePostDiv']))
print('Stormbringer (33000)', turret('Medium Vorton Projector II', 'ElectroPunch Ultra M', hullOpt=b(A('Stormbringer')['shipBonusUC1'] * 5), extra=SK('Vorton Arc Extension', 'rangeSkillBonus')))
loc, amb = A('Large Hybrid Locus Coordinator II'), A('Large Hybrid Ambit Extension II')
print('Rokh constructed (278993/49752)', turret('425mm Railgun II', 'Spike L', hullOpt=b(A('Rokh')['shipBonusCB'] * 5),
      penOpt=[b(te['maxRangeBonus'])] * 3 + [b(tc['maxRangeBonus'] * b(ors['maxRangeBonusBonus'])), b(tc['maxRangeBonus'])] + [b(loc['maxRangeBonus'])] * 2,
      penFal=[b(te['falloffBonus'])] * 3 + [b(tc['falloffBonus'] * b(ors['falloffBonusBonus'])), b(tc['falloffBonus']), b(amb['falloffBonus'])]))
mge, hbt, rfc = A('Missile Guidance Enhancer II'), A('Large Hydraulic Bay Thrusters II'), A('Large Rocket Fuel Cache Partition II')
print('Raven constructed (424649)', missile('Scourge Cruise Missile', hullV=b(A('Raven')['shipBonusCB3'] * 5),
      penV=[b(mge['missileVelocityBonus'])] * 2 + [b(mgc['missileVelocityBonus'] * b(mrs['missileVelocityBonusBonus'])), b(hbt['speedFactor'])],
      penT=[b(mge['explosionDelayBonus'])] * 2 + [b(mgc['explosionDelayBonus'] * b(mrs['explosionDelayBonusBonus'])), b(rfc['maxFlightTimeBonus'])]))
print('Hecate Sharpshooter (5250/4375)', turret('Light Neutron Blaster II', 'Null S', extra=1 / A('Hecate Sharpshooter Mode')['modeMaxRangePostDiv']))
print('Jackdaw Sharpshooter (70313)', missile('Scourge Light Missile', hullV=1 / A('Jackdaw Sharpshooter Mode')['modeMaxRangePostDiv']))
