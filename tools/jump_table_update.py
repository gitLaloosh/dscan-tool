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

Checked 2026-10-29 in the owner's browser: build 3660036's 13,978 gates make the same 6,989 connections as the page's
table from the client's jumps.static (build 3654997), none missing either way.

Encoding as tools/gen_intel_tables.py: sys = base64 of uint16 LE deltas of the sorted system IDs (the first from
30000000); edges = base64 of uint16 LE index pairs into sys, each connection once, sorted; md5 = the table's fingerprint
(here the md5 of the sorted "a-b" lines; the page keys its cached system names by it, so new systems get their names).
"""
import sys, os, re, io, json, base64, struct, hashlib, zipfile, tempfile, urllib.request

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
        for n in ('mapStargates.jsonl', 'mapSolarSystems.jsonl', 'latest.jsonl'):
            p = os.path.join(SDE, n)
            if os.path.exists(p): files[n] = open(p, encoding='utf-8').read()
        build = latest_build(files['latest.jsonl']) if 'latest.jsonl' in files else int(opt('--build') or 0)
    else:
        if SDE: build, blob = int(opt('--build') or 0), open(SDE, 'rb').read()
        else:
            build = latest_build(fetch(f'{BASE}/latest.jsonl').decode('utf-8'))
            blob = fetch(f'{BASE}/eve-online-static-data-{build}-jsonl.zip')
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            for n in ('mapStargates.jsonl', 'mapSolarSystems.jsonl'): files[n] = z.read(n).decode('utf-8')
    conns, gates = set(), 0
    for line in files['mapStargates.jsonl'].splitlines():
        if not line.strip(): continue
        g = json.loads(line); a = g['solarSystemID']; c = g['destination']['solarSystemID']; gates += 1
        assert a != c, g
        conns.add((min(a, c), max(a, c)))
    names = {}
    for line in files.get('mapSolarSystems.jsonl', '').splitlines():
        if line.strip():
            o = json.loads(line); names[int(o['_key'])] = (o.get('name') or {}).get('en', str(o['_key']))
    assert gates == 2 * len(conns), f'{gates} gates, {len(conns)} connections: a gate without its other end'
    return build, conns, names, gates

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
page = decode(J)
# the encoding round-trips: the page's own connections encode to the page's own sys and edges
t = encode(page, J['build']); assert (t['sys'], t['edges'], t['n'], t['systems']) == (J['sys'], J['edges'], J['n'], J['systems']), 'the encoding differs from gen_intel_tables.py'

try:
    build, conns, names, gates = read_sde()
except Exception as e:
    if CHECK and not SDE:   # the chain may run where CCP's site can't be reached: say so; the Action checks it twice a day
        print(f"jump table: skipped (CCP's static data not reachable from here: {type(e).__name__}); the GitHub Action checks it twice a day")
        sys.exit(0)
    raise

added, gone = sorted(conns - page), sorted(page - conns)
nm = lambda s: names.get(s, str(s))
out('build', build)
if not added and not gone:
    msg = f"jump table matches CCP's build {build}: {len(conns)} connections ({gates} gates); the page's table is from build {J['build']}"
    print(msg); summary(f'**No stargate changed.** {msg}.'); out('changed', 'false')
    sys.exit(0)
lines = [f'- added: {nm(a)} – {nm(c)}' for a, c in added] + [f'- removed: {nm(a)} – {nm(c)}' for a, c in gone]
msg = f"jump table differs from CCP's build {build}: {len(added)} connection(s) added, {len(gone)} removed"
print(msg); print('\n'.join(lines[:40])); out('changed', 'true')
summary(f'**Stargates changed in EVE build {build}.** {len(added)} added, {len(gone)} removed.\n\n' + '\n'.join(lines))
if WRITE:
    new = encode(conns, build)
    blk = m.group(1)
    blk = blk[:mm.start()] + 'const INTEL_JUMPS = ' + json.dumps(new, separators=(',', ':')) + ';' + blk[mm.end():]
    open(HTML, 'w', encoding='utf-8').write(src[:m.start(1)] + blk + src[m.end(1):])
    print(f'written: {new["n"]} connections, {new["systems"]} systems, build {build}')
    if BODY:
        open(BODY, 'w', encoding='utf-8').write(
            f'EVE build {build} changed the stargates. This updates the page\'s jump table (`INTEL_JUMPS` in index.html) '
            f'from CCP\'s published static data; nothing else changes.\n\n' + '\n'.join(lines) +
            f'\n\nThe table now has {new["n"]} connections between {new["systems"]} systems. Made by '
            f'`.github/workflows/jump-table.yml` with `tools/jump_table_update.py`. After merging, run `git pull` before your next commit.\n')
sys.exit(1 if CHECK else 0)
