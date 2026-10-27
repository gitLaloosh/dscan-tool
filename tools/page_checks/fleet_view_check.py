"""The fleet view (v2026.10.14.83; roadmap/local-and-fleet-plan.md L4, decisions D4, D5, D9).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/fleet_view_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The real page with ESI and zKillboard answered from sa_mocks.py: Crimson Tide's and Void Runners' kills and losses are
built from golden-fit killmails, so each common fit's numbers are checked against the regression suite's pyfa-verified
pins (Curse 177 DPS / 22,648 EHP, Vedmak 507, Loki 801), and the shares, ≈ counts and the summary against
sa_mocks.expected_fleet() (the rules in Python). Checks:
  * over the threshold: the Fleet / Groups switch, Fleet shown; Groups brings the columns back;
  * the 5 largest groups looked up (hostile first), the rest under "Not looked up" with Look up (1 request for a group
    with no kills);
  * a group's hulls lately: share and ≈ count from its kills (other groups' pilots and capsules don't count), "✓ N on
    scan" from the D-Scan; 4 zKillboard requests at most per group (kills + 3 hulls' losses), none asked twice;
  * the common fit (D5): "Variant 1  3 of 5" with "1 more: MWD instead of AB"; picking variant 2 changes the button and
    the line; one loss: "Fits vary"; no losses: "fit unknown"; 3 of 3: "a strict doctrine", with the newest loss's odd
    charge swapped for the variant's most common one (the pinned DPS);
  * Their fleet, estimated: raw DPS = Σ ≈count × the pinned DPS, ships counted, tackle / cap-warfare counts;
  * › opens the fit in the Fit Analyzer (EFT pasted, that hull analyzed);
  * at 390 px nothing runs off the page; no page errors.
v2026.10.14.82 fails (no fleet view). Since v2026.10.14.89 the fleet view is switched off on the page; this check checks that
first (Groups columns, no switch, no group lookups), then switches it on (saFleetOn = true) to keep its numbers checked.
"""
import sys, os, re
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
        'friendly': [{'id': M.BCM, 'name': 'Blue Coalition Member', 'kind': 'alliance'}, {'id': M.ALLIED, 'name': 'Allied Wing', 'kind': 'alliance'}],
        'hostile': [{'id': M.CRTS, 'name': 'Crimson Tide Syndicate', 'kind': 'alliance'}, {'id': M.TURNCOAT, 'name': 'Turncoat Corp', 'kind': 'corporation'}], 'rows': 15}
SCAN = M.SCAN + '\n' + '\n'.join(f"{M.byname['Curse']}\tSomeone's Curse {i}\tCurse\t2.1 AU" for i in range(4))
GROUPS = """() => [...document.querySelectorAll('#saFleet .fl-g')].map(c => ({key: c.dataset.flG, name: c.querySelector('.fl-gt .nm').firstChild.textContent.trim(),
  side: c.querySelector('.sa-mark').classList.contains('h') ? 'h' : 'n', msg: (c.querySelector('.fl-msg') || {}).textContent || '',
  rows: [...c.querySelectorAll('.fl-h')].map(r => ({hull: r.querySelector('.pr-hull .nm').firstChild.textContent, share: (r.querySelector('.fl-share b') || {}).firstChild ? r.querySelector('.fl-share b').firstChild.textContent.trim() : '',
    est: (r.querySelector('.fl-est') || {}).textContent || '', scan: (r.querySelector('.pr-hull .ctx') || {}).textContent || '', btn: (r.querySelector('.fl-varbtn') || {}).textContent || '',
    line: (r.querySelector('.fl-var > .ctx') || {}).textContent || '', dps: (r.querySelector('.pr-dps .pr-num') || {}).textContent || '', ehp: (r.querySelector('.fl-ehp') || {}).textContent || '',
    ew: [...r.querySelectorAll('.fl-ew .ewar-badge')].map(e => e.textContent).join(''), msg: (r.querySelector('.pr-msg') || {}).textContent || ''}))}))"""
SUM = """() => { const c = document.querySelector('#saFleet .fl-sum'); return {head: c.querySelector('.pr-head .ctx').textContent, v: [...c.querySelectorAll('.fl-stat .v')].map(e => e.textContent),
  ew: [...c.querySelectorAll('.fl-ewl > span')].map(e => e.textContent.trim()), ctx: [...c.querySelectorAll('.fl-stat .ctx')].map(e => e.textContent)}; }"""
def wait_done(pg, n, timeout=150000):
    pg.wait_for_function(f"() => {{ const c = document.querySelector('#saFleet .fl-sum .pr-head .ctx'); return c && c.textContent === '{n} of {n} groups looked up'; }}", timeout=timeout); pg.wait_for_timeout(400)

