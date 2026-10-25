"""The tool's name and header (v2026.10.14.60, the rename to EVE Threat Assessment).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/header_check.py [index.html]   -> 'FAILURES: N' (must be 0)

the owner 2026-10-25: "EVE Threat Assessment", tagline A, tab title with "(ETA)", only what users see renamed. Checks, at
1440 and 375 px:
  * the browser tab title, the header's name and its one-line tagline; the ESI caching sentence is the Refresh item
    data button's hover; the three tabs keep their names; v2026.10.14.62: in the order Pilot, Fit, D-Scan, the page
    opening on the Pilot Analyzer;
  * the name doesn't run into the version tag, and nothing scrolls sideways;
  * a ship saved before the rename (localStorage "dscanMyShip", the key kept on purpose) is still there after a reload.
No page errors.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esi_from_sde import route_all
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
OSPREY = open(os.path.join(HERE, '..', 'independent_checks', 'fits', 'osprey_navy_issue_mine.eft'), encoding='utf-8').read()

fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok

def run(b, W):
    ctx = b.new_context(viewport={'width': W, 'height': 800}, is_mobile=W < 600, has_touch=W < 600); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML); pg.evaluate("localStorage.removeItem('dscanMyShip')"); pg.reload()
    h = pg.evaluate("""() => { const hero = document.querySelector('header.hero'), b = document.getElementById('refreshCacheBtn');
        return {title: document.title, h1: hero.querySelector('h1').textContent, p: [...hero.querySelectorAll('p')].map(p => p.textContent),
          btn: b.title, tabs: [...document.querySelectorAll('.tab-btn')].map(t => t.textContent.trim())}; }""")
    check(h['title'] == 'EVE Threat Assessment (ETA)' and h['h1'] == 'EVE Threat Assessment', f'{W}: tab title "{h["title"]}", header "{h["h1"]}"')
    check(h['p'] == ["Who's in system, what they fly, and how to beat them."], f'{W}: one tagline {h["p"]}')
    check('ESI' in h['btn'] and 'week' in h['btn'], f'{W}: the caching sentence is the Refresh button\'s hover ("{h["btn"]}")')
    check(h['tabs'] == ['Pilot Analyzer', 'Fit Analyzer', 'D-Scan Analyzer'], f'{W}: the tabs keep their names, D-Scan last (v.62) {h["tabs"]}')
    # v2026.10.14.62: the page opens on the Pilot Analyzer
    shown = pg.evaluate("() => [...document.querySelectorAll('.tab-panel')].filter(p => getComputedStyle(p).display !== 'none').map(p => p.id).concat([document.querySelector('.tab-btn.active').id])")
    check(shown == ['tabPilot', 'tabBtnPilot'], f'{W}: opens on the Pilot Analyzer {shown}')
    gap = pg.evaluate("""() => { const r = document.createRange(); r.selectNodeContents(document.querySelector('header.hero h1')); const t = document.querySelector('header.hero .build-tag').getBoundingClientRect();
        return [...r.getClientRects()].every(a => a.right <= t.left || t.right <= a.left || a.bottom <= t.top || t.bottom <= a.top) ? 1 : -1; }""")   # 1 = every line of the name's text clear of the tag
    sw = pg.evaluate('document.documentElement.scrollWidth')
    check(gap > 0 and sw <= W, f'{W}: the name doesn\'t overlap the version tag, nothing scrolls sideways ({sw})')
    if W > 600:
        # a ship saved under the old name's key is still there after a reload
        pg.click('#myShipChip'); pg.fill('#myShipEft', OSPREY); pg.click('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-tiles'); pg.keyboard.press('Escape')
        pg.reload(); pg.wait_for_timeout(500)
        chip = ' '.join(pg.inner_text('#myShipChip').split())
        check(pg.evaluate("() => !!localStorage.getItem('dscanMyShip')") and 'Osprey Navy Issue' in chip, f'{W}: a saved ship survives a reload under the kept key ("{chip}")')
    check(not errs, f'{W}: no page errors {errs}')
    ctx.close()

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('CHROMIUM', '/opt/pw-browsers/chromium'))
    run(b, 1440); run(b, 375)
    b.close()
print(f'FAILURES: {fails}')
