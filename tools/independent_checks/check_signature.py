"""Signature radius (v2026.10.13.16). Hand-typed pyfa rules:
base 552 + flat adds (2029 shield extender signatureRadiusAdd, 3808 T3 subsystem 552)
x hull bonuses (unpenalized, x5)  x pen[default: rig drawbackSigRad x0.5 rigging V,
Inertial Stabilizer 554, MWD 554 x its own modifiers]  x pen[postMul: Signature
Suppressor 3113]  x pen[postDiv: T3D Defense Mode 1/attr2001]."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indep_common import *
RIG = 0.5
HB = {'Hyena': 'eliteBonusElectronicAttackShip2', 'Monitor': 'shipBonusMC', 'Prospect': 'expeditionFrigateBonusSignatureRadius',
      'Thalia': 'eliteBonusLogiFrig2', 'Scalpel': 'eliteBonusLogiFrig2', 'Cyclone Fleet Issue': 'shipBonusMBC3'}
SIG_RIGS = ('Shield Reinforcer', 'Core Defense Field Extender', 'Hyperspatial Velocity Optimizer', 'Warp Core Optimizer')
def sig(shipn, items, mode=None):
    s = A(shipn); base = s['signatureRadius']; hull = 1; default = []; postmul = []; postdiv = []; mwd = None; mwdmod = 1
    if shipn in HB: hull *= b(s[HB[shipn]] * 5)
    if 'MWDSignatureRadiusBonus' in s: mwdmod *= b(s['MWDSignatureRadiusBonus'])        # AF/HAC/CD role
    if 'eliteBonusInterceptor' in s: mwdmod *= b(s['eliteBonusInterceptor'] * 5)
    if shipn == 'Svipul' and mode == 'defense': mwdmod *= 1 / A('Svipul Defense Mode')['modeMWDSigPenaltyPostDiv']
    if shipn in ('Confessor', 'Jackdaw') and mode == 'defense': postdiv.append(1 / A(shipn + ' Defense Mode')['modeSignatureRadiusPostDiv'])
    for n, q in items:
        a = A(n)
        for _ in range(q):
            if 'Shield Extender' in n: base += a.get('signatureRadiusAdd', 0)
            if 'Defensive -' in n or 'Propulsion -' in n: base += a.get('signatureRadius', 0)
            if 'Wake Limiter' in n: mwdmod *= b(a['subsystemBonusAmarrPropulsion2' if 'Legion' in n else 'subsystemBonusMinmatarPropulsion2'] * 5)
            if n.startswith('Inertial Stabilizers'): default.append(b(a['signatureRadiusBonus']))
            if any(k in n for k in SIG_RIGS) and a.get('drawback'): default.append(b(a['drawback'] * RIG))
            if 'Signature Radius Suppressor' in n: postmul.append(a['signatureSuppressorSignatureRadiusBonusPassive'])
            if 'Microwarpdrive' in n: mwd = a['signatureRadiusBonus']
    common = base * hull * pen(postmul) * pen(postdiv)
    return round(common * pen(default), 2), (round(common * pen(default + [b(mwd * mwdmod)]), 2) if mwd else None)
LEG = [('Legion Defensive - Covert Reconfiguration', 1), ('Legion Core - Dissolution Sequencer', 1), ('Legion Offensive - Liquid Crystal Magnifiers', 1)]
LRIGS = [('Medium Hyperspatial Velocity Optimizer II', 1), ('Medium Polycarbon Engine Housing II', 1), ('Medium Energy Locus Coordinator II', 1)]
CASES = [
 ('vagabond_constructed (132/415)', 'Vagabond', [('Inertial Stabilizers II', 2), ('50MN Microwarpdrive II', 1), ('Signature Radius Suppressor I', 1), ('Medium Hyperspatial Velocity Optimizer II', 2), ('Medium Core Defense Field Extender II', 1)], None),
 ('hyena_constructed (36/205)', 'Hyena', [('5MN Microwarpdrive II', 1), ('Small Warp Core Optimizer I', 1), ('Small EM Shield Reinforcer I', 1)], None),
 ('svipul defense (60/155)', 'Svipul', [('5MN Microwarpdrive II', 1)], 'defense'),
 ('legion wake limiter (184/616)', 'Legion', LEG + [('Legion Propulsion - Wake Limiter', 1), ('50MN Microwarpdrive II', 1)] + LRIGS, None),
 ('legion owner pyfa fit (184/1050)', 'Legion', LEG + [('Legion Propulsion - Intercalated Nanofibers', 1), ('50MN Microwarpdrive II', 1)] + LRIGS, None),
 ('ishkur (39/137)', 'Ishkur', [('5MN Y-T8 Compact Microwarpdrive', 1)], None),
 ('sacrilege (135/473)', 'Sacrilege', [('50MN Y-T8 Compact Microwarpdrive', 1)], None),
 ('confessor defense (43)', 'Confessor', [], 'defense'),
 ('monitor (30)', 'Monitor', [], None),
]
for label, shipn, items, mode in CASES: print(f'{label:40s}', sig(shipn, items, mode))
