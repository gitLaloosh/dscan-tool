"""My Ship matchup scoreboard (v2026.10.14.41 strip; v2026.10.14.43 scoreboard inside the loss, option B of the
"Matchup placement" mockup; roadmap/my-ship-plan.md).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/matchup_strip_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The numbers are checked against pyfa by tools/independent_checks/check_matchup.py; this checks the page around them:
  * no scoreboard until a ship is saved and "Use in assessments" is on; then one board INSIDE the result box, above
    the cards: a threat half (DPS applied to you, how long they last), a middle (the edge, who is faster) and a
    my-ship half (how long you last, DPS applied to them), every value the page's own mysMatchup;
  * "DPS applied to you" is the Damage Application card's headline (names from CARD_NAMES, v2026.10.14.45); the edge goes to whoever outlasts the other;
  * moving the card's range slider updates it; the board is the same in the My ship view (click the other half);
  * a module-state change on my ship: the numbers that change turn amber (with the pasted fit's value on hover) and
    so do the changed numbers in the My ship view's cards; the Fit card's reset puts every number back, no amber;
  * Pilot losses: each loss has its own board inside its panel; the side shown stays when changing tabs;
  * phone (375 px): the two halves side by side, the edge and speed under them, sticky at the top, no sideways
    scrolling. No page errors.
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
Stasis Webifier II

Light Neutron Blaster II, Void S
Light Neutron Blaster II, Void S
Light Neutron Blaster II, Void S
Light Neutron Blaster II, Void S
Light Neutron Blaster II, Void S
"""
HECATE3 = HECATE.replace("Light Neutron Blaster II, Void S\nLight Neutron Blaster II, Void S\n", "", 1).replace("[Hecate, threat]", "[Hecate, three guns]")
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok
R = '#fitAnalyzerResults'
def cells(pg, scope=R):
    return pg.evaluate(f"() => Object.fromEntries([...document.querySelector('{scope} .mys-board').querySelectorAll('[data-cell]')].map(c => [c.dataset.cell, (c.querySelector('.mys-cell-v') || c).textContent]))")
EXPECT = """(scope) => { const host = document.querySelector(scope + ' .mys-switch-host'); const tf = mysStripThreatF(host);
  const m = mysMatchup(tf, myShip.f, tf.dmg || dmgDefaults(tf.estimate.application)); return Object.fromEntries(m.cells.map(c => [c.key, c.value])); }"""
ORDER = ['their', 'theyLast', 'edge', 'faster', 'youLast', 'your']   # threat half, middle, my-ship half
def settle(pg, ms=400):
    pg.wait_for_timeout(ms); pg.wait_for_function("() => !document.querySelector('.fit-card-busy')", timeout=60000); pg.wait_for_timeout(ms)

