"""The profile (v2026.11.01.1; the owner's idea, mockups profile_mockup.html .. profile_mockup_5.html).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/profile_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner: "turn the upper right portion of the page into something of a 'profile' of the user that starts out as being
incomplete or not started ... Pilot name, associations, fits, etc. Intel could sit outside of that but somehow attached as a
decorator". On the real page (ESI served from pyfa's SDE, made-up pilot and corporation), checks:
  * not set up: "Set up your profile", 0 of 3, the silhouette, "+ Add a fit", no switch, no Intel mark (Intel off);
  * the panel: your pilot, Standings and My Fits, each ticked when done, "0 of 3 set up"; the close button its head's last
    item, 32 px; it, Esc and a press outside close it, the focus back on the profile; "+ Add a fit" opens it at the paste box;
  * set up: the pilot's name (initials when the portrait can't load), the fit in use inside the one wide switch, which turns
    "Use in assessments" on and off; 3 of 3: no "n of 3", no steps;
  * 20 saved fits (the My Ships bug): the panel ends above the window's bottom and scrolls inside, the page doesn't move, and
    its scrolling isn't trapped (overscroll-behavior auto, LESSON #96);
  * Intel's mark (decided 2026-10-29 and 2026-10-31): off none; clear a cyan square; not working a hollow cyan square; near an
    amber "Intel · N near"; in system the Hostile red "IN SYSTEM" with a ring that pulses (none with reduced motion); the Intel
    tab's dot the same kind; pressing the mark opens the Intel tab and doesn't turn Intel off;
  * the Intel card's head: the title at the left; the switch, the gear and the info button, in that order, at the top right at
    1280, 860 and 390 px (the owner: "we want that stuff to remain in the top right");
  * "My Ship" reads "My Fit" (the owner: "accuracy matters"): the card names, and no "My Ship" left in the page's text;
  * 390 px: the profile above the tabs, 44 px or more, the switch with the fit (no name line), the panel a sheet from the bottom;
  * no page errors.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esi_from_sde import route_all
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
PF = {'x': 12, 'y': 14}   # the portrait: the switch and "+ Add a fit" sit over the rest of the profile's button
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok

L1 = "() => document.querySelector('#profileL1').innerText.replace(/\\s+/g, ' ').trim()"
HEAD = """() => { const h = document.querySelector('#intelPanel .it-head'), R = (s) => h.querySelector(s).getBoundingClientRect();
  const t = R('h2'), w = R('#intelSwLabel'), g = R('.it-gear'), i = R('.info-btn'), hr = h.getBoundingClientRect();
  return [Math.round(t.right), Math.round(w.left), Math.round(g.left), Math.round(i.left), Math.round(i.right), Math.round(hr.right), Math.round(hr.width)]; }"""

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(bypass_csp=True, viewport={'width': 1280, 'height': 800})
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg)
    pg.route('**/characters/*/portrait*', lambda r: r.abort())   # no portrait: the initials
    pg.goto('file://' + HTML); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(500)
    # ---- not set up ----
    st = pg.evaluate("""() => [document.querySelector('#profile').dataset.p, !!document.querySelector('#profileAv svg'), document.querySelector('#profileAddFit').hidden,
      document.querySelector('#myShipUseLabel').hidden, document.querySelector('#intelNear').hidden, getComputedStyle(document.querySelector('#tabBtnIntel .tb')).display]""")
    check(pg.evaluate(L1) == 'Set up your profile 0 of 3' and st == ['empty', True, False, True, True, 'none'],
          f'not set up: "Set up your profile", 0 of 3, the silhouette, "+ Add a fit", no switch, no Intel mark or tab dot ({pg.evaluate(L1)!r}) {st}')
    pg.click('#profileBtn', position=PF); pg.wait_for_selector('#profilePanel:not([hidden])')
    pan = pg.evaluate("""() => { const p = document.querySelector('#profilePanel'), h = p.querySelector('.pp-head'), x = h.lastElementChild.getBoundingClientRect(), hr = h.getBoundingClientRect();
      return [[...p.querySelectorAll('.pp-sec')].map(s => s.querySelector('.pp-sh').firstChild.nextSibling.textContent.trim() + (s.classList.contains('done') ? ' ✓' : '')),
        p.querySelector('.pp-steps').innerText.trim(), h.lastElementChild.className, Math.round(x.width), Math.round(x.height), Math.round(hr.right - x.right), document.activeElement.id]; }""")
    check(pan[0] == ['Pilot', 'Standings', 'My Fits'] and pan[1] == '0 of 3 set up: your pilot, Standings, a fit' and 'x-close' in pan[2] and pan[3] == 32 and pan[4] == 32 and pan[5] <= 0 and pan[6] == 'sidePilot',
          f'the panel: Pilot, Standings, My Fits, none ticked, "0 of 3 set up"; the close button last in its head, 32 px; the focus on your pilot {pan}')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    check(pg.is_hidden('#profilePanel') and pg.evaluate("document.activeElement.id") == 'profileBtn', 'Esc closes it, the focus back on the profile')
    pg.click('#profileBtn', position=PF); pg.click('#profilePanel .pp-x'); pg.wait_for_timeout(150)
    c1 = pg.is_hidden('#profilePanel')
    pg.click('#profileBtn', position=PF); pg.mouse.click(300, 600); pg.wait_for_timeout(150)
    check(c1 and pg.is_hidden('#profilePanel'), 'the close button and a press outside close it')
    pg.click('#profileAddFit')
    check(pg.is_visible('#profilePanel') and pg.evaluate("document.activeElement.id") == 'myShipEft', '"+ Add a fit" opens it at the paste box')
    pg.fill('#myShipEft', VEXOR); pg.click('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-tiles', timeout=60000)
    pg.keyboard.press('Escape')
    # ---- set up: a pilot (made up), Standings, a fit ----
    pg.evaluate("""() => { Object.assign(side.rec, {pilot: {id: 90000001, name: 'Kael Varos'}, corp: {id: 98000001, name: 'Ashfall Corp', kind: 'corporation'}, alliance: null});
      side.rec.hostile = [{id: 98000004, name: 'Red Tide Syndicate', kind: 'corporation'}]; sideWrite(); renderProfile(); }""")
    pg.wait_for_timeout(400)
    sw = pg.evaluate("""() => [document.querySelector('#profile').dataset.p, (document.querySelector('#profileAv .pf-ini') || {}).textContent, document.querySelector('#myShipUseLabel').hidden,
      document.querySelector('#myShipUseTxt').innerText.replace(/\\s+/g, ' ').trim(), document.querySelector('#myShipUse').checked, document.querySelector('#profileAddFit').hidden]""")
    check(sw == ['full', 'KV', False, 'Vexor · Brawl', True, True] and pg.evaluate(L1).startswith('Kael Varos') and 'of 3' not in pg.evaluate(L1),
          f'set up: the pilot (initials without a portrait), the fit in use inside the switch, on; no "n of 3" ({pg.evaluate(L1)!r}) {sw}')
    pg.click('#myShipUseLabel'); pg.wait_for_timeout(200)
    off = pg.evaluate("() => [document.querySelector('#myShipUse').checked, myShip.rec.use, getComputedStyle(document.querySelector('#myShipUseLabel .pf-fsw-track')).backgroundColor]")
    pg.click('#myShipUseLabel'); pg.wait_for_timeout(200)
    on = pg.evaluate("() => [document.querySelector('#myShipUse').checked, myShip.rec.use, getComputedStyle(document.querySelector('#myShipUseLabel .pf-fsw-track')).backgroundColor]")
    check(off[:2] == [False, False] and on[:2] == [True, True] and off[2] != on[2] and on[2] == 'rgb(31, 111, 128)', f'the switch turns "Use in assessments" off and on {off} {on}')
    pg.click('#profileBtn', position=PF); pg.wait_for_selector('#profilePanel:not([hidden])')
    done = pg.evaluate("() => [[...document.querySelectorAll('#profilePanel .pp-sec')].map(s => s.classList.contains('done')), document.querySelector('#profileSteps').hidden]")
    check(done == [[True, True, True], True], f'3 of 3: every section ticked, no steps {done}')
    pg.keyboard.press('Escape')
    # ---- 20 saved fits: the panel stays inside the window ----
    pg.evaluate("""() => { const s = JSON.parse(localStorage.getItem('dscanMyShips')); const f0 = s.fits[0];
      s.fits = Array.from({length: 20}, (_, i) => Object.assign({}, f0, {id: f0.id + (i ? '-' + i : ''), fitName: i ? 'Copy ' + i : f0.fitName})); localStorage.setItem('dscanMyShips', JSON.stringify(s)); }""")
    pg.reload(); pg.wait_for_timeout(500)
    pg.click('#profileBtn', position=PF); pg.wait_for_selector('#myShipPanel .mys-row'); pg.wait_for_timeout(300)
    y0 = pg.evaluate('scrollY')
    geo = pg.evaluate("""() => { const p = document.querySelector('#profilePanel'), r = p.getBoundingClientRect(), c = getComputedStyle(p);
      return [document.querySelectorAll('#myShipPanel .mys-row').length, Math.round(r.bottom), innerHeight, p.scrollHeight > p.clientHeight + 50, c.overflowY, c.overscrollBehaviorY]; }""")
    check(geo[0] == 20 and geo[1] <= geo[2] - 16 and geo[3] and geo[4] == 'auto' and geo[5] == 'auto',
          f'20 fits: the panel ends above the window\'s bottom and scrolls inside, the wheel not trapped {geo}')
    pg.mouse.move(1100, 500); pg.mouse.wheel(0, 400); pg.wait_for_timeout(300)
    check(pg.evaluate("document.querySelector('#profilePanel').scrollTop") > 0 and pg.evaluate('scrollY') == y0, 'the wheel scrolls the panel, not the page')
    pg.keyboard.press('Escape')
    # ---- Intel's mark ----
    MARK = """() => { const b = document.querySelector('#intelNear'), c = getComputedStyle(b), t = document.querySelector('#tabBtnIntel .tb'), tc = getComputedStyle(t);
      return {s: document.querySelector('#profile').dataset.s, hidden: b.hidden, bg: c.backgroundColor, border: c.borderTopColor, txt: b.innerText.replace(/\\s+/g, ' ').trim(),
        anim: getComputedStyle(document.querySelector('#profile'), '::before').animationName,   // v2026.11.01.4: the ring that pulses (opacity) is the profile's ::before
        dot: tc.display, dotBg: tc.backgroundColor, dotShadow: tc.boxShadow, w: Math.round(b.getBoundingClientRect().width)}; }"""
    def state(js):
        pg.evaluate("(js) => { (new Function(js))(); itHeaderSync(); }", js); pg.wait_for_timeout(100); return pg.evaluate(MARK)
    pg.evaluate("() => { window.__nl = []; window.itNearList = () => window.__nl; window.itThreat = () => true; window.itNearCount = () => window.__nl.filter(x => x.j <= it.set.range).length; }")
    cyan, amber, red = 'rgb(79, 195, 217)', 'rgb(217, 154, 60)', 'rgb(198, 91, 78)'
    m = state("it.on = false;")
    check(m['s'] == 'off' and m['hidden'] and m['dot'] == 'none', f'Intel off: no mark, no dot {m}')
    m = state("it.on = true; it.err = ''; it.kfNote = ''; window.__nl = [];")
    check(m['s'] == 'clear' and not m['hidden'] and m['bg'] == cyan and m['w'] <= 16 and m['dot'] == 'inline-block' and m['dotBg'] == cyan, f'on, clear: a cyan square on the portrait\'s corner, a cyan dot {m}')
    m = state("it.kfNote = 'The kill feed is not answering';")
    check(m['s'] == 'broken' and m['border'] == cyan and m['bg'] != cyan and 'rgb(79, 195, 217)' in m['dotShadow'], f'on, not working: a hollow cyan square, a hollow dot {m}')
    m = state("it.kfNote = ''; window.__nl = [{j: 2, st: {}}, {j: 3, st: {}}];")
    check(m['s'] == 'near' and m['bg'] == amber and m['txt'] == 'INTEL 2 near' and m['dotBg'] == amber and m['w'] > 40, f'near: an amber "Intel · 2 near" tab, an amber dot {m}')
    m = state("window.__nl = [{j: 0, st: {}}, {j: 2, st: {}}];")
    check(m['s'] == 'in' and m['bg'] == red and m['txt'] == 'INTEL IN SYSTEM' and m['anim'] == 'pfring' and m['dotBg'] == red, f'in system: the Hostile red, "IN SYSTEM", a pulsing ring, a red dot {m}')
    pg.emulate_media(reduced_motion='reduce'); pg.wait_for_timeout(100)
    check(pg.evaluate(MARK)['anim'] == 'none', 'in system with reduced motion: no pulse')
    pg.emulate_media(reduced_motion='no-preference')
    pg.click('#tabBtnPilot'); pg.click('#intelNear'); pg.wait_for_timeout(200)
    check(pg.evaluate("() => [document.getElementById('tabIntel').style.display, it.on]") == ['block', True], 'pressing the mark opens the Intel tab and leaves Intel on')
    pg.evaluate("() => { it.on = false; itHeaderSync(); itRender(true); }")
    # ---- the Intel card's head: the switch, the gear, the info button at the top right ----
    for w in (1280, 860, 390):
        pg.set_viewport_size({'width': w, 'height': 800}); pg.wait_for_timeout(300); pg.evaluate("() => itRender(true)"); pg.wait_for_timeout(150)
        h = pg.evaluate(HEAD)
        check(h[0] < h[1] < h[2] < h[3] and h[5] - h[4] <= 2 and h[1] - h[0] > (100 if w > 600 else 30),
              f'{w} px: the Intel card\'s head: the title, then at the top right the switch, the gear, the info button {h}')
    pg.set_viewport_size({'width': 1280, 'height': 800}); pg.wait_for_timeout(300)
    # ---- "My Fit" ----
    names = pg.evaluate("() => [CARD_NAMES.myshippage, CARD_NAMES['perspective.mine']]")
    pg.click('#tabBtnFit'); pg.wait_for_timeout(200)
    leftover = pg.evaluate("() => (document.body.innerText.match(/\\bMy Ships?\\b|\\bmy ships?\\b/g) || [])")
    check(names == ['Viewing My Fit', 'My Fit Perspective'] and not leftover, f'"My Ship" reads "My Fit": the card names, nothing left in the page\'s text {names} {leftover[:3]}')
    check(not errs, f'no page errors {errs[:3]}')
    ctx.close()
    # ---- 390 px ----
    ctx = b.new_context(bypass_csp=True, viewport={'width': 390, 'height': 800}, is_mobile=True, has_touch=True)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(400)
    pg.tap('#profileAddFit'); pg.fill('#myShipEft', VEXOR); pg.tap('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-tiles', timeout=60000)
    sheet = pg.evaluate("() => { const r = document.querySelector('#profilePanel').getBoundingClientRect(); return [Math.round(r.left), Math.round(r.right), Math.round(r.bottom)]; }")
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ph = pg.evaluate("""() => { const p = document.querySelector('#profile').getBoundingClientRect(), t = document.querySelector('.tab-btn').getBoundingClientRect();
      return [Math.round(p.bottom) <= Math.round(t.top) + 1, Math.round(p.height), getComputedStyle(document.querySelector('#profileL1')).display, document.querySelector('#myShipUseLabel').checkVisibility(),
        document.querySelector('#myShipUseTxt').innerText.replace(/\\s+/g, ' ').trim(), document.documentElement.scrollWidth]; }""")
    check(sheet == [0, 390, 800] and ph[:5] == [True, ph[1], 'none', True, 'Vexor · Brawl'] and ph[1] >= 44 and ph[5] <= 390,
          f'390 px: the profile above the tabs, finger-sized, the switch with the fit, no name line; the panel a sheet from the bottom {sheet} {ph}')
    check(not errs, f'390 px: no page errors {errs[:3]}')
    ctx.close(); b.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
