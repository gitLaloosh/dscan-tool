"""The "why" behind "you last" / "they last", and the Weaknesses card's title (v2026.10.14.58).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/ttk_why_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner 2026-10-24: "Option A works for the board" (a sentence or two in a panel on hover / tap), and for Weaknesses
"Threat Weaknesses" and "Your Weaknesses" in the perspective's colour, no "your guns" / "their guns" pill, the
capacitor under the picks. The times in the words are checked against pyfa's inputs by
tools/independent_checks/check_matchup.py and the sentence kinds by regression_suite/run_regression.mjs; this checks
the page, with the owner's two fits (tools/independent_checks/fits/) at 48.9 km, the Orthrus stopped, you orbiting:
  * desktop (1440 px): "you last" / "they last" are underlined; a mouse over the number shows the panel under it with
    exactly the expected words (the page's own mysMatchup words too) and it goes when the mouse leaves; a mouse click
    still switches the view; Tab onto a half shows its time's panel, Tab off hides it; Escape hides it; the halves
    are described by the same words for a screen reader; nothing on the page moves when the panel shows;
  * Weaknesses: "Threat Weaknesses" (amber) on the threat's view, "Your Weaknesses" (cyan) on the My ship view and
    on "Viewing my ship", open and collapsed, the word and the name on one baseline (v.59); no "your guns" / "their guns" tags; the capacitor row comes after the
    picks and the generic tiles;
  * phone (375 px, touch): a tap on the number opens the panel as a sheet and doesn't switch the view; its close
    button and a tap outside close it; a tap on the label under it, or elsewhere on the half, still switches; no
    sideways scrolling;
  * v2026.10.14.61: an Ancillary Armor Repairer with paste as my ship: the panel's words are the page's own and say what
    the repairer did with its paste.
No page errors anywhere.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esi_from_sde import route_all
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
FITS = os.path.join(HERE, '..', 'independent_checks', 'fits')
ORTHRUS = open(os.path.join(FITS, 'orthrus_threat.eft'), encoding='utf-8').read()
OSPREY = open(os.path.join(FITS, 'osprey_navy_issue_mine.eft'), encoding='utf-8').read()
YOU = {'title': 'You last 1 min 27 s', 'text': [
    "Your shield breaks at 1:06, 21 s into your X-Large Ancillary Shield Booster's first reload: it repairs 196 HP/s for 45 s, then reloads for 1 min.",
    'With no armor or hull repairer, the rest goes in 21 s.']}
THEM = {'title': 'They last 7 min 20 s', 'text': [
    'Their X-Large Ancillary Shield Booster has 9 charges, one clip: it repairs 196 HP/s for 45 s, then has nothing left to load.',
    "Their shield's regen alone can't keep up, and it breaks at 5:40.",
    'With no armor or hull repairer, the rest goes in 1 min 40 s.']}

fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok

R = '#fitAnalyzerResults'
TV, MV = f'{R} .mys-threat-view', f'{R} .mys-mine-view'
HOST = f'{R} .mys-switch-host'
POP = '.info-body.ttk-why'
def settle(pg, ms=400):
    pg.wait_for_timeout(ms); pg.wait_for_function("() => !document.querySelector('.fit-card-busy')", timeout=60000); pg.wait_for_timeout(ms)
def shown(pg):
    return pg.evaluate(f"() => {{ const e = document.querySelector('{POP}'); return !!e && !e.hidden && getComputedStyle(e).display !== 'none'; }}")
def panel(pg):
    return pg.evaluate(f"""() => {{ const e = document.querySelector('{POP}'); if(!e) return null;
        return {{title: e.querySelector('.ttk-why-title').textContent, text: [...e.querySelectorAll('.ttk-why-text p')].map(p => p.textContent),
                 role: e.getAttribute('role'), pos: getComputedStyle(e).position, box: e.getBoundingClientRect().toJSON()}}; }}""")
def view(pg): return pg.evaluate(f"() => document.querySelector('{HOST}').dataset.view")
def title(pg, scope, card='weak'):
    sel = f'{scope} button.cc-toggle[data-card="{card}"]'
    return ' '.join(pg.inner_text(sel).split()).lower() if pg.locator(sel).count() else ''
def who_color(pg, scope):
    return pg.evaluate(f"""() => {{ const v = [...document.querySelectorAll('{scope} button.cc-toggle[data-card="weak"] .wk-who')].find(e => getComputedStyle(e).display !== 'none');
        const probe = document.createElement('span'); probe.style.color = v && v.classList.contains('wk-mine') ? 'var(--cyan)' : 'var(--amber)'; document.body.appendChild(probe);
        const want = getComputedStyle(probe).color; probe.remove(); return v ? [v.textContent, getComputedStyle(v).color === want] : null; }}""")
def baselines(pg, scope):
    """v.59 (the owner's screenshot: "alignment issue"): the baseline of the shown "Threat" / "Your" and of "Weaknesses":
    each text's box (a Range) less its font's descent (canvas measureText, the same font), so it doesn't matter whether
    the text is a flex item or inline"""
    return pg.evaluate(f"""() => {{ const b = document.querySelector('{scope} button.cc-toggle[data-card="weak"]'); if(!b) return null;
        const ctx = document.createElement('canvas').getContext('2d');
        const at = (node) => {{ const st = getComputedStyle(node.parentElement); ctx.font = `${{st.fontWeight}} ${{st.fontSize}} ${{st.fontFamily}}`;
          const r = document.createRange(); r.selectNodeContents(node); return r.getBoundingClientRect().bottom - ctx.measureText(node.textContent).fontBoundingBoxDescent; }};
        const who = [...b.querySelectorAll('.wk-who')].find(e => getComputedStyle(e).display !== 'none');
        const name = [...b.querySelectorAll('*'), b].flatMap(e => [...e.childNodes]).find(n => n.nodeType === 3 && /Weaknesses/.test(n.textContent));
        return who && name ? [Math.round(at(who.firstChild) * 10) / 10, Math.round(at(name) * 10) / 10] : null; }}""")
def order_ok(pg, scope):
    """the capacitor rows after the picks and the generic tiles (DOCUMENT_POSITION_FOLLOWING = 4)"""
    return pg.evaluate(f"""() => {{ const c = document.querySelector('{scope} .fl-beat .weak-cap'), p = document.querySelector('{scope} .fl-beat .weak-picks'), g = document.querySelector('{scope} .fl-beat .weak-generic');
        return !!(c && p && g && (p.compareDocumentPosition(c) & 4) && (g.compareDocumentPosition(c) & 4) && c.querySelector('.cap-gauge')) ? c.querySelector('.cap-gauge-value').textContent : null; }}""")
def layout(pg):
    return pg.evaluate("() => [...document.querySelectorAll('#fitAnalyzerResults .mys-board, #fitAnalyzerResults .mys-fight, #fitAnalyzerResults .fl-beat, #fitAnalyzerResults .fl-dmg')].map(e => JSON.stringify(e.getBoundingClientRect()))")
SETUP_RANGE = f"() => {{ const h = document.querySelector('{HOST}'); mysFightSet(h, 'range', 48900, false); }}"

def desktop(b):
    ctx = b.new_context(viewport={'width': 1440, 'height': 1000}); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML); pg.evaluate("localStorage.removeItem('dscanMyShip')"); pg.reload()
    pg.click('#tabBtnFit'); pg.fill('#fitAnalyzerInput', ORTHRUS); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout'); settle(pg)
    check(title(pg, TV) == 'threat weaknesses' and who_color(pg, TV) == ['Threat', True], f'no ship saved: "{title(pg, TV)}", {who_color(pg, TV)}')
    bl = baselines(pg, TV)
    check(bl and abs(bl[0] - bl[1]) < 0.5, f'"Threat" and "Weaknesses" on one baseline (open card: {bl})')
    pg.click('#myShipChip'); pg.fill('#myShipEft', OSPREY); pg.click('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-tiles'); pg.keyboard.press('Escape')
    pg.wait_for_selector(f'{HOST} .mys-board'); settle(pg, 800)
    pg.evaluate(SETUP_RANGE); settle(pg, 1200)
    cells = pg.evaluate(f"() => Object.fromEntries([...document.querySelectorAll('{HOST} [data-cell]')].map(c => [c.dataset.cell, (c.querySelector('.mys-cell-v') || c).textContent]))")
    check(cells.get('their') == '470' and cells.get('theyLast') == '7 min 20 s' and cells.get('youLast') == '1 min 27 s' and cells.get('your') == '88', f'board at 48.9 km: {cells}')
    under = pg.evaluate(f"() => ['youLast', 'theyLast', 'their', 'your'].map(k => {{ const s = getComputedStyle(document.querySelector('{HOST} [data-cell=\"' + k + '\"] .mys-cell-v')); return s.textDecorationLine + ' ' + s.textDecorationStyle + ' ' + s.cursor; }})")
    check(under[0].startswith('underline dotted') and under[1].startswith('underline dotted') and 'underline' not in under[2] and 'underline' not in under[3] and under[0].endswith('help'),
          f'"you last" / "they last" dotted underline, the DPS numbers not ({under})')
    words = pg.evaluate(f"() => document.querySelector('{HOST}')._why")
    check(words == {'you': YOU, 'them': THEM}, f'the page\'s own words for the owner\'s fits: {words}')
    sr = pg.evaluate(f"""() => [...document.querySelectorAll('{HOST} button.mys-sw-btn')].map(b => {{ const d = document.getElementById(b.getAttribute('aria-describedby')); return d ? d.textContent : null; }})""")
    check(sr == [f"{THEM['title']}. {' '.join(THEM['text'])}", f"{YOU['title']}. {' '.join(YOU['text'])}"], f'screen reader: each half described by its time\'s words ({[x and x[:40] for x in sr]})')
    # hover
    before = layout(pg)
    cell = pg.locator(f'{HOST} [data-cell="youLast"] .mys-cell-v'); cell.scroll_into_view_if_needed(); cell.hover(); pg.wait_for_timeout(250)
    p = panel(pg); cb = pg.locator(f'{HOST} [data-cell="youLast"]').bounding_box()
    check(shown(pg) and p['title'] == YOU['title'] and p['text'] == YOU['text'] and p['role'] == 'tooltip', f'hover "you last": {p and (p["title"], p["role"])}')
    check(p['box']['top'] >= cb['y'] + cb['height'] - 0.5 and p['box']['left'] >= 15.5 and p['box']['right'] <= 1440 - 15.5 and abs(p['box']['width'] - 360) < 1,
          f'hover: the panel is under the number, inside the page, 360 px wide ({p["box"]["left"]:.0f}-{p["box"]["right"]:.0f}, top {p["box"]["top"]:.0f} vs cell bottom {cb["y"] + cb["height"]:.0f})')
    check(layout(pg) == before, 'hover: nothing on the page moves')
    pg.mouse.move(5, 5); pg.wait_for_timeout(200)
    check(not shown(pg), 'mouse leaves: the panel goes')
    pg.locator(f'{HOST} [data-cell="theyLast"] .mys-cell-v').hover(); pg.wait_for_timeout(250)
    p = panel(pg)
    check(shown(pg) and p['title'] == THEM['title'] and p['text'] == THEM['text'], f'hover "they last": {p and p["title"]}')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    check(not shown(pg), 'Escape hides it')
    # a mouse click on the number still switches the view
    pg.locator(f'{HOST} [data-cell="youLast"] .mys-cell-v').click(); settle(pg, 900)
    check(view(pg) == 'mine' and (not shown(pg) or panel(pg)['role'] == 'tooltip'), f'mouse click on "you last": the view switches ({view(pg)}), no sheet')
    pg.mouse.move(5, 5); pg.wait_for_timeout(150)
    pg.wait_for_selector(f'{MV} .fl-beat .weak-picks .wp-stat', timeout=60000); settle(pg)
    check(title(pg, MV) == 'your weaknesses' and who_color(pg, MV) == ['Your', True], f'My ship view: "{title(pg, MV)}", {who_color(pg, MV)}')
    bl = baselines(pg, MV)
    check(bl and abs(bl[0] - bl[1]) < 0.5, f'"Your" and "Weaknesses" on one baseline (open card: {bl})')
    cap_m = order_ok(pg, MV)
    check(cap_m is not None, f'My ship view: the capacitor ({cap_m}) after the picks and the tiles')
    pg.click(f'{R} .mys-sw-btn.is-threat'); settle(pg, 900); pg.wait_for_selector(f'{TV} .fl-beat .weak-picks .wp-stat', timeout=60000)
    cap_t = order_ok(pg, TV)
    check(title(pg, TV) == 'threat weaknesses' and who_color(pg, TV) == ['Threat', True] and cap_t is not None and pg.locator(f'{R} .wp-tag').count() == 0,
          f'threat view: "{title(pg, TV)}", no tags, the capacitor ({cap_t}) after the picks and the tiles')
    # keyboard: Tab onto the threat half shows "they last"; Tab on hides it
    pg.locator(f'{R} .mys-fa-head button').last.focus()
    for _ in range(8):
        if pg.evaluate("() => !!document.activeElement.closest('.mys-half.is-threat')"): break
        pg.keyboard.press('Tab')
    pg.wait_for_timeout(150); p = panel(pg)
    check(shown(pg) and p['title'] == THEM['title'], f'Tab onto the threat half: its panel ({p and p["title"]})')
    pg.keyboard.press('Tab'); pg.wait_for_timeout(150)
    check(not shown(pg), 'Tab on: hidden')
    # collapsed card titles
    pg.locator(f'{TV} button.cc-toggle[data-card="weak"]').first.click(); pg.wait_for_timeout(400)
    bl = baselines(pg, TV)
    check(title(pg, TV).startswith('threat weaknesses') and who_color(pg, TV) == ['Threat', True] and bl and abs(bl[0] - bl[1]) < 0.5, f'collapsed: "{title(pg, TV)[:20]}", one baseline ({bl})')
    pg.locator(f'{TV} button.cc-toggle[data-card="weak"]').first.click(); pg.wait_for_timeout(300)
    # Viewing my ship
    pg.click('#myShipChip'); pg.click('#myShipPanel [data-act="open"]'); pg.wait_for_selector(f'{R} .fit-layout'); settle(pg); pg.keyboard.press('Escape')
    bl = baselines(pg, R)
    check(title(pg, R) == 'your weaknesses' and who_color(pg, R) == ['Your', True] and pg.locator(f'{R} .mys-board').count() == 0 and bl and abs(bl[0] - bl[1]) < 0.5,
          f'"Viewing my ship": "{title(pg, R)}", no board, one baseline ({bl})')
    check(not errs, f'desktop: no page errors {errs}')
    ctx.close()

def aar(b):
    """v2026.10.14.61: an Ancillary Armor Repairer with paste (fits/vexor_aar_paste_loaded.eft) as my ship: the panel's
    words are the page's own and say what the repairer did with its paste (the times: check_matchup.py)."""
    vex = open(os.path.join(FITS, 'vexor_aar_paste_loaded.eft'), encoding='utf-8').read()
    ctx = b.new_context(viewport={'width': 1440, 'height': 1000}); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML); pg.evaluate("localStorage.removeItem('dscanMyShip')"); pg.reload()
    pg.click('#tabBtnFit'); pg.fill('#fitAnalyzerInput', ORTHRUS); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout'); settle(pg)
    pg.click('#myShipChip'); pg.fill('#myShipEft', vex); pg.click('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-tiles'); pg.keyboard.press('Escape')
    pg.wait_for_selector(f'{HOST} .mys-board'); settle(pg, 800)
    pg.evaluate(f"() => mysFightSet(document.querySelector('{HOST}'), 'range', 30000, false)"); settle(pg, 1200)
    words = pg.evaluate(f"() => document.querySelector('{HOST}')._why.you")
    pg.locator(f'{HOST} [data-cell="youLast"] .mys-cell-v').hover(); pg.wait_for_timeout(250)
    p = panel(pg); txt = ' '.join(words['text'])
    check(shown(pg) and p['title'] == words['title'] and p['text'] == words['text'] and 'Medium Ancillary Armor Repairer' in txt and ('with paste' in txt or 'paste runs out' in txt),
          f'AAR with paste as my ship (30 km): the panel says what it did with its paste ({txt[:160]}...)')
    check(not errs, f'AAR: no page errors {errs}')
    ctx.close()

