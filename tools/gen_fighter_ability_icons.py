"""Fighter ability icons, from the EVE client's own data (v2026.10.14.66; the owner 2026-10-25, on the Fighter bay mockup:
"can you use the actual fighter ability icons from the game?").

    PYFA_SRC=/path/to/pyfa python3 -I tools/gen_fighter_ability_icons.py --cache DIR [index.html] [--write]
    PYFA_SRC=/path/to/pyfa python3 -I tools/gen_fighter_ability_icons.py --check [index.html]   # no client: coverage only

DIR is the EVE client's shared cache (on Windows usually C:\\CCP\\EVE): it holds tq/resfileindex.txt and ResFiles/.
Neither pyfa nor the SDE has these icons (pyfa's dogma effects carry no iconID, and images.evetech.net serves item
icons and renders only), so they come from the client:
  * res:/staticdata/fighterabilitiesbytype.static -- per fighter type, its ability slots 0..2, each an abilityID;
  * res:/staticdata/fighterabilities.static       -- per abilityID, its iconID;
  * pyfa's staticdata/fsd_built/iconids.0.json     -- iconID -> res:/ icon file (the SDE's iconIDs);
  * tq/resfileindex.txt                             -- res:/ path -> the file in ResFiles/.
Both .static files are SQLite (table cache: key, JSON value).

Which slot is which pyfa ability effect: slot 0 is the squadron's primary ability (Attack, or Missiles on a superiority
fighter, or its EWAR), slot 1 its propulsion (MWD / afterburner / evasive maneuvers / MJD), slot 2 its secondary
(Missiles, or a bomb). The generator assigns each slot that way, then asserts:
  * every abilityID maps to the same effect on every fighter that has it;
  * every ability pyfa implements (FIGHTER_ABILITY_EFFECTS in index.html) on every published fighter has an icon;
  * a slot left without an effect is an ability pyfa doesn't implement (listed; e.g. superiority fighters' tackle, the
    Shadow's kamikaze), and pyfa shows no toggle for it either.
Output: FIGHTER_ABILITY_ICONS {typeId: {effectId: iconId}} in index.html and img/fighter-abilities/<iconId>.png (64 px,
copied unchanged from the client). The page shows the label alone when a type has no entry (a fighter newer than the
table). Re-run after a game update that adds fighters (pyfa_update_check.py lists new fighter types).
"""
import sys, os, json, re, sqlite3, shutil, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pyfa_sde import types, td, groups, _en

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
PYFA_SRC = os.environ.get('PYFA_SRC') or ''
args = sys.argv[1:]
cache = args[args.index('--cache') + 1] if '--cache' in args else None
html = next((a for i, a in enumerate(args) if not a.startswith('--') and (i == 0 or args[i - 1] != '--cache')), os.path.join(ROOT, 'index.html'))
if not cache and '--check' in args:
    # Without the client (the pyfa update chain): every published fighter's abilities that pyfa implements must have an
    # icon in the table, and every icon file must be there. A new fighter after a game update shows here: re-run with
    # --cache from a current client.
    s = open(html, encoding='utf-8').read()
    implemented = {int(k) for k in json.loads(re.search(r'const FIGHTER_ABILITY_EFFECTS = (.*?);\n', s).group(1))}
    table = json.loads(re.search(r'const FIGHTER_ABILITY_ICONS = (.*?);\n', s).group(1))
    problems = []
    n = 0
    for t, v in types.items():
        if not (v.get('published') and groups.get(str(v.get('groupID')), {}).get('categoryID') == 87): continue
        effs = sorted({e['effectID'] for e in td.get(t, {}).get('dogmaEffects', [])} & implemented)
        if not effs: continue
        n += 1
        have = sorted(int(e) for e in table.get(t, {}))
        if have != effs: problems.append(f'{t} {_en(v.get("typeName") or v.get("name"))}: abilities {effs}, icons for {have}')
    for r in table.values():
        for i in r.values():
            if not os.path.exists(os.path.join(ROOT, 'img', 'fighter-abilities', f'{i}.png')): problems.append(f'img/fighter-abilities/{i}.png missing')
    for x in sorted(set(problems)): print(x)
    print(f'{n} fighter types; {len(set(problems))} problems')
    sys.exit(0)
if not cache: sys.exit('--cache DIR (the EVE client shared cache, with tq/resfileindex.txt and ResFiles/) is required (or --check)')

idx = {}
for line in open(os.path.join(cache, 'tq', 'resfileindex.txt'), encoding='utf-8'):
    p = line.rstrip('\n').split(',')
    if len(p) >= 2: idx[p[0].lower()] = p[1]
def res(path): return os.path.join(cache, 'ResFiles', *idx[path.lower()].split('/'))
def static(path):
    c = sqlite3.connect('file:' + res(path) + '?mode=ro', uri=True)
    try: return {int(k): json.loads(v) for k, v in c.execute('select key, value from cache')}
    finally: c.close()
