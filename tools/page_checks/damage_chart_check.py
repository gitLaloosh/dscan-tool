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
  * Pilot losses: each loss tab has its own card; the "My ship" view has your own card since v2026.10.14.55 (mine_damage_check.py);
  * collapsed: the row's headline follows "Use in assessments" (v2026.10.14.47, bug list #1) and is there from
    the start on a phone;
  * v2026.10.14.48: Reset is a reserved icon (disabled at the defaults); the method text is behind the info button
    (panel over the page, Escape / outside press close it); Adjust is open on a loss tab that was hidden when drawn;
  * phone (375 px): the card starts collapsed, opens to a chart no wider than the screen, Adjust starts closed,
    no sideways scrolling. No page errors anywhere.
  * v2026.10.14.54 chart markers (F3, boards 5b + 5c), at 1440 and 375 px, with a fit carrying every kind (scram,
    web, painter, neut, nos, drones): the zones worked out again here from the fit's own projected inputs and EWAR
    modules (T scram / furthest web, D furthest painter, C furthest running neut / nos), each shaded from the plot's
    left edge to its range; their badges carry the EWAR card's letters, 20 px apart and inside the chart; the pins
    numbered by distance; the key has a row per zone and pin with its km and keeps them on every axis; the x axis
    prints the tackle distances (tackle colour) and your range (white), the y axis the DPS at your range in each
    line's colour (one white number when equal); no axis numbers touch; the plot frame and the chart's height stay
    put through every setting; a dragged slider only grows the y scale and release fits it again; a running neut
    switched off leaves the zones. The Hecate (scram 9 km, web 10 km) is checked against the board 5c numbers.
"""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esi_from_sde import route_all, run_async
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
ARBITRATOR = """[Arbitrator, every kind of range]
Drone Damage Amplifier II
Drone Damage Amplifier II
Damage Control II

Warp Scrambler II
Stasis Webifier II
Target Painter II

