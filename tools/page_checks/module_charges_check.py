"""Charges in modules that aren't turrets or launchers, on the page (v2026.10.14.78, roadmap/charges-plan.md delivery 4; the owner:
"weapons aren't the only modules that hold charges", module chips as icons "use hover to display the name", the ring
"B", unloading keeps the state "sounds good").

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/module_charges_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The real page, ESI and the game's icons served from pyfa's SDE copy. The numbers themselves are checked by
tools/independent_checks/check_module_charges.py; this checks what the page shows and does:
  * a Megathron with a Heavy Capacitor Booster II, a Tracking Computer II, a Sensor Booster II and a Large Ancillary Armor
    Repairer (all with their charge) and two blasters: the Charges list has a section per module, in rack order (weapons,
    capacitor booster, tracking computer, sensor booster, armor repairer), each with its own two column headers;
  * the module chips: All, then one icon per module named by its hover title, a count in the corner for the two blasters;
    a module's chip shows its section only; the EM chip hides the blaster rows and leaves every module row in view;
  * the ring: a blaster shows its charge's icon (no corner badge); the other modules keep their own icon with the charge
    in a corner (option B);
  * the Tracking Speed Script clicked: the Tracking Computer's corner shows it, the module stays Active, the Loaded line
    lists it; "No charge" dropped on the Capacitor Booster: no corner, still Active, its row "empty ×1";
  * the hover bar on the Sensor Booster: Unload charge and Charges…; Charges… opens the list at its section;
  * the Mid rack's menu: All active / All online / All offline / Unload all charges / Charges…; Unload all charges leaves
    the Mid modules with no corner, their states as they were; Use original charges brings every charge back;
  * the list view: the Tracking Computer's row carries its script, and the Mid slots don't list the scripts again;
  * a Maelstrom with two X-Large Ancillary Shield Boosters: Cap Booster 800 dropped on one loads both (one charge for
    every copy); its hover bar says "Unload charges (every copy)";
  * 390 px: the list with its chips inside the Fit card, no sideways scroll; no page errors.
v2026.10.14.77 fails (weapon sections only, no corner badges).
"""
import sys, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, os.path.join(HERE, '..', 'independent_checks'))
from esi_from_sde import route_all, icon_route
from playwright.sync_api import sync_playwright

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
CHROMIUM = os.environ.get('CHROMIUM_PATH') or ('/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') else None)
R = '#fitAnalyzerResults'
TC, SB, CAPB, AAR, BLASTER, ASB = 1978, 1952, 3578, 33103, 3186, 32780
TSS, ORS, TRS, NCB800, PASTE, CB800, NCB400 = 29001, 28999, 29009, 32014, 28668, 11289, 32006
MEGA = """[Megathron, Module charges]
Large Ancillary Armor Repairer, Nanite Repair Paste
Magnetic Field Stabilizer II
Damage Control II

Heavy Capacitor Booster II, Navy Cap Booster 800
Tracking Computer II, Optimal Range Script
Sensor Booster II, Targeting Range Script
100MN Afterburner II

Neutron Blaster Cannon II, Void L
Neutron Blaster Cannon II, Void L


Navy Cap Booster 800 x20
Nanite Repair Paste x100
Tracking Speed Script x1
Scan Resolution Script x1
"""
MAEL = """[Maelstrom, Two ASBs]
Damage Control II

X-Large Ancillary Shield Booster, Navy Cap Booster 400
X-Large Ancillary Shield Booster, Navy Cap Booster 400
Large Shield Extender II


Cap Booster 800 x20
"""
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok
def settle(pg, ms=250):
    pg.wait_for_timeout(ms)
    pg.wait_for_function(f"() => !document.querySelector('{R} .fit-card-busy') && !(document.querySelector('{R} .chg-pop') && !document.querySelector('{R} .chg-pop .chg-w, {R} .chg-pop .chg-wait:not(:empty)'))", timeout=120000)
    pg.wait_for_timeout(ms)
def paste(pg, text):
    pg.evaluate(f"() => {{ const r = document.querySelector('{R}'); if(r) r.innerHTML = ''; }}")
    pg.fill('#fitAnalyzerInput', text); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-ring, {R} .ms-row', timeout=60000); settle(pg)
def open_list(pg):
    if not pg.locator(f'{R} .chg-pop').count(): pg.click(f'{R} button.chg-btn')
    pg.wait_for_selector(f'{R} .chg-pop .chg-w:not([hidden]) .chg-row', timeout=120000); settle(pg)
