"""Damage Application in the My Ship Perspective (v2026.10.14.55, fight setup F4; roadmap/subtext-plan.md section 5,
roadmap/turret-application-plan.md board 4).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/mine_damage_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The number is pyfa's applied DPS of your ship on the threat (the board's "DPS applied to them", checked against pyfa by
tools/independent_checks/check_matchup.py); this checks the card around it, in the real page:
  * v2026.10.14.56: the fight's range (both cards' sliders and charts, the strip's slider) runs to the farther-reaching
    ship (no ship saved: the threat's own reach); 100 m steps;
  * placement: with a ship saved, the My ship view has the card on top, across the Fit and stats columns at 1440 px
    (Weaknesses beside it), full width at 1100 px, first on a phone; the tag names the threat; a cyan edge;
  * the headline is the board's "DPS applied to them" and the card's own point; one solid line; the key lists YOUR
    tackle and ranges ("Your scram (their MWD off)", "Your web", "Your drone range", "Your lock range"); the info
    panel is CARD_INFO["dmg#mine"]; Adjust has no signature slider and charts across Distance / Your speed;
  * one fight: the card's range slider and movement buttons write the threat's settings; the board follows; the
    threat's card (in the hidden view) shows them when switched back; the strip's menus move this card; its own
    "Chart across" leaves the threat card's axis alone; Reset puts the fight back (disabled at the defaults);
  * nothing moves (subtext rule 4): every area of the My ship view keeps its place and size while the card's
    range, movements, axis, MWD switch and Reset change;
  * Keep at Range: inside their scram the card's button is disabled with the reason, as on the threat's card;
  * a threat card left collapsed: its row follows a change made on this card (LESSON #43);
  * "More on Damage Application" in the strip opens THIS card's Adjust when the My ship view is shown;
  * hover: the tooltip says "DPS applied to them" with their speed;
  * Pilot losses: each loss tab's card charts against that tab's threat (its tag and the board's number);
  * phone (375 px): collapsed at first with the headline in its row, opens inside the screen, no sideways scroll.
No page errors anywhere.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esi_from_sde import route_all
from playwright.sync_api import sync_playwright

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')),
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'index.html')))
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'matchup_strip_check.py'), encoding='utf-8').read()
_ns = {}
exec(_src[_src.index('VEXOR = """'):_src.index('def check(')], _ns)
VEXOR, HECATE = _ns['VEXOR'], _ns['HECATE']
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

fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok

R = '#fitAnalyzerResults'
MV = f'{R} .mys-mine-view'
MC = f'{MV} .fl-dmg .dmg-card'
TC = f'{R} .mys-threat-view .fl-dmg .dmg-card'
S = f'{R} .mys-fight'
def settle(pg, ms=400):
    pg.wait_for_timeout(ms); pg.wait_for_function("() => !document.querySelector('.fit-card-busy')", timeout=60000); pg.wait_for_timeout(ms)
def set_range(pg, sel, v, release=True):
    pg.evaluate("([s, v, rel]) => { const i = document.querySelector(s); i.value = v; i.dispatchEvent(new Event('input', {bubbles: true})); if(rel) i.dispatchEvent(new Event('change', {bubbles: true})); }", [sel, str(v), release])
def board_your(pg, scope=R): return pg.inner_text(f'{scope} [data-cell="your"] .mys-cell-v')
def head(pg, sel=MC): return pg.inner_text(f'{sel} [data-out="head"]')
# the card's point, worked out again from the fight (wiring, not maths): the page's mysMatchup "DPS applied to them"
EXPECT = """(sel) => { const c = document.querySelector(sel)._dmg; const m = mysMatchup(c.f, c.mf, c.f.dmg); return dmgFmt(m.yourDps); }"""
def st(pg): return pg.evaluate(f"() => document.querySelector('{MC}')._dmg.f.dmg")
def pressed(pg, seg, sel=MC): return pg.get_attribute(f'{sel} button[data-seg="{seg}"][aria-pressed="true"]', 'data-v')
def save_ship(pg):
    pg.click('#myShipChip'); pg.fill('#myShipEft', VEXOR); pg.click('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-tiles'); pg.keyboard.press('Escape')
def to_mine(pg):
    pg.click(f'{R} .mys-sw-btn.is-mine'); pg.wait_for_selector(f'{MV} .fl-dmg'); settle(pg)
def to_threat(pg):
    pg.click(f'{R} .mys-sw-btn.is-threat'); pg.wait_for_selector(f'{R} .mys-threat-view:not([hidden])'); settle(pg, 300)
def open_card(pg, scope):
    if not pg.locator(f'{scope} .fl-dmg .dmg-card').count(): pg.locator(f'{scope} .fl-dmg .cc-toggle[data-card="dmg"]').first.click(); settle(pg, 300)
    pg.wait_for_selector(f'{scope} .fl-dmg .dmg-card [data-out="head"]:not(:empty)', timeout=60000)

def desktop(b, W):
    ctx = b.new_context(viewport={'width': W, 'height': 1000}); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML); pg.evaluate("localStorage.clear()"); pg.reload()
    pg.click('#tabBtnFit'); pg.fill('#fitAnalyzerInput', HECATE); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout'); settle(pg)
    check(pg.locator(f'{MV} .fl-dmg').count() == 0, f'{W}: no ship saved, no card of yours')
    # v2026.10.14.56: the fight's range runs to the farther-reaching ship; with no ship saved, the threat's own reach
    # (the typical-class preset has no weapons and doesn't widen it)
    TMAX = f"() => [document.querySelector('{TC} input[data-in=\"range\"]').max, dmgReachMax(document.querySelector('{TC}')._dmg.f.estimate.application)]"
    if not pg.locator(TC).count(): pg.locator(f'{R} .mys-threat-view .fl-dmg .cc-toggle[data-card="dmg"]').first.click(); settle(pg, 300)
    pg.wait_for_selector(f'{TC} input[data-in="range"]')
    t0 = pg.evaluate(TMAX) if pg.locator(TC).count() else None
    if t0 is None: t0 = pg.evaluate(f"() => [document.querySelector('{R} .fl-dmg .dmg-card input[data-in=\"range\"]').max, dmgReachMax(document.querySelector('{R} .fl-dmg .dmg-card')._dmg.f.estimate.application)]")
    check(str(t0[1]) == t0[0], f'{W}: no ship saved, the range runs to the threat\'s reach ({t0[0]} m)')
    save_ship(pg); settle(pg, 800)
    to_mine(pg); open_card(pg, MV)
    # placement
    bx = {k: pg.locator(f'{MV} .fl-{k}').bounding_box() for k in ('dmg', 'beat', 'fit', 'stats')}
    if W >= 1280:
        check(abs(bx['dmg']['x'] - bx['fit']['x']) < 2 and abs(bx['dmg']['x'] + bx['dmg']['width'] - bx['stats']['x'] - bx['stats']['width']) < 2 and abs(bx['dmg']['y'] - bx['beat']['y']) < 2
              and bx['fit']['y'] >= bx['dmg']['y'] + bx['dmg']['height'] - 1, f'{W}: the card on top across the Fit and stats columns, Weaknesses beside it')
    else:
        lay = pg.locator(f'{MV} .fit-layout').bounding_box()
        check(abs(bx['dmg']['width'] - lay['width']) < 2 and bx['fit']['y'] >= bx['dmg']['y'] + bx['dmg']['height'] - 1, f'{W}: the card full width on top')
    edge = pg.evaluate(f"getComputedStyle(document.querySelector('{MC}')).borderLeftColor")
    cyan = pg.evaluate("(() => { const d = document.createElement('div'); d.style.color = 'var(--cyan)'; document.body.appendChild(d); const c = getComputedStyle(d).color; d.remove(); return c; })()")
    check(edge == cyan and pg.inner_text(f'{MC} .dmg-vs') == 'applied to the Hecate · threat', f'{W}: cyan edge, tag "{pg.inner_text(f"{MC} .dmg-vs")}"')
    # v2026.10.14.56 (the owner: "engagement range appears to be capped for both perspectives by the threat's range. It
    # should probably be the greater of the two"): the Hecate reaches ~10 km, your Vexor's drones 60 km
    mx = pg.evaluate(f"""() => {{ const c = document.querySelector('{MC}')._dmg; return {{mine: document.querySelector('{MC} input[data-in="range"]').max,
      strip: document.querySelector('{S} input[data-fset="range"]').max, step: document.querySelector('{MC} input[data-in="range"]').step + '/' + document.querySelector('{S} input[data-fset="range"]').step,
      axis: c.m.axis.hi, them: dmgReachMax(c.f.estimate.application), you: dmgReachMax(c.mf.estimate.application), dcr: c.mf.estimate.application.projected.droneControlRange}}; }}""")
    want = str(max(mx['them'], mx['you']))
    check(mx['you'] > mx['them'] and mx['mine'] == mx['strip'] == want and str(mx['axis']) == want and int(want) >= mx['dcr'] and mx['step'] == '100/100',
          f'{W}: the range runs to the farther-reaching ship on your card, its chart and the strip ({mx})')
    to_threat(pg); open_card(pg, f'{R} .mys-threat-view')
    tm = pg.evaluate(f"() => [document.querySelector('{TC} input[data-in=\"range\"]').max, document.querySelector('{TC}')._dmg.m.axis.hi]")
    check(tm[0] == want and str(tm[1]) == want, f'{W}: the threat\'s card too: slider and chart to {want} m ({tm})')
    set_range(pg, f'{TC} input[data-in="range"]', mx['dcr']); settle(pg, 200)
    check(pg.inner_text(f'{TC} [data-out="range"]') == '60 km' and pg.evaluate(f"document.querySelector('{TC}')._dmg.f.dmg.range") == mx['dcr'],
          f'{W}: the threat\'s card can set the range to your drone range (60 km)')
    set_range(pg, f'{TC} input[data-in="range"]', 4400); settle(pg, 200)
    check(pg.evaluate(f"document.querySelector('{TC} input[data-in=\"range\"]').value") == '4400', f'{W}: 100 m steps: 4.4 km stays 4.4 km on the long slider')
    to_mine(pg); open_card(pg, MV)
    # the number
    h = head(pg)
    check(h == board_your(pg) == pg.evaluate(EXPECT, MC), f'{W}: headline {h} = the board\'s DPS applied to them ({board_your(pg)}) = the card\'s point')
    check(pg.locator(f'{MC} polyline.dmg-line').count() == 1 and pg.evaluate(f"getComputedStyle(document.querySelector('{MC} polyline.dmg-move')).strokeDasharray") in ('none', '')
          and pg.inner_text(f'{MC} [data-out="legend"]') == 'Hecate stopped, you orbiting', f'{W}: one solid line, legend "{pg.inner_text(f"{MC} [data-out=legend]")}"')
    rows = pg.evaluate(f"() => [...document.querySelectorAll('{MC} .dmg-ck-row .dmg-ck-l')].map(e => e.textContent)")
    check(rows == ['Your scram (their MWD off)', 'Your web', 'Your drone range', 'Your lock range'] and pg.inner_text(f'{MC} .dmg-ck-note') == 'Shaded: inside your range',
          f'{W}: the key lists your tackle and ranges ({rows})')
    check(pg.locator(f'{MC} input[data-in="sigPct"]').count() == 0 and pg.evaluate(f"() => [...document.querySelectorAll('{MC} button[data-seg=\"Chart across\"]')].map(b => b.dataset.v)") == ['distance', 'speed'],
          f'{W}: Adjust has no signature slider; Chart across Distance / Your speed')
    pg.click(f'{MC} summary.info-btn'); pg.wait_for_timeout(200)
    info = pg.inner_text(f'{MC} .info-body')
    check(pg.evaluate("CARD_INFO['dmg#mine'][1].slice(0, 40)") in info and pg.evaluate("CARD_INFO.dmg[0].slice(0, 40)") not in info, f'{W}: the info panel is CARD_INFO["dmg#mine"]')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    # hover
    pg.locator(f'{MC} [data-out="chart"]').scroll_into_view_if_needed()
    box = pg.locator(f'{MC} [data-out="chart"]').bounding_box()
    pg.mouse.move(box['x'] + box['width'] * 0.3, box['y'] + box['height'] * 0.5); pg.wait_for_timeout(150)
    tip = pg.inner_text(f'{MC} .dmg-tip') if pg.is_visible(f'{MC} .dmg-tip') else ''
    check('DPS applied to them' in tip and ('Their speed' in tip or "They're webbed" in tip), f'{W}: hover says DPS applied to them, their speed ({tip!r})')
    pg.mouse.move(5, 5)
    # rule 4 (nothing moves): every area of the My ship view keeps its place and size while this card's controls move
    RECTS = f"() => [...document.querySelectorAll('{MV} .fit-layout > div, {MC}')].map(e => {{ const r = e.getBoundingClientRect(); return [Math.round(r.top + scrollY), Math.round(r.height)]; }})"
    r0, moved = pg.evaluate(RECTS), []
    for what, act in (('range', lambda: set_range(pg, f'{MC} input[data-in="range"]', 9000)), ('Approach', lambda: pg.click(f'{MC} button[data-seg="You"][data-v="straight"]')),
                      ('they orbit', lambda: pg.click(f'{MC} button[data-seg="Them"][data-v="orbit"]')), ('Your speed axis', lambda: pg.click(f'{MC} button[data-seg="Chart across"][data-v="speed"]')),
                      ('MWD off', lambda: pg.click(f'{MC} input[data-in="prop"]')), ('Reset', lambda: pg.click(f'{MC} .dmg-reset'))):
        act(); settle(pg, 250)
        r1 = pg.evaluate(RECTS)
        if any(abs(a[0] - b_[0]) > 1 or abs(a[1] - b_[1]) > 1 for a, b_ in zip(r0, r1)) or len(r0) != len(r1): moved.append((what, r0, r1))
    check(not moved, f'{W}: nothing in the My ship view moves while this card\'s controls change {moved[:1]}')
    # one fight: this card writes the threat's settings, the board and the threat's card follow
    set_range(pg, f'{MC} input[data-in="range"]', 2000)
    pg.click(f'{MC} button[data-seg="You"][data-v="straight"]'); settle(pg, 300)
    s_ = st(pg); h = head(pg)
    check(s_['range'] == 2000 and s_['mode'] == 'straight' and h == board_your(pg) == pg.evaluate(EXPECT, MC) and pg.inner_text(f'{S} [data-fname="you"]') == 'Approach',
          f'{W}: range 2 km and Approach on this card: the fight, the board ({board_your(pg)}) and the strip follow ({h})')
    pg.click(f'{MC} button[data-seg="Chart across"][data-v="speed"]'); settle(pg, 200)
    check(st(pg)['axis'] == 'distance' and pg.evaluate(f"document.querySelector('{MC}')._dmg.m.st.axis") == 'speed' and head(pg) == h,
          f'{W}: Chart across Your speed is this card\'s own (the threat card stays on distance)')
    pg.click(f'{MC} button[data-seg="Chart across"][data-v="distance"]'); settle(pg, 200)
    # the strip moves this card
    pg.click(f'{S} details.mys-fpart-them > summary'); pg.wait_for_timeout(150)
    pg.click(f'{S} details.mys-fpart-them button.mys-fopt[data-v="orbit"]'); settle(pg, 300)
    check(pressed(pg, 'Them') == 'orbit' and head(pg) == board_your(pg) == pg.evaluate(EXPECT, MC) and 'orbiting' in pg.inner_text(f'{MC} [data-out="legend"]'),
          f'{W}: the strip\'s "Orbit" for them moves this card ({head(pg)}, {pg.inner_text(f"{MC} [data-out=legend]")!r})')
    # Keep at Range: inside their scram the button is disabled with the reason
    set_range(pg, f'{MC} input[data-in="range"]', 5000); settle(pg, 200)
    kb = f'{MC} button[data-seg="You"][data-v="keep"]'
    check(pg.is_disabled(kb) and 'scram' in (pg.get_attribute(kb, 'title') or ''), f'{W}: inside their scram, Keep at Range is not offered ({pg.get_attribute(kb, "title")!r})')
    # back to the threat view: its card shows the same fight
    to_threat(pg); open_card(pg, f'{R} .mys-threat-view')
    check(pg.inner_text(f'{TC} [data-out="range"]') == '5 km' and pressed(pg, 'You', TC) == 'straight' and pressed(pg, 'Them', TC) == 'orbit'
          and pg.evaluate(f"document.querySelector('{TC} input[data-in=\"range\"]').value") == '5000', f'{W}: the threat\'s card shows the fight set on yours (5 km, Approach, they orbit)')
    # collapsed threat card: its row follows a change made on your card (LESSON #43)
    pg.click(f'{R} .mys-threat-view .fl-dmg .cc-toggle[data-card="dmg"]'); settle(pg, 300)
    to_mine(pg); open_card(pg, MV)
    set_range(pg, f'{MC} input[data-in="range"]', 3000); settle(pg, 300)
    to_threat(pg)
    row = pg.inner_text(f'{R} .mys-threat-view .fl-dmg .cc-sum')
    check('at 3 km' in row, f'{W}: the threat card left collapsed: its row follows your card ({row!r})')
    pg.click(f'{R} .mys-threat-view .fl-dmg .cc-toggle[data-card="dmg"]'); settle(pg, 300)
    # Reset on your card puts the fight back
    to_mine(pg); open_card(pg, MV)
    pg.click(f'{MC} .dmg-reset'); settle(pg, 400)
    d = pg.evaluate(f"() => {{ const c = document.querySelector('{MC}')._dmg; return JSON.stringify(dmgDefaults(c.f.estimate.application)) === JSON.stringify(c.f.dmg); }}")
    check(d and pg.is_disabled(f'{MC} .dmg-reset') and head(pg) == board_your(pg), f'{W}: Reset puts the fight back and is disabled at the defaults ({head(pg)})')
    # "More on Damage Application" in the strip opens this card's Adjust
    pg.evaluate(f"() => {{ document.querySelector('{MC} .dmg-adjust').open = false; }}")
    pg.click(f'{S} details.mys-fpart-range > summary'); pg.wait_for_timeout(150)
    pg.click(f'{S} details.mys-fpart-range [data-act="fight-more"]'); pg.wait_for_timeout(800)
    check(pg.get_attribute(f'{MC} .dmg-adjust', 'open') is not None, f'{W}: "More on" in the strip opens your card\'s Adjust')
    sw = pg.evaluate('document.documentElement.scrollWidth'); check(sw <= W, f'{W}: no sideways scroll ({sw})')
    check(not errs, f'{W}: no page errors {errs}')
    ctx.close()

