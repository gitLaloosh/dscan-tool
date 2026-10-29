"""System Analyzer pilot rows: the possible ship for a gang size (v2026.10.14.92; roadmap/pilot-dossier-plan.md D4-D6).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/sa_size_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner on the dossier mockup: "for #4 that's fine but give users the option to switch between group sizes"; then "One
switch, Auto default", "Their alliance". The real page with ESI and zKillboard answered from sa_mocks.py. Vesna Dossier
(sa_mocks DOSSIER_SPEC: 45 kills in all three sizes, each with an NPC attacker that mustn't count; losses Curse, Vedmak)
is pasted in Local, alone or with another pilot of her alliance; the expected rows are worked out here from the mock's
killmails (players per kill, times), not from the page. Checks:
  * the switch on the Pilots card: Auto Solo Small gang Fleet All, Auto by default;
  * Auto, alone from her alliance: solo, so her solo hull (Loki, 4 of her 6 solo kills, the time of the newest), its
    tag, "fit unknown" (no loss of hers in it), the whole sentence on hover saying why solo;
  * Auto, 2 of her alliance in Local: small gang (Sabre, 12 of 20 small-gang kills), the hover says 2 of Random Third Party;
    one of her alliance in another corporation counts too, a pilot of another alliance doesn't;
  * Fleet: Purifier 11 of 19; All: Sabre "14 kills · 0 losses", no tag; switching asks zKillboard nothing; the choice is
    kept in the browser (dscanSaSize) and comes back on reload;
  * a pilot with no kill in the chosen size (the Vedmak pilot of pilot_rows_check, one solo kill) under Fleet: v.84's
    rule (the newest ship seen), no tag, the hover says why; under Solo: tagged, "1 of 1 solo kills";
  * a ship of hers on the D-Scan (a Vedmak, lost 3 d ago) still comes first, whatever the size, with that loss's numbers
    (the golden Vedmak pin);
  * a row opens the Pilot Analyzer with the dossier on the same size and that hull selected;
  * 390 px: the switch and the tag on the page, nothing off it; no page errors.
v2026.10.14.91 fails (no switch).
"""
import sys, os, math, re, json, time
from datetime import datetime, timezone
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
        'friendly': [], 'hostile': [], 'rows': 15}
VESNA, RANDO, VED, TESSA = M.PILOTS[M.DOSSIER_PILOT][0], M.PILOTS[M.THIRD_PILOT][0], M.PILOTS[M.SMALL_RED[1]][0], M.PILOTS[M.ANNEX_PILOT][0]
NAME = {v: k for k, v in M.byname.items()}

# ---- expected, from the mock's killmails ----
def ts(iso): return datetime.strptime(iso, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc).timestamp() * 1000
def jround(x): return math.floor(x + 0.5)   # JavaScript's Math.round: a tie goes up (Python's round goes to even; LESSON #34)
def ago(t):   # the page's saAgoShort
    m = max(0, jround((time.time() * 1000 - t) / 60000))
    if m < 60: return f'{m} min ago'
    h = jround(m / 60)
    if h < 48: return f'{h} h ago'
    d = jround(h / 24)
    return f'{d} d ago' if d < 60 else f'{jround(d / 30)} mo ago'
size = lambda n: 'solo' if n <= 1 else 'small' if n <= 10 else 'fleet'
def kills_of(cid):
    out = []
    for k in M.HIST[cid]['kills']:
        km = M.KM[k]; players = [a for a in km['attackers'] if a.get('character_id')]
        me = next(a for a in players if a['character_id'] == cid)
        out.append((NAME[me['ship_type_id']], size(len(players)), ts(km['killmail_time'])))
    return out
def want(cid, sz):
    ks = [k for k in kills_of(cid) if sz == 'all' or k[1] == sz]
    by = {}
    for h, s, t in ks: by.setdefault(h, []).append(t)
    if sz == 'all':
        for k in M.HIST[cid]['losses']:
            h = NAME[M.KM[k]['victim']['ship_type_id']]
            if h != 'Capsule': by.setdefault(h, []).append(ts(M.KM[k]['killmail_time']))
    hull = sorted(by, key=lambda h: (-len(by[h]), -max(by[h])))[0]
    return hull, len(by[hull]), len(ks), max(by[hull])

ROWS = """() => Object.fromEntries([...document.querySelectorAll('#saPilots button.pr-row')].map(b => [b.querySelector('.pr-pilot .nm').textContent, {
  hull: (b.querySelector('.pr-hull .nm') || {}).firstChild ? b.querySelector('.pr-hull .nm').firstChild.textContent : null,
  tag: (b.querySelector('.pr-size') || {}).textContent || '', tagCls: b.querySelector('.pr-size') ? b.querySelector('.pr-size').className : '',
  basis: (b.querySelector('.pr-hull .ctx') || {}).textContent || '', title: (b.querySelector('.pr-hull .ctx') || {}).title || '',
  dps: (b.querySelector('.pr-dps .pr-num') || {}).textContent || '', fu: !!b.querySelector('.pr-fu'), msg: (b.querySelector('.pr-msg') || {}).textContent || ''}]))"""
