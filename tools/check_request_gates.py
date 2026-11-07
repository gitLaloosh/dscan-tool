"""Every request the page sends, and how it is paced (v2026.10.14.104, LESSON #93).

    python3 -I tools/check_request_gates.py [index.html]     -> '... 0 problems' (exit 1 otherwise)

The owner, 2026-10-29, after v.100 got his address blocked by zKillboard for an hour: "if the tool were widely used and
we deployed code that got the user's IP banned for any period of time, this would be bad." zKillboard blocks an address
that asks too fast (R2Z2, its live feed: "15 requests per second per IP. Violators will be banned for 1 hour"). A
hidden tab runs its timers late and together, so pacing built from a batch of timers turns into a burst there.

Rules checked in index.html and browser-extension/*.js:
  * every fetch() call is listed in SITES below with the host it reaches. A new one fails this check until it is
    listed here: decide which gate it goes through before it ships;
  * zkillboard.com/api is reached only by zkbFetchNow, and zkbFetchNow only from zkbFetch, the page's one queue: its
    starts ZKB_SPACING_MS (1 s) after the last by Date.now(), ZKB_BUDGET per 10 minutes; since v2026.11.06.4 (build queue
    014) at most ZKB_PARALLEL (3) in the air (zkbSlot), and a list zKillboard couldn't finish asked once more, no sooner
    than ZKB_SLOW_RETRY_MS (30 s) after, then not again until the person presses (o.again);
  * r2z2.zkillboard.com is reached only by itR2Fetch (v2026.10.30.3: the one door), which waits for itKillTurn(), then
    checks the stop (itR2Stopped) and the tripwire before its fetch, and stops for an hour on 429; itKillTurn spaces
    starts by Date.now() and waits through itSleep, a worker's timer; at most IT_R2_PER_S (5) a second, a third of the
    limit (zKillboard's developer, 2026-06-04: the limit may be cut further if abuse continues);
  * nothing else on the page names the zKillboard hosts in a request (XMLHttpRequest, sendBeacon, EventSource, a
    WebSocket, or a fetch whose address isn't in the list);
  * no batch of timers staggers zKillboard requests (setTimeout(..., i * ...) next to itKillGet / zkbFetch).
ESI (esi.evetech.net) is listed but not gated: its calls are capped by how many run at once, not by timers, and ESI
limits errors rather than speed. A new ESI call still has to be listed.
  * v2026.11.04.4 (build queue 012, the lookup budgets): esiFetch is the page's one fetch() to ESI. It sends the request
    it is given as it is (fetch(url, init): no added headers, no cache-busting) and only reads the answer. Every
    esiFetch(...) call names ${ESI}, sits in a function listed in ESI_SITES, and says which kind of lookup it is (a key of
    ESI_KINDS, the budgets panel's "Last 15 min"). A direct fetch() to ESI anywhere else fails the first rule.
"""
import os, re, sys, glob

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
HTML = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
src = open(HTML, encoding='utf-8').read()

# function -> host it fetches. 'zkb' and 'r2z2' must go through their gates; 'esi' is capped by concurrency.
SITES = {
    'zkbFetchNow': 'zkb', 'itR2Fetch': 'r2z2',
    'esiFetch': 'esi',   # v2026.11.04.4: the one fetch() to ESI; its callers are ESI_SITES
}
# function -> its esiFetch calls (v2026.11.04.4; before, each of these had its own fetch() to ESI)
ESI_SITES = {'resolveNamesToIds', 'getType', 'getGroup', 'resolveIdsToNames', 'fetchKillmail',
    'getOrg', 'saAffiliation', 'paAffEsi', 'itSecFetch', 'itGateDest', 'gdServerVersion', 'esiDownCheck'}   # v2026.11.06.6: esiDownCheck (ESI /status/ once a minute only while ESI is down, build queue 015)   # v2026.11.04.3: gdServerVersion (ESI /status/ once per load: item data after a patch); v2026.10.31.5: itGateDest (a stargate's destination); v2026.10.29.5: itCheckBuild (ESI /status/) removed
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
    i, d = m.end(), 1   # v2026.11.02.1: past the parameters first (a default like o = {} has a brace of its own)
    while d:
        d += {'(': 1, ')': -1}.get(s[i], 0); i += 1
    i = s.index('{', i); d = 0
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
    elif fn == 'esiFetch':
        if not arg.startswith('url, init)'): problems.append(f'index.html:{line(src, m.start())}: esiFetch must send the request it was given as it is: fetch(url, init)')
    elif not re.search(HOST_RX[host], arg.split(')')[0] if host != 'esi' else arg):
        problems.append(f'index.html:{line(src, m.start())}: {fn}() is listed for {host} but this fetch() does not name it: {arg[:60]!r}')