def pilot(b):
    W = 1440
    ctx = b.new_context(viewport={'width': W, 'height': 1000}); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML); pg.evaluate("localStorage.clear()"); pg.reload()
    save_ship(pg); settle(pg, 300)
    pg.click('#tabBtnPilot')
    pg.evaluate("""async ([a, b]) => {
        const mk = async (text, day) => { const parsed = await parseEftFit(text);
          const est = await estimateHpAndDps(parsed.shipTypeId, parsed.tally, parsed.cargoItemIds, parsed.highSlotByFlag, 'sharpshooter', parsed.midSlotByFlag);
          return {parsed, loss: { km: {killmail_time: day}, killmailId: 1, tally: parsed.tally, highSlotByFlag: parsed.highSlotByFlag, estimate: est,
            input: {shipTypeId: parsed.shipTypeId, tally: parsed.tally, cargoItemIds: parsed.cargoItemIds, highSlotByFlag: parsed.highSlotByFlag, midSlotByFlag: parsed.midSlotByFlag} }}; };
        const x = await mk(a, '2026-10-01T00:00:00Z'), y = await mk(b, '2026-10-02T00:00:00Z');
        const idToName = new Map([...x.parsed.idToName, ...y.parsed.idToName]);
        renderFitTabs('Test Pilot', 'Mixed', [x.loss, y.loss], idToName); }""", [HECATE, ARBITRATOR])
    settle(pg, 800)
    out = []
    for i in (0, 1):
        pg.locator('#fitResults .assess-tabs button').nth(i).click(); settle(pg, 400)
        P = f'#fitResults .subtab-panel[data-idx="{i}"]'
        pg.click(f'{P} .mys-sw-btn.is-mine'); settle(pg, 600)
        if not pg.locator(f'{P} .mys-mine-view .fl-dmg .dmg-card').count(): pg.locator(f'{P} .mys-mine-view .fl-dmg .cc-toggle[data-card="dmg"]').first.click(); settle(pg, 300)
        pg.wait_for_selector(f'{P} .mys-mine-view .fl-dmg .dmg-card [data-out="head"]:not(:empty)', timeout=60000)
        out.append((pg.inner_text(f'{P} .mys-mine-view .dmg-vs'), pg.inner_text(f'{P} .mys-mine-view [data-out="head"]'), board_your(pg, P)))
        pg.click(f'{P} .mys-sw-btn.is-threat'); settle(pg, 300)
    # (the tag is the loss tabs' shared label, the pilot's hull; here 'Mixed': the two tabs carry different fits)
    check(all(o[0] == 'applied to the Mixed · Test Pilot' for o in out) and all(o[1] == o[2] for o in out) and out[0][1] != out[1][1],
          f'Pilot losses: each tab\'s card charts against that tab\'s threat, = its board ({out})')
    check(not errs, f'Pilot losses: no page errors {errs}')
    ctx.close()

