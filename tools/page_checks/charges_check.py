"""The Fit card's Charges list, drag and drop and "not on board" (v2026.10.14.76, roadmap/charges-plan.md delivery 2; the owner:
a list of "every usable charge for those weapons/launchers", "dropping on a single module loads it there. dropping in
middle of ring loads to all possible modules", "not on board" for a charge the fit doesn't have).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/charges_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The real page, ESI and the game's icons served from pyfa's SDE copy. Every number is compared with the page's own engine
run on a pasted fit that HAS that charge (buildFitFromEft), a path that doesn't go through the Charges code.
  * a Drake (6 Heavy Missile Launcher II with Scourge; Nova and Scourge Fury in cargo): the list is pyfa's getValidCharges
    for the launcher (written here from the SDE: published types of chargeGroup1-4, volume within the capacity); on board
    first (loaded x6, cargo 1,000 / 500), the rest "not on board" by DPS; each row's DPS and range = the pasted fit's;
    the damage-type chips filter it;
  * a click on Caldari Navy Scourge loads it in all six: Firepower = the pasted fit's, the amber "not on board" tag, six
    dashed tiles, the Loaded line says so; "use the fit's own" brings the fit back;
  * dragging Nova onto the first launcher loads that one only (1 Nova + 5 Scourge = that pasted fit), the list fading
    while dragging; then setting the Nova launcher online leaves 5 Scourge firing, setting a Scourge one online instead
    leaves 4 Scourge + Nova (the state follows the copy);
  * dragging Scourge Fury into the middle of the ring loads all six (on board: no tag); Enter on a row loads it too; the
    reset button restores the fit's charges and states; Escape closes the list;
  * two launcher types that share charges (a Caracal with Rapid Light and Light Missile Launchers): two sections; a drop
    in the middle loads both types;
  * list view: each launcher row's charge chip opens the list at that launcher; the charge rows aren't repeated;
  * My Ship keeps a loaded charge after a reload;
  * 390 and 320 px: the list is a bottom sheet; a finger held on a row then dragged onto a launcher loads that one; no
    sideways scroll; no page errors.
v2026.10.14.75 fails (no Charges list).
"""
import sys, os, re, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from esi_from_sde import route_all, icon_route, run_async
from pyfa_sde import types, td, _en
from playwright.sync_api import sync_playwright

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
CHROMIUM = os.environ.get('CHROMIUM_PATH') or ('/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') else None)
R = '#fitAnalyzerResults'
HML, SCOURGE, NOVA, FURY, NAVY = 2410, 209, 206, 2629, 27441
def drake(charges, launchers=None, cargo=True):
    lines = [f'Heavy Missile Launcher II, {c}' if c else 'Heavy Missile Launcher II' for c in charges]
    return ("[Drake, Charges]\nBallistic Control System II\nBallistic Control System II\nDamage Control II\n\n"
            "Large Shield Extender II\nLarge Shield Extender II\nMultispectrum Shield Hardener II\n10MN Afterburner II\n\n"
            + '\n'.join(lines) + "\n\nMedium Core Defense Field Extender I\nMedium Core Defense Field Extender I\nMedium Core Defense Field Extender I\n\n"
            "Hobgoblin II x5\n" + ("\n\nNova Heavy Missile x1000\nScourge Fury Heavy Missile x500\n" if cargo else ''))
NAME = {i: _en(types[str(i)].get('typeName') or types[str(i)].get('name')) for i in (SCOURGE, NOVA, FURY, NAVY)}
DRAKE = drake([NAME[SCOURGE]] * 6)
CARACAL = """[Caracal, Two launcher types]
Ballistic Control System II

10MN Afterburner II
Medium Shield Extender II

Rapid Light Missile Launcher II, Scourge Light Missile
Rapid Light Missile Launcher II, Scourge Light Missile
Light Missile Launcher II, Scourge Light Missile
Light Missile Launcher II, Scourge Light Missile
"""
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok

# pyfa Module.getValidCharges for a weapon, from the SDE
def A(t): return {x['attributeID']: x['value'] for x in (td.get(str(t)) or {}).get('dogmaAttributes', [])}
GROUP_TYPES = {}
for k, v in types.items(): GROUP_TYPES.setdefault(v.get('groupID'), []).append(int(k))
def valid_charges(w):
    a, cap = A(w), types[str(w)].get('capacity')
    out = set()
    for g in [int(a[x]) for x in (604, 605, 606, 609) if a.get(x)]:
        for t in GROUP_TYPES.get(g, []):
            v = types[str(t)]
            if not v.get('published'): continue
            if v.get('volume') is not None and cap is not None and v['volume'] > cap: continue
            if (a.get(128) or 0) > 0 and A(t).get(128) != a.get(128): continue
            out.add(t)
    return out

