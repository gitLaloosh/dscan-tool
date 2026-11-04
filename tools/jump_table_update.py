"""The page's jump table (INTEL_JUMPS) against CCP's published static data, newest build (v2026.10.29.5).

    python3 -I tools/jump_table_update.py [index.html] --check            # the update-check chain: exit 1 when a gate differs
    python3 -I tools/jump_table_update.py [index.html] --write --body F   # the GitHub Action: rewrite the table when a gate
                                                                         #   changed, and write a pull request's text to F
    ... --sde PATH   use a downloaded copy (the JSON Lines zip, or a folder holding mapStargates.jsonl and
                     mapSolarSystems.jsonl, with latest.jsonl for the build) instead of downloading

The owner, 2026-10-29: "Eve deploys patches very often. is there a way to automate the update so the user never has to
see it?" Until v2026.10.29.4 the page compared EVE's build (ESI /status/) with the build its table came from and showed an
amber warning after every patch, though patches seldom touch stargates. Now .github/workflows/jump-table.yml runs this
twice a day: CCP publishes the static data with each build (developers.eveonline.com/docs/services/static-data/:
tranquility/latest.jsonl names the build; eve-online-static-data-<build>-jsonl.zip holds mapStargates.jsonl, each gate
with its solarSystemID and destination.solarSystemID). When the gate connections differ from the page's, the Action
opens a pull request with the new table; otherwise nothing happens. Only the connections are compared: a new build with
the same gates changes nothing (the table keeps the build it was last rebuilt from).

v2026.11.02.4 (the Intel map, roadmap/intel-map-plan.md): the same run also derives INTEL_MAP, the map's table, from
mapSolarSystems.jsonl and mapRegions.jsonl, aligned to INTEL_JUMPS's sorted systems: CCP's flat schematic position
(position2D x and y, in units of 1e14 m, rounded half up, int16), the security status (to 3 decimals, then in
hundredths, rounded half up, int8: the same arithmetic as the browser-side export the first table came from,
claude/roadmap/intel-map-mockup/sde_extract3.js) and the region (an index into the region names, sorted by region ID).
A change there opens the same pull request; `--check` fails on it too.

v2026.11.04.1 (light-years in the map's hover, roadmap/map-ly-hover-plan.md): INTEL_MAP also holds each system's place in
space, CCP's geographic `position` (3D, metres; position2D is only the flat map's), as p3: x for every system, then y,
then z, each in units of p3u = 0.0001 light-year (CCP's light-year, LY_M = 9.46e15 m, not the real-world one), rounded
half up, int24 little-endian (the largest is about 54 LY: 540,000 units). 0.0001 LY rather than 0.001: the page rounds
distances UP to 0.01 LY (the owner: "Round up to 0.01"), so the table's own error must stay far below that step; it cost
4.1 KB gzipped more (measured on build 3665151).

Checked 2026-10-29 in the owner's browser: build 3660036's 13,978 gates make the same 6,989 connections as the page's
table from the client's jumps.static (build 3654997), none missing either way.

Encoding as tools/gen_intel_tables.py: sys = base64 of uint16 LE deltas of the sorted system IDs (the first from
30000000); edges = base64 of uint16 LE index pairs into sys, each connection once, sorted; md5 = the table's fingerprint
(here the md5 of the sorted "a-b" lines; the page keys its cached system names by it, so new systems get their names).
"""
import sys, os, re, io, json, math, base64, struct, hashlib, zipfile, tempfile, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
args = [a for a in sys.argv[1:] if not a.startswith('--')]
def opt(name):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv): return sys.argv[i + 1]
    return None
SDE = opt('--sde'); BODY = opt('--body')
HTML = next((a for a in args if a not in (SDE, BODY, opt('--build'))), os.path.join(HERE, '..', 'index.html'))
CHECK, WRITE = '--check' in sys.argv, '--write' in sys.argv
BASE = 'https://developers.eveonline.com/static-data/tranquility'
BEGIN, END = '// ---- INTEL TABLES (tools/gen_intel_tables.py; do not edit by hand) ----', '// ---- END INTEL TABLES ----'

