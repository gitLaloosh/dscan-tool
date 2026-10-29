"""Fleet from a kill: the Fleet tab (v2026.10.14.94; roadmap/fleet-from-kill-plan.md).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/fleet_kill_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner: "choose a row from the kills list (not a loss) in the pilot dossier ... use that killmail to build out the 'fleet'
from that kill using each pilot/participant's specified ship and weapon"; the Pilot Analyzer's fit rule; NPCs, capsules and
pilots with no ship left out; "its own tab ... only visible when the user has chosen to assess a fleet"; shareable; laid
out like the System Analyzer; mockup Claude outputs/fleet_from_kill_mockup.html, all four answers as recommended. The real
page with ESI and zKillboard answered from sa_mocks.py (Orla Fleetwood's kills: FLEET_KILL, BIG_KILL, SOLO_KILL). Checks:
  * Fleet ▸ on her kills with 2+ pilots, none on the solo kill; no Fleet tab before;
  * Fleet ▸: the Fleet tab shown and open; the kill (Thanatos, Carrier, 1DQ1-A, "8 pilots on the kill, 6 in ships": the
    NPC, the capsule and the pilot with no ship left out);
  * each pilot's ship and the weapon the killmail credits them with; each fit by the Pilot Analyzer's rule: their own loss
    (Curse, Vedmak: the golden pins' DPS), their alliance's common fit when they have none (Loki 801, "2 of 2"), else fit
    unknown; the weapon check on the Vedmak pilot credited with a launcher his fit doesn't carry;
  * one zKillboard request per pilot for their losses in that hull (none again for one the Pilot Analyzer already asked),
    plus one per group fallback;
  * sorted once in: the dossier's pilot first, then DPS, fit unknown last; the summary: raw DPS added up from the rows, the
    coverage line, logistics none, combined EHP;
  * Copy share link: the kill and each pilot's loss; opening it in a fresh page: the same fleet with no zKillboard request;
    a cut-short link: FLEET-01; Close: the tab hidden, the Pilot Analyzer back, the link gone from the address;
  * a row opens that pilot in the Pilot Analyzer, the dossier on that hull (the Loki: his alliance's fit);
  * a 20-pilot kill: 15 looked up, "Load 6 more pilots" (21 with her), then all; another kill replaces the fleet;
  * 390 px: nothing off the page, Close and × 40 px; no page errors.
v2026.10.14.93 fails (no Fleet ▸).
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
ORLA = M.PILOTS[M.ORLA][0]
PN = lambda i: M.PILOTS[i][0]
pin = lambda h: round(M.PIN[h]['dpsFixed'])
ROWS = """() => [...document.querySelectorAll('#fleetPanel .fk-card button.pr-row')].map(b => ({pilot: b.querySelector('.pr-pilot .nm').firstChild.textContent,
  hull: b.querySelector('.pr-hull .nm').firstChild.textContent, w: (b.querySelector('.fk-w') || {}).textContent || '', src: (b.querySelector('.fk-src') || {}).textContent || '',
  mis: (b.querySelector('.fk-mis') || {}).textContent || '', dps: (b.querySelector('.pr-dps .pr-num') || {}).textContent || '', fu: !!b.querySelector('.pr-dps .pr-fu'), type: b.dataset.fkType}))"""
def idle(pg):
    pg.wait_for_function("() => !document.querySelector('#fitBtn').disabled && document.querySelector('#pilotBusy').hidden", timeout=120000); pg.wait_for_timeout(400)
def analyze(pg, name):
    pg.click('#tabBtnPilot'); pg.fill('#pilotName', name); pg.fill('#manualShip', ''); pg.click('#fitBtn'); pg.wait_for_timeout(300); idle(pg)
def fleet_done(pg, n, timeout=120000):
    pg.wait_for_function(f"() => {{ const c = document.querySelector('#fleetPanel .fk-sum .pr-head .ctx'); return c && c.textContent.startsWith('{n} of {n} looked up'); }}", timeout=timeout); pg.wait_for_timeout(400)

with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []
    def new_ctx(w):
        ctx = b.new_context(viewport={'width': w, 'height': 1000}); ctx.on('page', lambda pg: pg.on('pageerror', lambda e: errs.append(str(e)))); M.route(ctx); return ctx
    ctx = new_ctx(1440); ctx.grant_permissions(['clipboard-read', 'clipboard-write'])
    pg = ctx.new_page(); pg.goto('file://' + HTML)
    check(pg.evaluate("() => document.querySelector('#fleetTabWrap').hidden"), 'no Fleet tab before a fleet is chosen')
    analyze(pg, ORLA)
    pg.wait_for_function("() => { const b = document.querySelector('#pilotAff'); return b.hidden || !b.querySelector('.busy-spin'); }", timeout=60000)
    pg.click(f'#pilotDossier [data-pd-exp="{M.byname["Curse"]}"]'); pg.wait_for_timeout(500)
    btn = pg.evaluate("() => Object.fromEntries([...document.querySelectorAll('.pdk[data-pdk]')].map(k => [k.dataset.pdk, !!k.querySelector('[data-pd-fleet]')]))")
    check(btn == {str(M.FLEET_KILL): True, str(M.BIG_KILL): True, str(M.SOLO_KILL): False}, f'Fleet ▸ on her kills with 2+ pilots, none on the solo kill {btn}')
    M.ZKB_CALLS.clear()
    pg.click(f'[data-pd-fleet="{M.FLEET_KILL}"]'); pg.wait_for_timeout(300); fleet_done(pg, 6)
    tab = pg.evaluate("() => [!document.querySelector('#fleetTabWrap').hidden, document.querySelector('#tabBtnFleet').textContent, document.querySelector('#tabBtnFleet').classList.contains('active'), getComputedStyle(document.querySelector('#tabFleet')).display, getComputedStyle(document.querySelector('#tabPilot')).display]")
    check(tab == [True, 'Fleet', True, 'block', 'none'], f'Fleet ▸: the Fleet tab shown and open {tab}')
    sub = pg.inner_text('#fleetPanel .fk-sub')
    check(sub.startswith(f"Chosen from {ORLA}'s Pilot Dossier · killed a Thanatos (Carrier) · ") and sub.endswith('· 1DQ1-A · 8 pilots on the kill, 6 in ships'),
          f'the kill, with the NPC, the capsule and the pilot with no ship left out ({sub!r})')
    R = pg.evaluate(ROWS)
    want = [  # the dossier's pilot first, then DPS (ties in the killmail's order), fit unknown last
        (ORLA, 'Curse', 'on the kill: Acolyte II', 'their loss 2 d ago', '', f"{pin('Curse'):,}"),
        (PN(M.THIRD_PILOT), 'Loki', 'on the kill: Heavy Assault Missile Launcher II', "alliance's common fit (2 of 2)", '', f"{pin('Loki'):,}"),
        (PN(M.DOSSIER_PILOT), 'Vedmak', 'on the kill: Heavy Entropic Disintegrator II', 'their loss 3 d ago', '', f"{pin('Vedmak'):,}"),
        (PN(M.SMALL_RED[1]), 'Vedmak', 'on the kill: Heavy Assault Missile Launcher II', 'their loss 5 d ago',
         'this fit carries Heavy Entropic Disintegrator II, not the Heavy Assault Missile Launcher II they used on the kill', f"{pin('Vedmak'):,}"),
        (PN(M.SMALL_RED[0]), 'Curse', 'on the kill: Acolyte II', 'their loss 3 d ago', '', f"{pin('Curse'):,}"),
        (PN(M.ANNEX_PILOT), 'Sabre', 'on the kill: 125mm Gatling AutoCannon II', "fit unknown: no loss of theirs or their alliance's", '', ''),
    ]
    got = [(r['pilot'], r['hull'], r['w'], r['src'], r['mis'], r['dps']) for r in R]
    check(got == want, "the pilots: ship and weapon from the killmail, each fit by the Pilot Analyzer's rule, the weapon check, sorted\n      page " + str(got) + "\n      want " + str(want))
    check(R[-1]['fu'], 'fit unknown: no DPS, last')
    calls = [c[0].split('/api/')[1] for c in M.ZKB_CALLS]
    per = [c for c in calls if re.match(r'losses/characterID/\d+/shipTypeID/\d+/', c)]
    grp = [c for c in calls if c.startswith('losses/allianceID/')]
    # (Orla's Curse losses were already asked by her own analysis: the page keeps them)
    check(len(per) == 5 and len(set(per)) == 5 and not any(f'/{M.ORLA}/' in '/' + c for c in per) and len(grp) == 2 and len(calls) == 7,
          f'one zKillboard request per pilot for their losses in that hull (none again for Orla, asked by her analysis), one per group fallback ({calls})')
    S = pg.evaluate("""() => { const s = document.querySelector('#fleetPanel .fk-sum'); const st = [...s.querySelectorAll('.fl-stat')].map(e => [e.querySelector('.k').textContent, e.querySelector('.v') ? e.querySelector('.v').textContent : e.querySelector('.fk-ewl').innerText.replace(/\\s+/g, ' ')]);
      return {cov: s.querySelector('.fk-cov').textContent, st}; }""")
    total = sum(int(r['dps'].replace(',', '')) for r in R if r['dps'])
    st = dict(S['st'])
    check(S['cov'] == "fits: 4 their own · 1 their alliance's common fit · 1 unknown (no DPS counted) · 1 weapon differs from the kill" and st['Raw DPS, all of it'] == f'{total:,}' and st['Logistics'] == '0' and 'neuts' in st['Tackle and EWAR'],
          f"the summary: raw DPS added up from the rows ({total:,}), the coverage line, tackle by kind, no logistics {S}")
    # share
    pg.click('#fleetPanel [data-fk-share]'); pg.wait_for_timeout(300)
    link = pg.evaluate("() => navigator.clipboard.readText()")
    m = re.match(r'.*#fleet=(\d+)/([0-9a-f]{40})/(.*)$', link)
    ent = dict((e.split('.')[0], e.split('.')[1:]) for e in m.group(3).split('~')) if m else {}
    check(m and int(m.group(1)) == M.FLEET_KILL and ent.get(str(M.ORLA), [''])[0] == 'o' and ent.get(str(M.ORLA))[1] == str(M.ORLA_LOSS) and ent.get(str(M.THIRD_PILOT), [''])[0] == 'a'
          and ent.get(str(M.THIRD_PILOT))[-2:] == ['2', '2'] and ent.get(str(M.ANNEX_PILOT)) == ['u'] and len(ent) == 6,
          f'Copy share link: the kill and each pilot\'s loss ({link[:140]}…)')
    # a row opens the Pilot Analyzer on that hull
    pg.click(f'#fleetPanel button.pr-row[data-fk-pilot="{PN(M.THIRD_PILOT)}"]'); pg.wait_for_timeout(400); idle(pg)
    o = pg.evaluate(f"() => [document.querySelector('#tabBtnPilot').classList.contains('active'), document.querySelector('#pilotName').value, [...document.querySelectorAll('#pilotDossier button.pd-row[aria-pressed=true]')].map(b => b.dataset.pdHull), !!document.querySelector('.pd-note'), !document.querySelector('#fleetTabWrap').hidden]")
    check(o[:4] == [True, PN(M.THIRD_PILOT), [str(M.byname['Loki'])], True] and o[4], f'a row opens that pilot in the Pilot Analyzer, the dossier on the Loki (his alliance\'s fit), the Fleet tab still there {o}')
    ctx.close()
    # the link in a fresh page: the same fleet, no zKillboard request
    ctx = new_ctx(1440); pg = ctx.new_page(); M.ZKB_CALLS.clear()
    pg.goto('file://' + HTML + '#fleet=' + link.split('#fleet=')[1]); pg.wait_for_timeout(300); fleet_done(pg, 6)
    R2 = pg.evaluate(ROWS)
    got2 = [(r['pilot'], r['hull'], r['src'], r['dps']) for r in R2]
    w2 = [(a, b_, d, f) for a, b_, c, d, e, f in want]
    w2[0] = (PN(M.THIRD_PILOT),) + w2[1][1:]; w2[1] = (ORLA,) + want[0][1:2] + want[0][3:4] + want[0][5:]   # no dossier pilot: by DPS
    check(sorted(got2) == sorted(w2) and got2[0][0] == PN(M.THIRD_PILOT) and not M.ZKB_CALLS and pg.inner_text('#fleetPanel .fk-sub').startswith('A shared fleet · killed a Thanatos'),
          f'the share link in a fresh page: the same fleet, by DPS, no zKillboard request ({got2}, {len(M.ZKB_CALLS)} calls)')
    pg.click('#fleetPanel [data-fk-close]'); pg.wait_for_timeout(300)
    c = pg.evaluate("() => [document.querySelector('#fleetTabWrap').hidden, document.querySelector('#tabBtnPilot').classList.contains('active'), location.hash]")
    check(c == [True, True, ''], f'Close: the tab hidden, the Pilot Analyzer back, the link gone from the address {c}')
    pg.goto('file://' + HTML + '#fleet=123/abc'); pg.wait_for_timeout(800)
    e1 = pg.inner_text('#fleetPanel')
    check('(FLEET-01)' in e1 and pg.evaluate("() => !document.querySelector('#fleetTabWrap').hidden"), f'a cut-short link: FLEET-01 ({e1[-120:]!r})')
    ctx.close()
    # a 20-pilot kill: 15 at a time; another kill replaces the fleet
    ctx = new_ctx(1440); pg = ctx.new_page(); pg.goto('file://' + HTML); analyze(pg, ORLA)
    pg.click(f'#pilotDossier [data-pd-exp="{M.byname["Curse"]}"]'); pg.wait_for_timeout(500)
    pg.click(f'[data-pd-fleet="{M.BIG_KILL}"]'); pg.wait_for_timeout(300); fleet_done(pg, 15)
    mo = pg.evaluate("() => [document.querySelector('#fleetPanel [data-fk-more]').textContent, document.querySelectorAll('#fleetPanel .fk-card button.pr-row').length, document.querySelector('#fleetPanel .fk-sum .pr-head .ctx').textContent]")
    check(mo == ['Load 6 more pilots', 21, '15 of 15 looked up, 6 not yet'], f'a 21-pilot fleet: 15 looked up, Load 6 more {mo}')
    pg.click('#fleetPanel [data-fk-more]'); fleet_done(pg, 21)
    check(not pg.query_selector('#fleetPanel [data-fk-more]'), 'Load more: all 21 looked up')
    pg.click('#tabBtnPilot'); pg.click(f'[data-pd-fleet="{M.FLEET_KILL}"]'); pg.wait_for_timeout(300); fleet_done(pg, 6)
    check(pg.evaluate("() => document.querySelectorAll('#fleetPanel .fk-card button.pr-row').length") == 6 and 'Thanatos' in pg.inner_text('#fleetPanel .fk-sub'), 'another kill replaces the fleet (one at a time)')
    ctx.close()
    # phone
    ctx = new_ctx(390); pg = ctx.new_page(); pg.goto('file://' + HTML); analyze(pg, ORLA)
    pg.click(f'#pilotDossier [data-pd-exp="{M.byname["Curse"]}"]'); pg.wait_for_timeout(500)
    fb = pg.evaluate(f"() => document.querySelector('[data-pd-fleet=\"{M.FLEET_KILL}\"]').getBoundingClientRect().height")
    pg.click(f'[data-pd-fleet="{M.FLEET_KILL}"]'); pg.wait_for_timeout(300); fleet_done(pg, 6)
    L = pg.evaluate("""() => [document.documentElement.scrollWidth, document.querySelector('#fleetCloseBtn').getBoundingClientRect().height, document.querySelector('[data-fk-close]').getBoundingClientRect().height,
      [...document.querySelectorAll('#fleetPanel *')].filter(e => { const b = e.getBoundingClientRect(); return e.checkVisibility() && b.width && (b.right > innerWidth + 1 || b.left < -1); }).map(e => e.className || e.tagName).slice(0, 4)]""")
    check(L[0] <= 390 and L[1] >= 40 and L[2] >= 40 and fb >= 40 and not L[3], f'390 px: nothing off the page, ×, Close and Fleet ▸ 40 px tall {L} {fb}')
    ctx.close()
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
