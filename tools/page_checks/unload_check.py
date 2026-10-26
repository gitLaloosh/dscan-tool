"""Unloading charges, the hover bar, the rack menus and the list inside the Fit card (v2026.10.14.77, roadmap/charges-plan.md
delivery 3; the owner: "unloading charges", "just put it in the online state", "make them choose a new charge using the list",
"Use original charges", the hover bar "worth trying", "All active" literal, the list "needs to stay inside of the fit
card", and chips to "filter by module type").

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/unload_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The real page, ESI and the game's icons served from pyfa's SDE copy. Weapon DPS is compared with pyfa's own handlers
(tools/pyfa_fit_oracle.py) on the fit each step produces: an unloaded copy is Online with no charge.
  * Drake, 6 Heavy Missile Launcher II with Scourge: "No charge" is the first row of the launcher's section (0, no range),
    the how-to text is behind the list's (i) ("How the Charges list works"; Escape closes the panel first, then the list);
  * "No charge" dragged onto the first launcher: that copy Online, the launcher's own icon, Firepower = pyfa, its line
    "5 weapons confirmed · 1 launcher empty" with "no charge" in the hover, the row "empty ×1", the Loaded line keeps the
    five and offers "Use original charges";
  * a click on the unloaded tile switches Offline / Online, never Active;
  * the hover bar (a mouse): Unload charge + Charges… on a loaded launcher, Charges… alone on an empty one; Unload charge
    unloads that copy (pyfa); Charges… opens the list; keyboard focus shows it, Escape closes it;
  * Nova dragged onto the empty first launcher: that copy Active with Nova (pyfa);
  * "Use original charges": six Scourge, all Active (pyfa);
  * the High rack's menu: All active / All online / All offline / Unload all charges / Charges…; the Mid rack's has the
    three states only; Unload all charges: six empty Online launchers, 0 weapon DPS, "6 launchers empty"; All active
    keeps them Online; the Mid rack's All offline / All active (the Large Shield Extenders, passive, go Online);
  * a Caracal (two launcher types): weapon chips (All weapons + one per type) show one section; the damage chips leave the
    No charge rows in view;
  * 390 and 320 px (touch): the list inside the Fit card, under its header, all on screen when opened from the top of the
    page; a held finger on a launcher opens Unload charge / Charges… without changing its state, Unload charge works, a
    tap still sets the state; the rack menu opens and Escape closes it;
  * every rack button clear of every tile (a circle against the turned squares) on a Drake, a Megathron and a Rifter at
    1440, 390 and 320 px; no sideways scroll; no page errors.
v2026.10.14.76 fails (no No charge row, no rack buttons).
"""
import sys, os, re, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, os.path.join(HERE, '..', 'independent_checks'))
from esi_from_sde import route_all, icon_route
from pyfa_sde import types, _en
from eft_engine import BYNAME
from pyfa_fit_oracle import OracleFit
import check_application as CA
from playwright.sync_api import sync_playwright

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
CHROMIUM = os.environ.get('CHROMIUM_PATH') or ('/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') else None)
R = '#fitAnalyzerResults'
HML, SCOURGE, NOVA = 2410, 209, 206
DRAKE = ("[Drake, Unload]\nBallistic Control System II\nBallistic Control System II\nDamage Control II\n\n"
         "Large Shield Extender II\nLarge Shield Extender II\nMultispectrum Shield Hardener II\n10MN Afterburner II\n\n"
         + "\n".join(["Heavy Missile Launcher II, Scourge Heavy Missile"] * 6)
         + "\n\nMedium Core Defense Field Extender I\nMedium Core Defense Field Extender I\nMedium Core Defense Field Extender I\n\n"
         "Hobgoblin II x5\n\n\nNova Heavy Missile x1000\nScourge Fury Heavy Missile x500\n")