ENGINE = """async (texts) => { const out = [];
  for(const t of texts){ const {f} = await buildFitFromEft(t); const e = f.estimate;
    out.push({total: e.dpsFixed, w: (e.application.weapons || []).map(w => ({id: w.weaponTypeId, ammo: w.ammoTypeId, dps: w.dps})), range: e.rangeEstimates}); }
  return out; }"""
LIST = f"""() => [...document.querySelectorAll('{R} .chg-pop .chg-w')].map(s => ({{weapon: Number(s.dataset.weapon), head: s.querySelector('.chg-wh').innerText,
  rows: [...s.querySelectorAll('.chg-row')].map(r => ({{id: Number(r.dataset.charge), dmg: r.dataset.dmg, hidden: r.hidden, name: r.querySelector('.chg-n').textContent,
    v: [...r.querySelectorAll('.chg-v')].map(x => x.textContent), tag: r.querySelector('.chg-tag').textContent, cur: r.classList.contains('is-cur'), away: r.classList.contains('is-away'),
    sec: (() => {{ let p = r.previousElementSibling; while(p && !p.classList.contains('chg-sec')) p = p.previousElementSibling; return p ? p.textContent : ''; }})()}}))}}))"""
TILES = f"""() => [...document.querySelectorAll('{R} .fit-ring .ms-tile[data-type-id="{HML}"]')].sort((a, b) => a.dataset.copy - b.dataset.copy).map(t => ({{charge: Number(t.dataset.chargeId || 0), away: t.classList.contains('chg-away'), from: t.dataset.from, copy: Number(t.dataset.copy)}}))"""
def total(pg):
    return pg.evaluate("""(R) => { const c = document.querySelector(R + ' .fl-stats'); const row = c.querySelector('button.cc-row[data-card="fp"]');
      if(row) return row.querySelector('.cc-sum').textContent.split(' DPS')[0]; return c.innerText.split('TOTAL DPS')[1].trim().split(/\\s+/)[0]; }""", R)
def settle(pg, ms=250):
    pg.wait_for_timeout(ms)
    pg.wait_for_function(f"() => !document.querySelector('{R} .fit-card-busy') && !(document.querySelector('{R} .chg-pop') && !document.querySelector('{R} .chg-pop .chg-row, {R} .chg-pop .chg-w'))", timeout=60000)
    pg.wait_for_timeout(ms)
def paste(pg, text):
    pg.evaluate(f"() => {{ const r = document.querySelector('{R}'); if(r) r.innerHTML = ''; }}")
    pg.fill('#fitAnalyzerInput', text); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-ring, {R} .ms-row', timeout=60000); settle(pg)
def open_list(pg):
    if not pg.locator(f'{R} .chg-pop').count(): pg.click(f'{R} button.chg-btn')
    pg.wait_for_selector(f'{R} .chg-pop .chg-row', timeout=60000); settle(pg)
def mouse_drag(pg, src, dst_xy):
    b = pg.locator(src).first.bounding_box()
    pg.mouse.move(b['x'] + b['width'] / 2, b['y'] + b['height'] / 2); pg.mouse.down()
    pg.mouse.move(b['x'] + b['width'] / 2 + 12, b['y'] + b['height'] / 2 + 12, steps=3); pg.wait_for_timeout(250)   # the fade's transition
    faded = pg.evaluate(f"() => getComputedStyle(document.querySelector('{R} .chg-pop')).opacity")
    pg.mouse.move(*dst_xy, steps=8); pg.mouse.up(); settle(pg)
    return float(faded)
def center(pg, sel):
    b = pg.locator(sel).first.bounding_box(); return (b['x'] + b['width'] / 2, b['y'] + b['height'] / 2)
def jsr(x): return int(x + 0.5)
def km_text(r):
    if r is None: return ''
    if r.get('kind') == 'missile': return f"{r['travelDistanceM'] / 1000:.1f} km"
    o, f = r['optimalM'] / 1000, r['falloffM'] / 1000
    return f"{o:.{1 if o < 10 else 0}f}+{f:.{1 if f < 10 else 0}f} km"

