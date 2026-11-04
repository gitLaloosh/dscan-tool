"""What changed in EVE's item data since the build ETA was checked against pyfa (the patch-day report, v2026.11.04.3).

    python3 -I tools/sde_change_report.py [index.html] --pyfa PATH            # print the report (CCP's newest build)
    python3 -I tools/sde_change_report.py [index.html] --pyfa PATH --write --body F
                                                   # the GitHub workflow: rewrite GAME_DATA_PENDING when the list changed,
                                                   #   and write the pull request's text to F
    ... --sde-old P --sde-new P [--old-build N --new-build N]
                                                   # local copies (CCP's JSON Lines zip, or a folder of its .jsonl files)
    ... --changes DIR                              # local copies of changes/<build>.jsonl (the checks; no network)

Build queue 008 (roadmap/game-data-update-plan.md section 2; the owner 2026-11-02: "Eve has an expansion releasing on Nov 10th
... How do we identify stat changes, new skills or modules, etc. Also need to address any implication on pyfa calculations
changing."). The page's numbers come from ESI's live item data run through pyfa's handlers (PYFA CORE tables generated from
the pyfa release in tools/pyfa_core_manifest.json, its `clientBuild`). After a patch, an item whose attributes or effects
changed may be off until pyfa updates; a new effect pyfa has no handler for can't be right at all. This lists them:

- the two builds: the newest SDE build (developers.eveonline.com/static-data/tranquility/latest.jsonl) and the newest SDE
  build at or before the manifest's clientBuild (pyfa's client build need not be an SDE build: found by following the
  changes files back, changes/<build>.jsonl, each naming the build before it in `_meta.lastBuildNumber`);
- method "full": both builds' data (eve-online-static-data-<build>-jsonl.zip; only the five files it needs are read, by
  HTTP range requests, about 25 MB a build instead of 100), compared item by item: new types, published or unpublished,
  attributes old -> new (dogma, and mass / volume / capacity / radius), effects added or removed;
- method "changes": when the older build's zip is no longer published, the changes files only say WHICH items changed
  (no old values), so those are listed as "changed (old values not published)";
- scope: types in categories 6 ships, 7 modules, 8 charges, 16 skills, 18 drones, 20 implants, 32 subsystems, 87 fighters;
- pyfa: for every effect new to an item in scope, whether pyfa's eos/effects.py has `class Effect<id>` (no class = pyfa
  doesn't model it: often harmless, e.g. a visual effect; a hull or module bonus without one is wrong until pyfa adds it).

--write rewrites the page's GAME_DATA_PENDING (every in-scope item changed since the verified build; the page notes it on
fits that use one) only when that list differs from the page's. Nothing is committed here: the workflow opens a pull
request, never commits to main (as tools/jump_table_update.py). The pyfa update process empties the list (PYFA_CORE.md).
"""
import sys, os, re, io, json, zlib, struct, zipfile, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from check_game_data_pending import RX, decode, line as pending_line

args = [a for a in sys.argv[1:] if not a.startswith('--')]
def opt(name):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv): return sys.argv[i + 1]
    return None
OPTS = {k: opt(k) for k in ('--pyfa', '--sde-old', '--sde-new', '--old-build', '--new-build', '--changes', '--body', '--base')}
HTML = next((a for a in args if a not in OPTS.values()), os.path.join(HERE, '..', 'index.html'))
WRITE = '--write' in sys.argv
BASE = OPTS['--base'] or 'https://developers.eveonline.com/static-data/tranquility'
UA = 'eve-threat-assessment patch-day report (github.com/gitlaloosh/dscan-tool)'
SCOPE = {6: 'Ships', 7: 'Modules', 8: 'Charges', 16: 'Skills', 18: 'Drones', 20: 'Implants', 32: 'Subsystems', 87: 'Fighters'}
TYPE_FIELDS = ('mass', 'volume', 'capacity', 'radius')
FILES = ('types.jsonl', 'groups.jsonl', 'typeDogma.jsonl', 'dogmaEffects.jsonl', 'dogmaAttributes.jsonl')

def out(key, val):   # a GitHub Actions step output (nothing outside the Action)
    f = os.environ.get('GITHUB_OUTPUT')
    if f:
        with open(f, 'a', encoding='utf-8') as h: h.write(f'{key}={val}\n')

# ---- reading CCP's data ----
def http(url, rng=None):
    h = {'User-Agent': UA}
    if rng: h['Range'] = f'bytes={rng[0]}-{rng[1]}'
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=300) as r: return r.status, r.read()

