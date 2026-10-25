"""My Ship, phase 1 (v2026.10.14.33; roadmap/my-ship-plan.md M1-M5, the "My ship" design canvas).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/my_ship_check.py [index.html]   -> 'FAILURES: N' (must be 0)

Loads the real page in Chromium (ESI served from pyfa's SDE, esi_from_sde.py) and checks:
  * the chip on every tab: "+ My Ship" with the switch disabled; paste, save, and the six-number summary equal
    the Fit Analyzer's own numbers for the same paste (EHP, DPS, lock range);
  * kept after a reload, with no ESI request until the ship is needed (only the chip's label is stored);
  * Open in Fit Analyzer ("Viewing my ship"); a module-state change is kept after a reload; reset clears it;
  * a threat in the Fit Analyzer and in the Pilot Analyzer: the threat <-> my ship switch, the threat keeps its
    own state change while my ship is shown, the scroll position is kept, a change to my ship there is kept too, "Use in assessments" off
    hides the switch; "Set as my ship" (keeps that fit's states, the button turns into "This is my ship");
  * Delete with the inline confirm; Escape and an outside click close the panel;
  * FIT-04 for a line that isn't recognized; MYSHIP-01 when the browser refuses storage, MYSHIP-02 (with FIT-03 inside) when the saved fit no longer
    resolves;
  * phone (375 px, mobile emulation): the chip above the tabs, the panel as a sheet at the bottom, the switch
    two columns wide and sticky, no sideways scrolling. No page errors anywhere.
"""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esi_from_sde import route_all, run_async
from playwright.sync_api import sync_playwright

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')),
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'index.html')))
VEXOR = """[Vexor, Brawl]
Damage Control II
Medium Armor Repairer II
Multispectrum Energized Membrane II
Drone Damage Amplifier II

50MN Microwarpdrive II
Warp Scrambler II
Stasis Webifier II

Heavy Neutron Blaster II, Void M
Heavy Neutron Blaster II, Void M
Heavy Neutron Blaster II, Void M

Medium Auxiliary Nano Pump I
Medium Auxiliary Nano Pump I
Medium Nanobot Accelerator I

Hammerhead II x5
"""
HECATE = """[Hecate, threat]
Magnetic Field Stabilizer II
Magnetic Field Stabilizer II
Damage Control II

5MN Microwarpdrive II
Medium Ancillary Shield Booster, Navy Cap Booster 50
Warp Scrambler II

Light Neutron Blaster II, Void S
Light Neutron Blaster II, Void S
Light Neutron Blaster II, Void S
Light Neutron Blaster II, Void S
Light Neutron Blaster II, Void S
"""
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok

def stored(pg):
    return pg.evaluate("() => { try { return JSON.parse(localStorage.getItem('dscanMyShip')); } catch(e) { return 'ERR'; } }")
def wait_idle(pg, scope):
    pg.wait_for_timeout(150)
    pg.wait_for_function(f"() => !document.querySelector('{scope} .fit-card-busy')", timeout=60000)
    pg.wait_for_timeout(150)
def first_state_btn(scope):
    return f"{scope} .fl-fit button.ms-state:not([disabled])"
def tile(pg, key):
    return pg.evaluate("(k) => { const t = [...document.querySelectorAll('#myShipPanel .mys-tile')].find(x => x.querySelector('.mys-tile-k').textContent.startsWith(k)); return t ? t.querySelector('.mys-tile-v').textContent : null; }", key)
def open_panel(pg):
    if pg.is_hidden('#myShipPanel'): pg.click('#myShipChip')
    pg.wait_for_selector('#myShipPanel:not([hidden])')
def wait_tiles(pg):
    pg.wait_for_function("() => { const v = document.querySelector('#myShipPanel .mys-tile-v'); return v && !/^[…—]$/.test(v.textContent); }", timeout=60000)

