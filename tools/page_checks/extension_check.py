"""The browser extension (browser-extension/, v1.0.0 with the tool's v2026.10.14.80; the owner: "build the browser extension", the
menu items "all three").

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/extension_check.py [index.html]   -> 'FAILURES: N' (must be 0)

Chromium loads the unpacked extension (new headless mode); zKillboard and ESI are mocked (killmail_mocks.py) and the tool's
address is set to a local web server serving index.html (a tab the extension opens isn't routed by Playwright on its first
load, so the page comes from http://127.0.0.1:<port>/; its ESI and zKillboard calls are routed). Checks:
  * the manifest: Manifest V3, permissions contextMenus and storage only, no host permissions, no content scripts;
  * the five menu items exist (kill link / page, pilot link / page, selected text), with zKillboard URL patterns;
  * the link each click makes (etaLinkFor): #zkill=<id> for a kill link or page, #pilot=<id> for a pilot link or page,
    #pilotname=<name> for selected text (spaces tidied, a selected zKillboard link opens that instead), nothing for an
    empty or too long selection;
  * end to end (etaHandleClick): a kill link opens a tab on the tool showing that kill (the Vedmak) as a shared killmail;
    a pilot link and a selected name open the Pilot Analyzer for Test Pilot; an unknown pilot ID shows SHARE-03;
  * the options page: the default address, a saved one is used by the next click, a bad address is refused, "Use the
    default" puts it back. No page errors.
v2026.10.14.79 fails (the tool doesn't read #zkill= / #pilot= / #pilotname=).
v1.1.0 (v2026.11.06.2, build queue 013): named "Threat Vector for zKillboard", the menus "... in Threat Vector", the default address
https://threatvector.space/; a saved address equal to the old default (https://gitlaloosh.github.io/dscan-tool/) opens the new one
and the options page shows the new one; any other saved address is kept.
"""
import sys, os, time, re, json, tempfile, threading, http.server, functools
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from playwright.sync_api import sync_playwright
from killmail_mocks import H, esi, zkb

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
EXT = os.path.abspath(os.path.join(HERE, '..', '..', 'browser-extension'))
class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path.split('?')[0].split('#')[0] in ('/', '/index.html'):
            body = open(HTML, 'rb').read()
            self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
        else:
            self.send_response(404); self.end_headers()
_srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), _Quiet)
threading.Thread(target=_srv.serve_forever, daemon=True).start()
TOOL = f'http://127.0.0.1:{_srv.server_address[1]}/'
DEFAULT = 'https://threatvector.space/'
OLD_DEFAULT = 'https://gitlaloosh.github.io/dscan-tool/'   # v1.1.0: before the move
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok

man = json.load(open(os.path.join(EXT, 'manifest.json')))
check(man.get('manifest_version') == 3 and sorted(man.get('permissions', [])) == ['contextMenus', 'storage'] and not man.get('host_permissions')
      and not man.get('content_scripts') and not man.get('optional_permissions'), f"manifest: V3, contextMenus + storage only, no host permissions or content scripts ({man.get('permissions')})")
check(man.get('name') == 'Threat Vector for zKillboard' and man.get('short_name') == 'Threat Vector' and man.get('version') == '1.1.0'
      and 'Threat Vector' in man.get('description', '') and 'EVE Threat Assessment' not in json.dumps(man), f"manifest: the new name, version 1.1.0 ({man.get('name')}, {man.get('version')})")

def wait_idle(pg):
    pg.wait_for_function("() => document.querySelector('#pilotBusy') && document.querySelector('#pilotBusy').hidden", timeout=90000); pg.wait_for_timeout(300)