class RemoteZip:
    """The members of a zip on a web server, read with range requests (the central directory, then each member)."""
    def __init__(self, url):
        self.url = url
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=60) as r: self.size = int(r.headers['Content-Length'])
        st, tail = http(url, (max(0, self.size - 65536), self.size - 1))
        if st != 206: raise OSError('no range requests')
        e = tail.rfind(b'PK\x05\x06')
        if e < 0: raise OSError('no end of central directory')
        cd_size, cd_off = struct.unpack('<II', tail[e + 12:e + 20])
        st, cd = http(url, (cd_off, cd_off + cd_size - 1))
        self.members, p = {}, 0
        while cd[p:p + 4] == b'PK\x01\x02':
            method, = struct.unpack('<H', cd[p + 10:p + 12]); csize, usize = struct.unpack('<II', cd[p + 20:p + 28])
            nl, xl, cl = struct.unpack('<HHH', cd[p + 28:p + 34]); lo, = struct.unpack('<I', cd[p + 42:p + 46])
            self.members[cd[p + 46:p + 46 + nl].decode('utf-8')] = (method, csize, lo); p += 46 + nl + xl + cl
    def read(self, name):
        method, csize, lo = self.members[name]
        st, lh = http(self.url, (lo, lo + 29))
        nl, xl = struct.unpack('<HH', lh[26:30]); start = lo + 30 + nl + xl
        st, comp = http(self.url, (start, start + csize - 1))
        return comp if method == 0 else zlib.decompress(comp, -15)

def lines_of(source, name):
    if isinstance(source, RemoteZip): return source.read(name).decode('utf-8').splitlines()
    if isinstance(source, str) and os.path.isdir(source):
        p = os.path.join(source, name)
        return open(p, encoding='utf-8').read().splitlines() if os.path.exists(p) else []
    with zipfile.ZipFile(source) as z: return z.read(name).decode('utf-8').splitlines()

def load(source):
    """{types: {id: {...}}, cat: {group: category}, dogma: {id: (attrs, effects)}, effects: {id: name}, attrs: {id: name}}"""
    D = {'types': {}, 'cat': {}, 'dogma': {}, 'effects': {}, 'attrs': {}}
    for l in lines_of(source, 'groups.jsonl'):
        if l.strip(): o = json.loads(l); D['cat'][int(o['_key'])] = int(o.get('categoryID', -1))
    for l in lines_of(source, 'types.jsonl'):
        if not l.strip(): continue
        o = json.loads(l); g = int(o.get('groupID', -1))
        if D['cat'].get(g) not in SCOPE: continue
        D['types'][int(o['_key'])] = {'group': g, 'name': (o.get('name') or {}).get('en', str(o['_key'])), 'published': bool(o.get('published')),
                                      **{f: o.get(f) for f in TYPE_FIELDS}}
    for l in lines_of(source, 'typeDogma.jsonl'):
        if not l.strip(): continue
        o = json.loads(l); k = int(o['_key'])
        if k not in D['types']: continue
        D['dogma'][k] = ({int(a['attributeID']): a['value'] for a in o.get('dogmaAttributes') or []}, {int(e['effectID']) for e in o.get('dogmaEffects') or []})
    for l in lines_of(source, 'dogmaEffects.jsonl'):
        if l.strip(): o = json.loads(l); D['effects'][int(o['_key'])] = o.get('name') or str(o['_key'])
    for l in lines_of(source, 'dogmaAttributes.jsonl'):
        if l.strip(): o = json.loads(l); D['attrs'][int(o['_key'])] = o.get('name') or str(o['_key'])
    return D

def changes_file(build):
    if OPTS['--changes']:
        p = os.path.join(OPTS['--changes'], f'{build}.jsonl')
        return open(p, encoding='utf-8').read() if os.path.exists(p) else None
    try: st, b = http(f'{BASE}/changes/{build}.jsonl')
    except Exception: return None
    return b.decode('utf-8')

def chain(new_build, verified):
    """Follow the changes files back from new_build to the newest build at or before verified: (old build, ids per file)."""
    ids, b, steps = {}, new_build, 0
    while b > verified and steps < 400:
        t = changes_file(b)
        if t is None: return None, ids
        meta = None
        for l in t.splitlines():
            if not l.strip(): continue
            o = json.loads(l)
            if o.get('_key') == '_meta': meta = o; continue
            for k in ('added', 'changed', 'removed'):
                if isinstance(o.get(k), list): ids.setdefault(o['_key'], set()).update(int(i) for i in o[k])
        if not meta: return None, ids
        b = int(meta['lastBuildNumber']); steps += 1
    return b, ids

# ---- pyfa ----
def pyfa_info(path):
    if not path: return None, set()
    eff = os.path.join(path, 'eos', 'effects.py')
    if not os.path.exists(eff): raise SystemExit(f'--pyfa {path}: no eos/effects.py')
    have = {int(m) for m in re.findall(r'^class Effect(\d+)\(', open(eff, encoding='utf-8').read(), re.M)}
    ver = None
    vy = os.path.join(path, 'version.yml')
    if os.path.exists(vy):
        m = re.search(r'^version:\s*(\S+)', open(vy, encoding='utf-8').read(), re.M)
        ver = m.group(1) if m else None
    return ver, have

