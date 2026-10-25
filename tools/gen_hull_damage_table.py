"""Generate SHIP_DAMAGE_MOD_EFFECTS (index.html, PYFA CORE section 'hull-damage-table')
from pyfa + SDE: every HULL and SUBSYSTEM effect that changes weapon, missile,
drone or fighter DAMAGE or RATE OF FIRE, with its exact filter.

    PYFA_SRC=/path/to/Pyfa python3 -I tools/gen_hull_damage_table.py [index.html]          # diff
    PYFA_SRC=/path/to/Pyfa python3 -I tools/gen_hull_damage_table.py [index.html] --write  # embed

Row = [target, kind, srcAttrId, perLevel, op, default, skills, skillsOn, groups, groupsOn, dmgType, penalized]
  target   'weapon' (turret/launcher item: damageMultiplier, speed), 'charge' (the loaded
           charge's em/thermal/kinetic/explosiveDamage), 'drone', 'fighter' (the
           Attack Missile ability, pyfa 'Turret Attack'), 'fighterMissiles' (the
           Missiles ability, pyfa 'Missile Attack'; v2026.10.14.4)
  kind     'damage' | 'rof' (rof rows multiply the CYCLE TIME, pyfa 'speed') | 'spool' (v2026.10.14.67: the weapon's
           damageMultiplierBonusMax, an Entropic Disintegrator's maximum spool-up -- Nergal, Ikitursa, Babaroga)
  srcAttr  attribute on the CARRIER (hull or subsystem); perLevel 5 when pyfa passes skill=
  op       'boost' (x(1 + v*perLevel/100)) | 'multiply' (x v)
  default  the attribute's SDE defaultValue (pyfa reads it when the carrier lacks it, LESSON #22)
  skills / skillsOn   requiredSkill ids (ANY), checked on 'item' (the weapon/drone/fighter) or 'charge'
  groups / groupsOn   group names (ANY), checked on 'item' or 'charge'
  dmgType  'em'|'therm'|'kin'|'exp' for per-damage-type rows, else null
  penalized 1 = stacking-penalized in pyfa (default group, pooled with the weapon's module bonuses)
A filter must be exactly reproducible as (skills) AND (groups) on the pool -- asserted.
Same method as gen_weapon_range_table.py (LESSONS #1, #16, #22).

Also writes FIGHTER_ABILITY_EFFECTS (v2026.10.14.4): every pyfa-implemented effect carried by a
fighter -> [effectName, target or null, [em, therm, kin, exp, damageMultiplier, duration attr ids] or
null]. The engine replays pyfa's default ability activation (eos/saveddata/fighter.py
Fighter.__init__) over it and sums every active damaging ability. Asserted here: every ability pyfa
turns on by default that deals damage has a modeled target.
"""
import sys, os, re, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pyfa_effects import *

pub = [int(t) for t, v in types.items() if v.get('published')]
attrId = {v['name']: int(k) for k, v in attrs.items()}
DEFAULT = {v['name']: v.get('defaultValue', 0.0) for v in attrs.values()}
TURRET_GROUPS = {'Energy Weapon', 'Hybrid Weapon', 'Projectile Weapon', 'Precursor Weapon', 'Vorton Projector'}
def adict(t): return {aname(x['attributeID']): x['value'] for x in td.get(str(t), {}).get('dogmaAttributes', [])}
DMG = {'emDamage': 'em', 'thermalDamage': 'therm', 'kineticDamage': 'kin', 'explosiveDamage': 'exp'}
weapons = [t for t in pub if cat(t) == 7 and (gname(t) in TURRET_GROUPS or gname(t).startswith('Missile Launcher'))]
charges = [t for t in pub if cat(t) == 8 and any(adict(t).get(a, 0) > 0 for a in DMG)]
drones = [t for t in pub if cat(t) == 18 and 'damageMultiplier' in adict(t)]
fighters = [t for t in pub if cat(t) == 87]
# Fighter abilities the engine models, by pyfa ability prefix (the class attribute 'prefix' of the effect).
FTR_ABILITY_TARGET = {'fighterAbilityAttackMissile': 'fighter', 'fighterAbilityMissiles': 'fighterMissiles'}
FTR_ATTR = {}
for _p, _t in FTR_ABILITY_TARGET.items(): FTR_ATTR[_p + 'DamageMultiplier'] = (_t, 'damage'); FTR_ATTR[_p + 'Duration'] = (_t, 'rof')
# Hull/skill handlers also boost fighterAbilityAttackTurret*, but no pyfa effect has that prefix, so no
# ability ever reads it (asserted below) -- those calls change nothing in pyfa's numbers.
FTR_UNREAD = {'fighterAbilityAttackTurretDamageMultiplier', 'fighterAbilityAttackTurretDuration'}
assert not any(getattr(c, 'prefix', None) == 'fighterAbilityAttackTurret' for c in EFFECTS.values()), 'an AttackTurret ability now exists: model it'

def sig(t): return (frozenset(reqs(t)), gname(t))          # what a filter can see: skills + group
def reps(pool):
    out = {}
    for t in pool: out.setdefault(sig(t), t)
    return list(out.values())