def desktop(b):
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML); pg.evaluate("localStorage.removeItem('dscanMyShip')"); pg.reload()
    pg.click('#tabBtnFit'); pg.fill('#fitAnalyzerInput', HECATE); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout'); settle(pg)
    check(pg.is_hidden(f'{R} .mys-switch-host') and pg.locator(f'{R} .mys-board').count() == 0, 'no ship saved: no scoreboard')
    pg.click('#myShipChip'); pg.fill('#myShipEft', VEXOR); pg.click('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-tiles'); pg.keyboard.press('Escape')
    pg.wait_for_function(f"() => {{ const b = document.querySelector('{R} .mys-board'); return b && !/…/.test(b.textContent); }}", timeout=60000); settle(pg, 600)
    c = cells(pg)
    check(list(c) == ORDER, f'six values in board order: {c}')
    check(c == pg.evaluate(EXPECT, R), 'every value is the page\'s own mysMatchup')
    check(c['their'] == pg.inner_text(f'{R} .fl-dmg [data-out="head"]'), f'"DPS applied to you" = the card headline ({c["their"]})')
    m = pg.evaluate(f"() => document.querySelector('{R} .mys-switch-host')._m")
    check(c['edge'] in ('edge: you', 'edge: threat', 'even', 'neither breaks') and pg.get_attribute(f'{R} .mys-edge', 'data-edge') == m['edge'], f'edge: {c["edge"]} (you last {c["youLast"]}, they last {c["theyLast"]})')
    bb, fl, box = pg.locator(f'{R} .mys-board').bounding_box(), pg.locator(f'{R} .mys-threat-view .fit-layout').bounding_box(), pg.locator(f'{R} .assess-box').bounding_box()
    check(box['y'] <= bb['y'] and bb['y'] + bb['height'] <= fl['y'] and bb['x'] >= box['x'], 'scoreboard inside the result box, above the cards')
    # the card's range slider moves the strip
    pg.evaluate("() => { const i = document.querySelector('#fitAnalyzerResults .fl-dmg input[data-in=\"range\"]'); i.value = 1500; i.dispatchEvent(new Event('input', {bubbles: true})); }"); pg.wait_for_timeout(200)
    c2 = cells(pg)
    check(c2['their'] == pg.inner_text(f'{R} .fl-dmg [data-out="head"]') and c2 != c and c2 == pg.evaluate(EXPECT, R) and pg.inner_text(f'{R} .mys-fight [data-fname="range"]') == '1.5 km' and pg.inner_text(f'{R} .mys-strip-note') == '',
          f'range slider: the board follows ({c["their"]} -> {c2["their"]})')
    # my ship view: same strip; change a state -> amber
    pg.click(f'{R} .mys-sw-btn.is-mine'); pg.wait_for_selector(f'{R} .mys-mine-view .fit-layout'); settle(pg)
    check(cells(pg) == c2 and pg.get_attribute(f'{R} .mys-sw-btn.is-mine', 'aria-pressed') == 'true', 'my ship view: the same board, my half pressed')
    # v2026.10.14.46 (bug list #1): no bar over the My Ship Perspective; its card edges are cyan, the threat's amber.
    # (computed styles still resolve inside the hidden perspective, so both are read without switching back; the
    # T3D Mode card has a plain grey edge in both perspectives on purpose)
    EDGES = """(sel) => { const v = document.querySelector(sel); const cs = getComputedStyle(v);
      const cols = [...v.querySelectorAll('.fit-summary:not(.td-mode-card), .ewar-card')].map(e => getComputedStyle(e).borderLeftColor);
      return {top: parseFloat(cs.borderTopWidth), pad: parseFloat(cs.paddingTop), cols: [...new Set(cols)], n: cols.length}; }"""
    em = pg.evaluate(EDGES, f'{R} .mys-mine-view'); et = pg.evaluate(EDGES, f'{R} .mys-threat-view')
    check(em['top'] == 0 and em['pad'] == 0 and em['n'] >= 5 and em['cols'] == ['rgb(79, 195, 217)'],
          f'My Ship Perspective: no top bar, every card edge cyan ({em})')
    check(et['n'] >= 5 and et['cols'] == ['rgb(138, 101, 41)'], f'Threat Perspective: card edges stay amber ({et})')
    check(pg.locator(f'{R} .is-changed').count() == 0, 'no amber before any change')
    # the Medium Armor Repairer off: "You last" must change (their DPS gets through faster)
    rep_id = pg.evaluate("() => myShip.f.estimate.moduleStates.items.find(i => /Armor Repairer/.test(i.name)).typeId")
    pg.locator(f'{R} .mys-mine-view .fl-fit button.ms-state[data-type-id="{rep_id}"][data-from="active"]').first.click(); settle(pg, 900)
    c3 = cells(pg); ch = pg.locator(f'{R} .mys-board .is-changed').count(); chv = pg.locator(f'{R} .mys-mine-view .is-changed').count()
    # v.58: a time's pasted value is at the end of its "why" panel (data-pasted), not in a native tooltip
    tip = pg.evaluate(f"() => {{ const c = document.querySelector('{R} .mys-board .is-changed'); return c ? (c.title || (c.dataset.pasted ? 'Your pasted fit: ' + c.dataset.pasted : '')) : ''; }}")
    check(c3 == pg.evaluate(EXPECT, R) and ch >= 1 and 'Your pasted fit:' in tip, f'state change: {ch} board values amber, hover "{tip}" ({c2} -> {c3})')
    check(chv >= 1, f'state change: {chv} changed numbers amber in the My ship view')
    pg.locator(f'{R} .mys-mine-view button.ms-reset').first.click(); settle(pg, 900)
    check(pg.locator(f'{R} .is-changed').count() == 0 and cells(pg) == c2, 'reset: numbers back, no amber')
    pg.click(f'{R} .mys-sw-btn.is-threat'); settle(pg)
    # Use in assessments off -> no strip
    pg.click('#myShipUseLabel'); pg.wait_for_timeout(300)
    check(pg.is_hidden(f'{R} .mys-switch-host'), '"Use in assessments" off: no scoreboard')
    pg.click('#myShipUseLabel'); pg.wait_for_selector(f'{R} .mys-board', timeout=60000)
    # Pilot losses: the strip follows the visible tab
    pg.click('#tabBtnPilot')
    run_async(pg, """async ([a, b]) => { const mk = async (text, day) => { const parsed = await parseEftFit(text);
        const est = await estimateHpAndDps(parsed.shipTypeId, parsed.tally, parsed.cargoItemIds, parsed.highSlotByFlag, 'sharpshooter', parsed.midSlotByFlag);
        return {parsed, fit: { km: {killmail_time: day}, killmailId: 1, tally: parsed.tally, highSlotByFlag: parsed.highSlotByFlag, estimate: est,
          input: {shipTypeId: parsed.shipTypeId, tally: parsed.tally, cargoItemIds: parsed.cargoItemIds, highSlotByFlag: parsed.highSlotByFlag, midSlotByFlag: parsed.midSlotByFlag} }}; };
        const x = await mk(a, '2026-10-01T00:00:00Z'), y = await mk(b, '2026-10-02T00:00:00Z');
        renderFitTabs('Test Pilot', 'Hecate', [x.fit, y.fit], x.parsed.idToName); }""", [HECATE, HECATE3])
    P = '#fitResults'
    V0, V1 = f'{P} .subtab-panel[data-idx="0"]', f'{P} .subtab-panel[data-idx="1"]'
    pg.wait_for_function(f"() => {{ const b = document.querySelector('{V0} .mys-board'); return b && !/…/.test(b.textContent); }}", timeout=60000); settle(pg)
    t1 = cells(pg, V0)
    pg.locator(f'{P} .subtab-btn').nth(1).click(); pg.wait_for_timeout(400)
    pg.wait_for_function(f"() => {{ const b = document.querySelector('{V1} .mys-board'); return b && !/…/.test(b.textContent); }}", timeout=60000)
    t2 = cells(pg, V1)
    check(t1 != t2 and t2 == pg.evaluate(EXPECT, V1), f'Pilot losses: each loss has its own board ({t1["your"]}/{t1["theyLast"]} -> {t2["your"]}/{t2["theyLast"]}; their DPS {t1["their"]} -> {t2["their"]})')
    pg.click(f'{V1} .mys-sw-btn.is-mine'); pg.wait_for_selector(f'{V1} .mys-mine-view .fit-layout', timeout=60000)
    pg.locator(f'{P} .subtab-btn').nth(0).click(); pg.wait_for_selector(f'{V0} .mys-mine-view .fit-layout', timeout=60000); settle(pg)
    check(pg.get_attribute(f'{V0} .mys-sw-btn.is-mine', 'aria-pressed') == 'true' and pg.is_hidden(f'{V0} .mys-threat-view') and pg.locator(f'{V1} .mys-mine-view .fit-layout').count() == 0,
          'Pilot losses: the side shown (my ship) stays when changing tabs; only the visible loss draws my ship')
    check(not errs, f'desktop: no page errors {errs}')
    ctx.close()