def phone(b):
    W = 375
    ctx = b.new_context(viewport={'width': W, 'height': 760}, is_mobile=True, has_touch=True); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML); pg.evaluate("localStorage.removeItem('dscanMyShip')"); pg.reload()
    pg.tap('#myShipChip'); pg.fill('#myShipEft', OSPREY); pg.tap('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-tiles')
    pg.touchscreen.tap(W // 2, 40); pg.wait_for_timeout(200)
    pg.tap('#tabBtnFit'); pg.fill('#fitAnalyzerInput', ORTHRUS); pg.tap('#fitAnalyzerBtn'); pg.wait_for_selector(f'{HOST} .mys-board', timeout=60000); settle(pg, 800)
    pg.evaluate(SETUP_RANGE); settle(pg, 1200)
    v = pg.locator(f'{HOST} [data-cell="youLast"] .mys-cell-v'); v.scroll_into_view_if_needed(); v.tap(); pg.wait_for_timeout(300)
    p = panel(pg)
    check(shown(pg) and p['title'] == YOU['title'] and p['text'] == YOU['text'] and p['role'] == 'dialog' and view(pg) == 'threat',
          f'tap "you last": the panel opens, the view stays ({view(pg)}, {p and p["role"]})')
    check(p['pos'] == 'fixed' and abs(p['box']['bottom'] - 760) < 1 and abs(p['box']['width'] - W) < 1 and pg.locator(f'{POP} .info-close').is_visible(),
          f'tap: a sheet across the bottom with a close button ({p["pos"]}, {p["box"]["width"]:.0f} px, bottom {p["box"]["bottom"]:.0f})')
    pg.locator(f'{POP} .info-close').tap(); pg.wait_for_timeout(200)
    check(not shown(pg) and view(pg) == 'threat', 'close button: closed, view unchanged')
    pg.locator(f'{HOST} [data-cell="theyLast"] .mys-cell-v').tap(); pg.wait_for_timeout(300)
    p = panel(pg)
    check(shown(pg) and p['title'] == THEM['title'] and view(pg) == 'threat', f'tap "they last": {p and p["title"]}')
    pg.touchscreen.tap(W // 2, 120); pg.wait_for_timeout(250)
    check(not shown(pg), 'a tap outside closes it')
    pg.locator(f'{HOST} [data-cell="theyLast"] .mys-cell-k').tap(); settle(pg, 900)
    check(view(pg) == 'threat' and not shown(pg), f'a tap on the label "they last" (the threat half is already shown): no panel ({view(pg)})')
    pg.locator(f'{HOST} [data-cell="youLast"] .mys-cell-k').tap(); settle(pg, 900)
    check(view(pg) == 'mine' and not shown(pg), f'a tap on the label "you last" switches, as elsewhere on the half ({view(pg)})')
    sw = pg.evaluate('document.documentElement.scrollWidth'); check(sw <= W, f'phone: no sideways scroll ({sw})')
    check(not errs, f'phone: no page errors {errs}')
    ctx.close()

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('CHROMIUM', '/opt/pw-browsers/chromium'))
    desktop(b); aar(b); phone(b)
    b.close()
print(f'FAILURES: {fails}')