def out(key, val):   # a GitHub Actions step output (nothing outside the Action)
    f = os.environ.get('GITHUB_OUTPUT')
    if f:
        with open(f, 'a', encoding='utf-8') as h: h.write(f'{key}={val}\n')
def summary(text):
    f = os.environ.get('GITHUB_STEP_SUMMARY')
    if f:
        with open(f, 'a', encoding='utf-8') as h: h.write(text + '\n')

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'eve-threat-assessment jump-table check (github.com/gitlaloosh/dscan-tool)'})
    with urllib.request.urlopen(req, timeout=300) as r: return r.read()

def latest_build(text):
    for line in text.splitlines():
        if line.strip():
            o = json.loads(line)
            if o.get('_key') == 'sde': return int(o['buildNumber'])
    raise SystemExit('latest.jsonl has no "sde" record')

# ---- CCP's data: the build, the gates, the system names ----
def read_sde():
    files = {}
    if SDE and os.path.isdir(SDE):
        for n in ('mapStargates.jsonl', 'mapSolarSystems.jsonl', 'mapRegions.jsonl', 'latest.jsonl'):
            p = os.path.join(SDE, n)
            if os.path.exists(p): files[n] = open(p, encoding='utf-8').read()
        build = latest_build(files['latest.jsonl']) if 'latest.jsonl' in files else int(opt('--build') or 0)
    else:
        if SDE: build, blob = int(opt('--build') or 0), open(SDE, 'rb').read()
        else:
            build = latest_build(fetch(f'{BASE}/latest.jsonl').decode('utf-8'))
            blob = fetch(f'{BASE}/eve-online-static-data-{build}-jsonl.zip')
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            for n in ('mapStargates.jsonl', 'mapSolarSystems.jsonl', 'mapRegions.jsonl'): files[n] = z.read(n).decode('utf-8')
    conns, gates = set(), 0
    for line in files['mapStargates.jsonl'].splitlines():
        if not line.strip(): continue
        g = json.loads(line); a = g['solarSystemID']; c = g['destination']['solarSystemID']; gates += 1
        assert a != c, g
        conns.add((min(a, c), max(a, c)))
    names, info, regions = {}, {}, {}
    for line in files.get('mapSolarSystems.jsonl', '').splitlines():
        if line.strip():
            o = json.loads(line); k = int(o['_key']); names[k] = (o.get('name') or {}).get('en', str(k))
            if o.get('position2D') is not None:
                p = o.get('position') or {}
                info[k] = (o['position2D']['x'], o['position2D']['y'], float(o['securityStatus']), int(o['regionID']), tuple(p.get(a) for a in 'xyz'))
    for line in files.get('mapRegions.jsonl', '').splitlines():
        if line.strip():
            o = json.loads(line); regions[int(o['_key'])] = (o.get('name') or {}).get('en', str(o['_key']))
    assert gates == 2 * len(conns), f'{gates} gates, {len(conns)} connections: a gate without its other end'
    return build, conns, names, gates, info, regions