with sync_playwright() as p:
    b = p.chromium.launch(**({'executable_path': CHROMIUM} if CHROMIUM else {}))
    # ---------------- desktop
    ctx = b.new_context(viewport={'width': 1440, 'height': 1100}); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.route(re.compile(r'https://images\.evetech\.net/.*'), icon_route)
    pg.goto('file://' + HTML); pg.evaluate("localStorage.clear(); localStorage.setItem('dscanFitView', 'ring')"); pg.reload(); pg.click('#tabBtnFit')
    paste(pg, DRAKE)
    check(pg.locator(f'{R} button.chg-btn').count() == 1, '1440: the Fit card has a Charges button')
    if not pg.locator(f'{R} button.chg-btn').count(): print(f'FAILURES: {fails}'); sys.exit(1)
    open_list(pg)
    L = pg.evaluate(LIST)
    want = valid_charges(HML)
    rows = L[0]['rows'] if L else []
    check(len(L) == 1 and L[0]['weapon'] == HML and '×6' in L[0]['head'] and {r['id'] for r in rows} == want,
          f'1440: one section, Heavy Missile Launcher II ×6, its rows = pyfa getValidCharges ({len(rows)} rows, {len(want)} valid)')
    on = [r for r in rows if r['sec'] == 'On board']
    check([(r['id'], r['tag']) for r in on] == [(SCOURGE, 'loaded ×6'), (FURY, 'cargo 500'), (NOVA, 'cargo 1,000')] and on[0]['cur'],
          f'1440: on board first, loaded then cargo by DPS ({[(r["name"], r["tag"]) for r in on]})')
    away = [r for r in rows if r['sec'] == 'Not on board']
    dps_away = [int(r['v'][0].replace(',', '')) for r in away]
    check(away and all(r['tag'] == 'not on board' and r['away'] for r in away) and dps_away == sorted(dps_away, reverse=True),
          f'1440: the rest "not on board", by DPS ({dps_away[:6]}...)')
    sample = [SCOURGE, FURY, NOVA, NAVY] + [r['id'] for r in away[-2:]]
    eng = run_async(pg, ENGINE, [drake([_en(types[str(c)].get('typeName') or types[str(c)].get('name'))] * 6) for c in sample])
    bad = []
    for c, e in zip(sample, eng):
        r = next(x for x in rows if x['id'] == c)
        d = sum(w['dps'] for w in e['w'] if w['id'] == HML)
        rg = next((x for x in e['range'] if x['weaponTypeId'] == HML and x['ammoTypeId'] == c), None)
        if r['v'][0] != f'{jsr(d):,}' or r['v'][1] != km_text(rg): bad.append((r['name'], r['v'], jsr(d), km_text(rg)))
    check(not bad, f'1440: each row\'s DPS and range = the pasted fit with that charge ({bad or len(sample)} rows)')
    pg.click(f'{R} button.chg-chip[data-chg-filter="em"]'); pg.wait_for_timeout(150)
    vis = pg.evaluate(LIST)[0]['rows']
    check(all((r['dmg'] == 'em') != r['hidden'] for r in vis) and any(not r['hidden'] for r in vis), '1440: the EM chip shows the EM charges only')
    pg.click(f'{R} button.chg-chip[data-chg-filter="all"]')
    # click: Caldari Navy Scourge in all six
    pg.click(f'{R} .chg-row[data-charge="{NAVY}"]'); settle(pg)
    want_total = run_async(pg, ENGINE, [drake([NAME[NAVY]] * 6)])[0]['total']
    t = pg.evaluate(TILES)
    loaded = pg.inner_text(f'{R} .fit-ring-loaded')
    check(total(pg) == f'{want_total:,}' and pg.locator(f'{R} .chg-away-tag').count() == 1 and [x['charge'] for x in t] == [NAVY] * 6 and all(x['away'] for x in t)
          and 'not on board' in loaded, f'1440: a click loads Caldari Navy Scourge in all six: {total(pg)} DPS (pasted {want_total}), "not on board" tag, dashed tiles, Loaded line ({loaded!r})')
    pg.click(f'{R} .chg-close'); settle(pg)   # the list covers the ring while open
    pg.click(f'{R} button.chg-own'); settle(pg)
    base_total = run_async(pg, ENGINE, [DRAKE])[0]['total']
    check(total(pg) == f'{base_total:,}' and pg.locator(f'{R} .chg-away-tag').count() == 0 and [x['charge'] for x in pg.evaluate(TILES)] == [SCOURGE] * 6,
          f'1440: "use the fit\'s own" brings it back ({total(pg)} DPS)')
    # drag Nova onto the first launcher
    open_list(pg)
    first = f'{R} .fit-ring .ms-tile[data-type-id="{HML}"][data-copy="0"]'
    faded = mouse_drag(pg, f'{R} .chg-row[data-charge="{NOVA}"]', center(pg, first))
    t = pg.evaluate(TILES)
    mix = run_async(pg, ENGINE, [drake([NAME[NOVA]] + [NAME[SCOURGE]] * 5), drake([NAME[SCOURGE]] * 5), drake([NAME[NOVA]] + [NAME[SCOURGE]] * 4)])
    check([x['charge'] for x in t] == [NOVA] + [SCOURGE] * 5 and total(pg) == f"{mix[0]['total']:,}" and faded < 0.5 and pg.locator(f'{R} .chg-away-tag').count() == 0,
          f'1440: Nova dragged onto the first launcher loads that one only ({total(pg)} = pasted {mix[0]["total"]}; the list faded to {faded} while dragging; on board: no tag)')
    pg.click(f'{R} .chg-close'); settle(pg)
    pg.click(first); settle(pg)   # the Nova launcher -> online
    check(total(pg) == f"{mix[1]['total']:,}", f'1440: the Nova launcher set online: 5 Scourge fire ({total(pg)} = pasted {mix[1]["total"]})')
    pg.click(first); settle(pg); pg.click(first); settle(pg)   # online -> offline -> active again
    pg.click(f'{R} .fit-ring .ms-tile[data-type-id="{HML}"][data-copy="3"]'); settle(pg)
    check(total(pg) == f"{mix[2]['total']:,}", f'1440: a Scourge launcher set online instead: Nova + 4 Scourge fire ({total(pg)} = pasted {mix[2]["total"]})')
    # drop Scourge Fury in the middle
    open_list(pg)
    mouse_drag(pg, f'{R} .chg-row[data-charge="{FURY}"]', center(pg, f'{R} .fit-ring-ship'))
    t = pg.evaluate(TILES)
    check([x['charge'] for x in t] == [FURY] * 6 and pg.locator(f'{R} .chg-away-tag').count() == 0, f'1440: Scourge Fury dropped in the middle loads all six ({[x["charge"] for x in t]})')
    pg.focus(f'{R} .chg-row[data-charge="{NOVA}"]'); pg.keyboard.press('Enter'); settle(pg)
    check([x['charge'] for x in pg.evaluate(TILES)] == [NOVA] * 6, '1440: Enter on a row loads it')
    pg.click(f'{R} button.ms-reset'); settle(pg)
    check(total(pg) == f'{base_total:,}' and [x['charge'] for x in pg.evaluate(TILES)] == [SCOURGE] * 6 and all(x['from'] == 'active' for x in pg.evaluate(TILES)),
          f'1440: the reset button restores the fit\'s charges and states ({total(pg)})')
    open_list(pg); pg.focus(f'{R} .chg-row'); pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    check(pg.locator(f'{R} .chg-pop').count() == 0, '1440: Escape closes the list')
    # two launcher types sharing charges
    paste(pg, CARACAL); open_list(pg)
    L = pg.evaluate(LIST)
    fury_l = next((r['id'] for s in L for r in s['rows'] if r['name'] == 'Scourge Fury Light Missile'), None)
    check(len(L) == 2 and fury_l, f'1440 Caracal: two sections ({[s["head"].split(chr(10))[0] for s in L]})')
    if fury_l:
        mouse_drag(pg, f'{R} .chg-row[data-charge="{fury_l}"]', center(pg, f'{R} .fit-ring-ship'))
        ch = pg.evaluate(f"() => [...document.querySelectorAll('{R} .fit-ring .ms-tile.has-charge')].map(t => Number(t.dataset.chargeId))")
        check(len(ch) == 4 and set(ch) == {fury_l}, f'1440 Caracal: a drop in the middle loads both launcher types ({ch})')
    # list view
    paste(pg, DRAKE)
    pg.click(f'{R} button.fit-view-btn[data-view="list"]'); settle(pg)
    chips = pg.evaluate(f"() => [...document.querySelectorAll('{R} button.ms-chg')].map(c => c.innerText)")
    dup = pg.evaluate(f"() => [...document.querySelectorAll('{R} .fl-fit .fititem:not(.ms-row)')].filter(r => /Scourge Heavy Missile/.test(r.textContent)).length")
    check(len(chips) == 6 and all('Scourge Heavy Missile' in c for c in chips) and dup == 0, f'1440 list: six launcher rows carry their charge, no repeated charge row ({len(chips)}, {dup})')
    pg.click(f'{R} button.ms-chg'); pg.wait_for_selector(f'{R} .chg-pop .chg-row', timeout=60000)
    check(pg.locator(f'{R} .chg-pop .chg-w[data-weapon="{HML}"]').count() == 1, '1440 list: a chip opens the list at its launcher')
    # My Ship keeps a loaded charge
    pg.click(f'{R} .chg-row[data-charge="{NAVY}"]'); settle(pg)
    pg.click(f'{R} button.mys-set'); pg.wait_for_timeout(800)
    pg.reload(); pg.wait_for_timeout(500)
    rec = pg.evaluate("() => { try{ const s = JSON.parse(localStorage.getItem('dscanMyShip')); const l = s.list || [s]; return l.map(r => r.chargePicks || null); }catch(e){ return String(e); } }")
    check(isinstance(rec, list) and any(r and r.get(str(HML)) == [NAVY] * 6 for r in rec), f'1440: My Ship keeps the loaded charge after a reload ({rec})')
    sc = pg.evaluate("[document.documentElement.scrollWidth, innerWidth]")
    check(sc[0] <= sc[1] and not errs, f'1440: no sideways scroll {sc}, no page errors {errs[:2]}')
    ctx.close()
    # ---------------- phone
    for w in (390, 320):
        ctx = b.new_context(viewport={'width': w, 'height': 844}, is_mobile=True, has_touch=True); pg = ctx.new_page()
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        route_all(pg); pg.route(re.compile(r'https://images\.evetech\.net/.*'), icon_route)
        pg.goto('file://' + HTML); pg.evaluate("localStorage.clear(); localStorage.setItem('dscanFitView', 'ring')"); pg.reload(); pg.click('#tabBtnFit')
        paste(pg, DRAKE)
        if not pg.locator(f'{R} .fit-ring').is_visible(): pg.click(f'{R} button.cc-toggle[data-card="fit"]'); settle(pg)
        pg.locator(f'{R} .fit-ring').scroll_into_view_if_needed()
        open_list(pg)
        box = pg.locator(f'{R} .chg-pop').bounding_box()
        pos = pg.evaluate(f"() => getComputedStyle(document.querySelector('{R} .chg-pop')).position")
        check(pos == 'fixed' and abs(box['x']) < 1 and abs(box['width'] - w) < 1 and abs(box['y'] + box['height'] - 844) < 1, f'{w}px: the list is a sheet at the bottom ({pos}, {box})')
        # a finger held on Nova, then dragged onto the first launcher (pointer events, as a touch screen sends them)
        tile = pg.locator(f'{R} .fit-ring .ms-tile[data-type-id="{HML}"][data-copy="0"]').bounding_box()
        pg.evaluate("""async ([R, cid, x, y]) => { const row = document.querySelector(R + ` .chg-row[data-charge="${cid}"]`), r = row.getBoundingClientRect();
          const ev = (t, cx, cy) => row.dispatchEvent(new PointerEvent(t, {bubbles: true, cancelable: true, pointerId: 7, pointerType: 'touch', isPrimary: true, button: 0, buttons: 1, clientX: cx, clientY: cy}));
          ev('pointerdown', r.left + 40, r.top + r.height / 2); await new Promise(res => setTimeout(res, 450));
          ev('pointermove', (r.left + x) / 2, (r.top + y) / 2); ev('pointermove', x, y); ev('pointerup', x, y); }""",
            [R, NOVA, tile['x'] + tile['width'] / 2, tile['y'] + tile['height'] / 2])
        settle(pg)
        t = pg.evaluate(TILES)
        check([x['charge'] for x in t] == [NOVA] + [SCOURGE] * 5, f'{w}px: a finger held on Nova and dragged onto the first launcher loads that one ({[x["charge"] for x in t]})')
        sc = pg.evaluate("[document.documentElement.scrollWidth, innerWidth]")
        check(sc[0] <= sc[1] and not errs, f'{w}px: no sideways scroll {sc}, no page errors {errs[:2]}')
        ctx.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
