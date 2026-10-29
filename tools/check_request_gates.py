"""Every request the page sends, and how it is paced (v2026.10.14.104, LESSON #93).

    python3 -I tools/check_request_gates.py [index.html]     -> '... 0 problems' (exit 1 otherwise)

The owner, 2026-10-29, after v.100 got his address blocked by zKillboard for an hour: "if the tool were widely used and
we deployed code that got the user's IP banned for any period of time, this would be bad." zKillboard blocks an address
that asks too fast (R2Z2, its live feed: "15 requests per second per IP. Violators will be banned for 1 hour"). A
hidden tab runs its timers late and together, so pacing built from a batch of timers turns into a burst there.

Rules checked in index.html and browser-extension/*.js:
  * every fetch() call is listed in SITES below with the host it reaches. A new one fails this check until it is
    listed here: decide which gate it goes through before it ships;
  * zkillboard.com/api is reached only by zkbFetchNow, and zkbFetchNow only from zkbFetch, the page's one queue: one
    at a time, ZKB_SPACING_MS (1 s) after the last start by Date.now(), ZKB_BUDGET per 10 minutes;
  * r2z2.zkillboard.com is reached only by itKillGet and itKillSeq, and each waits for itKillTurn() before its fetch;
    itKillTurn spaces starts by Date.now() and waits through itSleep, a worker's timer;
  * nothing else on the page names the zKillboard hosts in a request (XMLHttpRequest, sendBeacon, EventSource, a
    WebSocket, or a fetch whose address isn't in the list);
  * no batch of timers staggers zKillboard requests (setTimeout(..., i * ...) next to itKillGet / zkbFetch).
ESI (esi.evetech.net) is listed but not gated: its calls are capped by how many run at once, not by timers, and ESI
limits errors rather than speed. A new ESI call still has to be listed.
"""
import os, re, sys, glob

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
HTML = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
src = open(HTML, encoding='utf-8').read()

# function -> host it fetches. 'zkb' and 'r2z2' must go through their gates; 'esi' is capped by concurrency.
SITES = {
    'zkbFetchNow': 'zkb', 'itKillGet': 'r2z2', 'itKillSeq': 'r2z2',
    'resolveNamesToIds': 'esi', 'getType': 'esi', 'getGroup': 'esi', 'resolveIdsToNames': 'esi', 'fetchKillmail': 'esi',
    'getOrg': 'esi', 'saAffiliation': 'esi', 'paAffEsi': 'esi', 'itSecFetch': 'esi', 'itCheckBuild': 'esi',
}
HOST_RX = {'zkb': r'\$\{ZKB\}|zkillboard\.com/api', 'r2z2': r'\$\{IT_R2Z2\}|r2z2\.zkillboard\.com', 'esi': r'\$\{ESI\}|esi\.evetech\.net'}
problems = []

def func_spans(s):
    starts = [(m.start(), m.group(1)) for m in re.finditer(r'^\s*(?:async\s+)?function\s+(\w+)\s*\(', s, re.M)]
    return starts
def enclosing(starts, pos):
    names = [n for p, n in starts if p < pos]
    return names[-1] if names else None
def body(s, name):
    m = re.search(r'^\s*(?:async\s+)?function\s+' + re.escape(name) + r'\s*\(', s, re.M)
    if not m: return None
    i = s.index('{', m.end()); d = 0
    for j in range(i, len(s)):
        if s[j] == '{': d += 1
        elif s[j] == '}':
            d -= 1
            if not d: return s[i:j + 1]
    return None
def line(s, pos): return s.count('\n', 0, pos) + 1

starts = func_spans(src)
seen = {}
for m in re.finditer(r'(?<![\w.$])fetch\(', src):
    fn = enclosing(starts, m.start()); arg = src[m.end():m.end() + 160]
    seen[fn] = seen.get(fn, 0) + 1
    if fn not in SITES:
        problems.append(f'index.html:{line(src, m.start())}: fetch() in {fn}(), which is not listed in tools/check_request_gates.py: decide which gate it goes through, then list it')
        continue
    host = SITES[fn]
    if fn == 'zkbFetchNow':
        if not arg.startswith('url'): problems.append(f'index.html:{line(src, m.start())}: zkbFetchNow fetches something other than its url argument')
    elif not re.search(HOST_RX[host], arg.split(')')[0] if host != 'esi' else arg):
        problems.append(f'index.html:{line(src, m.start())}: {fn}() is listed for {host} but this fetch() does not name it: {arg[:60]!r}')
