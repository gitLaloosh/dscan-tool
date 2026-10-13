"""Audit index.html's effect tables against pyfa by RUNNING every handler.

    node tools/dump_effect_tables.mjs index.html > /tmp/tables.json
    PYFA_SRC=/path/to/Pyfa python3 -I tools/audit_effect_tables.py /tmp/tables.json

For each stat the tool models, it lists the pyfa effects that change it
(found by executing handlers -- LESSONS_LEARNED.md #1), then reports:
  MISSING  -- pyfa changes the stat, the table has no row for the effect
  EXTRA    -- the table has the effect but the handler doesn't touch that stat
  MISMATCH -- both have it, but source attribute / penalty / skill scaling differ
Carriers: ships (6), modules and rigs (7), subsystems (32), skills (16).
Implants, boosters, structures, beacons and projected effects are out of scope.
"""
import sys, os, json, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pyfa_effects import *

T = json.load(open(sys.argv[1]))
attrId = {v['name']: int(k) for k, v in attrs.items()}
pub = [int(t) for t, v in types.items() if v.get('published')]
CTX = {6: 'ship', 7: 'module', 32: 'module', 16: 'skill'}
def has_attr(t, a): return any(x['attributeID'] == attrId[a] for x in td.get(str(t), {}).get('dogmaAttributes', []))
modules = [t for t in pub if cat(t) == 7]
POOL = {a: [t for t in modules if has_attr(t, a)] for a in ('capacitorNeed', 'duration', 'shieldBonus', 'armorDamageAmount', 'structureDamageAmount')}

SHIP_TARGETS = {'capacitorCapacity', 'rechargeRate', 'shieldCapacity', 'armorHP', 'hp', 'maxTargetRange', 'scanResolution',
                'scanRadarStrength', 'scanLadarStrength', 'scanMagnetometricStrength', 'scanGravimetricStrength', 'shieldRechargeRate', 'signatureRadius'}
MOD_TARGETS = set(POOL)

def value_info(v):
    m = re.fullmatch(r"\(?a:(\w+)(\*(1|LVL))?\)?", repr(v))
    if m: return attrId.get(m.group(1)), m.group(3)
    m = re.fullmatch(r"\(1/a:(\w+)\)", repr(v))
    if m: return attrId.get(m.group(1)), 'inverse'
    return None, repr(v)

# Effects deliberately NOT in the tables, with the reason. Keep this list honest:
# every entry needs a reason a reader can check. Anything not listed is a finding.
KNOWN = {
    25:    'Capacitor Battery flat capacity add -- handled by the flat-add code path (attr67), not a table row',
    3811:  'T3 subsystem flat capacity add -- handled by the flat-add code path (subsystem attr482), not a table row',
    12924: 'T3D proximityDbuffEffectTacticalDestroyerHP -- value is 0 on every hull in this SDE; nothing to model yet',
    6063:  'Entosis Link -- "while active" sovereignty module; module-toggle item',
    6567:  'Networked Sensor Array -- "while active" Capital Sensor Array; module-toggle item',
    12597: 'Integrated Sensor Array -- "while active" Capital Sensor Array; module-toggle item',
    4921:  'MJD signature spike -- short burst during activation; shown as a Misc flag, module-toggle item',
    6208:  'MJFG signature spike -- as MJD',
    12126: 'Capital MJFG signature spike -- as MJD',
    8109:  'Signature Suppressor ACTIVE burst (x0.3) -- module-toggle item; the passive x0.9 (8108) is modeled',
    6581:  "Triage ewCapacitorNeedBonus (+900,000,000%) -- the game's way of blocking EWAR in triage, not a real drain",
    6642:  'Doomsday Rapid Firing -- in SKILL_MODULE_ATTR_MODS_AT_V (skill rows are matched separately)',
}
found = collections.defaultdict(list)   # (target) -> rows
for eid, ts in sorted(carriers().items()):
    if eid not in EFFECTS: continue
    for c in sorted({cat(t) for t in ts} & set(CTX)):
        def evaluate(coll, meth, a):
            # filters are evaluated at call time (LESSONS_LEARNED.md #16)
            if coll == 'modules' and len(a) >= 3 and a[1] in MOD_TARGETS and 'Charge' not in meth:
                return filter_hits(a[0], POOL[a[1]])
            return None
        calls, err = run(eid, CTX[c], evaluate)
        if err: continue
        for coll, meth, a, kw in calls:
            pen = repr(kw.get('stackingPenalties')) == 'True'
            row = dict(eid=eid, cat=c, meth=meth, pen=pen, group=kw.get('penaltyGroup'), skill=kw.get('skill'),
                       ex=[name(t) for t in ts if cat(t) == c][:3], n=len([t for t in ts if cat(t) == c]))
            if coll == 'ship' and len(a) >= 2 and a[0] in SHIP_TARGETS:
                row['src'], row['scale'] = value_info(a[1]); found['ship.' + a[0]].append(row)
            elif coll == 'modules' and len(a) >= 3 and callable(a[0]) and a[1] in MOD_TARGETS and 'Charge' not in meth:
                hits, rec = kw['_eval']
                if any(x[0] == 'skill?' for x in rec):
                    # LESSON #19: filter is requiresSkill(<the carrying skill>); not evaluable per effect.
                    print(f'UNEVALUATED self-skill filter: effect {eid} on module.{a[1]} -- check by hand (run(..., carrier=skillTypeId))')
                if not hits: continue
                row['src'], row['scale'] = value_info(a[2]); row['filter'] = rec; row['hits'] = len(hits)
                row['hitGroups'] = sorted({gname(t) for t in hits})[:6]
                found['module.' + a[1]].append(row)