# ---- the page's table ----
src = open(HTML, encoding='utf-8').read()
m = re.search(re.escape(BEGIN) + r'\n(.*?)\n' + re.escape(END), src, re.S)
if not m: sys.exit('index.html has no INTEL TABLES block')
mm = re.search(r'^const INTEL_JUMPS = (.*);$', m.group(1), re.M)
J = json.loads(mm.group(1))
def decode(t):
    d = struct.unpack('<%dH' % (len(base64.b64decode(t['sys'])) // 2), base64.b64decode(t['sys']))
    e = struct.unpack('<%dH' % (len(base64.b64decode(t['edges'])) // 2), base64.b64decode(t['edges']))
    S, prev = [], 30000000
    for x in d: prev += x; S.append(prev)
    return {(S[e[i]], S[e[i + 1]]) for i in range(0, len(e), 2)}
def encode(conns, build):
    S = sorted({s for c in conns for s in c}); at = {s: i for i, s in enumerate(S)}
    prev, deltas = 30000000, []
    for s in S:
        d = s - prev; assert 0 < d < 65536, d; deltas.append(d); prev = s
    pairs = []
    for a, c in sorted(conns): pairs += [at[a], at[c]]
    assert len(S) < 65536
    md5 = hashlib.md5(''.join(f'{a}-{c}\n' for a, c in sorted(conns)).encode()).hexdigest()
    return {'build': build, 'md5': md5, 'n': len(conns), 'systems': len(S),
            'sys': base64.b64encode(struct.pack('<%dH' % len(deltas), *deltas)).decode(),
            'edges': base64.b64encode(struct.pack('<%dH' % len(pairs), *pairs)).decode()}
# v2026.11.02.4: the map's table, aligned to the jump table's sorted systems (see the top)
LY_M, P3U = 9.46e15, 0.0001   # CCP's light-year in metres; the position table's unit in light-years (v2026.11.04.1)
def jr(v): return math.floor(v + 0.5)   # half up, as JavaScript's Math.round (Python's round() rounds half to even)
def encode_map(conns, info, regions, build, jumps_md5):
    S = sorted({s for c in conns for s in c}); missing = [s for s in S if s not in info]
    assert not missing, f'{len(missing)} systems without a position2D: {missing[:5]}'
    rids = sorted({info[s][3] for s in S}); ri = {r: i for i, r in enumerate(rids)}
    assert len(rids) < 256
    x = [jr(info[s][0] / 1e14) for s in S]; y = [jr(info[s][1] / 1e14) for s in S]
    sec = [jr(jr(info[s][2] * 1000) / 1000 * 100) for s in S]; reg = [ri[info[s][3]] for s in S]
    assert all(-32768 <= v < 32768 for v in x + y) and all(-128 <= v < 128 for v in sec)
    b64 = lambda f, a: base64.b64encode(struct.pack('<%d%s' % (len(a), f), *a)).decode()
    nopos = [s for s in S if None in info[s][4]]
    assert not nopos, f'{len(nopos)} systems without a position: {nopos[:5]}'
    p3 = [jr(info[s][4][a] / LY_M / P3U) for a in range(3) for s in S]   # x for every system, then y, then z
    assert all(-(1 << 23) <= v < (1 << 23) for v in p3)
    return {'build': build, 'jumps': jumps_md5, 'systems': len(S), 'x': b64('h', x), 'y': b64('h', y),
            'sec': b64('b', sec), 'reg': b64('B', reg), 'regions': [regions.get(r, str(r)) for r in rids],
            'p3': base64.b64encode(b''.join((v & 0xFFFFFF).to_bytes(3, 'little') for v in p3)).decode(), 'p3u': P3U}
def p3_values(t):   # the int24 values back (the checks and the diff count)
    b = base64.b64decode(t); return [int.from_bytes(b[i:i + 3], 'little', signed=True) for i in range(0, len(b), 3)]
mp = re.search(r'^const INTEL_MAP = (.*);$', m.group(1), re.M)
PM = json.loads(mp.group(1)) if mp else None
page = decode(J)
# the encoding round-trips: the page's own connections encode to the page's own sys and edges
t = encode(page, J['build']); assert (t['sys'], t['edges'], t['n'], t['systems']) == (J['sys'], J['edges'], J['n'], J['systems']), 'the encoding differs from gen_intel_tables.py'

try:
    build, conns, names, gates, info, regions = read_sde()
except Exception as e:
    if CHECK and not SDE:   # the chain may run where CCP's site can't be reached: say so; the Action checks it twice a day
        print(f"jump table: skipped (CCP's static data not reachable from here: {type(e).__name__}); the GitHub Action checks it twice a day")
        sys.exit(0)
    raise

added, gone = sorted(conns - page), sorted(page - conns)
nm = lambda s: names.get(s, str(s))
out('build', build)
NM = encode_map(conns, info, regions, build, encode(conns, build)['md5'] if added or gone else J['md5'])   # 'jumps': the INTEL_JUMPS fingerprint it is aligned to
same_map = PM is not None and all(PM.get(k) == NM[k] for k in ('jumps', 'systems', 'x', 'y', 'sec', 'reg', 'regions', 'p3', 'p3u'))
if not same_map:   # how many systems moved, changed security or region (a jump-table change re-aligns every row)
    if PM and PM.get('systems') == NM['systems'] and PM.get('jumps') == NM['jumps']:
        dec = lambda t, f: struct.unpack('<%d%s' % (NM['systems'], f), base64.b64decode(t))
        diff = sum(1 for k, f in (('x', 'h'), ('y', 'h'), ('sec', 'b'), ('reg', 'B')) for a, b in zip(dec(PM[k], f), dec(NM[k], f)) if a != b)
        if PM.get('p3') and PM.get('p3u') == NM['p3u']: diff += sum(1 for a, b in zip(p3_values(PM['p3']), p3_values(NM['p3'])) if a != b)
        elif PM.get('p3') != NM['p3']: diff += NM['systems']   # positions missing (a page from before v2026.11.04.1) or in other units
        map_msg = f'map table: {diff} value(s) differ from build {build}' + ('' if PM.get('regions') == NM['regions'] else ', region names changed')
    else: map_msg = 'map table: missing or made for another jump table'
    print(map_msg)
if not added and not gone and same_map:
    msg = f"jump table matches CCP's build {build}: {len(conns)} connections ({gates} gates); the page's table is from build {J['build']}"
    print(msg); summary(f'**No stargate changed.** {msg}.'); out('changed', 'false')
    sys.exit(0)
lines = [f'- added: {nm(a)} – {nm(c)}' for a, c in added] + [f'- removed: {nm(a)} – {nm(c)}' for a, c in gone] + ([] if same_map else [f'- {map_msg}'])
msg = (f"jump table differs from CCP's build {build}: {len(added)} connection(s) added, {len(gone)} removed" if added or gone
       else f"the map table differs from CCP's build {build} (no stargate changed)")
print(msg); print('\n'.join(lines[:40])); out('changed', 'true')
summary(f'**{msg}.**\n\n' + '\n'.join(lines))
if WRITE:
    new = encode(conns, build) if added or gone else J
    blk = m.group(1)
    blk = blk[:mm.start()] + 'const INTEL_JUMPS = ' + json.dumps(new, separators=(',', ':')) + ';' + blk[mm.end():]
    ml = 'const INTEL_MAP = ' + json.dumps(NM, ensure_ascii=False, separators=(',', ':')) + ';'
    mp2 = re.search(r'^const INTEL_MAP = (.*);$', blk, re.M)
    blk = blk[:mp2.start()] + ml + blk[mp2.end():] if mp2 else blk + '\n' + ml
    open(HTML, 'w', encoding='utf-8').write(src[:m.start(1)] + blk + src[m.end(1):])
    print(f'written: {new["n"]} connections, {new["systems"]} systems' + (f', build {build}' if added or gone else ' (unchanged)') + f'; map table from build {build}')
    if BODY:
        open(BODY, 'w', encoding='utf-8').write(
            f'EVE build {build} changed the stargates or the map. This updates the page\'s jump table (`INTEL_JUMPS`) and map table '
            f'(`INTEL_MAP`) in index.html from CCP\'s published static data; nothing else changes.\n\n' + '\n'.join(lines) +
            f'\n\nThe table now has {new["n"]} connections between {new["systems"]} systems. Made by '
            f'`.github/workflows/jump-table.yml` with `tools/jump_table_update.py`. After merging, run `git pull` before your next commit.\n')
sys.exit(1 if CHECK else 0)