for fn in SITES:
    if fn not in seen: problems.append(f'{fn}() is listed but has no fetch() any more: update the list')

# zKillboard API: only through the queue
callers = [enclosing(starts, m.start()) for m in re.finditer(r'(?<![\w.$])zkbFetchNow\(', src) if not src[:m.start()].rstrip().endswith('function')]
if callers != ['zkbFetch']: problems.append(f'zkbFetchNow is called from {callers}, not only from zkbFetch (the queue)')
q = body(src, 'zkbFetch') or ''
if not (re.search(r'zkbLastStart\s*\+\s*ZKB_SPACING_MS\s*-\s*Date\.now\(\)', q) and re.search(r'zkbLastStart\s*=\s*Date\.now\(\)', q) and re.search(r'zkbQueue\s*=', q)):
    problems.append('zkbFetch no longer queues one at a time, ZKB_SPACING_MS after the last start by Date.now()')
mm = re.search(r'const ZKB_SPACING_MS = (\d+);', src)
if not mm or int(mm.group(1)) < 1000: problems.append(f'ZKB_SPACING_MS is {mm and mm.group(1)} (at least 1000 ms)')
if not re.search(r'if\(!zkbBudgetSpend\(\)\)', body(src, 'zkbFetchNow') or ''): problems.append('zkbFetchNow no longer spends the ZKB_BUDGET')

# R2Z2: every request waits its turn at the gate
for fn in ('itKillGet', 'itKillSeq'):
    b = body(src, fn) or ''
    t, f = b.find('await itKillTurn()'), b.find('fetch(')
    if t < 0 or f < 0 or t > f: problems.append(f'{fn} does not wait for itKillTurn() before its fetch()')
g = body(src, 'itKillTurn') or ''
if not (re.search(r'itKillLast\s*\+\s*IT_KILL_PROBE_MS\s*-\s*Date\.now\(\)', g) and 'await itSleep(' in g and re.search(r'itKillLast\s*=\s*Date\.now\(\)', g) and re.search(r'itKillGate\s*=', g)):
    problems.append('itKillTurn no longer starts requests one at a time, IT_KILL_PROBE_MS apart by Date.now(), waiting through itSleep')
mm = re.search(r'const IT_KILL_PROBE_MS = (\d+);', src)
if not mm or int(mm.group(1)) < 80: problems.append(f'IT_KILL_PROBE_MS is {mm and mm.group(1)} (at least 80 ms; 15 a second is the limit)')
if 'new Worker(' not in (body(src, 'itSleep') or ''): problems.append('itSleep no longer times its waits in a worker (a hidden tab bunches page timers)')

# other ways to send a request
for rx, what in ((r'new\s+XMLHttpRequest', 'XMLHttpRequest'), (r'sendBeacon\(', 'navigator.sendBeacon'), (r'new\s+EventSource', 'EventSource'), (r'new\s+WebSocket', 'WebSocket')):
    for m in re.finditer(rx, src): problems.append(f'index.html:{line(src, m.start())}: {what}: send requests through fetch() and list it here')
# a batch of timers staggering zKillboard requests (v.100's burst)
for m in re.finditer(r'setTimeout\([^;\n]*\bi\s*\*[^;\n]*', src):
    ctx = src[m.start() - 200:m.end() + 200]
    if re.search(r'itKillGet|itKillSeq|zkbFetch', ctx): problems.append(f'index.html:{line(src, m.start())}: timers staggered by index next to a zKillboard request: in a hidden tab they fire together')

for f in glob.glob(os.path.join(ROOT, 'browser-extension', '*.js')):
    t = open(f, encoding='utf-8').read()
    if re.search(r'(?<![\w.$])fetch\(|XMLHttpRequest|sendBeacon|EventSource|WebSocket', t):
        problems.append(f'{os.path.relpath(f, ROOT)}: the extension sends a request: list it here with its gate')

for p in problems: print('PROBLEM', p)
print(f'REQUEST GATES: {sum(seen.values())} fetch() calls in {len(seen)} functions ({", ".join(f"{k}: {v}" for k, v in sorted(SITES.items()) if v != "esi")} gated; '
      f'{sum(1 for v in SITES.values() if v == "esi")} ESI functions listed); {len(problems)} problems')
sys.exit(1 if problems else 0)
