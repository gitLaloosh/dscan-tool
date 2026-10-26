"""Weaknesses "your guns" / "their guns" (v2026.10.14.42; roadmap/my-ship-plan.md phase 2b, decisions B1-B4).
v2026.10.14.58: the "your guns" / "their guns" tags are gone; the card's title says whose weaknesses it shows,
"Threat Weaknesses" (the threat's view, and with no ship saved) or "Your Weaknesses" (My ship view, "Viewing my ship").

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/weakness_picks_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The numbers are checked against pyfa by tools/independent_checks/check_weakness_picks.py; this checks the page around them:
  * no ship saved: the generic tiles, no picks, "Threat Weaknesses";
  * ship saved, "Use in assessments" on: the threat view ("Threat Weaknesses") shows your ammo / drones (the generic tiles
    are hidden); every tile is the page's own wpRank of wpCandidates at the strip's fight; the range slider re-ranks;
  * My ship view: "Your Weaknesses", "What the <threat> should use against you" and the threat's own ammo;
  * a collapsed Weaknesses card shows the picks in its summary row;
  * a state change on my ship: no amber inside the picks (they are not compared, M6) and the picks follow the change;
  * Pilot losses: the My ship view's picks follow the visible loss tab;
  * "Use in assessments" off: the generic tiles come back; "Viewing my ship" in the Fit Analyzer keeps the generic tiles;
  * phone (375 px): the picks show on the open Weaknesses card, no sideways scrolling. No page errors.
"""
import sys, os
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
Hobgoblin II x5

Null M x1000
Antimatter Charge M x1000
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


