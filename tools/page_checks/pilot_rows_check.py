"""Pilot rows in a small gang (v2026.10.14.82; roadmap/local-and-fleet-plan.md L3, decision D8).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/pilot_rows_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The real page with ESI and zKillboard answered from sa_mocks.py: each threat pilot's history is built from golden-fit
killmails, so a row's DPS and EHP are checked against the regression suite's pyfa-verified pins (Curse 177 DPS /
22,648 EHP, Vedmak 507 DPS), and which ship each row picks against sa_mocks.expected_rows() (the D8 rules in Python).
Checks:
  * small gang: the Pilots / Groups switch, Pilots shown; Groups brings the columns back; Pilots again;
  * every row looked up (2 zKillboard requests per pilot, nothing else asked twice), then sorted once: hostile first,
    then DPS (fit unknown, then no history, last);
  * the likely ship: newest seen in 30 days (a kill counts), a ship on the D-Scan first, else the hull lost most;
    "fit unknown" when there's no loss of it; capsules don't count; a pilot with no history says so;
  * the numbers: DPS and EHP as the pins, the Curse's EWAR letters T D C, "✓ on scan";
  * a row opens the Pilot Analyzer on that pilot and hull;
  * past 15 pilots: "Not looked up yet" and "Load N more pilots", which looks up the rest (2 requests each);
  * at 390 px nothing runs off the page; no page errors.
v2026.10.14.81 fails (no pilot rows).
"""
import sys, os, re, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from playwright.sync_api import sync_playwright
import sa_mocks as M

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok
SIDE = {'pilot': {'id': 90000001, 'name': 'Test Pilot'}, 'corp': {'id': M.CORP, 'name': 'Example Corp'}, 'alliance': {'id': M.ALLIANCE, 'name': 'Example Alliance'},
        'friendly': [{'id': M.BCM, 'name': 'Blue Coalition Member', 'kind': 'alliance'}], 'hostile': [{'id': M.CRTS, 'name': 'Crimson Tide Syndicate', 'kind': 'alliance'}], 'rows': 15}
ROWS = """() => [...document.querySelectorAll('#saPilots button.pr-row')].map(b => ({
  pilot: b.querySelector('.pr-pilot .nm').textContent, side: b.querySelector('.pr-pilot .sa-mark').classList.contains('h') ? 'h' : 'n',
  hull: (b.querySelector('.pr-hull .nm') || {}).firstChild ? b.querySelector('.pr-hull .nm').firstChild.textContent : null,
  basis: (b.querySelector('.pr-hull .ctx') || {}).textContent || '', dps: (b.querySelector('.pr-dps .pr-num') || {}).textContent || '',
  fu: !!b.querySelector('.pr-fu'), ehp: (b.querySelector('.pr-ehp') || {}).textContent || '', weak: (b.querySelector('.pr-weak') || {}).textContent || '',
  ew: [...b.querySelectorAll('.pr-ew .ewar-badge')].map(e => e.textContent).join(''), scan: (b.querySelector(':scope > .pr-scan') || {}).textContent || '',
  msg: (b.querySelector('.pr-msg') || {}).textContent || '', hullAttr: b.dataset.prHull}))"""
def setup(ctx, side):
    pg = ctx.new_page(); pg.goto('file://' + HTML)
    pg.evaluate("(s) => localStorage.setItem('dscanSide', JSON.stringify(s))", side); pg.reload(); pg.wait_for_timeout(300)
    return pg
def analyze(pg, local, scan=''):
    pg.click('#tabBtnDscan'); pg.fill('#localInput', local); pg.fill('#dscanInput', scan); pg.click('#analyzeBtn'); pg.wait_for_timeout(300)
    pg.wait_for_function("() => document.querySelector('#saBusy').hidden && !document.querySelector('#analyzeBtn').disabled", timeout=60000)
def rows_done(pg, n, timeout=120000):
    pg.wait_for_function(f"() => {{ const c = document.querySelector('#saPilots .pr-head .ctx'); return c && c.textContent === '{n} of {n} looked up'; }}", timeout=timeout); pg.wait_for_timeout(300)

