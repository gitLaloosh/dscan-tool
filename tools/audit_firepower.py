"""SINCE v2026.10.14.3: hull and subsystem damage/RoF come from the GENERATED table
SHIP_DAMAGE_MOD_EFFECTS (tools/gen_hull_damage_table.py diffs it). This audit now checks that
SHIP_ROLE_BONUS (the fallback) only lists hulls with NO pyfa damage effect, plus modules, skills
and drone control range. The original findings: history 2026-10-14_firepower-audit-findings.

Firepower audit (hand-tables plan, Phase 1): run every pyfa handler that
changes weapon/drone/fighter DAMAGE or RATE OF FIRE, and diff the result
against index.html's hand-built tables. Findings only -- changes nothing.

    node tools/dump_effect_tables.mjs index.html SHIP_ROLE_BONUS,MODULE_DAMAGE_GROUP_CATEGORY,TURRET_SPECIALIZATION_SKILL_IDS,MISSILE_SPECIALIZATION_SKILL_IDS,DRONE_SIZE_CLASS_SKILL_IDS,DRONE_RACIAL_SPECIALIZATION_SKILL_IDS,SHIP_DRONE_CONTROL_RANGE_BONUS,SHIP_DRONE_CONTROL_RANGE_PENALTY_MULT > /tmp/fp.json
    PYFA_SRC=/path/to/Pyfa python3 -I tools/audit_firepower.py /tmp/fp.json [--json out.json]

Targets recorded (pyfa attribute names):
  modules  damageMultiplier, speed            -> turrets (energy/hybrid/projectile/precursor/vorton) and launchers (missile)
  charges  em/thermal/kinetic/explosiveDamage -> missiles (per damage type)
  drones   damageMultiplier                   -> drone / dronesentry
  fighters fighterAbility*DamageMultiplier    -> fighter (Duration rows are reported; the tool has no fighter RoF bonus)
  extraAttributes droneControlRange           -> SHIP_DRONE_CONTROL_RANGE_BONUS / _PENALTY_MULT
Values are at skill level V (x5 when the handler passes skill=). Rate of fire is
reported in the tool's convention: rof +25 means cycle time x0.75.

Every hull row also carries its SCOPE: which weapons the filter really
reaches (e.g. only 'Large Hybrid Turret'). The tool's table applies a bonus to
the whole category, so a narrower pyfa scope is reported as a finding.
"""
import sys, os, re, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pyfa_effects import *

T = json.load(open(sys.argv[1]))
OUT = sys.argv[sys.argv.index('--json') + 1] if '--json' in sys.argv else None
pub = [int(t) for t, v in types.items() if v.get('published')]
TURRET_CAT = {'Energy Weapon': 'energy', 'Hybrid Weapon': 'hybrid', 'Projectile Weapon': 'projectile',
              'Precursor Weapon': 'precursor', 'Vorton Projector': 'vorton'}
turrets = [t for t in pub if cat(t) == 7 and gname(t) in TURRET_CAT]
launchers = [t for t in pub if cat(t) == 7 and gname(t).startswith('Missile Launcher')]
MLO = skillId['Missile Launcher Operation']
missiles = [t for t in pub if cat(t) == 8 and MLO in reqs(t)]
heavyLauncher = [t for t in pub if gname(t) == 'Missile Launcher Heavy'][0]
launcherReps = list({gname(t): t for t in launchers}.values())
SDI = skillId['Sentry Drone Interfacing']
drones = [t for t in pub if cat(t) == 18 and 'damageMultiplier' in {aname(a['attributeID']) for a in td.get(str(t), {}).get('dogmaAttributes', [])}]
sentries = {t for t in drones if SDI in reqs(t)}
fighters = [t for t in pub if cat(t) == 87]
weaponCat = {t: TURRET_CAT[gname(t)] for t in turrets}
weaponCat.update({t: 'missile' for t in launchers})
DMG = {'emDamage': 'em', 'thermalDamage': 'therm', 'kineticDamage': 'kin', 'explosiveDamage': 'exp'}
FTR_DMG = {'fighterAbilityAttackMissileDamageMultiplier', 'fighterAbilityMissilesDamageMultiplier', 'fighterAbilityAttackTurretDamageMultiplier'}
FTR_DUR = {'fighterAbilityAttackMissileDuration', 'fighterAbilityMissilesDuration', 'fighterAbilityAttackTurretDuration'}