HEAD = """() => ({name: (document.querySelector('#pilotHeadName') || {}).textContent || '', shared: !!document.querySelector('#fitCandidates .km-shared'),
  hull: (document.querySelector('#fitCandidates .hull-static') || document.querySelector('#fitCandidates .hp-name') || {}).textContent || '',
  tabs: document.querySelectorAll('#fitResults .subtab-btn').length, status: (document.querySelector('#fitStatus') || {}).textContent || '', hash: location.hash})"""

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(bypass_csp=True, user_data_dir=tempfile.mkdtemp(), headless=False, viewport={'width': 1440, 'height': 1000},
                                               args=['--headless=new', f'--disable-extensions-except={EXT}', f'--load-extension={EXT}'])
    errs = []
    ctx.on('page', lambda pg: pg.on('pageerror', lambda e: errs.append(str(e))))
    ctx.route(re.compile(r'https://esi\.evetech\.net/.*'), esi)
    ctx.route(re.compile(r'https://zkillboard\.com/.*'), zkb)
    # v2026.11.06.4 (build queue 014): a first load's unrouted zKillboard lookup (above: the tab loads before the routes hold) that the
    # page can't read now pauses every tab, kept in this browser; each load here starts without what an earlier one kept
    ctx.add_init_script("for(const k of ['dscanZkbPause', 'dscanZkbSlow']) try{ localStorage.removeItem(k); }catch(e){}")
    ctx.route(re.compile(r'https://(images\.evetech\.net|fonts\.).*'), lambda r: r.fulfill(status=404, body=''))
    worker = ctx.service_workers[0] if ctx.service_workers else ctx.wait_for_event('serviceworker', timeout=30000)
    ext_id = worker.url.split('/')[2]
    # v2026.11.06.1 (LESSON #115; it flaked in three runs of the full chain): Chrome may restart an extension's service worker when it
    # sits idle or the machine is busy (here it did while a click opened a tab), and the old handle then answers "Service worker
    # restarted". The extension keeps nothing in the worker's memory (the menus and the address are Chrome's), so ask the new one.
    class SW:
        @property
        def url(self): return worker.url
        def evaluate(self, expr, arg=None):
            for attempt in range(3):
                try: return W[0].evaluate(expr, arg)
                except Exception as e:
                    if 'Service worker restarted' not in str(e) and 'Target closed' not in str(e) or attempt == 2: raise
                    live = [x for x in ctx.service_workers if x.url.startswith(f'chrome-extension://{ext_id}/')]
                    W[0] = live[-1] if live else ctx.wait_for_event('serviceworker', timeout=30000)
    W = [worker]
    sw = SW()
    # the menu items: chrome.contextMenus.update fails for an item that doesn't exist
    # v2026.10.14.86: the menus are made in onInstalled; on a busy machine the check could ask first (flaked once with the
    # update-check chain running alongside). Ask again for up to 15 s before judging.
    for _ in range(30):
        menus = sw.evaluate("""() => Promise.all(ETA.MENUS.map(m => new Promise(r => chrome.contextMenus.update(m.id, {}, () => r([m.id, chrome.runtime.lastError ? chrome.runtime.lastError.message : 'ok', m.contexts.join(','), (m.targetUrlPatterns || m.documentUrlPatterns || []).join(' ')])))))""")
        if all(m[1] == 'ok' for m in menus): break
        time.sleep(0.5)
    check([m[0] for m in menus] == ['eta-kill-link', 'eta-kill-page', 'eta-pilot-link', 'eta-pilot-page', 'eta-pilot-name'] and all(m[1] == 'ok' for m in menus)
          and all('zkillboard.com/kill/*' in m[3] for m in menus[:2]) and all('zkillboard.com/character/*' in m[3] for m in menus[2:4]) and menus[4][2] == 'selection',
          f'the five menu items exist with their zKillboard patterns ({[(m[0], m[1], m[2]) for m in menus]})')
    CASES = [({'menuItemId': 'eta-kill-link', 'linkUrl': 'https://zkillboard.com/kill/9100003/'}, '#zkill=9100003'),
             ({'menuItemId': 'eta-kill-page', 'pageUrl': 'https://zkillboard.com/kill/9100003/'}, '#zkill=9100003'),
             ({'menuItemId': 'eta-pilot-link', 'linkUrl': 'https://zkillboard.com/character/90000001/'}, '#pilot=90000001'),
             ({'menuItemId': 'eta-pilot-page', 'pageUrl': 'https://zkillboard.com/character/90000001/'}, '#pilot=90000001'),
             ({'menuItemId': 'eta-pilot-name', 'selectionText': '  Test \n Pilot '}, '#pilotname=Test%20Pilot'),
             ({'menuItemId': 'eta-pilot-name', 'selectionText': "Chribba's Alt"}, "#pilotname=Chribba's%20Alt"),
             ({'menuItemId': 'eta-pilot-name', 'selectionText': 'see https://zkillboard.com/kill/9100003/'}, '#zkill=9100003'),
             ({'menuItemId': 'eta-pilot-name', 'selectionText': 'x' * 38}, None),
             ({'menuItemId': 'eta-pilot-name', 'selectionText': '   '}, None),
             ({'menuItemId': 'eta-kill-link', 'linkUrl': 'https://zkillboard.com/related/123/'}, None)]
    got = sw.evaluate("(cases) => cases.map(c => ETA.etaLinkFor(c))", [c for c, _ in CASES])
    check(got == [w for _, w in CASES], f'the link each click makes ({got})')
    titles = sw.evaluate("() => ETA.MENUS.map(m => m.title)")
    check(all(t.endswith(' in Threat Vector') for t in titles), f'every menu item names Threat Vector ({titles})')
    check(sw.evaluate("() => ETA.etaToolUrl()") == DEFAULT, f'the default address is {DEFAULT}')
    # v1.1.0: someone who pressed Save before the move has the old default stored; it opens the new address
    sw.evaluate("(u) => chrome.storage.sync.set({toolUrl: u})", OLD_DEFAULT)
    old = sw.evaluate("() => ETA.etaToolUrl()")
    op0 = ctx.new_page(); op0.goto(f'chrome-extension://{ext_id}/options.html'); op0.wait_for_timeout(300); old_shown = op0.input_value('#toolUrl'); op0.close()
    check(old == DEFAULT and old_shown == DEFAULT, f'a saved old default opens, and the options page shows, the new address ({old}, {old_shown})')
    sw.evaluate("(u) => chrome.storage.sync.set({toolUrl: u})", TOOL)
    def click(info):
        with ctx.expect_page(timeout=30000) as ev:
            url = sw.evaluate("(i) => ETA.etaHandleClick(i)", info)
        pg = ev.value; pg.wait_for_load_state()
        # v2026.11.06.1 (LESSON #72, #115): the tab starts loading before Playwright attaches to it, and on a busy machine its first
        # requests to ESI could still go out unrouted (a #pilotname= lookup asks at once: "network error"). Load the same address
        # again now that the routes hold; the address the extension opened is checked as it came (url, the hash).
        pg.reload(); pg.wait_for_load_state(); return url, pg
    # a kill link
    url, pg = click({'menuItemId': 'eta-kill-link', 'linkUrl': 'https://zkillboard.com/kill/9100003/'})
    try: pg.wait_for_selector('#fitResults .subtab-btn', timeout=90000)
    except Exception: pass
    wait_idle(pg); h = pg.evaluate(HEAD)
    check(url == TOOL + '#zkill=9100003' and h['shared'] and h['hull'] == 'Vedmak' and h['tabs'] == 1 and h['hash'] == f'#kill=9100003/{H[9100003]}',
          f"a kill link opens the tool on that kill as a shared killmail, the address then its share link ({url}, {h['hull']!r}, {h['hash']!r}, {h['status']!r})")
    pg.close()
    # a pilot link
    url, pg = click({'menuItemId': 'eta-pilot-link', 'linkUrl': 'https://zkillboard.com/character/90000001/'})
    try: pg.wait_for_selector('#fitResults .subtab-btn', timeout=90000)
    except Exception: pass
    wait_idle(pg); h = pg.evaluate(HEAD)
    check(url == TOOL + '#pilot=90000001' and h['name'] == 'Test Pilot' and not h['shared'] and h['tabs'] >= 1 and h['hash'] == '#pilot=90000001'
          and pg.input_value('#pilotName') == 'Test Pilot', f"a pilot link runs the Pilot Analyzer for that pilot, the address keeps the link ({h['name']!r}, {h['tabs']}, {h['hash']!r}, {h['status']!r})")
    pg.close()
    # a selected name
    url, pg = click({'menuItemId': 'eta-pilot-name', 'selectionText': 'Test Pilot'})
    try: pg.wait_for_selector('#fitResults .subtab-btn', timeout=90000)
    except Exception: pass
    wait_idle(pg); h = pg.evaluate(HEAD)
    check(url == TOOL + '#pilotname=Test%20Pilot' and h['name'] == 'Test Pilot' and h['tabs'] >= 1, f"a selected name runs the Pilot Analyzer ({h['name']!r}, {h['tabs']}, {h['status']!r})")
    pg.close()
    # an ID ESI doesn't know as a pilot
    url, pg = click({'menuItemId': 'eta-pilot-link', 'linkUrl': 'https://zkillboard.com/character/99999999/'})
    pg.wait_for_timeout(1500)
    st = pg.inner_text('#fitStatus')
    check('(SHARE-03)' in st, f'an unknown pilot ID: SHARE-03 ({st!r})')
    pg.close()
    # the options page
    op = ctx.new_page(); op.goto(f'chrome-extension://{ext_id}/options.html'); op.wait_for_timeout(300)
    shown = op.input_value('#toolUrl')
    op.fill('#toolUrl', 'not an address'); op.click('#save'); op.wait_for_timeout(200)
    bad = (op.inner_text('#status'), sw.evaluate("() => ETA.etaToolUrl()"))
    op.fill('#toolUrl', 'https://example.test/eta/#old'); op.click('#save'); op.wait_for_timeout(200)
    saved = (op.input_value('#toolUrl'), sw.evaluate("() => ETA.etaToolUrl()"))
    op.click('#reset'); op.wait_for_timeout(200)
    reset = (op.input_value('#toolUrl'), sw.evaluate("() => ETA.etaToolUrl()"))
    check(shown == TOOL and "isn't a web address" in bad[0] and bad[1] == TOOL and saved == ('https://example.test/eta/', 'https://example.test/eta/') and reset == (DEFAULT, DEFAULT),
          f'options: shows the saved address, refuses a bad one, saves a new one (hash dropped), "Use the default" puts it back ({shown}, {bad}, {saved}, {reset})')
    check(not errs, f'no page errors {errs[:2]}')
    ctx.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