# --- what index.html has, per target -------------------------------------
have = collections.defaultdict(dict)   # target -> {eid: [table rows]}
for eid, rows in T['MODULE_ATTR_MOD_EFFECTS'].items():
    for r in rows: have['module.' + r[0]].setdefault(int(eid), []).append(('MODULE_ATTR_MOD_EFFECTS', r))
for tbl in ('SIEGE_FAMILY_LOCAL_REP_EFFECTS', 'SIEGE_FAMILY_REMOTE_REP_EFFECTS'):
    for eid, rows in T.get(tbl, {}).items():
        for r in rows: have['module.' + r[0]].setdefault(int(eid), []).append((tbl, r))
for eid, rows in T['SHIP_CAP_ATTR_EFFECTS'].items():
    for r in rows: have['ship.' + r[0]].setdefault(int(eid), []).append(('SHIP_CAP_ATTR_EFFECTS', r))
HPMAP = {'shield': 'shieldCapacity', 'armor': 'armorHP', 'hull': 'hp'}
for eid, rows in T['SHIP_HP_ATTR_EFFECTS'].items():
    for r in rows: have['ship.' + HPMAP[r[0]]].setdefault(int(eid), []).append(('SHIP_HP_ATTR_EFFECTS', r))
for eid, rows in T['SHIP_SENSOR_ATTR_EFFECTS'].items():
    for r in rows:
        tgt = r[0]
        if tgt.startswith('scanStrength:'): tgt = 'scan' + tgt.split(':')[1].capitalize() + 'Strength'
        have['ship.' + tgt].setdefault(int(eid), []).append(('SHIP_SENSOR_ATTR_EFFECTS', r))
for eid in T['SENSOR_STRENGTH_PERCENT_EFFECT_IDS']:
    for k in ('Radar', 'Ladar', 'Magnetometric', 'Gravimetric'): have[f'ship.scan{k}Strength'].setdefault(int(eid), []).append(('SENSOR_STRENGTH_PERCENT_EFFECT_IDS', None))
for eid, r in T['SHIP_SHIELD_RECHARGE_EFFECTS'].items(): have['ship.shieldRechargeRate'].setdefault(int(eid), []).append(('SHIP_SHIELD_RECHARGE_EFFECTS', r))
for eid in list(T['SHIP_SIG_HULL_BONUS_EFFECTS']) + ['2716', '2644', '8108', '6730', '3808', '2029']:
    have['ship.signatureRadius'].setdefault(int(eid), []).append(('signature constants', None))
# Skill rows are keyed by skill, not effect: compare by (target, skill typeId).
skillRows = collections.defaultdict(list)
for r in T['SKILL_MODULE_ATTR_MODS_AT_V']: skillRows['module.' + r[0]].append(r)