Null S x1000
Antimatter Charge S x500
"""
HECATE3 = HECATE.replace("Light Neutron Blaster II, Void S\nLight Neutron Blaster II, Void S\n", "", 1).replace("[Hecate, threat]", "[Hecate, three guns]")
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok
R = '#fitAnalyzerResults'
# The page's own picks for the visible fight, as [label, value, sub] per tile (threat view: side 'yours', My ship view: 'theirs').
EXPECT = """async ([scope, side]) => {
  const host = document.querySelector(scope + ' .mys-switch-host'); const tf = mysStripThreatF(host);
  const st = tf.dmg || dmgDefaults(tf.estimate.application); const F = mysFight(tf, myShip.f, st);
  const c = await wpCandidates(side === 'yours' ? myShip.f : tf);
  const r = side === 'yours' ? wpRank(c, F.mApp, F.them, F.qOut, tf.estimate) : wpRank(c, F.tApp, F.me, F.qIn, myShip.f.estimate);
  const d = document.createElement('div'); d.innerHTML = wpCardHtml(r, side, 'x', '');
  return [...d.querySelectorAll('.wp-stat')].map(t => [...t.querySelectorAll('.rec-label, .wp-value, .wp-sub')].map(e => e.textContent));
}"""
def tiles(pg, sel):
    return pg.evaluate(f"() => [...document.querySelectorAll('{sel} .weak-picks .wp-stat')].map(t => [...t.querySelectorAll('.rec-label, .wp-value, .wp-sub')].map(e => e.textContent))")
def settle(pg, ms=400):
    pg.wait_for_timeout(ms); pg.wait_for_function("() => !document.querySelector('.fit-card-busy')", timeout=60000); pg.wait_for_timeout(ms)
def vis(pg, sel): return pg.locator(sel).count() > 0 and pg.locator(sel).first.is_visible()
def title(pg, scope):   # v.58: the Weaknesses card's title as shown (one of "Threat" / "Your" is hidden by CSS)
    sel = f'{scope} button.cc-toggle[data-card="weak"]'
    return ' '.join(pg.inner_text(sel).split()).lower() if pg.locator(sel).count() else '' 
TV, MV = f'{R} .mys-threat-view', f'{R} .mys-mine-view'

def desktop(b):
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML); pg.evaluate("localStorage.removeItem('dscanMyShip')"); pg.reload()
    pg.click('#tabBtnFit'); pg.fill('#fitAnalyzerInput', HECATE); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout'); settle(pg)
    check(vis(pg, f'{TV} .weak-generic') and not vis(pg, f'{TV} .weak-picks') and pg.locator(f'{R} .wp-tag').count() == 0 and title(pg, TV) == 'threat weaknesses',
          f'no ship saved: generic tiles, no picks, no tag, "{title(pg, TV)}"')
    pg.click('#myShipChip'); pg.fill('#myShipEft', VEXOR); pg.click('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-tiles'); pg.keyboard.press('Escape')
    pg.wait_for_selector(f'{TV} .weak-picks .wp-stat', timeout=60000); settle(pg, 600)
    check(title(pg, TV) == 'threat weaknesses' and pg.locator(f'{R} .wp-tag').count() == 0 and not vis(pg, f'{TV} .weak-generic'), f'threat view: "{title(pg, TV)}", generic tiles hidden')
    t1 = tiles(pg, TV)
    check(t1 == pg.evaluate(EXPECT, [R, 'yours']) and len(t1) == 2 and t1[0][0].startswith('Your Heavy Neutron Blaster II') and t1[1][0] == 'Your drones',
          f'threat view: your blasters and your drones, each the page\'s own wpRank ({t1})')
    # v2026.10.14.49 (subtext rule 2): how the picks are ranked is in the card's info panel, not a note under them
    head = pg.inner_text(f'{TV} .wp-head'); info = pg.evaluate("() => CARD_INFO.weak.join(' ')")
    check('against the Hecate' in head and pg.locator(f'{TV} .wp-note').count() == 0 and pg.locator(f'{TV} details.info-pop[data-info="weak"]').count() >= 1
          and 'Only the ammo, drones and fighters aboard' in info and '{card:dmg}' in info, f'threat view: head "{head}", ranking explained behind the info button')
    # sitting still at 1 km your blasters apply; then the range slider re-ranks them (Void M close, Null M further out)
    pg.locator(f'{R} .fl-dmg button[data-seg="You"][data-v="still"]').click(); pg.wait_for_timeout(300)
    pg.evaluate("() => { const i = document.querySelector('#fitAnalyzerResults .fl-dmg input[data-in=\"range\"]'); i.value = 1000; i.dispatchEvent(new Event('input', {bubbles: true})); }"); pg.wait_for_timeout(400)
    t2 = tiles(pg, TV)
    pg.evaluate("() => { const i = document.querySelector('#fitAnalyzerResults .fl-dmg input[data-in=\"range\"]'); i.value = 9000; i.dispatchEvent(new Event('input', {bubbles: true})); }"); pg.wait_for_timeout(400)
    t3 = tiles(pg, TV)
    check(t2 != t1 and t3 != t2 and t3 == pg.evaluate(EXPECT, [R, 'yours']) and t2[0][1] != 'Out of reach' and '9 km' in (pg.get_attribute(f'{TV} .weak-picks .wp-stat', 'title') or ''),
          f'still, range slider: the picks follow (1 km {t2[0][1:]} -> 9 km {t3[0][1:]})')
    # My ship view: their guns
    pg.click(f'{R} .mys-sw-btn.is-mine'); pg.wait_for_selector(f'{MV} .weak-picks .wp-stat', timeout=60000); settle(pg)
    m1 = tiles(pg, MV)
    check(title(pg, MV) == 'your weaknesses' and pg.locator(f'{R} .wp-tag').count() == 0 and 'What the Hecate should use against you' in pg.inner_text(f'{MV} .wp-head'),
          f'My ship view: "{title(pg, MV)}" and "What the Hecate should use against you"')
    check(m1 == pg.evaluate(EXPECT, [R, 'theirs']) and len(m1) == 1 and m1[0][0] == 'Their Light Neutron Blaster II ×5' and ' DPS · you ' in m1[0][2] and 'DPS applied to you' in (pg.get_attribute(f'{MV} .weak-picks .wp-stat', 'title') or ''),
          f'My ship view: their blasters, the page\'s own wpRank ({m1})')
    # a state change on my ship (Drone Damage Amplifier off): nothing amber inside the picks; back in the threat
    # view your drone pick has followed the change
    dda = pg.evaluate("() => myShip.f.estimate.moduleStates.items.find(i => /Drone Damage Amplifier/.test(i.name)).typeId")
    pg.locator(f'{MV} .fl-fit button.ms-state[data-type-id="{dda}"]').first.click(); settle(pg, 900)
    pg.wait_for_selector(f'{MV} .weak-picks .wp-stat', timeout=60000); settle(pg)
    amber = pg.locator(f'{MV} .is-changed').count()
    check(tiles(pg, MV) == pg.evaluate(EXPECT, [R, 'theirs']) and amber > 0 and pg.locator(f'{MV} .weak-picks .is-changed').count() == 0,
          f'DDA off: {amber} numbers amber on the cards, none inside the picks')
    pg.click(f'{R} .mys-sw-btn.is-threat'); pg.wait_for_timeout(300); pg.wait_for_selector(f'{TV} .weak-picks .wp-stat'); settle(pg)
    t4 = tiles(pg, TV)
    check(t4 == pg.evaluate(EXPECT, [R, 'yours']) and t4[1][2] != t3[1][2], f'DDA off: your drone pick follows ({t3[1][2]} -> {t4[1][2]})')
    pg.click(f'{R} .mys-sw-btn.is-mine'); pg.wait_for_selector(f'{MV} .fit-layout'); settle(pg)
    pg.locator(f'{MV} button.ms-reset').first.click(); settle(pg, 900)
    # collapsed card: the picks in the summary row
    pg.locator(f'{MV} button.cc-toggle[data-card="weak"]').first.click(); pg.wait_for_timeout(600)
    sumv = pg.inner_text(f'{MV} button.cc-row[data-card="weak"] .wp-sum') if pg.locator(f'{MV} button.cc-row[data-card="weak"] .wp-sum').count() else ''
    check(sumv.startswith('their ') and m1[0][1] in sumv and not vis(pg, f'{MV} button.cc-row[data-card="weak"] .cc-sum') and title(pg, MV).startswith('your weaknesses'),
          f'collapsed Weaknesses: "{title(pg, MV)[:16]}", summary "{sumv}"')
    pg.locator(f'{MV} button.cc-toggle[data-card="weak"]').first.click(); pg.wait_for_timeout(300)
    pg.click(f'{R} .mys-sw-btn.is-threat'); settle(pg)
    # Use in assessments off -> generic tiles
    pg.click('#myShipUseLabel'); pg.wait_for_timeout(400)
    check(vis(pg, f'{TV} .weak-generic') and not vis(pg, f'{TV} .weak-picks') and title(pg, TV) == 'threat weaknesses', '"Use in assessments" off: generic tiles back')
    pg.click('#myShipUseLabel'); pg.wait_for_selector(f'{TV} .weak-picks .wp-stat', timeout=60000)
    # Pilot losses: their picks follow the visible tab
    pg.click('#tabBtnPilot')
    run_async(pg, """async ([a, b]) => { const mk = async (text, day) => { const parsed = await parseEftFit(text);
        const est = await estimateHpAndDps(parsed.shipTypeId, parsed.tally, parsed.cargoItemIds, parsed.highSlotByFlag, 'sharpshooter', parsed.midSlotByFlag);
        return {parsed, fit: { km: {killmail_time: day}, killmailId: 1, tally: parsed.tally, highSlotByFlag: parsed.highSlotByFlag, estimate: est,
          input: {shipTypeId: parsed.shipTypeId, tally: parsed.tally, cargoItemIds: parsed.cargoItemIds, highSlotByFlag: parsed.highSlotByFlag, midSlotByFlag: parsed.midSlotByFlag} }}; };
        const x = await mk(a, '2026-10-01T00:00:00Z'), y = await mk(b, '2026-10-02T00:00:00Z');
        renderFitTabs('Test Pilot', 'Hecate', [x.fit, y.fit], x.parsed.idToName); }""", [HECATE, HECATE3])
    P = '#fitResults'
    V0, V1 = f'{P} .subtab-panel[data-idx="0"]', f'{P} .subtab-panel[data-idx="1"]'   # v.43: each loss is its own panel
    pg.wait_for_selector(f'{V0} .mys-board', timeout=60000); settle(pg)
    pg.click(f'{V0} .mys-sw-btn.is-mine'); pg.wait_for_selector(f'{V0} .mys-mine-view .weak-picks .wp-stat', timeout=60000); settle(pg)
    p1 = tiles(pg, f'{V0} .mys-mine-view')
    pg.locator(f'{P} .subtab-btn').nth(1).click(); pg.wait_for_selector(f'{V1} .mys-mine-view .weak-picks .wp-stat', timeout=60000); settle(pg)
    p2 = tiles(pg, f'{V1} .mys-mine-view')
    check(p1 and p2 and p1[0][0].endswith('×5') and p2[0][0].endswith('×3') and p2 == pg.evaluate(EXPECT, [V1, 'theirs']), f'Pilot losses: their picks follow the visible tab ({p1[0][0]} -> {p2[0][0]})')
    pg.click(f'{V1} .mys-sw-btn.is-threat'); pg.wait_for_selector(f'{V1} .mys-threat-view .weak-picks .wp-stat', timeout=60000); settle(pg)
    yp = tiles(pg, f'{V1} .mys-threat-view')
    check(yp == pg.evaluate(EXPECT, [V1, 'yours']) and len(yp) == 2, 'Pilot losses: your picks on the visible loss')
    # Viewing my ship (Fit Analyzer): no opponent, generic tiles
    pg.click('#tabBtnFit'); pg.click('#myShipChip'); pg.click('#myShipPanel [data-act="open"]'); pg.wait_for_selector(f'{R} .fit-layout'); settle(pg)
    pg.keyboard.press('Escape')
    check(vis(pg, f'{R} .weak-generic') and not vis(pg, f'{R} .weak-picks') and title(pg, R) == 'your weaknesses', f'"Viewing my ship": generic tiles (no opponent), "{title(pg, R)}"')
    check(not errs, f'desktop: no page errors {errs}')
    ctx.close()

def phone(b):
    W = 375
    ctx = b.new_context(viewport={'width': W, 'height': 740}, is_mobile=True, has_touch=True); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML); pg.evaluate("localStorage.removeItem('dscanMyShip')"); pg.reload()
    pg.tap('#myShipChip'); pg.fill('#myShipEft', VEXOR); pg.tap('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-tiles')
    pg.touchscreen.tap(W // 2, 40); pg.wait_for_timeout(200)
    pg.tap('#tabBtnFit'); pg.fill('#fitAnalyzerInput', HECATE); pg.tap('#fitAnalyzerBtn'); pg.wait_for_selector(f'{TV} .weak-picks .wp-stat', timeout=60000); settle(pg)
    box = pg.locator(f'{TV} .weak-picks').bounding_box()
    check(vis(pg, f'{TV} .weak-picks .wp-stat') and box['x'] >= 0 and box['x'] + box['width'] <= W, f'phone: picks on the open Weaknesses card ({box["width"]:.0f} px wide)')
    sw = pg.evaluate('document.documentElement.scrollWidth'); check(sw <= W, f'phone: no sideways scroll ({sw})')
    check(not errs, f'phone: no page errors {errs}')
    ctx.close()

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('CHROMIUM', '/opt/pw-browsers/chromium'))
    desktop(b); phone(b)
    b.close()
print(f'FAILURES: {fails}')
