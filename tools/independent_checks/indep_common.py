"""Shared helpers for the independent checks.

RULE (LESSONS_LEARNED.md #3): an expected value is only evidence if it is
derived WITHOUT the tool's own code or tables. These scripts type pyfa's rules
by hand (read from eos/effects.py + eos/modifiedAttributeDict.py) and take
every number from CCP's SDE via pyfa_sde -- never from index.html. Skill
values are read from the skill items too (SK below), never typed as literals:
a hand-typed 0.8 for Shield Operation (really -5%/lvl -> 0.75) is exactly the
kind of slip this avoids.
"""
import sys, os, math, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from pyfa_sde import *

GOLDEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'regression_suite', 'golden_fits.json')

def sk(skill, attr): return A(skill)[attr]
def SK(skill, attr):
    """Multiplier of a %/level skill bonus at level V: 1 + bonus*5/100."""
    return 1 + sk(skill, attr) * 5 / 100

def b(pct): return 1 + pct / 100

def pen(mults):
    """pyfa stacking penalty for ONE penalty group (eos/modifiedAttributeDict.py):
    >1 and <1 chains are penalized separately, largest effect first,
    each step 1 + (m-1)*exp(-(i^2)/7.1289)."""
    v = 1
    for chain in (sorted([m for m in mults if m > 1], key=lambda m: -abs(m - 1)),
                  sorted([m for m in mults if m < 1], key=lambda m: -abs(m - 1))):
        for i, m in enumerate(chain): v *= 1 + (m - 1) * math.exp(-i * i / 7.1289)
    return v