def evaluate(coll, meth, a):
    if len(a) < 2: return None
    attr = str(a[1])
    if coll == 'modules' and 'Charge' in meth and attr in DMG:
        # some missile bonuses test the LAUNCHER (group) rather than the charge: try every launcher group
        hits, rec = set(), set()
        for L in launcherReps:
            h, r = filter_hits(a[0], missiles, True, L); hits |= set(h); rec |= set(r)
        return sorted(hits), sorted(rec)
    if coll == 'modules' and 'Charge' not in meth and attr in ('damageMultiplier', 'speed'): return filter_hits(a[0], turrets + launchers)
    if coll == 'drones' and (attr == 'damageMultiplier' or attr in DMG): return filter_hits(a[0], drones)
    if coll == 'fighters' and attr in FTR_DMG | FTR_DUR: return filter_hits(a[0], fighters)
    return None

def attrsOf(t): return {aname(x['attributeID']): x['value'] for x in td.get(str(t), {}).get('dogmaAttributes', [])}
ATTR_DEFAULT = {v['name']: v.get('defaultValue', 0.0) for v in attrs.values()}
def numeric(expr, src):
    # pyfa's getModifiedItemAttr returns the attribute's DEFAULT when the item lacks it
    # (e.g. fighterLightDamageMultiplier defaults to 1) -- not 0.
    e = re.sub(r'a:(\w+)', lambda m: repr(src.get(m.group(1), ATTR_DEFAULT.get(m.group(1), 0.0))), repr(expr)).replace('LVL', '5')
    try: return float(eval(e, {'__builtins__': {}}))
    except Exception: return None

def scopeOf(hits, pool, rec):
    if set(hits) >= set(pool): return 'all'
    sk = sorted({x[1] if isinstance(x[1], str) else '?' for x in rec if x[0] == 'skill'})
    gs = sorted({x[1] for x in rec if x[0] == 'eq'})
    return ' & '.join(filter(None, ['skill ' + '/'.join(sk) if sk else '', 'group ' + '/'.join(gs) if gs else ''])) or f'{len(hits)} items'

def rows_for(eid, carrier, ctx):
    """pyfa rows [cat, kind, pct@V (tool convention), dmgType|None, scope, penalized] for one effect on one carrier."""
    calls, err = run(eid, ctx, evaluate, carrier=carrier if ctx == 'skill' else None)
    if err or not calls: return [], err
    src = attrsOf(carrier); out = []; charge = collections.defaultdict(dict)
    for coll, meth, a, kw in calls:
        if coll == 'extraAttributes' and len(a) >= 2 and str(a[0]) == 'droneControlRange':
            v = numeric(a[1], src)
            if v is not None: out.append(['droneControlRange', meth, v * (5 if kw.get('skill') else 1), None, 'fit', False])
            continue
        if '_eval' not in kw or not kw['_eval']: continue
        hits, rec = kw['_eval']
        if not hits: continue
        attr = str(a[1]); v = numeric(a[2], src)
        if v is None: out.append(['?', attr, repr(a[2]), None, 'unparsed', False]); continue
        lvl = 5 if kw.get('skill') else 1
        if meth.endswith('Boost'): pct = v * lvl
        elif meth.endswith('Multiply'): pct = (v - 1) * 100 if lvl == 1 else None
        else: out.append(['?', attr, f'{meth} {v}', None, 'method', False]); continue
        if pct is None: out.append(['?', attr, f'skill-scaled multiply {v}', None, 'method', False]); continue
        pen = repr(kw.get('stackingPenalties')) == 'True'
        if coll == 'modules' and attr in DMG:
            charge[(scopeOf(hits, missiles, rec), pen)][DMG[attr]] = pct
        elif coll == 'modules':
            for c in sorted({weaponCat[t] for t in hits}):
                pool = [t for t in weaponCat if weaponCat[t] == c]
                sub = [t for t in hits if weaponCat[t] == c]
                kind = 'damage' if attr == 'damageMultiplier' else 'rof'
                out.append([c, kind, round(pct if kind == 'damage' else -pct, 4), None, scopeOf(sub, pool, rec), pen])
        elif coll == 'drones' and attr in DMG:
            # per-damage-type drone bonus (Griffin Navy Issue role malus): collapse below like missiles
            charge[('drone|' + scopeOf(hits, drones, rec), pen)][DMG[attr]] = pct
        elif coll == 'drones':
            c = 'dronesentry' if set(hits) <= sentries else 'drone'
            out.append([c, 'damage', round(pct, 4), None, scopeOf(hits, sorted(sentries) if c == 'dronesentry' else drones, rec), pen])
        elif coll == 'fighters':
            if attr in FTR_DMG: out.append(['fighter', 'damage:' + attr, round(pct, 4), None, scopeOf(hits, fighters, rec), pen])
            else: out.append(['fighter', 'rof:' + attr, round(-pct, 4), None, scopeOf(hits, fighters, rec), pen])
    for (scope, pen), byType in charge.items():
        c = 'missile'
        if scope.startswith('drone|'): c, scope = 'drone', scope[6:]
        vals = set(round(x, 4) for x in byType.values())
        if len(byType) == 4 and len(vals) == 1: out.append([c, 'damage', vals.pop(), None, scope, pen])
        else:
            for d, p in byType.items(): out.append([c, 'damage', round(p, 4), d, scope, pen])
    # fighter damage: one bonus usually touches all three ability multipliers -> collapse
    fd = [r for r in out if r[0] == 'fighter' and r[1].startswith('damage:')]
    if fd and len({(r[2], r[4]) for r in fd}) == 1:
        out = [r for r in out if r not in fd] + [['fighter', 'damage', fd[0][2], None, fd[0][4], fd[0][5]]]
    return out, None