bytype = static('res:/staticdata/fighterabilitiesbytype.static')
abilities = static('res:/staticdata/fighterabilities.static')
iconFiles = json.load(open(os.path.join(PYFA_SRC, 'staticdata', 'fsd_built', 'iconids.0.json'), encoding='utf-8'))

s = open(html, encoding='utf-8').read()
implemented = {int(k): v[0] for k, v in json.loads(re.search(r'const FIGHTER_ABILITY_EFFECTS = (.*?);\n', s).group(1)).items()}
PROP = {e for e, n in implemented.items() if n in ('fighterAbilityMicroWarpDrive', 'fighterAbilityAfterburner', 'fighterAbilityEvasiveManeuvers')}
SECONDARY = {e for e, n in implemented.items() if n in ('fighterAbilityMissiles', 'fighterAbilityLaunchBomb')}
# pyfa's own list must agree (an ability pyfa implements has an Effect class in eos/effects.py)
src = open(os.path.join(PYFA_SRC, 'eos', 'effects.py'), encoding='utf-8').read()
for e in implemented:
    if not re.search(rf'\nclass Effect{e}\(BaseEffect\)', src): raise AssertionError(f'Effect{e} is in FIGHTER_ABILITY_EFFECTS but not in pyfa')

fighters = sorted(int(t) for t, v in types.items() if v.get('published') and groups.get(str(v.get('groupID')), {}).get('categoryID') == 87
                  and any(e['effectID'] in implemented for e in td.get(str(t), {}).get('dogmaEffects', [])))
abilityEffect, table, unimplemented, missing = {}, {}, collections.Counter(), []
for t in fighters:
    effs = sorted({e['effectID'] for e in td.get(str(t), {}).get('dogmaEffects', [])} & set(implemented))
    slots = bytype.get(t)
    if not slots: missing.append(t); continue
    prop = [e for e in effs if e in PROP]; sec = [e for e in effs if e in SECONDARY]; prim = [e for e in effs if e not in PROP and e not in SECONDARY]
    # superiority fighters: Missiles is their primary (slot 0); their slot 2 is an ability pyfa doesn't implement (tackle)
    if not prim and len(sec) == 1: prim, sec = sec, []
    expect = {0: prim, 1: prop, 2: sec}
    row = {}
    for k, v in sorted(slots.items()):
        slot, aid = int(k[-1]), v['abilityID']
        if len(expect[slot]) > 1: raise AssertionError(f'{t}: slot {slot} could be any of {expect[slot]}')
        if not expect[slot]: unimplemented[aid] += 1; continue
        e = expect[slot][0]
        if abilityEffect.setdefault(aid, e) != e: raise AssertionError(f'ability {aid} is effect {abilityEffect[aid]} and {e}')
        row[e] = abilities[aid]['iconID']
    if set(row) != set(effs): raise AssertionError(f'{t} {_en(types[str(t)].get("typeName") or types[str(t)].get("name"))}: abilities {effs}, icons for {sorted(row)}')
    table[str(t)] = {str(e): row[e] for e in sorted(row)}
for aid in unimplemented:
    if aid in abilityEffect: raise AssertionError(f'ability {aid} is implemented on one fighter and not on another')
icons = sorted({i for r in table.values() for i in r.values()})
print(f'{len(table)} fighter types, {sum(map(len, table.values()))} abilities, {len(icons)} icons; ability -> effect {dict(sorted(abilityEffect.items()))}')
print(f'abilities pyfa does not implement (no toggle): {dict(unimplemented)}; fighters missing from the client data: {missing}')
if missing: raise AssertionError('fighters missing from the client data -- update the client')

out = os.path.join(ROOT, 'img', 'fighter-abilities')
m = re.search(r'const FIGHTER_ABILITY_ICONS = (.*?);\n', s)
changed = not m or json.loads(m.group(1)) != table
for i in icons:
    f = iconFiles[str(i)]['iconFile']
    dst = os.path.join(out, f'{i}.png')
    if not os.path.exists(dst) or open(dst, 'rb').read() != open(res(f), 'rb').read():
        changed = True
        if '--write' in args: os.makedirs(out, exist_ok=True); shutil.copyfile(res(f), dst)
extra = sorted(set(os.listdir(out)) - {f'{i}.png' for i in icons}) if os.path.isdir(out) else []
if extra: print('icons no longer used (delete by hand):', extra)
if '--write' in args and changed:
    if not m: raise AssertionError('const FIGHTER_ABILITY_ICONS = ...; not in index.html -- add the line once')
    s = s[:m.start(1)] + json.dumps(table, separators=(',', ':')) + s[m.end(1):]
    open(html, 'w', encoding='utf-8').write(s); print('index.html table and icons written.')
else:
    print('table / icons differ from this client -- run with --write.' if changed else 'index.html table and icons are up to date with this client.')
