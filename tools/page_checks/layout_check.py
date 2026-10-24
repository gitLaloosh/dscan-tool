"""Layout check (v2026.10.14.15, layout Phase 1): loads the real index.html in Chromium at desktop (1440),
tablet (1100) and phone (375, mobile emulation) widths and checks the .fit-layout columns and that every
control still works after the move: mode buttons, the ASB out-of-charges toggle, module states, reset, and
the Pilot Analyzer's per-loss tabs (built with renderFitTabs from a pasted fit). Also checks there is no
sideways scrolling and that, from 900px up, the Fit column stays pinned while a state change recalculates.
v2026.10.14.16 (Phase 2): the Ring / List fit view -- default per width, one tile per module copy (same count
as the list's state rows), no two tiles overlapping and all inside the ring (a full 8/8/8 rack fit with rigs
and subsystems), a tile click recalculates like a list button, and the choice is remembered after a reload.
v2026.10.14.18 (Phase 3): collapsible cards -- default open/closed per width (phone: only Weaknesses open),
a collapsed card's summary row equals the open card's numbers, the choice survives a module-state change,
each Pilot Analyzer loss keeps its own, and keyboard focus stays on the toggle.
v2026.10.14.21: the Fit card collapses with the same toggle (no "hide" link, no "Module states assumed"
label), collapsed summary row, Pilot Analyzer default by width, reset icon button beside Ring / List.
v2026.10.14.19: collapsible bays in the Fit card (drone bay, cargo...) -- defaults (v.20: only the drone bay
open), summary rows, kept through a module-state change.
v2026.10.14.17 (the owner: "test how large strings will affect layout"): long strings everywhere -- the longest real
ship / module / charge / drone / implant / subsystem names in the SDE, a long fit name with and without spaces,
an unrecognized 120-character line, a 37-character pilot name (EVE's maximum), long D-scan names -- and every
visible element must stay inside its card / column, with no sideways scrolling. Drone rows: every row the same
two-line grid (squares right-aligned in one column).

    PYFA_SRC=/path/to/pyfa python3 tools/page_checks/layout_check.py [index.html]

Needs Playwright with Chromium (PLAYWRIGHT_BROWSERS_PATH or CHROMIUM_PATH). Ends with 'FAILURES: N' (must be 0).
LESSON #33: check layout at a real phone width with mobile emulation, not only a desktop screenshot.
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esi_from_sde import route_all
from playwright.sync_api import sync_playwright
HECATE = """[Hecate, mode test]
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

Small Ancillary Current Router I
Small Ancillary Current Router I
Small Ancillary Current Router I