Medium Energy Neutralizer II
Small Energy Nosferatu II

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
def set_range(pg, sel, v, release=True):
    # a drag ('input' events) and its release ('change', v.54: the y scale fits again then)
    pg.evaluate("([s, v, rel]) => { const i = document.querySelector(s); i.value = v; i.dispatchEvent(new Event('input', {bubbles: true})); if(rel) i.dispatchEvent(new Event('change', {bubbles: true})); }", [sel, str(v), release])

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
    check(head(pg) == pg.evaluate(EXPECT, C) and 'you still' in pg.inner_text(f'{C} [data-out="headSub"]'), 'You: Still')
    pg.click(f'{C} button[data-seg="You"][data-v="orbit"]')
    set_range(pg, f'{C} input[data-in="sigPct"]', 200); h2 = head(pg)
    check(head(pg) == pg.evaluate(EXPECT, C) and '200%' in pg.inner_text(f'{C} [data-out="sig"]'), f'signature slider ({h2})')
    set_range(pg, f'{C} input[data-in="theirPct"]', 60)
    pg.click(f'{C} button[data-seg="Them"][data-v="orbit"]')   # v.51: in-game names, Stopped / Approach / Orbit
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
    check(panel.is_visible() and info0 in panel.inner_text() and pg.evaluate("CARD_INFO.dmg[3]") in panel.inner_text(),
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
    # my ship view: since v2026.10.14.55 (F4) your own card, on top beside Weaknesses (tools/page_checks/mine_damage_check.py checks it)
    pg.click(f'{R} .mys-sw-btn.is-mine'); pg.wait_for_selector(f'{R} .mys-mine-view .fit-layout')
    mb, md = pg.locator(f'{R} .mys-mine-view .fl-beat').bounding_box(), pg.locator(f'{R} .mys-mine-view .fl-dmg').bounding_box()
    check(pg.locator(f'{R} .mys-mine-view .fl-dmg').count() == 1 and abs(mb['y'] - md['y']) < 2, f'my ship view: your card on top, level with Weaknesses ({mb["y"]:.0f} / {md["y"]:.0f})')
    pg.click(f'{R} .mys-sw-btn.is-threat')
    # v2026.10.14.40: drones are charted (pyfa getDroneMult): a Vexor threat's raw DPS counts its Hammerheads,
    # the chart marks its drone control range, and the note no longer lists drones as missing
    pg.fill('#fitAnalyzerInput', VEXOR); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout'); ready(pg)
    sub, chart = pg.inner_text(f'{C} [data-out="headSub"]'), pg.inner_text(f'{C} .dmg-chart')
    note = pg.inner_text(f'{C} .dmg-note') if pg.locator(f'{C} .dmg-note').count() else ''   # v.48: only shown when something isn't charted
    raw = pg.evaluate(f"() => {{ const a = document.querySelector('{C}')._dmg.f.estimate.application; return Math.round(a.weapons.reduce((s, w) => s + w.dps, 0) + a.drones.reduce((s, d) => s + d.dps, 0)); }}")
    check(f'{raw:,} raw' in sub and 'their drone range' in chart.lower() and 'Not in the chart yet' not in note and head(pg) == pg.evaluate(EXPECT, C),
          f'drone ship: raw {raw} incl. drones ({sub}), drone range marked, drones not listed as missing, headline {head(pg)}')
    # nothing to chart
    pg.fill('#fitAnalyzerInput', BESTOWER); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{C} .dmg-note')
    check('No turrets, missiles' in pg.inner_text(f'{C}'), 'a fit with no weapons: nothing to chart')
    # Pilot losses
    pg.click('#tabBtnPilot')
    n = run_async(pg, """async (text) => { const parsed = await parseEftFit(text);
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

# v2026.10.14.54 (F3): the chart's markers. Everything geometric is read off the drawn SVG (getBBox), and the
# expected zones are worked out here from the fit's inputs, not by calling the page's dmgRangeMarks.
CHART_STATE = """(sel) => { const card = document.querySelector(sel), c = card._dmg, m = c.m, svg = card.querySelector('.dmg-svg');
  const bb = (e) => { const b = e.getBBox(); return {x: b.x, y: b.y, w: b.width, h: b.height, t: e.textContent, cls: e.getAttribute('class') || ''}; };
  const pr = m.app.projected, ew = (c.f.estimate.ewarModules || []);
  const hit = card.querySelector('.dmg-hit');
  return {W: +svg.getAttribute('width'), H: +svg.getAttribute('height'), hit: ['x', 'y', 'width', 'height'].map(k => +hit.getAttribute(k)),
    hi: m.axis.hi, lo: m.axis.lo, yMax: m.yMax, axis: c.f.dmg.axis, range: c.f.dmg.range, mode: c.f.dmg.mode, cur: m.cur.dps, still: m.still.dps,
    engAt: m.at(m.axis.eng).dps, eng: m.axis.eng,
    inputs: {scram: pr.scramRange, webs: [...pr.webMods, ...pr.webDrones].map(w => w.optimal), tps: [...pr.tpMods, ...pr.tpDrones].map(w => w.optimal),
      neut: ew.filter(e => e.kind === 'neut' && e.running).map(e => e.rangeM), nos: ew.filter(e => e.kind === 'nos' && e.running).map(e => e.rangeM),
      lock: m.app.lockRange, drones: (m.app.drones || []).length, dcr: pr.droneControlRange},
    zones: [...svg.querySelectorAll('rect.dmg-zone')].map(e => ({cls: e.getAttribute('class'), x: +e.getAttribute('x'), w: +e.getAttribute('width')})),
    badges: [...svg.querySelectorAll('g.dmg-badge')].map(e => Object.assign(bb(e), {letter: e.querySelector('text').textContent, title: e.querySelector('title').textContent})),
    pins: [...svg.querySelectorAll('g.dmg-pin')].map(e => Object.assign(bb(e), {n: e.querySelector('text').textContent, title: e.querySelector('title').textContent})),
    lines: [...svg.querySelectorAll('line.dmg-zline')].map(e => +e.getAttribute('x1')),
    xrow: [...svg.querySelectorAll('text')].filter(e => +e.getAttribute('y') === +svg.getAttribute('height') - 8).map(bb),
    yrow: [...svg.querySelectorAll('text.dmg-tick, text.dmg-ylab')].filter(e => e.getAttribute('text-anchor') === 'end' && +e.getAttribute('y') !== +svg.getAttribute('height') - 8).map(bb),
    keyRows: [...card.querySelectorAll('.dmg-ck-row')].map(e => e.textContent.replace(/\\s+/g, ' ').trim()),
    keyNote: (card.querySelector('.dmg-ck-note') || {}).textContent || '',
    chartH: card.querySelector('.dmg-chart').getBoundingClientRect().height}; }"""
def km_label(x): return f'{x / 1000:.1f}'.rstrip('0').rstrip('.') if x < 100000 else f'{x / 1000:.0f}'
def km_text(m):
    k = m / 1000
    t = f'{k:.0f}' if k >= 100 else f'{k:.1f}' if k >= 10 else f'{k:.2f}'
    return (t.rstrip('0').rstrip('.') if '.' in t else t) + ' km'
def boxes_apart(bs, gap=0):
    bs = sorted(bs, key=lambda b: b['x'])
    return all(bs[i]['x'] + bs[i]['w'] + gap <= bs[i + 1]['x'] + 0.5 for i in range(len(bs) - 1))
def expected_zones(i):
    far = lambda a: max([x for x in a if x and x > 0] or [0])
    z = [(i['scram'] or 0, 'tackle', 'T', 'Their scram'), (far(i['webs']), 'tackle', 'T', 'Their web'), (far(i['tps']), 'disrupt', 'D', 'Their target painter'),
         (far(i['neut']), 'drain', 'C', 'Their neut'), (far(i['nos']), 'drain', 'C', 'Their nos')]
    return sorted([t for t in z if t[0] > 0], key=lambda t: t[0])

def markers_at(b, W):
    ctx = b.new_context(viewport={'width': W, 'height': 1000}, is_mobile=W < 600, has_touch=W < 600)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML)
    pg.evaluate("localStorage.removeItem('dscanMyShip'); localStorage.removeItem('dscanDmgPreset')"); pg.reload()
    pg.click('#tabBtnFit')
    # 1. the Hecate (this file's: a scram, no web): 9 km in the tackle colour, your range in white
    pg.fill('#fitAnalyzerInput', HECATE); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout')
    if not pg.locator(C).count(): pg.click(f'{R} .fl-dmg .cc-toggle[data-card="dmg"]')
    ready(pg)
    s = pg.evaluate(CHART_STATE, C)
    tack = [t['t'] for t in s['xrow'] if 'dmg-xlab tackle' in t['cls']]
    eng = [t['t'] for t in s['xrow'] if 'dmg-xlab eng' in t['cls']]
    check([z['cls'] for z in s['zones']] == ['dmg-zone tackle'] and [b_['letter'] for b_ in s['badges']] == ['T'], f'{W} Hecate: one tackle zone with a T badge ({[z["cls"] for z in s["zones"]]})')
    check(tack == ['9'] and eng == [km_label(s['range'])], f'{W} Hecate: x axis prints 9 in the tackle colour and your range {eng} in white ({tack})')
    check(s['keyRows'] == ['TTheir scram (your MWD off)9 km'], f'{W} Hecate: the key row ({s["keyRows"]})')
    # a dragged slider only grows the y scale; release fits it again. Charted across your speed, the range moves the
    # whole curve: at 20 km the blasters hardly land, at 1 km they do.
    if pg.get_attribute(f'{C} .dmg-adjust', 'open') is None: pg.click(f'{C} .dmg-adjust > summary')
    pg.click(f'{C} button[data-seg="Chart across"][data-v="speed"]')
    RG = f'{C} input[data-in="range"]'
    set_range(pg, RG, 20000); y0 = pg.evaluate(CHART_STATE, C)['yMax']
    set_range(pg, RG, 1000, release=False); y1 = pg.evaluate(CHART_STATE, C)['yMax']
    set_range(pg, RG, 20000, release=False); y2 = pg.evaluate(CHART_STATE, C)['yMax']
    pg.evaluate(f"() => document.querySelector('{RG}').dispatchEvent(new Event('change', {{bubbles: true}}))"); y3 = pg.evaluate(CHART_STATE, C)['yMax']
    check(y1 > y0 and y2 == y1 and y3 == y0, f'{W}: dragging holds the y scale (grows {y0} -> {y1}, held at {y2}), release fits it again ({y3})')
    pg.click(f'{C} button[data-seg="Chart across"][data-v="distance"]')
    # 2. a fit with every kind of range
    pg.fill('#fitAnalyzerInput', ARBITRATOR); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout')
    if not pg.locator(C).count(): pg.click(f'{R} .fl-dmg .cc-toggle[data-card="dmg"]')
    pg.wait_for_function(f"() => {{ const c = document.querySelector('{C}'); return c && c._dmg && /Arbitrator/.test(c._dmg.f.estimate.shipName || '') || (c && c._dmg && c._dmg.m && c._dmg.m.zones.length >= 4); }}", timeout=60000)
    ready(pg)
    if pg.get_attribute(f'{C} .dmg-adjust', 'open') is None: pg.click(f'{C} .dmg-adjust > summary')
    s = pg.evaluate(CHART_STATE, C)
    exp = expected_zones(s['inputs'])
    L, Tp, pw, ph = s['hit']
    xOf = lambda x: L + (min(max(x, s['lo']), s['hi']) - s['lo']) / (s['hi'] - s['lo']) * pw
    check(len(exp) == 5, f'{W} Arbitrator: the fit carries scram, web, painter, neut and nos ({[(round(e[0]), e[1]) for e in exp]})')
    check([z['cls'].split()[-1] for z in s['zones']] == [e[1] for e in exp] and all(abs(z['x'] - L) < 0.6 and abs(z['x'] + z['w'] - xOf(e[0])) < 0.6 for z, e in zip(s['zones'], exp)),
          f'{W} Arbitrator: each zone shaded from the plot\'s left edge to its range, in its category ({[(round(z["x"]), round(z["w"])) for z in s["zones"]]})')
    check([b_['letter'] for b_ in s['badges']] == [e[2] for e in exp] and all(b_['title'].startswith(e[3]) and b_['title'].endswith(km_text(e[0])) for b_, e in zip(s['badges'], exp)),
          f'{W} Arbitrator: badges carry the EWAR card\'s letters in distance order, titled with what and how far ({[b_["title"] for b_ in s["badges"]]})')
    tops = s['badges'] + s['pins']
    cx = sorted(t['x'] + t['w'] / 2 for t in tops)
    check(all(cx[i + 1] - cx[i] >= 19.5 for i in range(len(cx) - 1)) and min(t['x'] for t in tops) >= 0 and max(t['x'] + t['w'] for t in tops) <= s['W'] and all(t['y'] + t['h'] <= Tp for t in tops),
          f'{W} Arbitrator: badges and pins above the plot, 20 px apart and inside the chart ({[round(c) for c in cx]})')
    pins_exp = sorted([(x, l) for x, l, ok in ((s['inputs']['lock'], 'Their lock range', s['inputs']['lock'] and s['inputs']['lock'] <= s['hi']),
                                                (s['inputs']['dcr'], 'Their drone range', s['inputs']['drones'] and s['inputs']['dcr'] and s['inputs']['dcr'] <= s['hi'])) if ok])
    check([p_['n'] for p_ in s['pins']] == [str(i + 1) for i in range(len(pins_exp))] and [p_['title'] for p_ in s['pins']] == [f'{l}: {km_text(x)}' for x, l in pins_exp] and len(pins_exp) >= 1,
          f'{W} Arbitrator: pins numbered by distance ({[p_["title"] for p_ in s["pins"]]})')
    check(len(s['keyRows']) == len(exp) + len(pins_exp) and all(any(r.startswith(e[2] + e[3]) and r.endswith(km_text(e[0])) for r in s['keyRows']) for e in exp)
          and all(r.endswith(' km') for r in s['keyRows']) and s['keyNote'] == 'Shaded: inside their range' and 'their drone range' in pg.inner_text(f'{C} .dmg-chart').lower(),
          f'{W} Arbitrator: the key has a row per zone and pin ({s["keyRows"]}; {s["keyNote"]!r})')
    tackle_lbls = {km_label(e[0]) for e in exp if e[1] == 'tackle' and e[0] <= s['hi']} - {km_label(s['range'])}
    xl = [t for t in s['xrow'] if 'dmg-xlab' in t['cls']]
    check({t['t'].replace(' km', '') for t in xl if 'tackle' in t['cls']} == tackle_lbls and [t['t'].replace(' km', '') for t in xl if 'eng' in t['cls']] == [km_label(s['range'])],
          f'{W} Arbitrator: x axis prints the tackle distances {sorted(tackle_lbls)} and your range {km_label(s["range"])} (one number where they are equal)')
    check(boxes_apart(s['xrow']) and min(t['x'] for t in s['xrow']) >= 0 and max(t['x'] + t['w'] for t in s['xrow']) <= s['W'] + 0.5, f'{W} Arbitrator: no x axis numbers touch ({[t["t"] for t in sorted(s["xrow"], key=lambda t: t["x"])]})')
    # your range on a round tick (the tick's number goes), then on their scram (one number, yours)
    for v, what in ((20000, 'a round tick'), (int(exp[1][0]) // 100 * 100 if km_label(exp[1][0]) == km_label(exp[1][0] // 100 * 100) else 0, 'their scram')):
        if not v: continue
        set_range(pg, f'{C} input[data-in="range"]', v); t = pg.evaluate(CHART_STATE, C)
        texts = [x['t'].replace(' km', '') for x in t['xrow']]
        check(boxes_apart(t['xrow']) and texts.count(km_label(v)) == 1 and [x['t'] for x in t['xrow'] if 'dmg-xlab eng' in x['cls']] == [km_label(v)],
              f'{W} Arbitrator: your range on {what} ({km_label(v)} km): printed once, in white, nothing touches ({sorted(texts)})')
    set_range(pg, f'{C} input[data-in="range"]', s['range'])
    yl = [t for t in s['yrow'] if 'dmg-ylab' in t['cls']]
    want = sorted([(f'{round(s["still"]):,}', 'still'), (f'{round(s["cur"]):,}', 'move')]) if round(s['still']) != round(s['cur']) else [(f'{round(s["cur"]):,}', 'same')]
    check(sorted((t['t'], t['cls'].split()[-1]) for t in yl) == want, f'{W} Arbitrator: y axis prints the DPS at your range in each line\'s colour ({[(t["t"], t["cls"]) for t in yl]} vs {want})')
    ys = sorted(s['yrow'], key=lambda t: t['y'])
    check(all(ys[i]['y'] + ys[i]['h'] <= ys[i + 1]['y'] + 1.5 for i in range(len(ys) - 1)), f'{W} Arbitrator: no y axis numbers touch ({[t["t"] for t in ys]})')
    # 3. rule 4: the plot frame and the chart's height stay put through every setting, and the key keeps its rows
    frame, height, rows = s['hit'], s['chartH'], len(s['keyRows'])
    moved = []
    def look(what):
        t = pg.evaluate(CHART_STATE, C)
        if t['hit'][0] != frame[0] or t['hit'][1] != frame[1] or t['hit'][3] != frame[3] or abs(t['chartH'] - height) > 0.5 or len(t['keyRows']) != rows: moved.append((what, t['hit'], round(t['chartH'], 1), len(t['keyRows'])))
        return t
    for v in (0, 2000, 30000, 60000): set_range(pg, f'{C} input[data-in="range"]', v); look(f'range {v}')
    for mode in ('still', 'straight', 'orbit'): pg.locator(f'{C} button[data-seg="You"][data-v="{mode}"]').click(); look(mode)
    for v in (25, 300, 100): set_range(pg, f'{C} input[data-in="sigPct"]', v); look(f'sig {v}')
    sw = pg.locator(f'{C} input[data-in="prop"]')
    if sw.count(): sw.click(); look('MWD off'); sw.click(); look('MWD on')
    for ax in ('speed', 'sig', 'distance'):
        pg.locator(f'{C} button[data-seg="Chart across"][data-v="{ax}"]').click(); t = look(f'axis {ax}')
        if ax != 'distance':
            check(not t['zones'] and not t['badges'] and t['keyNote'] == 'Marked when charting across distance' and len(t['keyRows']) == rows
                  and [re.sub(r' m(/s)?$', '', x['t']) for x in t['xrow'] if 'dmg-xlab eng' in x['cls']] == [f'{round(t["eng"]):,}'],
                  f'{W} across {ax}: no zones, the key keeps its rows with the other note, your value printed in white ({[(x["t"], x["cls"]) for x in t["xrow"]]}, {t["keyNote"]!r}, {round(t["eng"])})')
    check(not moved, f'{W}: the plot frame, the chart\'s height and the key rows stay put through every setting {moved[:3]}')
    # mode still: both lines give the same number -> one white label
    pg.locator(f'{C} button[data-seg="You"][data-v="still"]').click()
    t = pg.evaluate(CHART_STATE, C)
    check([(x['t'], x['cls']) for x in t['yrow'] if 'dmg-ylab' in x['cls']] == [(f'{round(t["cur"]):,}', 'dmg-ylab same')], f'{W} you stopped: one white DPS number on the y axis')
    pg.locator(f'{C} button[data-seg="You"][data-v="orbit"]').click()
    # 4. a neut switched off (Fit card) leaves the zones
    n0 = len(pg.evaluate(CHART_STATE, C)['zones'])
    neut = pg.locator(f'{R} button.ms-state[data-from="active"][aria-label^="Medium Energy Neutralizer II"]').first
    neut.scroll_into_view_if_needed(); neut.click()
    try:
        pg.wait_for_function(f"() => !document.querySelector('{R} .fit-card-busy') && (c => c && c._dmg && c._dmg.m && c._dmg.m.zones.length === 4)(document.querySelector('{C}'))", timeout=30000); ok = True
    except Exception: ok = False
    t = pg.evaluate(CHART_STATE, C) if ok else {'keyRows': [], 'badges': []}
    check(n0 == 5 and ok and not any('Their neut' in r for r in t['keyRows']) and [b_['letter'] for b_ in t['badges']].count('C') == 1,
          f'{W}: the neut switched off on the Fit card leaves the zones and the key ({n0} -> {len(t.get("zones", []))}; {t["keyRows"]})')
    check(not errs, f'{W} markers: no page errors {errs}')
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
    markers_at(b, 1440); markers_at(b, 375)
    b.close()
print(f'FAILURES: {fails}')