car = carriers()
def effects_of(t): return [e['effectID'] for e in td.get(str(t), {}).get('dogmaEffects', []) if e['effectID'] in EFFECTS]

# ------------------------------------------------------------------ hulls + subsystems
def pyfa_table(carrierTypes, ctx):
    tab, errs = {}, []
    for t in carrierTypes:
        rows = []
        for eid in effects_of(t):
            r, err = rows_for(eid, t, ctx)
            if err: errs.append((t, eid, err))
            rows += [x + [eid] for x in r]
        if rows: tab[str(t)] = rows
    return tab, errs

# all hulls, published or not: special-edition hulls are unpublished but still fly and appear on killmails
ships = [int(t) for t, v in types.items() if groups.get(str(v['groupID']), {}).get('categoryID') == 6]
subsystems = [t for t in pub if cat(t) == 32]
shipTab, shipErr = pyfa_table(ships, 'ship')
subTab, subErr = pyfa_table(subsystems, 'module')

def tool_rows(entry): return [[r[0], r[1], float(r[2]), (r[3] if len(r) > 3 else None)] for r in entry if r[1] in ('damage', 'rof')]
def compare(pyfaTab, toolTab, label):
    findings = []
    for t in sorted(set(pyfaTab) | set(toolTab), key=int):
        p = [r for r in pyfaTab.get(t, []) if r[0] in ('energy', 'hybrid', 'projectile', 'precursor', 'vorton', 'missile', 'drone', 'dronesentry', 'fighter') and r[1] in ('damage', 'rof')]
        # pyfa often splits one missile bonus into four effects (one per damage type);
        # four same-value, same-scope rows covering em/therm/kin/exp = one unrestricted bonus.
        while True:
            groups4 = collections.defaultdict(list)
            for r in p:
                if r[0] == 'missile' and r[1] == 'damage' and r[3]: groups4[(round(r[2], 4), r[4])].append(r)
            quad = next((g for g in groups4.values() if {r[3] for r in g} >= {'em', 'therm', 'kin', 'exp'}), None)
            if not quad: break
            take = [next(r for r in quad if r[3] == d) for d in ('em', 'therm', 'kin', 'exp')]
            p = [r for r in p if not any(r is x for x in take)] + [['missile', 'damage', take[0][2], None, take[0][4], take[0][5], [x[6] for x in take]]]
        tl = tool_rows(toolTab.get(t, []))
        p = [r for r in p if abs(r[2]) > 1e-9]
        # one bonus is often split into one effect per launcher/turret family (Raven: cruise,
        # torpedo, rapid heavy). Same value on DIFFERENT scopes = one bonus; same scope twice = two.
        merged = collections.Counter()
        byKey = collections.defaultdict(collections.Counter)
        for r in p: byKey[(r[0], r[1], round(r[2], 2), r[3])][r[4]] += 1
        for k, sc in byKey.items(): merged[k] = max(sc.values())
        pk = merged
        tk = collections.Counter((r[0], r[1], round(r[2], 2), r[3]) for r in tl)
        missing = list((pk - tk).elements()); extra = list((tk - pk).elements())
        scopes = sorted({(r[0], r[1], r[4]) for r in p if r[4] != 'all'})
        if missing or extra or scopes:
            findings.append({'type': int(t), 'name': name(t), 'group': gname(t), 'missing': missing, 'extra': extra,
                             'narrowScope': scopes, 'pyfa': [r[:5] + [r[6]] for r in p], 'tool': toolTab.get(t, [])})
    return findings

