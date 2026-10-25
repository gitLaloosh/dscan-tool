"""My Ships: several saved fits (v2026.10.14.65; the owner 2026-10-25: switch "in the panel AND on the Matchup", no compare-all
view, most recently used first; picked from the list "it should become the active ship everywhere"; "limit the list of
fits they can save to 20 for now").

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/my_ships_check.py [index.html]   -> 'FAILURES: N' (must be 0)

Checks, on the real page (ESI served from pyfa's SDE):
  * a ship saved by v2026.10.14.33-.64 (localStorage dscanMyShip) is the first entry of the list; the first change writes
    the list (dscanMyShips) and keeps dscanMyShip as a copy of the ship in use;
  * "+ Add a fit" adds and uses; the list is most recently used first, "In use" on that one; the chip shows "+N";
    pasting a fit already saved adds nothing and uses that one;
  * a fit that isn't in use: its numbers in the panel (= the Fit Analyzer's for that paste), "Use this ship" / "Use";
  * using another fit changes the chip, every board and the stored inUse; each fit keeps its own module states;
  * the board's ship menu: every saved fit, a check on the one in use, picking one switches everywhere (the board's
    numbers are the page's own mysMatchup for the new ship), "Manage My Ships" opens the panel, Escape closes it;
  * Rename (chip, list, board, stored, Copy EFT's header), Replace fit (same entry), Delete a fit not in use;
  * 20 saved: "+ Add a fit" disabled with MYSHIP-03, the Fit Analyzer's "Set as my ship" disabled with MYSHIP-03, and a
    paste of a 21st fit refused with MYSHIP-03;
  * phone (375 px): the board's menu is a bottom sheet with 44 px options, a tap on "My ship" still switches the view,
    the panel's rows are finger-sized, nothing scrolls sideways. No page errors.
"""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esi_from_sde import route_all, run_async
from playwright.sync_api import sync_playwright

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')),
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'index.html')))
FITS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'independent_checks', 'fits')
OSPREY = open(os.path.join(FITS, 'osprey_navy_issue_mine.eft'), encoding='utf-8').read()
ORTHRUS = open(os.path.join(FITS, 'orthrus_threat.eft'), encoding='utf-8').read()
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
HECATE = """[Hecate, Kite]
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
HECATE3 = HECATE.replace("Light Neutron Blaster II, Void S\nLight Neutron Blaster II, Void S\n", "", 1)
CHIP_MORE = "() => { const m = document.querySelector('#myShipChip .mys-chip-more'); return m ? m.textContent : ''; }"
R = '#fitAnalyzerResults'
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok
def settle(pg, ms=400):
    pg.wait_for_timeout(ms); pg.wait_for_function("() => !document.querySelector('.fit-card-busy')", timeout=60000); pg.wait_for_timeout(ms)
def store(pg):
    return pg.evaluate("() => { try { return [JSON.parse(localStorage.getItem('dscanMyShips')), JSON.parse(localStorage.getItem('dscanMyShip'))]; } catch(e) { return ['ERR', 'ERR']; } }")
def rows(pg):
    return pg.evaluate("""() => [...document.querySelectorAll('#myShipPanel .mys-row')].map(r => ({t: r.querySelector('.mys-row-t').textContent.trim(),
      inUse: !!r.querySelector('.mys-inuse'), sel: r.classList.contains('is-sel'), id: r.dataset.id}))""")
def wait_tiles(pg):
    pg.wait_for_function("() => { const v = document.querySelector('#myShipPanel .mys-tile-v'); return v && !/^[…—]$/.test(v.textContent); }", timeout=60000)
def tile(pg, k):
    return pg.evaluate("(k) => { const t = [...document.querySelectorAll('#myShipPanel .mys-tile')].find(x => x.querySelector('.mys-tile-k').textContent === k); return t ? t.querySelector('.mys-tile-v').textContent : null; }", k)
def open_panel(pg):
    if pg.is_hidden('#myShipPanel'): pg.click('#myShipChip')
def add(pg, text):
    open_panel(pg)
    if pg.locator('#myShipPanel [data-act="add"]').count(): pg.click('#myShipPanel [data-act="add"]')
    pg.fill('#myShipEft', text); pg.click('#myShipPanel [data-act="save"]')
    pg.wait_for_selector('#myShipPanel .mys-list'); wait_tiles(pg)
def fa_ehp(pg, text):
    pg.click('#tabBtnFit'); pg.evaluate("() => { document.querySelector('#fitAnalyzerResults').innerHTML = ''; }")
    pg.fill('#fitAnalyzerInput', text); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout', timeout=60000); settle(pg)

def ref_ehp(pg, text):   # the engine's EHP for a paste, as the Fit Analyzer computes it
    return run_async(pg, "async (t) => { const {f} = await buildFitFromEft(t); return f.estimate.totalHP.toLocaleString(); }", text)
BOARD = f"() => Object.fromEntries([...document.querySelector('{R} .mys-board').querySelectorAll('[data-cell]')].map(c => [c.dataset.cell, (c.querySelector('.mys-cell-v') || c).textContent]))"
# the menu's name is laid over the half's own (invisible) name: the same box, so it reads as the half's name
ALIGN = f"""() => {{ const a = document.querySelector('{R} details.mys-pick > summary').getBoundingClientRect(), b = document.querySelector('{R} .mys-pick-ghost').getBoundingClientRect();
  return Math.max(Math.abs(a.left - b.left), Math.abs(a.right - b.right), Math.abs(a.top - b.top), Math.abs(a.bottom - b.bottom)); }}"""
EXPECT = """(scope) => { const host = document.querySelector(scope + ' .mys-switch-host'); const tf = mysStripThreatF(host);
  const m = mysMatchup(tf, myShip.f, tf.dmg || dmgDefaults(tf.estimate.application)); return Object.fromEntries(m.cells.map(c => [c.key, c.value])); }"""

def desktop(b):
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML)
    # a ship saved by v.33-.64 (one record under dscanMyShip) is the first saved fit
    pg.evaluate("(t) => { localStorage.removeItem('dscanMyShips'); localStorage.setItem('dscanMyShip', JSON.stringify({v: 1, eft: t, shipName: 'Vexor', fitName: 'Brawl', shipTypeId: 626, shipGroup: 'Cruiser', use: true, savedAt: '2026-10-20T10:00:00Z'})); }", VEXOR)
    pg.reload(); open_panel(pg); wait_tiles(pg)
    r = rows(pg)
    check(len(r) == 1 and r[0]['t'].startswith('Vexor') and r[0]['inUse'] and 'Vexor' in pg.inner_text('#myShipChip') and pg.evaluate(CHIP_MORE) == '',
          f'v.33 ship read as the first saved fit {r}')
    vexor_ehp = tile(pg, 'EHP')
    add(pg, HECATE)
    s2, s1 = store(pg)
    check(s2 and s2['v'] == 2 and len(s2['fits']) == 2 and s1 and s1['eft'] == HECATE and next(f for f in s2['fits'] if f['id'] == s2['inUse'])['eft'] == HECATE,
          'first change writes dscanMyShips (2 fits, inUse = Hecate) and dscanMyShip = the ship in use')
    hecate_ehp = tile(pg, 'EHP')
    add(pg, OSPREY)
    r = rows(pg)
    check([x['t'].split(' ·')[0] for x in r] == ['Osprey Navy Issue', 'Hecate', 'Vexor'] and r[0]['inUse'] and not r[1]['inUse'] and r[0]['sel'],
          f'added fits: most recently used first, "In use" on the new one {[x["t"] for x in r]}')
    check(pg.evaluate(CHIP_MORE) == '+2' and 'Osprey Navy Issue' in pg.inner_text('#myShipChip'), f'chip: the ship in use and "+2" ({pg.evaluate(CHIP_MORE)!r})')
    # pasting a fit already saved adds nothing and uses it
    add(pg, VEXOR)
    r = rows(pg)
    check(len(r) == 3 and r[0]['t'].startswith('Vexor') and r[0]['inUse'] and 'already in My Ships' in pg.inner_text('#myShipPanel'), f'duplicate paste: nothing added, the saved Vexor is used {[x["t"] for x in r]}')
    # a fit that isn't in use: its own numbers, "Use this ship"
    hid = next(x['id'] for x in r if x['t'].startswith('Hecate'))
    pg.click(f'#myShipPanel .mys-row-main[data-id="{hid}"]'); wait_tiles(pg)
    check(tile(pg, 'EHP') == hecate_ehp and pg.locator('#myShipPanel .mys-open[data-act="use"]').count() == 1 and 'Vexor' in pg.inner_text('#myShipChip'),
          f'viewing a fit not in use: its numbers ({tile(pg, "EHP")} = {hecate_ehp}), "Use this ship", the chip unchanged')
    pg.click('#myShipPanel .mys-open[data-act="use"]'); pg.wait_for_timeout(200); wait_tiles(pg)
    s2, s1 = store(pg)
    check('Hecate' in pg.inner_text('#myShipChip') and rows(pg)[0]['t'].startswith('Hecate') and s1['eft'] == HECATE and next(f for f in s2['fits'] if f['id'] == s2['inUse'])['eft'] == HECATE,
          '"Use this ship": chip, list order and storage follow')
    pg.keyboard.press('Escape')
    # the Fit Analyzer's EHP for the Vexor paste = the panel's number for it (computed while it was in use)
    check(ref_ehp(pg, VEXOR) == vexor_ehp and ref_ehp(pg, HECATE) == hecate_ehp, f'panel numbers = the Fit Analyzer engine\'s for each paste ({vexor_ehp}, {hecate_ehp})')
    # per-fit module states: change one on the Hecate (in use), switch to the Vexor and back
    open_panel(pg); pg.click('#myShipPanel [data-act="open"]'); pg.wait_for_selector(f'{R} .mys-banner'); settle(pg)
    b0 = pg.locator(f'{R} .fl-fit button.ms-state[data-from="active"]').first
    tid = b0.get_attribute('data-type-id'); b0.click(); settle(pg, 600)
    s2, _ = store(pg)
    hec = next(f for f in s2['fits'] if f['eft'] == HECATE)
    check(hec.get('moduleStates') and tid in hec['moduleStates'], f'module change kept with the Hecate (type {tid})')
    vid = next(f['id'] for f in s2['fits'] if f['eft'] == VEXOR)
    open_panel(pg); pg.click(f'#myShipPanel button[data-act="use"][data-id="{vid}"]'); pg.wait_for_timeout(300); pg.keyboard.press('Escape'); settle(pg, 600)
    check('Vexor' in pg.inner_text(f'{R} .mys-banner-v'), 'the Fit Analyzer\'s my-ship page follows the switch (Vexor)')
    s2, _ = store(pg)
    vex = next(f for f in s2['fits'] if f['eft'] == VEXOR); hec = next(f for f in s2['fits'] if f['eft'] == HECATE)
    check(not vex.get('moduleStates') and hec.get('moduleStates') and tid in hec['moduleStates'], 'each fit keeps its own states (Vexor as pasted, Hecate changed)')
    # the board's ship menu
    pg.click('#tabBtnFit'); pg.evaluate("() => { document.querySelector('#fitAnalyzerResults').innerHTML = ''; }")
    pg.fill('#fitAnalyzerInput', ORTHRUS); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .mys-board', timeout=60000)
    pg.wait_for_function(f"() => {{ const b = document.querySelector('{R} .mys-board'); return b && !/…/.test(b.textContent); }}", timeout=60000); settle(pg, 600)
    d = pg.evaluate(ALIGN); check(d <= 1, f'1440: the menu name sits exactly on the half\'s name ({d:.1f} px)')
    pg.set_viewport_size({'width': 1100, 'height': 900}); pg.wait_for_timeout(300)
    d = pg.evaluate(ALIGN); check(d <= 1, f'1100: the menu name sits exactly on the half\'s name ({d:.1f} px)')
    pg.set_viewport_size({'width': 1440, 'height': 900}); pg.wait_for_timeout(300)
    pg.click(f'{R} details.mys-pick > summary'); pg.wait_for_timeout(200)
    opts = pg.evaluate(f"() => [...document.querySelectorAll('{R} .mys-pick-menu button.mys-pick-opt[data-id]')].map(b => [b.textContent.trim().replace(/\\s+/g, ' '), b.getAttribute('aria-checked')])")
    check(len(opts) == 3 and opts[0][1] == 'true' and 'Vexor' in opts[0][0] and pg.is_visible(f'{R} .mys-pick-menu'), f'board menu: the saved fits, most recent first, the one in use checked {opts}')
    view0 = pg.get_attribute(f'{R} .mys-sw-btn.is-threat', 'aria-pressed')
    pg.click(f'{R} .mys-pick-menu button.mys-pick-opt[data-id="{hid}"]')
    pg.wait_for_function(f"() => {{ const b = document.querySelector('{R} .mys-board'); return b && /Hecate/.test(b.querySelector('.mys-pick summary').textContent) && !/…/.test(b.textContent); }}", timeout=60000); settle(pg, 800)
    check('Hecate' in pg.inner_text('#myShipChip') and pg.get_attribute(f'{R} .mys-sw-btn.is-threat', 'aria-pressed') == view0, 'picking from the board: the chip follows, the view stays')
    check(pg.evaluate(BOARD) == pg.evaluate(EXPECT, R), f'board numbers = mysMatchup for the new ship {pg.evaluate(BOARD)}')
    pg.click(f'{R} details.mys-pick > summary'); pg.keyboard.press('Escape')
    check(pg.evaluate(f"() => !document.querySelector('{R} details.mys-pick').open"), 'Escape closes the board menu')
    pg.click(f'{R} details.mys-pick > summary'); pg.click(f'{R} .mys-pick-manage'); pg.wait_for_timeout(200)
    check(pg.is_visible('#myShipPanel .mys-list'), '"Manage My Ships" opens the panel')
    # Rename
    pg.click('#myShipPanel [data-act="rename"]'); pg.fill('#myShipRename', 'Kite 2'); pg.click('#myShipPanel [data-act="rename-save"]'); pg.wait_for_timeout(400)
    s2, s1 = store(pg)
    eft_out = pg.evaluate("() => myShipEftOut(myShip.rec)")
    check('Kite 2' in pg.inner_text('#myShipChip') and rows(pg)[0]['t'] == 'Hecate · Kite 2' and s1['fitName'] == 'Kite 2' and eft_out.startswith('[Hecate, Kite 2]') and s1['eft'] == HECATE,
          f'Rename: chip, list, storage, Copy EFT header (stored text unchanged) ({rows(pg)[0]["t"]!r})')
    check('Kite 2' in pg.inner_text(f'{R} details.mys-pick > summary'), 'Rename: the board follows')
    # Replace a fit that isn't in use (the Osprey) with another paste: same entry
    oid = next(x['id'] for x in rows(pg) if x['t'].startswith('Osprey'))
    pg.click(f'#myShipPanel .mys-row-main[data-id="{oid}"]'); pg.click('#myShipPanel [data-act="replace"]')
    pg.fill('#myShipEft', HECATE3.replace('[Hecate, Kite]', '[Hecate, Three guns]')); pg.click('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-list'); wait_tiles(pg)
    s2, _ = store(pg)
    rep = next((f for f in s2['fits'] if f['id'] == oid), None)
    check(len(s2['fits']) == 3 and rep and rep['fitName'] == 'Three guns' and not any(f['shipName'] == 'Osprey Navy Issue' for f in s2['fits']), 'Replace fit: the same entry gets the new paste')
    # Delete a fit that isn't in use
    vid = next(x['id'] for x in rows(pg) if x['t'].startswith('Vexor'))
    pg.click(f'#myShipPanel .mys-row-main[data-id="{vid}"]'); pg.click('#myShipPanel [data-act="delete"]'); pg.click('#myShipPanel [data-act="delete-yes"]'); pg.wait_for_timeout(300)
    s2, s1 = store(pg)
    check(len(s2['fits']) == 2 and s1['eft'] == HECATE and 'Kite 2' in pg.inner_text('#myShipChip') and pg.evaluate(CHIP_MORE) == '+1', 'Delete a fit not in use: the ship in use stays')
    pg.keyboard.press('Escape')
    # the limit: 20
    pg.evaluate("""(t) => { const fits = []; for(let i = 0; i < 20; i++) fits.push({v: 1, id: 'x' + i, eft: t.replace('[Vexor, Brawl]', '[Vexor, Copy ' + i + ']'), shipName: 'Vexor', fitName: 'Copy ' + i, shipTypeId: 626,
        shipGroup: 'Cruiser', use: true, savedAt: '2026-10-2' + (i % 5) + 'T00:00:00Z', usedAt: '2026-10-' + String(10 + i).padStart(2, '0') + 'T00:00:00Z'});
      localStorage.setItem('dscanMyShips', JSON.stringify({v: 2, inUse: 'x19', use: true, fits})); }""", VEXOR)
    pg.reload(); open_panel(pg); wait_tiles(pg)
    add_btn = pg.locator('#myShipPanel [data-act="add"]')
    check(len(rows(pg)) == 20 and add_btn.is_disabled() and '(MYSHIP-03)' in (add_btn.get_attribute('title') or '') and '(MYSHIP-03)' in pg.inner_text('#myShipPanel'),
          f'20 saved: "+ Add a fit" disabled with MYSHIP-03 ({len(rows(pg))} rows)')
    pg.keyboard.press('Escape')
    fa_ehp(pg, HECATE)
    sb = pg.locator(f'{R} button.mys-set')
    check(sb.count() == 1 and sb.is_disabled() and '(MYSHIP-03)' in (sb.get_attribute('title') or ''), '20 saved: "Set as my ship" disabled with MYSHIP-03')
    r = run_async(pg, "async (t) => { try { await myShipAdopt(t, {shipName: 'Hecate', fitName: 'Kite', shipTypeId: 35683}, null, null); return 'added ' + myShip.list.length; } catch(e) { return e.code + ' ' + myShip.list.length; } }", HECATE)
    check(r == 'MYSHIP-03 20', f'a 21st fit is refused with MYSHIP-03 ({r})')
    check(not errs, f'desktop: no page errors {errs}')
    ctx.close()

def phone(b):
    W = 375
    ctx = b.new_context(viewport={'width': W, 'height': 740}, is_mobile=True, has_touch=True); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML); pg.evaluate("() => { localStorage.removeItem('dscanMyShips'); localStorage.removeItem('dscanMyShip'); }"); pg.reload()
    pg.tap('#myShipChip'); pg.fill('#myShipEft', VEXOR); pg.tap('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-list'); wait_tiles(pg)
    pg.tap('#myShipPanel [data-act="add"]'); pg.fill('#myShipEft', HECATE); pg.tap('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-list'); wait_tiles(pg)
    hs = pg.evaluate("() => [...document.querySelectorAll('#myShipPanel .mys-row-main, #myShipPanel .mys-add')].map(b => b.getBoundingClientRect().height)")
    check(min(hs) >= 44 and pg.evaluate("document.documentElement.scrollWidth") <= W, f'phone: panel rows and buttons sized for a finger, no sideways scroll {[round(h) for h in hs]}')
    pg.tap('#myShipBackdrop', position={'x': 20, 'y': 20})   # above the sheet
    pg.tap('#tabBtnFit'); pg.fill('#fitAnalyzerInput', ORTHRUS); pg.tap('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .mys-board', timeout=60000)
    pg.wait_for_function(f"() => {{ const b = document.querySelector('{R} .mys-board'); return b && !/…/.test(b.textContent); }}", timeout=60000); settle(pg, 600)
    d = pg.evaluate(ALIGN); check(d <= 1, f'375: the menu name sits exactly on the half\'s name ({d:.1f} px)')
    pg.tap(f'{R} details.mys-pick > summary'); pg.wait_for_timeout(300)
    box = pg.locator(f'{R} .mys-pick-menu').bounding_box()
    oh = pg.evaluate(f"() => [...document.querySelectorAll('{R} .mys-pick-menu button.mys-pick-opt')].map(b => b.getBoundingClientRect().height)")
    check(box and abs(box['y'] + box['height'] - 740) <= 1 and box['x'] <= 1 and box['width'] >= W - 1 and min(oh) >= 44, f'phone: the ship menu is a bottom sheet with 44 px options ({box}, {oh})')
    pg.tap(f'{R} .mys-pick-head .info-close'); pg.wait_for_timeout(200)
    check(pg.evaluate(f"() => !document.querySelector('{R} details.mys-pick').open"), 'phone: the sheet\'s close button closes it')
    pg.tap(f'{R} .mys-sw-btn.is-mine .mys-sw-k'); pg.wait_for_selector(f'{R} .mys-mine-view .fit-layout'); settle(pg)
    check(pg.get_attribute(f'{R} .mys-sw-btn.is-mine', 'aria-pressed') == 'true', 'phone: a tap on "My ship" still shows the My Ship Perspective')
    check(pg.evaluate("document.documentElement.scrollWidth") <= W, 'phone: no sideways scroll')
    check(not errs, f'phone: no page errors {errs}')
    ctx.close()

with sync_playwright() as p:
    CHROMIUM = os.environ.get('CHROMIUM_PATH') or ('/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') else None)
    b = p.chromium.launch(**({'executable_path': CHROMIUM} if CHROMIUM else {}))
    desktop(b); phone(b)
    b.close()
print(f'FAILURES: {fails}')
