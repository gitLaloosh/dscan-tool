"""Damage Application, formerly "Their damage on you" (v2026.10.14.36; renamed v2026.10.14.45; roadmap/turret-application-plan.md Phase 2b, the "Their damage on you" canvas).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/damage_chart_check.py [index.html]   -> 'FAILURES: N' (must be 0)

Loads the real page in Chromium (ESI served from pyfa's SDE, esi_from_sde.py). The numbers themselves are checked
against pyfa by tools/independent_checks/check_damage_chart.py; this checks the page around them:
  * placement (FIT_LAYOUT, v2026.10.14.37): at 1440 px the card is at the top across the Fit and stats columns,
    Weaknesses beside it; at 1100 px full width on top, sliders beside the chart; on a phone first; scrolling
    through the layout the sticky Fit column never covers another area (LESSON #38); the My ship view (no
    card) starts its columns level;
  * Fit Analyzer, no ship saved: the card charts against the cruiser
    preset (Caracal + 50MN Microwarpdrive II), the headline is the card's own point for the engagement range
    (their optimal + falloff), both lines and the legend are drawn, "Show values" has the table, the Firepower card
    links to it;
  * every control redraws the card without running the fit engine (estimateHpAndDps not called), and Reset puts
    the defaults back; the MWD switch off at the scram range changes nothing (scrammed either way), on vs off
    changes the number away from it;
  * another class preset is kept after a reload; the card collapses and opens;
  * a saved ship (Use in assessments on) replaces the preset ("applied to your Vexor"), off brings the preset back;
  * drones charted (v2026.10.14.40): a Vexor's raw DPS counts its drones, its drone control range is marked;
  * a fit with no turrets / missiles / drones: the card says there is nothing to chart;
  * Pilot losses: each loss tab has its own card; the "My ship" view has none;
  * collapsed: the row's headline follows "Use in assessments" (v2026.10.14.47, bug list #1) and is there from
    the start on a phone;
  * v2026.10.14.48: Reset is a reserved icon (disabled at the defaults); the method text is behind the info button
    (panel over the page, Escape / outside press close it); Adjust is open on a loss tab that was hidden when drawn;
  * phone (375 px): the card starts collapsed, opens to a chart no wider than the screen, Adjust starts closed,
    no sideways scrolling. No page errors anywhere.
"""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esi_from_sde import route_all
from playwright.sync_api import sync_playwright

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')),
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'index.html')))
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
BESTOWER = """[Bestower, hauler]
Expanded Cargohold II

10MN Afterburner II
"""
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok

R = '#fitAnalyzerResults'
C = f'{R} .fl-dmg .dmg-card'
def ready(pg, scope=C):
    pg.wait_for_selector(f'{scope} [data-out="head"]:not(:empty)', timeout=60000); pg.wait_for_timeout(100)
def head(pg, scope=C):
    return pg.inner_text(f'{scope} [data-out="head"]')
# the card's own point for its current state, worked out again from the fit and the target (wiring, not maths)
EXPECT = """(sel) => { const card = document.querySelector(sel), c = card._dmg; const m = dmgModel(c.f, c.T, c.f.dmg);
  const app = m.app, tgt = dmgTargetObj(c.T.pt, c.f.dmg.prop, c.f.dmg.sigPct / 100);
  const p = {distance: c.f.dmg.range, tgtSpeed: m.ySpeed, tgtAngle: c.f.dmg.mode === 'orbit' ? 90 : 0, atkSpeed: m.tSpeed, atkAngle: c.f.dmg.theirMode === 'orbit' ? 90 : 0, ignoreLockRange: true};
  const pt = pyfaProjectedPoint(app, tgt, p);
  return dmgFmt(pyfaAppliedDps(app, Object.assign({}, p, {tgtSpeed: pt.tgtSpeed, tgtSigRadius: pt.tgtSigRadius, tgtRadius: tgt.radius}))); }"""
COUNT_ENGINE = "() => { if(!window.__est){ window.__est = 0; const o = estimateHpAndDps; estimateHpAndDps = function(){ window.__est++; return o.apply(this, arguments); }; } return window.__est; }"
def set_range(pg, sel, v):
    pg.evaluate("([s, v]) => { const i = document.querySelector(s); i.value = v; i.dispatchEvent(new Event('input', {bubbles: true})); }", [sel, str(v)])

