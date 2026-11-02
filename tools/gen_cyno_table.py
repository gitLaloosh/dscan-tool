"""Generate CYNO_FIT (index.html, v2026.11.02.2): which hulls can fit a cynosural field generator, by kind, read from CCP's
SDE (the modules' canFitShipGroupNN / canFitShipTypeN attributes), for the System Analyzer's "Ships on scan" rail
(the owner: "some industrial ships can light cynos so let's have a 'Cyno Capable' category").

    PYFA_SRC=/path/to/Pyfa python3 -I tools/gen_cyno_table.py [index.html]          # diff
    PYFA_SRC=/path/to/Pyfa python3 -I tools/gen_cyno_table.py [index.html] --write  # embed

CYNO_FIT {kind: {g: [ship group ids], t: [ship type ids]}}; kind 'regular' (Cynosural Field Generator I), 'covert',
'industrial'. Every published module of the "Cynosural Field Generator" group is read (Standup structure modules aren't in it).
"""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pyfa_sde import types, td, groups, aname, name, _en

grp = [int(g) for g, v in groups.items() if _en(v.get('groupName')) == 'Cynosural Field Generator']
assert len(grp) == 1, grp
mods = sorted(int(t) for t, v in types.items() if v.get('published') and v.get('groupID') == grp[0])
def kind(t):
    n = name(t)
    return 'covert' if 'Covert' in n else 'industrial' if 'Industrial' in n else 'regular'
table = {}
for t in mods:
    k = kind(t)
    e = table.setdefault(k, {'g': [], 't': []})
    for a in td.get(str(t), {}).get('dogmaAttributes', []):
        n = aname(a['attributeID']) or ''
        if re.fullmatch(r'canFitShipGroup\d+', n): e['g'].append(int(a['value']))
        elif re.fullmatch(r'canFitShipType\d+', n): e['t'].append(int(a['value']))
for e in table.values(): e['g'] = sorted(set(e['g'])); e['t'] = sorted(set(e['t']))
assert set(table) == {'regular', 'covert', 'industrial'}, sorted(table)
for k in sorted(table):
    print(k, [_en(groups[str(g)]['groupName']) for g in table[k]['g']], [name(t) for t in table[k]['t']])
html = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(os.path.dirname(__file__), '..', 'index.html'))
src = open(html, encoding='utf-8').read()
new = 'const CYNO_FIT = ' + json.dumps({k: table[k] for k in ('regular', 'covert', 'industrial')}, separators=(',', ':')) + ';'
m = re.search(r'const CYNO_FIT = \{.*?\};', src)
if m:
    print('index.html table is up to date with this SDE.' if m.group(0) == new else 'vs index.html: CHANGED')
if '--write' in sys.argv:
    src, n = re.subn(r'const CYNO_FIT = \{.*?\};', lambda _: new, src, count=1)
    assert n == 1, 'no CYNO_FIT line to replace'
    open(html, 'w', encoding='utf-8').write(src); print('wrote', html)