# Fallback check: a SHIP_ROLE_BONUS hull must have no pyfa damage/RoF row at all.
shipF = [f for f in compare(shipTab, T['SHIP_ROLE_BONUS'], 'hull') if str(f['type']) in T['SHIP_ROLE_BONUS']]
subF = []

# ------------------------------------------------------------------ fitted modules / rigs
modTab = {}
for t in [t for t in pub if cat(t) == 7]:
    for eid in effects_of(t):
        r, _ = rows_for(eid, t, 'module')
        for x in r:
            if x[0] in ('?',) or x[0] == 'droneControlRange': continue
            modTab.setdefault(gname(t), set()).add((x[0], x[1].split(':')[0], x[3], x[4], x[5]))
modF = []
for g, rows in sorted(modTab.items()):
    cats = sorted({r[0] for r in rows})
    toolCat = T['MODULE_DAMAGE_GROUP_CATEGORY'].get(g)
    modF.append({'group': g, 'pyfaCats': cats, 'toolCat': toolCat, 'rows': sorted(map(list, rows), key=str)})

# ------------------------------------------------------------------ skills
skillRows = {}
for t in [t for t in pub if cat(t) == 16]:
    for eid in effects_of(t):
        r, _ = rows_for(eid, t, 'skill')
        for x in r:
            if x[0] != '?': skillRows.setdefault(name(t), []).append(x + [eid])

# ------------------------------------------------------------------ drone control range (hulls)
dcr = {}
for t, rows in shipTab.items():
    for r in rows:
        if r[0] == 'droneControlRange': dcr.setdefault(t, []).append(r)

# ------------------------------------------------------------------ report
def show(f):
    print(f"  {f['name']} ({f['group']}, {f['type']})")
    for m in f['missing']: print('     MISSING in tool:', m)
    for e in f['extra']: print('     EXTRA in tool:  ', e)
    for s in f['narrowScope']: print('     scope narrower in pyfa:', s)
real = [f for f in shipF if f['missing']]   # pyfa has rows for a fallback hull -> remove it from SHIP_ROLE_BONUS
print(f'SHIP_ROLE_BONUS fallback: {len(T["SHIP_ROLE_BONUS"])} hulls; with pyfa damage rows (should be 0): {len(real)}')
for f in real: show(f)
print('\nMODULE GROUPS with damage/RoF effects (pyfa categories vs MODULE_DAMAGE_GROUP_CATEGORY):')
for m in modF: print(f"  {m['group']}: pyfa {m['pyfaCats']} | tool {m['toolCat']}")
print('\nSKILLS with damage/RoF effects:')
for s, rows in sorted(skillRows.items()):
    print(f'  {s}: ' + '; '.join(f'{r[0]} {r[1]} {r[2]:g}{" " + r[3] if r[3] else ""} [{r[4]}]{" PEN" if r[5] else ""}' for r in rows))
print('\nDRONE CONTROL RANGE (hulls):')
for t, rows in dcr.items(): print(f'  {name(t)} {t}:', [(r[1], r[2]) for r in rows], '| tool bonus', T['SHIP_DRONE_CONTROL_RANGE_BONUS'].get(t), 'penalty', T['SHIP_DRONE_CONTROL_RANGE_PENALTY_MULT'].get(t))
if OUT:
    json.dump({'hulls': shipF, 'subsystems': subF, 'modules': modF, 'skills': skillRows, 'droneControlRange': dcr,
               'errors': {'hull': shipErr[:50], 'sub': subErr[:50]}}, open(OUT, 'w'), indent=1, default=list)
    print('\nwrote', OUT)