def main_desktop(b):
    ctx = b.new_context(viewport={'width': 1440, 'height': 900})
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    esi_calls = []; pg.on('request', lambda r: esi_calls.append(r.url) if 'esi.evetech.net' in r.url else None)
    route_all(pg)
    pg.goto('file://' + HTML)
    pg.evaluate("localStorage.removeItem('dscanMyShip')"); pg.reload()
    # empty state, on every tab
    for tab in ('#tabBtnDscan', '#tabBtnPilot', '#tabBtnFit'):
        pg.click(tab)
        check(pg.is_visible('#myShipChip') and 'My Ship' in pg.inner_text('#myShipChip'), f'{tab}: "+ My Ship" chip visible')
    check(pg.is_disabled('#myShipUse'), 'empty: "Use in assessments" disabled')
    pg.click('#myShipChip')
    check(pg.is_visible('#myShipPanel') and pg.evaluate("document.activeElement && document.activeElement.id") == 'myShipEft', 'empty: panel opens with the paste box focused')
    pg.click('#myShipPanel [data-act="save"]')
    check(pg.inner_text('#myShipPanelStatus').strip() == 'Paste a fit first.', 'empty paste: "Paste a fit first." (a prompt, no code)')
    pg.fill('#myShipEft', 'not a fit')
    pg.click('#myShipPanel [data-act="save"]'); pg.wait_for_timeout(300)
    check('(FIT-02)' in pg.inner_text('#myShipPanelStatus'), f'bad paste: FIT-02 ({pg.inner_text("#myShipPanelStatus")[:60]!r})')
    pg.fill('#myShipEft', VEXOR)
    pg.click('#myShipPanel [data-act="save"]')
    pg.wait_for_selector('#myShipPanel .mys-tiles'); wait_tiles(pg)
    chip = pg.inner_text('#myShipChip')
    check('Vexor' in chip and 'Brawl' in chip, f'saved: chip shows the ship and fit ({chip!r})')
    check(not pg.is_disabled('#myShipUse') and pg.is_checked('#myShipUse'), 'saved: switch enabled and on')
    rec = stored(pg)
    check(rec and rec.get('eft') == VEXOR and rec.get('shipName') == 'Vexor' and rec.get('use') is True and rec.get('v') == 1, 'saved: stored record (EFT text, ship, switch)')
    check(rec and 'estimate' not in json.dumps(rec) and len(json.dumps(rec)) < 4000, 'saved: numbers are not stored (recomputed on load)')
    ref = pg.evaluate("""async (t) => { const {f} = await buildFitFromEft(t); const e = f.estimate;
        return {ehp: e.totalHP.toLocaleString(), dps: e.dpsFixed.toLocaleString(), lock: kmText(e.exact ? e.exact.targetingRange : e.targetingRange) + ' km',
                spd: e.speed.boosted.toLocaleString() + ' m/s'}; }""", VEXOR)
    check(tile(pg, 'EHP') == ref['ehp'], f"summary EHP = Fit Analyzer's ({tile(pg, 'EHP')} vs {ref['ehp']})")
    check(tile(pg, 'DPS') == ref['dps'], f"summary DPS = Fit Analyzer's ({tile(pg, 'DPS')} vs {ref['dps']})")
    check(tile(pg, 'Lock range') == ref['lock'], f"summary lock range = Fit Analyzer's ({tile(pg, 'Lock range')})")
    check(tile(pg, 'Speed, MWD on') == ref['spd'], f"summary speed with MWD = Fit Analyzer's ({tile(pg, 'Speed, MWD on')})")
    check(pg.is_visible('#myShipPanel [data-act="open"]') and pg.is_visible('#myShipPanel [data-act="copy"]') and pg.is_visible('#myShipPanel [data-act="replace"]'), 'summary: Open in Fit Analyzer, Replace, Copy EFT')
    pg.keyboard.press('Escape')
    check(pg.is_hidden('#myShipPanel') and pg.evaluate("document.activeElement.id") == 'myShipChip', 'Escape closes the panel, focus back on the chip')
    # reload: kept, and no ESI request until it is needed
    esi_calls.clear(); pg.reload(); pg.wait_for_timeout(600)
    check('Vexor' in pg.inner_text('#myShipChip'), 'reload: chip still shows my ship')
    check(not [u for u in esi_calls if '/universe/' in u], f'reload: no ESI request on page load ({len(esi_calls)})')
    open_panel(pg); wait_tiles(pg)
    check(tile(pg, 'EHP') == ref['ehp'], 'reload: recomputed summary equals the first one')
    pg.mouse.click(30, 880)  # outside the panel
    check(pg.is_hidden('#myShipPanel'), 'outside click closes the panel')
    # Open in Fit Analyzer, change a module, reload, reset
    open_panel(pg); pg.click('#myShipPanel [data-act="open"]')
    pg.wait_for_selector('#fitAnalyzerResults .mys-banner')
    check(pg.is_visible('#tabFit') and 'Vexor' in pg.inner_text('#fitAnalyzerResults .mys-banner') and pg.evaluate("document.querySelector('#fitAnalyzerResults .mys-banner-k').textContent === CARD_NAMES.myshippage"), 'Open in Fit Analyzer: the Viewing My Ship banner (name from CARD_NAMES)')
    check(pg.locator('#fitAnalyzerResults .mys-switch-host').count() == 0 and pg.locator('#fitAnalyzerResults .mys-set').count() == 0, 'my ship view: no switch and no "Set as my ship"')
    R = '#fitAnalyzerResults'
    btn = pg.locator(first_state_btn(R)).first
    tid, frm, to = btn.get_attribute('data-type-id'), btn.get_attribute('data-from'), btn.get_attribute('data-to')
    btn.click(); wait_idle(pg, R)
    rec = stored(pg)
    check(rec and rec.get('moduleStates') and tid in rec['moduleStates'], f'module change kept with my ship (type {tid} {frm} -> {to})')
    pg.reload(); open_panel(pg); wait_tiles(pg)
    check('changed' in pg.inner_text('#myShipPanel .mys-states'), 'reload: panel says module states were changed')
    pg.click('#myShipPanel [data-act="open"]'); pg.wait_for_selector('#fitAnalyzerResults .mys-banner .mys-banner-v')
    pg.wait_for_selector(f'{R} .fl-fit .ms-state')
    st = pg.evaluate(f"(id) => [...document.querySelectorAll('{R} .fl-fit .ms-state[data-type-id=\"' + id + '\"]')].map(b => b.dataset.from)", tid)
    check(to in st, f'reload: the changed state is back ({st})')
    check(pg.locator(f'{R} button.ms-reset.is-custom').count() == 1, 'reload: reset icon active')
    pg.click(f'{R} button.ms-reset'); wait_idle(pg, R)
    rec = stored(pg)
    check(rec and not rec.get('moduleStates') and not rec.get('droneStates'), 'reset: stored states cleared')
    # a threat in the Fit Analyzer
    pg.click('#fitAnalyzerResults [data-act="mys-another"]')
    check(pg.inner_html('#fitAnalyzerResults').strip() == '', '"Analyze another fit" clears the view')
    pg.fill('#fitAnalyzerInput', HECATE); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .mys-threat-view .fit-layout')
    check(pg.is_visible(f'{R} .mys-board') and 'Hecate' in pg.inner_text(f'{R} .mys-sw-btn.is-threat') and 'Vexor' in pg.inner_text(f'{R} .mys-sw-btn.is-mine'), 'Fit Analyzer threat: switch shows Threat (Hecate) and My ship (Vexor)')
    check(pg.is_visible(f'{R} button.mys-set'), 'Fit Analyzer threat: "Set as my ship" button')
    T = f'{R} .mys-threat-view'
    tb = pg.locator(first_state_btn(T)).first; t_id, t_to = tb.get_attribute('data-type-id'), tb.get_attribute('data-to')
    tb.click(); wait_idle(pg, T)
    y0 = pg.locator(R).bounding_box()['y']; pg.evaluate(f'window.scrollTo(0, {y0 - 120})'); pg.wait_for_timeout(150); s0 = pg.evaluate('scrollY')
    pg.click(f'{R} .mys-sw-btn.is-mine'); pg.wait_for_selector(f'{R} .mys-mine-view .fit-layout'); pg.wait_for_timeout(150)
    check(abs(pg.evaluate('scrollY') - s0) <= 1, f"switching keeps the scroll position ({s0} -> {pg.evaluate('scrollY')})")
    check(pg.is_hidden(T) and pg.is_visible(f'{R} .mys-mine-view') and pg.get_attribute(f'{R} .mys-sw-btn.is-mine', 'aria-pressed') == 'true', 'switch to my ship: threat hidden, my ship shown')
    M = f'{R} .mys-mine-view'
    check('Heavy Neutron Blaster II' in pg.inner_html(f'{M} .fl-fit') and 'Light Neutron Blaster II' not in pg.inner_html(f'{M} .fl-fit'), 'my ship view shows the Vexor fit')
    mb = pg.locator(first_state_btn(M)).first; m_id = mb.get_attribute('data-type-id')
    mb.click(); wait_idle(pg, M)
    rec = stored(pg); check(rec and rec.get('moduleStates') and m_id in rec['moduleStates'], 'change made behind the switch kept with my ship')
    pg.click(f'{R} .mys-sw-btn.is-threat'); pg.wait_for_timeout(200)
    st = pg.evaluate(f"(id) => [...document.querySelectorAll('{T} .fl-fit .ms-state[data-type-id=\"' + id + '\"]')].map(b => b.dataset.from)", t_id)
    check(pg.is_visible(T) and t_to in st, f"back to the threat: the threat's own change is still there ({st})")
    pg.click('#myShipUseLabel'); pg.wait_for_timeout(150)
    check(pg.is_hidden(f'{R} .mys-switch-host') and stored(pg).get('use') is False, '"Use in assessments" off: switch hidden, stored')
    pg.click('#myShipUseLabel'); pg.wait_for_timeout(150)
    check(pg.is_visible(f'{R} .mys-board') and pg.get_attribute(f'{R} .mys-sw-btn.is-threat', 'aria-pressed') == 'true', '"Use in assessments" on again: switch back, on the threat')
    pg.click(f'{R} .mys-sw-btn.is-mine'); pg.wait_for_selector(f'{M} .fit-layout')
    # Pilot Analyzer threat
    pg.click('#tabBtnPilot')
    n = run_async(pg, """async (text) => { const parsed = await parseEftFit(text);
        const mk = async (day) => { const est = await estimateHpAndDps(parsed.shipTypeId, parsed.tally, parsed.cargoItemIds, parsed.highSlotByFlag, 'sharpshooter', parsed.midSlotByFlag);
          return { km: {killmail_time: day}, killmailId: 1, tally: parsed.tally, highSlotByFlag: parsed.highSlotByFlag, estimate: est,
            input: {shipTypeId: parsed.shipTypeId, tally: parsed.tally, cargoItemIds: parsed.cargoItemIds, highSlotByFlag: parsed.highSlotByFlag, midSlotByFlag: parsed.midSlotByFlag} }; };
        renderFitTabs('Test Pilot', 'Hecate', [await mk('2026-10-01T00:00:00Z'), await mk('2026-10-02T00:00:00Z')], parsed.idToName);
        return document.querySelectorAll('#fitResults .mys-threat-view .fit-layout').length; }""", HECATE)
    P = '#fitResults'
    check(n == 2 and pg.locator(f'{P} .assess-box > .subtab-panel[data-idx="0"] > .mys-switch-host > .mys-board').is_visible() and 'Test Pilot' in pg.inner_text(f'{P} .mys-sw-btn.is-threat'),
          'Pilot Analyzer: the scoreboard is inside the visible loss (Hecate · Test Pilot)')   # v2026.10.14.43
    pg.click(f'{P} .mys-sw-btn.is-mine'); pg.wait_for_selector(f'{P} .mys-mine-view .fit-layout')
    check(pg.is_visible(f'{P} .assess-tabs') and pg.is_hidden(f'{P} .subtab-panel[data-idx="0"] > .mys-threat-view'), 'Pilot Analyzer my ship: loss tabs stay, the loss shows my ship')
    st = pg.evaluate(f"(id) => [...document.querySelectorAll('{P} .mys-mine-view .fl-fit .ms-state[data-type-id=\"' + id + '\"]')].map(b => b.dataset.from)", m_id)
    check(len(st) > 0 and st == pg.evaluate("(id) => moduleCopyStates(myShip.f.estimate.moduleStates.items.find(i => i.typeId == id), (myShip.f.moduleCopyOrder || {})[id])", m_id),
          f'Pilot Analyzer my ship shows the change made in the Fit Analyzer ({st})')
    # a change here, then back to the Fit Analyzer: that view is redrawn (stale-view refresh)
    pb = pg.locator(f'{P} .mys-mine-view .fl-fit button.ms-state[data-type-id="{m_id}"]').first
    p_to = pb.get_attribute('data-to'); pb.click(); wait_idle(pg, f'{P} .mys-mine-view')
    pg.click('#tabBtnFit'); pg.wait_for_timeout(200)
    st = pg.evaluate(f"(id) => [...document.querySelectorAll('{M} .fl-fit .ms-state[data-type-id=\"' + id + '\"]')].map(b => b.dataset.from)", m_id)
    check(p_to in st, f'Fit Analyzer my ship view redrawn after a change on the Pilot tab ({st})')
    # Set as my ship (Hecate, with its changed state)
    pg.click(f'{R} .mys-sw-btn.is-threat'); pg.click(f'{R} button.mys-set'); pg.wait_for_timeout(300)
    rec = stored(pg)
    check('Hecate' in pg.inner_text('#myShipChip') and rec.get('eft') == HECATE and rec.get('moduleStates') and t_id in rec['moduleStates'], '"Set as my ship": Hecate saved with its changed states')
    check(pg.locator(f'{R} .mys-is-tag').count() == 1, '"Set as my ship" turns into "This is my ship"')
    check('Hecate' in pg.inner_text(f'{P} .mys-sw-btn.is-mine'), 'switches elsewhere follow the new ship')
    # Delete
    open_panel(pg); wait_tiles(pg)
    pg.click('#myShipPanel [data-act="delete"]')
    check(pg.is_visible('#myShipPanel .mys-confirm'), 'Delete asks first (inline)')
    pg.click('#myShipPanel [data-act="delete-yes"]'); pg.wait_for_timeout(200)
    check(stored(pg) is None and 'Vexor' not in pg.inner_text('#myShipChip') and 'Hecate' not in pg.inner_text('#myShipChip') and pg.is_disabled('#myShipUse'), 'Delete: storage cleared, chip empty, switch disabled')
    check(pg.is_hidden(f'{R} .mys-switch-host') and pg.is_hidden(f'{P} .mys-switch-host') and pg.is_visible(f'{R} .mys-threat-view'), 'Delete: every switch hidden, threats shown')
    check('Deleted' in pg.inner_text('#myShipPanel'), 'Delete: panel says so and offers the paste box')
    check(not errs, f'desktop: no page errors {errs}')
    ctx.close()

