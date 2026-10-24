"""The fight strip under the Matchup (v2026.10.14.51, fight setup F1; roadmap/turret-application-plan.md "Fight setup
mockup", Option C, board 2b).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/fight_strip_check.py [index.html]   -> 'FAILURES: N' (must be 0)

Erik 2026-10-24: "option C is my preference" (one strip joined under the Matchup, each part under the board's own
column), in-game movement names for both ships, and one fight for both perspectives. The real page (Hecate threat,
saved Vexor, ESI served from the SDE):
  * the strip sits right under the board, its three parts under the board's three columns (1440 and 1100 px);
  * labels: the threat's movement (Stopped by default), the range, your movement and speed, from the card's settings;
    a speed keeps its width (no sliding);
  * each part opens a menu; a choice closes it and sets the SAME setting the Damage Application card's Adjust panel
    sets: the card's buttons and sliders follow, its headline and the board are the page's own dmgModel / mysMatchup;
  * the card's Adjust panel changes the strip too; one part open at a time; Escape and a press outside close it;
  * the My Ship Perspective shares the fight: a change there shows in the threat's card when switching back;
  * Pilot losses: each loss keeps its own fight;
  * Keep at Range (v2026.10.14.53, F2) for both ships: the plan's example (you keeping range from an approaching
    Hecate at 15 km: 0 applied to you, 291 to them, they last 26 s), chosen-but-can't-hold marked amber with the
    reason, not offered inside their scram/web or when the other ship closes faster;
  * "More on Damage Application" opens the card's Adjust panel and scrolls to it;
  * phone (375 px): three parts in a row under the board, each a 44 px target opening a sheet from the bottom, with
    a close button; the collapsed card's row follows a change; no sideways scroll;
  * the board's note is gone (empty unless there's an error) and so is "How effective HP and DPS are calculated"
    (now METHODOLOGY.md). No page errors.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'matchup_strip_check.py'), encoding='utf-8').read()
_ns = {'__file__': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'matchup_strip_check.py')}
exec(compile(_src.split('\nwith sync_playwright()')[0], 'matchup_strip_check.py', 'exec'), _ns)
HTML, HECATE, HECATE3, VEXOR, settle, EXPECT, cells = (_ns[k] for k in ('HTML', 'HECATE', 'HECATE3', 'VEXOR', 'settle', 'EXPECT', 'cells'))
from esi_from_sde import route_all
from playwright.sync_api import sync_playwright

R = '#fitAnalyzerResults'
S = f'{R} .mys-fight'
C = f'{R} .fl-dmg .dmg-card'
failures = []
def check(ok, msg):
    print(('OK   ' if ok else 'FAIL ') + msg)
    if not ok: failures.append(msg)

def label(pg, part, scope=S): return pg.inner_text(f'{scope} [data-fname="{part}"]') + ('' if part == 'range' else (' · ' + pg.inner_text(f'{scope} [data-fnum="{part}"]')).rstrip(' ·'))
def st(pg, sel=C): return pg.evaluate(f"() => document.querySelector('{sel}')._dmg.f.dmg")
def model(pg, sel=C): return pg.evaluate(f"() => {{ const m = document.querySelector('{sel}')._dmg.m; return {{y: dmgFmt(m.ySpeed), t: dmgFmt(m.tSpeed), tTop: dmgFmt(m.theirTop), head: dmgFmt(m.cur.dps)}}; }}")
def pick(pg, part, v, scope=S):
    pg.click(f'{scope} details.mys-fpart-{part} > summary'); pg.wait_for_timeout(150)
    pg.click(f'{scope} details.mys-fpart-{part} button.mys-fopt[data-v="{v}"]'); pg.wait_for_timeout(300)
def pressed(pg, seg, sel=C): return pg.get_attribute(f'{sel} button[data-seg="{seg}"][aria-pressed="true"]', 'data-v')
def open_parts(pg): return pg.evaluate(f"() => [...document.querySelectorAll('{S} details.mys-fpart[open]')].map(d => d.dataset.part)")

# v2026.10.14.52 (Erik's screenshot: "info panel clipping bottom edge of the matchup bar"): the Matchup's info panel
# opens whole -- every corner on screen and not cut off or covered (the board's overflow:hidden clipped it).
PANEL_SEEN = """async () => { const d = document.querySelector('#fitAnalyzerResults .mys-board details.info-pop'); d.open = true;
  const body = d.querySelector('.info-body'); body.scrollIntoView({block: 'nearest'});
  await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  const b = body.getBoundingClientRect();
  const pts = [[b.left + 8, b.top + 8], [b.right - 8, b.top + 8], [b.left + 8, b.bottom - 8], [b.right - 8, b.bottom - 8], [(b.left + b.right) / 2, b.bottom - 8]];
  const hidden = pts.filter(([x, y]) => { const e = document.elementFromPoint(x, y); return !(e && body.contains(e)); }).length;
  const text = body.innerText.includes(CARD_INFO.board[3].slice(0, 40));
  return {hidden, w: Math.round(b.width), h: Math.round(b.height), left: Math.round(b.left), right: Math.round(b.right), text}; }"""
def board_panel(pg, W):
    r = pg.evaluate(PANEL_SEEN)
    check(r['hidden'] == 0 and r['h'] > 150 and r['left'] >= 0 and r['right'] <= W and r['text'], f'{W}: the Matchup\'s info panel opens whole, nothing clipped or covered ({r})')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    check(pg.evaluate("() => !document.querySelector('#fitAnalyzerResults .mys-board details.info-pop[open]')"), f'{W}: Escape closes it')

def load(pg):
    route_all(pg); pg.goto('file://' + HTML); pg.evaluate("localStorage.clear()"); pg.reload()
    pg.click('#tabBtnFit'); pg.fill('#fitAnalyzerInput', HECATE); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout'); settle(pg)
    check('How effective HP and DPS are calculated' not in pg.inner_text(R), 'the methodology note is gone from the page (METHODOLOGY.md)')
    pg.click('#myShipChip'); pg.fill('#myShipEft', VEXOR); pg.click('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-tiles'); pg.keyboard.press('Escape')
    pg.wait_for_function(f"() => {{ const b = document.querySelector('{R} .mys-board'); return b && !/…/.test(b.textContent); }}", timeout=60000); settle(pg, 600)

def desktop(b, W):
    pg = b.new_page(viewport={'width': W, 'height': 900}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    load(pg)
    bb = pg.locator(f'{R} .mys-board').bounding_box(); sb = pg.locator(S).bounding_box()
    th, mid, mine = (pg.locator(f'{R} .mys-board {s}').bounding_box() for s in ('.mys-half.is-threat', '.mys-mid', '.mys-half.is-mine'))
    pt, pr, py = (pg.locator(f'{S} details.mys-fpart-{p}').bounding_box() for p in ('them', 'range', 'you'))
    check(abs(sb['y'] - (bb['y'] + bb['height'])) <= 1 and abs(sb['x'] - bb['x']) <= 1 and abs(sb['width'] - bb['width']) <= 1, f'{W}: the strip is joined right under the board, same width')
    if W >= 900:
        check(abs(pt['x'] - th['x']) <= 2 and abs(pr['x'] - mid['x']) <= 2 and abs(pr['width'] - mid['width']) <= 2 and abs(py['x'] + py['width'] - (mine['x'] + mine['width'])) <= 2,
              f'{W}: three parts under the board\'s three columns (threat {pt["x"]:.0f}/{th["x"]:.0f}, range {pr["x"]:.0f}+{pr["width"]:.0f} / {mid["x"]:.0f}+{mid["width"]:.0f})')
    m0 = model(pg)
    check(label(pg, 'them') == 'Stopped' and label(pg, 'range') == pg.inner_text(f'{C} [data-out="range"]') and label(pg, 'you') == f'Orbit · {m0["y"]} m/s',
          f'{W}: labels from the card ({label(pg, "them")} | {label(pg, "range")} | {label(pg, "you")})')
    check(pg.inner_text(f'{R} .mys-strip-note') == '' and not pg.is_visible(f'{R} .mys-strip-note'), f'{W}: no note under the board')
    board_panel(pg, W)
    # the threat's menu: Orbit
    pg.click(f'{S} details.mys-fpart-them > summary'); pg.wait_for_timeout(150)
    menu = pg.locator(f'{S} details.mys-fpart-them .mys-fmenu').bounding_box()
    check(pg.is_visible(f'{S} details.mys-fpart-them .mys-fmenu') and menu['x'] >= 0 and menu['x'] + menu['width'] <= W
          and pg.get_attribute(f'{S} details.mys-fpart-them button.mys-fopt[aria-pressed="true"]', 'data-v') == 'still', f'{W}: the threat\'s menu opens on screen, Stopped pressed')
    pg.click(f'{S} details.mys-fpart-them button.mys-fopt[data-v="orbit"]'); pg.wait_for_timeout(300)
    m1 = model(pg)
    check(open_parts(pg) == [] and st(pg)['theirMode'] == 'orbit' and pressed(pg, 'Them') == 'orbit' and pg.is_enabled(f'{C} input[data-in="theirPct"]')
          and label(pg, 'them') == f'Orbit · {m1["t"]} m/s' and m1['t'] == m1['tTop'], f'{W}: Orbit chosen: the menu closes, the card\'s Them is Orbit, their speed slider on ({label(pg, "them")})')
    check(cells(pg) == pg.evaluate(EXPECT, R) and cells(pg)['their'] == pg.inner_text(f'{C} [data-out="head"]') == m1['head'], f'{W}: the board and the card headline follow ({m1["head"]})')
    # range menu
    pg.click(f'{S} details.mys-fpart-range > summary'); pg.wait_for_timeout(150)
    pg.evaluate(f"""() => {{ const i = document.querySelector('{S} input[data-fset="range"]'); i.value = 9000; i.dispatchEvent(new Event('input', {{bubbles: true}})); }}"""); pg.wait_for_timeout(300)
    check(st(pg)['range'] == 9000 and pg.inner_text(f'{C} [data-out="range"]') == '9 km' and pg.input_value(f'{C} input[data-in="range"]') == '9000' and label(pg, 'range') == '9 km'
          and cells(pg) == pg.evaluate(EXPECT, R), f'{W}: the range slider in the strip moves the card\'s range and the board')
    # one part open at a time; Escape; a press outside
    pg.click(f'{S} details.mys-fpart-you > summary'); pg.wait_for_timeout(150)
    check(open_parts(pg) == ['you'], f'{W}: one part open at a time ({open_parts(pg)})')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    check(open_parts(pg) == [], f'{W}: Escape closes it')
    pg.click(f'{S} details.mys-fpart-you > summary'); pg.wait_for_timeout(150)
    pg.mouse.click(5, 5); pg.wait_for_timeout(150)
    check(open_parts(pg) == [], f'{W}: a press outside closes it')
    # the card changes the strip
    pg.click(f'{C} button[data-seg="You"][data-v="straight"]'); pg.wait_for_timeout(300)
    check(label(pg, 'you').startswith('Approach · ') and st(pg)['mode'] == 'straight', f'{W}: the card\'s Adjust changes the strip ({label(pg, "you")})')
    pick(pg, 'you', 'still')
    check(label(pg, 'you') == 'Stopped' and pressed(pg, 'You') == 'still' and pg.is_disabled(f'{C} input[data-in="speedPct"]') and pg.is_disabled(f'{S} input[data-fset="speedPct"]'),
          f'{W}: You Stopped: the speed sliders are greyed out (they keep their place)')
    # the My Ship Perspective shares the fight
    pg.click(f'{R} .mys-sw-btn.is-mine'); pg.wait_for_selector(f'{R} .mys-mine-view .fit-layout'); settle(pg)
    check(pg.is_visible(S), f'{W}: the strip stays in the My Ship Perspective')
    pick(pg, 'them', 'toward')
    c_mine = cells(pg)
    pg.click(f'{R} .mys-sw-btn.is-threat'); pg.wait_for_timeout(500); settle(pg)
    check(st(pg)['theirMode'] == 'toward' and pressed(pg, 'Them') == 'toward' and cells(pg) == c_mine == pg.evaluate(EXPECT, R) and pg.inner_text(f'{C} [data-out="head"]') == c_mine['their'],
          f'{W}: one fight: Approach set in the My Ship Perspective is on the threat\'s card ({c_mine["their"]})')
    # v2026.10.14.53 (F2): Keep at Range -- the example from turret-application-plan.md: the Hecate approaching at full
    # speed, you keeping range at 15 km (you're faster, outside its 9 km scram and 10 km web) -> nothing applied to you,
    # 291 applied to them, they last 26 s
    if W == 1440:
        pick(pg, 'them', 'toward'); pg.evaluate(f"""() => {{ mysFightSet(document.querySelector('{R} .mys-switch-host'), 'theirPct', 100); mysFightSet(document.querySelector('{R} .mys-switch-host'), 'range', 15000); }}"""); pg.wait_for_timeout(300)
        pick(pg, 'you', 'keep')
        c = cells(pg); mk = model(pg)
        check(st(pg)['mode'] == 'keep' and pressed(pg, 'You') == 'keep' and pg.is_disabled(f'{C} input[data-in="speedPct"]') and label(pg, 'you') == f'Keep at Range · {mk["t"]} m/s' and mk['y'] == mk['t']
              and c == pg.evaluate(EXPECT, R) and (c['their'], c['youLast'], c['your'], c['theyLast']) == ('0', 'holds', '291', '26 s'),
              f'{W}: Keep at Range at 15 km, the Hecate approaching: you move at its speed ({mk["y"]} m/s); the plan\'s example: {c}')
        check('holding' in pg.inner_text(f'{C} [data-out="speed"]') and pg.locator(f'{S} .mys-fseg.is-warn').count() == 0, f'{W}: Keep at Range holds: "{pg.inner_text(f"{C} [data-out=speed]")}", no warning')
        pg.evaluate(f"""() => mysFightSet(document.querySelector('{R} .mys-switch-host'), 'range', 5000)"""); pg.wait_for_timeout(300)
        why = pg.get_attribute(f'{S} details.mys-fpart-you > summary', 'title') or ''
        check(pg.locator(f'{S} details.mys-fpart-you > summary.is-warn').count() == 1 and 'scram (9 km)' in why and 'web (10 km)' in why
              and 'is-warn' in (pg.get_attribute(f'{C} button[data-seg="You"][data-v="keep"]', 'class') or '') and "can't hold" in pg.inner_text(f'{C} [data-out="speed"]') and cells(pg) == pg.evaluate(EXPECT, R),
              f'{W}: moved inside their scram and web at 5 km: Keep at Range stays chosen, marked amber ("{why}")')
        pick(pg, 'you', 'orbit')
        pg.click(f'{S} details.mys-fpart-you > summary'); pg.wait_for_timeout(150)
        kb = f'{S} details.mys-fpart-you button.mys-fopt[data-v="keep"]'
        check(pg.is_disabled(kb) and 'inside their scram' in pg.inner_text(kb) and pg.is_disabled(f'{C} button[data-seg="You"][data-v="keep"]'),
              f'{W}: inside their tackle Keep at Range isn\'t offered ("{pg.inner_text(kb)}")')
        pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
        # their Keep at Range: you approach faster than the Hecate can fly -> not offered
        pg.evaluate(f"""() => {{ const h = document.querySelector('{R} .mys-switch-host'); mysFightSet(h, 'range', 15000); mysFightSet(h, 'mode', 'straight'); mysFightSet(h, 'speedPct', 100); }}"""); pg.wait_for_timeout(300)
        tb = f'{S} details.mys-fpart-them button.mys-fopt[data-v="keep"]'
        pg.click(f'{S} details.mys-fpart-them > summary'); pg.wait_for_timeout(150)
        check(pg.is_disabled(tb) and "you're faster" in pg.inner_text(tb), f'{W}: you approach faster than they fly: their Keep at Range isn\'t offered ("{pg.inner_text(tb)}")')
        pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
        pg.evaluate(f"""() => mysFightSet(document.querySelector('{R} .mys-switch-host'), 'speedPct', 60)"""); pg.wait_for_timeout(300)
        pick(pg, 'them', 'keep'); mk = model(pg)
        check(st(pg)['theirMode'] == 'keep' and mk['t'] == mk['y'] and label(pg, 'them') == f'Keep at Range · {mk["t"]} m/s' and cells(pg) == pg.evaluate(EXPECT, R),
              f'{W}: you approach at 60%: they keep range at your speed ({mk["t"]} m/s)')
        pick(pg, 'them', 'toward'); pick(pg, 'you', 'still')
    # More on Damage Application
    pg.evaluate("window.scrollTo(0, 0)")
    pg.click(f'{S} details.mys-fpart-range > summary'); pg.wait_for_timeout(150)
    pg.click(f'{S} details.mys-fpart-range [data-act="fight-more"]'); pg.wait_for_timeout(1200)
    top = pg.evaluate(f"() => document.querySelector('{C}').getBoundingClientRect().top")
    check(pg.get_attribute(f'{C} .dmg-adjust', 'open') is not None and -5 <= top <= 120 and open_parts(pg) == [], f'{W}: "More on" opens Adjust and scrolls to the card (top {top:.0f})')
    check(pg.evaluate('document.documentElement.scrollWidth') <= W, f'{W}: no sideways scroll')
    # Pilot losses: each loss keeps its own fight
    if W == 1440:
        pg.click('#tabBtnPilot')
        pg.evaluate("""async ([a, b]) => { const mk = async (text, day) => { const parsed = await parseEftFit(text);
            const est = await estimateHpAndDps(parsed.shipTypeId, parsed.tally, parsed.cargoItemIds, parsed.highSlotByFlag, 'sharpshooter', parsed.midSlotByFlag);
            return {parsed, fit: { km: {killmail_time: day}, killmailId: 1, tally: parsed.tally, highSlotByFlag: parsed.highSlotByFlag, estimate: est,
              input: {shipTypeId: parsed.shipTypeId, tally: parsed.tally, cargoItemIds: parsed.cargoItemIds, highSlotByFlag: parsed.highSlotByFlag, midSlotByFlag: parsed.midSlotByFlag} }}; };
            const x = await mk(a, '2026-10-01T00:00:00Z'), y = await mk(b, '2026-10-02T00:00:00Z');
            renderFitTabs('Test Pilot', 'Hecate', [x.fit, y.fit], x.parsed.idToName); }""", [HECATE, HECATE3])
        V0, V1 = '#fitResults .subtab-panel[data-idx="0"]', '#fitResults .subtab-panel[data-idx="1"]'
        pg.wait_for_function(f"() => {{ const b = document.querySelector('{V0} .mys-board'); return b && !/…/.test(b.textContent); }}", timeout=60000); settle(pg)
        pg.locator('#fitResults .subtab-btn').nth(1).click(); pg.wait_for_timeout(500)
        pg.wait_for_function(f"() => {{ const b = document.querySelector('{V1} .mys-board'); return b && !/…/.test(b.textContent); }}", timeout=60000); settle(pg)
        pick(pg, 'them', 'orbit', f'{V1} .mys-fight')
        t1 = pg.evaluate(f"() => [document.querySelector('{V0} .fl-dmg')._dmgF.dmg, document.querySelector('{V1} .fl-dmg')._dmgF.dmg].map(s => s ? s.theirMode : null)")
        check(t1[1] == 'orbit' and t1[0] != 'orbit' and cells(pg, V1) == pg.evaluate(EXPECT, V1) and label(pg, 'them', f'{V1} .mys-fight').startswith('Orbit'),
              f'Pilot losses: the second loss\'s strip sets only its own fight ({t1})')
    check(not errs, f'{W}: no page errors {errs}')
    pg.close()

def phone(b):
    W = 375
    pg = b.new_context(viewport={'width': W, 'height': 800}, is_mobile=True, has_touch=True).new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    load(pg)
    board_panel(pg, W)
    pg.evaluate("window.scrollTo(0, 0)")
    parts = [pg.locator(f'{S} details.mys-fpart-{p} > summary').bounding_box() for p in ('them', 'range', 'you')]
    check(all(abs(p['y'] - parts[0]['y']) <= 1 and p['height'] >= 44 for p in parts) and parts[0]['x'] < parts[1]['x'] < parts[2]['x'] and parts[2]['x'] + parts[2]['width'] <= W,
          f'{W}: three parts in a row, 44 px targets ({[round(p["height"]) for p in parts]})')
    pg.click(f'{S} details.mys-fpart-you > summary'); pg.wait_for_timeout(200)
    sh = pg.locator(f'{S} details.mys-fpart-you .mys-fmenu').bounding_box()
    check(sh['x'] >= -1 and sh['x'] + sh['width'] <= W + 1 and abs(sh['y'] + sh['height'] - 800) <= 2 and pg.is_visible(f'{S} details.mys-fpart-you .info-close'), f'{W}: a sheet from the bottom with a close button')
    pg.click(f'{S} details.mys-fpart-you button.mys-fopt[data-v="straight"]'); pg.wait_for_timeout(500)
    row = pg.inner_text(f'{R} .fl-dmg .cc-row[data-card="dmg"] .cc-sum') if pg.locator(f'{R} .fl-dmg .cc-row[data-card="dmg"]').count() else ''
    check(open_parts(pg) == [] and 'approaching' in row, f'{W}: Approach closes the sheet; the collapsed card\'s row follows ("{row}")')
    pg.click(f'{S} details.mys-fpart-them > summary'); pg.wait_for_timeout(200)
    pg.click(f'{S} details.mys-fpart-them .info-close'); pg.wait_for_timeout(200)
    check(open_parts(pg) == [], f'{W}: the close button closes the sheet')
    pg.click(f'{S} details.mys-fpart-range > summary'); pg.wait_for_timeout(200)
    pg.click(f'{S} details.mys-fpart-range [data-act="fight-more"]'); pg.wait_for_timeout(1500)
    check(pg.locator(f'{R} .fl-dmg .dmg-card').count() == 1 and pg.get_attribute(f'{R} .fl-dmg .dmg-adjust', 'open') is not None, f'{W}: "More on" opens the collapsed card and its Adjust panel')
    check(pg.evaluate('document.documentElement.scrollWidth') <= W, f'{W}: no sideways scroll')
    check(not errs, f'{W}: no page errors {errs}')
    pg.close()

with sync_playwright() as p:
    b = p.chromium.launch()
    desktop(b, 1440)
    desktop(b, 1100)
    phone(b)
    b.close()
print(f'FAILURES: {len(failures)}')
sys.exit(1 if failures else 0)
