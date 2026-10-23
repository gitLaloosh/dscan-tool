"""Regenerate WEAPON_RANGE_MOD_EFFECTS (index.html) from pyfa + SDE, and diff
it against the copy embedded in index.html. Since v2026.10.14.34 it also covers the application attributes
(turret tracking, missile and Vorton explosion radius / velocity) for the damage-application core.

    PYFA_SRC=/path/to/Pyfa python3 -I tools/gen_weapon_range_table.py [index.html] [--write]

This is the worked example for LESSONS_LEARNED.md #1 (execute handlers, don't
regex them) and #2 (gate on effects, not group names). Use it as the template
for any other "every handler that changes attribute X" table.
"""
import sys, json, re, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pyfa_effects import *

WEAP = {'Energy Weapon', 'Hybrid Weapon', 'Projectile Weapon', 'Precursor Weapon', 'Vorton Projector'}
pub = [int(t) for t, v in types.items() if v.get('published')]
turrets = [t for t in pub if cat(t) == 7 and gname(t) in WEAP]
MLO = skillId['Missile Launcher Operation']
missiles = [t for t in pub if cat(t) == 8 and MLO in reqs(t)]
launcher = [t for t in pub if gname(t) == 'Missile Launcher Heavy'][0]
attrId = {v['name']: int(k) for k, v in attrs.items()}
TARGET = {'maxRange': 'optimal', 'falloff': 'falloff', 'charge.maxVelocity': 'missileVelocity', 'charge.explosionDelay': 'missileFlightTime',
          # v2026.10.14.34 (turret-application-plan.md Phase 1): what pyfa's damage graph reads per weapon --
          # turret tracking, the missile's explosion radius / velocity, and a Vorton Projector's own explosion
          # radius / velocity (on the module, not a charge). Same recorder, rows and checks as range.
          'trackingSpeed': 'tracking', 'charge.aoeCloudSize': 'missileExplosionRadius', 'charge.aoeVelocity': 'missileExplosionVelocity',
          'aoeCloudSize': 'vortonExplosionRadius', 'aoeVelocity': 'vortonExplosionVelocity'}
CTX = {6: 'ship', 7: 'module', 32: 'module'}   # skills keep their own MAX_* constants in index.html

table, errors = {}, []
for eid, ts in sorted(carriers().items()):
    if eid not in EFFECTS: continue
    for c in sorted({cat(t) for t in ts} & set(CTX)):
        def evaluate(coll, meth, a):
            # Evaluate the filter NOW, while loop variables in the handler still
            # hold this iteration's values (LESSONS_LEARNED.md #16).
            if coll != 'modules' or len(a) < 3: return None
            isCharge = 'Charge' in meth
            if (('charge.' if isCharge else '') + str(a[1])) not in TARGET: return None
            return filter_hits(a[0], missiles if isCharge else turrets, isCharge, launcher)
        calls, err = run(eid, CTX[c], evaluate)
        if err: errors.append((eid, err)); continue
        for coll, meth, a, kw in calls:
            if coll != 'modules' or len(a) < 3 or not callable(a[0]): continue
            isCharge = 'Charge' in meth
            key = ('charge.' if isCharge else '') + str(a[1])
            if key not in TARGET or not meth.endswith('Boost'): continue
            hits, rec = kw['_eval']
            if not hits: continue
            # The filter must be reproducible as (any of skills) AND (any of groups):
            sk = sorted({skillId[x[1]] for x in rec if x[0] == 'skill'})
            gs = sorted({x[1] for x in rec if x[0] == 'eq'})
            pool = missiles if isCharge else turrets
            calc = [t for t in pool if (not sk or any(s in reqs(t) for s in sk)) and (not gs or gname(t) in gs)]
            assert set(calc) == set(hits), f'effect {eid}: filter not expressible as skills/groups -- handle by hand'
            m = re.fullmatch(r"\(?a:(\w+)(\*1)?\)?", repr(a[2]))
            assert m, f'effect {eid}: unexpected value expression {a[2]!r}'
            pen = repr(kw.get('stackingPenalties')) == 'True'
            row = [TARGET[key], sk or None, gs or None, attrId[m.group(1)], 5 if kw.get('skill') else 1, 1 if pen else 0]
            table.setdefault(str(eid), [])
            if row not in table[str(eid)]: table[str(eid)].append(row)

print(f'{len(table)} effects, {sum(map(len, table.values()))} rows; handler errors (unrelated effects): {len(errors)}')
html = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(os.path.dirname(__file__), '..', 'index.html'))
m = re.search(r'const WEAPON_RANGE_MOD_EFFECTS = (\{.*?\});', open(html).read(), re.S)
if m:
    embedded = json.loads(m.group(1))
    added = sorted(set(table) - set(embedded), key=int); removed = sorted(set(embedded) - set(table), key=int)
    changed = sorted([k for k in set(table) & set(embedded) if table[k] != embedded[k]], key=int)
    print('vs index.html -- new:', added, 'gone:', removed, 'changed:', changed)
    if not (added or removed or changed): print('index.html table is up to date with this pyfa/SDE.')
if '--write' in sys.argv:   # v2026.10.14.34: rewrite the embedded table (then re-lock: check_pyfa_core.mjs --update)
    src = open(html, encoding='utf-8').read()
    body = ',\n'.join(f'  "{k}":' + json.dumps(table[k], separators=(',', ':')) for k in sorted(table, key=int))
    new = 'const WEAPON_RANGE_MOD_EFFECTS = {\n' + body + '};'
    src, n = re.subn(r'const WEAPON_RANGE_MOD_EFFECTS = \{.*?\};', lambda _: new, src, count=1, flags=re.S)
    assert n == 1
    open(html, 'w', encoding='utf-8').write(src); print('wrote', html)