def storage_blocked(b):
    ctx = b.new_context(viewport={'width': 1280, 'height': 900})
    ctx.add_init_script("Storage.prototype.setItem = function(){ throw new DOMException('blocked', 'SecurityError'); };")
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML)
    pg.click('#myShipChip'); pg.fill('#myShipEft', VEXOR + 'Not A Real Module II\n'); pg.click('#myShipPanel [data-act="save"]')
    pg.wait_for_selector('#myShipPanel .mys-tiles')
    txt = pg.inner_text('#myShipPanel')
    check('Not A Real Module II. (FIT-04)' in txt, 'unrecognized line: FIT-04 note in the panel')
    check('(MYSHIP-01)' in txt and 'kept until this page closes' in txt, 'storage blocked: MYSHIP-01, and the ship still works for this page')
    check('Vexor' in pg.inner_text('#myShipChip'), 'storage blocked: chip set')
    check(not errs, f'storage blocked: no page errors {errs}')
    ctx.close()

def unloadable(b):
    ctx = b.new_context(viewport={'width': 1280, 'height': 900})
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML)
    pg.evaluate("""localStorage.setItem('dscanMyShip', JSON.stringify({v: 1, eft: '[Notaship Xyz, gone]\\nDamage Control II', shipName: 'Notaship Xyz', fitName: 'gone', use: true, savedAt: '2026-10-23T00:00:00Z'}))""")
    pg.reload(); pg.click('#myShipChip')
    pg.wait_for_function("() => /MYSHIP-02/.test(document.getElementById('myShipPanel').innerText)", timeout=30000)
    txt = pg.inner_text('#myShipPanel')
    check('(MYSHIP-02)' in txt and 'FIT-03' in txt, f'unloadable saved fit: MYSHIP-02 with the underlying FIT-03 ({txt[txt.find("couldn"):][:110]!r})')
    check(stored(pg) is not None, 'unloadable saved fit: the saved text is kept')
    pg.evaluate("localStorage.setItem('dscanMyShip', '{not json')"); pg.reload(); pg.click('#myShipChip')
    check('(MYSHIP-02)' in pg.inner_text('#myShipPanel') and pg.is_visible('#myShipEft'), 'damaged stored copy: MYSHIP-02 and the paste box')
    check(not errs, f'MYSHIP-02: no page errors {errs}')
    ctx.close()

