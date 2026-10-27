"""Shared killmail links (v2026.10.14.79; the owner: "sharing assessment of a zkill entry ... that way we know what to compare to",
the link "just carrying the killmail", then from the mockup: "a. menu b. agreed c. yes d. fine for now").

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/shared_kill_check.py [index.html]   -> 'FAILURES: N' (must be 0)

zKillboard and ESI are mocked (the killmails of last_kill_check.py, with real-looking 40-character hashes; ESI answers 422
to a wrong hash, as it does). Checks:
  * the loss's ⋮ menu: "Copy share link" first, above Export fit; a click copies <page>#kill=<id>/<hash> of the loss on
    screen (the second tab gives the second loss's link) and reads "Copied!";
  * opening that link: the Pilot tab on that one loss, with NO zKillboard call (the killmail comes from ESI); the pilot's
    name, the hull with a "shared killmail" tag (no hull dropdown, no Last Kill line), the date and system, a zKillboard
    link, "See Test Pilot's Loki losses"; one tab; Firepower and EHP equal to the same loss in the normal analysis; the
    address keeps the link; Refresh losses draws it again;
  * "See Test Pilot's Loki losses": the normal analysis (two Loki losses, the Last Kill line), the address drops the link;
  * a zKillboard kill link pasted into the pilot box: one zKillboard call (/api/killID/), that loss (the Vedmak), and the
    address shows its share link; an ID zKillboard doesn't know: SHARE-01;
  * a link cut short (#kill=<id> only): SHARE-02; a wrong hash: ESI-05; a new link typed into the address bar of an open
    page (hashchange) loads it;
  * 390 px: the header wraps, no sideways scroll. No page errors.
v2026.10.14.78 fails (no share item, a link opens nothing).
"""
import sys, os, re, json, hashlib
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
    km['solar_system_id'] = 30000142; km['victim']['character_id'] = 90000001
    KM[kid] = km
KM[9100005] = dict(KM[9100001], killmail_id=9100005, killmail_time='2026-10-05T12:00:00Z')
H = {kid: hashlib.sha1(str(kid).encode()).hexdigest() for kid in KM}
STUBS = [{'killmail_id': kid, 'zkb': {'hash': H[kid]}} for kid in (9100001, 9100002, 9100003, 9100004, 9100005)]
_ved = KM[9100003]['victim']['ship_type_id']
KM[9100100] = {'killmail_id': 9100100, 'killmail_time': '2026-09-01T18:18:03Z', 'solar_system_id': 30000142, 'victim': dict(KM[9100002]['victim'], items=[]),
               'attackers': [{'character_id': 90000001, 'ship_type_id': _ved, 'weapon_type_id': _ved, 'final_blow': True, 'damage_done': 900, 'security_status': 0}]}
H[9100100] = hashlib.sha1(b'9100100').hexdigest()
NAME = {int(k): _en(v.get('typeName') or v.get('name')) for k, v in types.items()}
NAME.update({90000001: 'Test Pilot', 30000142: 'Jita'})
ZKB_CALLS = []

fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok

def esi(route):
    url, body = route.request.url, route.request.post_data or ''
    if '/universe/ids/' in url and 'Test Pilot' in body:
        return route.fulfill(status=200, content_type='application/json', body=json.dumps({'characters': [{'id': 90000001, 'name': 'Test Pilot'}]}))
    m = re.search(r'/killmails/(\d+)/([^/]+)/', url)
    if m:
        kid = int(m.group(1))
        if kid not in KM or H[kid] != m.group(2): return route.fulfill(status=422, content_type='application/json', body='{"error":"Invalid killmail_id and/or killmail_hash"}')
        return route.fulfill(status=200, content_type='application/json', body=json.dumps(KM[kid]))
    if '/universe/names/' in url:
        ids = json.loads(body)
        return route.fulfill(status=200, content_type='application/json', body=json.dumps([{'id': i, 'name': NAME.get(i, f'type {i}'), 'category': 'inventory_type'} for i in ids]))
    return esi_handle(route)
def zkb(route):
    cors = {'access-control-allow-origin': '*'}
    url = route.request.url
    ZKB_CALLS.append(url)
    if '/kills/' in url: return route.fulfill(status=200, content_type='application/json', headers=cors, body=json.dumps([{'killmail_id': 9100100, 'zkb': {'hash': H[9100100]}}]))
    m = re.search(r'/killID/(\d+)/', url)
    if m:
        kid = int(m.group(1))
        return route.fulfill(status=200, content_type='application/json', headers=cors, body=json.dumps([s for s in STUBS if s['killmail_id'] == kid]))
    m = re.search(r'/shipTypeID/(\d+)/', url)
    stubs = [s for s in STUBS if not m or KM[s['killmail_id']]['victim']['ship_type_id'] == int(m.group(1))]
    return route.fulfill(status=200, content_type='application/json', headers=cors, body=json.dumps(stubs))