E = M.expected_fleet()
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 1440, 'height': 1000})
    errs = []
    ctx.on('page', lambda pg: pg.on('pageerror', lambda e: errs.append(str(e))))
    M.route(ctx)
    pg = ctx.new_page(); pg.goto('file://' + HTML)
    pg.evaluate("(s) => localStorage.setItem('dscanSide', JSON.stringify(s))", SIDE); pg.reload(); pg.wait_for_timeout(300)
    # v2026.10.14.89: the fleet view is switched off on the page (the owner: "too many assumptions based on local"); first that,
    # then switched on here to keep its numbers checked
    M.ZKB_CALLS.clear()
    pg.click('#tabBtnDscan'); pg.fill('#localInput', M.LOCAL); pg.fill('#dscanInput', SCAN); pg.click('#analyzeBtn'); pg.wait_for_timeout(300)
    pg.wait_for_function("() => document.querySelector('#saBusy').hidden && !document.querySelector('#analyzeBtn').disabled", timeout=60000); pg.wait_for_timeout(1500)
    off = pg.evaluate("() => [!!document.querySelector('#saFleet'), !!document.querySelector('.sa-cols'), !!document.querySelector('.sa-mode [data-sa-view]'), document.querySelector('.sa-mode .sa-pill').textContent]")
    grp = [c[0] for c in M.ZKB_CALLS if '/kills/allianceID/' in c[0] or '/shipTypeID/' in c[0] or '/kills/corporationID/' in c[0]]
    check(off[:3] == [False, True, False] and not off[3].startswith('Fleet') and not grp, f'v.89: off by default: the Groups columns, no switch, no group lookups on zKillboard {off} ({len(grp)} lookups)')
    pg.evaluate("() => { saFleetOn = true; }")
    M.ZKB_CALLS.clear()
    pg.click('#tabBtnDscan'); pg.fill('#localInput', M.LOCAL); pg.fill('#dscanInput', SCAN); pg.click('#analyzeBtn'); pg.wait_for_timeout(300)
    pg.wait_for_function("() => document.querySelector('#saBusy').hidden && !document.querySelector('#analyzeBtn').disabled", timeout=60000)
    sw = pg.evaluate("() => [...document.querySelectorAll('.sa-mode [data-sa-view]')].map(b => [b.textContent, b.getAttribute('aria-pressed')])")
    check(sw == [['Fleet', 'true'], ['Groups', 'false']] and pg.is_visible('#saFleet') and not pg.query_selector('.sa-cols'), f'over the threshold: the Fleet / Groups switch, Fleet shown {sw}')
    wait_done(pg, 5)
    G = pg.evaluate(GROUPS)
    order = [(g['name'], g['side']) for g in G]
    want = [('Crimson Tide Syndicate', 'h'), ('Void Runners', 'h'), ('Northern Pact', 'n'), ('Quiet Harbor Collective', 'n'), ('Lantern Bay Traders', 'n')]
    check(order == want, f'the 5 largest groups, hostile first {order}')
    rest = pg.evaluate("() => [...document.querySelectorAll('#saFleet .fl-rr .nm')].map(e => e.firstChild.textContent.trim())")
    check(rest == ['Ashen Reach Industries', 'Turncoat Corp', 'Three Pilots Inc'], f'the rest under Not looked up, hostile first {rest}')
    crts, void = G[0], G[1]
    got = [(r['hull'], int(r['share'].rstrip('%')), int(r['est'].lstrip('≈'))) for r in crts['rows']]
    check(got == E['rows'][M.CRTS], f"shares and ≈ counts from its kills (other groups and capsules don't count): {got} vs {E['rows'][M.CRTS]}")
    curse, ved, loki = crts['rows']
    check(curse['scan'] == '✓ 4 on scan' and ved['scan'] == 'none on scan', f"on scan from the D-Scan ({curse['scan']!r}, {ved['scan']!r})")
    check(curse['btn'].replace('▾', '').split() == ['Variant', '1', '3', 'of', '5'] and curse['line'] == '1 more: MWD instead of AB',
          f"the common fit: most common variant, what the next one changes ({curse['btn']!r}, {curse['line']!r})")
    check(curse['dps'] == str(E['dps']['Curse']) and curse['ehp'] == f"{round(M.PIN['Curse']['totalHP'] / 1000)}k" and curse['ew'] == 'TDC',
          f"the Curse fit's numbers = the pins ({curse['dps']} DPS, {curse['ehp']}, {curse['ew']})")
    check(ved['btn'].startswith('Fits vary') and ved['dps'] == str(E['dps']['Vedmak']), f"one loss: fits vary, showing it ({ved['btn']!r}, {ved['dps']})")
    check('fit unknown' in loki['msg'], f"no losses of the hull: fit unknown ({loki['msg']!r})")
    vl = void['rows'][0]
    check((vl['hull'], vl['share'], vl['est']) == ('Loki', '100%', '≈13') and vl['btn'].replace('▾', '').split()[-3:] == ['3', 'of', '3'] and vl['line'] == 'a strict doctrine' and vl['dps'] == str(E['dps']['Loki']),
          f"3 of 3: a strict doctrine; the newest loss's Scourge swapped for the variant's most common charge, so the pinned DPS ({vl['btn']!r}, {vl['line']!r}, {vl['dps']})")
    empty = [g['msg'] for g in G[2:]]
    check(all(m == 'No kills on zKillboard' for m in empty), f'groups with no kills say so {empty}')
    S = pg.evaluate(SUM)
    check(S['v'][0] == f"≈{E['sum_dps']:,}" and S['ctx'][0].endswith(f"≈{E['ships']} ships counted"), f"their fleet: raw DPS Σ ≈count × pinned DPS = {E['sum_dps']:,} ({S['v'][0]}), {E['ships']} ships ({S['ctx'][0]!r})")
    check(S['ew'] == ['T≈32', 'D≈19', 'C≈42'] and S['v'][-1] == '≈0', f"tackle / disruption / cap warfare counts, no logistics ({S['ew']}, {S['v'][-1]})")
    calls = [c[0] for c in M.ZKB_CALLS]
    fleet = [c for c in calls if re.search(r'/kills/(alliance|corporation)ID/\d+/$', c) or '/shipTypeID/' in c]
    check(len(fleet) == len(set(fleet)) == 4 + 2 + 3 and len([c for c in fleet if M.CRTS.__str__() in c]) == 4,
          f'zKillboard: kills + 3 hulls for Crimson Tide (4), kills + 1 hull for Void Runners, kills for the others; none twice ({len(fleet)})')
    # variant 2
    pg.locator(f'#saFleet .fl-g[data-fl-g="a{M.CRTS}"] summary.fl-varbtn').first.click(); pg.wait_for_timeout(200)
    opts = pg.evaluate("() => [...document.querySelectorAll('#saFleet details.fl-pick[open] button.fl-opt')].map(b => [...b.children].map(e => e.textContent).join(' '))")
    pg.click(f'#saFleet details.fl-pick[open] button.fl-opt[data-fl-var$="|1"]'); pg.wait_for_timeout(300)
    c2 = pg.evaluate(GROUPS)[0]['rows'][0]
    check(opts == ['3 of 5 the most common', '2 of 5 MWD instead of AB'] and c2['btn'].replace('▾', '').split() == ['Variant', '2', '2', 'of', '5'] and c2['line'] == 'MWD instead of AB',
          f"picking variant 2: the menu, the button, the line ({opts}, {c2['btn']!r}, {c2['line']!r})")
    S2 = pg.evaluate(SUM); d2 = int(c2['dps'].replace(',', ''))
    want2 = E['sum_dps'] - 19 * E['dps']['Curse'] + 19 * d2
    check(d2 != E['dps']['Curse'] and S2['v'][0] == f"≈{want2:,}", f"the numbers and their fleet follow the pick (Hammerhead II on variant 2: {d2} DPS; fleet {S2['v'][0]} = {want2:,})")
    # look up a smaller group
    M.ZKB_CALLS.clear()
    pg.click('#saFleet [data-fl-look="c%d"]' % M.ASHR); wait_done(pg, 6)
    n = [g['name'] for g in pg.evaluate(GROUPS)]
    check('Ashen Reach Industries' in n and len([c for c in M.ZKB_CALLS if '/corporationID/%d/' % M.ASHR in c[0]]) == 1, f'Look up adds that group (1 request for a group with no kills) {n}')
    # Groups and back
    pg.click('[data-sa-view="groups"]'); pg.wait_for_timeout(200)
    g = pg.evaluate("() => [!!document.querySelector('.sa-cols'), !!document.querySelector('#saFleet')]")
    pg.click('[data-sa-view="fleet"]'); pg.wait_for_timeout(200)
    check(g == [True, False] and pg.is_visible('#saFleet'), f'Groups shows the columns, Fleet the view again {g}')
    # › opens the fit in the Fit Analyzer
    pg.click(f'#saFleet .fl-g[data-fl-g="a{M.VOIDR}"] button.fl-open')
    pg.wait_for_function("() => document.querySelector('#tabFit').style.display === 'block' && /^\\[Loki,/.test(document.querySelector('#fitAnalyzerInput').value)", timeout=30000)
    pg.wait_for_timeout(2500)
    fa = pg.evaluate("() => [document.querySelector('#fitAnalyzerInput').value.split('\\n')[0], (document.querySelector('#fitAnalyzerResults').textContent.match(/Loki/) || [''])[0]]")
    check(fa[0].startswith('[Loki, Void Runners, variant 1]') and fa[1] == 'Loki', f'› opens the fit in the Fit Analyzer {fa}')
    # phone
    pg.set_viewport_size({'width': 390, 'height': 844}); pg.click('#tabBtnDscan'); pg.wait_for_timeout(300)
    over = pg.evaluate("() => [document.documentElement.scrollWidth, [...document.querySelectorAll('#saFleet *')].filter(e => { const r = e.getBoundingClientRect(); return e.checkVisibility() && r.width && (r.right > innerWidth + 1 || r.left < -1); }).map(e => e.className || e.tagName).slice(0, 5)]")
    check(over[0] <= 390 and not over[1], f'390 px: nothing runs off the page {over}')
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