CARACAL = """[Caracal, Two launcher types]
Ballistic Control System II

10MN Afterburner II
Medium Shield Extender II

Rapid Light Missile Launcher II, Scourge Light Missile
Rapid Light Missile Launcher II, Scourge Light Missile
Light Missile Launcher II, Scourge Light Missile
Light Missile Launcher II, Scourge Light Missile
"""
MEGA = """[Megathron, Rack test]
Magnetic Field Stabilizer II
Magnetic Field Stabilizer II
Damage Control II
1600mm Steel Plates II
1600mm Steel Plates II
Multispectrum Energized Membrane II
Multispectrum Energized Membrane II

100MN Afterburner II
Stasis Webifier II
Warp Scrambler II
Heavy F-RX Compact Capacitor Booster

""" + "\n".join(["Neutron Blaster Cannon II, Void L"] * 7) + "\n"
RIFTER = """[Rifter, Rack test]
Gyrostabilizer II
Damage Control II
200mm Steel Plates II

1MN Afterburner II
Warp Scrambler II
Stasis Webifier II

200mm AutoCannon II, Republic Fleet EMP S
200mm AutoCannon II, Republic Fleet EMP S
200mm AutoCannon II, Republic Fleet EMP S
"""
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok

# pyfa: the Drake's launchers as given [(state, charge typeId or None)], the rest as the page has them by default
DRAKE_REST = [('Ballistic Control System II', 'online'), ('Ballistic Control System II', 'online'), ('Damage Control II', 'active'),
              ('Large Shield Extender II', 'online'), ('Large Shield Extender II', 'online'), ('Multispectrum Shield Hardener II', 'active'),
              ('10MN Afterburner II', 'active'), ('Medium Core Defense Field Extender I', 'online'), ('Medium Core Defense Field Extender I', 'online'),
              ('Medium Core Defense Field Extender I', 'online')]
def pyfa_weapon_dps(launchers):
    ml = [(BYNAME[n], s, None) for n, s in DRAKE_REST] + [(HML, s, c) for s, c in launchers]
    o = OracleFit(BYNAME['Drake'], ml).calculate()
    if o.errors or o.oracleGaps: return None
    return sum(CA.module_dps(m) for m in o.modules if int(m.item.ID) == HML and m.state >= 2)

def settle(pg, ms=250):
    pg.wait_for_timeout(ms)
    pg.wait_for_function(f"() => !document.querySelector('{R} .fit-card-busy') && !(document.querySelector('{R} .chg-pop') && !document.querySelector('{R} .chg-pop .chg-w, {R} .chg-pop .chg-wait:not(:empty)'))", timeout=60000)
    pg.wait_for_timeout(ms)
def paste(pg, text):
    pg.evaluate(f"() => {{ const r = document.querySelector('{R}'); if(r) r.innerHTML = ''; }}")
    pg.fill('#fitAnalyzerInput', text); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-ring, {R} .ms-row', timeout=60000); settle(pg)
def open_list(pg):
    if not pg.locator(f'{R} .chg-pop').count(): pg.click(f'{R} button.chg-btn')
    pg.wait_for_selector(f'{R} .chg-pop .chg-row', timeout=60000); settle(pg)
def close_list(pg):
    if pg.locator(f'{R} .chg-pop').count(): pg.click(f'{R} .chg-close'); settle(pg)
def center(pg, sel):
    b = pg.locator(sel).first.bounding_box(); return (b['x'] + b['width'] / 2, b['y'] + b['height'] / 2)
def mouse_drag(pg, src, dst_xy):
    b = pg.locator(src).first.bounding_box()
    pg.mouse.move(b['x'] + b['width'] / 2, b['y'] + b['height'] / 2); pg.mouse.down()
    pg.mouse.move(b['x'] + b['width'] / 2 + 12, b['y'] + b['height'] / 2 + 12, steps=3); pg.wait_for_timeout(200)
    pg.mouse.move(*dst_xy, steps=8); pg.mouse.up(); settle(pg)
