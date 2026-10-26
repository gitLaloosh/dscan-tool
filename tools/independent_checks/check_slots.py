"""The hull's slots per rack (v2026.10.14.75, roadmap/charges-plan.md delivery 1): estimate.slots, the Fit card ring's
positions (its empty slots are the ones nothing is fitted in).

    PYFA_SRC=... python3 -I tools/independent_checks/check_slots.py [index.html]   -> 'N mismatches' (must be 0)

pyfa's count is Fit.getNumSlots(slot) = the ship's modified attribute named by Fit.slots (hiSlots, medSlots, lowSlots,
rigSlots, maxSubSystems). Here every golden fit is run through pyfa's own handlers (tools/pyfa_fit_oracle.py, a T3's
subsystems included) and those five attributes are read off the oracle's ship. Part 1 also asserts, with the handler
recorder, that pyfa's only handler changing them is slotModifier (effect 3774, subsystems): if a pyfa update adds
another, the tool's formula needs it and this check fails first.
Also: the ring draws one position per slot (fitted + empty) on every rack whose hull count is at least what is fitted.
"""
import sys, os, json, re, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from golden_oracle import oracle_for, GOLDEN
from pyfa_sde import PYFA_SRC
html = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
bad = 0
def fail(m):
    global bad
    bad += 1; print('MISMATCH', m)
ATTRS = {'high': 'hiSlots', 'mid': 'medSlots', 'low': 'lowSlots', 'rig': 'rigSlots', 'subsystem': 'maxSubSystems'}

# Part 1: pyfa's handlers on the slot attributes (source scan of eos/effects.py: every call naming one of them)
src = open(os.path.join(PYFA_SRC, 'eos', 'effects.py'), encoding='utf-8').read()
writers = set()
for m in re.finditer(r"class (Effect\d+)\(BaseEffect\):\n\s+\"\"\"\n\s+(\w+)(.*?)(?=\nclass Effect|\Z)", src, re.S):
    cls, name, body = m.group(1), m.group(2), m.group(3)
    for a in ATTRS.values():
        if re.search(r"\.(increase|boost|multiply|force|preAssign|decrease)\w*\(\s*['\"]%s['\"]" % a, body): writers.add((cls, name, a))
want = {('Effect3774', 'slotModifier', a) for a in ('hiSlots', 'medSlots', 'lowSlots')}
if writers != want: fail(f'pyfa handlers on the slot attributes changed: {sorted(writers)} (expected slotModifier on hiSlots/medSlots/lowSlots)')
else: print('pyfa handlers on slots: slotModifier (3774) on hiSlots / medSlots / lowSlots only')

# Part 2: every golden fit
G = json.load(open(GOLDEN))
tmp = tempfile.mkdtemp(); dump = os.path.join(tmp, 'd.json')
subprocess.run(['node', os.path.join(ROOT, 'regression_suite', 'dump_results.mjs'), html, dump, 'slots,moduleStates'], check=True, stdout=subprocess.DEVNULL)
D = json.load(open(dump))
n = t3 = 0
for k in G:
    t = D.get(k) or {}
    if not t.get('slots'): fail(f'{k}: no slots'); continue
    o = oracle_for(k)
    want = {r: int(round(o.ship.get(a) or 0)) for r, a in ATTRS.items()}
    got = {r: int(round(v)) for r, v in t['slots'].items()}
    if got != want: fail(f'{k}: tool {got} pyfa {want}')
    fitted = {}
    for it in (t.get('moduleStates') or {}).get('items') or []: fitted[it['slot']] = fitted.get(it['slot'], 0) + round(it['qty'])
    over = {r: (fitted.get(r, 0), got.get(r, 0)) for r in ATTRS if fitted.get(r, 0) > got.get(r, 0)}
    if over: print(f'note {k}: more fitted than the hull has (the ring draws the fitted ones, no empty): {over}')
    n += 1; t3 += want['subsystem'] > 0
print(f'{bad} mismatches ({n} fits, {t3} with subsystems; slots per rack vs pyfa Fit.getNumSlots)')
sys.exit(1 if bad else 0)
