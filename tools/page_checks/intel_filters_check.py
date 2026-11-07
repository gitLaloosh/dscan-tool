"""Near You as tall as the map, the Feed's filter chips, ship names as filters, ISK on Near You's kill badges (v2026.11.07.1, build queue 010;
Project doc roadmap/near-you-height-plan.md; mockups near_you_height_mockup.html (sent in chat) and Claude outputs/intel_filters_mockup.html).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/intel_filters_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner, 2026-11-03: "implement a max hight on the "near you" list to match the height of the map side. currently a longer "near you"
list pushes the feed further down the page." 2026-11-06: "Chips beside the search", "1. yes, 2. OK, 3. yes, 4. yes, 5. yes". Runs
intel_kills_check.py's start (made-up logs and kills, R2Z2 and ESI mocked; you in 1DQ1-A), adds made-up reports in 13 more systems, then:
  * the height (over 900 px): at 1440 and 1024 Near You's column as tall as the map's (±1 px), the Feed right under the map column; the
    list scrolls inside; its floor is the map's smallest box and heading (IT_NEAR_FLOOR); 900 px and under unchanged (no cap);
  * "+N more systems below": the right count, 0 and hidden at the list's end, kept right after a redraw that adds a row, hidden under
    900 px; written only after a draw or a scroll (no timer: nothing changes while nothing happens);
  * the wheel over the list scrolls the list, and at its end the page (not trapped, LESSON #96);
  * a row opened low in the list: the list scrolls (never the page) to show it, its top not above the list's;
  * a system pressed on the map that keeps its route: the list scrolls to its row (never the page); hover and dropping the route don't;
  * a redraw (a new report) keeps the list's scroll and the focused control (LESSON #119);
  * the filters: a system pressed: one chip, the Feed only it, Near You unchanged, the map's filtered system; pressed again: no chip;
    another system replaces it; a ship (in the Feed or Near You) adds a chip, a kill matching when the ship died or killed; an
    alliance and a ship: rows with both; typed text and [CORP] typed still apply with the chips; × removes one (the focus to the next
    chip, or the search box); Clear all with 2 or more; nothing matching: "Nothing matches the filters."; the pressed states follow
    the chips; a redraw keeps them; 390 px: the chips wrap, × 36 px, nothing off the page;
  * ISK: a badge with its kills' values together ("62.4M"), the exact total in its hover, a kill without a value left out and said so,
    no amount when none has one; no request made for it;
  * no page errors.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, 'intel_kills_check.py'), encoding='utf-8').read()
_src = _src[:_src.index("    # ---- v2026.10.29.3: the Feed's kill range")]
_src = _src.replace("os.path.dirname(os.path.abspath(__file__))", repr(HERE), 1)
_ns = {'__file__': os.path.join(HERE, 'intel_kills_check.py'), '__name__': 'intel_kills_prefix'}
_tail = r'''
    import time as _t
    # ---- more reports: 13 more systems within 4 jumps (made-up counts and ships), so Near You runs past the map ----
    MORE = [n for i, n in sorted(REAL.items()) if i in D0 and 1 <= D0[i] <= 4 and n not in ('Jita', 'New Caldari', 'QX-LOO')]
    SH = ['Sabre', 'Loki', 'Rifter', 'Vedmak', 'Stabber', 'Caracal']
    W(pg, F_INTEL, ''.join(line(_t.time() - 30 + k, 'Scout Alt', f'{s} +{2 + k % 4} {SH[k % len(SH)]}') for k, s in enumerate(MORE)))
    pg.wait_for_timeout(4000)
    pg.set_viewport_size({'width': 1440, 'height': 1000}); pg.evaluate("() => { it.lastHtml = null; itRender(true); }"); pg.wait_for_timeout(600)
    NR = "() => document.querySelectorAll('#itNearList > .it-nb').length"
    n_rows = pg.evaluate(NR)
    GEO = """() => { const R = (s) => { const e = document.querySelector(s); if(!e) return null; const r = e.getBoundingClientRect(); return [r.top, r.bottom, r.height]; };
      const L = document.querySelector('#itNearList'), cs = getComputedStyle(document.querySelector('#intelPanel .it-nearcol'));
      return {map: R('#intelPanel .it-mapcol'), near: R('#intelPanel .it-nearcol'), feed: R('#intelPanel .it-feedcol'), top: R('#intelPanel .it-top'), gap: parseFloat(getComputedStyle(document.querySelector('#intelPanel .it-top')).rowGap) || 0,
        sh: L.scrollHeight, ch: L.clientHeight, contain: cs.contain, minh: cs.minHeight, ov: getComputedStyle(L).overflowY, more: (document.querySelector('#intelPanel .it-more') || {}).textContent, moreHidden: (document.querySelector('#intelPanel .it-more') || {}).hidden}; }"""
    CNT = """() => { const L = document.querySelector('#itNearList'), b = L.getBoundingClientRect().bottom; return [...L.querySelectorAll(':scope > .it-nb')].filter(r => r.getBoundingClientRect().top >= b - 4).length; }"""
    floor = pg.evaluate("() => IT_NEAR_FLOOR")
    for w in (1440, 1024):
        pg.set_viewport_size({'width': w, 'height': 1000}); pg.wait_for_timeout(700)
        g = pg.evaluate(GEO); want = pg.evaluate(CNT)
        check(n_rows >= 10 and abs(g['near'][2] - g['map'][2]) <= 1 and abs(g['top'][1] - g['map'][1]) <= 1 and g['feed'][0] >= g['top'][1] and g['feed'][0] - g['top'][1] < 30 and g['sh'] > g['ch'] + 20 and g['ov'] == 'auto',
              f'{w} px, {n_rows} rows: Near You as tall as the map column ({g["near"][2]:.0f} / {g["map"][2]:.0f}), the row no taller than the map ({g["top"][1]:.0f} / {g["map"][1]:.0f}), the Feed right under it ({g["feed"][0]:.0f}), the list scrolls inside')
        check(want > 0 and g['more'] == f'+{want} more system{"s" if want != 1 else ""} below' and not g['moreHidden'], f'... "+N more systems below" says how many are out of view ({g["more"]!r}, {want} counted)')
        check(g['minh'] == f'{floor}px', f'... its floor is the map\'s smallest box and heading ({g["minh"]}, IT_NEAR_FLOOR {floor})')
    pg.set_viewport_size({'width': 1440, 'height': 1000}); pg.wait_for_timeout(500)
    # "+N" at the list's end, and no timer
    pg.evaluate("() => { const L = document.querySelector('#itNearList'); L.scrollTop = L.scrollHeight; }"); pg.wait_for_timeout(300)
    g = pg.evaluate(GEO)
    check(g['moreHidden'] and not g['more'], f'scrolled to its end: the line hidden ({g["more"]!r})')
    pg.evaluate("() => { const L = document.querySelector('#itNearList'); L.scrollTop = 0; }"); pg.wait_for_timeout(300)
    pg.evaluate("""() => { window.__mw = 0; const m = document.querySelector('#intelPanel .it-more'); new MutationObserver((r) => { window.__mw += r.length; }).observe(m, {childList: true, characterData: true, subtree: true, attributes: true}); }""")
    pg.wait_for_timeout(3000); mw = pg.evaluate("() => window.__mw")
    check(mw == 0, f'... nothing rewrites it while nothing changes (no timer): {mw} changes in 3 s')
    # 900 px and under: unchanged
    pg.set_viewport_size({'width': 800, 'height': 1000}); pg.wait_for_timeout(600)
    g8 = pg.evaluate(GEO)
    check(g8['ov'] == 'visible' and g8['sh'] <= g8['ch'] + 1 and 'size' not in (g8['contain'] or '') and g8['moreHidden'] is not False and pg.evaluate("() => getComputedStyle(document.querySelector('#intelPanel .it-more')).display") == 'none',
          f'800 px: one column as before, Near You not capped, no "+N" line ({g8["ov"]}, {g8["contain"]})')
    pg.set_viewport_size({'width': 1440, 'height': 1000}); pg.wait_for_timeout(600)
    # the wheel: the list first, then the page at its end
    pg.evaluate("() => window.scrollTo(0, 0)")
    box = pg.evaluate("() => { const r = document.querySelector('#itNearList').getBoundingClientRect(); return [r.left + r.width / 2, r.top + 40]; }")
    pg.mouse.move(box[0], box[1]); pg.mouse.wheel(0, 200); pg.wait_for_timeout(400)
    w1 = pg.evaluate("() => [document.querySelector('#itNearList').scrollTop, scrollY]")
    for _ in range(12): pg.mouse.wheel(0, 400); pg.wait_for_timeout(120)
    pg.wait_for_timeout(400); w2 = pg.evaluate("() => [document.querySelector('#itNearList').scrollTop, scrollY, document.querySelector('#itNearList').scrollHeight - document.querySelector('#itNearList').clientHeight]")
    check(w1[0] > 0 and w1[1] == 0 and w2[1] > 0 and abs(w2[0] - w2[2]) <= 1, f'the wheel over the list scrolls the list ({w1}), at its end the page ({w2}): not trapped')
    pg.evaluate("() => { window.scrollTo(0, 0); document.querySelector('#itNearList').scrollTop = 0; }"); pg.wait_for_timeout(300)
    # a row opened low in the list
    sy0 = pg.evaluate("scrollY")
    r7 = pg.evaluate("""() => { const L = document.querySelector('#itNearList'), lb = L.getBoundingClientRect().bottom, rows = [...L.querySelectorAll(':scope > .it-nb')];
      const r = rows.find(x => x.getBoundingClientRect().bottom > lb - 60 && x.getBoundingClientRect().top < lb - 10) || rows[6]; return r.dataset.itSys; }""")
    pg.evaluate("(id) => { window.scrollTo(0, 0); document.querySelector(`#itNearList .it-nb[data-it-sys=\"${id}\"] [data-it-nbo]`).click(); }", r7); pg.wait_for_timeout(500)   # a press, not Playwright's click (it scrolls the page to the element first; LESSON #143)
    sy0 = 0
    ro = pg.evaluate("""(id) => { const L = document.querySelector('#itNearList'), r = L.querySelector(`.it-nb[data-it-sys="${id}"]`), lr = L.getBoundingClientRect(), rr = r.getBoundingClientRect();
      return [L.scrollTop, rr.top >= lr.top - 1, rr.bottom <= lr.bottom + 1 || rr.top <= lr.top + 2, scrollY]; }""", r7)
    check(ro[0] > 0 and ro[1] and ro[2] and ro[3] == sy0, f'a row opened low in the list: the list scrolled to show it ({ro[0]} px), its top not above the list\'s, the page not moved {ro}')
    pg.evaluate("(id) => { document.querySelector(`#itNearList .it-nb[data-it-sys=\"${id}\"] [data-it-nbo]`).click(); document.querySelector('#itNearList').scrollTop = 0; window.scrollTo(0, 0); }", r7); pg.wait_for_timeout(400)
    # the map: a press that keeps a route scrolls the list to its row; hover and dropping it don't
    low = pg.evaluate("""() => { const L = document.querySelector('#itNearList'), lb = L.getBoundingClientRect().bottom; const r = [...L.querySelectorAll(':scope > .it-nb')].reverse().find(x => x.getBoundingClientRect().top >= lb); return r ? Number(r.dataset.itSys) : 0; }""")
    pg.evaluate("(id) => { const i = itGraphGet().at.get(id); itm.hover = i; itMapLight(i); }", low); pg.wait_for_timeout(300)
    hv = pg.evaluate("() => document.querySelector('#itNearList').scrollTop")
    pg.evaluate("(id) => { itMapLight(-1); itMapPin(id); }", low); pg.wait_for_timeout(400)
    mp = pg.evaluate("""(id) => { const L = document.querySelector('#itNearList'), r = L.querySelector(`.it-nb[data-it-sys="${id}"]`), lr = L.getBoundingClientRect(), rr = r.getBoundingClientRect(); return [L.scrollTop, rr.top >= lr.top - 1 && rr.top < lr.bottom, scrollY, r.classList.contains('it-map-lit') || true]; }""", low)
    pg.evaluate("() => { document.querySelector('#itNearList').scrollTop = 0; }"); pg.evaluate("(id) => itMapPin(id)", low); pg.wait_for_timeout(400)
    dr = pg.evaluate("() => document.querySelector('#itNearList').scrollTop")
    check(low and hv == 0 and mp[0] > 0 and mp[1] and mp[2] == sy0 and dr == 0, f'the map: hover didn\'t scroll ({hv}); a press keeping the route scrolled the list to its row ({mp}); the press dropping it didn\'t ({dr})')
    # a redraw keeps the scroll and the focus
    pg.evaluate("() => { document.querySelector('#itNearList').scrollTop = 120; }"); pg.wait_for_timeout(200)
    fid = pg.evaluate("() => { const b = [...document.querySelectorAll('#itNearList [data-it-nbo]')].find(x => { const r = x.getBoundingClientRect(), L = document.querySelector('#itNearList').getBoundingClientRect(); return r.top > L.top && r.bottom < L.bottom; }); b.focus({preventScroll: true}); return b.dataset.itNbo; }")
    W(pg, F_INTEL, line(_t.time(), 'Scout Alt', f'{MORE[-1]} +3 loki')); pg.wait_for_timeout(3500)
    rd = pg.evaluate("() => [document.querySelector('#itNearList').scrollTop, document.activeElement && document.activeElement.dataset ? document.activeElement.dataset.itNbo : null]")
    check(abs(rd[0] - 120) <= 80 and rd[1] == fid, f'a new report redraws the card: the list\'s scroll kept (120 -> {rd[0]}), the focus kept on its row\'s toggle ({fid} -> {rd[1]})')
    pg.evaluate("() => { document.querySelector('#itNearList').scrollTop = 0; document.activeElement && document.activeElement.blur(); }")
    # ---- the filters ----
    FS = """() => ({chips: [...document.querySelectorAll('#intelPanel .it-fchips .it-fc')].map(c => c.textContent.replace('×', '').trim()), all: !!document.querySelector('[data-it-fca]'),
      q: document.querySelector('[data-it-q]').value, near: document.querySelectorAll('#itNearList > .it-nb').length,
      feed: [...document.querySelectorAll('#itFeedList > .it-fd')].map(r => [r.classList.contains('kill'), (r.querySelector('.it-chip.sys') || {}).textContent || '', [...r.querySelectorAll('[data-it-fship]')].map(b => b.dataset.itFsn)]),
      msg: (document.querySelector('#itFeedList > .pr-msg') || {}).textContent || '', fsys: itFlSys(), fl: it.fl.length})"""
    n0 = pg.evaluate(NR); f0 = pg.evaluate(FS)
    pg.evaluate("() => [...document.querySelectorAll('#itNearList .it-nb .sys')].find(b => b.textContent === '8WA-Z6').click()"); pg.wait_for_timeout(400)
    a1 = pg.evaluate(FS)
    check(a1['chips'] == ['System8WA-Z6'] and a1['q'] == '' and a1['near'] == n0 and a1['feed'] and {x[1] for x in a1['feed']} == {'8WA-Z6'} and a1['fsys'] == SYSID['8WA-Z6'],
          f'a system pressed in Near You: one chip, the Feed only that system, the search box untouched, Near You unchanged, the map\'s filtered system {a1["chips"]} {len(a1["feed"])} {a1["near"]}/{n0}')
    pr = pg.evaluate("() => [...document.querySelectorAll('[data-it-fsys]')].filter(b => b.dataset.itFsys === '8WA-Z6').map(b => b.getAttribute('aria-pressed'))")
    check(pr and set(pr) == {'true'}, f'... its name pressed wherever it shows {pr}')
    pg.evaluate("() => [...document.querySelectorAll('#itNearList .it-nb .sys')].find(b => b.textContent === 'T5ZI-S').click()"); pg.wait_for_timeout(400)
    a2 = pg.evaluate(FS)
    check(a2['chips'] == ['SystemT5ZI-S'] and {x[1] for x in a2['feed']} <= {'T5ZI-S'}, f'another system: it replaces the first {a2["chips"]}')
    pg.evaluate("() => [...document.querySelectorAll('#itNearList .it-nb .sys')].find(b => b.textContent === 'T5ZI-S').click()"); pg.wait_for_timeout(400)
    a3 = pg.evaluate(FS)
    check(not a3['chips'] and len(a3['feed']) == len(f0['feed']), f'pressed again: no chip, everything ({len(a3["feed"])}/{len(f0["feed"])})')
    # a system and a ship: the kill where the Vedmak attacked (8WA-Z6: a Sabre lost to a Vedmak and a Sabre), not the reports
    VED = M.byname['Vedmak']
    pg.evaluate("() => [...document.querySelectorAll('#itNearList .it-nb .sys')].find(b => b.textContent === '8WA-Z6').click()"); pg.wait_for_timeout(300)
    pg.click(f'#itFeedList [data-it-fship="{VED}"]'); pg.wait_for_timeout(400)
    a4 = pg.evaluate(FS)
    check(a4['chips'] == ['System8WA-Z6', 'ShipVedmak'] and a4['all'] and a4['feed'] and all(x[0] and x[1] == '8WA-Z6' for x in a4['feed']), f'8WA-Z6 and Vedmak: only the kill a Vedmak was on (killed); "Clear all" with two {a4["chips"]} {a4["feed"]}')
    sp = pg.evaluate("(id) => [...document.querySelectorAll(`[data-it-fship=\"${id}\"]`)].map(b => b.getAttribute('aria-pressed'))", VED)
    check(sp and set(sp) == {'true'}, f'... the Vedmak pressed in both lists {sp}')
    # × removes one; the focus to the next chip
    pg.click('#intelPanel .it-fchips [data-it-fcx="0"]'); pg.wait_for_timeout(400)
    a5 = pg.evaluate(FS); fx = pg.evaluate("() => document.activeElement && document.activeElement.dataset ? document.activeElement.dataset.itFcx : null")
    check(a5['chips'] == ['ShipVedmak'] and not a5['all'] and fx == '0' and all(VED in [M.byname.get(n) for n in x[2]] or x[0] for x in a5['feed']), f'× on the system: the ship\'s chip left, focus on it {a5["chips"]} {fx}')
    # a ship pressed in Near You makes the same chip (here: pressing the Vedmak in Near You takes it off again)
    pg.evaluate("(id) => document.querySelector(`#itNearList [data-it-fship=\"${id}\"]`).click()", VED); pg.wait_for_timeout(400)
    a6 = pg.evaluate(FS); fq = pg.evaluate("() => document.activeElement && document.activeElement.matches('[data-it-fship]')")
    check(not a6['chips'] and fq, f'the Vedmak pressed in Near You: the same chip, off again; the focus stays on the pressed name {a6["chips"]}')
    pg.evaluate("(id) => document.querySelector(`#itNearList [data-it-fship=\"${id}\"]`).click()", VED); pg.wait_for_timeout(300)
    a7 = pg.evaluate(FS)
    check(a7['chips'] == ['ShipVedmak'], f'... and on from Near You {a7["chips"]}')
    # every attacker's ship counts, not only the victim's or the final blow's (whose ships the row's text names)
    mo = pg.evaluate("""() => { const e = {kind: 'kill', p: {ships: [], sys: []}, kill: {km: {victim: {ship_type_id: 11}, attackers: [{ship_type_id: 12, final_blow: true}, {ship_type_id: 13}]}}};
      return [11, 12, 13, 14].map(id => itFlMatch(e, {kind: 'ship', id})); }""")
    check(mo == [True, True, True, False], f'a kill matches the victim\'s ship and every attacker\'s, the final blow or not; not another ship {mo}')
    # an alliance and the ship: rows with both
    grp = pg.evaluate("() => { const b = document.querySelector('#itFeedList [data-it-grp^=\"alliance:\"]'); return b ? b.dataset.itGrp : null; }")
    pg.click(f'#itFeedList [data-it-grp="{grp}"]'); pg.wait_for_timeout(400)
    a8 = pg.evaluate(FS)
    both = pg.evaluate("""([g, ship]) => { const [k, id] = g.split(':'), v = itGrpTk(k, Number(id)); return itFeedShown().length === it.feed.filter(e => e.t >= Date.now() - it.set.forget * 60000 && itShipsOf(e).has(ship) && itGrpIn(e, {kind: k, tk: v.ticker.toLowerCase()})).length; }""", [grp, VED])
    check(len(a8['chips']) == 2 and a8['chips'][0] == 'ShipVedmak' and a8['chips'][1].startswith('Alliance') and both and a8['fl'] == 2, f'an alliance and the Vedmak: the rows with both (every chip must match) {a8["chips"]} {len(a8["feed"])}')
    # typed text with chips; [CORP] typed by hand
    pg.fill('[data-it-q]', 'zzzz-nothing'); pg.wait_for_timeout(400)
    a9 = pg.evaluate(FS)
    check(not a9['feed'] and a9['msg'] == 'Nothing matches the filters.', f'typed text and the chips both apply; nothing matching says so {a9["msg"]!r}')
    pg.fill('[data-it-q]', ''); pg.click('#intelPanel [data-it-fca]'); pg.wait_for_timeout(400)
    a10 = pg.evaluate(FS); fs = pg.evaluate("() => document.activeElement && document.activeElement.matches('[data-it-q]')")
    check(not a10['chips'] and len(a10['feed']) == len(f0['feed']) and fs, f'Clear all: no chips, everything, the focus in the search box {len(a10["feed"])}')
    tk = pg.evaluate("() => { const b = document.querySelector('#itFeedList [data-it-grp^=\"corporation:\"]'), [k, id] = b.dataset.itGrp.split(':'); return itGrpTok(k, itGrpTk(k, Number(id)).ticker); }")
    pg.fill('[data-it-q]', tk.lower()); pg.wait_for_timeout(400); a11 = pg.evaluate(FS); pg.fill('[data-it-q]', ''); pg.wait_for_timeout(300)
    check(0 < len(a11['feed']) < len(f0['feed']) and not a11['chips'], f'{tk.lower()} typed by hand still filters to that corporation ({len(a11["feed"])} of {len(f0["feed"])})')
    # a redraw keeps the chips and the focus
    pg.click(f'#itFeedList [data-it-fship="{VED}"]'); pg.wait_for_timeout(300)
    pg.focus('#intelPanel .it-fchips [data-it-fcx="0"]')
    W(pg, F_INTEL, line(_t.time(), 'Scout Alt', f'{MORE[0]} +2 rifter')); pg.wait_for_timeout(3500)
    a12 = pg.evaluate(FS); kf = pg.evaluate("() => !!document.activeElement && document.activeElement.matches('[data-it-fcx]')")
    check(a12['chips'] == ['ShipVedmak'] and kf, f'a new report: the chip and the Feed\'s filter kept, the focus on its × {a12["chips"]} {kf}')
    # the card's cheap compare includes the chips: a chip set without a forced redraw still redraws the Feed
    pg.evaluate("(id) => { it.fl = [{kind: 'ship', id: %d, label: 'Loki'}]; it.drawNow = Date.now(); itRender(); }" % M.byname['Loki'], 0); pg.wait_for_timeout(300)
    qk = pg.evaluate(FS)
    check(qk['chips'] == ['ShipLoki'] and all(M.byname['Loki'] in [M.byname.get(n) for n in x[2]] or x[0] for x in qk['feed']), f'a chip changed, the card redrawn without forcing it (the chips are in its quick key) {qk["chips"]}')
    pg.evaluate("() => { it.fl = []; itRender(true); }")
    # 390 px: three chips wrap, × 36 px, nothing off the page
    pg.evaluate("(g) => { it.fl = [{kind: 'sys', id: %d, label: '8WA-Z6'}, {kind: 'ship', id: %d, label: 'Vedmak'}, {kind: g.split(':')[0], id: Number(g.split(':')[1]), label: ''}]; itRender(true); }" % (SYSID['8WA-Z6'], VED), grp)
    pg.set_viewport_size({'width': 390, 'height': 900}); pg.wait_for_timeout(700)
    ph = pg.evaluate("() => [document.documentElement.scrollWidth, [...document.querySelectorAll('#intelPanel .it-fc-x')].map(b => Math.round(b.getBoundingClientRect().height)), [...document.querySelectorAll('#intelPanel .it-fc')].map(c => Math.round(c.getBoundingClientRect().right))]")
    check(ph[0] <= 390 and ph[1] and set(ph[1]) == {36} and max(ph[2]) <= 390, f'390 px: three chips wrap, each × 36 px, nothing off the page {ph}')
    pg.set_viewport_size({'width': 1440, 'height': 1000}); pg.evaluate("() => { it.fl = []; itRender(true); }"); pg.wait_for_timeout(500)
    # ---- ISK on Near You's kill badges ----
    KB = """(sys) => { const r = document.querySelector(`#itNearList .it-nb[data-it-sys="${sys}"]`); return [...r.querySelectorAll('.it-kl')].map(b => [b.textContent, b.title]); }"""
    s8 = SYSID['8WA-Z6']; k1 = pg.evaluate(KB, s8)
    check(k1 and k1[0][0] == '1 friendly lost62.4M' and 'Together 62,400,000 ISK' in k1[0][1], f'a badge with its kill\'s value: "1 friendly lost 62.4M", the exact total in its hover {k1}')
    pg.evaluate("(s) => { const st = it.near.get(s); st.kills.push({t: Date.now(), id: -11, v: 'f', isk: 12e6}); st.kills.push({t: Date.now(), id: -12, v: 'f', isk: 0}); itRender(true); }", s8); pg.wait_for_timeout(300)
    k2 = pg.evaluate(KB, s8)
    check(k2 and k2[0][0] == '3 friendlies lost74.4M' and 'Together 74,400,000 ISK' in k2[0][1] and '2 of 3 kills have a value' in k2[0][1], f'three kills, one without a value: the two summed, the hover says so {k2}')
    pg.evaluate("(s) => { const st = it.near.get(s); st.kills.push({t: Date.now(), id: -13, v: 'h', isk: 5e6}); itRender(true); }", s8); pg.wait_for_timeout(300)
    k4 = pg.evaluate(KB, s8)
    check(len(k4) == 2 and k4[0][0] == '3 friendlies lost74.4M' and k4[1][0] == '1 hostile killed5.0M', f'each badge sums its own kills only {k4}')
    pg.evaluate("(s) => { const st = it.near.get(s); st.kills = st.kills.filter(k => k.id !== -13).map(k => ({...k, isk: 0})); itRender(true); }", s8); pg.wait_for_timeout(300)
    k3 = pg.evaluate(KB, s8)
    check(k3 and k3[0][0] == '3 friendlies lost' and 'ISK' not in k3[0][1], f'none with a value: no amount {k3}')
    zk = [p for _, p, _ in REQS]   # R2Z2 only; the zKillboard API: none asked for values
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
'''
exec(compile(_src + _tail, 'intel_filters_check.py', 'exec'), _ns)
print(f"FAILURES: {_ns['NS']['fails']}")
sys.exit(1 if _ns['NS']['fails'] else 0)
