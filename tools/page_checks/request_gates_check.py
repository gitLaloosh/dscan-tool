"""zKillboard's two gates hold in a hidden tab (v2026.10.14.104, LESSON #93; tools/check_request_gates.py checks the code).

    python3 -I tools/page_checks/request_gates_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner, 2026-10-29: "if the tool were widely used and we deployed code that got the user's IP banned for any period of
time, this would be bad." The real page, twice: as it is, and with its timers made to fire only every 2 s, together, as
a hidden tab's do (a tab behind the game). Each time, many zKillboard requests are asked for at once through the
page's own functions, and every request is timed where it arrives. Checks:
  * the zKillboard API queue (zkbFetch: Pilot Analyzer, the dossier, System Analyzer rows): 6 asked at once go one at a
    time, at least 1 s apart (0.9 s allowing for timing noise);
  * R2Z2, the live kill feed (itKillGet, through itKillTurn): 40 asked at once, never over 12 in any second (zKillboard's
    limit is 15, then the address is blocked for an hour), and all 40 answered within 8 s with the timers bunched too
    (the gate's waits are a worker's);
  * no page errors.
v2026.10.14.102 fails (40 kill requests at once).
"""
import sys, os, re, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from playwright.sync_api import sync_playwright
import sa_mocks as M

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok

COALESCE = """(() => { const st = window.setTimeout; window.setTimeout = (fn, ms, ...a) => { const at = Math.ceil((Date.now() + (+ms || 0)) / 2000) * 2000; return st(fn, Math.max(0, at - Date.now()), ...a); }; })();"""
HITS = {'zkb': [], 'r2z2': []}
ACAO = {'access-control-allow-origin': '*'}
def zkb(route):
    HITS['zkb'].append(time.time()); return route.fulfill(status=200, content_type='application/json', headers=ACAO, body='[]')
def r2z2(route):
    HITS['r2z2'].append(time.time())
    n = int(re.search(r'/(\d+)\.json', route.request.url).group(1)) if re.search(r'/(\d+)\.json', route.request.url) else 0
    return route.fulfill(status=200, content_type='application/json', headers=ACAO, body=json.dumps({'killmail_id': n, 'sequence_id': n, 'esi': {}, 'zkb': {}}))
def per_s(ts): return max((sum(1 for u in ts if t <= u < t + 1) for t in ts), default=0)

with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    for label, init in (('a shown tab', None), ('a hidden tab (timers every 2 s, together)', COALESCE)):
        ctx = b.new_context(viewport={'width': 1280, 'height': 900})
        if init: ctx.add_init_script(init)
        ctx.route(re.compile(r'https://esi\.evetech\.net/.*'), M.esi)
        ctx.route(re.compile(r'https://zkillboard\.com/.*'), zkb)
        ctx.route(re.compile(r'https://r2z2\.zkillboard\.com/.*'), r2z2)
        ctx.route(re.compile(r'https://(images\.evetech\.net|fonts\.).*'), lambda r: r.fulfill(status=404, body=''))
        pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto('file://' + HTML); pg.wait_for_timeout(500)
        pg.evaluate("() => { try{ localStorage.removeItem(ZKB_BUDGET_KEY); }catch(e){} }")
        HITS['zkb'].clear(); HITS['r2z2'].clear()
        t0 = time.time()
        n = pg.evaluate("async () => (await Promise.all(Array.from({length: 6}, (_, i) => zkbFetch(`${ZKB}/kills/characterID/${90000100 + i}/`).then(r => r.status)))).filter(s => s === 200).length", )
        tz = time.time() - t0
        gap = min((y - x for x, y in zip(sorted(HITS['zkb']), sorted(HITS['zkb'])[1:])), default=0)
        check(n == 6 and len(HITS['zkb']) == 6 and gap >= 0.9, f'{label}: the zKillboard API queue: 6 asked at once, {len(HITS["zkb"])} sent one at a time, the closest two {gap:.2f} s apart (1 s, less timing noise; {tz:.1f} s)')
        t0 = time.time()
        n = pg.evaluate("async () => { it.kf = itKfNew(); const r = await Promise.all(Array.from({length: 40}, (_, i) => itKillGet(5000 + i))); return r.filter(Boolean).length; }")
        tk = time.time() - t0
        check(n == 40 and per_s(HITS['r2z2']) <= 12 and tk < 8, f'{label}: R2Z2: 40 asked at once, at most {per_s(HITS["r2z2"])} in any second (the limit is 15), all answered in {tk:.1f} s')
        ctx.close()
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