SW = "() => [...document.querySelectorAll('#saPilots [data-sa-size]')].map(b => [b.dataset.saSize, b.textContent, b.getAttribute('aria-pressed')])"
def setup(ctx):
    pg = ctx.new_page(); pg.goto('file://' + HTML)
    pg.evaluate("(s) => { localStorage.setItem('dscanSide', JSON.stringify(s)); localStorage.removeItem('dscanSaSize'); }", SIDE); pg.reload(); pg.wait_for_timeout(300)
    return pg
def analyze(pg, names, scan=''):
    pg.click('#tabBtnDscan'); pg.fill('#localInput', '\n'.join(names)); pg.fill('#dscanInput', scan); pg.click('#analyzeBtn'); pg.wait_for_timeout(300)
    pg.wait_for_function("() => document.querySelector('#saBusy').hidden && !document.querySelector('#analyzeBtn').disabled", timeout=60000)
    n = len(names)
    pg.wait_for_function(f"() => {{ const c = document.querySelector('#saPilots .pr-head .ctx'); return c && c.textContent === '{n} of {n} looked up'; }}", timeout=180000); pg.wait_for_timeout(400)
def switch(pg, v):
    pg.click(f'#saPilots [data-sa-size="{v}"]')
    pg.wait_for_function(f"() => document.querySelector('#saPilots [data-sa-size=\"{v}\"]').getAttribute('aria-pressed') === 'true'", timeout=10000); pg.wait_for_timeout(600)

