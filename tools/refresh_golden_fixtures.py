"""Refresh every golden fit's type/group records from CCP's SDE (pyfa's dump).

    PYFA_SRC=/path/to/Pyfa python3 -I tools/refresh_golden_fixtures.py            # report only
    PYFA_SRC=/path/to/Pyfa python3 -I tools/refresh_golden_fixtures.py --write    # rewrite golden_fits.json

Why (LESSONS_LEARNED.md #6): many fixtures were captured as trimmed records.
On 2026-10-14 a missing GROUP record made the engine drop ishtar_zkb137694046's
shield booster entirely, and ~20 fits had fitted modules missing attributes
the engine reads (a cap booster charge with no GJ, a plate with no HP add, an
MWD with no speed factor...). The live page always fetches full records from
ESI, so a trimmed fixture tests something the page never sees.

What it does, per fit:
  * every type the fit references (types{}, shipTypeId, tally incl. cargo,
    highSlotByFlag/midSlotByFlag, killmail items) gets its SDE dogma
    attributes and effects, plus mass/volume/capacity/radius/group/name.
    Other fields an ESI capture had (description, icon_id...) are kept.
  * every group a type points at gets {name, category_id}.
  * types the SDE doesn't have are left alone and reported.
The file is written back in its existing serialization (compact JSON,
ASCII-escaped), so only refreshed records change.

Also writes regression_suite/shared_types.json (v2026.10.14.73): the types the page fetches for EVERY fit
whatever it flies -- the generic Fighter tile's 12 T2 fighters (FIGHTER_REC_TYPES, read from index.html) and
the 4 bombs those bombers launch (fighterAbilityLaunchBombType, attr 2324) -- with their groups. Every harness
that answers type fetches from a fit's fixture falls back to it, so 263 fits don't each carry 16 copies.

Reported per fit: types added, attributes added, attribute values changed
(a value change means the fixture held other game data -- e.g. pre-patch
Hawk), effects added/removed, groups added. Pins are NOT touched: rerun
regression_suite/run_regression.mjs and explain every number that moves.
"""
import sys, os, json, collections, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pyfa_sde import types, td, groups, attrs, _en

GOLDEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'regression_suite', 'golden_fits.json')
WRITE = '--write' in sys.argv

def sde_type(t):
    v = types[str(t)]; d = td.get(str(t), {'dogmaAttributes': [], 'dogmaEffects': []})
    attrsOut = [{'attribute_id': a['attributeID'], 'value': a['value']} for a in d.get('dogmaAttributes', [])]
    have = {a['attribute_id'] for a in attrsOut}
    # ESI lists these type fields as dogma attributes too (mass 4, capacity 38, volume 161, radius 162)
    for aid, key in ((4, 'mass'), (38, 'capacity'), (161, 'volume'), (162, 'radius')):
        if aid not in have and v.get(key) is not None: attrsOut.append({'attribute_id': aid, 'value': v[key]})
    return {'type_id': int(t), 'name': _en(v.get('typeName') or v.get('name')), 'group_id': v['groupID'],
            'published': bool(v.get('published')), 'mass': v.get('mass', 0), 'volume': v.get('volume', 0),
            'capacity': v.get('capacity', 0), 'radius': v.get('radius', 0),
            'dogma_attributes': attrsOut,
            'dogma_effects': [{'effect_id': e['effectID'], 'is_default': bool(e.get('isDefault', False))} for e in d.get('dogmaEffects', [])]}

def referenced_ids(f):
    ids = set(f.get('types', {}))
    ids.add(str(f['shipTypeId']))
    for items in (f.get('tally') or {}).values(): ids |= set(items)
    for key in ('highSlotByFlag', 'midSlotByFlag'):
        for lst in (f.get(key) or {}).values():
            for it in lst: ids.add(str(it['id']))
    if f.get('killmail'):
        for it in f['killmail']['victim'].get('items', []): ids.add(str(it['item_type_id']))
    return ids

def aname(a): return attrs.get(str(a), {}).get('name', str(a))