def close_list(pg):
    if pg.locator(f'{R} .chg-pop').count(): pg.click(f'{R} .chg-close'); settle(pg)
def center(pg, sel):
    b = pg.locator(sel).first.bounding_box(); return (b['x'] + b['width'] / 2, b['y'] + b['height'] / 2)
def mouse_drag(pg, src, dst):
    pg.locator(src).first.scroll_into_view_if_needed(); pg.wait_for_timeout(100)
    dst_xy = center(pg, dst)   # after the list scrolled
    b = pg.locator(src).first.bounding_box()
    pg.mouse.move(b['x'] + b['width'] / 2, b['y'] + b['height'] / 2); pg.mouse.down()
    pg.mouse.move(b['x'] + b['width'] / 2 + 12, b['y'] + b['height'] / 2 + 12, steps=3); pg.wait_for_timeout(200)
    pg.mouse.move(*dst_xy, steps=8); pg.mouse.up(); settle(pg)
TILE = lambda t, k=0: f'{R} .fit-ring .ms-tile[data-type-id="{t}"][data-copy="{k}"]'
# each tile: its state, the big icon's type, the corner's type (0: none)
TILES = f"""() => Object.fromEntries([...document.querySelectorAll('{R} .fit-ring .ms-tile[data-type-id]')].map(t => [t.dataset.typeId + ':' + t.dataset.copy,
  {{from: t.dataset.from, icon: Number(((t.querySelector(':scope > img') || {{}}).src || '').replace(/.*\\/types\\/(\\d+)\\/.*/, '$1')) || 0,
    badge: Number(((t.querySelector('.ms-badge img') || {{}}).src || '').replace(/.*\\/types\\/(\\d+)\\/.*/, '$1')) || 0}}]))"""
SECS = f"""() => [...document.querySelectorAll('{R} .chg-pop .chg-w')].map(s => ({{kind: s.dataset.kind, id: Number(s.dataset.weapon), hidden: s.hidden,
  cols: [...s.querySelectorAll('.chg-cols span')].slice(1).map(x => x.textContent),
  rows: [...s.querySelectorAll('.chg-row')].filter(r => !r.hidden).length, none: (s.querySelector('.chg-none .chg-tag') || {{}}).textContent || ''}}))"""