weaponReps, chargeReps, droneReps, fighterReps = reps(weapons), reps(charges), reps(drones), reps(fighters)
pairs = [(c, w) for c in chargeReps for w in weaponReps]

def eval_pairs(lam):
    REC.clear(); hits = []
    for c, w in pairs:
        p = Probe(w, c)
        try:
            if lam(p): hits.append((c, w))
        except Exception: pass
    return hits, sorted(set(REC))

def evaluate(coll, meth, a):
    if len(a) < 2 or not callable(a[0]): return None
    attr = str(a[1])
    if coll == 'modules' and 'Charge' in meth and attr in DMG: return ('charge', eval_pairs(a[0]))
    if coll == 'modules' and 'Charge' not in meth and attr in ('damageMultiplier', 'speed', 'damageMultiplierBonusMax'): return ('weapon', filter_hits(a[0], weaponReps))
    if coll == 'drones' and (attr == 'damageMultiplier' or attr in DMG): return ('drone', filter_hits(a[0], droneReps))
    if coll == 'fighters' and attr in set(FTR_ATTR) | FTR_UNREAD: return ('fighter', filter_hits(a[0], fighterReps))
    return None

def matches(t, skills, groups):
    return (not skills or any(s in reqs(t) for s in skills)) and (not groups or gname(t) in groups)

def fit_filter(target, hits, rec):
    sk = sorted({skillId[x[1]] for x in rec if x[0] == 'skill' and x[1] in skillId})
    gs = sorted({x[1] for x in rec if x[0] == 'eq'})
    if any(x[0] == 'skill?' for x in rec): raise AssertionError('filter tests the carrying skill')
    if target != 'charge':
        pool = {'weapon': weaponReps, 'drone': droneReps, 'fighter': fighterReps, 'fighterMissiles': fighterReps}[target]
        calc = [t for t in pool if matches(t, sk, gs)]
        if set(calc) != set(hits): raise AssertionError(f'filter not expressible as skills AND groups ({sk}, {gs})')
        return sk or None, 'item', gs or None, 'item'
    for sOn in ('charge', 'item'):
        for gOn in ('item', 'charge'):
            calc = [(c, w) for c, w in pairs
                    if (not sk or any(s in reqs(c if sOn == 'charge' else w) for s in sk))
                    and (not gs or gname(c if gOn == 'charge' else w) in gs)]
            if set(calc) == set(hits): return sk or None, sOn, gs or None, gOn
    raise AssertionError(f'charge filter not expressible ({sk}, {gs})')

table, errors, skipped = {}, [], collections.Counter()
carrierTypes = [int(t) for t, v in types.items() if groups.get(str(v['groupID']), {}).get('categoryID') in (6, 32)]
effectCarriers = collections.defaultdict(set)
for t in carrierTypes:
    for e in td.get(str(t), {}).get('dogmaEffects', []): effectCarriers[e['effectID']].add(t)
for eid in sorted(effectCarriers):
    if eid not in EFFECTS: continue
    ctxs = {('ship' if cat(t) == 6 else 'module') for t in effectCarriers[eid]}
    for ctx in sorted(ctxs):
        calls, err = run(eid, ctx, evaluate)
        if err: errors.append((eid, err)); continue
        for coll, meth, a, kw in calls:
            ev = kw.get('_eval')
            if not ev: continue
            target, (hits, rec) = ev
            if not hits: continue
            attr = str(a[1])
            if target == 'fighter' and attr in FTR_UNREAD: skipped[f'attribute no pyfa fighter ability reads: {attr}'] += 1; continue
            if target == 'fighter': target = FTR_ATTR[attr][0]
            if 'pyfa_effects.Any' in repr(a[2]):   # depends on the pilot (e.g. AT ships' security-status scaling)
                skipped[f'pilot-dependent value, not modeled: {ename(eid)} ({eid}) {attr}'] += 1; continue
            m = re.fullmatch(r"\(?a:(\w+)(\*1)?\)?", repr(a[2]))
            if not m: raise AssertionError(f'effect {eid}: unexpected value expression {a[2]!r}')
            # A few hull bonuses are stacking-penalized in pyfa (Claw 4464 RoF): flag them; the
            # engine pools them with that weapon's module bonuses in pyfa's default penalty group.
            pen = 1 if repr(kw.get('stackingPenalties')) == 'True' else 0
            if pen and kw.get('penaltyGroup') not in (None, 'default'): raise AssertionError(f'effect {eid}: penalty group {kw.get("penaltyGroup")}')
            op = 'boost' if meth.endswith('Boost') else 'multiply' if meth.endswith('Multiply') else None
            if not op: raise AssertionError(f'effect {eid}: method {meth}')
            perLevel = 5 if kw.get('skill') else 1
            if op == 'multiply' and perLevel != 1: raise AssertionError(f'effect {eid}: skill-scaled multiply')
            try: sk, sOn, gs, gOn = fit_filter(target, hits, rec)
            except AssertionError as ex: raise AssertionError(f'effect {eid} {ename(eid)} {attr}: {ex}')
            kind = 'rof' if attr == 'speed' or FTR_ATTR.get(attr, (0, ''))[1] == 'rof' else 'spool' if attr == 'damageMultiplierBonusMax' else 'damage'
            if kind == 'spool' and (op != 'boost' or pen): raise AssertionError(f'effect {eid}: spool row {op} pen={pen} -- model it')
            dmgType = DMG.get(attr) if target in ('charge', 'drone') else None
            row = [target, kind, attrId[m.group(1)], perLevel, op, DEFAULT.get(m.group(1), 0.0), sk, sOn, gs, gOn, dmgType, pen]
            if pen and not (target == 'weapon' and kind == 'rof'):   # the engine pools only weapon RoF rows (Claw)
                raise AssertionError(f'effect {eid}: penalized {target} {kind} row -- extend weaponRofMult/hullWeaponMods first')
            rows = table.setdefault(str(eid), [])
            if row not in rows: rows.append(row)