# ---- the comparison ----
def fmt(v):
    if isinstance(v, float) and v.is_integer(): v = int(v)
    return f'{v:g}' if isinstance(v, float) else str(v)

def compare(old, new):
    """{type id: {'name', 'cat', 'kind': new|changed|removed, 'lines': [...], 'effects_added': set}}"""
    res = {}
    for k in sorted(set(old['types']) | set(new['types'])):
        a, b = old['types'].get(k), new['types'].get(k)
        t = b or a; cat = (new if b else old)['cat'].get(t['group'])
        item = {'name': t['name'], 'cat': cat, 'lines': [], 'effects_added': set()}
        da, db = old['dogma'].get(k, ({}, set())), new['dogma'].get(k, ({}, set()))
        if a is None:
            item['kind'] = 'new'
            if not b['published']: item['lines'].append('not published yet')
            item['effects_added'] = set(db[1])
        elif b is None:
            item['kind'] = 'removed'
        else:
            item['kind'] = 'changed'
            if a['published'] != b['published']: item['lines'].append('published' if b['published'] else 'unpublished')
            if a['name'] != b['name']: item['lines'].append(f'renamed from {a["name"]}')
            if a['group'] != b['group']: item['lines'].append(f'group {a["group"]} -> {b["group"]}')
            for f in TYPE_FIELDS:
                if a.get(f) != b.get(f): item['lines'].append(f'{f} {fmt(a.get(f))} -> {fmt(b.get(f))}')
            for at in sorted(set(da[0]) | set(db[0])):
                va, vb = da[0].get(at), db[0].get(at)
                if va != vb:
                    nm = new['attrs'].get(at) or old['attrs'].get(at) or str(at)
                    item['lines'].append(f'{nm} {"(none)" if va is None else fmt(va)} -> {"(none)" if vb is None else fmt(vb)}')
            add, rem = db[1] - da[1], da[1] - db[1]
            item['effects_added'] = add
            for e in sorted(rem): item['lines'].append(f'effect removed: {old["effects"].get(e, e)} ({e})')
            if not item['lines'] and not add: continue
        res[k] = item
    return res

def compare_ids(ids, new):
    """Method "changes": the items the changes files name (old values not published)."""
    res = {}
    named = set(ids.get('types', set())) | set(ids.get('typeDogma', set()))
    for k in sorted(named):
        t = new['types'].get(k)
        if not t: continue   # out of scope, or gone
        res[k] = {'name': t['name'], 'cat': new['cat'].get(t['group']), 'kind': 'changed', 'lines': ['changed (old values not published)'],
                  'effects_added': set(new['dogma'].get(k, ({}, set()))[1]) & set(ids.get('dogmaEffects', set()))}
    return res

def report(res, new, old_build, new_build, method, pyfa_ver, have, new_effects):
    L = [f'**EVE item data: build {old_build} -> {new_build}** (method: {method}; '
         + (f'pyfa {pyfa_ver}' if pyfa_ver else 'pyfa version unknown' if have else 'no pyfa given: handlers not checked') + ').', '']
    missing = set()
    for k, it in res.items():
        for e in it['effects_added']:
            if have and e not in have: missing.add(e)
    if not res:
        L.append('Nothing changed in ships, modules, charges, skills, drones, implants, subsystems or fighters.')
        return '\n'.join(L), missing
    n = {}
    for it in res.values(): n[it['cat']] = n.get(it['cat'], 0) + 1
    L.append('Changed: ' + ', '.join(f'{SCOPE[c].lower()} {n[c]}' for c in SCOPE if c in n) + f'; effects pyfa has no handler for: {len(missing)}.')
    L.append('')
    def item_lines(k, it):
        out = [f'- **{it["name"]}** ({k}): {it["kind"]}']
        shown = it['lines'][:12]
        for l in shown: out.append(f'  - {l}')
        if len(it['lines']) > 12: out.append(f'  - +{len(it["lines"]) - 12} more')
        for e in sorted(it['effects_added']):
            nm = new['effects'].get(e, str(e))
            out.append(f'  - effect added: {nm} ({e})' + (' **(no pyfa handler)**' if have and e not in have else ''))
        return out
    order = [('New ships', lambda it: it['cat'] == 6 and it['kind'] == 'new'),
             ('Ships changed', lambda it: it['cat'] == 6 and it['kind'] != 'new')] + [(SCOPE[c], (lambda c: lambda it: it['cat'] == c)(c)) for c in SCOPE if c != 6]
    for title, f in order:
        ks = [k for k, it in res.items() if f(it)]
        if not ks: continue
        L.append(f'### {title} ({len(ks)})')
        for k in sorted(ks, key=lambda k: res[k]['name'].lower()): L += item_lines(k, res[k])
        L.append('')
    if new_effects:
        L.append(f'### New effect IDs ({len(new_effects)})')
        for e in sorted(new_effects):
            L.append(f'- {new["effects"].get(e, e)} ({e})' + ('' if not have else ': pyfa has it' if e in have else ': **no pyfa handler**'))
        L.append('')
    L.append('Until pyfa updates and the PYFA CORE tables are regenerated (PYFA_CORE.md "When pyfa or its data moves"), the page '
             'marks fits and hulls that use these items ("Changed in EVE\'s update").')
    return '\n'.join(L), missing