def phone(b):
    W = 375
    ctx = b.new_context(viewport={'width': W, 'height': 740}, is_mobile=True, has_touch=True); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML); pg.evaluate("localStorage.clear()"); pg.reload()
    pg.tap('#tabBtnFit'); pg.fill('#fitAnalyzerInput', HECATE); pg.tap('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout'); settle(pg)
    save_ship(pg); settle(pg, 800)
    pg.tap(f'{R} .mys-sw-btn.is-mine .mys-half-head'); pg.wait_for_selector(f'{MV} .fl-dmg'); settle(pg, 600)   # v.58: a tap on a time opens its why panel
    check(pg.locator(f'{MV} .fl-dmg .cc-closed').count() == 1, 'phone: your card starts collapsed')
    try: pg.wait_for_function(f"() => /DPS applied to the Hecate at/.test(document.querySelector('{MV} .fl-dmg .cc-sum').textContent)", timeout=20000); ok = True
    except Exception: ok = False
    check(ok, f"phone: the collapsed row has the headline ({pg.inner_text(f'{MV} .fl-dmg .cc-sum')!r})")
    check(pg.locator(f'{MV} .fl-dmg').bounding_box()['y'] < pg.locator(f'{MV} .fl-beat').bounding_box()['y'], 'phone: your card is first')
    pg.tap(f'{MV} .fl-dmg .cc-toggle[data-card="dmg"]'); settle(pg, 400)
    pg.wait_for_selector(f'{MC} [data-out="head"]:not(:empty)', timeout=60000)
    svg = pg.locator(f'{MC} .dmg-svg').bounding_box()
    check(svg['x'] >= 0 and svg['x'] + svg['width'] <= W and head(pg) == board_your(pg), f'phone: chart inside the screen, headline {head(pg)} = the board')
    check(pg.get_attribute(f'{MC} .dmg-adjust', 'open') is None, 'phone: Adjust starts closed')
    pg.tap(f'{MC} .dmg-adjust > summary'); pg.wait_for_timeout(150)
    sw = pg.evaluate('document.documentElement.scrollWidth'); check(sw <= W, f'phone: no sideways scroll with Adjust open ({sw})')
    check(not errs, f'phone: no page errors {errs}')
    ctx.close()

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('CHROMIUM', '/opt/pw-browsers/chromium'))
    desktop(b, 1440); desktop(b, 1100); pilot(b); phone(b)
    b.close()
print(f'FAILURES: {fails}')
