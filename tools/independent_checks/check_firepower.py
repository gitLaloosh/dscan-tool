"""Firepower fix (hand-tables Phase 1). Expected DPS for constructed fits, from
hand-typed pyfa rules and SDE values only -- nothing from index.html.

Rules (pyfa eos/effects.py; all hull bonuses here are unpenalized):
  turret   shot = sum(ammo damage) x weapon damageMultiplier x Surgical Strike V x size skill V
                  [x Specialization V if the weapon requires it] x hull;  cycle = speed x Gunnery V x Rapid Firing V x hull
  vorton   shot = ... x Vorton Power Amplification V x size skill V x hull; cycle = speed x Vorton Projector Operation V x hull
  missile  per damage type: charge damage x Warhead Upgrades V x class skill V x hull bonus FOR THAT TYPE;
           cycle = launcher speed x Missile Launcher Operation V x Rapid Launch V x hull
  drone    sum(damage) x drone damageMultiplier x Drone Interfacing V x size skill V x racial spec V x hull
           x pen[drone damage modules: every module carrying moduleBonusDroneDamageAmplifier]; cycle = speed
  fighter  Attack Missile: sum(damage) x ability multiplier x squadron size x Fighters V x Drone Interfacing V
           (fighter clause) x hull x pen[drone damage modules] / duration
Hull handlers read by hand: Leviathan 6635 (C1, kinetic only, XL torps/cruise), 6657 (C5, em/therm/exp),
6638 (C2, XL launcher speed); Akoman 12949 (role7, Large Energy Turret damage); Thunderchild 8054/8056
(UB1 Large Vorton damage, UB2 speed); Nemesis 4393 (eliteBonusCovertOps2, thermal torpedo damage only);
Gnosis 3483 (role7, Medium Energy Turret damage); Caracal 5131 (shipBonusCC speed, Heavy / Heavy Assault /
Rapid Light launchers ONLY); Anhinga: no damage or rate-of-fire effect at all; Dominix 2187 (GB2 drones);
Thanatos 6601 (CarrierG1 fighters)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indep_common import *

SS, GUN, RF = SK('Surgical Strike', 'damageMultiplierBonus'), SK('Gunnery', 'turretSpeeBonus'), SK('Rapid Firing', 'rofBonus')
WU, MLO, RL = SK('Warhead Upgrades', 'damageMultiplierBonus'), SK('Missile Launcher Operation', 'rofBonus'), SK('Rapid Launch', 'rofBonus')
VPA, VPO = SK('Vorton Power Amplification', 'damageMultiplierBonus'), SK('Vorton Projector Operation', 'turretSpeeBonus')
DI, FTR = SK('Drone Interfacing', 'damageMultiplierBonus'), SK('Fighters', 'damageMultiplierBonus')
DT = ('emDamage', 'thermalDamage', 'kineticDamage', 'explosiveDamage')

def turret(w, ammo, sizeSkill, hullDmg=1, hullCyc=1, spec=None):
    W, C = A(w), A(ammo)
    shot = sum(C.get(d, 0) for d in DT) * W['damageMultiplier'] * SS * SK(sizeSkill, 'damageMultiplierBonus') * (SK(spec, 'damageMultiplierBonus') if spec else 1) * hullDmg
    return shot / (W['speed'] / 1000 * GUN * RF * hullCyc)
def vorton(w, ammo, sizeSkill, hullDmg=1, hullCyc=1, spec=None, modDmg=(), modCyc=()):
    W, C = A(w), A(ammo)
    shot = sum(C.get(d, 0) for d in DT) * W['damageMultiplier'] * VPA * SK(sizeSkill, 'damageMultiplierBonus') * (SK(spec, 'damageMultiplierBonus') if spec else 1) * hullDmg * pen(list(modDmg))
    return shot / (W['speed'] / 1000 * VPO * hullCyc * pen(list(modCyc)))
def missile(launcher, ch, classSkill, hullByType=None, hullCyc=1):
    L, C = A(launcher), A(ch); hullByType = hullByType or {}
    shot = sum(C.get(d, 0) * hullByType.get(d, 1) for d in DT) * WU * SK(classSkill, 'damageMultiplierBonus')
    return shot / (L['speed'] / 1000 * MLO * RL * hullCyc)

out = {}
lev = A('Leviathan')
c1, c5, c2 = b(lev['shipBonusTitanC1'] * 5), b(lev['shipBonusTitanC5'] * 5), b(lev['shipBonusTitanC2'] * 5)
out['Leviathan, XL Torpedo Launcher I + Scourge XL Torpedo (kinetic)'] = missile('XL Torpedo Launcher I', 'Scourge XL Torpedo', 'XL Torpedoes', {'kineticDamage': c1, 'emDamage': c5, 'thermalDamage': c5, 'explosiveDamage': c5}, c2)
out['Leviathan, XL Torpedo Launcher I + Mjolnir XL Torpedo (EM)'] = missile('XL Torpedo Launcher I', 'Mjolnir XL Torpedo', 'XL Torpedoes', {'kineticDamage': c1, 'emDamage': c5, 'thermalDamage': c5, 'explosiveDamage': c5}, c2)
out['Anhinga, Cruise Missile Launcher I + Inferno Cruise Missile (no hull bonus)'] = missile('Cruise Missile Launcher I', 'Inferno Cruise Missile', 'Cruise Missiles')
out['Akoman, Mega Pulse Laser II + Multifrequency L'] = turret('Mega Pulse Laser II', 'Multifrequency L', 'Large Energy Turret', b(A('Akoman')['shipBonusRole7']), spec='Large Pulse Laser Specialization')
th = A('Thunderchild')
out['Thunderchild, Large Vorton Projector I + GalvaSurge Condenser Pack L'] = vorton('Large Vorton Projector I', 'GalvaSurge Condenser Pack L', 'Large Vorton Projector', b(th['shipBonusUB1'] * 5), b(th['shipBonusUB2'] * 5))
out['Nemesis, Torpedo Launcher I + Mjolnir Torpedo (EM: thermal bonus does not apply)'] = missile('Torpedo Launcher I', 'Mjolnir Torpedo', 'Torpedoes', {'thermalDamage': b(A('Nemesis')['eliteBonusCovertOps2'] * 5)})
out['Gnosis, Heavy Pulse Laser I + Multifrequency M'] = turret('Heavy Pulse Laser I', 'Multifrequency M', 'Medium Energy Turret', b(A('Gnosis')['shipBonusRole7']))
out['Caracal, Light Missile Launcher I + Scourge Light Missile (Caracal RoF bonus does not apply)'] = missile('Light Missile Launcher I', 'Scourge Light Missile', 'Light Missiles')

vts = A('Vorton Tuning System II')   # Vorton damage module: damageMultiplier / speedMultiplier, stacking-penalized
out['Stormbringer (zKill 138986635), Medium Vorton Projector II + ElectroPunch Ultra M + 3x Vorton Tuning System II'] = vorton(
    'Medium Vorton Projector II', 'ElectroPunch Ultra M', 'Medium Vorton Projector', spec='Medium Vorton Specialization', modDmg=[vts['damageMultiplier']] * 3, modCyc=[vts['speedMultiplier']] * 3)
out['Skybreaker, Small Vorton Projector II + GalvaSurge Condenser Pack S (hull 8048 shipBonusUF2)'] = vorton(
    'Small Vorton Projector II', 'GalvaSurge Condenser Pack S', 'Small Vorton Projector', b(A('Skybreaker')['shipBonusUF2'] * 5), spec='Small Vorton Specialization')
hh, neo = A('Hammerhead II'), A("Imperial Navy 'Neophyte' Heat Sink")
droneOne = sum(hh.get(d, 0) for d in DT) * hh['damageMultiplier'] * DI * SK('Medium Drone Operation', 'damageMultiplierBonus') * SK('Gallente Drone Specialization', 'damageMultiplierBonus') \
           * b(A('Dominix')['shipBonusGB2'] * 5) * pen([b(neo['droneDamageBonus'])]) / (hh['speed'] / 1000)
out["Dominix, 5x Hammerhead II + Imperial Navy 'Neophyte' Heat Sink (drone DPS)"] = 5 * droneOne

fb, dda = A('Firbolg I'), A('Drone Damage Amplifier II')
sq = sum(fb[k] for k in ('fighterAbilityAttackMissileDamageEM', 'fighterAbilityAttackMissileDamageTherm', 'fighterAbilityAttackMissileDamageKin', 'fighterAbilityAttackMissileDamageExp')) \
     * fb['fighterAbilityAttackMissileDamageMultiplier'] * fb['fighterSquadronMaxSize'] * FTR * DI * b(A('Thanatos')['shipBonusCarrierG1'] * 5) \
     * pen([b(dda['droneDamageBonus'])] * 3) / (fb['fighterAbilityAttackMissileDuration'] / 1000)
out['Thanatos, 3 squadrons Firbolg I + 3x DDA II, Attack Missile ability ONLY (= v2026.10.14.3; pyfa also counts Missiles, below)'] = 3 * sq
out['  (same, without the DDAs)'] = 3 * sq / pen([b(dda['droneDamageBonus'])] * 3)

# --- v2026.10.14.4: every fighter ability pyfa counts by default (the owner's pyfa screenshot: Thanatos +
# 3x DDA II + ONE squadron of Firbolg I = 831 DPS, volley 7,125). Rules, by hand from pyfa:
#   eos/saveddata/fighter.py Fighter.__init__: abilities in item-effect order; 'fighterAbilityAttackM'
#     is activated; every implemented ability BEFORE it is activated too, except MicroWarpDrive and
#     EvasiveManeuvers; nothing after it. (Every fighter's SDE effect list is in effect-ID order.)
#   -> Missiles (6431) + Attack Missile (6465) when both exist; superiority fighters (no 6465) get
#      Missiles; heavy bombers' LaunchBomb (6485, after 6465) is OFF.
#   fighterAbility.py getVolley: sum(<prefix>Damage EM..Exp) x amount x <prefix>DamageMultiplier;
#     getDps: volley / <prefix>Duration (factorReload off by default -> no rearm time).
#   Every damage handler (Fighters 6560, Drone Interfacing 6663, Heavy Fighters 6563, racial fighter
#     specs 12844-12848, carrier hulls 6601-6606, Caiman/Komodo 6984, 12869, DDA 6556) boosts the
#     Attack Missile AND Missiles multipliers alike; Fighter Support Unit 6566 multiplies both
#     Durations by fighterBonusROFPercent, stacking-penalized in its own 'postMul' group.
ABIL = ('fighterAbilityAttackMissile', 'fighterAbilityMissiles')
def fighter_squadron(name, hull, dda=0, fsu=()):
    F = A(name)
    mult = FTR * DI * hull * pen([b(A('Drone Damage Amplifier II')['droneDamageBonus'])] * dda)
    if gname(T(name)) == 'Heavy Fighter': mult *= SK('Heavy Fighters', 'damageMultiplierBonus')
    req3 = F.get('requiredSkill3')
    if req3: mult *= 1 + A(name_of(req3))['damageMultiplierBonus'] * 5 / 100
    dur = pen([A(m)['fighterBonusROFPercent'] for m in fsu])
    vol = dps = 0
    for p in ABIL:
        if p + 'Duration' not in F: continue
        v = sum(F.get(f'{p}Damage{t}', 0) for t in ('EM', 'Therm', 'Kin', 'Exp')) * F.get(p + 'DamageMultiplier', 1) * F['fighterSquadronMaxSize'] * mult
        vol += v; dps += v / (F[p + 'Duration'] * dur / 1000)
    return dps, vol
def name_of(tid): return name(int(tid))
thG1 = b(A('Thanatos')['shipBonusCarrierG1'] * 5)
d, v = fighter_squadron('Firbolg I', thG1, dda=3)
out["Thanatos + 3x DDA II, ONE squadron Firbolg I, all default abilities (pyfa screenshot 831 / volley 7,125)"] = d
out['  volley of the same'] = v
out['Thanatos + 3x DDA II, 3 squadrons Firbolg I, all default abilities'] = 3 * d
out['Thanatos + 2x Fighter Support Unit II, ONE squadron Firbolg I'] = fighter_squadron('Firbolg I', thG1, fsu=['Fighter Support Unit II'] * 2)[0]
out['Thanatos, ONE squadron Satyr I (superiority: Missiles ability only)'] = fighter_squadron('Satyr I', thG1)[0]
nyxG1 = b(A('Nyx')['shipBonusSupercarrierG1'] * 5)   # 6605; Thanatos has no heavy fighter slots
out['Nyx, ONE squadron Cyclops I (heavy: Missiles + Attack Missile)'] = fighter_squadron('Cyclops I', nyxG1)[0]
out['Nyx, ONE squadron Ametat I (heavy bomber: Attack Missile only, bomb ability off)'] = fighter_squadron('Ametat I', nyxG1)[0]
out['Thanatos, ONE squadron Satyr II (T2: Gallente Fighter Specialization)'] = fighter_squadron('Satyr II', thG1)[0]

# Older fighter goldens (2026-10-08/11 hand derivations counted Attack Missile only and claimed pyfa
# had no fighter DPS -- it does; the owner's screenshot). Re-derived here:
out['thanatos_zkb138975919_fighter_bay as fixtured (its 2x Fighter Support Unit I are not in the fixture): Thanatos, 6x Templar I'] = fighter_squadron('Templar I', thG1)[0]
out['  the real ship WITH its 2x Fighter Support Unit I'] = fighter_squadron('Templar I', thG1, fsu=['Fighter Support Unit I'] * 2)[0]
out['nyx_constructed_heavy_fighter_specialization_bonus: Nyx, 6x Cyclops I'] = fighter_squadron('Cyclops I', nyxG1)[0]
out['thanatos_constructed_t2_light_fighter_specialization_bonus: Thanatos, 6x Templar II'] = fighter_squadron('Templar II', thG1)[0]

for k, v in out.items(): print(f'{k}: {v:.2f}')