# ---- FIGHTER_ABILITY_EFFECTS + pyfa default activation check ----
def default_active(effect_ids):
    """pyfa Fighter.__init__: 'fighterAbilityAttackM' on; every implemented ability before it on,
    except MicroWarpDrive / EvasiveManeuvers; nothing after it. Order = item effect order, which for
    every fighter in the SDE is ascending effect ID (asserted below)."""
    out, std = [], False
    for e in effect_ids:
        if e not in EFFECTS: continue                     # not implemented in pyfa -> never activated
        n = ename(e)
        if n == 'fighterAbilityAttackM': out.append(e); std = True
        elif not std and n not in ('fighterAbilityMicroWarpDrive', 'fighterAbilityEvasiveManeuvers'): out.append(e)
    return out
fighterAbilities, abilitySets = {}, collections.Counter()
for t in fighters:
    effs = [e['effectID'] for e in td.get(str(t), {}).get('dogmaEffects', [])]
    if effs != sorted(effs): raise AssertionError(f'fighter {t}: effects not in ID order -- engine sorts by ID')
    A_ = adict(t)
    for e in effs:
        if e not in EFFECTS: continue
        prefix = getattr(EFFECTS[e], 'prefix', None)
        tg = FTR_ABILITY_TARGET.get(prefix)
        ids = [attrId[f'{prefix}Damage{x}'] for x in ('EM', 'Therm', 'Kin', 'Exp')] + [attrId[f'{prefix}DamageMultiplier'], attrId[f'{prefix}Duration']] if tg else None
        fighterAbilities[str(e)] = [ename(e), tg, ids]
    on = default_active(effs)
    for e in on:   # pyfa FighterAbility.dealsDamage: <prefix>DamageMultiplier on the item, or a charge (bombs)
        prefix = getattr(EFFECTS[e], 'prefix', None)
        deals = prefix and (f'{prefix}DamageMultiplier' in A_ or prefix == 'fighterAbilityLaunchBomb')
        if deals and prefix not in FTR_ABILITY_TARGET: raise AssertionError(f'fighter {t}: default-active damaging ability {ename(e)} not modeled')
    abilitySets[(gname(t), tuple(ename(e) for e in on))] += 1
fighterAbilities = dict(sorted(fighterAbilities.items(), key=lambda kv: int(kv[0])))
print('fighter default abilities (pyfa):')
for (g, k), v in sorted(abilitySets.items()): print(f'  {v:3d} {g}: {", ".join(k)}')

print(f'{len(table)} effects, {sum(map(len, table.values()))} rows; unrelated handler errors {len(errors)}')
for k, v in skipped.items(): print('  skipped:', k)
html = next((x for x in sys.argv[1:] if not x.startswith('--')), os.path.join(os.path.dirname(__file__), '..', 'index.html'))
src = open(html).read()
uptodate = True
for tname, data in (('SHIP_DAMAGE_MOD_EFFECTS', table), ('FIGHTER_ABILITY_EFFECTS', fighterAbilities)):
    pat = re.compile(r'(const ' + tname + r' = )(\{.*?\});', re.S)
    m = pat.search(src)
    blob = json.dumps(data, separators=(',', ':'))
    if '--write' in sys.argv:
        if not m: sys.exit(tname + ' not found in ' + html)
        src = src[:m.start(2)] + blob + src[m.end(2):]
        print('wrote', tname)
    elif m:
        emb = json.loads(m.group(2))
        added = sorted(set(data) - set(emb), key=int); removed = sorted(set(emb) - set(data), key=int)
        changed = sorted([k for k in set(data) & set(emb) if data[k] != emb[k]], key=int)
        print(f'{tname} vs index.html -- new:', added, 'gone:', removed, 'changed:', changed)
        uptodate &= not (added or removed or changed)
    else:
        print(tname, 'not in index.html yet'); uptodate = False
if '--write' in sys.argv: open(html, 'w').write(src); print('into', html)
elif uptodate: print('index.html table is up to date with this pyfa/SDE.')
