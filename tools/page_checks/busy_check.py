"""Busy indicator while the page waits on zKillboard / ESI (v2026.10.14.39; todo-inbox 2026-10-23).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/busy_check.py [index.html]   -> 'FAILURES: N' (must be 0)

Loads the real page in Chromium. ESI is served from pyfa's SDE (esi_from_sde.py) plus a stand-in pilot; zKillboard
by this script: the pilot's losses are four golden-fit killmails (a Loki, a Curse, a Vedmak, a Leshak), served
from the golden fixtures through ESI's killmail route. zKillboard answers are held back in the page (a fetch
wrapper, window.__delay) so a run takes a known time. Checks:
  * Analyze Pilot: the bar appears (not in the first 250 ms), names what is loading and mirrors the status line's
    step; the button shows a spinner; the bar and spinner go away when the run ends;
  * switching hull (a candidate button) with the page scrolled down: the bar is on screen (sticky), the old
    results are dimmed and not clickable, the clicked button spins, a click on another hull meanwhile is ignored,
    and the hull clicked first is the one shown at the end (no race);
  * the last-kill pivot and Refresh losses use the same bar;
  * a cached hull switch finishes without the bar ever showing;
  * Fit Analyzer: its own bar while a slow fit resolves;
  * reduced motion: the spinner doesn't spin. No page errors.
"""
import sys, os, re, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from esi_from_sde import handle as esi_handle
from pyfa_sde import types, _en
from playwright.sync_api import sync_playwright

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')),
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'index.html')))
GOLDEN = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'regression_suite', 'golden_fits.json')))
LOSSES = [('loki_zkb138935092', 9100001), ('curse_zkb139073592_ewar', 9100002), ('vedmak_zkb139012125_precursor_role_bonus', 9100003),
          ('leshak_zkb139013625_precursor_battleship_role_bonus', 9100004)]
KM = {}
for i, (k, kid) in enumerate(LOSSES):
    km = json.loads(json.dumps(GOLDEN[k]['killmail'])); km['killmail_id'] = kid; km['killmail_time'] = f'2026-10-0{i + 1}T12:00:00Z'
    KM[kid] = km
# the Loki twice, so it ranks first
STUBS = [{'killmail_id': kid, 'zkb': {'hash': f'h{kid}'}} for _, kid in LOSSES] + [{'killmail_id': 9100005, 'zkb': {'hash': 'h9100005'}}]
KM[9100005] = dict(KM[9100001], killmail_id=9100005, killmail_time='2026-10-05T12:00:00Z')
# v2026.10.14.43: a last kill for the header line -- Test Pilot in a Vedmak (and one other attacker) killing the Curse
_ved = KM[9100003]['victim']['ship_type_id']
KM[9100100] = {'killmail_id': 9100100, 'killmail_time': '2026-09-01T18:18:03Z', 'solar_system_id': 30000142,
               'victim': dict(KM[9100002]['victim'], items=[]),
               'attackers': [{'character_id': 90000001, 'ship_type_id': _ved, 'weapon_type_id': _ved, 'final_blow': True, 'damage_done': 900, 'security_status': 0},
                             {'character_id': 90000002, 'ship_type_id': _ved, 'weapon_type_id': _ved, 'final_blow': False, 'damage_done': 100, 'security_status': 0}]}
NAME = {int(k): _en(v.get('typeName') or v.get('name')) for k, v in types.items()}
DELAY = """(() => { const of = window.fetch.bind(window); window.__delay = {zkb: 0, ids: 0};
  window.fetch = (u, o) => { const s = String(u), d = /zkillboard\\.com/.test(s) ? window.__delay.zkb : (/universe\\/ids/.test(s) ? window.__delay.ids : 0);
    return d ? new Promise(r => setTimeout(r, d)).then(() => of(u, o)) : of(u, o); }; })();"""

fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok

def esi(route):
    url, body = route.request.url, route.request.post_data or ''
    if '/universe/ids/' in url and 'Test Pilot' in body:
        return route.fulfill(status=200, content_type='application/json', body=json.dumps({'characters': [{'id': 90000001, 'name': 'Test Pilot'}]}))
    m = re.search(r'/killmails/(\d+)/', url)
    if m: return route.fulfill(status=200, content_type='application/json', body=json.dumps(KM[int(m.group(1))]))
    if '/universe/names/' in url:
        ids = json.loads(body)
        return route.fulfill(status=200, content_type='application/json', body=json.dumps([{'id': i, 'name': NAME.get(i, f'type {i}'), 'category': 'inventory_type'} for i in ids]))
    return esi_handle(route)
def zkb(route):
    cors = {'access-control-allow-origin': '*'}
    url = route.request.url
    if '/kills/' in url: return route.fulfill(status=200, content_type='application/json', headers=cors, body=json.dumps([{'killmail_id': 9100100, 'zkb': {'hash': 'h9100100'}}]))
    m = re.search(r'/shipTypeID/(\d+)/', url)
    stubs = [s for s in STUBS if not m or KM[s['killmail_id']]['victim']['ship_type_id'] == int(m.group(1))]
    return route.fulfill(status=200, content_type='application/json', headers=cors, body=json.dumps(stubs))