def tabs_shown(pg, ms=60000):
    try: pg.wait_for_selector('#fitResults .subtab-btn', timeout=ms); return True
    except Exception: return False
def wait_idle(pg):
    pg.wait_for_function("() => document.querySelector('#pilotBusy').hidden", timeout=90000); pg.wait_for_timeout(250)
def page(b, w, h, mobile=False, url=''):
    ctx = b.new_context(viewport={'width': w, 'height': h}, is_mobile=mobile, has_touch=mobile)
    try: ctx.grant_permissions(['clipboard-read', 'clipboard-write'])
    except Exception: pass
    pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route(re.compile(r'https://esi\.evetech\.net/.*'), esi)
    pg.route(re.compile(r'https://zkillboard\.com/.*'), zkb)
    pg.route(re.compile(r'https://(images\.evetech\.net|fonts\.).*'), lambda r: r.fulfill(status=404, body=''))
    pg.goto('file://' + HTML + url)
    pg.evaluate("localStorage.removeItem('dscanMyShip'); localStorage.removeItem('dscanMyShips')")
    return ctx, pg, errs
STATS = """() => { const t = document.querySelector('#fitResults .subtab-panel:not([style*="none"])'); if(!t) return null;
  const v = (label) => { const e = [...t.querySelectorAll('.estimate-stat')].find(x => x.innerText.toUpperCase().includes(label)); return e ? e.innerText.replace(/\\s+/g, ' ').trim() : null; };
  return {dps: v('TOTAL DPS'), volley: v('VOLLEY')}; }"""
HEAD = """() => ({name: document.querySelector('#pilotHeadName').textContent, hull: (document.querySelector('#fitCandidates .km-shared .hull-static') || {}).textContent || null,
  tag: !!document.querySelector('#fitCandidates .km-shared-tag'), dropdown: !!document.querySelector('#fitCandidates .hull-pick'), lastKill: !!document.querySelector('#lastKillInfo .lk-sum'),
  when: (document.querySelector('#lastKillInfo .km-when') || {}).textContent || '', zkb: (document.querySelector('#lastKillInfo .km-shared-acts a') || {}).href || '',
  see: (document.querySelector('#kmSeeLosses') || {}).textContent || '', tabs: document.querySelectorAll('#fitResults .subtab-btn').length,
  status: document.querySelector('#fitStatus').textContent, hash: location.hash, pilotBox: document.querySelector('#pilotName').value})"""

