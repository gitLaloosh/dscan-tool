"""Pilot Affiliation in the Pilot Analyzer (v2026.10.14.87).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/affiliation_check.py [index.html]   -> 'FAILURES: N' (must be 0)

the owner via todo-inbox: "add pilot affiliation info (alliance, corp, etc). is it possible to pull their zkill threat level
too?", the place he marked (top right of the Pilot Analyzer), and "let's use your pick for all three questions" on
Claude outputs/pilot_affiliation_mockup.html. The real page with ESI and zKillboard answered from sa_mocks.py (its
pilots' ESI character records and corporation histories; zKillboard stats for one of them). Checks:
  * the box: corporation and alliance names and tickers (sa_mocks ORGS), In corp since (the newest corporation history
    record), Pilot since (birthday year), Sec (security status to one decimal); Your Side's tag inside the box;
  * zKillboard, all time, as zKillboard gives it: Danger = dangerRatio %, solo = 100 - gangRatio %, gang ≈ avgGangSize,
    kills, losses, ISK destroyed (shortened); the link to the pilot's zKillboard page;
  * one zKillboard stats request, after the analysis' own (kills, losses); the same pilot again within the hour: none;
  * a pilot with no zKillboard history says so; zKillboard down says "zKillboard stats unavailable (ZKB-01)" (ZKB-05 for an
    answer that isn't a stats object) with the whole message on hover, the rest of the box still there; ESI's character record failing: "(PILOT-08)";
  * ESI's character record failing: no zKillboard stats request; a name that isn't a pilot (PILOT-01): no box;
  * 1480 px: the box at the top right, beside the inputs and the pilot line (no overlap), above the loss tabs;
    1100 px and 390 px: under the pilot line, nothing off the page; no page errors.
v2026.10.14.86 fails (no box).
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
        'friendly': [], 'hostile': [{'id': M.CRTS, 'name': 'Crimson Tide Syndicate', 'kind': 'alliance'}], 'rows': 15}
VED = M.SMALL_RED[1]; NAME = M.PILOTS[VED][0]; OTHER = M.SMALL_RED[0]
BOX = """() => { const b = document.querySelector('#pilotAff'); const t = (s) => (b.querySelector(s) || {}).textContent || '';
  return {hidden: b.hidden, orgs: [...b.querySelectorAll('.pa-org .nm')].map(e => e.textContent), facts: t('.pa-facts'), side: t('#pilotSideTag .side-tag .nm'),
    danger: t('[data-pa-bar=danger] .v'), gang: t('[data-pa-bar=gang] .v'), kills: t('[data-pa=kills]'), losses: t('[data-pa=losses]'), isk: t('[data-pa=isk]'),
    link: (b.querySelector('.pa-zk-h a') || {}).href || '', msg: [...b.querySelectorAll('.pa-msg')].map(e => [e.textContent, e.title || ''])}; }"""
def analyze(pg, name):
    pg.click('#tabBtnPilot'); pg.fill('#pilotName', name); pg.click('#fitBtn'); pg.wait_for_timeout(300)
    pg.wait_for_function("() => !document.querySelector('#fitBtn').disabled", timeout=90000)
def settled(pg):
    pg.wait_for_function("() => { const b = document.querySelector('#pilotAff'); return b.hidden || !b.querySelector('.busy-spin'); }", timeout=60000); pg.wait_for_timeout(200)
def setup(ctx):
    pg = ctx.new_page(); pg.goto('file://' + HTML)
    pg.evaluate("(s) => localStorage.setItem('dscanSide', JSON.stringify(s))", SIDE); pg.reload(); pg.wait_for_timeout(300)
    return pg

with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []
    def new_ctx(w):
        ctx = b.new_context(viewport={'width': w, 'height': 1000}); ctx.on('page', lambda pg: pg.on('pageerror', lambda e: errs.append(str(e)))); M.route(ctx); return ctx
    ctx = new_ctx(1480)
    pg = setup(ctx)
    M.ZKB_CALLS.clear()
    analyze(pg, NAME); settled(pg)
    r = pg.evaluate(BOX)
    corp, alli = M.ORGS[M.PILOTS[VED][1]], M.ORGS[M.CRTS]
    check(not r['hidden'] and r['orgs'] == [f'{corp[1]}[{corp[2]}]', f'{alli[1]}<{alli[2]}>'], f"corporation and alliance with tickers {r['orgs']}")
    check(r['facts'] == 'In corp since Mar 2025Pilot since 2019Sec −2.4', f"In corp since (newest history record), Pilot since, Sec to one decimal ({r['facts']!r})")
    check(r['side'].startswith('Hostile · your hostile list'), f"Your Side's tag in the box ({r['side']!r})")
    S = M.ZK_STATS[VED]
    want = [f"{S['dangerRatio']}% dangerous", f"{100 - S['gangRatio']}% solo · gang ≈{round(S['avgGangSize'])}", f"{S['shipsDestroyed']:,}", f"{S['shipsLost']:,}", '212.4b']
    got = [r['danger'], r['gang'], r['kills'], r['losses'], r['isk']]
    check(got == want and r['link'] == f'https://zkillboard.com/character/{VED}/', f"zKillboard's numbers as given: {got} (want {want}), link {r['link']}")
    calls = [c[0] for c in M.ZKB_CALLS]
    st = [i for i, c in enumerate(calls) if '/stats/characterID/' in c]
    own = [i for i, c in enumerate(calls) if re.search(r'/(kills|losses)/characterID/%d/' % VED, c)]
    check(len(st) == 1 and own and st[0] > max(own), f"one stats request, after the analysis' own ({len(st)} stats; order {[c.split('/api/')[1] for c in calls]})")
    # layout at 1480: top right, beside the inputs and the pilot line, above the loss tabs
    L = pg.evaluate("""() => { const r = (s) => { const e = document.querySelector(s); if(!e) return null; const b = e.getBoundingClientRect(); return [b.left, b.top, b.right, b.bottom]; };
      return {box: r('#pilotAff'), panel: r('#tabPilot > section.panel'), row: r('#tabPilot .row'), head: r('#tabPilot .pilot-head'), btn: r('#refreshLossesBtn'), tabs: r('#fitResults')}; }""")
    bx, pn = L['box'], L['panel']
    beside = all(x is not None and x[2] <= bx[0] for x in (L['row'], L['head'], L['btn']))
    check(abs(pn[2] - bx[2] - 20) <= 2 and bx[1] - pn[1] < 30 and beside and L['tabs'][1] >= bx[3], f"1480 px: top right of the panel, beside the inputs and pilot line, above the loss tabs {L}")
    # the same pilot again: no new stats request (kept an hour)
    M.ZKB_CALLS.clear()
    analyze(pg, NAME); settled(pg)
    again = [c[0] for c in M.ZKB_CALLS if '/stats/characterID/' in c[0]]
    check(not again and pg.evaluate(BOX)['kills'] == f"{S['shipsDestroyed']:,}", f'the same pilot again: no new stats request ({len(again)}), the numbers kept')
    # no zKillboard history
    analyze(pg, M.PILOTS[OTHER][0]); settled(pg)
    r2 = pg.evaluate(BOX)
    check([m[0] for m in r2['msg']] == ['No kills or losses on zKillboard.'] and r2['orgs'], f"no zKillboard history said plainly {r2['msg']}")
    # not a pilot: no box
    pg.click('#tabBtnPilot'); pg.fill('#pilotName', 'Nobody Here At All'); pg.click('#fitBtn'); pg.wait_for_timeout(1500)
    check(pg.evaluate("() => document.querySelector('#pilotAff').hidden") and '(PILOT-01)' in pg.inner_text('#fitStatus'), 'a name that isn\'t a pilot: no box (PILOT-01)')
    ctx.close()
    # zKillboard failing: a wrong answer, then a 500
    ctx = new_ctx(1480)
    FROST = M.SMALL_FROST[0]
    ctx.route(re.compile(r'https://zkillboard\.com/api/stats/characterID/%d/.*' % VED), lambda rt: rt.fulfill(status=500, body='', headers={'access-control-allow-origin': '*'}))
    ctx.route(re.compile(r'https://zkillboard\.com/api/stats/characterID/%d/.*' % FROST), lambda rt: rt.fulfill(status=200, content_type='application/json', body='[]', headers={'access-control-allow-origin': '*'}))
    pg = setup(ctx)
    analyze(pg, M.PILOTS[FROST][0]); settled(pg)
    r5 = pg.evaluate(BOX)
    check(r5['orgs'] and [m[0] for m in r5['msg']] == ['zKillboard stats unavailable (ZKB-05)'] and 'unexpected answer' in r5['msg'][0][1],
          f"an answer that isn't zKillboard's stats object: ZKB-05 {r5['msg']}")
    # (a 500 makes the zKillboard queue wait before asking again, so the ZKB-05 case goes first)
    analyze(pg, NAME); settled(pg)
    r3 = pg.evaluate(BOX)
    check(r3['orgs'] and len(r3['msg']) == 1 and r3['msg'][0][0] == 'zKillboard stats unavailable (ZKB-01)' and "isn't answering" in r3['msg'][0][1],
          f"zKillboard down (500): a short line, zKillboard's outage message (ZKB-01) on hover, the rest of the box there {r3['msg']}")
    ctx.close()
    # ESI's character record failing, in a page of its own (after the 500 above the zKillboard queue would answer from its
    # back-off without asking, and the "not asked" check below would pass whatever the page did: LESSON #77)
    ctx = new_ctx(1480)
    ctx.route(re.compile(r'https://esi\.evetech\.net/.*/characters/%d/\?.*' % OTHER), lambda rt: rt.fulfill(status=404, content_type='application/json', body='{"error":"Character not found"}'))
    pg = setup(ctx)
    M.ZKB_CALLS.clear()
    analyze(pg, M.PILOTS[OTHER][0]); settled(pg); pg.wait_for_timeout(2500)
    r4 = pg.evaluate(BOX)
    asked = [c[0] for c in M.ZKB_CALLS if '/stats/characterID/' in c[0]]
    check(not asked, f"ESI's character record failing: zKillboard's stats aren't asked (nowhere to show them) {asked}")
    check(r4['msg'] and r4['msg'][0][0] == "Couldn't load their corporation (PILOT-08)" and 'status 404' in r4['msg'][0][1] and not r4['orgs'],
          f"ESI's character record failing: PILOT-08, the cause on hover {r4['msg']}")
    ctx.close()
    # narrower: under the pilot line
    for W in (1100, 390):
        ctx = new_ctx(W); pg = setup(ctx)
        analyze(pg, NAME); settled(pg)
        L = pg.evaluate("""() => { const r = (s) => document.querySelector(s).getBoundingClientRect();
          return [r('#pilotAff').top >= r('#tabPilot .pilot-head').bottom, r('#fitResults').top >= r('#pilotAff').bottom, document.documentElement.scrollWidth,
            [...document.querySelectorAll('#pilotAff *')].filter(e => { const b = e.getBoundingClientRect(); return e.checkVisibility() && b.width && (b.right > innerWidth + 1 || b.left < -1); }).map(e => e.className || e.tagName).slice(0, 5)]; }""")
        check(L[0] and L[1] and L[2] <= W and not L[3], f'{W} px: under the pilot line, above the loss tabs, nothing off the page {L}')
        ctx.close()
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