def source_for(path, build):
    if path: return path
    url = f'{BASE}/eve-online-static-data-{build}-jsonl.zip'
    try: return RemoteZip(url)
    except Exception:
        st, blob = http(url)   # a server without range requests: the whole zip
        return io.BytesIO(blob)

def main():
    src = open(HTML, encoding='utf-8').read()
    m = RX.search(src)
    if not m: raise SystemExit('index.html has no GAME_DATA_PENDING line')
    page_verified, page_build, page_ids = int(m.group(1)), int(m.group(2)), set(decode(m.group(3)))
    verified = json.load(open(os.path.join(HERE, 'pyfa_core_manifest.json'), encoding='utf-8'))['pyfa']['clientBuild']
    pyfa_ver, have = pyfa_info(OPTS['--pyfa'] or os.environ.get('PYFA_SRC'))
    if OPTS['--sde-new']: new_build = int(OPTS['--new-build'] or 0)
    else:
        st, b = http(f'{BASE}/latest.jsonl')
        new_build = next(int(o['buildNumber']) for o in map(json.loads, filter(str.strip, b.decode('utf-8').splitlines())) if o.get('_key') == 'sde')
    out('build', new_build)
    if not OPTS['--sde-new'] and page_build == new_build:
        print(f'build {new_build} is the one the page\'s list was made for: nothing new'); out('changed', 'false'); return 0
    if new_build and new_build <= verified:
        print(f'build {new_build} is not after the verified build {verified}: nothing to report'); out('changed', 'false'); return 0
    if OPTS['--sde-old']: old_build, ids = int(OPTS['--old-build'] or 0), {}
    else:
        old_build, ids = chain(new_build, verified)
        if old_build is None: raise SystemExit(f'the changes files from build {new_build} back to {verified} are incomplete')
        touched = {k for k in ('types', 'typeDogma', 'groups', 'dogmaEffects', 'dogmaAttributes') if ids.get(k)}
        if not touched and page_ids == set():
            print(f'builds {old_build} -> {new_build}: no item data changed (changes files)'); out('changed', 'false'); return 0
    new = load(source_for(OPTS['--sde-new'], new_build))
    try:
        old = load(source_for(OPTS['--sde-old'], old_build)); method = 'full'
        res = compare(old, new)
        new_effects = set(new['effects']) - set(old['effects'])
    except Exception as e:
        if OPTS['--sde-old']: raise
        method = f'changes (build {old_build}\'s data is not published: {type(e).__name__})'
        res = compare_ids(ids, new); new_effects = set(ids.get('dogmaEffects', set())) & set(new['effects'])
    text, missing = report(res, new, old_build, new_build, method, pyfa_ver, have, new_effects)
    print(text)
    f = os.environ.get('GITHUB_STEP_SUMMARY')
    if f:
        with open(f, 'a', encoding='utf-8') as h: h.write(text[:200000] + '\n')
    want = {k for k, it in res.items() if it['kind'] != 'removed'}
    changed = want != page_ids
    out('changed', 'true' if changed else 'false')
    print(f'\npending list: {len(want)} item(s)' + (' (the page lists the same)' if not changed else f' (the page lists {len(page_ids)})'))
    if WRITE and changed:
        new_line = pending_line(verified, new_build if want else 0, want)
        open(HTML, 'w', encoding='utf-8', newline='').write(src[:m.start()] + new_line + src[m.end():])
        print('written: GAME_DATA_PENDING')
    if OPTS['--body'] and changed:
        if len(text) > 60000:   # GitHub's limit for a pull request's text is 65,536 characters
            text = text[:60000].rsplit('\n', 1)[0] + '\n\n(cut here: run `python3 -I tools/sde_change_report.py --pyfa <pyfa>` for the whole report)'
        open(OPTS['--body'], 'w', encoding='utf-8').write(
            text + '\n\n---\nOpened by the "Game data" workflow (tools/sde_change_report.py). Merging it updates the page\'s list of '
            'changed items; nothing else in the page changes. The pyfa update process clears the list (PYFA_CORE.md).\n')
    return 0

if __name__ == '__main__':
    sys.exit(main())