def bar_state(pg, bar='#pilotBusy'):
    return pg.evaluate(f"""() => {{ const b = document.querySelector('{bar}'); const r = b.getBoundingClientRect();
      return {{hidden: b.hidden, vis: getComputedStyle(b).visibility, top: r.top, bottom: r.bottom, label: b.querySelector('.busy-label').textContent, detail: b.querySelector('.busy-detail').textContent}}; }}""")
def wait_idle(pg, bar='#pilotBusy'):
    pg.wait_for_function(f"() => document.querySelector('{bar}').hidden", timeout=60000); pg.wait_for_timeout(100)
def shown_hull(pg):
    return pg.evaluate("() => { const a = document.querySelector('#fitResults .subtab-btn.active'); const t = document.querySelector('#fitResults'); return t.innerText.slice(0, 4000); }")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('CHROMIUM', '/opt/pw-browsers/chromium'))
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.add_init_script(DELAY)
    pg.route(re.compile(r'https://esi\.evetech\.net/.*'), esi)
    pg.route(re.compile(r'https://zkillboard\.com/.*'), zkb)
    pg.route(re.compile(r'https://(images\.evetech\.net|fonts\.).*'), lambda r: r.fulfill(status=404, body=''))
    pg.goto('file://' + HTML); pg.evaluate("localStorage.removeItem('dscanMyShip')")
    pg.click('#tabBtnPilot'); pg.fill('#pilotName', 'Test Pilot')
    pg.evaluate('window.__delay.zkb = 1500')
    pg.click('#fitBtn'); pg.wait_for_timeout(100)
    s0 = bar_state(pg)
    check(not s0['hidden'] and s0['vis'] == 'hidden', f'Analyze: bar started but not shown in the first 250 ms ({s0["vis"]})')
    pg.wait_for_timeout(500); s1 = bar_state(pg)
    check(not s1['hidden'] and s1['vis'] == 'visible' and 'Analyzing Test Pilot' in s1['label'], f'Analyze: bar shown, "{s1["label"]}"')
    check(pg.evaluate("document.getElementById('fitBtn').classList.contains('is-loading')"), 'Analyze: the button spins')
    pg.wait_for_function("() => /Loki|Querying|Pulling|sampling/.test(document.querySelector('#pilotBusy .busy-detail').textContent)", timeout=20000)
    check(True, 'Analyze: the bar mirrors the status line step (' + bar_state(pg)['detail'][:60] + ')')
    wait_idle(pg)
    check(not pg.evaluate("document.getElementById('fitBtn').classList.contains('is-loading')") and pg.locator('#fitResults .fit-layout').count() > 0
          and pg.locator('.candidate-btn').count() >= 3, f'Analyze: done, bar gone, results and {pg.locator(".candidate-btn").count()} hull buttons shown')
    # v2026.10.14.43: one header line -- pilot, hull dropdown, last kill (one line, opens on click)
    hb = [pg.locator(x).bounding_box() for x in ('#pilotHeadName', '.hull-pick-btn', '.lk-sum')]
    check(all(hb) and max(b['y'] + b['height'] / 2 for b in hb) - min(b['y'] + b['height'] / 2 for b in hb) < 6 and 'Test Pilot' in pg.inner_text('#pilotHeadName')
          and pg.is_hidden('.hull-menu') and pg.is_hidden('.lk-body'), 'header: pilot, hull dropdown and last kill on one line, both closed')
    if os.environ.get('SHOTS'): pg.locator('#tabPilot section.panel').screenshot(path=os.path.join(os.environ['SHOTS'], 'pilot_header.png'))
    pg.click('.lk-sum'); pg.wait_for_timeout(150)
    check(pg.is_visible('#lkPivotBtn') and pg.is_visible('.lk-body a[href*="zkillboard.com/kill/"]'), 'header: the last kill opens to the full details and the pivot button')
    pg.click('.lk-sum'); pg.click('.hull-pick-btn'); pg.wait_for_timeout(150)
    check(pg.is_visible('.hull-menu') and pg.locator('.hull-menu .candidate-btn').count() >= 3, 'header: the hull dropdown lists their most-lost hulls')
    if os.environ.get('SHOTS'): pg.screenshot(path=os.path.join(os.environ['SHOTS'], 'pilot_hull_menu.png'))
    pg.click('.hull-pick-btn'); pg.wait_for_timeout(100)
    first = pg.locator('.candidate-btn.active').text_content().strip()   # v.43: the hulls sit in the closed dropdown
    check('Loki' in first, f'Loki ranked first ({first.splitlines()[0]})')
    # switch hull with the page scrolled down
    pg.evaluate("window.scrollTo(0, document.querySelector('#fitResults').getBoundingClientRect().top + scrollY + 900)"); pg.wait_for_timeout(100)
    sy = pg.evaluate('scrollY')
    cur = pg.locator('.candidate-btn:has-text("Curse")'); vd = pg.locator('.candidate-btn:has-text("Vedmak")')
    cur.dispatch_event('click'); pg.wait_for_timeout(450)   # a real click would scroll the button into view first
    sy = pg.evaluate('scrollY')
    s2 = bar_state(pg)
    check(s2['vis'] == 'visible' and abs(s2['top'] - 8) < 2 and 'Curse' in s2['label'] and sy > 900, f'switch hull, scrolled {sy} px down: bar pinned at the top of the screen ({s2["top"]:.0f} px), "{s2["label"]}"')
    st = pg.evaluate("() => { const r = getComputedStyle(document.getElementById('fitResults')); return [r.opacity, r.pointerEvents]; }")
    check(float(st[0]) < 0.6 and st[1] == 'none', f'switch hull: old results dimmed and not clickable {st}')
    check(pg.evaluate("document.querySelector('.hull-pick-btn').classList.contains('is-loading') && /Curse/.test(document.querySelector('.hull-pick-btn').textContent) && !document.querySelector('.hull-pick').open"),
          'switch hull: the dropdown closes, names the Curse and spins')
    vd.dispatch_event('click')   # a second hull while the first loads: ignored
    wait_idle(pg)
    txt = pg.inner_text('#fitResults')
    check('Curse' in pg.locator('.candidate-btn.active').text_content() and 'Vedmak' not in txt[:600] and pg.evaluate("/Curse/.test(document.getElementById('fitStatus').textContent) || /Curse/.test(document.getElementById('fitResults').innerText)"),
          'switch hull: the click on another hull meanwhile was ignored; the Curse is shown')
    # cached: back to the Loki, no bar
    pg.evaluate('window.__delay.zkb = 0')
    seen = []
    pg.evaluate("window.__barSeen = false; new MutationObserver(() => {}).observe(document.body, {subtree: true, attributes: true}); setInterval(() => { const b = document.getElementById('pilotBusy'); if(!b.hidden && getComputedStyle(b).visibility === 'visible') window.__barSeen = true; }, 10);")
    pg.click('.hull-pick-btn'); pg.locator('.candidate-btn:has-text("Loki")').click(); wait_idle(pg); pg.wait_for_timeout(300)
    check(not pg.evaluate('window.__barSeen') and 'Loki' in pg.locator('.candidate-btn.active').text_content() and 'Loki' in pg.inner_text('.hull-pick-btn'), 'cached hull switch (from the dropdown): done without the bar showing')
    # Refresh losses
    pg.evaluate('window.__delay.zkb = 900; window.__barSeen = false')
    pg.evaluate('window.scrollTo(0, 0)'); pg.click('#refreshLossesBtn'); pg.wait_for_timeout(450)
    s3 = bar_state(pg)
    check(s3['vis'] == 'visible' and 'Refreshing losses' in s3['label'], f'Refresh losses: bar "{s3["label"]}"')
    wait_idle(pg)
    check(not pg.evaluate("document.getElementById('refreshLossesBtn').disabled"), 'Refresh losses: button usable again')
    check(not errs, f'Pilot Analyzer: no page errors {errs}')
    # Fit Analyzer
    pg.click('#tabBtnFit'); pg.fill('#fitAnalyzerInput', "[Rifter, slow]\n\n1MN Afterburner II\n\n200mm AutoCannon II, EMP S\n")
    pg.evaluate('window.__delay.ids = 1200'); pg.click('#fitAnalyzerBtn'); pg.wait_for_timeout(500)
    s4 = bar_state(pg, '#fitAnalyzerBusy')
    check(s4['vis'] == 'visible' and 'Analyzing fit' in s4['label'], f'Fit Analyzer: its own bar "{s4["label"]}" ({s4["detail"][:50]})')
    wait_idle(pg, '#fitAnalyzerBusy')
    check(pg.locator('#fitAnalyzerResults .fit-layout').count() == 1 and not pg.evaluate("document.getElementById('fitAnalyzerResults').classList.contains('is-busy')"), 'Fit Analyzer: done, results shown, not dimmed')
    check(not errs, f'Fit Analyzer: no page errors {errs}')
    ctx.close()
    # reduced motion
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce'); pg = ctx.new_page()
    pg.route(re.compile(r'https://.*'), lambda r: r.fulfill(status=404, body=''))
    pg.goto('file://' + HTML)
    an = pg.evaluate("() => { const b = document.getElementById('pilotBusy'); b.hidden = false; return getComputedStyle(b.querySelector('.busy-spin')).animationName; }")
    check(an == 'none', f'reduced motion: the spinner does not spin ({an})')
    ctx.close()
    b.close()
print(f'FAILURES: {fails}')