raw = open(GOLDEN).read()
G = json.loads(raw)
assert json.dumps(G, separators=(',', ':')) == raw, 'golden_fits.json is not in the expected compact serialization'
report = collections.OrderedDict(); unknown = collections.defaultdict(set)
for fitId, f in G.items():
    if not isinstance(f, dict) or 'types' not in f: continue
    r = collections.Counter(); notes = []
    T, Gr = f['types'], f.setdefault('groups', {})
    for t in sorted(referenced_ids(f), key=int):
        if t not in types: unknown[fitId].add(t); continue
        new = sde_type(t)
        old = T.get(t)
        if old is None:
            T[t] = new; r['types added'] += 1; notes.append(f'+type {new["name"]}')
        else:
            oa = {a['attribute_id']: a['value'] for a in old.get('dogma_attributes', [])}
            na = {a['attribute_id']: a['value'] for a in new['dogma_attributes']}
            added = [a for a in na if a not in oa]; dropped = [a for a in oa if a not in na]
            changed = [a for a in na if a in oa and abs(oa[a] - na[a]) > 1e-9]
            oe = {e['effect_id'] for e in old.get('dogma_effects', [])}; ne = {e['effect_id'] for e in new['dogma_effects']}
            if added: r['attributes added'] += len(added); r['records filled'] += 1
            # Merge, don't replace: an attribute or effect a live-ESI capture had but
            # this SDE build lacks is kept (zero placeholders 18/264, Hornet EC-300
            # maxRange, Baryon Exotic Plasma XL effect 600). The SDE wins on values.
            if dropped: r['attributes only in fixture (kept)'] += len(dropped)
            new['dogma_attributes'] += [a for a in old.get('dogma_attributes', []) if a['attribute_id'] in dropped]
            new['dogma_effects'] += [e for e in old.get('dogma_effects', []) if e['effect_id'] in oe - ne]
            for a in changed: notes.append(f'{new["name"]}: {aname(a)} {oa[a]} -> {na[a]}')
            r['values changed'] += len(changed)
            if ne - oe: notes.append(f'{new["name"]}: +effects {sorted(ne - oe)}'); r['effects added'] += len(ne - oe)
            if oe - ne: notes.append(f'{new["name"]}: effects only in fixture, kept {sorted(oe - ne)}'); r['effects only in fixture (kept)'] += len(oe - ne)
            for k in ('name', 'group_id', 'mass', 'volume', 'capacity', 'radius'):
                if old.get(k) in (None, '') or (k == 'group_id' and old.get(k) != new[k]): old[k] = new[k]
            old['dogma_attributes'] = new['dogma_attributes']; old['dogma_effects'] = new['dogma_effects']
        gid = str(T[t]['group_id'])
        if gid not in Gr and gid in groups:
            Gr[gid] = {'name': _en(groups[gid]['groupName']), 'category_id': groups[gid]['categoryID']}
            r['groups added'] += 1
    if any(v for k, v in r.items() if '(kept)' not in k): report[fitId] = (r, notes)

# A fully refreshed file prints "0 of N fits change" -- use report mode as the
# completeness check after any golden-fit addition or SDE update.
print(f'{len(report)} of {sum(1 for f in G.values() if isinstance(f, dict) and "types" in f)} fits change')
tot = collections.Counter()
for fitId, (r, notes) in report.items():
    tot.update(r)
    print(f'\n{fitId}: ' + ', '.join(f'{k} {v}' for k, v in r.items()))
    for n in notes[:12]: print('   ', n)
    if len(notes) > 12: print(f'    ... {len(notes) - 12} more')
print('\nTOTAL:', dict(tot))
for fitId, ids in unknown.items(): print(f'not in SDE (left alone) {fitId}: {sorted(ids, key=int)}')

# The shared fixture (see the docstring).
HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'index.html')
SHARED = os.path.join(os.path.dirname(GOLDEN), 'shared_types.json')
blk = re.search(r'const FIGHTER_REC_TYPES = (\{.*?\}\}\s*;)', open(HTML).read(), re.S)
assert blk, 'FIGHTER_REC_TYPES not found in index.html'
rec = sorted({t for t in re.findall(r'\b(\d{4,6})\b', blk.group(1))}, key=int)
assert len(rec) == 12, f'FIGHTER_REC_TYPES: expected 12 fighters, found {rec}'
bombs = sorted({str(int(a['value'])) for t in rec for a in td[t].get('dogmaAttributes', []) if a['attributeID'] == 2324}, key=int)
shared = {'note': 'Types every fit fetches (the generic Fighter tile): written by tools/refresh_golden_fixtures.py --write', 'types': {}, 'groups': {}}
for t in rec + bombs:
    shared['types'][t] = sde_type(t)
    gid = str(shared['types'][t]['group_id'])
    shared['groups'][gid] = {'name': _en(groups[gid]['groupName']), 'category_id': groups[gid]['categoryID']}
sraw = json.dumps(shared, separators=(',', ':'), ensure_ascii=True)
old_s = open(SHARED).read() if os.path.exists(SHARED) else None
print(f'shared_types.json: {len(rec)} fighters + {len(bombs)} bombs, {len(shared["groups"])} groups: ' + ('unchanged' if old_s == sraw else 'CHANGES'))
if WRITE:
    open(GOLDEN, 'w').write(json.dumps(G, separators=(',', ':')))
    print('\nwrote', GOLDEN)
    if old_s != sraw: open(SHARED, 'w').write(sraw); print('wrote', SHARED)
