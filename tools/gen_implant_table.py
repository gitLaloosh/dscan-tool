"""Generate the implant / booster tables (index.html, PYFA CORE section 'implant-calc', since
v2026.10.14.12 -- backlog "Fit Analyzer: apply implants/boosters", Phase 1) from pyfa's own handlers.

    PYFA_SRC=/path/to/Pyfa python3 -I tools/gen_implant_table.py [index.html]          # diff
    PYFA_SRC=/path/to/Pyfa python3 -I tools/gen_implant_table.py [index.html] --write  # embed

pyfa runs implants and boosters as ordinary carriers (eos/saveddata/implant.py, booster.py):
  * Implant.calculateModifiedAttributes: every effect that is type 'passive' and activeByDefault,
    context ('implant',);
  * Booster.calculateModifiedAttributes: every 'passive' effect, plus 'boosterSideEffect' effects
    the user switched on -- pyfa's default is OFF for every side effect (BoosterSideEffect.active =
    False), so side effects are skipped here (DEVIATIONS.md: none, this is pyfa's default);
  * eos/saveddata/fit.py: per runTime (early, normal, late) the order is character+ship, drones,
    fighters, BOOSTERS, IMPLANTS, modules.
Handlers branch on that context (e.g. stackingPenalties = 'implant' not in context), so every effect
is recorded in the context of the item that carries it ('implant' or 'booster'), never reused from a
module/skill table.

Tables (JSON between `const NAME = ` and `;`):
  IMPLANT_EFFECTS {"<ctx>:<effectId>": [[target, attr, op, srcAttr, perLevel, default, penaltyGroup,
                                         skills, skillsOn, groups, groupsOn, runTime], ...]}
      ctx 'implant' | 'booster'.
      target: 'ship' | 'module' | 'charge' (the charge loaded in a module) | 'drone' | 'fighter' |
              'implant' (set bonuses: they modify OTHER implants' attributes, runTime early) |
              'extra' (fit.extraAttributes, e.g. droneControlRange; op is then 'add').
      attr / srcAttr: attribute NAMES (srcAttr: on the carrier; IMPLANT_ATTRS maps names to ids).
      op: 'boost' x(1+v/100) | 'mul' x v | 'add' (pyfa increase, a pre-increase) | 'addPost'
          (increase(position='post'), added after the multipliers). No 'force' row exists (asserted).
      perLevel: 5 when pyfa passes skill= (the All 5 character), else 1.
      penaltyGroup: pyfa's stacking group when stackingPenalties=True, else null.
      skills/groups: filter = (any of skills) AND (any of groups), asserted exact on every published
      item of the target's category; skillsOn/groupsOn: 'item' or 'charge' (charge rows only).
  IMPLANT_ATTRS {name: attributeId} for every attr / srcAttr above.
  PYFA_REMOVED_IMPLANT_IDS [typeIds] implants / boosters pyfa's database does not have (pyfa_sde.pyfa_removed_types:
      expired event boosters deleted by db_update.py, unpublished names); pyfa's EFT import drops them.
Skipped and reported: effects pyfa has no handler for (they do nothing in pyfa either), overheat /
'self' rows, rows whose value depends on the pilot (security status).
"""
import sys, os, re, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pyfa_effects import *

attrId = {v['name']: int(k) for k, v in attrs.items()}
DEFAULT = {v['name']: v.get('defaultValue', 0.0) for v in attrs.values()}
pub = [int(t) for t, v in types.items() if v.get('published')]
def effs_of(t): return [e['effectID'] for e in td.get(str(t), {}).get('dogmaEffects', [])]
def etype(e):
    t = getattr(EFFECTS[e], 'type', None)
    return t if isinstance(t, tuple) else ((t,) if t else ())
# v2026.10.14.13 (LESSON #32): pyfa's database is not the SDE -- db_update.py deletes expired event boosters and
# unpublishes a few names, and pyfa's EFT import then drops those lines. They are left out here and listed in
# PYFA_REMOVED_IMPLANT_IDS so the tool drops them too.
REMOVED = {t for t in pyfa_removed_types() if cat(t) == 20}
IMPLANTS = [t for t in pub if cat(t) == 20 and gname(t) != 'Booster' and t not in REMOVED]
BOOSTERS = [t for t in pub if cat(t) == 20 and gname(t) == 'Booster' and t not in REMOVED]

