"""PANIC (Pulse Activated Nexus Invulnerability Core) -- bug list #2, v2026.10.14.9 / .10.

    PYFA_SRC=... python3 -I tools/independent_checks/check_panic.py

History: v.9 let the tool set the PANIC active although pyfa can't; v.10 took that back
(Erik: an Active state that changes no number looks broken). The tool now follows pyfa
(online at most) and only describes the PANIC on the EWAR / Misc card. This script derives,
WITHOUT reading index.html, the facts that rests on:

1. pyfa cannot activate it: no class Effect6719 in eos/effects.py, so Item.isType('active')
   is false and Module.isValidState refuses ACTIVE. Also lists every published module CCP's
   data makes activatable (activation effect with a duration, 16 'online' excluded) that pyfa
   can't activate; expected exactly {42522}. If pyfa gains a handler, the generated
   EFFECT_STATE_TYPE picks it up and this check tells you to revisit the Misc flag wording.
2. The numbers the Misc flag quotes, from pyfa's own handlers at All V
   (tools/pyfa_fit_oracle.py): buffDuration (attr 2535) after the Invulnerability Core
   Operation skill (Effect6807, +10%/level -> 360 s at V; base 240 s), maxRange (attr 54).
3. pyfa's handlers give a Rorqual identical ship attributes with and without a PANIC online.
Ends with 'N problems' (must be 0).
"""
import sys, os, ast
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from pyfa_sde import PYFA_SRC, types, groups, effs, td, _en
from pyfa_fit_oracle import OracleFit

PANIC, PANIC_EFFECT, RORQUAL = 42522, 6719, 28352
bad = 0

# 1. pyfa handler types, read from the class bodies (ast), not executed
tree = ast.parse(open(os.path.join(PYFA_SRC, 'eos', 'effects.py')).read())
handler_types = {}
for node in tree.body:
    if isinstance(node, ast.ClassDef) and node.name.startswith('Effect') and node.name[6:].isdigit():
        t = None
        for st in node.body:
            if isinstance(st, ast.Assign) and any(getattr(x, 'id', None) == 'type' for x in st.targets):
                t = ast.literal_eval(st.value)
        handler_types[int(node.name[6:])] = (t,) if isinstance(t, str) else (t or ())
def pyfa_active(eid): return 'active' in handler_types.get(eid, ())

panic_effects = [e['effectID'] for e in td[str(PANIC)]['dogmaEffects']]
print(f'PANIC effects {panic_effects}; pyfa can activate it: {any(pyfa_active(e) for e in panic_effects)} (expected False -> max state online)')
if any(pyfa_active(e) for e in panic_effects): bad += 1; print('  PROBLEM: pyfa now has an active handler -- revisit the Misc flag and this check')

found = {}
for k, v in types.items():
    if not v.get('published'): continue
    g = groups.get(str(v['groupID']))
    if not g or g['categoryID'] != 7: continue
    es = [e['effectID'] for e in td.get(k, {}).get('dogmaEffects', [])]
    if any(pyfa_active(e) for e in es): continue
    act = [e for e in es if e != 16 and effs.get(str(e), {}).get('effectCategory') == 1 and effs[str(e)].get('durationAttributeID')]
    if act: found[int(k)] = act
print('game-activatable modules pyfa cannot activate:', {k: (_en(types[str(k)].get('typeName')), v) for k, v in found.items()})
if found != {PANIC: [PANIC_EFFECT]}: bad += 1; print('  PROBLEM: expected only {42522: [6719]}')

# 2. numbers for the Misc flag, from pyfa's handlers at All V
f = OracleFit(RORQUAL, [(PANIC, 'online', None)]).calculate()
m = f.modules[0]
base = {x['attributeID']: x['value'] for x in td[str(PANIC)]['dogmaAttributes']}
print(f"buffDuration (2535): base {base.get(2535)} ms -> pyfa at All V {m.get('buffDuration')} ms = {m.get('buffDuration') / 60000:g} min "
      f"(Invulnerability Core Operation, Effect6807); maxRange (54) = {m.get('maxRange') / 1000:g} km")
if (m.get('buffDuration'), m.get('maxRange')) != (360000.0, 200000.0): bad += 1; print('  PROBLEM: expected 360000 ms / 200000 m')

# 3. pyfa: a PANIC online changes no ship attribute
KEYS = ['maxVelocity', 'agility', 'mass', 'shieldCapacity', 'armorHP', 'hp', 'capacitorCapacity', 'rechargeRate',
        'signatureRadius', 'maxTargetRange', 'scanResolution'] + [f'{l}{d}DamageResonance' for l in ('shield', 'armor', '') for d in ('Em', 'Thermal', 'Kinetic', 'Explosive')]
def ship_attrs(mods):
    fx = OracleFit(RORQUAL, mods).calculate()
    return {k: fx.ship.get(k) for k in KEYS}
a, b = ship_attrs([]), ship_attrs([(PANIC, 'online', None)])
diff = {k: (a[k], b[k]) for k in KEYS if a[k] != b[k]}
print(f'PANIC online vs none: {"identical" if not diff else diff}; Rorqual speed {a["maxVelocity"]:.2f} m/s')
if diff: bad += 1
print(f'{bad} problems')
