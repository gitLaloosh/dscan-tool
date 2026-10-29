"""The UI rules in the real page (v2026.10.29.7; CLAUDE.md "UI rules"; the static half: tools/check_ui_rules.py).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/ui_rules_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner approved the controls mockup on 2026-10-29: one tag, one switch, one slider, one text field. The real page
(Hecate threat, saved Vexor, ESI served from the SDE, as tools/page_checks/fight_strip_check.py):
  * tags: the header's Standings and My Ship chips have 4px corners, no visible border at rest, the tag fill;
  * one switch: "Use in assessments" is 36x20 with 3px corners, #1f6f80 when on;
  * one slider: every slider on the page is filled to its handle (--p matches its value) when a card renders, after a
    keyboard move, and after code sets the value (a movement picked in the fight strip moves its speed slider);
  * one text field: the fit box at rest has the quiet border; focused, a cyan border and the cyan ring (was amber);
    hovered, the brighter border;
  * no page errors.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'matchup_strip_check.py'), encoding='utf-8').read()
_ns = {'__file__': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'matchup_strip_check.py')}
exec(compile(_src.split('\nwith sync_playwright()')[0], 'matchup_strip_check.py', 'exec'), _ns)
HTML, HECATE, VEXOR, settle = (_ns[k] for k in ('HTML', 'HECATE', 'VEXOR', 'settle'))
from esi_from_sde import route_all
from playwright.sync_api import sync_playwright

R = '#fitAnalyzerResults'
failures = []
def check(ok, msg):
    print(('OK   ' if ok else 'FAIL ') + msg)
    if not ok: failures.append(msg)

FILLS = """() => [...document.querySelectorAll('input[type="range"]')].map(r => {
  const lo = +r.min || 0, hi = r.max === '' ? 100 : +r.max, want = hi > lo ? (r.value - lo) / (hi - lo) * 100 : 0;
  const got = parseFloat(r.style.getPropertyValue('--p'));
  return {k: r.dataset.in || r.dataset.fset || '?', want: Math.round(want * 10) / 10, got: Number.isNaN(got) ? null : Math.round(got * 10) / 10}; })"""
def fills_ok(pg, what):
    f = pg.evaluate(FILLS); bad = [x for x in f if x['got'] is None or abs(x['got'] - x['want']) > 0.2]
    check(len(f) > 0 and not bad, f'{what}: every slider filled to its handle ({len(f)} sliders; wrong: {bad[:4]})')
def cs(pg, sel, *props):
    return pg.evaluate(f"(ps) => {{ const c = getComputedStyle(document.querySelector({sel!r})); return ps.map(p => c.getPropertyValue(p)); }}", list(props))

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1440, 'height': 900}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML); pg.evaluate("localStorage.clear()"); pg.reload()

    # tags
    for sel in ('#myShipChip', 'button.side-chip'):
        rad, bst, bc, bg = cs(pg, sel, 'border-top-left-radius', 'border-top-style', 'border-top-color', 'background-color')
        check(rad == '4px' and bst != 'dashed' and bc in ('rgba(0, 0, 0, 0)', 'transparent') and bg == 'rgb(26, 33, 40)',
              f'{sel}: a tag (4px corners, no dashed or visible border, the tag fill) ({rad}, {bst}, {bc}, {bg})')

    # text field: the fit box
    pg.click('#tabBtnFit')
    rest = cs(pg, '#fitAnalyzerInput', 'border-top-color', 'border-top-left-radius')
    check(rest == ['rgb(42, 52, 61)', '4px'], f'the fit box at rest: the quiet border, 4px corners ({rest})')
    pg.hover('#fitAnalyzerInput'); pg.wait_for_timeout(100)
    hov = cs(pg, '#fitAnalyzerInput', 'border-top-color')
    check(hov == ['rgb(58, 70, 80)'], f'hovered: the brighter border ({hov})')
    pg.focus('#fitAnalyzerInput'); pg.wait_for_timeout(100)
    foc, ring = cs(pg, '#fitAnalyzerInput', 'border-top-color', 'box-shadow')
    check(foc == 'rgb(79, 195, 217)' and ('rgba(79, 195, 217' in ring or 'srgb 0.309804 0.764706 0.85098' in ring) and ring.endswith(' 2px'), f'focused: the cyan border and the ring, never amber ({foc}; {ring})')

    pg.fill('#fitAnalyzerInput', HECATE); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout'); settle(pg)
    pg.click('#myShipChip'); pg.fill('#myShipEft', VEXOR); pg.click('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-tiles'); pg.keyboard.press('Escape')
    pg.wait_for_function(f"() => {{ const b = document.querySelector('{R} .mys-board'); return b && !/…/.test(b.textContent); }}", timeout=60000); settle(pg, 600)

    # switch
    bx = pg.locator('input.mys-sw').first.bounding_box()
    rad, on = cs(pg, 'input.mys-sw', 'border-top-left-radius', 'background-color')
    checked = pg.evaluate("() => document.querySelector('input.mys-sw').checked")
    check(round(bx['width']) == 36 and round(bx['height']) == 20 and rad == '3px' and (not checked or on == 'rgb(31, 111, 128)'),
          f'"Use in assessments": one switch, 36x20, 3px corners, #1f6f80 on ({bx["width"]}x{bx["height"]}, {rad}, {on}, on={checked})')

    # sliders
    pg.wait_for_timeout(200); fills_ok(pg, 'the fit rendered')
    sl = pg.locator(f'{R} .dmg-ctl input[type="range"]').first
    if sl.count():
        v0 = sl.input_value(); sl.focus(); [pg.keyboard.press('ArrowRight') for _ in range(5)]; pg.wait_for_timeout(200)
        check(sl.input_value() != v0, f'the Damage Application range moved by keyboard ({v0} -> {sl.input_value()})')
        fills_ok(pg, 'after five keyboard steps on the Damage Application range')
    pg.click(f'{R} .mys-fight details.mys-fpart-them > summary'); pg.wait_for_timeout(150)
    pg.click(f'{R} .mys-fight details.mys-fpart-them button.mys-fopt[data-v="toward"]'); pg.wait_for_timeout(300)
    pg.evaluate(f"() => {{ const s = document.querySelector('{R} .mys-fight input[data-fset=\"theirPct\"]'); s.value = 40; s.dispatchEvent(new Event('input', {{bubbles: true}})); }}"); pg.wait_for_timeout(300)
    fills_ok(pg, 'after their speed set to 40% and the strip re-synced by code')
    pg.keyboard.press('Escape')
    pg.screenshot(path=os.environ.get('UI_SHOT', '/tmp/ui_rules_check.png'), full_page=False)

    check(not errs, f'no page errors ({errs[:2]})')
    b.close()
print(f'FAILURES: {len(failures)}')
sys.exit(1 if failures else 0)