TILE = lambda k: f'{R} .fit-ring .ms-tile[data-type-id="{HML}"][data-copy="{k}"]'
TILES = f"""() => [...document.querySelectorAll('{R} .fit-ring .ms-tile[data-type-id="{HML}"]')].sort((a, b) => a.dataset.copy - b.dataset.copy)
  .map(t => ({{charge: Number(t.dataset.chargeId || 0), from: t.dataset.from, unl: !!t.dataset.unloaded, icon: (t.querySelector('img') || {{}}).src || ''}}))"""
FP = f"""() => {{ const t = document.querySelector('{R} button.cc-toggle[data-card="fp"]'), c = t && t.closest('.fit-summary'); if(!c) return null;
  const tile = (label) => [...c.querySelectorAll('.estimate-stat')].find(e => e.innerText.toUpperCase().includes(label));
  const w = tile('WEAPON DPS'), tot = tile('TOTAL DPS'), sub = tot && tot.querySelector('.estimate-sub');
  return {{weapon: w ? w.innerText.replace(/[^0-9,]/g, ' ').trim().split(/\\s+/).pop() : null, line: sub ? sub.textContent : '', hover: sub ? sub.title : ''}}; }}"""
def fp(pg): return pg.evaluate(FP)
def num(x): return int(str(x).replace(',', '')) if x not in (None, '') else None
def jsr(x): return int(x + 0.5)
RACK_CLEAR = f"""() => {{ const out = [];
  const tiles = [...document.querySelectorAll('{R} .fit-ring .ms-tile, {R} .fit-ring .fr-empty')].map(t => {{ const r = t.getBoundingClientRect(), s = t.offsetWidth;
    const turn = parseFloat(t.style.getPropertyValue('--turn')) || 0; return {{x: r.left + r.width / 2, y: r.top + r.height / 2, h: s / 2, a: turn * Math.PI / 180}}; }});
  for(const b of document.querySelectorAll('{R} .fit-ring button.rack-btn')){{
    const r = b.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2, rad = r.width / 2;
    for(const t of tiles){{
      const dx = cx - t.x, dy = cy - t.y, lx = dx * Math.cos(t.a) + dy * Math.sin(t.a), ly = -dx * Math.sin(t.a) + dy * Math.cos(t.a);
      const qx = Math.max(-t.h, Math.min(t.h, lx)), qy = Math.max(-t.h, Math.min(t.h, ly));
      if(Math.hypot(lx - qx, ly - qy) < rad - 0.5) out.push(b.dataset.rack);
    }}
  }}
  return {{racks: document.querySelectorAll('{R} .fit-ring button.rack-btn').length, overlaps: out}}; }}"""

