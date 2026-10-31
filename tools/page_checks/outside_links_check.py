"""Links out of the site, the zK icon, the Pilot Dossier's fleet icon, system and victim colours (v2026.10.31.3).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/outside_links_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner: his option D ("use the empty space under the expand/collaps button to do your little fleet icon/button"); "a little
icon with "zK" inside of it ... to link out to zkillboard instead of having to type it all out ... maintain the color scheme of the
light blue leaving the site"; "any links that leave the site, we should probably get the user to confirm" (with "Don't ask again"
per site); the column "Fleet size" with the count alone ("some killmails could have hundreds of pilots"); "system names should use
the coloring rules we came up with"; "victims should also be assessed for standing ... and names should be colored". The real page
with ESI and zKillboard answered from sa_mocks.py; zKillboard's own pages answered here (nothing reaches zkillboard.com):
  * the page's source: every link to zKillboard is zkLinkHtml (no "zKillboard ↗" text, one target="_blank");
  * the dossier's kills: "Fleet size" with the count alone; a fleet icon on every kill, the solo one too, under the expand
    button's column and left of the row; it opens the Fleet tab; a zK icon in the last column;
  * system names in their security colour (1DQ1-A null, Jita high), in the dossier and the Fleet tab's line;
  * a zK icon asks first: Cancel opens nothing and gives the focus back; Escape closes; Open opens one new tab at that address;
    "Don't ask again" remembers zKillboard, the next click opens at once; under Intel's gear "Ask again" brings the question back;
  * the victim's name in its standing's colour, hostile when its corporation is set hostile under Standings;
  * a kill in the past 4 hours: its time in amber, the older ones not;
  * the Fleet tab's zK icon centred with its buttons; 390 px: the fleet icon 40 px at the start of the kill, zK 32 px, nothing
    off the page; no page errors.
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
ORLA = M.PILOTS[M.ORLA][0]
SIDE = {'pilot': {'id': 90000001, 'name': 'Test Pilot'}, 'corp': {'id': M.CORP, 'name': 'Example Corp'}, 'alliance': {'id': M.ALLIANCE, 'name': 'Example Alliance'},
        'friendly': [{'id': M.THIRD, 'name': 'Random Third Party', 'kind': 'alliance'}], 'hostile': [{'id': M.CRTS, 'name': 'Crimson Tide Syndicate', 'kind': 'alliance'}], 'rows': 15}

src = open(HTML, encoding='utf-8').read()
check('zKillboard ↗' not in src and src.count('target="_blank"') == 1 and 'function zkLinkHtml' in src,
      f'the source: no "zKillboard ↗" text, one target="_blank" (zkLinkHtml) ({src.count("zKillboard ↗")}, {src.count(chr(116)+"arget=" + chr(34) + "_blank" + chr(34))})')

with sync_playwright() as p:
    b = p.chromium.launch()
    errs, outside = [], []
    def new_ctx(w):
        ctx = b.new_context(viewport={'width': w, 'height': 1000}); ctx.on('page', lambda pg: pg.on('pageerror', lambda e: errs.append(str(e)))); M.route(ctx)
        ctx.route('https://zkillboard.com/kill/**', lambda r: (outside.append(r.request.url), r.fulfill(status=200, content_type='text/html', body='<p>stand-in</p>')))
        ctx.route('https://zkillboard.com/character/**', lambda r: (outside.append(r.request.url), r.fulfill(status=200, content_type='text/html', body='<p>stand-in</p>')))
        return ctx
    def dossier(pg, side=SIDE):
        pg.goto('file://' + HTML); pg.evaluate("(s) => { localStorage.setItem('dscanSide', JSON.stringify(s)); }", side); pg.reload(); pg.wait_for_timeout(400)
        pg.click('#tabBtnPilot'); pg.fill('#pilotName', ORLA); pg.fill('#manualShip', ''); pg.click('#fitBtn'); pg.wait_for_timeout(300)
        pg.wait_for_function("() => !document.querySelector('#fitBtn').disabled && document.querySelector('#pilotBusy').hidden", timeout=120000); pg.wait_for_timeout(500)
        pg.click(f'#pilotDossier [data-pd-exp="{M.byname["Curse"]}"]'); pg.wait_for_timeout(1500)
    ctx = new_ctx(1440); pg = ctx.new_page(); dossier(pg)
    D = pg.evaluate("""(hid) => { const k = document.querySelector(`#pdk-${hid}`), exp = document.querySelector(`[data-pd-exp="${hid}"]`).getBoundingClientRect();
      const head = [...k.querySelector('.pdk-h').children].map(x => x.textContent);
      return {head, exp: exp.left + exp.width / 2, rows: [...k.querySelectorAll('.pdk[data-pdk]')].map(r => { const f = r.querySelector('button.pdk-fb[data-pd-fleet]'), fb = f && f.getBoundingClientRect(), t = r.querySelector('.pdk-t').getBoundingClientRect();
        return {id: r.dataset.pdk, g: r.querySelector('.pdk-g').childNodes[1].textContent, fx: fb ? fb.left + fb.width / 2 : null, fr: fb ? fb.right : null, tl: t.left, zk: (r.querySelector('.pdk-l a.zk-ic') || {}).textContent || '',
          href: (r.querySelector('.pdk-l a.zk-ic') || {href: ''}).getAttribute('href'), sys: (r.querySelector('.pdk-s .it-sn') || {className: ''}).className, vic: (r.querySelector('.pdk-v .std-n') || {className: ''}).className}; }),
        usual: [...document.querySelectorAll('#pilotDossier .sec-sys')].map(e => [e.textContent, e.className])}; }""", M.byname['Curse'])
    R = D['rows']
    check(D['head'][2] == 'Fleet size' and all(r['g'] in ('1', '8', '21') for r in R) and len(R) == 3, f'"Fleet size", the count alone {D["head"][2]} {[r["g"] for r in R]}')
    check(all(r['fx'] is not None and abs(r['fx'] - D['exp']) < 4 and r['fr'] < r['tl'] for r in R),
          f'a fleet icon on every kill, the solo one too, under the expand button and left of the row ({D["exp"]:.0f}) {[(r["id"], r["fx"] and round(r["fx"])) for r in R]}')
    check(all(r['zk'] == 'zK' and r['href'] == f"https://zkillboard.com/kill/{r['id']}/" for r in R), f'a zK icon in the last column, to that kill {[r["href"] for r in R]}')
    check(all('ns s0' in r['sys'] for r in R) and any(t == 'Jita' and 'hs s9' in c for t, c in D['usual']), f'system names in their security colour: 1DQ1-A null, Jita high {R[0]["sys"]} {D["usual"]}')
    check(all('std-n n' in r['vic'] for r in R), f'the victim: a neutral name, its icon before it {[r["vic"] for r in R]}')
    # a kill in the past 4 hours: its time in amber (the owner: "timestamps in the WHEN column within the past 4 hours should be in amber")
    A = pg.evaluate("""(hid) => { const ts = pdKillList(pd.d.hulls.find(h => h.id === hid)).map(k => k.t), newest = Math.max(...ts), real = Date.now;
      Date.now = () => newest + 3 * 3600 * 1000; document.querySelector(`[data-pd-exp="${hid}"]`).click(); document.querySelector(`[data-pd-exp="${hid}"]`).click(); Date.now = real;
      const amber = getComputedStyle(document.documentElement).getPropertyValue('--amber').trim();
      return [...document.querySelectorAll(`#pdk-${hid} .pdk[data-pdk]`)].map(r => [r.classList.contains('recent'), getComputedStyle(r.querySelector('.pdk-t b')).color, Number(pdKillList(pd.d.hulls.find(h => h.id === hid)).find(k => String(k.id) === r.dataset.pdk).t) === newest]).concat([[amber]]); }""", M.byname['Curse'])
    amb = A.pop()[0]
    check(A and all(r[0] == r[2] for r in A) and any(r[0] for r in A) and not all(r[0] for r in A) and len({r[1] for r in A if r[0]}) == 1 and {r[1] for r in A if r[0]} != {r[1] for r in A if not r[0]},
          f'a kill in the past 4 hours: its time in amber ({amb}), the older ones not {A}')
    # leaving the site
    z = f'#pdk-{M.byname["Curse"]} .pdk[data-pdk="{R[0]["id"]}"] a.zk-ic'
    n0 = len(ctx.pages); pg.click(z); pg.wait_for_timeout(300)
    B = pg.evaluate("() => { const b = document.getElementById('leaveBox'); return b ? [b.querySelector('b').textContent, b.querySelector('.leave-url').textContent, document.activeElement.dataset.leave] : null; }")
    check(B and B[0] == 'Open zKillboard?' and B[1] == f'zkillboard.com/kill/{R[0]["id"]}/' and B[2] == 'go' and len(ctx.pages) == n0 and not outside,
          f'a zK icon asks first, the address shown, Open focused, nothing opened {B} {len(ctx.pages) - n0} {outside}')
    pg.click('#leaveBox [data-leave="no"]'); pg.wait_for_timeout(200)
    c1 = pg.evaluate("(z) => [!document.getElementById('leaveBox'), document.activeElement === document.querySelector(z)]", z)
    pg.click(z); pg.wait_for_timeout(200); pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    c2 = pg.evaluate("() => !document.getElementById('leaveBox')")
    check(c1 == [True, True] and c2 and len(ctx.pages) == n0 and not outside, f'Cancel opens nothing and gives the focus back; Escape closes {c1} {c2}')
    pg.click(z); pg.wait_for_timeout(200)
    with ctx.expect_page() as np: pg.click('#leaveBox [data-leave="go"]')
    newp = np.value; newp.wait_for_load_state(); u1 = newp.url; newp.close()
    check(u1 == f'https://zkillboard.com/kill/{R[0]["id"]}/' and len(ctx.pages) == n0 and pg.evaluate("() => !document.getElementById('leaveBox')"), f'Open opens one new tab at that address {u1}')
    pg.click(z); pg.wait_for_timeout(200); pg.check('#leaveBox [data-leave="skip"]')
    with ctx.expect_page() as np: pg.click('#leaveBox [data-leave="go"]')
    np.value.close()
    with ctx.expect_page() as np: pg.click(z)
    np.value.close()
    k = pg.evaluate("() => [localStorage.getItem('dscanLeaveOk'), !document.getElementById('leaveBox')]")
    check(k == ['["zkillboard.com"]', True], f'"Don\'t ask again": zKillboard remembered, the next click opens at once {k}')
    pg.click('#tabBtnIntel'); pg.wait_for_timeout(300); pg.click('#intelPanel [data-it-act="gear"]'); pg.wait_for_timeout(300)
    g = pg.evaluate("() => { const b = document.querySelector('#intelPanel [data-it-act=\"leaveask\"]'); return b ? b.parentElement.textContent : null; }")
    pg.click('#intelPanel [data-it-act="leaveask"]'); pg.wait_for_timeout(300)
    g2 = pg.evaluate("() => [localStorage.getItem('dscanLeaveOk'), !!document.querySelector('#intelPanel [data-it-act=\"leaveask\"]')]")
    pg.click('#tabBtnPilot'); pg.wait_for_timeout(300); pg.click(z); pg.wait_for_timeout(200)
    g3 = pg.evaluate("() => !!document.getElementById('leaveBox')"); pg.keyboard.press('Escape')
    check(g and 'zKillboard opens without asking' in g and g2 == ['[]', False] and g3, f'under Intel\'s gear, "Ask again" brings the question back {g!r} {g2} {g3}')
    # the Fleet tab, from the fleet icon
    pg.click(f'#pdk-{M.byname["Curse"]} button.pdk-fb[data-pd-fleet="{M.FLEET_KILL}"]'); pg.wait_for_timeout(300)
    pg.wait_for_function("() => { const c = document.querySelector('#fleetPanel .fk-sum .pr-head .ctx'); return c && /^(\\d+) of \\1 looked up/.test(c.textContent); }", timeout=120000)
    F = pg.evaluate("""() => { const a = document.querySelector('#fleetPanel .fk-acts a.zk-ic').getBoundingClientRect(), c = document.querySelector('#fleetPanel [data-fk-close]').getBoundingClientRect();
      return [document.querySelector('.tab-btn.active').textContent, fk.killId, (document.querySelector('#fleetPanel .fk-sub .it-sn') || {className: ''}).className, Math.abs((a.top + a.bottom) / 2 - (c.top + c.bottom) / 2), fk.victim.corp,
        (document.querySelector('#fleetPanel .fk-sub .fk-vbtn .std-n') || {className: ''}).className]; }""")
    check(F[0] == 'Fleet' and F[1] == M.FLEET_KILL and 'ns s0' in F[2] and F[3] < 2, f'the fleet icon opens the Fleet tab; its system in colour; its zK icon centred with the buttons {F[:4]}')
    ctx.close()
    # the victim's corporation set hostile under Standings
    side2 = dict(SIDE, hostile=SIDE['hostile'] + [{'id': F[4], 'name': 'Victim Corp', 'kind': 'corporation'}])
    ctx = new_ctx(1440); pg = ctx.new_page(); dossier(pg, side2)
    vh = pg.evaluate("(hid) => [...document.querySelectorAll(`#pdk-${hid} .pdk[data-pdk] .pdk-v .std-n`)].map(e => [e.className, getComputedStyle(e).color, e.closest('.std-nm').querySelector('svg.it-st').classList[1]])", M.byname['Curse'])
    hostile = pg.evaluate("() => getComputedStyle(document.documentElement).getPropertyValue('--danger').trim()")
    check(vh and all(c == 'std-n h' and k == 'bad' for c, _, k in vh), f'the victim hostile when its corporation is: its name in the hostile colour, − before it {vh} ({hostile})')
    ctx.close()
    # phone
    ctx = new_ctx(390); pg = ctx.new_page(); dossier(pg)
    L = pg.evaluate("""(hid) => { const r = document.querySelector(`#pdk-${hid} .pdk[data-pdk]`), f = r.querySelector('button.pdk-fb').getBoundingClientRect(), v = r.querySelector('.pdk-v').getBoundingClientRect(), z = r.querySelector('a.zk-ic').getBoundingClientRect();
      return [Math.round(f.height), f.right <= v.left + 1, Math.abs(f.top - v.top) < 6, Math.round(z.height), document.documentElement.scrollWidth]; }""", M.byname['Curse'])
    check(L[0] >= 40 and L[1] and L[2] and L[3] >= 32 and L[4] <= 390, f'390 px: the fleet icon 40 px at the start of the kill, zK 32 px, nothing off the page {L}')
    ctx.close()
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