def sig(t): return (frozenset(reqs(t)), gname(t))
def reps(pool):
    out = {}
    for t in pool: out.setdefault(sig(t), t)
    return list(out.values())
POOLS = {'module': reps([t for t in pub if cat(t) == 7]), 'drone': reps([t for t in pub if cat(t) == 18]),
         'fighter': reps([t for t in pub if cat(t) == 87]), 'implant': reps(IMPLANTS)}
CHARGE_REPS = reps([t for t in pub if cat(t) == 8])
PAIRS = [(c, w) for c in CHARGE_REPS for w in POOLS['module'] if gname(w).startswith(('Missile Launcher', 'Energy Weapon', 'Hybrid Weapon', 'Projectile Weapon', 'Precursor Weapon', 'Vorton Projector'))]
# v2026.10.14.28 (Erik: "Ok do it" -- mindlinks on burst strength): Command Burst modules paired with every charge
# they can load (chargeGroup1-5). Before this the mindlinks' filteredChargeBoost rows on warfareBuffNMultiplier
# matched no pair and were skipped ("filter matches no published item"), so a pasted fit's mindlink only
# lengthened its bursts (the module buffDuration row) and never strengthened them. LESSON #35.
def _chargeGroups(t):
    return {int(x['value']) for x in td.get(str(t), {}).get('dogmaAttributes', [])
            if re.fullmatch(r'chargeGroup\d', aname(x['attributeID']) or '') and x['value']}
_BURSTS = [w for w in POOLS['module'] if gname(w) == 'Command Burst']
if not _BURSTS: raise AssertionError('no published Command Burst module -- group renamed?')
PAIRS += [(c, w) for w in _BURSTS for c in CHARGE_REPS if types[str(c)]['groupID'] in _chargeGroups(w)]
if not any(gname(w) == 'Command Burst' for c, w in PAIRS): raise AssertionError('no Command Burst charge pairs')
COLL_TARGET = {'modules': 'module', 'drones': 'drone', 'fighters': 'fighter', 'appliedImplants': 'implant'}

def matches(t, sk, gs): return (not sk or any(s in reqs(t) for s in sk)) and (not gs or gname(t) in gs)
def recs(rec):
    if any(x[0] == 'skill?' for x in rec): raise AssertionError('filter tests the carrying skill')
    if any(x[0] == 'hasattr' for x in rec): raise AssertionError('filter tests an item attribute')
    return sorted({skillId[x[1]] for x in rec if x[0] == 'skill' and x[1] in skillId}), sorted({x[1] for x in rec if x[0] == 'eq'})

def evaluate(coll, meth, a):
    if coll not in COLL_TARGET or not a or not callable(a[0]): return None
    try:
        if 'Charge' in meth:
            REC.clear(); hits = []
            for c, w in PAIRS:
                try:
                    if a[0](Probe(w, c)): hits.append((c, w))
                except Exception: pass
            sk, gs = recs(sorted(set(REC)))
            for sOn in ('charge', 'item'):
                for gOn in ('charge', 'item'):
                    calc = [(c, w) for c, w in PAIRS if (not sk or any(s in reqs(c if sOn == 'charge' else w) for s in sk))
                            and (not gs or gname(c if gOn == 'charge' else w) in gs)]
                    if set(calc) == set(hits): return ('charge', sk or None, sOn, gs or None, gOn, len(hits))
            raise AssertionError(f'charge filter not expressible ({sk}, {gs})')
        tgt = COLL_TARGET[coll]
        hits, rec = filter_hits(a[0], POOLS[tgt])
        sk, gs = recs(rec)
        if {t for t in POOLS[tgt] if matches(t, sk, gs)} != set(hits): raise AssertionError(f'filter not expressible as skills AND groups ({sk}, {gs})')
        return (tgt, sk or None, 'item', gs or None, 'item', len(hits))
    except AssertionError as ex: return ('ERR', str(ex))

OPS = {'boost': 'boost', 'multiply': 'mul', 'increase': 'add', 'force': 'force'}
def opname(meth):
    m = re.sub(r'^filtered(Item|Charge)', '', meth); m = re.sub(r'(Item|Charge)Attr$', '', m)
    m = m[0].lower() + m[1:]
    if m not in OPS: raise AssertionError(f'unexpected operation {meth}')
    return OPS[m]
