"""Pilot Analyzer when zKillboard's API is down (v2026.10.14.31; error codes since v2026.10.14.32).

    PYFA_SRC=... python3 tools/page_checks/zkb_outage_check.py [index.html]   -> 'FAILURES: N'

Since 2026-10-22 zKillboard answers 503 {"error":"API result unavailable, please try again later"} after a
60 s wait when its API queue doesn't produce a result (zKillboard view/api.php, commit ffc94263). The page
must say plainly what zKillboard did, not blame the user's network, and stay usable. Since v2026.11.06.4 (build
queue 014) that 503 means zKillboard is slow on that list (ZKB-06), not down, and the page waits 65 s itself
(ZKB_TIMEOUT_MS, just past zKillboard's own minute). Four cases, each with zKillboard served by this script:
  502   -> the outage message (ZKB-01) at once, no "check your network connection" hint
  503   -> zKillboard's own "unavailable": the slow message (ZKB-06) at once, no network hint, no page pause
  hang  -> no answer at all: the slow message after ~65 s (the lookups run side by side, so not 130)
  ok    -> an empty answer: the normal "no recorded kills or losses" texts (PILOT-03 since v.90)
ESI is served from pyfa's SDE (esi_from_sde.py) plus a stand-in character for the pilot name.
"""
import sys, os, json, re, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esi_from_sde import handle as esi_handle
from playwright.sync_api import sync_playwright

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')),
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'index.html')))
OUTAGE = "(ZKB-01)"   # v2026.10.14.32: checked by error code, so the wording can change

def run(mode, pilot='Test Pilot'):
    def esi(route):
        if '/universe/ids/' in route.request.url and 'Test Pilot' in (route.request.post_data or ''):
            return route.fulfill(status=200, content_type='application/json',
                                 body=json.dumps({'characters': [{'id': 90000001, 'name': 'Test Pilot'}]}))
        return esi_handle(route)
    def zkb(route):
        if mode == 'hang': return
        cors = {'access-control-allow-origin': '*'}
        if mode == '502': return route.fulfill(status=502, content_type='text/html', headers=cors, body='<html>Bad gateway</html>')
        if mode == '503':
            return route.fulfill(status=503, content_type='application/json', headers=cors,
                                 body='{"error":"API result unavailable, please try again later"}')
        return route.fulfill(status=200, content_type='application/json', headers=cors, body='[]')
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ.get('CHROMIUM', '/opt/pw-browsers/chromium'))
        pg = b.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.route(re.compile(r'https://esi\.evetech\.net/.*'), esi)
        pg.route(re.compile(r'https://zkillboard\.com/.*'), zkb)
        pg.route(re.compile(r'https://(images\.evetech\.net|fonts\.).*'), lambda r: r.fulfill(status=404, body=''))
        pg.goto('file://' + HTML); pg.click('#tabBtnPilot')
        pg.fill('#pilotName', pilot); t0 = time.time(); pg.click('#fitBtn')
        pg.wait_for_function("() => !document.getElementById('fitBtn').disabled", timeout=90000)
        out = (time.time() - t0, pg.inner_text('#fitStatus'), pg.inner_text('#lastKillInfo'), errs, pg.evaluate("() => zkbUnavailableUntil > Date.now()"))
        b.close()
        return out

fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok
for mode in ('502', '503', 'hang', 'ok'):
    secs, status, lastkill, errs, paused = run(mode)
    if mode == 'ok':
        # v2026.10.14.90: the Pilot Dossier reads kills and losses together: "No recorded kills or losses ... (PILOT-03)"
        check('No recorded kills or losses' in status and '(PILOT-03)' in status and 'No recorded kills' in lastkill, f'{mode}: normal empty-result texts ({secs:.1f} s; {status!r})')
    else:
        code = OUTAGE if mode == '502' else '(ZKB-06)'
        check(code in status and code in lastkill and paused == (mode == '502'), f'{mode}: {code} in both places, {"a" if mode == "502" else "no"} page pause ({secs:.1f} s; {status[:90]!r})')
        check('network connection' not in status, f'{mode}: no "check your network" hint')
        check(secs < 5 if mode != 'hang' else 60 < secs < 80, f'{mode}: gave up in {secs:.1f} s')
    check(not errs, f'{mode}: no page errors {errs}')
# v2026.10.14.32: an unknown pilot name shows PILOT-01 (ESI's stand-in knows only "Test Pilot")
secs, status, lastkill, errs, paused = run('ok', pilot='Nobody Here')
check('(PILOT-01)' in status, f'unknown pilot: status ends with (PILOT-01): {status[:120]!r}')
check(not errs, f'unknown pilot: no page errors {errs}')
print(f'FAILURES: {fails}')
