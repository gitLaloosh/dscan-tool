"""The last kill in the Pilot Analyzer header (v2026.10.14.44, option A of the "Last kill details" mockup).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/last_kill_check.py [index.html]   -> 'FAILURES: N' (must be 0)

zKillboard and ESI are mocked (the killmails of busy_check.py, plus a last kill with seven other attackers). Checks:
  * closed: one line in the header (pilot, hull dropdown, last kill on one row);
  * open: a panel floats under the line -- the header and the loss box do not move; "Vedmak killed a Curse", the
    time, "using Heavy Entropic Disintegrator II" with an "ammo" tag, the pivot button and the zKillboard link;
  * attackers: loaded on first open, final blow first, five rows then "… 2 more" (expands, collapses), "—" for a
    weapon that is only the hull or missing, damage tags (fixed types / "ammo" / none);
  * Escape and a press outside close it; the pivot button closes it and loads that hull;
  * phone (375 px): the panel is a sheet across the bottom with a close button, two-line rows, no sideways scroll.
No page errors.
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


# v2026.10.14.44: seven other attackers -- final blow (drone), blaster (ammo), hull-as-weapon, launcher (ammo),
# tackle (no damage), no weapon, hull-as-weapon -- and Test Pilot flying a Vedmak with a Heavy Entropic Disintegrator II
_A = lambda cid, ship, wpn, fb=False, dmg=100: {'character_id': cid, 'ship_type_id': ship, **({'weapon_type_id': wpn} if wpn else {}), 'final_blow': fb, 'damage_done': dmg, 'security_status': 0}
KM[9100100]['attackers'] = [_A(90000001, _ved, 47918, False, 900), _A(90000002, _ved, 2185, True, 300), _A(90000003, 626, 3146, False, 800),
    _A(90000004, 629, 629, False, 700), _A(90000005, 621, 2410, False, 600), _A(90000006, 11176, 448, False, 5), _A(90000007, 629, None, False, 400), _A(90000008, 629, 629, False, 200)]
PILOTS = {90000001: 'Test Pilot', 90000002: 'Ca1ned', 90000003: 'FireMaccon', 90000004: 'Forbidden Hunter', 90000005: 'james56', 90000006: 'kimy JP', 90000007: 'SPEKTR N12', 90000008: 'Esinhart Ohmiras'}
NAME.update(PILOTS)

def wait_idle(pg):
    pg.wait_for_function("() => document.querySelector('#pilotBusy').hidden", timeout=60000); pg.wait_for_timeout(150)
def start(b, w, h, mobile=False):
    ctx = b.new_context(viewport={'width': w, 'height': h}, is_mobile=mobile, has_touch=mobile); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route(re.compile(r'https://esi\.evetech\.net/.*'), esi)
    pg.route(re.compile(r'https://zkillboard\.com/.*'), zkb)
    pg.route(re.compile(r'https://(images\.evetech\.net|fonts\.).*'), lambda r: r.fulfill(status=404, body=''))
    pg.goto('file://' + HTML); pg.evaluate("localStorage.removeItem('dscanMyShip')")
    pg.click('#tabBtnPilot'); pg.fill('#pilotName', 'Test Pilot'); pg.click('#fitBtn'); wait_idle(pg)
    pg.wait_for_selector('.lk-sum')
    return ctx, pg, errs
def box(pg, sel): return pg.locator(sel).first.bounding_box()
def rows(pg):
    return pg.evaluate("() => [...document.querySelectorAll('#attackerList .lk-att-row')].map(r => ({hidden: r.hidden, who: r.querySelector('.lk-att-who').textContent, ship: r.querySelector('.lk-att-ship').textContent, weapon: r.querySelector('.lk-att-weapon').textContent, tag: r.querySelector('.lk-att-dmg').textContent.trim(), fb: r.classList.contains('finalblow')}))")

def desktop(b):
    ctx, pg, errs = start(b, 1440, 900)
    hb = [box(pg, x) for x in ('#pilotHeadName', '#fitCandidates .hull-static', '.lk-sum')]
    check(max(x['y'] + x['height'] / 2 for x in hb) - min(x['y'] + x['height'] / 2 for x in hb) < 6 and pg.is_hidden('.lk-body'), 'closed: pilot, hull and last kill on one line')
    before = [box(pg, x) for x in ('#pilotHeadName', '#fitCandidates .hull-static', '.lk-sum', '#fitResults .assess-tabs')]
    pg.click('.lk-sum'); pg.wait_for_selector('#attackerList .lk-att-row', timeout=30000); pg.wait_for_timeout(200)
    after = [box(pg, x) for x in ('#pilotHeadName', '#fitCandidates .hull-static', '.lk-sum', '#fitResults .assess-tabs')]
    check(all(abs(a['y'] - c['y']) < 1 and abs(a['x'] - c['x']) < 1 for a, c in zip(before, after)), 'open: the header line and the loss box do not move')
    pb, sb, tb = box(pg, '.lk-body'), box(pg, '.lk-sum'), box(pg, '#fitResults .assess-tabs')
    check(pb['y'] >= sb['y'] + sb['height'] and pb['y'] < tb['y'] + 40 and abs(pb['x'] - sb['x']) < 2 and pb['height'] > 200,
          f'open: a panel floats under the last-kill line, over the loss box ({pb["width"]:.0f} x {pb["height"]:.0f})')
    t = pg.inner_text('.lk-body')
    check('Vedmak killed a Curse' in pg.inner_text('.lk-title') and 'using Heavy Entropic Disintegrator II' in pg.inner_text('.lk-weapon') and 'ammo' in pg.inner_text('.lk-weapon')
          and pg.is_visible('#lkPivotBtn') and pg.is_visible('.lk-body a[href*="zkillboard.com/kill/9100100/"]') and pg.inner_text('.lk-when').strip() != '',
          f'open: headline, time, weapon with its tag, pivot button and zKillboard link ({pg.inner_text(".lk-title")} | {pg.inner_text(".lk-when")})')
    r = rows(pg)
    vis = [x for x in r if not x['hidden']]
    check(len(r) == 7 and len(vis) == 5 and r[0]['who'] == 'Ca1ned' and r[0]['fb'] and 'final blow' in r[0]['weapon'] and [x['who'] for x in r[1:]] == ['FireMaccon', 'Forbidden Hunter', 'james56', 'SPEKTR N12', 'Esinhart Ohmiras', 'kimy JP'],
          f'attackers: final blow first, then by damage; five shown ({[x["who"] for x in vis]})')
    by = {x['who']: x for x in r}
    check(by['Forbidden Hunter']['weapon'] == '—' and by['SPEKTR N12']['weapon'] == '—' and by['FireMaccon']['weapon'] == 'Heavy Neutron Blaster II' and by['Forbidden Hunter']['ship'] == 'Rupture',
          'attackers: "—" when the weapon is only the hull or missing')
    check(by['FireMaccon']['tag'] == 'ammo' and by['james56']['tag'] == 'ammo' and by['Forbidden Hunter']['tag'] == '' and by['kimy JP']['tag'] == '' and by['Ca1ned']['tag'] not in ('', 'ammo'),
          f'attackers: damage tags (drone {by["Ca1ned"]["tag"]!r}, blaster/launcher "ammo", none for tackle or the hull)')
    check(pg.inner_text('.lk-more').startswith('… 2 more'), 'attackers: "… 2 more"')
    if os.environ.get('SHOTS'): pg.screenshot(path=os.path.join(os.environ['SHOTS'], 'last_kill_panel.png'))
    pg.click('.lk-more'); pg.wait_for_timeout(100)
    check(all(not x['hidden'] for x in rows(pg)) and 'Show fewer' in pg.inner_text('.lk-more'), '"… 2 more" shows all seven')
    pg.click('.lk-more'); pg.wait_for_timeout(100)
    check(sum(not x['hidden'] for x in rows(pg)) == 5, '"Show fewer" goes back to five')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    check(pg.is_hidden('.lk-body') and pg.evaluate("document.activeElement && document.activeElement.classList.contains('lk-sum')"), 'Escape closes it, focus back on the line')
    pg.click('.lk-sum'); pg.wait_for_timeout(100); pg.mouse.click(1300, 860); pg.wait_for_timeout(100)
    check(pg.is_hidden('.lk-body'), 'a press outside closes it')
    pg.click('.lk-sum'); pg.wait_for_timeout(100)
    check(pg.locator('#attackerList .lk-att-row').count() == 7, 'reopened: the attackers are still there (looked up once)')
    pg.click('#lkPivotBtn'); wait_idle(pg)
    check(pg.is_hidden('.lk-body') and 'Vedmak' in pg.inner_text('#fitCandidates') and pg.input_value('#manualShip') == 'Vedmak', 'the pivot button closes it and loads the Vedmak losses')
    check(not errs, f'desktop: no page errors {errs}')
    ctx.close()
    for w in (1000, 700):   # the panel shifts left rather than running off the right edge
        ctx, pg, errs = start(b, w, 900)
        pg.click('.lk-sum'); pg.wait_for_selector('#attackerList .lk-att-row', timeout=30000); pg.wait_for_timeout(150)
        pb = box(pg, '.lk-body'); sw = pg.evaluate('document.documentElement.scrollWidth')
        check(pb['x'] >= 0 and pb['x'] + pb['width'] <= w - 15 and sw <= w, f'{w} px: the panel stays on screen ({pb["x"]:.0f}..{pb["x"] + pb["width"]:.0f}), no sideways scroll ({sw})')
        check(not errs, f'{w} px: no page errors {errs}')
        ctx.close()

def phone(b):
    W = 375
    ctx, pg, errs = start(b, W, 740, True)
    pg.tap('.lk-sum'); pg.wait_for_selector('#attackerList .lk-att-row', timeout=30000); pg.wait_for_timeout(200)
    pb = box(pg, '.lk-body')
    check(abs(pb['x']) < 1 and abs(pb['width'] - W) < 1 and abs(pb['y'] + pb['height'] - 740) < 2 and pg.is_visible('.lk-close'), f'phone: a sheet across the bottom with a close button ({pb["height"]:.0f} px tall)')
    r0 = box(pg, '#attackerList .lk-att-row'); who = box(pg, '#attackerList .lk-att-who'); ship = box(pg, '#attackerList .lk-att-ship')
    check(ship['y'] > who['y'] + who['height'] - 2, 'phone: two lines per attacker (pilot, then hull and weapon)')
    sw = pg.evaluate('document.documentElement.scrollWidth'); check(sw <= W, f'phone: no sideways scroll ({sw})')
    if os.environ.get('SHOTS'): pg.screenshot(path=os.path.join(os.environ['SHOTS'], 'last_kill_phone.png'))
    pg.tap('.lk-close'); pg.wait_for_timeout(150)
    check(pg.is_hidden('.lk-body'), 'phone: the close button closes it')
    check(not errs, f'phone: no page errors {errs}')
    ctx.close()

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('CHROMIUM', '/opt/pw-browsers/chromium'))
    desktop(b); phone(b)
    b.close()
print(f'FAILURES: {fails}')