Navy Cap Booster 50 x20
"""
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
html = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))); bad = []
CHROMIUM = os.environ.get('CHROMIUM_PATH') or ('/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') else None)
def total_dps(pg, scope):
    """Total DPS as shown, from the open Firepower card or its collapsed summary row (v.18)."""
    return pg.evaluate("""(scope) => { const c = document.querySelector(scope + ' .fl-stats');
      const row = c.querySelector('button.cc-row[data-card="fp"]');
      if(row) return row.querySelector('.cc-sum').textContent.split(' DPS')[0];
      return c.innerText.split('TOTAL DPS')[1].trim().split(/\\s+/)[0]; }""", scope)
def check(c, msg):
    print(('OK   ' if c else 'FAIL ') + msg)
    if not c: bad.append(msg)
# v2026.10.14.49: every card's info panel, opened one at a time: on screen, and on a wide layout inside its card's
# column (the Weaknesses / Mode panel in the narrow left column used to open off the screen's left edge).
INFO_PANELS = """async (W) => {
  const bad = [], seen = [];
  for(const d of document.querySelectorAll('#fitAnalyzerResults details.info-pop')){
    if(!d.offsetParent) continue;
    d.open = true; await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
    const body = d.querySelector('.info-body');
    body.scrollIntoView({block: 'nearest'}); await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
    // v2026.10.14.52 (the owner: the Matchup's panel was cut off by the board's edge): every corner of the panel must be
    // the panel itself on screen, not something drawn over it or a clipped edge
    const b = body.getBoundingClientRect();
    const hidden = [[b.left + 8, b.top + 8], [b.right - 8, b.top + 8], [b.left + 8, b.bottom - 8], [b.right - 8, b.bottom - 8]]
      .filter(([x, y]) => { const e = document.elementFromPoint(x, y); return !(e && body.contains(e)); });
    if(hidden.length) bad.push(`${d.dataset.info}: ${hidden.length} corner(s) not visible (clipped or covered)`);
    const r = body.getBoundingClientRect(), col = d.closest('.fit-layout > div');
    const c = col ? col.getBoundingClientRect() : {left: 0, right: W};
    seen.push(d.dataset.info);
    if(r.left < -1 || r.right > W + 1 || r.width < 200) bad.push(`${d.dataset.info}: ${Math.round(r.left)}..${Math.round(r.right)} of the ${W} px window`);
    else if(W >= 600 && (r.left < c.left - 1 || r.right > c.right + 1)) bad.push(`${d.dataset.info}: ${Math.round(r.left)}..${Math.round(r.right)}, column ${Math.round(c.left)}..${Math.round(c.right)}`);
    d.open = false;
  }
  return {bad, seen};
}"""
with sync_playwright() as p:
    b = p.chromium.launch(**({'executable_path': CHROMIUM} if CHROMIUM else {}))
    for W in (1440, 1100, 375):
        ctx = b.new_context(viewport={'width': W, 'height': 900}, is_mobile=W < 600, has_touch=W < 600)
        pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        route_all(pg)
        pg.goto('file://' + html); pg.click('#tabBtnFit'); pg.fill('#fitAnalyzerInput', HECATE); pg.click('#fitAnalyzerBtn')
        pg.wait_for_function("() => document.querySelector('#fitAnalyzerResults .fit-layout')", timeout=30000); pg.wait_for_timeout(600)
        R = '#fitAnalyzerResults'
        sw = pg.evaluate('document.documentElement.scrollWidth'); check(sw <= W, f'{W}: no sideways scroll (page width {sw})')
        areas = pg.evaluate("""() => ['fl-beat','fl-fit','fl-stats'].map(c => { const r = document.querySelector('#fitAnalyzerResults .'+c).getBoundingClientRect(); return [c, Math.round(r.x), Math.round(r.y + scrollY), Math.round(r.width)]; })""")
        print('  areas', areas)
        # v2026.10.14.37: "Their damage on you" (FIT_LAYOUT band) sits above Fit + stats from 1280 px, so Fit and
        # stats start level with each other, below it; Weaknesses starts at the top beside it
        if W >= 1280: check(areas[0][1] < areas[1][1] < areas[2][1] and abs(areas[1][2]-areas[2][2]) < 5 and areas[0][2] <= areas[1][2], f'{W}: three columns side by side')
        elif W >= 900: check(areas[1][1] < areas[0][1] and areas[0][1] == areas[2][1] and areas[2][2] > areas[0][2], f'{W}: fit left, beat above stats on the right')
        else: check(areas[0][2] < areas[1][2] < areas[2][2] and areas[0][1] == areas[1][1] == areas[2][1], f'{W}: one column beat > fit > stats')
        dps = lambda: total_dps(pg, R)
        d0 = dps()
        # mode switch
        pg.locator(R + ' .td-mode-btn').nth(2).click(); pg.wait_for_timeout(400)
        d1 = dps(); check(d1 != d0, f'{W}: mode switch re-renders stats ({d0} -> {d1})')
        check('active' in pg.locator(R + ' .td-mode-btn').nth(2).get_attribute('class'), f'{W}: clicked mode marked active')
        pg.locator(R + ' .td-mode-btn').nth(0).click(); pg.wait_for_timeout(400)
        check(dps() == d0, f'{W}: back to the first mode gives the first DPS')
        # module state: switch the first blaster off, fit column must not move
        if W >= 900: pg.evaluate("window.scrollTo(0, document.querySelector('#fitAnalyzerResults .fl-fit').getBoundingClientRect().top + scrollY + 250)"); pg.wait_for_timeout(200)
        y0 = pg.evaluate("document.querySelector('#fitAnalyzerResults .fl-fit').getBoundingClientRect().top")
        btn = pg.locator(R + ' button.ms-state[data-from="active"]').first
        btn.click(); pg.wait_for_function("() => !document.querySelector('#fitAnalyzerResults .fit-card-busy') && document.querySelector('#fitAnalyzerResults button.ms-reset.is-custom')", timeout=30000); pg.wait_for_timeout(300)
        d2 = dps(); check(d2 != d0, f'{W}: switching a blaster to online recalculates ({d0} -> {d2})')
        y1 = pg.evaluate("document.querySelector('#fitAnalyzerResults .fl-fit').getBoundingClientRect().top")
        if W >= 900: check(abs(y1 - y0) < 2 and abs(y0 - 12) < 2, f'{W}: fit column pinned at the top and stays put on a state change ({y0:.0f} -> {y1:.0f})')
        # ASB toggle still wired
        n = pg.locator(R + ' .cap-asb-toggle').count()
        if n:
            t0 = pg.inner_text(R + ' .fl-stats'); pg.locator(R + ' .cap-asb-toggle').first.click(); pg.wait_for_timeout(400)
            check(pg.inner_text(R + ' .fl-stats') != t0, f'{W}: ASB charges toggle re-renders')
        pg.locator(R + ' button.ms-reset').click(); pg.wait_for_function("() => !document.querySelector('#fitAnalyzerResults button.ms-reset.is-custom')", timeout=30000); pg.wait_for_timeout(300)
        check(dps() == d0, f'{W}: reset to best case restores DPS')
        # Pilot Analyzer path: renderFitTabs with two "losses" built from the same paste
        pg.click('#tabBtnPilot')
        res = pg.evaluate("""async (text) => {
          const parsed = await parseEftFit(text);
          const mk = async (day) => { const modes = {}; const order = hullModeOrder(parsed.shipTypeId); const active = resolveModeKey(parsed.shipTypeId, null);
            for (const m of order) modes[m] = await estimateHpAndDps(parsed.shipTypeId, parsed.tally, parsed.cargoItemIds, parsed.highSlotByFlag, m, parsed.midSlotByFlag);
            return { km: {killmail_time: day}, killmailId: 1, tally: parsed.tally, highSlotByFlag: parsed.highSlotByFlag, estimate: modes[active], tacticalModes: modes, activeMode: active,
              input: {shipTypeId: parsed.shipTypeId, tally: parsed.tally, cargoItemIds: parsed.cargoItemIds, highSlotByFlag: parsed.highSlotByFlag, midSlotByFlag: parsed.midSlotByFlag} }; };
          renderFitTabs('Test Pilot', 'Hecate', [await mk('2026-10-01T00:00:00Z'), await mk('2026-10-02T00:00:00Z')], parsed.idToName);
          return document.querySelectorAll('#fitResults .fit-layout').length; }""", HECATE)
        check(res == 2, f'{W}: Pilot Analyzer renders one layout per loss ({res})')
        P = '#fitResults .subtab-panel[data-idx="0"]'
        opened = pg.evaluate(f"document.querySelector('{P} button.cc-toggle[data-card=fit]').getAttribute('aria-expanded') === 'true'")
        check(opened == (W >= 900), f'{W}: Pilot fit card starts {"open" if W >= 900 else "closed"} ({opened})')
        if not opened:
            ps = pg.text_content(P + ' button.cc-row[data-card=fit] .cc-sum')
            check(ps.startswith('Hecate — ') and ps.endswith(' loss'), f'{W}: collapsed Pilot fit card names the loss "{ps}"')
            pg.locator(P + ' button.cc-toggle[data-card=fit]').click(); pg.wait_for_timeout(200)
        pdps = lambda: total_dps(pg, P)
        p0 = pdps(); pg.locator(P + ' button.ms-state[data-from="active"]').first.click()
        pg.wait_for_function(f"() => document.querySelector('{P} button.ms-reset.is-custom') && !document.querySelector('{P} .fit-card-busy')", timeout=30000); pg.wait_for_timeout(300)
        check(pdps() != p0, f'{W}: Pilot tab 1 state change recalculates ({p0} -> {pdps()})')
        check(pg.evaluate("!document.querySelector('#fitResults .subtab-panel[data-idx=\"1\"] button.ms-reset.is-custom')"), f'{W}: Pilot tab 2 unaffected')
        pg.locator(P + ' .td-mode-btn').nth(1).click(); pg.wait_for_timeout(400)
        check('active' in pg.locator(P + ' .td-mode-btn').nth(1).get_attribute('class') and pg.locator(P + ' button.ms-reset.is-custom').count() == 1, f'{W}: Pilot mode switch keeps the custom states')
        check(not errs, f'{W}: no page errors {errs}')
        ctx.close()
    b.close()

STRESS = """[Legion, ring stress]
Tracking Enhancer II
Damage Control II
Heat Sink II
Heat Sink II
Heat Sink II
Sentient Signal Amplifier
Heat Sink II
Heat Sink II

