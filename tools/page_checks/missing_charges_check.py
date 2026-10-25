"""Page check (v2026.10.14.24, the owner option A): a pasted fit (Fit Analyzer) whose Capacitor Booster or Ancillary
Shield Booster has no charge loaded and none in cargo is EMPTY -- no injection / the ASB runs on capacitor --
and the Weaknesses card flags "No charges for its <module>". Goes through the real page: EFT paste ->
parseEftFit -> estimateHpAndDps(..., {fitSource: 'eft'}), then a module-state change (recomputeFitWithStates)
must keep the rule. A charge in cargo counts (no flag). v2026.10.14.61: an Ancillary Armor Repairer with no Nanite Repair
Paste anywhere is flagged "No paste for its ..."; the Repairs strip's burst shows only with paste aboard, and on a killmail
with none seen as an assumed full clip (in its hover).

    PYFA_SRC=/path/to/pyfa python3 tools/page_checks/missing_charges_check.py [index.html]

Ends with 'FAILURES: N' (must be 0).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esi_from_sde import route_all, run_async
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
    # v2026.10.14.50 (subtext rule 1): the Capacitor card's caption is one short line; the sentence is its hover
    def caption():
        return pg.evaluate("() => { const c = document.querySelector('#fitAnalyzerResults .cap-ring-row .cap-gauge-caption .ctx'); return c ? [c.textContent, c.title] : ['', '']; }")
    t = paste(CB)
    check('No charges for its Small Capacitor Booster II' in t, 'cap booster, no charges: Weaknesses card flag')
    c = caption()
    check(c[0] == 'best case · booster has no charges' and 'has no charges in the fit, not injecting' in c[1], f'cap booster, no charges: Capacitor card caption {c}')
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
    c = caption()
    check(c[0] == 'best case · booster injecting' and 'injecting +8.8 GJ/s' in c[1] and 'from cargo' in c[1], f'charge in cargo: 8.8 GJ/s injected (Cap Booster 150 from cargo) {c}')
    t = paste(ASB)
    check('No charges for its Small Ancillary Shield Booster' in t, 'ASB, no charges: Weaknesses card flag')
    c = caption()
    check(c[0] == 'best case · ASB has no charges' and 'has no charges in the fit, running on capacitor' in c[1], f'ASB, no charges: Capacitor card caption {c}')
    check(pg.evaluate("() => !document.querySelector('#fitAnalyzerResults button.cap-asb-toggle')"), 'ASB, no charges: no out-of-charges toggle (it already is)')
    # v2026.10.14.61: an Ancillary Armor Repairer with no Nanite Repair Paste anywhere is flagged; the Repairs strip's burst
    # shows only with paste aboard (loaded or in cargo), and on a killmail with none seen, as an assumed full clip
    FITS = os.path.join(ROOT, 'tools', 'independent_checks', 'fits')
    vex = {v: open(os.path.join(FITS, f'vexor_aar_paste_{v}.eft'), encoding='utf-8').read() for v in ('loaded', 'cargo', 'none')}
    BURST = "(sel) => { const b = document.querySelector(sel + ' .repairs-bp-burst'); return b ? [b.textContent.trim(), b.closest('.repairs-bp').title] : null; }"
    for v in ('loaded', 'cargo', 'none'):
        t = paste(vex[v]); burst = pg.evaluate(BURST, '#fitAnalyzerResults')
        flag = pg.evaluate("() => { const r = [...document.querySelectorAll('#fitAnalyzerResults .charges-missing-row')].find(x => /paste/.test(x.textContent)); return r ? [r.querySelector('.warn-title').textContent, r.querySelector('.ctx').textContent] : null; }")
        if v == 'none':
            check(flag == ['No paste for its Medium Ancillary Armor Repairer', 'none aboard: no 3x paste boost'] and burst is None, f'AAR, no paste: flagged {flag}, no burst {burst}')
        else:
            check(flag is None and burst and burst[0].endswith('burst') and 'Nanite Repair Paste burst' in burst[1] and 'assumed' not in burst[1], f'AAR, paste {v}: no flag, burst {burst}')
    # a killmail (no fitSource) with no paste seen: the burst, as an assumed full clip
    pg.click('#tabBtnPilot')
    run_async(pg, """async (text) => { const parsed = await parseEftFit(text);
        const est = await estimateHpAndDps(parsed.shipTypeId, parsed.tally, parsed.cargoItemIds, parsed.highSlotByFlag, 'sharpshooter', parsed.midSlotByFlag);
        renderFitTabs('Test Pilot', 'Vexor', [{ km: {killmail_time: '2026-10-01T00:00:00Z'}, killmailId: 1, tally: parsed.tally, highSlotByFlag: parsed.highSlotByFlag, estimate: est,
          input: {shipTypeId: parsed.shipTypeId, tally: parsed.tally, cargoItemIds: parsed.cargoItemIds, highSlotByFlag: parsed.highSlotByFlag, midSlotByFlag: parsed.midSlotByFlag} }], parsed.idToName); }""", vex['none'])
    pg.wait_for_selector('#fitResults .fit-layout', timeout=30000); pg.wait_for_timeout(500)
    burst = pg.evaluate(BURST, '#fitResults')
    check(burst and 'assumed' in burst[1] and 'No paste for its' not in pg.inner_text('#fitResults'), f'AAR on a killmail, no paste seen: burst as an assumed clip, no flag {burst}')
    check(not errs, f'no page errors {errs}')
    b.close()
print(f'FAILURES: {len(bad)}')
