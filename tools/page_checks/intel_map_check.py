"""The Intel map beside Near You, the Near You range setting and the range steppers (v2026.11.02.4, roadmap/intel-map-plan.md).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/intel_map_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner chose layout B ("lets go with B": the map beside Near You, the Feed below; a List | Map switch on a phone), the rings
("standing color with gang-size rings"), the reach ("the map's upper bound range should match the largest option for the feed's
upper bound range", from Near You's reach, following the Feed until set), a Near You range under the gear ("can't be less than
alert range, can't be greater than feed range") and one stepper for all four ranges ("Yes, all four"). Runs intel_check.py's start
(its made-up Chatlogs folder, ESI and system names; you in 1DQ1-A; real systems and gates, made-up pilots), then:
  * the table: INTEL_MAP aligned to INTEL_JUMPS (same fingerprint, every system), decoded;
  * layout B at 1440 px: the map left of Near You, both at the top, the Feed below;
  * the map holds exactly the systems within its reach by gate jumps (the Feed's 10), counted here independently;
  * made-up reports: a solo hostile, a small gang, a fleet, a neutral pair, a clear system: each one's ring in its standing's
    colour and its gang's size (pixels read off the canvas), the clear one without a ring;
  * a Near You row hovered: its system's route drawn (shortest by gates, as long as its jumps); pressed: kept, "Route shown" on its
    rows in Near You and the Feed; pressed again: gone; "Hide all routes";
  * a system hovered on the map: the tooltip (name, jumps, route) and its rows lit; pressed: kept; a drag moves the map and keeps
    nothing; the wheel zooms it and the page doesn't scroll; a system's name in a row filters the Feed and keeps no route;
  * drawn only on a change: nothing for 12 s with nothing new; a new report: drawn; the Pilot tab in front: not drawn, back: drawn;
  * the settings: Feed, Near You, Alert as steppers in that order; Near You's − greys out at the alert range and its + at the
    Feed's range, each saying why; the alert range raised past Near You pulls it along; typed numbers snap; a held button keeps
    stepping; Enter on a focused button steps; the values kept; Esc closes and the card follows (Near You's line, a report 9 jumps
    out shown once Near You reaches it);
  * the map's Jumps shown: follows the Feed until set (the Feed to 15: the map 15), set by hand it stays; from Near You's reach up
    to 30 (the Feed's largest), greyed with the reason at both ends;
  * a phone (390 px, touch): List | Map in Near You, List first and the map not drawn; Map: the map, no list, you and every report
    named inside the box (a narrow map first cut names off at its right edge); one finger over the
    map scrolls the page, two fingers zoom the map and don't; 44 px stepper buttons; no sideways scroll;
  * a saved setting from before (no Near You range, no map reach) loads with the defaults; nonsense values are ignored; with an
    alert range of 10 and the Feed at 10, Near You's default (alert + 5) is held at 10 and says so;
  * no page errors.
v2026.11.02.3 fails (no map, no table, no steppers).
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, 'intel_check.py'), encoding='utf-8').read()
_src = _src[:_src.index('    jumps = pg.evaluate("(names) => Object.fromEntries')]
_src = _src.replace("os.path.dirname(os.path.abspath(__file__))", repr(HERE), 1)
_ns = {'__file__': os.path.join(HERE, 'intel_check.py'), '__name__': 'intel_check_prefix'}
_tail = r'''
    import math
    P1, P2, P3 = M.PILOTS[M.pick(98000003)][0], M.PILOTS[M.pick(98000003, 1)][0], M.PILOTS[M.pick(98000004)][0]
    HOME = SYSID['1DQ1-A']; D0 = bfs(HOME)
    def at(n): return sorted(k for k, v in D0.items() if v == n and SYSNAME[k].startswith('N'))   # made-up names: no report on them yet
    PN = M.PILOTS[M.pick(98000005)][0]   # a corporation not in the standings: neutral
    tick(pg, 2000)
    # ---- the table ----
    tab = pg.evaluate("() => { const T = itMapTable(); return T && [T.n, INTEL_MAP.jumps === INTEL_JUMPS.md5, INTEL_MAP.systems === INTEL_JUMPS.systems, T.regions.length > 50, T.xs.length]; }")
    check(tab == [len(ids), True, True, True, len(ids)], f'the map table: aligned to the jump table (same fingerprint, {len(ids)} systems) and decoded {tab}')
    # ---- layout B ----
    lay = pg.evaluate("""() => { const r = (s) => { const e = document.querySelector(s); if(!e) return null; const b = e.getBoundingClientRect(); return [Math.round(b.left), Math.round(b.top), Math.round(b.right), Math.round(b.bottom)]; };
      return [r('#intelPanel .it-mapcol'), r('#intelPanel .it-nearcol'), r('#intelPanel .it-feedcol'), !!document.querySelector('#itMapSlot .it-map canvas')]; }""")
    m_, n_, f_ = lay[0], lay[1], lay[2]
    check(m_ and n_ and f_ and lay[3] and m_[2] <= n_[0] and abs(m_[1] - n_[1]) < 4 and f_[1] >= max(m_[3], n_[3]) - 2, f'layout B at 1440 px: the map left of Near You at the top, the Feed below {lay}')
    # ---- the systems in reach ----
    want = sorted(k for k, v in D0.items() if v <= 10)
    got = pg.evaluate("() => [itMapReach(), itm.vis.map(i => itGraphGet().ids[i]).sort((a, b) => a - b)]")
    check(got[0] == 10 and got[1] == want, f'the map: the {len(want)} systems within 10 gate jumps (the Feed\'s range), no more, no less ({got[0]}, {len(got[1])})')
    # ---- made-up reports: rings ----
    CAND = [k for n in range(3, 8) for k in at(n)]
    SA, SB, SC, SD, SE, S9 = [SYSNAME[k] for k in CAND[:5]] + [SYSNAME[at(9)[0]]]
    REP = [(SA, f'{SA} {P1}'), (SB, f'{SB} {P1} +5'), (SC, f'{SC} {P2} +13'), (SD, f'{SD} {PN} +1'), (SE, f'{SE} clr'), (S9, f'{S9} {P1}')]
    for _, txt in REP: W(pg, F_INTEL, line(time.time(), 'Scout Alt', txt))
    tick(pg, 4000)
    rep = pg.evaluate("() => Object.fromEntries([...itm.rep].map(([i, r]) => [itSysName(itGraphGet().ids[i]), [r.side, r.n]]))")
    exp = {SA: ['hostile', 1], SB: ['hostile', 6], SC: ['hostile', 14], SD: ['neutral', 2], SE: ['clear', 0], S9: ['hostile', 1]}
    check(all(rep.get(k) == v for k, v in exp.items()), f'the reports on the map: standing and pilots {[(k, rep.get(k)) for k in exp]}')
    # the ring's radius: along 4 diagonals (the canvas's own pixels, transparent where nothing is drawn) from the system's dot, where the ring's colour is strongest (its glow fades either side)
    RING = """(name) => { const g = itGraphGet(), i = g.at.get(it.names.byLower.get(name.toLowerCase())), x = itm.Q[2 * i], y = itm.Q[2 * i + 1], c = itm.cv.getContext('2d'), dpr = window.devicePixelRatio || 1;
      return [1, 3, 5, 7, 0, 2, 4, 6].map(k => { const a = k * Math.PI / 4; let best = [0, 0, 0], bestR = 0, bestG = 0, gR = 0, maxA = 0;
        for(let r = 5; r <= 24; r += 0.5){ const d = c.getImageData(Math.round((x + r * Math.cos(a)) * dpr), Math.round((y + r * Math.sin(a)) * dpr), 1, 1).data;
          const w = d[3] / 255, red = (d[0] - (d[1] + d[2]) / 2) * w, grey = (Math.min(d[0], d[1], d[2]) - (Math.max(d[0], d[1], d[2]) - Math.min(d[0], d[1], d[2]))) * w;   // the canvas is see-through: weigh by alpha
          if(red > best[0]){ best[0] = red; bestR = r; } if(grey > bestG){ bestG = grey; gR = r; } if(r >= 6 && r <= 18) maxA = Math.max(maxA, d[3]); }
        return [bestR, Math.round(best[0]), gR, Math.round(bestG), maxA]; }); }"""
    def ring(name):
        rays = pg.evaluate(RING, name); drawn = sum(1 for r in rays if r[4] > 120)   # rays crossing anything solid 6-18 px out (a gate line or a label may cross 1-3)
        rays4 = rays[:4]
        med = lambda v: sorted(v)[len(v) // 2]
        return {'red': med([r[0] for r in rays4]) if med([r[1] for r in rays4]) > 60 else 0, 'grey': med([r[2] for r in rays4]) if med([r[3] for r in rays4]) > 100 else 0, 'solid': drawn, 'rays': rays4}
    rT, rD, rK, rM, rC = ring(SA), ring(SB), ring(SC), ring(SD), ring(SE)
    near = lambda v, w: abs(v - w) <= 1.5
    check(near(rT['red'], 7), f'a solo hostile: a red ring of the smallest size (7 px) {rT}')
    check(near(rD['red'], 11), f'a small gang (2–10): a red ring of the middle size (11 px) {rD}')
    check(near(rK['red'], 16), f'a fleet (11+): the largest red ring (16 px) {rK}')
    check(rM['red'] == 0 and near(rM['grey'], 11), f'a neutral pair: a grey ring of the middle size, not red {rM}')
    check(rC['red'] == 0 and rC['grey'] == 0 and rC['solid'] <= 3 and rT['solid'] >= 7, f'a clear report: no ring of any colour (solid on {rC["solid"]} of 8 rays; a ring: {rT["solid"]}) {rC}')
    # ---- a Near You row: hover, press ----
    pg.mouse.move(5, 5); tick(pg, 200); d0 = pg.evaluate('() => itm.draws')
    pg.hover('#itNearList .it-nb[data-it-sys="%d"] .age' % SYSID[SB]); tick(pg, 200)
    hv = pg.evaluate("() => [itm.rowHover >= 0 ? itSysName(itGraphGet().ids[itm.rowHover]) : '', itm.draws, itMapRoute(itm.rowHover).length]")
    check(hv[0] == SB and hv[1] > d0 and hv[2] == D0[SYSID[SB]], f'a Near You row hovered: its system\'s route drawn, as long as its jumps ({D0[SYSID[SB]]}) {hv}')
    pg.click('#itNearList .it-nb[data-it-sys="%d"] .age' % SYSID[SB]); tick(pg, 300)
    pn = pg.evaluate("""(id) => [[...itm.pinned], [...document.querySelectorAll('#itNearList .it-nb')].filter(r => r.querySelector('.it-map-rtag')).map(r => Number(r.dataset.itSys)),
      [...document.querySelectorAll('#itFeedList .it-fd')].filter(r => r.querySelector('.it-map-rtag')).map(r => r.querySelector('[data-it-fsys]').dataset.itFsys), !document.querySelector('.it-map-clr').hidden]""", SYSID[SB])
    check(pn[0] == [SYSID[SB]] and pn[1] == [SYSID[SB]] and pn[2] and set(pn[2]) == {SB} and pn[3], f'pressed: the route kept, "Route shown" on its rows in Near You and the Feed, "Hide all routes" shown {pn}')
    pg.click('#itNearList .it-nb[data-it-sys="%d"] .age' % SYSID[SB]); tick(pg, 300)
    pn2 = pg.evaluate("() => [itm.pinned.size, document.querySelectorAll('.it-map-rtag').length]")
    check(pn2 == [0, 0], f'pressed again: gone {pn2}')
    # ---- the map itself: hover, press, drag, wheel ----
    POS = "(name) => { const i = itGraphGet().at.get(it.names.byLower.get(name.toLowerCase())), r = itm.cv.getBoundingClientRect(); return [r.left + itm.Q[2 * i], r.top + itm.Q[2 * i + 1]]; }"
    x, y = pg.evaluate(POS, SC); pg.mouse.move(x, y); tick(pg, 200)
    tp = pg.evaluate("() => [itm.tip.hidden, itm.tip.textContent, [...document.querySelectorAll('.it-map-lit')].map(r => r.className.split(' ')[0])]")
    check(not tp[0] and SC in tp[1] and f'{D0[SYSID[SC]]} jump' in tp[1] and 'route:' in tp[1] and 'it-nb' in tp[2], f'a system hovered on the map: the tooltip (name, jumps, route) and its rows lit {tp}')
    pg.mouse.click(x, y); tick(pg, 200)
    check(pg.evaluate("() => [...itm.pinned]") == [SYSID[SC]], 'pressed on the map: its route kept')
    pg.click('.it-map-clr'); tick(pg, 200)
    v0 = pg.evaluate("() => [itm.view.tx, itm.view.ty, itm.pinned.size]")
    pg.mouse.move(x, y); pg.mouse.down(); pg.mouse.move(x + 60, y + 30, steps=6); pg.mouse.up(); tick(pg, 200)
    v1 = pg.evaluate("() => [itm.view.tx, itm.view.ty, itm.pinned.size]")
    check(v0[2] == 0 and v1[2] == 0 and abs(v1[0] - v0[0] - 60) < 2 and abs(v1[1] - v0[1] - 30) < 2, f'"Hide all routes" cleared them; a drag moves the map and keeps nothing {v0} -> {v1}')
    pg.evaluate("() => window.scrollTo(0, 200)"); sy0 = pg.evaluate('scrollY'); k0 = pg.evaluate('itm.view.k')
    x, y = pg.evaluate(POS, '1DQ1-A'); pg.mouse.move(x, y); pg.mouse.wheel(0, -300); tick(pg, 200)
    check(pg.evaluate('itm.view.k') > k0 * 1.3 and pg.evaluate('scrollY') == sy0, f'the wheel over the map zooms it ({k0} -> {pg.evaluate("itm.view.k")}); the page doesn\'t scroll')
    pg.click('.it-map-zoom [data-im-z="fit"]'); tick(pg, 100)
    pg.click('#itNearList .it-nb[data-it-sys="%d"] [data-it-fsys]' % SYSID[SA]); tick(pg, 300)
    fq = pg.evaluate("() => [it.q, itm.pinned.size]")
    check(fq == [SA, 0], f'a system\'s name in a row filters the Feed, as before, and keeps no route {fq}')
    pg.click('#itNearList .it-nb[data-it-sys="%d"] [data-it-fsys]' % SYSID[SA]); tick(pg, 300)
    # ---- drawn only on a change ----
    pg.mouse.move(5, 5); tick(pg, 300); d1 = pg.evaluate('itm.draws'); tick(pg, 12000); d2 = pg.evaluate('itm.draws')
    W(pg, F_INTEL, line(time.time(), 'Scout Alt', f'N-8YET {P2}')); tick(pg, 3500); d3 = pg.evaluate('itm.draws')
    check(d2 == d1 and d3 > d2, f'drawn only on a change: {d2 - d1} draws in 12 s with nothing new, a new report drawn ({d2} -> {d3})')
    pg.click('#tabBtnPilot'); tick(pg, 300); d4 = pg.evaluate('itm.draws')
    W(pg, F_INTEL, line(time.time(), 'Scout Alt', f'E-VKJV {P2}')); tick(pg, 4000); d5 = pg.evaluate('itm.draws')
    pg.click('#tabBtnIntel'); tick(pg, 600); d6 = pg.evaluate("() => [itm.draws, [...itm.rep.keys()].map(i => itSysName(itGraphGet().ids[i])).includes('E-VKJV')]")
    check(d5 == d4 and d6[0] > d5 and d6[1], f'the Pilot tab in front: the map not drawn ({d4} -> {d5}); back on Intel: drawn with the new report {d6}')
    # ---- the settings: three steppers ----
    pg.click('[data-it-act="gear"]'); tick(pg, 300)
    ST = """() => [...document.querySelectorAll('.it-pop .rs[data-rs]')].map(g => { const [m, p] = g.querySelectorAll('.rs-b'); return [g.dataset.rs, g.querySelector('.rs-v').value, m.disabled, p.disabled, m.title, p.title, g.querySelector('.rs-n').textContent]; })"""
    s0 = pg.evaluate(ST)
    check([r[0] for r in s0] == ['killRange', 'nearRange', 'range'] and [r[1] for r in s0] == ['10', '8', '3'] and not pg.evaluate("() => document.querySelector('.it-pop select[data-it-set=\"range\"], .it-pop select[data-it-set=\"killRange\"]')"),
          f'the settings: Feed, Near You, Alert as steppers in that order (10, 8 = alert + 5, 3), no range lists left {[r[:2] for r in s0]}')
    NB = lambda k, d: f'.it-pop [data-rs="{k}"] .rs-b[data-rs-d="{d}"]'
    for _ in range(5): pg.click(NB('nearRange', -1))
    s1 = {r[0]: r for r in pg.evaluate(ST)}
    for _ in range(3): pg.click(NB('nearRange', 1))
    s2 = {r[0]: r for r in pg.evaluate(ST)}
    check(s1['nearRange'][1] == '3' and s1['nearRange'][2] and 'less than your alert range (3)' in s1['nearRange'][4], f'Near You down to the alert range: − greyed, saying why {s1["nearRange"]}')
    check(s2['nearRange'][1] == '6' and not s2['nearRange'][2] and not s2['nearRange'][3], f'and up again {s2["nearRange"][:4]}')
    pg.fill('.it-pop [data-rs="nearRange"] .rs-v', '25'); pg.keyboard.press('Enter'); tick(pg, 200)
    s3 = {r[0]: r for r in pg.evaluate(ST)}
    kept25 = pg.evaluate("() => JSON.parse(localStorage.getItem('dscanIntel')).nearRange")
    check(s3['nearRange'][1] == '10' and kept25 == 10 and s3['nearRange'][3] and "more than the Feed's kill range (10)" in s3['nearRange'][5], f'a typed 25 snaps to the Feed\'s range: 10 shown and kept ({kept25}), + greyed, saying why {s3["nearRange"]}')
    for _ in range(4): pg.click(NB('range', 1))
    s4 = {r[0]: r for r in pg.evaluate(ST)}
    check(s4['range'][1] == '10' and s4['range'][3] and s4['nearRange'][1] == '10' and s4['killRange'][1] == '10' and s4['killRange'][2], f'the alert range to its largest (10): Near You held at 10, the Feed can\'t go below it {[s4[k][:4] for k in s4]}')
    for _ in range(4): pg.click(NB('range', -1))
    pg.focus(NB('killRange', 1)); pg.keyboard.press('Enter'); tick(pg, 200)
    s5 = {r[0]: r for r in pg.evaluate(ST)}
    btn = pg.query_selector(NB('nearRange', 1)); bb = btn.bounding_box(); pg.mouse.move(bb['x'] + 5, bb['y'] + 5); pg.mouse.down(); tick(pg, 1400); pg.mouse.up()
    s6 = {r[0]: r for r in pg.evaluate(ST)}
    check(s5['range'][1] == '3' and s5['killRange'][1] == '15' and int(s6['nearRange'][1]) >= 14, f'Enter on a focused + steps (the Feed 10 -> 15); a held + keeps stepping (Near You {s5["nearRange"][1]} -> {s6["nearRange"][1]})')
    pg.fill('.it-pop [data-rs="nearRange"] .rs-v', '9'); pg.keyboard.press('Enter'); tick(pg, 200)
    sv = pg.evaluate("() => JSON.parse(localStorage.getItem('dscanIntel'))")
    check(sv['nearRange'] == 9 and sv['killRange'] == 15 and sv['range'] == 3 and sv['mapReach'] is None, f'the values kept ({sv["nearRange"]}, {sv["killRange"]}, {sv["range"]}, map {sv["mapReach"]})')
    pg.keyboard.press('Escape'); tick(pg, 500)
    after = pg.evaluate("() => [document.querySelector('.it-pop') === null, document.querySelector('[data-it-nearctx]').textContent, [...document.querySelectorAll('#itNearList .it-nb')].map(r => Number(r.dataset.itSys))]")
    check(after[0] and 'within 9 jumps' in after[1] and SYSID[S9] in after[2], f'Esc closes them and the card follows: Near You within 9 jumps, the report 9 jumps out ({S9}) now in it {after[:2]}')
    # ---- the map's Jumps shown ----
    MR = """() => { const g = document.querySelector('.it-map [data-rs="mapReach"]'), [m, p] = g.querySelectorAll('.rs-b'); return [g.querySelector('.rs-v').value, g.querySelector('.rs-n').textContent, m.disabled, p.disabled, m.title, p.title, itm.vis.length]; }"""
    m1 = pg.evaluate(MR)
    check(m1[0] == '15' and 'follows the Feed (15)' in m1[1] and m1[6] == len([k for k, v in D0.items() if v <= 15]), f'the map follows the Feed (15) until set: {m1[:2]}, {m1[6]} systems')
    pg.fill('.it-map [data-rs="mapReach"] .rs-v', '40'); pg.keyboard.press('Enter'); tick(pg, 300)
    m2 = pg.evaluate(MR)
    pg.fill('.it-map [data-rs="mapReach"] .rs-v', '1'); pg.keyboard.press('Enter'); tick(pg, 300)
    m3 = pg.evaluate(MR)
    check(m2[0] == '30' and m2[3] and "largest kill range (30)" in m2[5] and m2[6] == len([k for k, v in D0.items() if v <= 30]), f'a typed 40 snaps to 30 (the Feed\'s largest), + greyed, saying why {m2[:4]} {m2[6]}')
    check(m3[0] == '9' and m3[2] and 'Near You (9)' in m3[4], f'a typed 1 snaps to Near You\'s 9: − greyed, saying why {m3[:3]} {m3[4]!r}')
    pg.fill('.it-map [data-rs="mapReach"] .rs-v', '20'); pg.keyboard.press('Enter'); tick(pg, 300)
    pg.evaluate("() => { it.set.killRange = 10; itWriteSet(); itRender(true); }"); tick(pg, 300)
    m4 = pg.evaluate(MR); sv2 = pg.evaluate("() => JSON.parse(localStorage.getItem('dscanIntel')).mapReach")
    check(m4[0] == '20' and 'yours' in m4[1] and sv2 == 20, f'set by hand (20), the map stays when the Feed goes back to 10 {m4[:2]} (kept: {sv2})')
    check(not errs, f'no page errors {errs[:3]}')
    # ---- a saved setting from before ----
    old = {'channels': ['region.intel'], 'me': MAIN, 'range': 3, 'killRange': 10, 'forget': 15}
    pg.evaluate("(o) => { localStorage.setItem('dscanIntel', JSON.stringify(o)); }", dict(old, nearRange='x', mapReach=99)); pg.reload(); pg.wait_for_timeout(400)
    ld = pg.evaluate("() => [it.set.nearRange, it.set.mapReach, itNearReach(), itMapReach(), it.set.nearView]")
    check(ld == [None, None, 8, 10, 'list'], f'a saved setting from before (nonsense values ignored): the defaults, Near You 8, the map 10 {ld}')
    pg.evaluate("(o) => { localStorage.setItem('dscanIntel', JSON.stringify(o)); }", dict(old, range=10)); pg.reload(); pg.wait_for_timeout(400)
    ld2 = pg.evaluate("() => [itNearReach(), RS.nearRange.note()]")
    check(ld2[0] == 10 and 'held at the Feed' in ld2[1], f'an alert range of 10 with the Feed at 10: Near You\'s default (alert + 5) held at 10, and it says so {ld2}')
    # ---- a phone ----
    ctx2 = b.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True, device_scale_factor=2); ctx2.on('page', lambda q: q.on('pageerror', lambda e: errs.append(str(e))))
    ctx2.add_init_script(FS); route(ctx2); m = ctx2.new_page(); m.goto('file://' + HTML)
    m.evaluate("(s) => { localStorage.setItem('dscanSide', JSON.stringify(s)); }", SIDE)
    m.evaluate("(o) => localStorage.setItem('dscanIntel', JSON.stringify(o))", old); m.reload(); m.wait_for_timeout(400)
    m.click('#tabBtnIntel'); setup_logs(m); m.click('[data-it-act="folder"]'); m.wait_for_timeout(500); m.click('#intelSwLabel'); tick(m, 3000)
    for _, txt in REP[:3]: W(m, F_INTEL, line(time.time(), 'Scout Alt', txt))
    tick(m, 4000)
    ph = m.evaluate("() => { const v = (s) => { const e = document.querySelector(s); return !!e && e.getClientRects().length > 0; }; return [v('.it-nv'), v('#itNearList'), v('.it-mapcol'), itm.draws, document.documentElement.scrollWidth]; }")
    check(ph[0] and ph[1] and not ph[2] and ph[3] == 0 and ph[4] <= 390, f'a phone: List | Map in Near You, the list first, the map not drawn; no sideways scroll {ph}')
    m.click('[data-it-nv="map"]'); tick(m, 600)
    ph2 = m.evaluate("() => { const v = (s) => { const e = document.querySelector(s); return !!e && e.getClientRects().length > 0; }; return [v('#itNearList'), v('.it-map canvas'), itm.draws > 0, itm.rep.size, document.documentElement.scrollWidth]; }")
    check(not ph2[0] and ph2[1] and ph2[2] and ph2[3] >= 3 and ph2[4] <= 390, f'Map: the map with its reports, no list, no sideways scroll {ph2}')
    lb = m.evaluate("() => [itm.W, itm.H, itm.labels.length, itm.labels.filter(([i, x0, y0, x1, y1]) => x0 < 0 || y0 < 0 || x1 > itm.W || y1 > itm.H).length, itm.rep.size]")
    check(lb[2] >= lb[4] + 1 and lb[3] == 0, f'a phone: you and every report named, every name inside the map (none cut off at its edge) {lb}')
    cdp = ctx2.new_cdp_session(m)
    m.evaluate("() => window.scrollTo(0, document.querySelector('.it-map-box').getBoundingClientRect().top + scrollY - 200)"); tick(m, 300)
    bb = m.query_selector('.it-map-box canvas').bounding_box(); cx, cy = bb['x'] + bb['width'] / 2, bb['y'] + 120
    T = lambda t, pts: cdp.send('Input.dispatchTouchEvent', {'type': t, 'touchPoints': [{'x': px, 'y': py, 'id': k} for k, (px, py) in enumerate(pts)]})
    y0, k0 = m.evaluate('scrollY'), m.evaluate('itm.view.k')
    T('touchStart', [(cx, cy)])
    for k in range(1, 11): T('touchMove', [(cx, cy - 25 * k)]); m.wait_for_timeout(16)
    T('touchEnd', []); tick(m, 500)
    y1, k1 = m.evaluate('scrollY'), m.evaluate('itm.view.k')
    m.evaluate("() => window.scrollTo(0, document.querySelector('.it-map-box').getBoundingClientRect().top + scrollY - 200)"); tick(m, 300)
    bb = m.query_selector('.it-map-box canvas').bounding_box(); cx, cy = bb['x'] + bb['width'] / 2, bb['y'] + 150; y2 = m.evaluate('scrollY')
    T('touchStart', [(cx - 30, cy), (cx + 30, cy)])
    for k in range(1, 11): T('touchMove', [(cx - 30 - 6 * k, cy), (cx + 30 + 6 * k, cy)]); m.wait_for_timeout(16)
    T('touchEnd', []); tick(m, 500)
    y3, k3 = m.evaluate('scrollY'), m.evaluate('itm.view.k')
    check(y1 > y0 + 100 and k1 == k0 and y3 == y2 and k3 > 1.5, f'touch: one finger over the map scrolls the page ({y0} -> {y1}), the map unmoved; two fingers zoom the map ({k3:.2f}) and don\'t scroll ({y2} -> {y3})')
    m.click('[data-it-act="gear"]'); tick(m, 400)
    bs = m.evaluate("() => [...document.querySelectorAll('.it-pop .rs-b, .it-map .rs-b')].map(b => { const r = b.getBoundingClientRect(); return Math.round(Math.min(r.width, r.height)); })")
    check(bs and min(bs) >= 44, f'a phone: the stepper buttons 44 px {sorted(set(bs))}')
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
'''
exec(compile(_src + _tail, 'intel_map_check.py', 'exec'), _ns)
print(f"FAILURES: {_ns['fails']}")
sys.exit(1 if _ns['fails'] else 0)