for fn in SITES:
    if fn not in seen: problems.append(f'{fn}() is listed but has no fetch() any more: update the list')

# ESI: only through esiFetch, from the listed functions, each call with its kind (v2026.11.04.4)
mk = re.search(r'const ESI_KINDS = \{([^}]*)\}', src)
KINDS = set(re.findall(r'(\w+):', mk.group(1))) if mk else set()
if not KINDS: problems.append('ESI_KINDS not found (the kinds of ESI lookup the budgets panel counts)')
esi_seen = set()
for m in re.finditer(r'(?<![\w.$])esiFetch\(', src):
    if src[:m.start()].rstrip().endswith('function'): continue
    fn = enclosing(starts, m.start()); esi_seen.add(fn)
    # the call's arguments, to its closing parenthesis
    i, d = m.end(), 1
    while d and i < len(src):
        d += {'(': 1, ')': -1}.get(src[i], 0); i += 1
    args = src[m.end():i - 1]
    if fn not in ESI_SITES: problems.append(f'index.html:{line(src, m.start())}: esiFetch() in {fn}(), which is not in ESI_SITES: list it')
    if not re.match(r'\s*`\$\{ESI\}', args): problems.append(f'index.html:{line(src, m.start())}: esiFetch() for something other than ${{ESI}}: {args[:60]!r}')
    kk = re.search(r",\s*'(\w+)'\s*$", args)
    if not kk or kk.group(1) not in KINDS: problems.append(f'index.html:{line(src, m.start())}: esiFetch() without a kind of lookup from ESI_KINDS (the last argument): {args[-40:]!r}')
for fn in ESI_SITES - esi_seen: problems.append(f'{fn}() is in ESI_SITES but has no esiFetch() any more: update the list')
eb = body(src, 'esiFetch') or ''
if re.search(r'headers|cache|Date\.now\(\)\s*\+|[?&]_=', eb.split('esiNote')[0]): problems.append('esiFetch changes the request (headers or cache-busting); it must send what it was given')

# zKillboard API: only through the queue
callers = [enclosing(starts, m.start()) for m in re.finditer(r'(?<![\w.$])zkbFetchNow\(', src) if not src[:m.start()].rstrip().endswith('function')]
if callers != ['zkbFetch']: problems.append(f'zkbFetchNow is called from {callers}, not only from zkbFetch (the queue)')
q = body(src, 'zkbFetch') or ''
if not (re.search(r'zkbLastStart\s*\+\s*ZKB_SPACING_MS\s*-\s*Date\.now\(\)', q) and re.search(r'zkbLastStart\s*=\s*Date\.now\(\)', q) and re.search(r'zkbQueue\s*=', q)):
    problems.append('zkbFetch no longer starts its requests ZKB_SPACING_MS after the last start by Date.now()')
if not re.search(r'await zkbSlot\(\);', q) or not re.search(r'zkbFree\(\)', q): problems.append('zkbFetch no longer takes a slot (ZKB_PARALLEL) for each request')
mm = re.search(r'const ZKB_PARALLEL = (\d+)', src)
if not mm or int(mm.group(1)) > 3: problems.append(f'ZKB_PARALLEL is {mm and mm.group(1)} (at most 3 in the air)')
mm = re.search(r'ZKB_SLOW_RETRY_MS = (\d+)', src)
if not mm or int(mm.group(1)) < 30000: problems.append(f'ZKB_SLOW_RETRY_MS is {mm and mm.group(1)} (at least 30000 ms)')
if not (re.search(r'if\(sl && sl\.n >= 2\)\{ if\(!o\.again\) throw', q) and re.search(r'sl\.at \+ ZKB_SLOW_RETRY_MS - Date\.now\(\)', q)):
    problems.append('zkbFetch no longer asks a slow list only once more, ZKB_SLOW_RETRY_MS after (and again only when pressed)')
# v2026.11.06.6 (build queue 015): ESI's /status/ while ESI is down: once a minute at most, one timer (cleared before it is set again)
mm = re.search(r'const ESI_DOWN_CHECK_MS = (\d+);', src)
if not mm or int(mm.group(1)) < 60000: problems.append(f'ESI_DOWN_CHECK_MS is {mm and mm.group(1)} (at least 60000 ms)')
if not re.search(r'clearTimeout\(esiDown\.t\); esiDown\.t = down \? setTimeout\(', body(src, 'esiDownCheck') or ''): problems.append('esiDownCheck no longer keeps one timer, set only while ESI is down')
mm = re.search(r'const ZKB_SPACING_MS = (\d+);', src)
if not mm or int(mm.group(1)) < 1000: problems.append(f'ZKB_SPACING_MS is {mm and mm.group(1)} (at least 1000 ms)')
# v2026.11.02.1: a caller may keep a reserve (the Fleet tab's Load all), which only ever lowers the cap, never raises it
if not re.search(r'if\(!zkbBudgetSpend\((?:ZKB_BUDGET - \(o\.reserve \|\| 0\)(?:, o\.who)?)?\)\)', body(src, 'zkbFetchNow') or ''): problems.append('zkbFetchNow no longer spends the ZKB_BUDGET')
_sp = re.search(r'function zkbBudgetSpend\((lim = ZKB_BUDGET)?(?:, who)?\)\{', src)   # v2026.11.04.4: who (the budgets' "Used by")
if not _sp or not re.search(r'if\(a\.length >= ' + ('lim' if _sp.group(1) else 'ZKB_BUDGET') + r'\) return false;', body(src, 'zkbBudgetSpend') or ''):
    problems.append('zkbBudgetSpend no longer caps at ZKB_BUDGET (or a lower limit its caller passes)')

