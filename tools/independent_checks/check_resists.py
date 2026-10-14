"""Resistance phase (hand-tables P2, v2026.10.14.5): expected resists and EHP for constructed
fits, from pyfa's OWN effect handlers run on SDE items (tools/pyfa_fit_oracle.py) -- nothing
from index.html. Cross-checked first against the owner's pyfa screenshots: the Rorqual QuadFeed and
the Legion EFT (all 12 resists), and the user's Dominix Navy Issue (armor 75/71/71/71 with a
Reactive Armor Hardener + Damage Control) -- see the history doc.

pyfa rules these fits isolate (eos/effects.py, eos/modifiedAttributeDict.py):
  * Compensation skills (2053-2056, 2105-2112): +hardeningBonus x level = 5% x 5 = +25% to the
    module's own resistance bonus (Shield Resistance Amplifier, Armor Coating, Energized Armor
    Membrane). The tool used 20%.
  * Damage Control (2302) and Bastion (6658, shield + armor) multiply resonance in the 'preMul'
    penalty group, so they stack-penalize each other; Bastion's hull multiplier is unpenalized.
  * Reactive Armor Hardener (4928, runTime late): simulated against the ship's armor resonance
    after every other effect; its 3-decimal average joins the 'preMul' group (with DC).
  * Polarized weapons (5994/5995) FORCE every resonance to resistanceKiller(Hull), capped by the
    max-resonance attributes (default 1.0): 0% resist on every layer.
  * Special-edition hulls carry their base hull's resist effects (Punisher Kador Edition +20% armor).
  * Flex hardener scripts (6629) boost the hardener's own bonus by the script's BonusBonus.
EHP: pyfa's uniform damage pattern: sum over layers of HP / mean(resonance)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from pyfa_fit_oracle import OracleFit, resonances

def report(label, ship, mods, mode=None):
    f = OracleFit(ship, mods, mode=mode).calculate()
    r = resonances(f)
    hp = {'shield': f.ship.get('shieldCapacity'), 'armor': f.ship.get('armorHP'), 'hull': f.ship.get('hp')}
    ehp = sum(hp[l] / (sum(r[l].values()) / 4) for l in r)
    res = {l: [round((1 - r[l][d]) * 100, 2) for d in ('em', 'therm', 'kin', 'exp')] for l in r}
    print(f'{label}\n    shield {res["shield"]}  armor {res["armor"]}  hull {res["hull"]}  EHP {ehp:,.1f}')
    return res, ehp

MSH, ESA, LSE, DC2 = 'Multispectrum Shield Hardener II', 'EM Shield Amplifier II', 'Large Shield Extender II', 'Damage Control II'
MEM = 'Multispectrum Energized Membrane II'
report('Moa: Multispectrum Shield Hardener II + EM Shield Amplifier II + Large Shield Extender II + Damage Control II',
       'Moa', [(MSH, 'active'), (ESA, 'online'), (LSE, 'online'), (DC2, 'online')])
report('Paladin: Bastion Module I (active) + Damage Control II + 2x Multispectrum Energized Membrane II',
       'Paladin', [('Bastion Module I', 'active'), (DC2, 'online'), (MEM, 'online'), (MEM, 'online')])
report('Megathron: Reactive Armor Hardener + Damage Control II + 2x Multispectrum Energized Membrane II',
       'Megathron', [('Reactive Armor Hardener', 'active'), (DC2, 'online'), (MEM, 'online'), (MEM, 'online')])
report('Rifter: Polarized 200mm AutoCannon (online)', 'Rifter', [('Polarized 200mm AutoCannon', 'online')])
report('Punisher Kador Edition, empty', 'Punisher Kador Edition', [])
report('Phoenix: Capital Flex Shield Hardener II + Shield EM Resistance Script',
       'Phoenix', [('Capital Flex Shield Hardener II', 'active', 'Shield EM Resistance Script')])
report('  same, no script', 'Phoenix', [('Capital Flex Shield Hardener II', 'active')])
report('Confessor, Defense Mode, empty', 'Confessor', [], mode='Confessor Defense Mode')