def overlap(a, b):
    return a['x'] < b['x'] + b['width'] - 1 and b['x'] < a['x'] + a['width'] - 1 and a['y'] < b['y'] + b['height'] - 1 and b['y'] < a['y'] + a['height'] - 1
def no_overlap(pg, W):
    # LESSON #38: scroll through the whole layout; the sticky Fit column must never cover another area
    h = pg.evaluate(f"document.querySelector('{R} .fit-layout').getBoundingClientRect().bottom + scrollY")
    hits = []
    for y in range(0, int(h), 300):
        pg.evaluate(f'window.scrollTo(0, {y})'); pg.wait_for_timeout(30)
        fit = pg.locator(f'{R} .fl-fit').bounding_box()
        for k in ('dmg', 'beat', 'stats'):
            if pg.locator(f'{R} .fl-{k}').count() and overlap(fit, pg.locator(f'{R} .fl-{k}').bounding_box()): hits.append((y, k))
    pg.evaluate('window.scrollTo(0, 0)')
    check(not hits, f'{W}: scrolling through the layout, the sticky Fit column covers nothing {hits[:4]}')

def tablet(b):
    ctx = b.new_context(viewport={'width': 1100, 'height': 900})
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML)
    pg.evaluate("localStorage.removeItem('dscanMyShip'); localStorage.removeItem('dscanDmgPreset')"); pg.reload()
    pg.click('#tabBtnFit'); pg.fill('#fitAnalyzerInput', HECATE); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout'); ready(pg)
    b_ = {k: pg.locator(f'{R} .fl-{k}').bounding_box() for k in ('dmg', 'beat', 'fit', 'stats')}
    lay = pg.locator(f'{R} .fit-layout').bounding_box()
    check(abs(b_['dmg']['width'] - lay['width']) < 2 and b_['fit']['y'] >= b_['dmg']['y'] + b_['dmg']['height'] - 1 and abs(b_['fit']['y'] - b_['beat']['y']) < 2
          and b_['fit']['x'] < b_['beat']['x'], '1100: the card full width at the top, Fit left and the cards right below it')
    check(pg.locator(f'{C} .dmg-adjust[open]').count() == 1, '1100: the card is wide enough for the sliders beside the chart (Adjust open)')
    no_overlap(pg, '1100')
    sw = pg.evaluate('document.documentElement.scrollWidth'); check(sw <= 1100, f'1100: no sideways scroll ({sw})')
    check(not errs, f'1100: no page errors {errs}')
    ctx.close()