def penalty(kw): return str(kw.get('penaltyGroup', 'default')) if kw.get('stackingPenalties') is True else None
def value(expr):
    r = repr(expr)
    m = re.fullmatch(r"\(?a:(\w+)(\*1)?\)?", r)
    if m: return m.group(1), 1
    m = re.fullmatch(r"\(a:(\w+)\*LVL\)", r)
    if m: return m.group(1), 5
    raise AssertionError(f'unexpected value expression {r}')

def build():
    table, skipped, errors, used = {}, collections.Counter(), [], set()
    for ctx, items in (('implant', IMPLANTS), ('booster', BOOSTERS)):
        byEff = collections.defaultdict(list)
        for t in items:
            for e in effs_of(t): byEff[e].append(t)
        for eid in sorted(byEff):
            if eid not in EFFECTS: skipped[f'{ctx}: no pyfa handler (does nothing in pyfa): {ename(eid)}'] += 1; continue
            ty = etype(eid)
            if ctx == 'implant' and not ('passive' in ty and getattr(EFFECTS[eid], 'activeByDefault', True)):
                skipped[f'implant: not passive/activeByDefault ({ty}): {ename(eid)}'] += 1; continue
            if ctx == 'booster' and 'passive' not in ty:
                skipped[f'booster: {"side effect (pyfa default off)" if "boosterSideEffect" in ty else ty}: {ename(eid)}'] += 1; continue
            calls, err = run(eid, ctx, evaluate, rich=True)
            if err: errors.append((ctx, eid, err)); continue
            rows = []; rt = getattr(EFFECTS[eid], 'runTime', 'normal')
            srcHas = {str(a[0]) for coll, meth, a, kw in calls if coll == 'cond' and meth == 'srcHas'}
            for coll, meth, a, kw in calls:
                if coll == 'cond' and meth == 'srcHas': continue   # checked below: the gated value must default to neutral
                if coll == 'cond': raise AssertionError(f'{ctx} effect {eid}: condition {meth} {a} -- model it')
                if coll == 'self': skipped[f'{ctx}: self {a[0] if a else "?"} (overheat / own attribute): {ename(eid)}'] += 1; continue
                if coll == 'extra':
                    k, v = a[0], a[1]; src, lvl = value(v)
                    rows.append(['extra', str(k), 'add', src, lvl, DEFAULT.get(src, 0.0), None, None, 'item', None, 'item', rt]); continue
                if coll == 'extraAttributes':
                    if meth != 'increase': raise AssertionError(f'{ctx} effect {eid}: extraAttributes.{meth}')
                    src, lvl = value(a[1])
                    rows.append(['extra', str(a[0]), 'add', src, lvl, DEFAULT.get(src, 0.0), None, None, 'item', None, 'item', rt]); continue
                if coll == 'ship':
                    if not a: continue
                    target, attr, expr, f = 'ship', str(a[0]), a[1], (None, 'item', None, 'item')
                elif coll in COLL_TARGET:
                    ev = kw.get('_eval')
                    if ev is None: raise AssertionError(f'{ctx} effect {eid}: {coll}.{meth} without a filter')
                    if ev[0] == 'ERR': raise AssertionError(f'{ctx} effect {eid}: {ev[1]}')
                    target, sk, sOn, gs, gOn, n = ev
                    if n == 0: skipped[f'{ctx}: filter matches no published item: {ename(eid)} {a[1]}'] += 1; continue
                    attr, expr, f = str(a[1]), a[2], (sk, sOn, gs, gOn)
                else:
                    raise AssertionError(f'{ctx} effect {eid}: unexpected collection {coll}.{meth}')
                if 'pyfa_effects.Any' in repr(expr): skipped[f'{ctx}: pilot-dependent value: {ename(eid)} {attr}'] += 1; continue
                src, lvl = value(expr)
                if kw.get('skill'): lvl = 5
                op = opname(meth)
                if kw.get('position', 'pre') != 'pre':
                    if op != 'add' or kw['position'] != 'post': raise AssertionError(f'{ctx} effect {eid}: position {kw["position"]} on {meth}')
                    op = 'addPost'   # pyfa increase(position='post'), pyfaModAdd 'addPost'
                row = [target, attr, op, src, lvl, DEFAULT.get(src, 0.0), penalty(kw), f[0], f[1], f[2], f[3], rt]
                if row not in rows: rows.append(row)
            for r in rows:
                if r[3] in srcHas and r[5] != {'mul': 1.0}.get(r[2], 0.0):
                    raise AssertionError(f'{ctx} effect {eid}: row gated on the carrier having {r[3]}, whose default {r[5]} is not neutral')
            if rows:
                table[f'{ctx}:{eid}'] = rows
                for r in rows: used.update((r[1], r[3]))
    return table, skipped, errors, used