E = M.expected_rows()
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 1440, 'height': 1000})
    errs = []
    ctx.on('page', lambda pg: pg.on('pageerror', lambda e: errs.append(str(e))))
    M.route(ctx)
    pg = setup(ctx, SIDE)
    M.ZKB_CALLS.clear()
    analyze(pg, '\n'.join(M.SMALL_LOCAL), M.SCAN_ROWS)
    sw = pg.evaluate("() => [...document.querySelectorAll('.sa-mode [data-sa-view]')].map(b => [b.textContent, b.getAttribute('aria-pressed')])")
    check(sw == [['Pilots', 'true'], ['Groups', 'false']] and pg.is_visible('#saPilots') and not pg.query_selector('.sa-cols'), f'small gang: the Pilots / Groups switch, Pilots shown {sw}')
    first = pg.evaluate(ROWS)
    check([r['pilot'] for r in first] == [n for n, *_ in sorted(E, key=lambda r: M.SMALL_LOCAL.index(r[0]))] and any(r['msg'] for r in first),
          f"while loading the rows keep the order they were asked in, hostile group first {[r['pilot'] for r in first]}")
    rows_done(pg, 7)
    R = pg.evaluate(ROWS)
    got = [(r['pilot'], r['hull'], int(r['dps'].replace(',', '')) if r['dps'] else None) for r in R]
    check(got == E, f"rows: the likely ship, its DPS, sorted hostile first then DPS:\n      page {got}\n      want {E}")
    by = {r['pilot']: r for r in R}
    nm = lambda i: M.PILOTS[i][0]
    curse = by[nm(M.SMALL_RED[0])]
    exp_ew = ''.join(l for l, k in (('T', 'ewarScramRangeM'), ('D', 'ewarTdRangeM'), ('C', 'ewarNeutRangeM')) if k in M.PIN['Curse'])
    check(curse['basis'] == 'on scan; lost one 3 d ago' and curse['ehp'] == f"{round(M.PIN['Curse']['totalHP'] / 1000)}k" and curse['ew'] == exp_ew,
          f"a Curse lost 3 d ago: EHP {curse['ehp']} (pin {M.PIN['Curse']['totalHP']}), EWAR {curse['ew']!r} (from the pins {exp_ew!r}), {curse['basis']!r}")
    ved = by[nm(M.SMALL_RED[1])]
    check(ved['basis'] == 'on a kill 2 h ago' and ved['hullAttr'] == 'Vedmak', f"a kill counts: newest ship seen ({ved['basis']!r})")
    loki = by[nm(M.SMALL_RED[2])]
    check(loki['fu'] and loki['hull'] == 'Loki' and loki['dps'] == '' and loki['ew'] == '' and loki['ehp'] and loki['hullAttr'] == '', f"never lost that hull: fit unknown, bare hull EHP {loki['ehp']} ({loki['basis']!r})")
    old = by[nm(M.SMALL_FROST[0])]
    check(old['basis'].startswith('2 of 3 losses, latest 40 d ago'), f"nothing in 30 days: the hull lost most ({old['basis']!r})")
    sc = by[nm(M.SMALL_FROST[2])]
    check(sc['hull'] == 'Curse' and sc['basis'].startswith('on scan;') and sc['scan'] == '✓ on scan', f"a ship on the D-Scan wins over a newer one ({sc['basis']!r}, {sc['scan']!r})")
    none = by[nm(M.SMALL_FROST[1])]; pod = by[nm(M.SMALL_FROST[3])]
    check('No kills or losses' in none['msg'] and 'Only capsules' in pod['msg'], f"no history / only a capsule said plainly ({none['msg']!r}, {pod['msg']!r})")
    calls = [c[0] for c in M.ZKB_CALLS]
    per = [c for c in calls if '/characterID/' in c]
    check(len(per) == 14 and len(set(per)) == 14 and len(calls) == 15, f'2 zKillboard requests per pilot, nothing asked twice (+1 for the evidence) ({len(per)}, {len(calls)})')
    # Groups and back
    pg.click('[data-sa-view="groups"]'); pg.wait_for_timeout(200)
    g = pg.evaluate("() => [!!document.querySelector('.sa-cols'), !!document.querySelector('#saPilots')]")
    pg.click('[data-sa-view="pilots"]'); pg.wait_for_timeout(200)
    back = pg.evaluate(ROWS)
    check(g == [True, False] and [r['pilot'] for r in back] == [r['pilot'] for r in R], f'Groups shows the columns, Pilots the same rows again {g}')
    # a row opens the Pilot Analyzer on that pilot and hull
    pg.click(f'#saPilots button.pr-row[data-pr-pilot="{nm(M.SMALL_RED[1])}"]'); pg.wait_for_timeout(500)
    pa = pg.evaluate("() => [document.querySelector('#tabPilot').style.display, document.querySelector('#pilotName').value, document.querySelector('#manualShip').value]")
    check(pa == ['block', nm(M.SMALL_RED[1]), 'Vedmak'], f'a row opens the Pilot Analyzer on that pilot and hull {pa}')
    # past 15: load more
    side20 = dict(SIDE, rows=20)
    ctx2 = b.new_context(viewport={'width': 1440, 'height': 1000}); ctx2.on('page', lambda pg: pg.on('pageerror', lambda e: errs.append(str(e)))); M.route(ctx2)
    pg2 = setup(ctx2, side20)   # its own browser storage: nothing kept from the first paste
    many = [v[0] for k, v in M.PILOTS.items() if v[1] == 98000007][:17]
    M.ZKB_CALLS.clear()
    analyze(pg2, '\n'.join(many))
    rows_done(pg2, 15, 180000)
    r2 = pg2.evaluate(ROWS)
    more = pg2.evaluate("() => (document.querySelector('[data-pr-more]') || {}).textContent || ''")
    ids_many = {str(k) for k, v in M.PILOTS.items() if v[0] in many}
    mine = lambda: [c for c in M.ZKB_CALLS if re.search(r'/(kills|losses)/characterID/(\d+)/$', c[0]) and re.search(r'characterID/(\d+)', c[0]).group(1) in ids_many]   # the other page's Pilot Analyzer may still be asking
    n1 = len(mine())
    check(len(r2) == 17 and sum(r['msg'] == 'Not looked up yet' for r in r2) == 2 and more == 'Load 2 more pilots' and n1 == 30, f'17 pilots: 15 looked up (30 requests: {n1}), 2 waiting, "{more}"')
    pg2.click('[data-pr-more]'); rows_done(pg2, 17, 60000)
    n2 = len(mine())
    check(n2 == 34 and not pg2.query_selector('[data-pr-more]'), f'Load more looks up the rest (2 requests each: {n2 - n1})')
    # phone
    pg.set_viewport_size({'width': 390, 'height': 844}); pg.click('#tabBtnDscan'); pg.wait_for_timeout(300)
    over = pg.evaluate("() => [document.documentElement.scrollWidth, [...document.querySelectorAll('#saPilots *')].filter(e => { const r = e.getBoundingClientRect(); return e.checkVisibility() && r.width && (r.right > innerWidth + 1 || r.left < -1); }).map(e => e.className || e.tagName).slice(0, 5)]")
    check(over[0] <= 390 and not over[1], f'390 px: nothing runs off the page {over}')
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
