"""Generate the Intel tables in index.html (v2026.10.14.96, roadmap/intel-plan.md):

  INTEL_JUMPS  every stargate connection, from the EVE client's own res:/staticdata/jumps.static
  INTEL_SHIPS  every published ship's name (English, and Chinese) -> type ID, from pyfa's SDE data

    EVE_RES=/path/with/resfileindex.txt+ResFiles PYFA_SRC=/path/to/Pyfa python3 -I tools/gen_intel_tables.py [index.html]          # diff
    EVE_RES=... PYFA_SRC=... python3 -I tools/gen_intel_tables.py [index.html] --write                                          # embed

EVE_RES is a folder holding a copy of the client's tq/resfileindex.txt and tq/start.ini (as tq/...) and the
ResFiles/<xx>/<file> that resfileindex names for res:/staticdata/jumps.static (C:\\CCP\\EVE on the owner's PC, read
only). Without EVE_RES (the computer not linked) the jump table is not re-derived: the script says
"jumps: skipped" and checks the ship names only.

jumps.static (its jumps.schema): a uint32 count, then 65-byte items: jumpID, stargateID, fromSystemID, toSystemID
(uint32 LE at 0/4/8/12), jumpType (1 byte at 16), two vec3 doubles (the gates' coordinates). Each connection is
stored once. The page gets:
  sys    base64 of uint16 LE deltas of the sorted system IDs (the first from 30000000)
  edges  base64 of uint16 LE index pairs into sys (each connection once)
  build  the client build (start.ini) the table came from; ESI /status/ server_version is compared with it
  md5    the jumps.static fingerprint (resfileindex's md5 of the file)
System names are not in the client file in a readable form; the page reads them from ESI /universe/names/ the
first time Intel starts and keeps them (INTEL-03 if that fails).
"""
import sys, os, re, json, glob, base64, struct, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
args = [a for a in sys.argv[1:] if not a.startswith('--')]
HTML = args[0] if args else os.path.join(HERE, '..', 'index.html')
WRITE = '--write' in sys.argv
BEGIN, END = '// ---- INTEL TABLES (tools/gen_intel_tables.py; do not edit by hand) ----', '// ---- END INTEL TABLES ----'

src = open(HTML, encoding='utf-8').read()
m = re.search(re.escape(BEGIN) + r'\n(.*?)\n' + re.escape(END), src, re.S)
if not m: sys.exit('index.html has no INTEL TABLES block')
cur = m.group(1)
def cur_json(name):
    mm = re.search(r'^const ' + name + r' = (.*);$', cur, re.M)
    return json.loads(mm.group(1)) if mm else None

# ---- ships, from pyfa's SDE copy ----
PY = os.environ.get('PYFA_SRC')
if not PY: sys.exit('PYFA_SRC is not set')
FSD = os.path.join(PY, 'staticdata', 'fsd_built')
groups, types = {}, {}
for f in sorted(glob.glob(os.path.join(FSD, 'groups.*.json'))): groups.update(json.load(open(f, encoding='utf-8')))
for f in sorted(glob.glob(os.path.join(FSD, 'types.*.json'))): types.update(json.load(open(f, encoding='utf-8')))
shipGroups = {int(g) for g, v in groups.items() if v.get('categoryID') == 6}
ships = {}
for t, v in types.items():
    if v.get('groupID') in shipGroups and v.get('published'):
        n = v.get('typeName') or {}
        ships[int(t)] = [n.get('en-us', ''), n.get('zh', '')]
# a Chinese name two ships share can't name one of them: left out (the English name still works)
zhCount = {}
for en, zh in ships.values(): zhCount[zh] = zhCount.get(zh, 0) + 1
shipRows = {str(t): [en, zh if zh and zhCount[zh] == 1 else ''] for t, (en, zh) in sorted(ships.items())}
assert len(shipRows) > 300, len(shipRows)

# ---- jumps, from the client ----
RES = os.environ.get('EVE_RES')
jumps = None
if RES:
    idx = open(os.path.join(RES, 'tq', 'resfileindex.txt'), encoding='utf-8', errors='replace').read()
    line = next(l for l in idx.splitlines() if l.startswith('res:/staticdata/jumps.static,'))
    _, rel, md5, size, _z = line.split(',')
    b = open(os.path.join(RES, 'ResFiles', *rel.split('/')), 'rb').read()
    assert hashlib.md5(b).hexdigest() == md5, 'jumps.static does not match resfileindex'
    ini = open(os.path.join(RES, 'tq', 'start.ini'), encoding='utf-8').read()
    build = int(re.search(r'^build\s*=\s*(\d+)', ini, re.M).group(1))
    n = struct.unpack_from('<I', b, 0)[0]
    assert len(b) == 4 + 65 * n, (len(b), n)
    conns = set()
    for i in range(n):
        _jid, _sg, fr, to = struct.unpack_from('<4I', b, 4 + i * 65)
        assert fr != to
        conns.add((min(fr, to), max(fr, to)))
    assert len(conns) == n, 'a connection is stored twice'
    S = sorted({s for c in conns for s in c})
    at = {s: i for i, s in enumerate(S)}
    prev, deltas = 30000000, []
    for s in S:
        d = s - prev; assert 0 < d < 65536 or (prev == 30000000 and 0 < d < 65536), d
        deltas.append(d); prev = s
    pairs = []
    for a, c in sorted(conns): pairs += [at[a], at[c]]
    assert len(S) < 65536
    jumps = {'build': build, 'md5': md5, 'n': n, 'systems': len(S),
             'sys': base64.b64encode(struct.pack('<%dH' % len(deltas), *deltas)).decode(),
             'edges': base64.b64encode(struct.pack('<%dH' % len(pairs), *pairs)).decode()}
else:
    jumps = cur_json('INTEL_JUMPS')
    if not jumps: sys.exit('no INTEL_JUMPS in the page and EVE_RES is not set')

new = ('const INTEL_JUMPS = ' + json.dumps(jumps, separators=(',', ':')) + ';\n'
       + 'const INTEL_SHIPS = ' + json.dumps(shipRows, ensure_ascii=False, separators=(',', ':')) + ';')
if new == cur:
    print(f"intel tables match: {len(shipRows)} ships (pyfa), {jumps['n']} gate connections between {jumps['systems']} systems "
          f"(client build {jumps['build']}){'' if RES else ' -- jumps: skipped (no EVE_RES, the table in the page kept)'}")
    sys.exit(0)
if WRITE:
    out = src[:m.start(1)] + new + src[m.end(1):]
    open(HTML, 'w', encoding='utf-8').write(out)
    print(f"written: {len(shipRows)} ships, {jumps['n']} connections, {jumps['systems']} systems, build {jumps['build']}")
    sys.exit(0)
old = cur_json('INTEL_SHIPS') or {}
print('intel tables differ:')
if old != shipRows:
    add = sorted(set(shipRows) - set(old)); gone = sorted(set(old) - set(shipRows))
    chg = [t for t in shipRows if t in old and old[t] != shipRows[t]]
    print(f'  ships: +{len(add)} -{len(gone)} changed {len(chg)}', [shipRows[t][0] for t in add[:8]], [old[t][0] for t in gone[:8]])
oj = cur_json('INTEL_JUMPS') or {}
if RES and oj != jumps:
    print(f"  jumps: page build {oj.get('build')} md5 {oj.get('md5')} n {oj.get('n')} -> client build {jumps['build']} md5 {jumps['md5']} n {jumps['n']}")
sys.exit(1)