def phone(b):
    W = 375
    ctx = b.new_context(viewport={'width': W, 'height': 740}, is_mobile=True, has_touch=True)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML)
    chip, tab = pg.locator('#myShipChip').bounding_box(), pg.locator('#tabBtnDscan').bounding_box()
    check(chip['y'] + chip['height'] <= tab['y'] + 1 and chip['height'] >= 44, f'phone: chip above the tabs, finger-sized ({chip["height"]:.0f}px)')
    pg.tap('#myShipChip'); pg.wait_for_selector('#myShipPanel:not([hidden])')
    box = pg.locator('#myShipPanel').bounding_box()
    check(abs(box['y'] + box['height'] - 740) <= 1 and box['x'] <= 1 and box['width'] >= W - 1, f'phone: panel is a sheet at the bottom ({box})')
    check(pg.is_visible('#myShipBackdrop'), 'phone: backdrop behind the sheet')
    pg.fill('#myShipEft', VEXOR); pg.tap('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-tiles'); wait_tiles(pg)
    sw = pg.evaluate('document.documentElement.scrollWidth'); check(sw <= W, f'phone: no sideways scroll with the panel open ({sw})')
    pg.touchscreen.tap(W // 2, 40); pg.wait_for_timeout(150)  # the backdrop, above the sheet
    check(pg.is_hidden('#myShipPanel'), 'phone: tapping the backdrop closes the sheet')
    pg.tap('#tabBtnFit'); pg.fill('#fitAnalyzerInput', HECATE); pg.tap('#fitAnalyzerBtn'); pg.wait_for_selector('#fitAnalyzerResults .mys-threat-view .fit-layout')
    sb = [pg.locator(f'#fitAnalyzerResults .mys-sw-btn.{c}').bounding_box() for c in ('is-threat', 'is-mine')]
    check(abs(sb[0]['y'] - sb[1]['y']) < 1 and sb[0]['height'] >= 44, f'phone: scoreboard is two side-by-side buttons ({sb[0]["height"]:.0f}px)')
    pg.tap('#fitAnalyzerResults .mys-sw-btn.is-mine .mys-half-head'); pg.wait_for_selector('#fitAnalyzerResults .mys-mine-view .fit-layout')   # v.58: a tap on a time opens its why panel
    pg.evaluate('window.scrollTo(0, 1600)'); pg.wait_for_timeout(200)
    top = pg.locator('#fitAnalyzerResults .mys-switch-host').bounding_box()['y']
    check(abs(top) <= 1, f'phone: switch stays at the top when scrolling ({top:.0f})')
    sw = pg.evaluate('document.documentElement.scrollWidth'); check(sw <= W, f'phone: no sideways scroll with my ship shown ({sw})')
    pg.screenshot(path=os.path.join(os.environ.get('SHOTS', '/tmp'), 'myship_phone.png'))
    check(not errs, f'phone: no page errors {errs}')
    ctx.close()

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('CHROMIUM', '/opt/pw-browsers/chromium'))
    main_desktop(b); storage_blocked(b); unloadable(b); phone(b)
    b.close()
print(f'FAILURES: {fails}')