def phone(b):
    W = 375
    ctx = b.new_context(viewport={'width': W, 'height': 740}, is_mobile=True, has_touch=True); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML); pg.evaluate("localStorage.removeItem('dscanMyShip')"); pg.reload()
    pg.tap('#myShipChip'); pg.fill('#myShipEft', VEXOR); pg.tap('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-tiles')
    pg.touchscreen.tap(W // 2, 40); pg.wait_for_timeout(200)
    pg.tap('#tabBtnFit'); pg.fill('#fitAnalyzerInput', HECATE); pg.tap('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .mys-board', timeout=60000); settle(pg)
    pg.wait_for_function(f"() => {{ const b = document.querySelector('{R} .mys-board'); return b && !/…/.test(b.textContent); }}", timeout=60000)
    th, mi, mid = [pg.locator(f'{R} {x}').bounding_box() for x in ('.mys-sw-btn.is-threat', '.mys-sw-btn.is-mine', '.mys-mid')]
    check(abs(th['y'] - mi['y']) < 1 and th['height'] >= 44 and mid['y'] >= th['y'] + th['height'] - 1 and pg.is_visible(f'{R} .mys-edge'),
          f'phone: two halves side by side, the edge and speed under them')
    pg.evaluate('window.scrollTo(0, 2500)'); pg.wait_for_timeout(200)
    top = pg.locator(f'{R} .mys-switch-host').bounding_box()['y']
    check(0 <= top < 4, f'phone: the board stays at the top when scrolling ({top:.0f} px)')
    sw = pg.evaluate('document.documentElement.scrollWidth'); check(sw <= W, f'phone: no sideways scroll ({sw})')
    check(not errs, f'phone: no page errors {errs}')
    ctx.close()

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('CHROMIUM', '/opt/pw-browsers/chromium'))
    desktop(b); phone(b)
    b.close()
print(f'FAILURES: {fails}')
