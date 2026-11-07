"""The Intel map: light-years in the hover, "center on me", your system made obvious (v2026.11.04.1, roadmap/map-ly-hover-plan.md).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/intel_map_you_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner: "i'm just looking for the distance in LY (from the player's current system) to show up in the data seen on hover",
rounded up to 0.01 ("Round up to 0.01"); a center-on-me button with + − ⤢ ("crosshair is fine"; "Keep current zoom", "Center on me
after a jump"); "the user's pilot location is not obvious on the galaxy map" (a pin, a filled YOU label, a short beacon, an edge
arrow; mockup v4 approved as is, 2026-11-03). Runs intel_check.py's start (its made-up Chatlogs folder, ESI and system names; you in
1DQ1-A; real systems and gates, made-up pilots), then:
  * the table: INTEL_MAP.p3 decoded here (int24 LE, x for every system then y then z, units p3u = 0.0001 LY);
  * light-years: every system on the map, the page's text = the distance worked out here from the decoded table, rounded UP to
    0.01 with exact decimals; spot pairs from 1DQ1-A worked out from CCP's positions (SDE build 3665151, 9.46e15 m per LY):
    8WA-Z6 0.51 (a neighbour), E-VKJV 2.96 (another region; plain rounding says 2.95), JP4-AA 3.20 and FM-JK5 2.05 (plain
    rounding says 3.19 and 2.04), F-TE1T 7.00 (just under a 7.0 LY jump range; not on the map, worked out all the same);
  * the hover: "N.NN LY from 1DQ1-A" as its second line; none on your own system;
  * your system: a pin drawn after every ring (a fleet of 12 reported in your system, the hover on it: the pin's head white where
    the red ring and the cyan hover ring cross it), the security dot under its tip; YOU · 1DQ1-A on a white chip with 30+ reported
    systems around, no other name over the pin; the legend's first entry;
  * center on me: zoomed in and dragged away, the crosshair puts you in the middle (within 1 px) at the same zoom, one draw;
    ⤢ still the whole area; the "You" arrow on the edge only while you're out of view, pointing at you (within 5°), a press
    centers; a jump (a new Local line) at 2.25×: centered on the new system, still 2.25×;
  * the beacon: on the first draw and on a jump, over within 2 s, nothing left running (no animation frame asked for after it,
    its canvas clear), the map itself drawn at most twice meanwhile; none for a jump made while another tab was in front, none
    while the page is hidden, none at all with reduced motion;
  * your system unknown: no crosshair, no arrow;
  * a phone (390 px, touch): the four corner buttons 44 px, a press on a system shows its light-years;
  * no page errors.
v2026.11.04.1 is the first page that passes (v2026.11.02.4 has no positions, no crosshair, no pin).
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, 'intel_check.py'), encoding='utf-8').read()
_src = _src[:_src.index('    jumps = pg.evaluate("(names) => Object.fromEntries')]
_src = _src.replace("os.path.dirname(os.path.abspath(__file__))", repr(HERE), 1)
_ns = {'__file__': os.path.join(HERE, 'intel_check.py'), '__name__': 'intel_check_prefix'}
_tail = r'''
    import math, re as _re
    from decimal import Decimal, ROUND_CEILING
    HOME = SYSID['1DQ1-A']; D0 = bfs(HOME)
    tick(pg, 2000)
    # ---- the table, decoded here ----
    MP = json.loads(_re.search(r'^const INTEL_MAP = (.*);$', open(HTML, encoding='utf-8').read(), _re.M).group(1))
    raw = base64.b64decode(MP.get('p3', '')); P3 = [int.from_bytes(raw[i:i + 3], 'little', signed=True) for i in range(0, len(raw), 3)]
    n = len(ids); AT = {s: k for k, s in enumerate(ids)}
    check(MP.get('p3u') == 0.0001 and len(P3) == 3 * n and MP['systems'] == n, f'the table: positions in space for all {n} systems in units of 0.0001 LY ({len(P3)} values, p3u {MP.get("p3u")})')
    def ly(a, b):   # exact: integer units, then the square root to 0.0001 LY's 1/1000
        ka, kb = AT[a], AT[b]; d2 = sum((P3[ax * n + ka] - P3[ax * n + kb]) ** 2 for ax in range(3))
        return Decimal(d2).sqrt() * Decimal('0.0001')
    up = lambda d: str(d.quantize(Decimal('0.01'), rounding=ROUND_CEILING))
    # ---- every system on the map: the page's text = the distance worked out here, rounded up ----
    got = pg.evaluate("() => itm.vis.filter(i => i !== itm.home).map(i => [itGraphGet().ids[i], itMapLyText(itMapLy(i, itm.home))])")
    bad = [(SYSNAME[s], t, up(ly(s, HOME))) for s, t in got if t != up(ly(s, HOME))]
    check(len(got) > 50 and not bad, f'light-years from 1DQ1-A for every system on the map ({len(got)}), rounded up to 0.01: the page = worked out here {bad[:4]}')
    SPOT = {'8WA-Z6': '0.51', 'E-VKJV': '2.96', 'JP4-AA': '3.20', 'FM-JK5': '2.05', 30004757: '7.00'}   # SDE 3665151, worked out with 9.46e15 m per LY
    sp = pg.evaluate("(ids) => ids.map(id => { const i = itGraphGet().at.get(id); return itMapLyText(itMapLy(i, itGraphGet().at.get(%d))); })" % HOME, [SYSID[k] if isinstance(k, str) else k for k in SPOT])
    check(sp == list(SPOT.values()), f'spot pairs from CCP\'s positions: 8WA-Z6 0.51, E-VKJV 2.96, JP4-AA 3.20, FM-JK5 2.05, F-TE1T 7.00 (the page: {sp})')
    # ---- the hover ----
    POS = "(id) => { const i = itGraphGet().at.get(id), r = itm.cv.getBoundingClientRect(); return [r.left + itm.Q[2 * i], r.top + itm.Q[2 * i + 1]]; }"
    pg.evaluate("() => document.querySelector('.it-map-box').scrollIntoView({block: 'center'})"); tick(pg, 300)
    x, y = pg.evaluate(POS, SYSID['E-VKJV']); pg.mouse.move(x, y); tick(pg, 250)
    tl = pg.evaluate("() => itm.tip.innerText.split('\\n')")
    check(len(tl) > 2 and tl[1].strip() == '2.96 LY from 1DQ1-A', f'hovering E-VKJV: "2.96 LY from 1DQ1-A" as the second line {tl[:3]}')
    x, y = pg.evaluate(POS, HOME); pg.mouse.move(x, y); tick(pg, 250)
    th = pg.evaluate("() => [itm.hover === itm.home, itm.tip.hidden, itm.tip.innerText]")
    check(th[0] and not th[1] and 'LY' not in th[2], f'hovering your own system: no light-years {th}')
    pg.mouse.move(5, 5); tick(pg, 200)
    # ---- your system: the pin over every ring ----
    W(pg, F_INTEL, line(time.time(), 'Scout Alt', f'1DQ1-A {M.PILOTS[M.pick(98000003)][0]} +11'))
    tick(pg, 3500)
    x, y = pg.evaluate(POS, HOME); pg.mouse.move(x, y); tick(pg, 250)
    PX = """([dx, dy]) => { const c = itm.cv.getContext('2d'), dpr = window.devicePixelRatio || 1, i = itm.home, d = c.getImageData(Math.round((itm.Q[2 * i] + dx) * dpr), Math.round((itm.Q[2 * i + 1] + dy) * dpr), 1, 1).data; return [d[0], d[1], d[2], d[3]]; }"""
    hr = pg.evaluate("() => [itm.rep.get(itm.home) && itm.rep.get(itm.home).n, itm.hover === itm.home]")
    head = [pg.evaluate(PX, p) for p in ([0, -16], [4, -21], [-4, -17])]
    white = lambda c: min(c[:3]) > 225 and c[3] > 240
    dark = [pg.evaluate(PX, p) for p in ([-8, -19], [8, -19], [0, -19])]   # its dark outline over the cyan hover ring (21 px out), its hole
    check(hr == [12, True] and all(white(c) for c in head) and all(max(c[:3]) < 50 and c[3] > 240 for c in dark),
          f'a fleet of 12 in your system and the hover on it: the pin\'s head white where the red ring and the cyan hover ring cross it, its dark outline and hole over them {hr} {head} {dark}')
    dot = pg.evaluate(PX, [0, 3])
    check(dot[3] > 200 and abs(dot[0] - 0x8f) < 30 and abs(dot[1] - 0x2f) < 30 and abs(dot[2] - 0x69) < 30, f'your system\'s security dot (1DQ1-A, null-sec) under the pin\'s tip {dot}')
    pg.mouse.move(5, 5); tick(pg, 200)
    # 30+ reported systems around you: the YOU chip placed, white, nothing over the pin
    near = sorted((s for s, v in D0.items() if 1 <= v <= 9), key=lambda s: (D0[s], s))[:33]
    T0 = time.time()
    HOST = [v[0] for v in M.PILOTS.values() if v[1] in (98000003, 98000004, 98000005, 98000007, 98000008) and not set(v[0].split()) & set(ONE_WORD)]   # one each (a pilot reported again elsewhere moves); none sharing a word with intel_check's one-word pilots
    W(pg, F_INTEL, ''.join(line(T0 + k * 0.01, 'Gate Watcher', f'{SYSNAME[s]} {HOST[k + 1]}') for k, s in enumerate(near[:len(HOST) - 1])))
    tick(pg, 4500)
    lab = pg.evaluate("""() => { const i = itm.home, hx = itm.Q[2 * i], hy = itm.Q[2 * i + 1], pin = [hx - 9, hy - 29, hx + 9, hy], me = itm.labels.find(l => l[0] === i);
      const over = itm.labels.filter(l => l[0] !== i && l[1] < pin[2] && l[3] > pin[0] && l[2] < pin[3] && l[4] > pin[1]).length;
      const c = itm.cv.getContext('2d'), dpr = window.devicePixelRatio || 1, px = me ? c.getImageData(Math.round((me[1] + 1.5) * dpr), Math.round((me[2] + 1.5) * dpr), 1, 1).data : [];
      return [itm.rep.size, !!me, me && me[1] >= 0 && me[3] <= itm.W && me[2] >= 0 && me[4] <= itm.H, over, [...px]]; }""")
    check(lab[0] >= 30 and lab[1] and lab[2] and lab[3] == 0 and white(lab[4]), f'{lab[0]} reported systems around you: the YOU chip placed inside the map on white, no other name over the pin {lab}')
    leg = pg.evaluate("() => { const s = document.querySelector('.it-map-leg > span'); return [!!s.querySelector('svg.pin'), s.textContent.trim()]; }")
    check(leg == [True, 'you'], f'the legend\'s first entry: the pin, "you" {leg}')
    # ---- center on me ----
    k1 = pg.evaluate('itm.view.k'); pg.click('[data-im-z="in"]'); pg.click('[data-im-z="in"]'); tick(pg, 150)
    x, y = pg.evaluate(POS, HOME); pg.mouse.move(x + 30, y + 40); pg.mouse.down(); pg.mouse.move(x + 150, y + 110, steps=6); pg.mouse.up(); tick(pg, 200)
    before = pg.evaluate("() => [itm.view.k, itm.Q[2 * itm.home] - itm.W / 2, itm.Q[2 * itm.home + 1] - itm.H / 2, itm.draws]")
    pg.click('[data-im-z="me"]'); tick(pg, 200)
    after = pg.evaluate("() => [itm.view.k, itm.Q[2 * itm.home] - itm.W / 2, itm.Q[2 * itm.home + 1] - itm.H / 2, itm.draws]")
    check(abs(before[1]) > 50 and abs(after[1]) <= 1 and abs(after[2]) <= 1 and after[0] == before[0] and before[0] > k1 * 2 and after[3] == before[3] + 1,
          f'zoomed in ({before[0]:.2f}×) and dragged away, the crosshair: you in the middle (off by {after[1]:.1f}, {after[2]:.1f} px) at the same zoom, one draw {before} -> {after}')
    # the "You" arrow: only while you're out of view; points at you; a press centers
    ar0 = pg.evaluate('itm.you.hidden')
    pg.mouse.move(400, 300); x, y = pg.evaluate(POS, HOME)
    pg.mouse.move(x - 20, y - 20); pg.mouse.down(); pg.mouse.move(x - 20 + 700, y - 20 + 500, steps=10); pg.mouse.up(); tick(pg, 200)
    ar = pg.evaluate("""() => { const b = itm.you, r = b.getBoundingClientRect(), box = itm.box.getBoundingClientRect(), cx = itm.W / 2, cy = itm.H / 2, hx = itm.Q[2 * itm.home], hy = itm.Q[2 * itm.home + 1];
      const bx = r.left + r.width / 2 - box.left, by = r.top + r.height / 2 - box.top, a1 = Math.atan2(hy - cy, hx - cx), a2 = Math.atan2(by - cy, bx - cx);
      const m = /rotate\\(([-\\d.e]+)rad\\)/.exec(b.querySelector('svg').style.transform), a3 = m ? Number(m[1]) : NaN;
      const dd = (p, q) => Math.abs(Math.atan2(Math.sin(p - q), Math.cos(p - q))) * 180 / Math.PI;
      return [b.hidden, hx < 0 || hy < 0 || hx > itm.W || hy > itm.H, Math.round(dd(a1, a2) * 10) / 10, Math.round(dd(a1, a3) * 10) / 10, r.left >= box.left - 1 && r.right <= box.right + 1 && r.top >= box.top - 1 && r.bottom <= box.bottom + 1]; }""")
    check(ar0 and not ar[0] and ar[1] and ar[2] <= 5 and ar[3] <= 5 and ar[4], f'the "You" arrow: hidden while you\'re in view, shown once you\'re dragged out, inside the box, toward you (placed {ar[2]}°, pointing {ar[3]}° off) {ar}')
    pg.click('.it-map-you'); tick(pg, 200)
    ac = pg.evaluate("() => [itm.you.hidden, Math.abs(itm.Q[2 * itm.home] - itm.W / 2) <= 1 && Math.abs(itm.Q[2 * itm.home + 1] - itm.H / 2) <= 1]")
    check(ac == [True, True], f'pressing it centers on you, and it goes {ac}')
    pg.click('[data-im-z="fit"]'); tick(pg, 150)
    check(pg.evaluate("() => [itm.view.k, itm.view.tx, itm.view.ty]") == [1, 0, 0], '⤢ still shows the whole area')
    # ---- a jump at 2.25×, and the beacon ----
    pg.evaluate("""() => { window.__raf = 0; const r = window.requestAnimationFrame.bind(window); window.requestAnimationFrame = (f) => { window.__raf++; return r(f); }; }""")
    pg.click('[data-im-z="in"]'); pg.click('[data-im-z="in"]'); tick(pg, 150)
    j0 = pg.evaluate("() => [itm.beacons, itm.draws, itm.view.k]")
    W(pg, F_LOCAL_MAIN, line(time.time(), 'EVE System', 'Channel changed to Local : 8WA-Z6*'))
    seen = None
    for _ in range(40):
        tick(pg, 100); seen = pg.evaluate("() => [itSysName(itMySys()), itm.beacons, itm.beacon !== 0, itm.draws]")
        if seen[0] == '8WA-Z6' and seen[1] > j0[0]: break
    t_start = time.time(); dur = None
    while time.time() - t_start < 3:
        if pg.evaluate('itm.beacon') == 0: dur = time.time() - t_start; break
        tick(pg, 50)
    j1 = pg.evaluate("() => [itSysName(itMySys()), itm.view.k, Math.round((itm.Q[2 * itm.home] - itm.W / 2) * 10) / 10, Math.round((itm.Q[2 * itm.home + 1] - itm.H / 2) * 10) / 10, itm.beacons, itm.draws]")
    check(j1[0] == '8WA-Z6' and j1[1] == j0[2] and abs(j1[2]) <= 1 and abs(j1[3]) <= 1, f'a jump at {j0[2]:.2f}×: centered on the new system (8WA-Z6), the zoom kept {j1[:4]}')
    r0 = pg.evaluate('window.__raf'); tick(pg, 600); r1 = pg.evaluate('window.__raf')
    clear = pg.evaluate("() => { const c = itm.fx, d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let a = 0; for(let k = 3; k < d.length; k += 4) a += d[k]; return a; }")
    check(j1[4] == j0[0] + 1 and seen and seen[2] and dur is not None and dur < 2 and r1 - r0 <= 3 and clear == 0 and j1[5] - j0[1] <= 2,
          f'the beacon on the jump: played, over within 2 s ({dur and round(dur, 2)} s after seen running), nothing running after it ({r1 - r0} animation frames asked for in 0.6 s), its canvas clear ({clear}), the map drawn {j1[5] - j0[1]} times')
    # a jump while another tab is in front: no beacon when you come back later; a hidden page: none
    pg.click('#tabBtnPilot'); tick(pg, 200); b0 = pg.evaluate('itm.beacons')
    W(pg, F_LOCAL_MAIN, line(time.time(), 'EVE System', 'Channel changed to Local : 1DQ1-A*')); tick(pg, 6500)
    pg.click('#tabBtnIntel'); tick(pg, 1500)
    bt = pg.evaluate("() => [itSysName(itMySys()), itm.home === itGraphGet().at.get(itMySys()), itm.beacons]")
    check(bt[:2] == ['1DQ1-A', True] and bt[2] == b0, f'a jump made while the Pilot tab was in front: the map follows when you come back, no beacon then {bt} (beacons before: {b0})')
    pg.evaluate("() => { Object.defineProperty(document, 'hidden', {configurable: true, get: () => true}); document.dispatchEvent(new Event('visibilitychange')); }")
    b1 = pg.evaluate('itm.beacons'); W(pg, F_LOCAL_MAIN, line(time.time(), 'EVE System', 'Channel changed to Local : 8WA-Z6*')); tick(pg, 3000)
    pg.evaluate("() => { delete document.hidden; document.dispatchEvent(new Event('visibilitychange')); }"); tick(pg, 800)
    bh = pg.evaluate("() => [itm.beacons, itSysName(itMySys())]")
    check(bh == [b1, '8WA-Z6'], f'a jump while the page is hidden: no beacon (before {b1}, after {bh})')
    # ---- your system unknown ----
    pg.evaluate("() => { it.me.sys = 'Nowhere Known'; itMapRefresh(true); }"); tick(pg, 300)
    un = pg.evaluate("() => [document.querySelector('[data-im-z=\"me\"]').hidden, itm.you.hidden, itm.el.querySelector('.it-map-msg').hidden]")
    check(un == [True, True, False], f'your system unknown: no crosshair, no arrow, the map\'s message instead {un}')
    pg.evaluate("() => { it.me.sys = '8WA-Z6'; itMapRefresh(true); }"); tick(pg, 300)
    check(not errs, f'no page errors {errs[:3]}')
    # ---- reduced motion: no beacon ever ----
    old = {'channels': ['region.intel'], 'me': MAIN, 'range': 3, 'killRange': 10, 'forget': 15}
    ctx3 = b.new_context(bypass_csp=True, viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce'); ctx3.on('page', lambda q: q.on('pageerror', lambda e: errs.append(str(e))))
    ctx3.add_init_script(FS); route(ctx3); r = ctx3.new_page(); r.goto('file://' + HTML)
    r.evaluate("(s) => { localStorage.setItem('dscanSide', JSON.stringify(s)); }", SIDE)
    r.evaluate("(o) => localStorage.setItem('dscanIntel', JSON.stringify(o))", old); r.reload(); r.wait_for_timeout(400)
    r.click('#tabBtnIntel'); setup_logs(r); r.click('[data-it-act="folder"]'); r.wait_for_timeout(500); r.click('#intelSwLabel'); tick(r, 3500)
    rm0 = r.evaluate("() => [itm.draws > 0, itm.beacons]")
    W(r, F_LOCAL_MAIN, line(time.time(), 'EVE System', 'Channel changed to Local : 8WA-Z6*')); tick(r, 3500)
    rm1 = r.evaluate("() => [itSysName(itMySys()), itm.beacons]")
    check(rm0 == [True, 0] and rm1 == ['8WA-Z6', 0], f'reduced motion: no beacon on the first draw or on a jump {rm0} {rm1}')
    ctx3.close()
    # ---- a phone ----
    ctx2 = b.new_context(bypass_csp=True, viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True, device_scale_factor=2); ctx2.on('page', lambda q: q.on('pageerror', lambda e: errs.append(str(e))))
    ctx2.add_init_script(FS); route(ctx2); m = ctx2.new_page(); m.goto('file://' + HTML)
    m.evaluate("(s) => { localStorage.setItem('dscanSide', JSON.stringify(s)); }", SIDE)
    m.evaluate("(o) => localStorage.setItem('dscanIntel', JSON.stringify(o))", old); m.reload(); m.wait_for_timeout(400)
    m.click('#tabBtnIntel'); setup_logs(m); m.click('[data-it-act="folder"]'); m.wait_for_timeout(500); m.click('#intelSwLabel'); tick(m, 3000)
    m.click('[data-it-nv="map"]'); tick(m, 600)
    m.evaluate("() => document.querySelector('.it-map-box').scrollIntoView({block: 'center'})"); tick(m, 300)
    bs = m.evaluate("() => [...document.querySelectorAll('.it-map-zoom button')].map(b => { const r = b.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; })")
    x, y = m.evaluate("(id) => { const i = itGraphGet().at.get(id), r = itm.cv.getBoundingClientRect(); return [r.left + itm.Q[2 * i], r.top + itm.Q[2 * i + 1]]; }", SYSID['E-VKJV'])
    m.touchscreen.tap(x, y); tick(m, 400)
    pt = m.evaluate("() => [itm.tip.hidden, itm.tip.innerText.split('\\n')[1] || '']")
    m.evaluate("() => { itm.view.tx = -3000; itMapDraw(); }"); tick(m, 200)
    ab = m.evaluate("() => { const r = itm.you.getBoundingClientRect(); return [itm.you.hidden, Math.round(r.width), Math.round(r.height)]; }")
    check(len(bs) == 4 and all(w >= 44 and h >= 44 for w, h in bs) and not pt[0] and pt[1].strip() == '2.96 LY from 1DQ1-A' and not ab[0] and ab[1] >= 44 and ab[2] >= 44 and m.evaluate('document.documentElement.scrollWidth') <= 390,
          f'a phone: the four corner buttons {bs}, the "You" arrow {ab[1:]} at least 44 px; a press on E-VKJV shows its light-years {pt}; no sideways scroll')
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
'''
exec(compile(_src + _tail, 'intel_map_you_check.py', 'exec'), _ns)
print(f"FAILURES: {_ns['fails']}")
sys.exit(1 if _ns['fails'] else 0)
