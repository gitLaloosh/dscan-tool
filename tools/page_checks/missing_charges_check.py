"""Page check (v2026.10.14.24, the owner option A): a pasted fit (Fit Analyzer) whose Capacitor Booster or Ancillary
Shield Booster has no charge loaded and none in cargo is EMPTY -- no injection / the ASB runs on capacitor --
and the Weaknesses card flags "No charges for its <module>". Goes through the real page: EFT paste ->
parseEftFit -> estimateHpAndDps(..., {fitSource: 'eft'}), then a module-state change (recomputeFitWithStates)
must keep the rule. A charge in cargo counts (no flag).

    PYFA_SRC=/path/to/pyfa python3 tools/page_checks/missing_charges_check.py [index.html]

Ends with 'FAILURES: N' (must be 0).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esi_from_sde import route_all
from playwright.sync_api import sync_playwright
CB = """[Rifter, cap booster test]
Small Armor Repairer II

Small Capacitor Booster II
1MN Afterburner II
"""
CB_CARGO = CB + "\n\n\nCap Booster 150 x20\n"
ASB = """[Rifter, asb test]

Small Ancillary Shield Booster
1MN Afterburner II
"""
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
html = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))); bad = []
CHROMIUM = os.environ.get('CHROMIUM_PATH') or ('/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') else None)
def check(c, msg):
    print(('OK   ' if c else 'FAIL ') + msg)
    if not c: bad.append(msg)
with sync_playwright() as p:
    b = p.chromium.launch(**({'executable_path': CHROMIUM} if CHROMIUM else {}))
    pg = b.new_page(viewport={'width': 1440, 'height': 900}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg)
    pg.goto('file://' + html); pg.click('#tabBtnFit')
    def paste(text):
        pg.evaluate("() => { const r = document.querySelector('#fitAnalyzerResults'); if(r) r.innerHTML = ''; }")
        pg.fill('#fitAnalyzerInput', text); pg.click('#fitAnalyzerBtn')
        pg.wait_for_function("() => document.querySelector('#fitAnalyzerResults .fit-layout')", timeout=30000); pg.wait_for_timeout(500)
        return pg.inner_text('#fitAnalyzerResults')
    t = paste(CB)
    check('No charges for its Small Capacitor Booster II' in t, 'cap booster, no charges: Weaknesses card flag')
    check('has no charges in the fit, not injecting' in t, 'cap booster, no charges: Capacitor card caption')
    check('injecting +' not in t, 'cap booster, no charges: no injection shown')
    # a module-state change recalculates through recomputeFitWithStates -- the rule must survive it
    n0 = pg.evaluate("() => document.querySelectorAll('#fitAnalyzerResults button.ms-state').length")
    clicked = pg.evaluate("""() => { const b = [...document.querySelectorAll('#fitAnalyzerResults button.ms-state')].find(x => /Afterburner/.test(x.getAttribute('title') || x.textContent));
      if(!b) return false; b.click(); return true; }""")
    pg.wait_for_timeout(1200)
    t2 = pg.inner_text('#fitAnalyzerResults')
    check(clicked and 'No charges for its Small Capacitor Booster II' in t2, f'flag kept after a module-state change (state buttons {n0})')
    t = paste(CB_CARGO)
    check('No charges for its' not in t, 'charge in cargo: no flag')
    check('injecting +8.8 GJ/s' in t, 'charge in cargo: 8.8 GJ/s injected (Cap Booster 150 from cargo)')
    t = paste(ASB)
    check('No charges for its Small Ancillary Shield Booster' in t, 'ASB, no charges: Weaknesses card flag')
    check('has no charges in the fit, running on capacitor' in t, 'ASB, no charges: Capacitor card caption')
    check(pg.evaluate("() => !document.querySelector('#fitAnalyzerResults button.cap-asb-toggle')"), 'ASB, no charges: no out-of-charges toggle (it already is)')
    check(not errs, f'no page errors {errs}')
    b.close()
print(f'FAILURES: {len(bad)}')