with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []
    def new_ctx(w):
        ctx = b.new_context(viewport={'width': w, 'height': 1000}); ctx.on('page', lambda pg: pg.on('pageerror', lambda e: errs.append(str(e)))); M.route(ctx); return ctx
    ctx = new_ctx(1440); pg = setup(ctx)
    # Auto, alone from her alliance: solo
    analyze(pg, [VESNA])
    sw = pg.evaluate(SW)
    check([x[:2] for x in sw] == [['auto', 'Auto'], ['solo', 'Solo'], ['small', 'Small gang'], ['fleet', 'Fleet'], ['all', 'All']] and [x[2] for x in sw] == ['true', 'false', 'false', 'false', 'false'],
          f'the switch on the Pilots card, Auto by default {sw}')
    h, n, of, t = want(M.DOSSIER_PILOT, 'solo')
    r = pg.evaluate(ROWS)[VESNA]
    check(r['hull'] == h == 'Loki' and r['tag'] == 'solo' and 'solo' in r['tagCls'] and r['basis'] == f'{n} of {of} solo kills · {ago(t)}' and r['fu'],
          f"Auto, the only one of her alliance in Local: her solo hull, tagged, fit unknown ({r['hull']}, {r['tag']!r}, {r['basis']!r}; want {h} {n} of {of} {ago(t)})")
    check(r['title'].endswith('Solo: the only one of Random Third Party in Local.') and f'{n} of their {of} solo kills among their newest 45' in r['title'],
          f"the whole sentence on hover, with why solo ({r['title']!r})")
    # Auto, 2 of her alliance: small gang
    M.ZKB_CALLS.clear()
    analyze(pg, [VESNA, RANDO])
    h, n, of, t = want(M.DOSSIER_PILOT, 'small')
    r = pg.evaluate(ROWS)[VESNA]
    check(r['hull'] == h == 'Sabre' and r['tag'] == 'small gang' and r['basis'] == f'{n} of {of} small-gang kills · {ago(t)}' and r['title'].endswith('Small gang: 2 of Random Third Party in Local.'),
          f"Auto, 2 of her alliance in Local: small gang ({r['hull']}, {r['basis']!r}, {r['title'][-60:]!r}; want {h} {n} of {of})")
    asked = len(M.ZKB_CALLS)
    # her group is her alliance (not her corporation, not everyone in Local)
    analyze(pg, [VESNA, TESSA])
    r2 = pg.evaluate(ROWS)[VESNA]
    analyze(pg, [VESNA, VED])
    r3 = pg.evaluate(ROWS)[VESNA]
    check(r2['tag'] == 'small gang' and r2['title'].endswith('Small gang: 2 of Random Third Party in Local.') and r3['tag'] == 'solo' and r3['hull'] == 'Loki',
          f"her group is her alliance: one of another corporation of it counts ({r2['tag']!r}), a pilot of another alliance doesn't ({r3['tag']!r} {r3['hull']})")
    analyze(pg, [VESNA, RANDO])
    asked = len(M.ZKB_CALLS)
    # Fleet, then All: no request
    switch(pg, 'fleet')
    h, n, of, t = want(M.DOSSIER_PILOT, 'fleet')
    r = pg.evaluate(ROWS)[VESNA]
    check(r['hull'] == h == 'Purifier' and r['tag'] == 'fleet' and r['basis'] == f'{n} of {of} fleet kills · {ago(t)}' and r['fu'] and 'in Local' not in r['title'],
          f"Fleet: her fleet hull ({r['hull']}, {r['basis']!r}; want {h} {n} of {of}), no Local reason when chosen by hand")
    switch(pg, 'all')
    h, n, of, t = want(M.DOSSIER_PILOT, 'all')
    r = pg.evaluate(ROWS)[VESNA]
    check(r['hull'] == h == 'Sabre' and r['tag'] == '' and r['basis'] == f'{n} kills · 0 losses · {ago(t)}', f"All: kills and losses together, no tag ({r['hull']}, {r['basis']!r}; want {h} {n})")
    check(len(M.ZKB_CALLS) == asked, f'switching asks zKillboard nothing ({len(M.ZKB_CALLS) - asked} new requests)')
    pg.reload(); pg.wait_for_timeout(300)
    analyze(pg, [VESNA, RANDO])
    kept = pg.evaluate(SW)
    check([x[2] for x in kept] == ['false', 'false', 'false', 'false', 'true'] and pg.evaluate(ROWS)[VESNA]['hull'] == 'Sabre', f'the choice is kept in this browser {kept}')
    # a pilot with no kill in that size: v.84's rule
    analyze(pg, [VESNA, RANDO, VED])
    switch(pg, 'fleet')
    r = pg.evaluate(ROWS)[VED]
    check(r['hull'] == 'Vedmak' and r['tag'] == '' and r['basis'] == 'on a kill 2 h ago' and r['title'].startswith('on a kill 2 h ago. No fleet kills among their newest 1, so the newest ship they were seen in.'),
          f"no kill in that size: the newest ship seen, no tag, said why on hover ({r['basis']!r}, {r['title']!r})")
    switch(pg, 'solo')
    r = pg.evaluate(ROWS)[VED]
    check(r['tag'] == 'solo' and r['basis'] == '1 of 1 solo kills · 2 h ago' and r['dps'] == f"{round(M.PIN['Vedmak']['dpsFixed']):,}",
          f"Solo: tagged, its fit from their Vedmak loss ({r['basis']!r}, DPS {r['dps']})")
    # a ship of hers on the D-Scan comes first
    switch(pg, 'fleet')
    analyze(pg, [VESNA], f"{M.byname['Vedmak']}\tSomeone's Vedmak\tVedmak\t1.2 AU")
    r = pg.evaluate(ROWS)[VESNA]
    check(r['hull'] == 'Vedmak' and r['tag'] == '' and r['basis'] == 'on scan; lost one 3 d ago' and r['dps'] == f"{round(M.PIN['Vedmak']['dpsFixed']):,}",
          f"a ship of hers on the D-Scan comes first, with that loss's numbers ({r['hull']}, {r['basis']!r}, {r['dps']})")
    # a row opens the dossier on the same size, that hull selected
    analyze(pg, [VESNA])   # Fleet still chosen: Purifier
    pg.click(f'#saPilots button.pr-row[data-pr-pilot="{VESNA}"]'); pg.wait_for_timeout(300)
    pg.wait_for_function("() => !document.querySelector('#fitBtn').disabled && document.querySelector('#pilotBusy').hidden && document.querySelector('#pilotDossier button.pd-row')", timeout=120000); pg.wait_for_timeout(500)
    o = pg.evaluate("() => [[...document.querySelectorAll('#pilotDossier [data-pd-mode]')].filter(b => b.getAttribute('aria-pressed') === 'true').map(b => b.dataset.pdMode), [...document.querySelectorAll('#pilotDossier button.pd-row[aria-pressed=true]')].map(b => b.dataset.pdHull), document.querySelector('#fitStatus').textContent]")
    check(o[0] == ['fleet'] and o[1] == [str(M.byname['Purifier'])], f'a row opens the Pilot Analyzer, its dossier on the same size, that hull selected {o}')
    ctx.close()
    # phone
    ctx = new_ctx(390); pg = setup(ctx)
    analyze(pg, [VESNA, RANDO])
    L = pg.evaluate("""() => { const s = document.querySelector('#saPilots .pr-sizes').getBoundingClientRect(), t = document.querySelector('#saPilots .pr-size').getBoundingClientRect();
      return [Math.round(s.left), Math.round(s.right), Math.round(t.right), document.documentElement.scrollWidth,
        [...document.querySelectorAll('#saPilots .pr-sizes button')].map(b => b.getBoundingClientRect().height)]; }""")
    check(L[0] >= 0 and L[1] <= 390 and L[2] <= 390 and L[3] <= 390 and all(hh >= 40 for hh in L[4]), f'390 px: the switch and the tag on the page, buttons 40 px tall {L}')
    ctx.close()
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