def desktop(b):
    ctx = b.new_context(viewport={'width': 1440, 'height': 900})
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML)
    pg.evaluate("localStorage.removeItem('dscanMyShip'); localStorage.removeItem('dscanDmgPreset')"); pg.reload()
    pg.click('#tabBtnFit'); pg.fill('#fitAnalyzerInput', HECATE); pg.click('#fitAnalyzerBtn')
    pg.wait_for_selector(f'{R} .fit-layout'); ready(pg)
    b_ = {k: pg.locator(f'{R} .fl-{k}').bounding_box() for k in ('dmg', 'beat', 'fit', 'stats')}
    check(abs(b_['dmg']['x'] - b_['fit']['x']) < 2 and abs(b_['dmg']['x'] + b_['dmg']['width'] - b_['stats']['x'] - b_['stats']['width']) < 2
          and abs(b_['dmg']['y'] - b_['beat']['y']) < 2 and b_['fit']['y'] >= b_['dmg']['y'] + b_['dmg']['height'] - 1 and abs(b_['fit']['y'] - b_['stats']['y']) < 2,
          '1440: the card at the top, across the Fit and stats columns, Weaknesses beside it (FIT_LAYOUT)')
    no_overlap(pg, '1440')
    vs = pg.inner_text(f'{C} .dmg-vs')
    check('typical cruiser' in vs and pg.get_attribute(f'{C} .dmg-chip[data-preset="cruiser"]', 'aria-pressed') == 'true'
          and 'Caracal with a 50MN Microwarpdrive II' in pg.inner_text(f'{C} .dmg-presets'), f'no ship saved: the cruiser preset ({vs})')
    st = pg.evaluate(f"() => document.querySelector('{C}')._dmg.f.dmg")
    rng = pg.evaluate(f"""() => {{ const app = document.querySelector('{C}')._dmg.f.estimate.application; const w = app.weapons.sort((a, b) => b.dps - a.dps)[0]; return Math.round((w.optimal + w.falloff) / 100) * 100; }}""")
    check(st['range'] == rng and st['mode'] == 'orbit' and st['prop'] is True, f'defaults: their optimal + falloff ({st["range"]} m), orbiting, MWD on')
    check(head(pg) == pg.evaluate(EXPECT, C), f'headline = the card\'s point ({head(pg)} DPS)')
    check(pg.locator(f'{C} polyline.dmg-still').count() == 1 and pg.locator(f'{C} polyline.dmg-move').count() == 1
          and pg.locator(f'{C} .dmg-legend .dmg-key').count() == 2, 'two lines and a two-entry legend')
    check(pg.locator(f'{C} .dmg-table tbody tr').count() == 7, '"Show values": a table of 7 rows')
    check(pg.locator(f'{C} .dmg-marker').count() >= 1 and 'scram' in pg.inner_text(f'{C} .dmg-chart'), 'markers: their scram range')
    fp = pg.inner_text(f'{R} .dmg-fp-slot')
    check(fp.startswith(head(pg) + ' DPS applied to a typical cruiser') and fp.strip().endswith('↑'), f'Firepower card links up to the chart ({fp})')
    # hover
    pg.locator(f'{C} [data-out="chart"]').scroll_into_view_if_needed()
    box = pg.locator(f'{C} [data-out="chart"]').bounding_box()
    pg.mouse.move(box['x'] + box['width'] * 0.4, box['y'] + box['height'] / 2); pg.wait_for_timeout(100)
    check(pg.is_visible(f'{C} .dmg-tip') and 'DPS' not in pg.inner_text(f'{C} .dmg-tip-t') and pg.locator(f'{C} .dmg-tip-r').count() == 2, 'hover: tooltip with both lines')
    # controls redraw without the fit engine
    n0 = pg.evaluate(COUNT_ENGINE)
    h0 = head(pg)
    set_range(pg, f'{C} input[data-in="range"]', 2000); h1 = head(pg)
    check(h1 != h0 and pg.inner_text(f'{C} [data-out="range"]') == '2 km' and head(pg) == pg.evaluate(EXPECT, C), f'range slider: redrawn ({h0} -> {h1} at 2 km)')
    pg.click(f'{C} button[data-seg="You"][data-v="still"]')
    check(head(pg) == pg.evaluate(EXPECT, C) and 'you still' in pg.inner_text(f'{C} [data-out="headText"]'), 'You: Still')
    pg.click(f'{C} button[data-seg="You"][data-v="orbit"]')
    set_range(pg, f'{C} input[data-in="sigPct"]', 200); h2 = head(pg)
    check(head(pg) == pg.evaluate(EXPECT, C) and '200%' in pg.inner_text(f'{C} [data-out="sig"]'), f'signature slider ({h2})')
    set_range(pg, f'{C} input[data-in="theirPct"]', 60)
    pg.click(f'{C} button[data-seg="Their heading"][data-v="orbit"]')
    check(head(pg) == pg.evaluate(EXPECT, C), 'their speed and heading')
    pg.click(f'{C} button[data-seg="Chart across"][data-v="speed"]')
    check(pg.locator(f'{C} polyline.dmg-still').count() == 0 and pg.locator(f'{C} .dmg-legend .dmg-key').count() == 1 and 'm/s' in pg.text_content(f'{C} .dmg-table'),
          'chart across your speed: one line, the table in m/s')
    pg.click(f'{C} button[data-seg="Chart across"][data-v="sig"]')
    check('Your signature' in pg.text_content(f'{C} .dmg-table thead') and re.search(r'\d m<', pg.inner_html(f'{C} .dmg-table tbody')), 'chart across your signature')
    # MWD switch: inside their scram range the MWD is off either way (the Hecate's blasters do nothing that far
    # out, so the speed and signature the card works with are compared, not the DPS)
    pg.click(f'{C} button[data-seg="Chart across"][data-v="distance"]')
    set_range(pg, f'{C} input[data-in="sigPct"]', 100); set_range(pg, f'{C} input[data-in="theirPct"]', 0)
    scram = pg.evaluate(f"() => document.querySelector('{C}')._dmg.f.estimate.application.projected.scramRange")
    cur = lambda: pg.evaluate(f"() => {{ const c = document.querySelector('{C}')._dmg; return [Math.round(c.m.cur.speed), Math.round(c.m.cur.sig)]; }}")
    set_range(pg, f'{C} input[data-in="range"]', int(scram // 100 * 100) - 500); a_on = cur()
    pg.click(f'{C} input[data-in="prop"]'); a_off = cur()
    pg.click(f'{C} input[data-in="prop"]')
    set_range(pg, f'{C} input[data-in="range"]', int(scram // 100 * 100) + 3000); b_on = cur()
    pg.click(f'{C} input[data-in="prop"]'); b_off = cur()
    check(a_on == a_off and b_on[0] > b_off[0] and b_on[1] > b_off[1], f'MWD switch: no change inside the scram ({a_on} / {a_off}), a change outside ({b_on} / {b_off}) [speed, signature]')
    check(pg.evaluate(COUNT_ENGINE) == n0, f'no fit-engine run for any control ({pg.evaluate(COUNT_ENGINE) - n0} runs)')
    # v2026.10.14.48 (subtext rule 4): Reset is an icon that is always there, enabled once a control moved
    check(pg.is_visible(f'{C} .dmg-reset') and pg.is_enabled(f'{C} .dmg-reset'), 'Reset enabled once a control moved')
    pg.click(f'{C} .dmg-reset'); ready(pg)
    st2 = pg.evaluate(f"() => document.querySelector('{C}')._dmg.f.dmg")
    check(st2 == st and pg.is_visible(f'{C} .dmg-reset') and pg.is_disabled(f'{C} .dmg-reset') and head(pg) == h0, f'Reset: the defaults back, the icon stays (disabled) ({head(pg)})')
    # v2026.10.14.48: how the card works is behind its info button, in a panel over the page
    info0 = pg.evaluate("CARD_INFO.dmg[0]")
    h_before = pg.locator(C).bounding_box()['height']
    check(info0 not in pg.inner_text(C), 'the method text is not on the card any more')
    pg.click(f'{C} summary.info-btn'); pg.wait_for_timeout(200)
    panel = pg.locator(f'{C} .info-body')
    check(panel.is_visible() and info0 in panel.inner_text() and pg.evaluate("CARD_INFO.dmg[2]") in panel.inner_text(),
          'info button opens the panel with the card\'s CARD_INFO text')
    pb = panel.bounding_box()
    check(pb['x'] >= 0 and pb['x'] + pb['width'] <= pg.viewport_size['width'], f"the open panel is inside the window ({pb['x']:.0f} to {pb['x'] + pb['width']:.0f} of {pg.viewport_size['width']})")
    check(abs(pg.locator(C).bounding_box()['height'] - h_before) < 1 and pg.evaluate(f"getComputedStyle(document.querySelector('{C} .info-body')).position") == 'absolute',
          'the panel floats over the page (the card keeps its height)')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    check(not panel.is_visible(), 'Escape closes the panel')
    pg.click(f'{C} summary.info-btn'); pg.wait_for_timeout(150); pg.mouse.click(5, 5); pg.wait_for_timeout(150)
    check(not panel.is_visible(), 'a press outside closes the panel')
    # a module-state change keeps the card state and redraws
    set_range(pg, f'{C} input[data-in="range"]', 5000)
    pg.locator(f'{R} .fl-fit button.ms-state:not([disabled])').first.click()
    pg.wait_for_timeout(300); pg.wait_for_function("() => !document.querySelector('#fitAnalyzerResults .fit-card-busy')", timeout=60000); ready(pg)
    check(pg.evaluate(f"() => document.querySelector('{C}')._dmg.f.dmg.range") == 5000 and head(pg) == pg.evaluate(EXPECT, C), 'module-state change: card kept its range and redrew')
    # another preset, kept after a reload
    pg.click(f'{C} .dmg-chip[data-preset="battleship"]'); pg.wait_for_function(f"() => /battleship/.test(document.querySelector('{C} .dmg-vs').textContent)", timeout=60000); ready(pg)
    check('Raven with a 500MN Microwarpdrive II' in pg.inner_text(f'{C} .dmg-presets') and head(pg) == pg.evaluate(EXPECT, C), f'battleship preset ({head(pg)} DPS)')
    pg.reload(); pg.click('#tabBtnFit'); pg.fill('#fitAnalyzerInput', HECATE); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout'); ready(pg)
    check('typical battleship' in pg.inner_text(f'{C} .dmg-vs'), 'preset kept after a reload')
    # collapse / open
    pg.click(f'{C} .cc-toggle[data-card="dmg"]'); pg.wait_for_timeout(100)
    closed = pg.inner_text(f'{R} .fl-dmg .cc-closed')
    check(pg.evaluate("CARD_NAMES.dmg") in closed and 'DPS applied to a typical battleship' in closed, f'collapsed: one row with the headline ({closed.strip()[:80]})')
    pg.click(f'{R} .fl-dmg .cc-toggle[data-card="dmg"]'); ready(pg)
    check(pg.is_visible(f'{C} .dmg-svg'), 'opened again')
    # my ship replaces the preset
    pg.click('#myShipChip'); pg.fill('#myShipEft', VEXOR); pg.click('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-tiles')
    pg.keyboard.press('Escape')
    pg.wait_for_function(f"() => /your Vexor/.test((document.querySelector('{C} .dmg-vs') || {{}}).textContent || '')", timeout=60000); ready(pg)
    check(pg.locator(f'{C} .dmg-presets').count() == 0 and head(pg) == pg.evaluate(EXPECT, C) and '50MN Microwarpdrive II' in pg.inner_text(f'{C} .dmg-controls'),
          f'my ship saved: applied to your Vexor, no preset picker ({head(pg)} DPS)')
    pg.click('#myShipUseLabel'); pg.wait_for_function(f"() => /typical battleship/.test(document.querySelector('{C} .dmg-vs').textContent)", timeout=60000)
    check(True, '"Use in assessments" off: back to the preset')
    pg.click('#myShipUseLabel'); pg.wait_for_function(f"() => /your Vexor/.test(document.querySelector('{C} .dmg-vs').textContent)", timeout=60000)
    # v2026.10.14.47 (bug list #1, the owner via the inbox): with the card collapsed, switching "Use in assessments" off
    # and on must update the collapsed row too (it kept the old "DPS applied to you ..." text)
    ready(pg); mine_head = head(pg)
    pg.click(f'{C} .cc-toggle[data-card="dmg"]'); pg.wait_for_timeout(100)
    ROW = f"(document.querySelector('{R} .fl-dmg .cc-closed .cc-sum') || {{}}).textContent || ''"
    check(f'{mine_head} DPS applied to you' in pg.evaluate(ROW), f'collapsed, my ship in use: the row reads {pg.evaluate(ROW)!r}')
    pg.click('#myShipUseLabel')
    try: pg.wait_for_function(f"() => /typical battleship/.test({ROW})", timeout=20000); ok = True
    except Exception: ok = False
    check(ok, f'collapsed, "Use in assessments" off: the row follows the preset ({pg.evaluate(ROW)!r})')
    pg.click('#myShipUseLabel')
    try: pg.wait_for_function(f"() => /DPS applied to you/.test({ROW})", timeout=20000); ok = True
    except Exception: ok = False
    check(ok and f'{mine_head} DPS applied to you' in pg.evaluate(ROW), f'collapsed, back on: the row follows my ship again ({pg.evaluate(ROW)!r})')
    pg.click(f'{R} .fl-dmg .cc-toggle[data-card="dmg"]'); ready(pg)
    check(head(pg) == mine_head, f'opened again: same headline ({head(pg)})')
    # my ship view: no card
    pg.click(f'{R} .mys-sw-btn.is-mine'); pg.wait_for_selector(f'{R} .mys-mine-view .fit-layout')
    check(pg.locator(f'{R} .mys-mine-view .fl-dmg').count() == 0, 'my ship view: no damage card')
    mb, mf = pg.locator(f'{R} .mys-mine-view .fl-beat').bounding_box(), pg.locator(f'{R} .mys-mine-view .fl-fit').bounding_box()
    check(abs(mb['y'] - mf['y']) < 2, f'my ship view: with no card the columns start level (the empty band takes no height; {mb["y"]:.0f} / {mf["y"]:.0f})')
    pg.click(f'{R} .mys-sw-btn.is-threat')
    # v2026.10.14.40: drones are charted (pyfa getDroneMult): a Vexor threat's raw DPS counts its Hammerheads,
    # the chart marks its drone control range, and the note no longer lists drones as missing
    pg.fill('#fitAnalyzerInput', VEXOR); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout'); ready(pg)
    sub, chart = pg.inner_text(f'{C} [data-out="headSub"]'), pg.inner_text(f'{C} .dmg-chart')
    note = pg.inner_text(f'{C} .dmg-note') if pg.locator(f'{C} .dmg-note').count() else ''   # v.48: only shown when something isn't charted
    raw = pg.evaluate(f"() => {{ const a = document.querySelector('{C}')._dmg.f.estimate.application; return Math.round(a.weapons.reduce((s, w) => s + w.dps, 0) + a.drones.reduce((s, d) => s + d.dps, 0)); }}")
    check(f'{raw:,} raw' in sub and 'their drone range' in chart and 'Not in the chart yet' not in note and head(pg) == pg.evaluate(EXPECT, C),
          f'drone ship: raw {raw} incl. drones ({sub}), drone range marked, drones not listed as missing, headline {head(pg)}')
    # nothing to chart
    pg.fill('#fitAnalyzerInput', BESTOWER); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{C} .dmg-note')
    check('No turrets, missiles' in pg.inner_text(f'{C}'), 'a fit with no weapons: nothing to chart')
    # Pilot losses
    pg.click('#tabBtnPilot')
    n = pg.evaluate("""async (text) => { const parsed = await parseEftFit(text);
        const mk = async (day) => { const est = await estimateHpAndDps(parsed.shipTypeId, parsed.tally, parsed.cargoItemIds, parsed.highSlotByFlag, 'sharpshooter', parsed.midSlotByFlag);
          return { km: {killmail_time: day}, killmailId: 1, tally: parsed.tally, highSlotByFlag: parsed.highSlotByFlag, estimate: est,
            input: {shipTypeId: parsed.shipTypeId, tally: parsed.tally, cargoItemIds: parsed.cargoItemIds, highSlotByFlag: parsed.highSlotByFlag, midSlotByFlag: parsed.midSlotByFlag} }; };
        renderFitTabs('Test Pilot', 'Hecate', [await mk('2026-10-01T00:00:00Z'), await mk('2026-10-02T00:00:00Z')], parsed.idToName);
        return document.querySelectorAll('#fitResults .mys-threat-view .fl-dmg').length; }""", HECATE)
    pg.wait_for_selector('#fitResults .fl-dmg [data-out="head"]:not(:empty)', timeout=60000)
    check(n == 2 and 'your Vexor' in pg.inner_text('#fitResults .fl-dmg .dmg-vs'), f'Pilot losses: a card per loss tab, applied to your Vexor ({n})')
    # v2026.10.14.48 (the owner's screenshot: "Adjust" with no sliders): the second loss tab's card was drawn while its
    # tab was hidden (no width), which closed Adjust; on the wide layout it must be open
    pg.locator('#fitResults .assess-tabs button').nth(1).click(); pg.wait_for_timeout(400)
    adj = pg.evaluate("[...document.querySelectorAll('#fitResults .mys-threat-view .fl-dmg .dmg-adjust')].map(d => ({open: d.open, shown: d.offsetParent !== null}))")
    check(len(adj) == 2 and all(a['open'] for a in adj), f'Pilot losses: Adjust open on every loss tab, also one that was hidden when drawn ({adj})')
    pg.locator('#fitResults .assess-tabs button').nth(0).click(); pg.wait_for_timeout(300)
    # the owner's repro (bug list #1) on the Pilot Analyzer itself: collapse the card on the shown loss, switch "Use in
    # assessments" off -> the row follows the preset
    P = '#fitResults .subtab-panel:not([hidden]) .mys-threat-view .fl-dmg'
    pg.click(f'{P} .cc-toggle[data-card="dmg"]'); pg.wait_for_timeout(150)
    PROW = f"(document.querySelector('{P} .cc-sum') || {{}}).textContent || ''"
    before = pg.evaluate(PROW)
    pg.click('#myShipUseLabel')
    try: pg.wait_for_function(f"() => /typical/.test({PROW})", timeout=20000); ok = True
    except Exception: ok = False
    check(ok and 'DPS applied to you' in before, f'Pilot loss, collapsed: "Use in assessments" off updates the row ({before!r} -> {pg.evaluate(PROW)!r})')
    pg.click('#myShipUseLabel')
    check(not errs, f'desktop: no page errors {errs}')
    pg.screenshot(path=os.path.join(os.environ.get('SHOTS', '/tmp'), 'dmg_desktop.png'), full_page=True)
    ctx.close()

def phone(b):
    W = 375
    ctx = b.new_context(viewport={'width': W, 'height': 740}, is_mobile=True, has_touch=True)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML)
    pg.evaluate("localStorage.removeItem('dscanMyShip'); localStorage.removeItem('dscanDmgPreset')"); pg.reload()
    pg.tap('#tabBtnFit'); pg.fill('#fitAnalyzerInput', HECATE); pg.tap('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout')
    check(pg.locator(f'{R} .fl-dmg .cc-closed').count() == 1, 'phone: the card starts collapsed')
    # v2026.10.14.47: a card that starts collapsed shows its headline at once (it used to say "damage applied to
    # you, by distance" until opened once)
    try: pg.wait_for_function(f"() => /DPS applied to a typical cruiser at/.test(document.querySelector('{R} .fl-dmg .cc-sum').textContent)", timeout=20000); ok = True
    except Exception: ok = False
    check(ok, f"phone: the collapsed row has the headline ({pg.inner_text(f'{R} .fl-dmg .cc-sum')!r})")
    check(pg.locator(f'{R} .fl-dmg').bounding_box()['y'] < pg.locator(f'{R} .fl-beat').bounding_box()['y'], 'phone: the card is first, above Weaknesses')
    pg.tap(f'{R} .fl-dmg .cc-toggle[data-card="dmg"]'); ready(pg)
    svg = pg.locator(f'{C} .dmg-svg').bounding_box()
    check(svg['x'] >= 0 and svg['x'] + svg['width'] <= W, f'phone: chart inside the screen ({svg["x"]:.0f} to {svg["x"] + svg["width"]:.0f})')
    check(pg.get_attribute(f'{C} .dmg-adjust', 'open') is None, 'phone: Adjust starts closed')
    pg.tap(f'{C} .dmg-adjust > summary'); pg.wait_for_timeout(100)
    sw = pg.evaluate('document.documentElement.scrollWidth'); check(sw <= W, f'phone: no sideways scroll with Adjust open ({sw})')
    seg = pg.locator(f'{C} .dmg-seg button').first.bounding_box()
    check(seg['height'] >= 36, f'phone: segment buttons finger-sized ({seg["height"]:.0f}px)')
    box = pg.locator(f'{C} [data-out="chart"]').bounding_box()
    pg.touchscreen.tap(box['x'] + box['width'] * 0.5, box['y'] + box['height'] / 2); pg.wait_for_timeout(100)
    check(pg.is_visible(f'{C} .dmg-tip'), 'phone: tapping the chart shows the values')
    pg.locator(f'{C}').scroll_into_view_if_needed()
    pg.screenshot(path=os.path.join(os.environ.get('SHOTS', '/tmp'), 'dmg_phone.png'), full_page=True)
    # v2026.10.14.48: on a phone the info panel is a sheet from the bottom with a close button
    pg.tap(f'{C} summary.info-btn'); pg.wait_for_timeout(250)
    pos = pg.evaluate(f"getComputedStyle(document.querySelector('{C} .info-body')).position")
    check(pos == 'fixed' and pg.is_visible(f'{C} button.info-close'), f'phone: the info panel is a sheet with a close button ({pos})')
    pg.tap(f'{C} button.info-close'); pg.wait_for_timeout(200)
    check(not pg.is_visible(f'{C} .info-body'), 'phone: the close button closes the sheet')
    check(not errs, f'phone: no page errors {errs}')
    ctx.close()

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('CHROMIUM', '/opt/pw-browsers/chromium'))
    desktop(b); tablet(b); phone(b)
    b.close()
print(f'FAILURES: {fails}')
