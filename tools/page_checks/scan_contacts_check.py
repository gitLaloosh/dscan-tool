"""On Scan: contacts that aren't ships share one line (v2026.10.14.86).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/scan_contacts_check.py [index.html]   -> 'FAILURES: N' (must be 0)

the owner via todo-inbox 2026-10-27: "run a dscan analysis that contains a scanner probe in it > scanner probes are showing up
in the resistance results"; then "your recommendation sounds fine" (fold every non-ship into one line, as celestials).
The real page, ESI answered from pyfa's SDE (sa_mocks.route). A D-Scan of 2 Ferox, a Caracal, 4 Core Scanner Probe I, a
Combat Scanner Probe I, a Mobile Depot and 5 Hobgoblin II. Checks:
  * one resistance card per ship type, nothing else with resistance bars;
  * one "Other contacts (4)" card after the ship cards, each with its count, the group on hover;
  * the count line: "2 ship type(s), 11 other line(s)";
  * the System Analyzer's own scan list (populateShipSelect / On Scan count) still has only the ships.
v2026.10.14.85 fails (a card per probe type).
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from playwright.sync_api import sync_playwright
import sa_mocks as M

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok
ROWS = [('Ferox', 2), ('Caracal', 1), ('Core Scanner Probe I', 4), ('Combat Scanner Probe I', 1), ('Mobile Depot', 1), ('Hobgoblin II', 5)]
SCAN = '\n'.join(f"{M.byname[t]}\tSomeone's {t} {i}\t{t}\t{1 + i} AU" for t, n in ROWS for i in range(n))
with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []
    for W in (1440, 390):
        ctx = b.new_context(viewport={'width': W, 'height': 1000}); M.route(ctx)
        pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto('file://' + HTML); pg.click('#tabBtnDscan'); pg.fill('#dscanInput', SCAN); pg.click('#analyzeBtn')
        pg.wait_for_function("() => document.querySelectorAll('#resultsGrid > .card').length >= 1 && !document.querySelector('#analyzeBtn').disabled", timeout=60000); pg.wait_for_timeout(300)
        r = pg.evaluate("""() => { const cards = [...document.querySelectorAll('#resultsGrid > .card')];
          return {cards: cards.map(c => [c.querySelector('.cname').textContent, !!c.querySelector('.bars')]),
            other: (cards.find(c => c.classList.contains('sc-other')) || {querySelectorAll: () => []}).querySelectorAll('.cmeta span').length ? [...cards.find(c => c.classList.contains('sc-other')).querySelectorAll('.cmeta span')].map(s => [s.textContent, s.title]) : [],
            count: document.querySelector('#contactsCount').textContent, ships: lastScanShips.map(s => s.name).sort(),
            over: document.documentElement.scrollWidth}; }""")
        check(r['cards'][:2] == [['Ferox', True], ['Caracal', True]] and sum(1 for _, bars in r['cards'] if bars) == 2,
              f"{W} px: a resistance card per ship type, nothing else with bars {r['cards']}")
        want = [['Core Scanner Probe I (x4)', 'Scanner Probe'], ['Combat Scanner Probe I (x1)', 'Scanner Probe'], ['Mobile Depot (x1)', 'Mobile Depot'], ['Hobgoblin II (x5)', 'Combat Drone']]
        check(r['cards'][2] == ['Other contacts (4)', False] and sorted(r['other']) == sorted(want) and len(r['cards']) == 3,
              f"{W} px: one “Other contacts (4)” line after the ships, counts and group on hover {r['other']}")
        check(r['count'] == '2 ship type(s), 11 other line(s)' and r['ships'] == ['Caracal', 'Ferox'], f"{W} px: {r['count']!r}; the scan's ships {r['ships']}")
        check(r['over'] <= W, f'{W} px: nothing runs off the page ({r["over"]})')
        ctx.close()
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
