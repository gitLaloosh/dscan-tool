"""Required skills 4-6 (v2026.10.13.21). Hand-typed pyfa rules with SDE values.

pyfa's requiresSkill() checks an item's DIRECT required skills, read from the
SDE table requiredskillsfortypes -- identical, for every published type, to
attributes requiredSkill1-6 (182, 183, 184, 1285, 1289, 1290). The tool read
only 1-3.
  * Capital T2 turrets carry Gunnery in slot 4: Controlled Bursts (cap need),
    Sharpshooter / Trajectory Analysis (range) and Tracking Enhancers /
    Computers (Gunnery-filtered) all apply in pyfa.
  * Turret Specialization skills (+2%/level damage) apply only to turrets that
    require one (pyfa Effect1003-1020, 6571-6576, 7074-7076, 8044-8046, 12862).
    The tool used "has requiredSkill3" as a stand-in, which is wrong for the
    non-T2 capital short-range turrets (their slot 3 is Gunnery or Motion
    Prediction): +10% DPS too much.
  * Drone damage skills (pyfa Effect1730) boost drones requiring THAT skill.
    Aralez requires both Gallente and Caldari Drone Specialization (slots 3, 4):
    x1.10 twice.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indep_common import *

SS = SK('Sharpshooter', 'rangeSkillBonus'); TA = SK('Trajectory Analysis', 'falloffBonus')
SURG = SK('Surgical Strike', 'damageMultiplierBonus'); CET = SK('Capital Energy Turret', 'damageMultiplierBonus')
SPEC = SK('Capital Pulse Laser Specialization', 'damageMultiplierBonus')
GUN = SK('Gunnery', 'turretSpeeBonus'); RF = SK('Rapid Firing', 'rofBonus'); CB = SK('Controlled Bursts', 'capNeedBonus')
rev, te, mf = A('Revelation'), A('Tracking Enhancer II'), A('Multifrequency XL')
A1 = b(rev['shipBonusDreadnoughtA1'] * 5); A3 = b(rev['shipBonusDreadnoughtA3'] * 5)
GUNNERY, CPLS = int(T('Gunnery')), int(T('Capital Pulse Laser Specialization'))

def revelation(gun, n=2):
    W = A(gun); r = reqs(T(gun))
    g = GUNNERY in r; spec = SPEC if CPLS in r else 1
    cyc = W['speed'] / 1000 * GUN * RF
    shot = (mf['emDamage'] + mf['thermalDamage']) * W['damageMultiplier'] * SURG * CET * spec * A1
    cap = W['capacitorNeed'] * (CB if g else 1) * A3 * b(mf.get('capNeedBonus', 0))
    opt = W['maxRange'] * mf['weaponRangeMultiplier'] * (SS if g else 1) * (pen([b(te['maxRangeBonus'])]) if g else 1)
    fal = W['falloff'] * (TA if g else 1) * (pen([b(te['falloffBonus'])]) if g else 1)
    return {'dps': round(n * shot / cyc, 1), 'capGJs': round(n * cap / cyc, 3), 'optimal': round(opt), 'falloff': round(fal),
            'gunnery': g, 'spec': spec}

print('Revelation 2x Quad Mega Pulse Laser II + TE II, Multifrequency XL:', revelation('Quad Mega Pulse Laser II'))
print('Revelation 2x Quad Mega Pulse Laser I + TE II, Multifrequency XL: ', revelation('Quad Mega Pulse Laser I'))

ar = A('Aralez')
DI = SK('Drone Interfacing', 'damageMultiplierBonus'); MDO = SK('Medium Drone Operation', 'damageMultiplierBonus')
GDS = SK('Gallente Drone Specialization', 'damageMultiplierBonus'); CDS = SK('Caldari Drone Specialization', 'damageMultiplierBonus')
per = (ar['kineticDamage'] + ar['thermalDamage'] + ar['emDamage'] + ar['explosiveDamage']) * ar['damageMultiplier'] * DI * MDO * GDS * CDS / (ar['speed'] / 1000)
print('Abaddon 2x Aralez: drone DPS', round(2 * per, 1), '(bandwidth', ar['droneBandwidthUsed'], 'each of', A('Abaddon')['droneBandwidth'], ')')
