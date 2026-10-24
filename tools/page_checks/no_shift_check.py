"""Nothing moves unless you open or close something (subtext rule 4, v2026.10.14.48, roadmap/subtext-plan.md).

    PYFA_SRC=... python3 tools/page_checks/no_shift_check.py [index.html]

the owner (2026-10-24): "when making changes to the damage application slider, numbers change on multiple cards which
causes the content to shuffle and move elements on the page ... this redesign should also address that."

The real page (Fit Analyzer, a Hecate threat against a saved Vexor, ESI served from the SDE) at 1440, 1100 and
375 px. Every Damage Application control is used in turn: each slider at several values, every movement button,
the chart-axis buttons, the prop toggle. After each, every card's top edge and height is compared with the start.
FAILS when a part that the rule already covers moves by more than 1 px (phase S1: the Matchup board and the
Damage Application card; S2: also the Mode row, Weaknesses, EWAR / Misc and Fit, at every width; S3, v.50: every
card, and anything else measured). How far and at which control is printed, so a failure says what moved it.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# The two fits and helpers from matchup_strip_check.py, without running that check: only its top part (before the
# browser block) is executed.
import types
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'matchup_strip_check.py'), encoding='utf-8').read()
M = types.SimpleNamespace(); _ns = {'__file__': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'matchup_strip_check.py')}
exec(compile(_src.split('\nwith sync_playwright()')[0], 'matchup_strip_check.py', 'exec'), _ns)
M.HTML, M.HECATE, M.VEXOR, M.settle = _ns['HTML'], _ns['HECATE'], _ns['VEXOR'], _ns['settle']
from esi_from_sde import route_all
from playwright.sync_api import sync_playwright

HTML = M.HTML
R = '#fitAnalyzerResults'
# These must not move; the set grows as the phases move cards to the rule. S1 (v.48): the Matchup board and the
# Damage Application card on the wide layouts. S2 (v.49): also the Damage Application card on a phone (its headline
# is a number and one line now), the Mode row, Weaknesses (the picks are three single lines per tile), EWAR / Misc
# and the Fit card, at every width. Each of them must also have been measured (a card that isn't found can't move).
# S3 (v.50): also Firepower, Resistance, Navigation & Targeting and Capacitor, so every card on the page; anything
# else measured (a part that isn't a card) fails too.
ALL = {'board', 'dmg', 'tdmode', 'weak', 'ewar', 'fit', 'fp', 'rs', 'nav', 'cp'}
HARD = {1440: ALL, 1100: ALL, 375: ALL}
failures = []
def check(ok, msg):
    print(('OK   ' if ok else 'FAIL ') + msg)
    if not ok: failures.append(msg)

BOXES = r"""() => {
  const out = {};
  const b = document.querySelector('#fitAnalyzerResults .mys-board');
  // the board is sticky on a phone (it stays at the top while scrolling), so only its height is compared
  if(b){ const r = b.getBoundingClientRect(); out['board'] = [getComputedStyle(b.closest('.mys-switch-host') || b).position === 'sticky' ? 0 : r.top + scrollY, r.height]; }
  for(const el of document.querySelectorAll('#fitAnalyzerResults .mys-threat-view .fit-layout > div > *')){
    if(el.offsetParent === null) continue;
    const t = el.querySelector('button.cc-toggle[data-card]');
    const key = el.classList.contains('dmg-card') || el.querySelector('.dmg-card') ? 'dmg' : el.classList.contains('td-mode-card') ? 'tdmode' : t ? t.dataset.card : (el.className.toString().split(' ')[0] || 'part');
    const r = el.getBoundingClientRect(); out[key] = [r.top + scrollY, r.height];
  }
  return out; }"""

def set_input(pg, name, value):
    pg.evaluate(f"""() => {{ const i = document.querySelector('{R} .fl-dmg input[data-in="{name}"]'); if(!i) return;
        if(i.type === 'checkbox') i.checked = {str(bool(value)).lower()}; else i.value = {value};
        i.dispatchEvent(new Event('input', {{bubbles: true}})); }}""")
    pg.wait_for_timeout(200)

def actions(pg):
    """Yields (label, do) for every Damage Application control; each returns the page to a changed state."""
    mx = float(pg.locator(f'{R} .fl-dmg input[data-in="range"]').get_attribute('max'))
    for v in (0, mx * 0.1, mx * 0.3, mx * 0.6, mx):
        yield f'range {v / 1000:g} km', lambda v=v: set_input(pg, 'range', v)
    for v in (0, 50, 100):
        yield f'your speed {v}%', lambda v=v: set_input(pg, 'speedPct', v)
    for v in (25, 300, 100):
        yield f'your signature {v}%', lambda v=v: set_input(pg, 'sigPct', v)
    for v in (100, 50, 0):
        yield f'their speed {v}%', lambda v=v: set_input(pg, 'theirPct', v)
    for seg in ('You', 'Them', 'Chart across'):   # v.51: 'Them' (Stopped / Approach / Orbit) replaced 'Their heading'
        for b in pg.locator(f'{R} .fl-dmg button[data-seg="{seg}"]').all():
            v = b.get_attribute('data-v')
            yield f'{seg}: {v}', lambda b=b: (b.click(), pg.wait_for_timeout(200))
    if pg.locator(f'{R} .fl-dmg input[data-in="prop"]').count():
        yield 'your MWD off', lambda: set_input(pg, 'prop', 0)
        yield 'your MWD on', lambda: set_input(pg, 'prop', 1)
    # v2026.10.14.51 (F1): the fight strip under the Matchup -- every movement choice and the range, each opened,
    # chosen and closed again (an open menu floats over the page; only what's left after closing is compared)
    def strip_pick(part, v):
        pg.click(f'{R} .mys-fight details.mys-fpart-{part} > summary'); pg.wait_for_timeout(150)
        pg.click(f'{R} .mys-fight details.mys-fpart-{part} button.mys-fopt[data-v="{v}"]'); pg.wait_for_timeout(200)
    def strip_range(v):
        pg.click(f'{R} .mys-fight details.mys-fpart-range > summary'); pg.wait_for_timeout(150)
        pg.evaluate(f"""() => {{ const i = document.querySelector('{R} .mys-fight input[data-fset="range"]'); i.value = {v}; i.dispatchEvent(new Event('input', {{bubbles: true}})); }}""")
        pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    for part, vals in (('them', ('toward', 'orbit', 'still')), ('you', ('still', 'straight', 'orbit'))):
        for v in vals:
            yield f'strip {part}: {v}', lambda part=part, v=v: strip_pick(part, v)
    for v in (mx * 0.2, mx * 0.8):
        yield f'strip range {v / 1000:g} km', lambda v=v: strip_range(v)

with sync_playwright() as p:
    b = p.chromium.launch()
    for W in (1440, 1100, 375):
        pg = b.new_context(viewport={'width': W, 'height': 1000}, is_mobile=W < 600, has_touch=W < 600).new_page()
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        route_all(pg); pg.goto('file://' + HTML); pg.evaluate("localStorage.clear()"); pg.reload()
        pg.click('#tabBtnFit'); pg.fill('#fitAnalyzerInput', M.HECATE); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout'); M.settle(pg)
        pg.click('#myShipChip'); pg.fill('#myShipEft', M.VEXOR); pg.click('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-tiles'); pg.keyboard.press('Escape')
        pg.wait_for_function(f"() => {{ const b = document.querySelector('{R} .mys-board'); return b && !/…/.test(b.textContent); }}", timeout=60000); M.settle(pg, 800)
        if pg.locator(f'{R} .fl-dmg .dmg-card').count() == 0:     # phone: the card starts collapsed
            pg.click(f'{R} .fl-dmg .cc-toggle[data-card="dmg"]'); pg.wait_for_timeout(400)
        pg.wait_for_selector(f'{R} .fl-dmg [data-out="head"]:not(:empty)')
        if pg.get_attribute(f'{R} .fl-dmg .dmg-adjust', 'open') is None:
            pg.click(f'{R} .fl-dmg .dmg-adjust > summary'); pg.wait_for_timeout(200)
        M.settle(pg, 400)
        base = pg.evaluate(BOXES)
        check(HARD[W] <= set(base), f'{W}: every card the rule covers is on the page ({sorted(HARD[W] - set(base))} missing)')
        worst = {}
        for label, do in list(actions(pg)):
            do(); M.settle(pg, 150)
            now = pg.evaluate(BOXES)
            for k, (y0, h0) in base.items():
                if k not in now: continue
                d = max(abs(now[k][0] - y0), abs(now[k][1] - h0))
                if d > worst.get(k, (0, ''))[0]: worst[k] = (d, label)
        for k in base:
            d, why = worst.get(k, (0, ''))
            if k in HARD[W]:
                check(d <= 1, f'{W}: {k} stays put while every Damage Application control is used (moved {d:.0f} px{", worst at " + why if d > 1 else ""})')
            else:
                check(d <= 1, f'{W}: {k} (not a card) stays put (moved {d:.0f} px{", worst at " + why if d > 1 else ""})')
        check(not errs, f'{W}: no page errors {errs}')
        pg.close()
    b.close()
print(f'FAILURES: {len(failures)}')
sys.exit(1 if failures else 0)