# R2Z2: every request waits its turn at the gate
b = body(src, 'itR2Fetch') or ''
t_, s_, w_, f_ = b.find('await itKillTurn()'), b.find('if(itR2Stopped())'), b.find('itR2Times.length >= IT_R2_PER_S'), b.find('fetch(')
if min(t_, s_, w_, f_) < 0 or not (t_ < s_ < w_ < f_): problems.append('itR2Fetch no longer waits for itKillTurn(), then checks the stop and the tripwire, before its fetch()')
if not re.search(r'IT_R2_STOP_STATUS\.includes\(r\.status\)\)\{\s*itR2Stop\(', b): problems.append('itR2Fetch no longer stops at a "too many" answer (IT_R2_STOP_STATUS)')
mm = re.search(r'const IT_R2_STOP_STATUS = \[([^\]]*)\]', src)
if not mm or '429' not in mm.group(1): problems.append('IT_R2_STOP_STATUS must include 429')
mm = re.search(r'const IT_R2_STOP_MS = (\d+) \* 60000;', src)
if not mm or int(mm.group(1)) < 60: problems.append('IT_R2_STOP_MS must be at least an hour (zKillboard bans for an hour)')
mm = re.search(r'const IT_R2_PER_S = (\d+);', src)
if not mm or int(mm.group(1)) > 5: problems.append(f'IT_R2_PER_S is {mm and mm.group(1)} (at most 5 a second: a third of the limit)')
g = body(src, 'itKillTurn') or ''
if not (re.search(r'itKillLast\s*\+\s*IT_KILL_PROBE_MS\s*-\s*Date\.now\(\)', g) and 'await itSleep(' in g and re.search(r'itKillLast\s*=\s*Date\.now\(\)', g) and re.search(r'itKillGate\s*=', g)):
    problems.append('itKillTurn no longer starts requests one at a time, IT_KILL_PROBE_MS apart by Date.now(), waiting through itSleep')
if not re.search(r'const IT_KILL_PROBE_MS = 1000 / IT_R2_PER_S;', src): problems.append('IT_KILL_PROBE_MS is no longer 1000 / IT_R2_PER_S')
if 'new Worker(' not in (body(src, 'itSleep') or ''): problems.append('itSleep no longer times its waits in a worker (a hidden tab bunches page timers)')

# other ways to send a request
for rx, what in ((r'new\s+XMLHttpRequest', 'XMLHttpRequest'), (r'sendBeacon\(', 'navigator.sendBeacon'), (r'new\s+EventSource', 'EventSource'), (r'new\s+WebSocket', 'WebSocket')):
    for m in re.finditer(rx, src): problems.append(f'index.html:{line(src, m.start())}: {what}: send requests through fetch() and list it here')
# a batch of timers staggering zKillboard requests (v.100's burst)
for m in re.finditer(r'setTimeout\([^;\n]*\bi\s*\*[^;\n]*', src):
    ctx = src[m.start() - 200:m.end() + 200]
    if re.search(r'itKillGet|itKillSeq|itR2Fetch|zkbFetch', ctx): problems.append(f'index.html:{line(src, m.start())}: timers staggered by index next to a zKillboard request: in a hidden tab they fire together')

for f in glob.glob(os.path.join(ROOT, 'browser-extension', '*.js')):
    t = open(f, encoding='utf-8').read()
    if re.search(r'(?<![\w.$])fetch\(|XMLHttpRequest|sendBeacon|EventSource|WebSocket', t):
        problems.append(f'{os.path.relpath(f, ROOT)}: the extension sends a request: list it here with its gate')

for p in problems: print('PROBLEM', p)
print(f'REQUEST GATES: {sum(seen.values())} fetch() calls in {len(seen)} functions ({", ".join(f"{k}: {v}" for k, v in sorted(SITES.items()) if v != "esi")} gated; '
      f'ESI through esiFetch from {len(esi_seen)} listed functions); {len(problems)} problems')
sys.exit(1 if problems else 0)