Sensor Booster II
Tracking Computer II
50MN Microwarpdrive II
Stasis Webifier II
Warp Disruptor II
Sensor Booster II
Tracking Computer II
Stasis Webifier II

Heavy Beam Laser II, Gleam M
Heavy Beam Laser II, Gleam M
Heavy Beam Laser II, Gleam M
Heavy Beam Laser II, Gleam M
Heavy Beam Laser II, Gleam M
Heavy Beam Laser II, Gleam M
Covert Ops Cloaking Device II
Sisters Expanded Probe Launcher

Medium Hyperspatial Velocity Optimizer II
Medium Polycarbon Engine Housing II
Medium Energy Locus Coordinator II

Legion Core - Dissolution Sequencer
Legion Defensive - Covert Reconfiguration
Legion Offensive - Liquid Crystal Magnifiers
Legion Propulsion - Intercalated Nanofibers
"""
# v2026.10.14.49: every card's info panel, opened one at a time: on screen, and on a wide layout inside its card's
# column (the Weaknesses / Mode panel in the narrow left column used to open off the screen's left edge).
INFO_PANELS = """async (W) => {
  const bad = [], seen = [];
  for(const d of document.querySelectorAll('#fitAnalyzerResults details.info-pop')){
    if(!d.offsetParent) continue;
    d.open = true; await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
    const body = d.querySelector('.info-body');
    body.scrollIntoView({block: 'nearest'}); await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
    // v2026.10.14.52 (the owner: the Matchup's panel was cut off by the board's edge): every corner of the panel must be
    // the panel itself on screen, not something drawn over it or a clipped edge
    const b = body.getBoundingClientRect();
    const hidden = [[b.left + 8, b.top + 8], [b.right - 8, b.top + 8], [b.left + 8, b.bottom - 8], [b.right - 8, b.bottom - 8]]
      .filter(([x, y]) => { const e = document.elementFromPoint(x, y); return !(e && body.contains(e)); });
    if(hidden.length) bad.push(`${d.dataset.info}: ${hidden.length} corner(s) not visible (clipped or covered)`);
    const r = body.getBoundingClientRect(), col = d.closest('.fit-layout > div');
    const c = col ? col.getBoundingClientRect() : {left: 0, right: W};
    seen.push(d.dataset.info);
    if(r.left < -1 || r.right > W + 1 || r.width < 200) bad.push(`${d.dataset.info}: ${Math.round(r.left)}..${Math.round(r.right)} of the ${W} px window`);
    else if(W >= 600 && (r.left < c.left - 1 || r.right > c.right + 1)) bad.push(`${d.dataset.info}: ${Math.round(r.left)}..${Math.round(r.right)}, column ${Math.round(c.left)}..${Math.round(c.right)}`);
    d.open = false;
  }
  return {bad, seen};
}"""
with sync_playwright() as p:
    b = p.chromium.launch(**({'executable_path': CHROMIUM} if CHROMIUM else {}))
    for W in (1440, 1100, 375):
        ctx = b.new_context(viewport={'width': W, 'height': 900}, is_mobile=W < 600, has_touch=W < 600)
        pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        route_all(pg)
        def run(text):
            pg.goto('file://' + html); pg.click('#tabBtnFit'); pg.fill('#fitAnalyzerInput', text); pg.click('#fitAnalyzerBtn')
            pg.wait_for_function("() => document.querySelector('#fitAnalyzerResults .fit-layout')", timeout=30000); pg.wait_for_timeout(500)
        R = '#fitAnalyzerResults'
        run(STRESS)
        want = 'ring' if W >= 600 else 'list'
        on = pg.evaluate(f"document.querySelector('{R} .fit-view-btn.on').dataset.view")
        check(on == want, f'{W}: default fit view {want} ({on})')
        if on != 'ring': pg.click(R + ' .fit-view-btn[data-view="ring"]'); pg.wait_for_timeout(300)
        tiles = pg.evaluate(f"""() => [...document.querySelectorAll('{R} .fit-ring .ms-tile')].map(t => {{ const r = t.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; }})""")
        box = pg.evaluate(f"() => {{ const r = document.querySelector('{R} .fit-ring').getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; }}")
        overlap = sum(1 for i in range(len(tiles)) for j in range(i + 1, len(tiles))
                      if min(tiles[i][2], tiles[j][2]) - max(tiles[i][0], tiles[j][0]) > 0.5 and min(tiles[i][3], tiles[j][3]) - max(tiles[i][1], tiles[j][1]) > 0.5)
        inside = all(t[0] >= box[0] - 0.5 and t[1] >= box[1] - 0.5 and t[2] <= box[2] + 0.5 and t[3] <= box[3] + 0.5 for t in tiles)
        check(len(tiles) == 31 and overlap == 0 and inside, f'{W}: ring of 8/8/8 + 3 rigs + 4 subsystems: {len(tiles)} tiles (31), {overlap} overlapping, all inside the ring: {inside} (ring {box[2]-box[0]:.0f}px)')
        check(pg.locator(R + ' .fit-ring-loaded').count() == 1 and 'Gleam M' in pg.inner_text(R + ' .fit-ring-loaded'), f'{W}: loaded charges listed under the ring')
        sw = pg.evaluate('document.documentElement.scrollWidth'); check(sw <= W, f'{W}: ring view, no sideways scroll ({sw})')
        # same count as the list's rows (Hecate), and a tile click recalculates
        run(HECATE)
        if pg.evaluate(f"document.querySelector('{R} .fit-view-btn.on').dataset.view") != 'ring': pg.click(R + ' .fit-view-btn[data-view="ring"]'); pg.wait_for_timeout(300)
        nt = pg.locator(R + ' .fit-ring .ms-tile').count()
        d0 = total_dps(pg, R)
        pg.locator(R + ' .fit-ring button.ms-tile[data-from="active"]').first.click()
        pg.wait_for_function("() => document.querySelector('#fitAnalyzerResults button.ms-reset.is-custom') && !document.querySelector('#fitAnalyzerResults .fit-card-busy')", timeout=30000); pg.wait_for_timeout(300)
        d1 = total_dps(pg, R)
        check(d1 != d0 and pg.locator(R + ' .fit-ring .ms-tile.ms-online').count() >= 1, f'{W}: ring tile click recalculates ({d0} -> {d1})')
        pg.click(R + ' .fit-view-btn[data-view="list"]'); pg.wait_for_timeout(300)
        nr = pg.locator(R + ' .ms-row').count()
        check(nt == nr and pg.locator(R + ' .fit-ring').count() == 0, f'{W}: list shows the same {nr} module rows as the ring has tiles ({nt})')
        check(pg.locator(R + ' .ms-row.ms-online').count() >= 1 and pg.locator(R + ' button.ms-reset.is-custom').count() == 1, f'{W}: the state set in the ring carries over to the list')
        run(HECATE)
        check(pg.evaluate(f"document.querySelector('{R} .fit-view-btn.on').dataset.view") == 'list', f'{W}: list choice remembered after a reload')
        pg.click(R + ' .fit-view-btn[data-view="ring"]'); pg.wait_for_timeout(200); run(HECATE)
        check(pg.evaluate(f"document.querySelector('{R} .fit-view-btn.on').dataset.view") == 'ring', f'{W}: ring choice remembered after a reload')
        check(not errs, f'{W}: ring checks, no page errors {errs}')
        ctx.close()
    b.close()

CARD_KEYS = ['weak', 'ewar', 'fp', 'rs', 'nav', 'cp', 'dmg']   # dmg: Damage Application (v2026.10.14.36); nv -> nav v2026.10.14.45
with sync_playwright() as p:
    b = p.chromium.launch(**({'executable_path': CHROMIUM} if CHROMIUM else {}))
    for W in (1440, 375):
        ctx = b.new_context(viewport={'width': W, 'height': 900}, is_mobile=W < 600, has_touch=W < 600)
        pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        route_all(pg)
        pg.goto('file://' + html); pg.click('#tabBtnFit'); pg.fill('#fitAnalyzerInput', HECATE.replace('Warp Scrambler II', 'Warp Scrambler II\nStasis Webifier II')); pg.click('#fitAnalyzerBtn')
        pg.wait_for_function("() => document.querySelector('#fitAnalyzerResults .fit-layout')", timeout=30000); pg.wait_for_timeout(400)
        R = '#fitAnalyzerResults'
        state = lambda: pg.evaluate(f"() => Object.fromEntries([...document.querySelectorAll('{R} button.cc-toggle:not(.bay-toggle):not([data-card=fit])')].map(b => [b.dataset.card, b.getAttribute('aria-expanded') === 'true']))")
        st = state()
        want = {k: (W >= 600 or k == 'weak') for k in CARD_KEYS}
        check(st == want, f'{W}: cards open by default as specified {st}')
        # open every card, read its numbers, close it, compare with the summary row
        for k in CARD_KEYS:
            if not state()[k]: pg.click(f'{R} button.cc-toggle[data-card="{k}"]'); pg.wait_for_timeout(150)
        stats = pg.inner_text(R + ' .fl-stats'); beat = pg.inner_text(R + ' .fl-beat')
        dps_open = total_dps(pg, R); ehp_open = stats.split('Total')[1].split('ehp')[0].strip()
        # v2026.10.14.45: every title is its CARD_NAMES name (roadmap/card-names.md), open and collapsed
        TITLES = "() => Object.fromEntries([...document.querySelectorAll('" + R + " button.cc-toggle:not(.bay-toggle)')].map(b => [b.dataset.card, (b.querySelector('.cc-title') || b).textContent.trim() === CARD_NAMES[b.dataset.card]]))"
        t_open = pg.evaluate(TITLES)
        check(set(CARD_KEYS) <= set(t_open) and all(t_open.values()), f'{W}: open card titles are their CARD_NAMES names {t_open}')
        for k in CARD_KEYS:
            pg.click(f'{R} button.cc-toggle[data-card="{k}"]'); pg.wait_for_timeout(150)
            focused = pg.evaluate("document.activeElement && document.activeElement.dataset ? document.activeElement.dataset.card : null")
            check(focused == k, f'{W}: focus stays on the {k} toggle after collapsing ({focused})')
        sums = pg.evaluate(f"() => Object.fromEntries([...document.querySelectorAll('{R} button.cc-row:not(.bay-toggle):not([data-card=fit])')].map(b => [b.dataset.card, b.querySelector('.cc-sum').textContent]))")
        check(set(sums) == set(CARD_KEYS) and all(sums.values()), f'{W}: every card collapses to a summary row {sorted(sums)}')
        t_closed = pg.evaluate(TITLES)
        check(set(CARD_KEYS) <= set(t_closed) and all(t_closed.values()), f'{W}: collapsed card titles are their CARD_NAMES names {t_closed}')
        check(sums['fp'].startswith(dps_open + ' DPS'), f'{W}: Firepower summary "{sums["fp"]}" = open card total {dps_open}')
        check(sums['rs'] == ehp_open + ' EHP', f'{W}: Resistance summary "{sums["rs"]}" = open card total {ehp_open}')
        check('Warp Scrambler II' in sums['ewar'] and 'Stasis Webifier II' in sums['ewar'], f'{W}: EWAR summary names the modules "{sums["ewar"]}"')
        check(('Drains in' in sums['cp'] or 'Stable at' in sums['cp']) and 'm/s' in sums['nav'] and 'align' in sums['nav'], f'{W}: Capacitor / Navigation summaries "{sums["cp"]}" / "{sums["nav"]}"')
        # a module state change keeps the cards collapsed, and the summary follows the new numbers
        pg.locator(R + ' button.ms-state[data-from="active"]').first.click()
        pg.wait_for_function("() => document.querySelector('#fitAnalyzerResults button.ms-reset.is-custom') && !document.querySelector('#fitAnalyzerResults .fit-card-busy')", timeout=30000); pg.wait_for_timeout(300)
        st2 = state()
        check(not any(st2.values()), f'{W}: cards stay collapsed through a module-state change {st2}')
        check(total_dps(pg, R) != dps_open, f'{W}: collapsed Firepower summary follows the recalculation ({dps_open} -> {total_dps(pg, R)})')
        sw = pg.evaluate('document.documentElement.scrollWidth'); check(sw <= W, f'{W}: collapsed cards, no sideways scroll ({sw})')
        # Pilot Analyzer: each loss keeps its own open / closed cards
        pg.click('#tabBtnPilot')
        pg.evaluate("""async (text) => { const parsed = await parseEftFit(text);
          const mk = async (day) => { const est = await estimateHpAndDps(parsed.shipTypeId, parsed.tally, parsed.cargoItemIds, parsed.highSlotByFlag, 'sharpshooter', parsed.midSlotByFlag);
            return { km: {killmail_time: day}, killmailId: 1, tally: parsed.tally, highSlotByFlag: parsed.highSlotByFlag, estimate: est,
              input: {shipTypeId: parsed.shipTypeId, tally: parsed.tally, cargoItemIds: parsed.cargoItemIds, highSlotByFlag: parsed.highSlotByFlag, midSlotByFlag: parsed.midSlotByFlag} }; };
          renderFitTabs('Test Pilot', 'Hecate', [await mk('2026-10-01T00:00:00Z'), await mk('2026-10-02T00:00:00Z')], parsed.idToName); }""", HECATE)
        pg.wait_for_timeout(300)
        P0, P1 = '#fitResults .subtab-panel[data-idx="0"]', '#fitResults .subtab-panel[data-idx="1"]'
        pg.click(f'{P0} button.cc-toggle[data-card="weak"]'); pg.wait_for_timeout(150)
        a = pg.evaluate(f"document.querySelector('{P0} button.cc-toggle[data-card=weak]').getAttribute('aria-expanded')")
        b1 = pg.evaluate(f"document.querySelector('{P1} button.cc-toggle[data-card=weak]').getAttribute('aria-expanded')")
        check(a == 'false' and b1 == 'true', f'{W}: Pilot loss 1 collapses Weaknesses, loss 2 keeps it open ({a}, {b1})')
        check(not errs, f'{W}: collapsible cards, no page errors {errs}')
        ctx.close()
    b.close()

LONG_FIT_NAME = 'Doctrine fit pasted from the corp wiki - Armor HAC v3.2 FINAL (do not change without asking the FC first)'
UNBROKEN = 'Doctrine_fit_without_any_spaces_' + 'X' * 70
GARBAGE = 'ThisIsAnUnrecognizedItemNameWithoutAnySpaces' + 'Q' * 76
def long_eft(fit_name):
    return f"""[Stratios Emergency Responder, {fit_name}]
