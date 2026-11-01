"""One close button on every info and settings panel; the Fleet tab's kill list scrolls inside, with each kill's ISK (v2026.11.01.3).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/close_buttons_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner: "all info and settings panels need to have their own close button in the top right. only some do currently";
"fleet tab > list of kills originating from intel tab needs scrolling. systems with large battles will fill the entire screen and
cause endless scrolling"; "add isk value of a kill to the list of killmails in the fleet tab"; then "Build with my picks", "Scroll
inside", "Close buttons only" (mockup Claude outputs/close_buttons_kill_list_mockup.html). Runs intel_kills_check.py's start
(made-up logs and kills, R2Z2 and ESI answered by stand-ins), then:
  * an info panel (Intel's), Intel settings (the gear), "Open zKillboard?" (leaving the site) and a Fleet tab info panel: the
    shared close button shows at a wide width, 32 px, in the panel's top right corner; pressing it closes the panel and puts the
    focus back on what opened it; Esc does the same;
  * the Fleet tab's kill list with 31 kills: about six and a half rows show, the rest scroll inside, the wheel at its end moves the
    page on (not trapped); each kill's ISK is zKillboard's value as the Feed writes it, amber, the exact value in its hover, none
    for a kill without a value; a kill picked far down stays in view after the tab redraws; a kill opened while out of view is
    scrolled into view (the list only, never the page);
  * 390 px: the info panel a sheet with a 44 px close button; the kill list's ISK and pilots on the second line; nothing off the
    page;
  * no page errors.
v2026.11.01.2 fails (the close button on a phone only; the list grows with every kill; no ISK).
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, 'intel_kills_check.py'), encoding='utf-8').read()
_src = _src[:_src.index("    # ---- v2026.10.29.3: the Feed's kill range")]
_src = _src.replace("os.path.dirname(os.path.abspath(__file__))", repr(HERE), 1)
_ns = {'__file__': os.path.join(HERE, 'intel_kills_check.py'), '__name__': 'intel_kills_prefix'}
_tail = r'''
    pg.wait_for_timeout(1000)
    # the close button of a panel: [shown, width, height, right gap, top gap, what has the focus]
    XB = """(a) => { const p = document.querySelector(a[0]); if(!p) return null; const x = p.querySelector('button.x-close'); if(!x) return ['no button'];
      const r = x.getBoundingClientRect(), q = p.getBoundingClientRect(); return [x.checkVisibility(), Math.round(r.width), Math.round(r.height), Math.round(q.right - r.right), Math.round(r.top - q.top), x.getAttribute('aria-label')]; }"""
    FOC = "() => { const a = document.activeElement; return a ? (a.id || a.className || a.tagName) : ''; }"
    def corner(x): return x and x[0] is True and x[1:3] == [32, 32] and 0 <= x[3] <= 16 and 0 <= x[4] <= 14 and x[5] == 'Close'
    # an info panel: Intel's
    pg.click('#intelPanel .it-head summary.info-btn'); pg.wait_for_timeout(300)
    x1 = pg.evaluate(XB, ['#intelPanel .it-head details.info-pop[open] .info-body'])
    pg.click('#intelPanel .it-head details.info-pop[open] button.x-close'); pg.wait_for_timeout(200)
    c1 = pg.evaluate("() => [!!document.querySelector('#intelPanel .it-head details.info-pop[open]'), document.activeElement && document.activeElement.matches('summary.info-btn')]")
    pg.click('#intelPanel .it-head summary.info-btn'); pg.wait_for_timeout(200); pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    e1 = pg.evaluate("() => !!document.querySelector('#intelPanel .it-head details.info-pop[open]')")
    check(corner(x1) and c1 == [False, True] and e1 is False, f'an info panel (Intel): the close button at a wide width, 32 px, top right; it closes, the focus back on the info button; Esc closes {x1} {c1} {e1}')
    # Intel settings (the gear)
    pg.click('#intelPanel .it-head [data-it-act="gear"]'); pg.wait_for_timeout(300)
    x2 = pg.evaluate(XB, ['#intelPanel .it-pop'])
    pg.click('#intelPanel .it-pop button.x-close'); pg.wait_for_timeout(300)
    c2 = pg.evaluate("() => [!!document.querySelector('#intelPanel .it-pop'), document.activeElement && document.activeElement.classList.contains('it-gear')]")
    pg.click('#intelPanel .it-head [data-it-act="gear"]'); pg.wait_for_timeout(200)
    pg.evaluate("() => document.querySelector('#intelPanel .it-pop').querySelector('select, input').focus()"); pg.keyboard.press('Escape'); pg.wait_for_timeout(300)   # from inside the panel
    e2 = pg.evaluate("() => [!!document.querySelector('#intelPanel .it-pop'), document.activeElement && document.activeElement.classList.contains('it-gear')]")
    check(corner(x2) and c2 == [False, True] and e2 == [False, True], f'Intel settings: the close button top right; it closes, the focus back on the gear; Esc from inside it the same {x2} {c2} {e2}')
    # leaving the site: "Open zKillboard?"
    pg.click('#itFeedList a.zk-ic'); pg.wait_for_timeout(300)
    x3 = pg.evaluate(XB, ['#leaveBox'])
    pg.click('#leaveBox button.x-close'); pg.wait_for_timeout(200)
    c3 = pg.evaluate("() => [!!document.getElementById('leaveBox'), document.activeElement && document.activeElement.matches('a.zk-ic')]")
    check(corner(x3) and c3 == [False, True], f'"Open zKillboard?": the close button top right; it closes, the focus back on the link {x3} {c3}')
    # ---- the Fleet tab's kill list: 31 kills on one badge ----
    vals = pg.evaluate("""() => { const e0 = it.feed.find(x => x.kind === 'kill' && x.kill.ships >= 2); const out = [];
      for(let i = 0; i < 30; i++){ const km = JSON.parse(JSON.stringify(e0.kill.km)); km.killmail_id += 500000 + i; const v = i === 7 ? 0 : [1.42e6, 6.4e7, 1.63e9, 2.31e8, 9.9e5][i % 5] * (1 + i / 100);
        itAddKill({km, z: {hash: String(i % 10).repeat(40), totalValue: v}, t: Date.now() - 2000 - i * 1000, history: true}); out.push([km.killmail_id, v]); }
      itRenderLists(); return [e0.p.sys[0].id, e0.kill.victim.side, out]; }""")
    pg.wait_for_timeout(300)
    pg.evaluate("(a) => document.querySelector(`#itNearList [data-it-kb=\"${a[0]}:${a[1]}\"]`).click()", vals[:2]); pg.wait_for_timeout(2500)
    LIST = """() => { const L = document.querySelector('#fleetPanel .fk-picks'); if(!L) return null; const B = [...L.querySelectorAll('button.fk-pk')], h = B[0].getBoundingClientRect().height;
      return {n: B.length, rows: +(L.clientHeight / (h + 4)).toFixed(2), scrolls: L.scrollHeight > L.clientHeight + 4, ob: getComputedStyle(L).overscrollBehaviorY, top: L.scrollTop,
        isk: Object.fromEntries(fk.picks.map((p, i) => [p.id, [B[i].querySelector('.fk-pk-i').textContent, B[i].querySelector('.fk-pk-i').title, getComputedStyle(B[i].querySelector('.fk-pk-i')).color]])),
        pressed: B.findIndex(b => b.getAttribute('aria-pressed') === 'true'),
        seen: (() => { const b = B.find(b => b.getAttribute('aria-pressed') === 'true'); if(!b) return null; const r = b.getBoundingClientRect(), q = L.getBoundingClientRect(); return r.top >= q.top - 1 && r.bottom <= q.bottom + 1; })()}; }"""
    s0 = pg.evaluate(LIST)
    want = {kid: (pg.evaluate('(v) => itIsk(v)', v) if v else '') for kid, v in vals[2]}
    isk_ok = s0 and all(s0['isk'][str(k)][0] == w and (s0['isk'][str(k)][2] == 'rgb(217, 154, 60)') and ((w and s0['isk'][str(k)][1].endswith("ISK (zKillboard's value)")) or (not w and s0['isk'][str(k)][1] == '')) for k, w in want.items())
    check(s0 and s0['n'] == 31 and 6.0 <= s0['rows'] <= 7.0 and s0['scrolls'] and s0['ob'] == 'auto' and s0['pressed'] == 0 and s0['seen'],
          f'31 kills: about six and a half rows show, the rest scroll inside (overscroll auto: the wheel not trapped), the newest pressed and in view {s0 and {k: s0[k] for k in ("n", "rows", "scrolls", "ob", "pressed", "seen")}}')
    check(isk_ok, f"each kill's ISK: zKillboard's value as the Feed writes it, amber, the exact value in its hover; none without a value {[(k, s0['isk'][str(k)], w) for k, w in list(want.items())[:3]] if s0 else s0} {s0 and s0['isk'][str(vals[2][7][0])]}")
    # the wheel at the list's end moves the page on
    pg.evaluate("() => { window.scrollTo(0, 0); const L = document.querySelector('#fleetPanel .fk-picks'); L.scrollTop = L.scrollHeight; }"); pg.wait_for_timeout(200)
    bx = pg.evaluate("() => { const r = document.querySelector('#fleetPanel .fk-picks').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }")
    pg.mouse.move(*bx); pg.mouse.wheel(0, 300); pg.wait_for_timeout(500)
    wy = pg.evaluate("() => window.scrollY")
    pg.evaluate("() => window.scrollTo(0, 0)"); pg.wait_for_timeout(200)
    check(wy > 50, f'the wheel at the end of the list moves the page on ({wy} px)')
    # a kill far down picked: in view after the redraws as its pilots come in
    pg.evaluate("() => { const L = document.querySelector('#fleetPanel .fk-picks'); L.scrollTop = L.querySelector('[data-fk-pick=\"24\"]').offsetTop - L.offsetTop - 40; }"); pg.wait_for_timeout(200)
    t0_ = pg.evaluate("() => document.querySelector('#fleetPanel .fk-picks').scrollTop")
    pg.click('#fleetPanel [data-fk-pick="24"]'); pg.wait_for_timeout(3000)
    s1 = pg.evaluate(LIST); y1 = pg.evaluate("() => window.scrollY")
    check(s1 and s1['pressed'] == 24 and s1['seen'] and abs(s1['top'] - t0_) <= 2, f'a kill far down picked: pressed, in view, the list where it was after the redraws ({t0_} -> {s1 and s1["top"]}) {s1 and s1["pressed"]}')
    # a kill opened while out of view: the list scrolls to it (the page doesn't)
    pg.evaluate("() => { document.querySelector('#fleetPanel .fk-picks').scrollTop = 0; window.scrollTo(0, 0); document.querySelector('#fleetPanel [data-fk-pick=\"29\"]').click(); }"); pg.wait_for_timeout(3000)
    s2 = pg.evaluate(LIST); y2 = pg.evaluate("() => window.scrollY")
    check(s2 and s2['pressed'] == 29 and s2['seen'] and y2 == 0, f'a kill opened out of view: the list scrolled to it, the page not ({y2}) {s2 and (s2["pressed"], s2["seen"], s2["top"])}')
    # a Fleet tab info panel: the same close button
    pg.click('#fleetPanel .fk-sum summary.info-btn'); pg.wait_for_timeout(300)
    x4 = pg.evaluate(XB, ['#fleetPanel .fk-sum details.info-pop[open] .info-body'])
    pg.click('#fleetPanel .fk-sum details.info-pop[open] button.x-close'); pg.wait_for_timeout(200)
    c4 = pg.evaluate("() => !!document.querySelector('#fleetPanel details.info-pop[open]')")
    check(corner(x4) and c4 is False, f'a Fleet tab info panel: the close button top right; it closes {x4} {c4}')
    # 390 px
    pg.set_viewport_size({'width': 390, 'height': 900}); pg.wait_for_timeout(500)
    PH = """() => { const B = [...document.querySelectorAll('#fleetPanel .fk-pk')].slice(0, 3); return B.map(b => { const n = b.querySelector('.fk-pk-n').getBoundingClientRect(), i = b.querySelector('.fk-pk-i').getBoundingClientRect(), a = b.querySelector('.fk-pk-a').getBoundingClientRect(), r = b.getBoundingClientRect();
      return [i.top > n.bottom - 2, Math.abs(i.top - a.top) < 3, i.right <= r.right && a.right <= r.right]; }); }"""
    ph = pg.evaluate(PH); ow = pg.evaluate("() => document.documentElement.scrollWidth")
    pg.click('#fleetPanel .fk-sum summary.info-btn'); pg.wait_for_timeout(300)
    x5 = pg.evaluate(XB, ['#fleetPanel .fk-sum details.info-pop[open] .info-body'])
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    check(ph and all(all(r) for r in ph) and ow <= 390 and x5 and x5[0] is True and x5[1:3] == [44, 44], f'390 px: the ISK and pilots on the second line, inside the row; nothing off the page ({ow}); the info sheet\'s close button 44 px {ph} {x5}')
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
'''
exec(compile(_src + _tail, 'close_buttons_check.py', 'exec'), _ns)
print(f"FAILURES: {_ns['NS']['fails']}")
sys.exit(1 if _ns['NS']['fails'] else 0)