with sync_playwright() as p:
    b = p.chromium.launch(**({'executable_path': CHROMIUM} if CHROMIUM else {}))
    ctx = b.new_context(viewport={'width': 1440, 'height': 1100}); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.route(re.compile(r'https://images\.evetech\.net/.*'), icon_route)
    pg.goto('file://' + HTML); pg.evaluate("localStorage.clear(); localStorage.setItem('dscanFitView', 'ring')"); pg.reload(); pg.click('#tabBtnFit')
    paste(pg, MEGA)
    t = pg.evaluate(TILES)
    check(t.get(f'{BLASTER}:0', {}).get('badge') == 0 and t.get(f'{TC}:0', {}).get('icon') == TC and t.get(f'{TC}:0', {}).get('badge') == ORS
          and t.get(f'{SB}:0', {}).get('badge') == TRS and t.get(f'{CAPB}:0', {}).get('badge') == NCB800 and t.get(f'{AAR}:0', {}).get('badge') == PASTE,
          f'1440 ring: a blaster shows its charge (no corner); the Tracking Computer, Sensor Booster, Capacitor Booster and AAR keep their icon, the charge in a corner ({ {k: v for k, v in t.items() if int(k.split(":")[0]) in (BLASTER, TC, SB, CAPB, AAR)} })')
    open_list(pg)
    secs = pg.evaluate(SECS)
    check([s['kind'] for s in secs] == ['weapon', 'capBooster', 'tc', 'sb', 'aar'] and [s['cols'] for s in secs] == [['DPS', 'range'], ['GJ/s', 'Capacitor'], ['Range', 'Tracking'], ['Lock range', 'Scan res'], ['Burst HP/s', 'Sustained']],
          f'1440: a section per module in rack order, each with its own headers ({[(s["kind"], s["cols"]) for s in secs]})')
    if len(secs) < 2: print(f'FAILURES: {fails + 1}'); sys.exit(1)   # a build without them (v.77)
    chips = pg.evaluate(f"() => [...document.querySelectorAll('{R} .chg-pop button.chg-wchip')].map(c => [c.dataset.chgWeapon, c.title, !!c.querySelector('img'), (c.querySelector('b') || {{}}).textContent || ''])")
    check(len(chips) == 6 and chips[0][1] == 'Every module' and all(c[2] for c in chips[1:]) and chips[1][3] == '2' and all(c[3] == '' for c in chips[2:])
          and chips[3][1] == 'Tracking Computer II', f'1440: module chips: All, an icon per module named by its hover, a count on the two blasters ({chips})')
    pg.click(f'{R} .chg-pop button.chg-wchip[data-chg-weapon="{TC}"]'); pg.wait_for_timeout(150)
    vis = [s['kind'] for s in pg.evaluate(SECS) if not s['hidden']]
    pg.click(f'{R} .chg-pop button.chg-wchip[data-chg-weapon=""]'); pg.wait_for_timeout(150)
    pg.click(f'{R} button.chg-chip[data-chg-filter="em"]'); pg.wait_for_timeout(150)
    after = pg.evaluate(SECS)
    pg.click(f'{R} button.chg-chip[data-chg-filter="all"]'); pg.wait_for_timeout(150)
    check(vis == ['tc'] and after[0]['rows'] == 1 and all(s['rows'] == x['rows'] for s, x in zip(after[1:], secs[1:])),
          f'1440: the Tracking Computer chip shows its section only ({vis}); EM leaves the blasters\' No charge row and every module row ({[s["rows"] for s in after]} vs {[s["rows"] for s in secs]})')
    # a script for every Tracking Computer
    pg.click(f'{R} .chg-w[data-weapon="{TC}"] .chg-row[data-charge="{TSS}"]'); settle(pg)
    t = pg.evaluate(TILES); close_list(pg)
    loaded = pg.inner_text(f'{R} .fit-ring-loaded')
    check(t[f'{TC}:0']['badge'] == TSS and t[f'{TC}:0']['icon'] == TC and t[f'{TC}:0']['from'] == 'active' and 'Tracking Speed Script' in loaded and 'Optimal Range Script' not in loaded,
          f"1440: Tracking Speed Script clicked: the Tracking Computer's corner shows it, still Active; the Loaded line lists it ({t[f'{TC}:0']}, {loaded!r})")
    # No charge onto the Capacitor Booster
    open_list(pg)
    mouse_drag(pg, f'{R} .chg-w[data-weapon="{CAPB}"] .chg-row.chg-none', TILE(CAPB))
    t = pg.evaluate(TILES); open_list(pg); cap = [s for s in pg.evaluate(SECS) if s['kind'] == 'capBooster']
    check(t[f'{CAPB}:0']['badge'] == 0 and t[f'{CAPB}:0']['from'] == 'active' and cap and cap[0]['none'] == 'empty ×1',
          f"1440: No charge dropped on the Capacitor Booster: no corner, still Active, its row \"empty ×1\" ({t[f'{CAPB}:0']}, {cap[0]['none'] if cap else None!r})")
    close_list(pg)
    # the hover bar on the Sensor Booster
    pg.hover(TILE(SB)); pg.wait_for_timeout(600)
    bar = pg.evaluate(f"() => {{ const b = document.querySelector('{R} .ring-hb'); return b ? [...b.querySelectorAll('button')].map(x => x.title) : null; }}")
    if bar: pg.click(f'{R} .ring-hb .hb-list'); settle(pg)
    open_list(pg); vis = [s['kind'] for s in pg.evaluate(SECS) if not s['hidden']]
    check(bar == ['Unload charge', 'Charges…'] and vis == ['sb'], f'1440: the Sensor Booster\'s hover bar: {bar}; Charges… opens the list at its section ({vis})')
    close_list(pg)
    # the Mid rack
    pg.click(f'{R} button.rack-btn[data-rack="mid"]'); pg.wait_for_timeout(200)
    mid = pg.evaluate(f"() => [...document.querySelectorAll('{R} .rack-menu button')].map(x => x.textContent.trim())")
    before = pg.evaluate(TILES)
    if 'Unload all charges' in mid: pg.click(f'{R} .rack-menu button[data-act="unload"]'); settle(pg)
    else: pg.keyboard.press('Escape')
    t = pg.evaluate(TILES)
    check(mid == ['All active', 'All online', 'All offline', 'Unload all charges', 'Charges…'] and all(t[f'{m}:0']['badge'] == 0 and t[f'{m}:0']['from'] == before[f'{m}:0']['from'] for m in (TC, SB, CAPB))
          and t[f'{AAR}:0']['badge'] == PASTE, f'1440: the Mid rack\'s menu {mid}; Unload all charges: no corners, states as they were, the Low rack untouched')
    pg.click(f'{R} button.chg-own'); settle(pg)
    t = pg.evaluate(TILES)
    check(t[f'{TC}:0']['badge'] == ORS and t[f'{SB}:0']['badge'] == TRS and t[f'{CAPB}:0']['badge'] == NCB800, f'1440: Use original charges brings every charge back ({[t[f"{m}:0"]["badge"] for m in (TC, SB, CAPB)]})')
    # the list view
    pg.evaluate("localStorage.setItem('dscanFitView', 'list')"); paste(pg, MEGA)
    if pg.locator(f'{R} button.fit-view-btn[data-view="list"]').count(): pg.click(f'{R} button.fit-view-btn[data-view="list"]'); settle(pg)
    lv = pg.evaluate(f"""() => {{ const rows = [...document.querySelectorAll('{R} .ms-row')];
      const tc = rows.find(r => r.querySelector('button.ms-chg[data-weapon="{TC}"]'));
      const mid = [...document.querySelectorAll('{R} .fitgroup')].find(g => (g.querySelector('h3') || {{}}).textContent === 'Mid slots');
      return {{chip: tc ? tc.querySelector('button.ms-chg').textContent : null, midText: mid ? mid.innerText : ''}}; }}""")
    check(lv['chip'] and 'Optimal Range Script' in lv['chip'] and lv['midText'].count('Optimal Range Script') == 1 and lv['midText'].count('Targeting Range Script') == 1,
          f"1440 list view: the Tracking Computer's row carries its script; the Mid slots don't list the scripts again ({lv['chip']!r})")
    pg.evaluate("localStorage.setItem('dscanFitView', 'ring')")
    # two ASBs: one charge for every copy
    paste(pg, MAEL)
    if pg.locator(f'{R} button.fit-view-btn[data-view="ring"]').count(): pg.click(f'{R} button.fit-view-btn[data-view="ring"]'); settle(pg)
    open_list(pg)
    mouse_drag(pg, f'{R} .chg-w[data-weapon="{ASB}"] .chg-row[data-charge="{CB800}"]', TILE(ASB, 0))
    t = pg.evaluate(TILES)
    close_list(pg)
    pg.hover(TILE(ASB, 1)); pg.wait_for_timeout(600)
    bar = pg.evaluate(f"() => {{ const b = document.querySelector('{R} .ring-hb'); return b ? [...b.querySelectorAll('button')].map(x => x.title) : null; }}")
    check(t.get(f'{ASB}:0', {}).get('badge') == CB800 and t.get(f'{ASB}:1', {}).get('badge') == CB800 and bar == ['Unload charges (every copy)', 'Charges…'],
          f"1440 Maelstrom: Cap Booster 800 dropped on one ASB loads both ({t.get(f'{ASB}:0')}, {t.get(f'{ASB}:1')}); hover bar {bar}")
    pg.mouse.move(5, 5)
    sc = pg.evaluate("[document.documentElement.scrollWidth, innerWidth]")
    check(sc[0] <= sc[1] and not errs, f'1440: no sideways scroll {sc}, no page errors {errs[:2]}')
    ctx.close()
    # ---------------- phone
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.route(re.compile(r'https://images\.evetech\.net/.*'), icon_route)
    pg.goto('file://' + HTML); pg.evaluate("localStorage.clear(); localStorage.setItem('dscanFitView', 'ring')"); pg.reload(); pg.click('#tabBtnFit')
    paste(pg, MEGA)
    if not pg.locator(f'{R} .fit-ring').is_visible(): pg.click(f'{R} button.cc-toggle[data-card="fit"]'); settle(pg)
    pg.evaluate('window.scrollTo(0, 0)'); open_list(pg)
    g = pg.evaluate(f"""() => {{ const p = document.querySelector('{R} .chg-pop'), c = p.closest('.fit-summary').getBoundingClientRect(), r = p.getBoundingClientRect();
      const chips = [...p.querySelectorAll('button.chg-wchip')].map(x => x.getBoundingClientRect()).every(x => x.right <= r.right + 0.5 && x.left >= r.left - 0.5);
      return {{inside: r.left >= c.left - 0.5 && r.right <= c.right + 0.5, chips, n: p.querySelectorAll('.chg-w').length}}; }}""")
    sc = pg.evaluate("[document.documentElement.scrollWidth, innerWidth]")
    check(g['inside'] and g['chips'] and g['n'] == 5 and sc[0] <= sc[1] and not errs, f'390px: the list and its chips inside the Fit card ({g}), no sideways scroll {sc}, no page errors {errs[:2]}')
    b.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