Unit P-343554's Modified Omnidirectional Tracking Enhancer
Drone Damage Amplifier II
Damage Control II
{GARBAGE}

Medium Capacitor Booster II, Navy Cap Booster 400
10MN Afterburner II
Warp Scrambler II
Large Shield Extender II

Heavy Pulse Laser II, Imperial Navy Multifrequency M
Heavy Missile Launcher II, Legion Scourge Auto-Targeting Heavy Missile
Modulated Deep Core Miner II, Variegated Asteroid Mining Crystal Type A II

Medium Drone Durability Rig I


Mutated 'Excavator' Ice Harvesting Drone x1
Prototype 'Pluto' Ice Harvesting Drone x2
Medium Shield Maintenance Bot II x2
'Augmented' Hammerhead x2
Hammerhead II x5

Inherent Implants 'Squire' Capacitor Systems Operation EO-606
Agency 'Pyrolancea' DB9 Dose IV

Variegated Asteroid Mining Crystal Type C II x20
Navy Cap Booster 400 x40
"""
LONG_DSCAN = '\n'.join([
    "+\tStratios Emergency Responder\t3,225 m",
    "Some pilot's extremely long ship name that they typed in the fitting window\tMiasmos Quafe Ultramarine Edition\t12 km",
    "NoSpacesInThisShipNameAtAllJustOneVeryLongWordForTestingTheCards\tCapsule - Genolution 'Auroral' 197-variant\t-",
    "+\tVexor Navy Issue\t1.2 AU"])
OUT_OF_BOX = """(sel) => {
  const bad = [];
  const desc = (c, r) => Math.round(r.left - c.left) + '..' + Math.round(r.right - c.left) + ' of ' + Math.round(c.width);
  document.querySelectorAll(sel).forEach(col => {
    const c = col.getBoundingClientRect();
    col.querySelectorAll('*').forEach(e => {
      if(!e.offsetParent) return;
      if(e.closest('details.info-pop:not([open])')) return;   // v2026.10.14.49: a closed info panel isn't shown (INFO_PANELS checks it open)
      const r = e.getBoundingClientRect();
      if(r.width === 0 || r.height === 0) return;
      if(r.right > c.right + 1 || r.left < c.left - 1) bad.push((e.className || e.tagName).toString().slice(0, 40) + ' ' + desc(c, r));
    });
    // text can overflow its element without growing the element's box (one long word): check the text itself
    const w = document.createTreeWalker(col, NodeFilter.SHOW_TEXT), rg = document.createRange();
    let t;
    while((t = w.nextNode())){
      if(!t.textContent.trim() || !t.parentElement || !t.parentElement.offsetParent || t.parentElement.closest('details.info-pop:not([open])')) continue;
      rg.selectNodeContents(t);
      for(const r of rg.getClientRects()){
        if(r.width > 0 && (r.right > c.right + 1 || r.left < c.left - 1)){ bad.push('text "' + t.textContent.trim().slice(0, 40) + '" ' + desc(c, r)); break; }
      }
    }
  });
  return bad.slice(0, 6);
}"""
# v2026.10.14.49: every card's info panel, opened one at a time: on screen, and on a wide layout inside its card's
# column (the Weaknesses / Mode panel in the narrow left column used to open off the screen's left edge).
INFO_PANELS = """async (W) => {
  const bad = [], seen = [];
  for(const d of document.querySelectorAll('#fitAnalyzerResults details.info-pop')){
    if(!d.offsetParent) continue;
    d.open = true; await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
    const body = d.querySelector('.info-body');
    body.scrollIntoView({block: 'nearest'}); await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
    // v2026.10.14.52 (the owner: the Matchup's panel was cut off by the board's edge): every corner of the panel must be
    // the panel itself on screen, not something drawn over it or a clipped edge
    const b = body.getBoundingClientRect();
    const hidden = [[b.left + 8, b.top + 8], [b.right - 8, b.top + 8], [b.left + 8, b.bottom - 8], [b.right - 8, b.bottom - 8]]
      .filter(([x, y]) => { const e = document.elementFromPoint(x, y); return !(e && body.contains(e)); });
    if(hidden.length) bad.push(`${d.dataset.info}: ${hidden.length} corner(s) not visible (clipped or covered)`);
    const r = body.getBoundingClientRect(), col = d.closest('.fit-layout > div');
    const c = col ? col.getBoundingClientRect() : {left: 0, right: W};
    seen.push(d.dataset.info);
    if(r.left < -1 || r.right > W + 1 || r.width < 200) bad.push(`${d.dataset.info}: ${Math.round(r.left)}..${Math.round(r.right)} of the ${W} px window`);
    else if(W >= 600 && (r.left < c.left - 1 || r.right > c.right + 1)) bad.push(`${d.dataset.info}: ${Math.round(r.left)}..${Math.round(r.right)}, column ${Math.round(c.left)}..${Math.round(c.right)}`);
    d.open = false;
  }
  return {bad, seen};
}"""
with sync_playwright() as p:
    b = p.chromium.launch(**({'executable_path': CHROMIUM} if CHROMIUM else {}))
    for W in (1440, 1100, 375):
        ctx = b.new_context(viewport={'width': W, 'height': 900}, is_mobile=W < 600, has_touch=W < 600)
        pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        route_all(pg)
        for label, name in (('long fit name', LONG_FIT_NAME), ('unbroken fit name', UNBROKEN)):
            for view in ('ring', 'list'):
                pg.goto('file://' + html); pg.click('#tabBtnFit'); pg.fill('#fitAnalyzerInput', long_eft(name)); pg.click('#fitAnalyzerBtn')
                pg.wait_for_function("() => document.querySelector('#fitAnalyzerResults .fit-layout')", timeout=30000); pg.wait_for_timeout(400)
                if pg.evaluate("document.querySelector('#fitAnalyzerResults .fit-view-btn.on').dataset.view") != view:
                    try: pg.click(f'#fitAnalyzerResults .fit-view-btn[data-view="{view}"]', timeout=5000); pg.wait_for_timeout(300)
                    except Exception as e: check(False, f'{W}: {label}: could not click the {view} switch (page zoomed out by an overflow? width {pg.evaluate("innerWidth")}px)'); continue
                ob = pg.evaluate(OUT_OF_BOX, '#fitAnalyzerResults .fl-beat, #fitAnalyzerResults .fl-fit, #fitAnalyzerResults .fl-stats, #tabFit section.panel')
                sw = pg.evaluate('document.documentElement.scrollWidth')
                check(not ob and sw <= W, f'{W}: {label}, {view} view: everything inside its column (page {sw}px) {ob}')
                if view == 'list':
                    ip = pg.evaluate(INFO_PANELS, W)
                    check(not ip['bad'] and {'weak', 'fit'} <= set(ip['seen']), f'{W}: {label}: every info panel opens on screen and inside its column ({", ".join(ip["seen"])}) {ip["bad"]}')
        tops = pg.evaluate("""() => [...document.querySelectorAll('#fitAnalyzerResults .ds-row')].map(r => { const p = r.querySelector('.ds-pips').getBoundingClientRect(), n = r.querySelector('.ms-name').getBoundingClientRect(); return [Math.round(p.right), Math.round(p.top - n.top)]; })""")
        check(len(tops) >= 4 and len({t[0] for t in tops}) == 1 and all(abs(t[1]) <= 4 for t in tops), f'{W}: drone squares right-aligned on the name line in every row {tops}')
        # Pilot Analyzer header with a 37-character pilot name (EVE's maximum)
        pg.click('#tabBtnPilot')
        pg.evaluate("""async (text) => { const parsed = await parseEftFit(text);
          const est = await estimateHpAndDps(parsed.shipTypeId, parsed.tally, parsed.cargoItemIds, parsed.highSlotByFlag, 'sharpshooter', parsed.midSlotByFlag);
          renderFitTabs('Abcdefghijklmnopqrstuvwxyz Abcdefghij', 'Stratios Emergency Responder', [{ km: {killmail_time: '2026-10-01T00:00:00Z'}, killmailId: 123456789, tally: parsed.tally, highSlotByFlag: parsed.highSlotByFlag, estimate: est,
            input: {shipTypeId: parsed.shipTypeId, tally: parsed.tally, cargoItemIds: parsed.cargoItemIds, highSlotByFlag: parsed.highSlotByFlag, midSlotByFlag: parsed.midSlotByFlag} }], parsed.idToName); }""", long_eft(LONG_FIT_NAME))
        pg.wait_for_timeout(400)
        ob = pg.evaluate(OUT_OF_BOX, '#tabPilot section.panel')
        check(not ob and pg.evaluate('document.documentElement.scrollWidth') <= W, f'{W}: Pilot Analyzer with a 37-character pilot name: everything inside the panel {ob}')
        # D-scan tab with long names
        pg.click('#tabBtnDscan'); pg.fill('#dscanInput', LONG_DSCAN); pg.click('#analyzeBtn')
        pg.wait_for_function("() => document.querySelector('#resultsGrid') && document.querySelector('#resultsGrid').children.length >= 2", timeout=30000); pg.wait_for_timeout(400)
        ob = pg.evaluate(OUT_OF_BOX, '#resultsGrid > *')
        check(not ob and pg.evaluate('document.documentElement.scrollWidth') <= W, f'{W}: D-scan contacts with long names: everything inside its card {ob}')
        check(not errs, f'{W}: long strings, no page errors {errs}')
        ctx.close()
    b.close()

with sync_playwright() as p:
    b = p.chromium.launch(**({'executable_path': CHROMIUM} if CHROMIUM else {}))
    for W in (1440, 375):
        ctx = b.new_context(viewport={'width': W, 'height': 900}, is_mobile=W < 600, has_touch=W < 600)
        pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        route_all(pg)
        pg.goto('file://' + html); pg.click('#tabBtnFit'); pg.fill('#fitAnalyzerInput', long_eft('bay test')); pg.click('#fitAnalyzerBtn')
        pg.wait_for_function("() => document.querySelector('#fitAnalyzerResults .fit-layout')", timeout=30000); pg.wait_for_timeout(400)
        R = '#fitAnalyzerResults .fl-fit'
        bays = lambda: pg.evaluate(f"() => Object.fromEntries([...document.querySelectorAll('{R} button.bay-toggle')].map(b => [b.dataset.card, b.getAttribute('aria-expanded') === 'true']))")
        st = bays()
        want = {'bay:drone': True, 'bay:cargo': False} # v.20: every bay but the drone bay starts closed
        check(st == want, f'{W}: bays open by default as specified {st}')
        if not st.get('bay:cargo'): pg.click(f'{R} button.bay-toggle[data-card="bay:cargo"]'); pg.wait_for_timeout(150)
        for k in ('bay:drone', 'bay:cargo'):
            pg.click(f'{R} button.bay-toggle[data-card="{k}"]'); pg.wait_for_timeout(150)
        sums = pg.evaluate(f"() => Object.fromEntries([...document.querySelectorAll('{R} button.bay-toggle.cc-row')].map(b => [b.dataset.card, b.querySelector('.cc-sum').textContent]))")
        check(sums.get('bay:drone', '').startswith('5 / 5 in space · 5 types · 12 items') and sums.get('bay:cargo') == '2 types · 60 items', f'{W}: collapsed bay summaries {sums}')
        check(pg.locator(R + ' button.ds-pip').count() == 0, f'{W}: collapsed drone bay hides its squares')
        pg.locator(R + ' button.ms-state[data-from="active"]').first.click()
        pg.wait_for_function("() => document.querySelector('#fitAnalyzerResults button.ms-reset.is-custom') && !document.querySelector('#fitAnalyzerResults .fit-card-busy')", timeout=30000); pg.wait_for_timeout(300)
        check(bays() == {'bay:drone': False, 'bay:cargo': False}, f'{W}: bays stay collapsed through a module-state change {bays()}')
        pg.click(f'{R} button.bay-toggle[data-card="bay:drone"]'); pg.wait_for_timeout(150)
        check(pg.locator(R + ' button.ds-pip').count() > 0 and pg.evaluate("document.activeElement && document.activeElement.dataset.card") == 'bay:drone', f'{W}: drone bay reopens with its squares, focus kept')
        sw = pg.evaluate('document.documentElement.scrollWidth'); check(sw <= W, f'{W}: bays, no sideways scroll ({sw})')
        check(not errs, f'{W}: bays, no page errors {errs}')
        ctx.close()
    b.close()

with sync_playwright() as p:
    b = p.chromium.launch(**({'executable_path': CHROMIUM} if CHROMIUM else {}))
    for W in (1440, 375):
        ctx = b.new_context(viewport={'width': W, 'height': 900}, is_mobile=W < 600, has_touch=W < 600)
        pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        route_all(pg)
        pg.goto('file://' + html); pg.click('#tabBtnFit'); pg.fill('#fitAnalyzerInput', HECATE); pg.click('#fitAnalyzerBtn')
        pg.wait_for_function("() => document.querySelector('#fitAnalyzerResults .fit-layout')", timeout=30000); pg.wait_for_timeout(400)
        F = '#fitAnalyzerResults .fl-fit'
        txt = pg.inner_text(F)
        check('Module states assumed' not in txt and not re.search(r'\bhide\b', txt) and 'show modules and states' not in txt, f'{W}: Fit card has no "Module states assumed" label and no hide / show link')
        tg = F + ' button.cc-toggle[data-card=fit]'
        check(pg.locator(tg).count() == 1 and pg.get_attribute(tg, 'aria-expanded') == 'true' and pg.locator(tg + ' .cc-chev').count() == 1, f'{W}: Fit card title is a toggle with the arrow, open by default in the Fit Analyzer')
        check(pg.locator(F + ' .fit-card-head .fit-view-switch').count() == 1, f'{W}: Ring / List switch sits in the Fit card header')
        check(pg.locator(F + ' .fit-view-controls button.ms-reset[disabled]').count() == 1 and 'Reset to best case' not in pg.inner_text(F), f'{W}: a reset icon button sits next to Ring / List, disabled while everything is default')
        pg.locator(F + ' button.ms-state[data-from="active"]').first.click()
        pg.wait_for_function("() => document.querySelector('#fitAnalyzerResults button.ms-reset.is-custom') && !document.querySelector('#fitAnalyzerResults .fit-card-busy')", timeout=30000); pg.wait_for_timeout(300)
        check(pg.locator(F + ' .fit-view-controls button.ms-reset.is-custom:not([disabled])').count() == 1, f'{W}: the reset button next to Ring / List turns active after a state change')
        pg.click(tg); pg.wait_for_timeout(200)
        sm = pg.text_content(F + ' button.cc-row[data-card=fit] .cc-sum')
        fam = pg.evaluate(f"getComputedStyle(document.querySelector('{F} button.cc-row[data-card=fit] .cc-sum')).textTransform")
        check(sm == 'Hecate — mode test' and fam == 'uppercase' and pg.locator(F + ' button.ms-state').count() == 0, f'{W}: collapsed Fit card shows the fit name in the stat-label style "{sm}" ({fam})')
        pg.click(F + ' button.cc-toggle[data-card=fit]'); pg.wait_for_timeout(200)
        check(pg.locator(F + ' button.ms-state').count() > 0 and pg.locator(F + ' button.ms-reset.is-custom').count() == 1, f'{W}: Fit card reopens with the custom states kept')
        check(not errs, f'{W}: Fit card toggle, no page errors {errs}')
        ctx.close()
    b.close()
print('FAILURES:', len(bad))