table, skipped, errors, used = build()
# Implant set bonuses (target 'implant') must run early, before the bonuses they scale are read (pyfa
# reads a carrier's attribute when its own handler runs): asserted, so a change in pyfa is noticed.
for k, rows in table.items():
    for r in rows:
        if r[0] == 'implant' and r[11] != 'early': raise AssertionError(f'{k}: implant-target row not early: {r}')
        if r[0] != 'implant' and r[11] == 'early': raise AssertionError(f'{k}: early row on {r[0]}: order would matter, model it')
        if r[11] == 'late': raise AssertionError(f'{k}: late row: order would matter, model it')
setTargets = {r[1] for rows in table.values() for r in rows if r[0] == 'implant'}
for k, rows in table.items():
    for r in rows:
        # the engine applies set bonuses as plain unpenalized multipliers on the other implants'
        # attributes, read once: true only while these hold
        if r[0] == 'implant' and (r[2] != 'mul' or r[6] is not None): raise AssertionError(f'{k}: set-bonus row is not an unpenalized multiply: {r}')
        if r[0] == 'implant' and r[3] in setTargets: raise AssertionError(f'{k}: a set bonus reads an attribute another set bonus changes: {r}')
        if r[2] == 'force': raise AssertionError(f'{k}: force row -- model it')
for k in table: table[k] = [r[:11] for r in table[k]]   # runTime asserted above, not needed by the engine
IMPLANT_ATTRS = {n: attrId[n] for n in sorted(used) if n in attrId}
missing = sorted(n for n in used if n not in attrId)
if missing and missing != ['droneControlRange']: raise AssertionError(f'attribute names not in the SDE: {missing}')

print(f'IMPLANT_EFFECTS: {len(table)} effects ({sum(k.startswith("implant:") for k in table)} implant, {sum(k.startswith("booster:") for k in table)} booster), '
      f'{sum(map(len, table.values()))} rows; handler errors {len(errors)}')
for e in errors: print('  handler error:', e)
for k, v in sorted(skipped.items()): print(f'  skipped x{v}:', k)
print('  rows by target:attr:op:penalty', dict(sorted(collections.Counter(f'{r[0]}:{r[1]}:{r[2]}:{r[6]}' for rows in table.values() for r in rows).items())) if '--verbose' in sys.argv else '')
if errors: raise SystemExit('handler errors: fix the recorder/stand-ins before trusting this table')

html = next((x for x in sys.argv[1:] if not x.startswith('--')), os.path.join(os.path.dirname(__file__), '..', 'index.html'))
src = open(html).read(); uptodate = True
print(f'PYFA_REMOVED_IMPLANT_IDS: {len(REMOVED)} implants / boosters pyfa does not offer (expired event boosters, unpublished names)')
for tname, data in (('IMPLANT_EFFECTS', table), ('IMPLANT_ATTRS', IMPLANT_ATTRS), ('PYFA_REMOVED_IMPLANT_IDS', sorted(REMOVED))):
    m = re.compile(r'(const ' + tname + r' = )([\[{].*?[\]}]);\n', re.S).search(src)
    blob = json.dumps(data, separators=(',', ':'))
    if '--write' in sys.argv:
        if not m: sys.exit(tname + ' not found in ' + html)
        src = src[:m.start(2)] + blob + src[m.end(2):]; print('wrote', tname)
    elif m:
        same = json.loads(m.group(2)) == json.loads(blob); print(f'{tname} vs index.html:', 'same' if same else 'DIFFERENT'); uptodate &= same
    else: print(tname, 'not in index.html yet'); uptodate = False
if '--write' in sys.argv: open(html, 'w').write(src); print('into', html)
elif uptodate: print('index.html table is up to date with this pyfa/SDE.')