with sync_playwright() as p:
    b = p.chromium.launch(**({'executable_path': CHROMIUM} if CHROMIUM else {}))
    # ---------------- desktop
    ctx = b.new_context(viewport={'width': 1440, 'height': 1100}); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.route(re.compile(r'https://images\.evetech\.net/.*'), icon_route)
    pg.goto('file://' + HTML); pg.evaluate("localStorage.clear(); localStorage.setItem('dscanFitView', 'ring')"); pg.reload(); pg.click('#tabBtnFit')
    paste(pg, DRAKE)
    open_list(pg)
    first = pg.evaluate(f"""() => {{ const s = document.querySelector('{R} .chg-pop .chg-w'), r = s && s.querySelector('.chg-row'); return r ? {{none: r.classList.contains('chg-none'),
      charge: r.dataset.charge, name: r.querySelector('.chg-n').textContent, v: [...r.querySelectorAll('.chg-v')].map(x => x.textContent), tag: !!r.querySelector('.chg-tag')}} : null; }}""")
    check(first and first['none'] and first['charge'] == '0' and first['name'] == 'No charge' and first['v'] == ['0', '–'] and not first['tag'],
          f'1440: "No charge" is the first row of the launcher\'s section, 0 DPS, no range, no line under it ({first})')
    if not (first and first['none']): print(f'FAILURES: {fails}'); sys.exit(1)   # a build without it (v.76): nothing more to check
    info = pg.evaluate(f"""() => {{ const d = document.querySelector('{R} .chg-pop details.info-pop'); return d ? {{title: d.querySelector('summary').getAttribute('title'), foot: !!document.querySelector('{R} .chg-foot')}} : null; }}""")
    check(info and info['title'] == 'How the Charges list works' and not info['foot'], f'1440: the how-to text is behind the list\'s (i), no paragraph under the list ({info})')
    if info:
        pg.click(f'{R} .chg-pop details.info-pop summary'); pg.wait_for_timeout(200)
        txt = pg.inner_text(f'{R} .chg-pop details.info-pop .info-body')
        pg.keyboard.press('Escape'); pg.wait_for_timeout(250)
        st = pg.evaluate(f"() => [!!document.querySelector('{R} .chg-pop details.info-pop[open]'), !!document.querySelector('{R} .chg-pop')]")
        check('No charge' in txt and st == [False, True], f'1440: the (i) explains No charge; Escape closes the panel and leaves the list open ({st})')
    # No charge onto the first launcher
    mouse_drag(pg, f'{R} .chg-row.chg-none', center(pg, TILE(0)))
    t = pg.evaluate(TILES); f1 = fp(pg)
    want = pyfa_weapon_dps([('online', None)] + [('active', SCOURGE)] * 5)
    check(t[0]['from'] == 'online' and t[0]['unl'] and not t[0]['charge'] and f'/types/{HML}/' in t[0]['icon'] and all(x['from'] == 'active' and x['charge'] == SCOURGE for x in t[1:]),
          f'1440: "No charge" dropped on the first launcher: that copy Online, its own icon, the rest as they were ({[(x["from"], x["charge"], x["unl"]) for x in t]})')
    check(num(f1['weapon']) == jsr(want) and f1['line'] == '5 weapons confirmed · 1 launcher empty' and 'no charge' in f1['hover'],
          f'1440: Firepower {f1["weapon"]} = pyfa {want:.2f}; its line "{f1["line"]}", the hover names it ({f1["hover"][-90:]!r})')
    row = pg.evaluate(f"() => {{ const r = document.querySelector('{R} .chg-row.chg-none'); return [r.classList.contains('is-cur'), (r.querySelector('.chg-tag') || {{}}).textContent]; }}")
    close_list(pg)
    loaded = pg.inner_text(f'{R} .fit-ring-loaded')
    check(row == [True, 'empty ×1'] and 'Scourge Heavy Missile ×5' in loaded and 'Use original charges' in loaded and 'empty' not in loaded and 'no charge' not in loaded.lower(),
          f'1440: the row says "empty ×1"; the Loaded line keeps the five and offers Use original charges ({row}, {loaded!r})')
    # the unloaded tile: Offline / Online only
    seq = []
    for _ in range(3):
        pg.click(TILE(0)); settle(pg); seq.append(pg.evaluate(TILES)[0]['from'])
    check(seq == ['offline', 'online', 'offline'], f'1440: a click on the unloaded tile switches Offline / Online, never Active ({seq})')
    pg.click(TILE(0)); settle(pg)   # back Online
    # the hover bar
    pg.hover(TILE(1)); pg.wait_for_timeout(600)
    bar = pg.evaluate(f"() => {{ const b = document.querySelector('{R} .ring-hb'); return b ? [...b.querySelectorAll('button')].map(x => x.title) : null; }}")
    check(bar == ['Unload charge', 'Charges…'], f'1440: hovering a loaded launcher shows Unload charge and Charges… ({bar})')
    if bar:
        pg.click(f'{R} .ring-hb .hb-unload'); settle(pg)
    t = pg.evaluate(TILES); f2 = fp(pg)
    want2 = pyfa_weapon_dps([('online', None)] * 2 + [('active', SCOURGE)] * 4)
    check(t[1]['unl'] and t[1]['from'] == 'online' and num(f2['weapon']) == jsr(want2) and f2['line'].endswith('2 launchers empty'),
          f'1440: Unload charge unloads that copy: {f2["weapon"]} = pyfa {want2:.2f} ("{f2["line"]}")')
    pg.mouse.move(5, 5); pg.wait_for_timeout(400)
    pg.hover(TILE(0)); pg.wait_for_timeout(600)
    bar = pg.evaluate(f"() => {{ const b = document.querySelector('{R} .ring-hb'); return b ? [...b.querySelectorAll('button')].map(x => x.title) : null; }}")
    check(bar == ['Charges…'], f'1440: on an empty launcher the bar has Charges… only ({bar})')
    if bar:
        pg.click(f'{R} .ring-hb .hb-list'); settle(pg)
    check(pg.locator(f'{R} .chg-pop').count() == 1, '1440: Charges… opens the list')
    # load Nova into the empty first copy: Active
    pg.wait_for_selector(f'{R} .chg-pop .chg-row[data-charge="{NOVA}"]', timeout=60000)
    mouse_drag(pg, f'{R} .chg-row[data-charge="{NOVA}"]', center(pg, TILE(0)))
    t = pg.evaluate(TILES); f3 = fp(pg)
    want3 = pyfa_weapon_dps([('active', NOVA), ('online', None)] + [('active', SCOURGE)] * 4)
    check(t[0]['charge'] == NOVA and t[0]['from'] == 'active' and not t[0]['unl'] and num(f3['weapon']) == jsr(want3),
          f'1440: Nova loaded into the empty first launcher makes it Active: {f3["weapon"]} = pyfa {want3:.2f}')
    close_list(pg)
    # keyboard: focus shows the bar, Escape closes it and leaves the focus on the tile
    pg.keyboard.press('Shift'); pg.focus(TILE(2)); pg.wait_for_timeout(300)
    kb = pg.locator(f'{R} .ring-hb').count()
    pg.keyboard.press('Tab'); pg.wait_for_timeout(100)   # into the bar
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    kb2 = pg.evaluate(f"() => [!!document.querySelector('{R} .ring-hb'), document.activeElement && document.activeElement.dataset ? document.activeElement.dataset.copy : null]")
    check(kb == 1 and kb2 == [False, '2'], f'1440: keyboard focus on a launcher shows the bar; Escape closes it, focus back on the tile ({kb}, {kb2})')
    # Use original charges
    pg.click(f'{R} button.chg-own'); settle(pg)
    t = pg.evaluate(TILES); f4 = fp(pg); want4 = pyfa_weapon_dps([('active', SCOURGE)] * 6)
    check(all(x['charge'] == SCOURGE and x['from'] == 'active' for x in t) and num(f4['weapon']) == jsr(want4) and f4['line'] == '6 weapons confirmed',
          f'1440: Use original charges: six Scourge, all Active ({f4["weapon"]} = pyfa {want4:.2f}, "{f4["line"]}")')
    # the rack menus
    pg.click(f'{R} button.rack-btn[data-rack="high"]'); pg.wait_for_timeout(200)
    hi = pg.evaluate(f"() => [...document.querySelectorAll('{R} .rack-menu button')].map(x => x.textContent.trim())")
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    pg.click(f'{R} button.rack-btn[data-rack="mid"]'); pg.wait_for_timeout(200)
    mid = pg.evaluate(f"() => [...document.querySelectorAll('{R} .rack-menu button')].map(x => x.textContent.trim())")
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    check(hi == ['All active', 'All online', 'All offline', 'Unload all charges', 'Charges…'] and mid == ['All active', 'All online', 'All offline']
          and pg.locator(f'{R} .rack-menu').count() == 0, f'1440: the High rack\'s menu ({hi}); the Mid rack\'s, states only ({mid}); Escape closes them')
    pg.click(f'{R} button.rack-btn[data-rack="high"]'); pg.wait_for_timeout(200); pg.click(f'{R} .rack-menu button[data-act="unload"]'); settle(pg)
    t = pg.evaluate(TILES); f5 = fp(pg)
    check(all(x['unl'] and x['from'] == 'online' for x in t) and num(f5['weapon']) == 0 and f5['line'] == '6 launchers empty',
          f'1440: Unload all charges: six empty Online launchers, weapon DPS {f5["weapon"]}, "{f5["line"]}"')
    pg.click(f'{R} button.rack-btn[data-rack="high"]'); pg.wait_for_timeout(200); pg.click(f'{R} .rack-menu button[data-act="active"]'); settle(pg)
    check(all(x['from'] == 'online' for x in pg.evaluate(TILES)), '1440: All active keeps the empty launchers Online')
    pg.click(f'{R} button.chg-own'); settle(pg)
    MIDS = "() => Object.fromEntries([...document.querySelectorAll('" + R + " .fit-ring .ms-tile')].filter(t => /Shield Extender|Hardener|Afterburner/.test(t.title)).map(t => [t.title.split(':')[0] + '#' + t.dataset.copy, t.dataset.from]))"
    pg.click(f'{R} button.rack-btn[data-rack="mid"]'); pg.wait_for_timeout(200); pg.click(f'{R} .rack-menu button[data-act="offline"]'); settle(pg)
    off = pg.evaluate(MIDS)
    pg.click(f'{R} button.rack-btn[data-rack="mid"]'); pg.wait_for_timeout(200); pg.click(f'{R} .rack-menu button[data-act="active"]'); settle(pg)
    on = pg.evaluate(MIDS)
    check(off and set(off.values()) == {'offline'} and all(v == ('online' if 'Shield Extender' in k else 'active') for k, v in on.items()) and len(on) == 4,
          f'1440: the Mid rack: All offline {sorted(set(off.values()))}; All active: the hardener and afterburner Active, the passive extenders Online ({on})')
    pg.click(f'{R} button.ms-reset'); settle(pg)
    # two launcher types: the weapon chips
    paste(pg, CARACAL); open_list(pg)
    chips = pg.evaluate(f"() => [...document.querySelectorAll('{R} .chg-pop button.chg-wchip')].map(c => c.textContent.trim())")
    check(len(chips) == 3 and chips[0] == 'All weapons', f'1440 Caracal: weapon chips, All weapons + one per launcher type ({chips})')
    if len(chips) == 3:
        pg.click(f'{R} .chg-pop button.chg-wchip:nth-of-type(3)'); pg.wait_for_timeout(150)
        vis = pg.evaluate(f"() => [...document.querySelectorAll('{R} .chg-pop .chg-w')].filter(s => !s.hidden).map(s => s.querySelector('.chg-wh b').textContent)")
        pg.click(f'{R} button.chg-chip[data-chg-filter="em"]'); pg.wait_for_timeout(150)
        nones = pg.evaluate(f"() => [...document.querySelectorAll('{R} .chg-pop .chg-w:not([hidden]) .chg-row.chg-none')].filter(r => !r.hidden).length")
        check(vis == [chips[2]] and nones == 1, f'1440 Caracal: a weapon chip shows its section only ({vis}); the EM chip leaves its No charge row in view ({nones})')
    # rack buttons clear of the tiles
    for name, text in (('Drake', DRAKE), ('Megathron', MEGA), ('Rifter', RIFTER)):
        paste(pg, text); g = pg.evaluate(RACK_CLEAR)
        check(g['racks'] == 3 and not g['overlaps'], f'1440 {name}: three rack buttons, none touching a tile ({g})')
    sc = pg.evaluate("[document.documentElement.scrollWidth, innerWidth]")
    check(sc[0] <= sc[1] and not errs, f'1440: no sideways scroll {sc}, no page errors {errs[:2]}')
    ctx.close()
    # ---------------- phone (touch)
    for w in (390, 320):
        ctx = b.new_context(viewport={'width': w, 'height': 844}, is_mobile=True, has_touch=True, device_scale_factor=2); pg = ctx.new_page()
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        route_all(pg); pg.route(re.compile(r'https://images\.evetech\.net/.*'), icon_route)
        pg.goto('file://' + HTML); pg.evaluate("localStorage.clear(); localStorage.setItem('dscanFitView', 'ring')"); pg.reload(); pg.click('#tabBtnFit')
        paste(pg, DRAKE)
        if not pg.locator(f'{R} .fit-ring').is_visible(): pg.click(f'{R} button.cc-toggle[data-card="fit"]'); settle(pg)
        pg.evaluate('window.scrollTo(0, 0)'); pg.wait_for_timeout(150)
        open_list(pg)
        g = pg.evaluate(f"""() => {{ const p = document.querySelector('{R} .chg-pop'), card = p.closest('.fit-summary'), head = card.querySelector('.fit-card-head');
          const r = p.getBoundingClientRect(), c = card.getBoundingClientRect(), h = head.getBoundingClientRect();
          return {{pos: getComputedStyle(p).position, top: Math.round(r.top), bottom: Math.round(r.bottom), inCard: r.left >= c.left - 0.5 && r.right <= c.right + 0.5, belowHead: r.top >= h.bottom - 0.5, vh: innerHeight}}; }}""")
        check(g['pos'] == 'absolute' and g['inCard'] and g['belowHead'] and g['top'] >= 0 and g['bottom'] <= g['vh'],
              f'{w}px: the list opens inside the Fit card, under its header, all on screen ({g})')
        close_list(pg)
        loc = pg.locator(TILE(2)); loc.scroll_into_view_if_needed(); pg.wait_for_timeout(300); bb = loc.bounding_box()
        cdp = ctx.new_cdp_session(pg); x, y = bb['x'] + bb['width'] / 2, bb['y'] + bb['height'] / 2
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y}]}); pg.wait_for_timeout(700)
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []}); pg.wait_for_timeout(500)
        menu = pg.evaluate(f"() => {{ const m = document.querySelector('{R} .ring-hb.is-menu'); return m ? [...m.querySelectorAll('button')].map(x => x.innerText.trim()) : null; }}")
        state = pg.evaluate(TILES)[2]['from']
        check(menu == ['Unload charge', 'Charges…'] and state == 'active', f'{w}px: a held finger opens Unload charge / Charges… and leaves the state alone ({menu}, {state})')
        if menu:
            b2 = pg.locator(f'{R} .ring-hb.is-menu .hb-unload').bounding_box()
            pg.touchscreen.tap(b2['x'] + b2['width'] / 2, b2['y'] + b2['height'] / 2); settle(pg)
        t = pg.evaluate(TILES)
        check(t[2]['unl'] and t[2]['from'] == 'online', f'{w}px: Unload charge from the menu unloads that launcher ({t[2]})')
        loc = pg.locator(TILE(3)); bb = loc.bounding_box()
        pg.touchscreen.tap(bb['x'] + bb['width'] / 2, bb['y'] + bb['height'] / 2); settle(pg)
        check(pg.evaluate(TILES)[3]['from'] == 'offline' and not pg.locator(f'{R} .ring-hb').count(), f'{w}px: a tap still sets the state ({pg.evaluate(TILES)[3]["from"]})')
        rb = pg.locator(f'{R} button.rack-btn[data-rack="high"]').bounding_box()
        pg.touchscreen.tap(rb['x'] + rb['width'] / 2, rb['y'] + rb['height'] / 2); pg.wait_for_timeout(300)
        opened = pg.locator(f'{R} .rack-menu').count()
        pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
        check(opened == 1 and pg.locator(f'{R} .rack-menu').count() == 0, f'{w}px: the rack menu opens; Escape closes it')
        for name, text in (('Drake', DRAKE), ('Megathron', MEGA), ('Rifter', RIFTER)):
            paste(pg, text)
            if not pg.locator(f'{R} .fit-ring').is_visible(): pg.click(f'{R} button.cc-toggle[data-card="fit"]'); settle(pg)
            g = pg.evaluate(RACK_CLEAR)
            check(g['racks'] == 3 and not g['overlaps'], f'{w}px {name}: three rack buttons, none touching a tile ({g})')
        sc = pg.evaluate("[document.documentElement.scrollWidth, innerWidth]")
        check(sc[0] <= sc[1] and not errs, f'{w}px: no sideways scroll {sc}, no page errors {errs[:2]}')
        ctx.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