with sync_playwright() as p:
    b = p.chromium.launch()
    # ---------------- the sender
    ctx, pg, errs = page(b, 1440, 1000)
    pg.click('#tabBtnPilot'); pg.fill('#pilotName', 'Test Pilot'); pg.fill('#manualShip', 'Loki'); pg.click('#fitBtn'); wait_idle(pg)
    pg.wait_for_selector('#fitResults .subtab-btn')
    base = pg.evaluate(STATS)
    pg.click('#fitResults .fit-menu-btn'); pg.wait_for_timeout(150)
    items = pg.evaluate("() => [...document.querySelectorAll('#fitResults .fit-menu-item')].map(x => x.textContent.trim())")
    check(items[:2] == ['Copy share link', 'Export fit to clipboard (EFT)'], f'the loss menu: Copy share link first, above Export fit ({items})')
    if 'Copy share link' not in items: print(f'FAILURES: {fails}'); sys.exit(1)   # a build without it (v.78)
    pg.click('#fitResults .fit-menu-item[data-action="share-link"]'); pg.wait_for_timeout(200)
    label = pg.inner_text('#fitResults .fit-menu-item[data-action="share-link"]')
    link1 = pg.evaluate('navigator.clipboard.readText()')
    check(label == 'Copied!' and link1.startswith('file://' + HTML) and link1.endswith(f'#kill=9100001/{H[9100001]}'), f'a click copies the loss\'s link and reads "Copied!" ({label!r}, {link1[-60:]!r})')
    pg.wait_for_timeout(1300)
    pg.click('#fitResults .subtab-btn[data-idx="1"]'); pg.click('#fitResults .fit-menu-btn'); pg.wait_for_timeout(150)
    pg.click('#fitResults .fit-menu-item[data-action="share-link"]'); pg.wait_for_timeout(200)
    link2 = pg.evaluate('navigator.clipboard.readText()')
    check(link2.endswith(f'#kill=9100005/{H[9100005]}'), f'on the second tab it copies the second loss\'s link ({link2[-60:]!r})')
    check(not errs, f'sender: no page errors {errs[:2]}')
    ctx.close()
    # ---------------- the recipient
    ZKB_CALLS.clear()
    ctx, pg, errs = page(b, 1440, 1000, url=f'#kill=9100001/{H[9100001]}')
    if not tabs_shown(pg, 90000):
        check(False, f"opening the link shows the loss ({pg.inner_text('#fitStatus')!r})"); print(f'FAILURES: {fails}'); sys.exit(1)
    wait_idle(pg)
    h = pg.evaluate(HEAD); st = pg.evaluate(STATS)
    check(not ZKB_CALLS, f'opening a link makes no zKillboard call ({ZKB_CALLS[:2]})')
    check(h['name'] == 'Test Pilot' and h['hull'] == 'Loki' and h['tag'] and not h['dropdown'] and not h['lastKill'] and h['tabs'] == 1 and h['pilotBox'] == 'Test Pilot',
          f'the Pilot tab on that one loss: the pilot, the hull tagged "shared killmail", no dropdown, no Last Kill line, one tab ({h})')
    check('Jita' in h['when'] and h['zkb'] == 'https://zkillboard.com/kill/9100001/' and h['see'] == "See Test Pilot's Loki losses" and h['status'].startswith("Shared killmail: Test Pilot's Loki"),
          f"the date and system, the zKillboard link, \"See Test Pilot's Loki losses\", the status line ({h['when']!r}, {h['status']!r})")
    check(st == base and st['dps'], f'Firepower equals the same loss in the normal analysis ({st} vs {base})')
    check(h['hash'] == f'#kill=9100001/{H[9100001]}', f'the address keeps the link ({h["hash"]})')
    pg.click('#refreshLossesBtn'); wait_idle(pg)
    h2 = pg.evaluate(HEAD)
    check(h2['tabs'] == 1 and h2['tag'] and pg.evaluate(STATS) == base, 'Refresh losses draws the shared loss again')
    # See their losses
    pg.click('#kmSeeLosses'); wait_idle(pg); pg.wait_for_selector('#lastKillInfo .lk-sum', timeout=60000)
    h3 = pg.evaluate(HEAD)
    check(h3['tabs'] == 2 and h3['lastKill'] and not h3['tag'] and h3['hash'] == '', f'"See their losses": the normal analysis (2 Loki losses, the Last Kill line); the address drops the link ({h3["tabs"]}, {h3["hash"]!r})')
    # a zKillboard link pasted into the pilot box
    ZKB_CALLS.clear()
    pg.fill('#manualShip', ''); pg.fill('#pilotName', 'https://zkillboard.com/kill/9100003/'); pg.click('#fitBtn'); wait_idle(pg)
    h4 = pg.evaluate(HEAD)
    check(h4['hull'] == 'Vedmak' and h4['tabs'] == 1 and h4['hash'] == f'#kill=9100003/{H[9100003]}' and len(ZKB_CALLS) == 1 and '/killID/9100003/' in ZKB_CALLS[0],
          f'a pasted zKillboard link: one zKillboard call, that loss (the Vedmak), the address shows its link ({h4["hull"]}, {ZKB_CALLS})')
    pg.fill('#pilotName', 'zkillboard.com/kill/9999999/'); pg.click('#fitBtn'); wait_idle(pg)
    s1 = pg.inner_text('#fitStatus')
    check('(SHARE-01)' in s1 and not pg.evaluate("document.querySelectorAll('#fitResults .subtab-btn').length"), f'an ID zKillboard doesn\'t know: SHARE-01 ({s1!r})')
    # a new link in the address bar of the open page
    pg.evaluate(f"location.hash = '#kill=9100002/{H[9100002]}'"); pg.wait_for_timeout(300); wait_idle(pg); tabs_shown(pg, 20000)
    h5 = pg.evaluate(HEAD)
    check(h5['hull'] == 'Curse' and h5['tag'], f'a link typed into the address bar of the open page loads it ({h5["hull"]})')
    check(not errs, f'recipient: no page errors {errs[:2]}')
    ctx.close()
    # ---------------- broken links
    ctx, pg, errs = page(b, 1440, 1000, url='#kill=9100001')
    pg.wait_for_timeout(600)
    s2 = pg.inner_text('#fitStatus')
    check('(SHARE-02)' in s2, f'a link cut short: SHARE-02 ({s2!r})')
    ctx.close()
    ctx, pg, errs = page(b, 1440, 1000, url='#kill=9100001/' + 'a' * 40)
    pg.wait_for_timeout(400); wait_idle(pg)
    s3 = pg.inner_text('#fitStatus')
    check('(ESI-05)' in s3 and '422' in s3, f'a wrong hash: ESI-05 ({s3!r})')
    ctx.close()
    # ---------------- phone
    ctx, pg, errs = page(b, 390, 844, True, url=f'#kill=9100001/{H[9100001]}')
    tabs_shown(pg, 90000); wait_idle(pg)
    g = pg.evaluate("""() => { const r = (s) => document.querySelector(s).getBoundingClientRect();
      const a = r('#fitCandidates .km-shared'), c = r('#lastKillInfo .km-shared-acts');
      return {sc: [document.documentElement.scrollWidth, innerWidth], right: Math.max(a.right, c.right)}; }""")
    check(g['sc'][0] <= g['sc'][1] and g['right'] <= 390, f'390px: the header fits, no sideways scroll ({g})')
    check(not errs, f'phone: no page errors {errs[:2]}')
    ctx.close()
    b.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