json.dump({k: v for k, v in found.items()}, open(os.environ.get('OUT', '/tmp/audit_found.json'), 'w'), default=str, indent=0)
for tgt in sorted(set(found) | set(have)):
    rows = found.get(tgt, [])
    print(f'\n=== {tgt}: pyfa effects {len({r["eid"] for r in rows})}, table effects {len(have.get(tgt, {}))}')
    for r in rows:
        if r['cat'] == 16: continue   # skills: separate section below
        if r['eid'] not in have.get(tgt, {}):
            if r['eid'] in KNOWN:
                print(f"  known   {r['eid']} {EFFECTS[r['eid']].__doc__.split()[0]}: {KNOWN[r['eid']]}"); continue
            print(f"  MISSING {r['eid']} {EFFECTS[r['eid']].__doc__.split()[0]} [{r['meth']} src={aname(r['src']) if r['src'] else r['scale']} pen={r['pen']} grp={r['group']} skill={r['skill']}] filter={r.get('filter','')[:3] if r.get('filter') else ''} on {r['n']}x {r['ex']}")
    pyfaIds = {r['eid'] for r in rows}
    for eid in have.get(tgt, {}):
        if eid not in pyfaIds: print(f'  EXTRA   {eid} {ename(eid) if str(eid) in effs else "?"} via {[x[0] for x in have[tgt][eid]]}')
    sk = [r for r in rows if r['cat'] == 16]
    if sk and tgt.startswith('module.'):
        tableSkills = {(s if isinstance(s, int) else s) for r in skillRows.get(tgt, []) for s in []}
        for r in sk:
            print(f"  skill   {r['eid']} {EFFECTS[r['eid']].__doc__.split()[0]} src={aname(r['src']) if r['src'] else r['scale']} on {r['ex'][:1]} filter={r.get('filter','')[:2]}")

# --- Row-level checks: same effect present, but is every (stat, source attr) row there,
#     with the right filter and stacking flag? ------------------------------------------
print('\n\n######## ROW-LEVEL CHECKS ########')
def table_rows(tgt, eid):
    return [r for (_, r) in have.get(tgt, {}).get(eid, []) if r is not None]
def filt_ok(row_kind, row_vals, rec):
    sk = sorted({skillId[x[1]] for x in rec if x[0] == 'skill'}); gs = sorted({x[1].lower() for x in rec if x[0] == 'eq'})
    if row_kind == 's': return sorted(row_vals) == sk and not gs
    if row_kind == 'g': return sorted(v.lower() for v in row_vals) == gs and not sk
    return False
for tgt, rows in sorted(found.items()):
    for r in rows:
        if r['cat'] == 16 or r['eid'] not in have.get(tgt, {}): continue
        trs = table_rows(tgt, r['eid'])
        if not trs: continue
        if tgt.startswith('module.'):
            match = [t for t in trs if t[4] == r['src']]
            if not match:
                print(f"  ROW MISSING {tgt} {r['eid']} {ename(r['eid'])}: src={aname(r['src']) if r['src'] else r['scale']} filter={r['filter']} pen={r['pen']}")
                continue
            if not any(filt_ok(t[2], t[3], r['filter']) for t in match):
                print(f"  FILTER DIFF {tgt} {r['eid']} {ename(r['eid'])}: pyfa {r['filter']} vs table {[ (t[2], t[3]) for t in match]}")
            if any((len(t) > 6 and bool(t[6]) != r['pen']) or (len(t) <= 6 and r['pen']) for t in match):
                print(f"  PENALTY DIFF {tgt} {r['eid']} {ename(r['eid'])}: pyfa pen={r['pen']} table {[t[6] if len(t) > 6 else 0 for t in match]}")
            if any(bool(t[5]) != bool(r['skill']) for t in match):
                print(f"  LEVEL DIFF {tgt} {r['eid']} {ename(r['eid'])}: pyfa skill={r['skill']} table perLevel {[t[5] for t in match]}")
        else:
            srcs = [t[2] if len(t) > 2 and isinstance(t[2], int) else None for t in trs]
            if r['src'] not in srcs and not any(isinstance(t, list) and r['src'] in t for t in trs):
                print(f"  ROW MISSING {tgt} {r['eid']} {ename(r['eid'])}: src={aname(r['src']) if r['src'] else r['scale']} table={trs}")

# --- Skills: [attr, 's'|'g', ids|names, pct@V] -----------------------------------------
print('\n######## SKILL ROWS (SKILL_MODULE_ATTR_MODS_AT_V) ########')
for tgt in ('module.capacitorNeed', 'module.duration'):
    rows = [r for r in found.get(tgt, []) if r['cat'] == 16]
    table = skillRows.get(tgt, [])
    for r in rows:
        carrier = r['ex'][0]
        try: pct = A(carrier)[aname(r['src'])] * 5
        except Exception: pct = None
        sk = sorted({skillId[x[1]] for x in r['filter'] if x[0] == 'skill'}); gs = sorted({x[1].lower() for x in r['filter'] if x[0] == 'eq'})
        want = [tgt.split('.')[1], 's' if sk else 'g', sk or gs, pct]
        ok = any(t[0] == want[0] and t[1] == want[1] and sorted(t[2]) == sorted(want[2]) and abs(t[3] - (want[3] or 0)) < 1e-6 for t in table)
        if not ok: print(f"  SKILL ROW MISSING/DIFFERENT: {want}  ({carrier}, effect {r['eid']} {ename(r['eid'])})")
