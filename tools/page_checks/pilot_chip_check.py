"""Intel's pilot chip: its parts and what each does (v2026.11.01.2; mockup Claude outputs/pilot_chip_hover_mockup.html, B2).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/pilot_chip_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner: "Go with B2"; "i would prefer that alliance and corp were not grouped. should be able to filter by either. also remove
the ability to change standing from there. once we move to SSO, standing is set by the corp and alliance". Runs intel_check.py's
start (its made-up Chatlogs folder, ESI and groups; you in 1DQ1-A), then made-up lines and a made-up kill. Checks:
  * a chip's parts in order: the standing (not a button; its tip "Hostile, from your Standings"), the name (a button: the Pilot
    Analyzer), the corporation (a button: its logo and [TICKER]), the alliance (logo and <TICKER>); none for a pilot without one;
  * hover: the whole chip gets an outline and dividers between its parts, only the part under the pointer fills, in white (no cyan);
    keyboard focus on a part does the same;
  * a corporation pressed: the Feed's search box says [TICKER], the Feed shows only lines with that corporation (a kill too), the
    button is pressed, Near You isn't filtered; pressed again, everything; an alliance the same with <TICKER> (both of its
    corporations); a ticker typed in brackets filters the same way; the standing pressed does nothing;
  * the name pressed: the Pilot Analyzer;
  * without hover (a phone; matchMedia stubbed): the first tap shows the parts and does nothing else (kept when the lists redraw), the second does what the part
    says, a tap elsewhere puts the chip back; 390 px: nothing off the page, no name on two lines (the groups go under it);
  * reduced motion: no transitions;
  * no page errors.
v2026.11.01.1 fails (the chip is one button).
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, 'intel_check.py'), encoding='utf-8').read()
_src = _src[:_src.index('    jumps = pg.evaluate("(names) => Object.fromEntries')]
_src = _src.replace("os.path.dirname(os.path.abspath(__file__))", repr(HERE), 1)
_ns = {'__file__': os.path.join(HERE, 'intel_check.py'), '__name__': 'intel_check_prefix'}
_tail = r'''
    P_RLH, P_BLDF, P_LBT = M.PILOTS[M.pick(98000003)][0], M.PILOTS[M.pick(98000004)][0], M.PILOTS[M.pick(98000013)][0]
    L1 = [f'N-8YET {P_RLH}* loki', f'8WA-Z6 {P_BLDF} sabre', f'T5ZI-S {P_LBT} rifter']
    t0 = time.time() - 120
    W(pg, F_INTEL, ''.join(line(t0 + 10 * i, 'Scout Alt', m) for i, m in enumerate(L1))); tick(pg, 3500)
    # a made-up kill: a Lantern Bay Traders victim (no alliance), two Bloodfin Corp attackers (Crimson Tide Syndicate)
    pg.evaluate("""([a]) => { itAddKill({km: {killmail_id: 9201, killmail_time: new Date(Date.now() - 60000).toISOString(), solar_system_id: 30004762,
        victim: {character_id: 91000045, corporation_id: 98000013, ship_type_id: 587},
        attackers: [1, 2].map(i => ({character_id: a + i, corporation_id: 98000004, alliance_id: 99000003, ship_type_id: 22456, final_blow: i === 0, damage_done: 100}))},
      z: {locationID: 40000001, totalValue: 1e7, attackerCount: 2, hash: 'x', npc: false}, t: Date.now() - 60000}); itRenderLists(); }""", [M.pick(98000004)])   # other Bloodfin pilots than the reported one: one chip per name
    tick(pg, 1500)   # the tickers (ESI, made up) fill in
    pg.evaluate("() => itRenderLists()"); tick(pg, 300)
    PARTS = """(name) => { const c = [...document.querySelectorAll('#itFeedList .it-chip.p')].find(x => x.querySelector('.nm').textContent === name); if(!c) return null;
      return [...c.children].map(s => [s.tagName, s.className, s.textContent.trim(), s.title, s.querySelectorAll('.it-lg').length, s.querySelectorAll('.it-lg.c').length]); }"""
    a = pg.evaluate(PARTS, P_RLH)
    check(a and [x[1] for x in a] == ['it-seg st', 'it-seg nmb', 'it-seg grp co', 'it-seg grp al'] and [x[0] for x in a] == ['SPAN', 'BUTTON', 'BUTTON', 'BUTTON']
          and a[0][3].endswith(', from your Standings') and a[1][2] == P_RLH and f'Open {P_RLH} in the Pilot Analyzer' in a[1][3], f'a chip: standing (not a button, a tip), name, corporation, alliance, as buttons {a}')
    check(a and a[2][2] == '[RLH]' and a[2][4:] == [1, 1] and a[3][2] == '<CRTS>' and a[3][4:] == [1, 0] and a[2][3] == 'Red Ledger Holdings [RLH]. Show only this corporation in the Feed'
          and a[3][3] == 'Crimson Tide Syndicate <CRTS>. Show only this alliance in the Feed' and 'change' not in a[0][3].lower(),
          f'the corporation: its logo (round) and [RLH]; the alliance: its logo and <CRTS>; their tips; nothing about changing the standing {a and a[2:]}')
    b_ = pg.evaluate(PARTS, P_LBT)
    check(b_ and [x[1] for x in b_] == ['it-seg st', 'it-seg nmb', 'it-seg grp co'], f'a pilot without an alliance: no alliance part {b_}')
    # hover: the chip outlined, dividers, only the part under the pointer filled (white)
    sel = lambda nm, k: f"#itFeedList .it-chip.p:has(.nm:text-is('{nm}')) .it-seg.{k}"
    pg.hover(sel(P_RLH, 'co')); tick(pg, 300)
    HOV = """(name) => { const c = [...document.querySelectorAll('#itFeedList .it-chip.p')].find(x => x.querySelector('.nm').textContent === name); const s = [...c.children].map(x => getComputedStyle(x));
      return [getComputedStyle(c).outlineColor, s.map(x => x.backgroundColor), s.map(x => x.boxShadow)]; }"""
    h = pg.evaluate(HOV, P_RLH)
    clear = lambda col: col in ('rgba(0, 0, 0, 0)', 'transparent')
    check(h[0] not in ('rgba(0, 0, 0, 0)',) and clear(h[1][0]) and clear(h[1][1]) and h[1][2].startswith('rgba(255, 255, 255') and clear(h[1][3])
          and all('inset' in x or '1px' in x for x in h[2][1:]), f'hover on the corporation: the chip outlined, dividers, only the corporation filled in white {h}')
    pg.hover(sel(P_RLH, 'st')); tick(pg, 300)
    h2 = pg.evaluate(HOV, P_RLH)
    check(h2[0] not in ('rgba(0, 0, 0, 0)',) and all(clear(x) for x in h2[1]), f'hover on the standing: the chip outlined, no part filled (it does nothing) {h2}')
    pg.mouse.move(5, 5); tick(pg, 300)
    h3 = pg.evaluate(HOV, P_RLH)
    check(h3[0] == 'rgba(0, 0, 0, 0)' and all('none' == x for x in h3[2]), f'at rest: no outline, no dividers {h3}')
    # the keyboard: focus on the name: the chip outlined, the name filled
    pg.evaluate("(name) => [...document.querySelectorAll('#itFeedList .it-chip.p')].find(x => x.querySelector('.nm').textContent === name).querySelector('.nmb').focus()", P_RLH)
    pg.keyboard.press('Shift+Tab'); pg.keyboard.press('Tab'); tick(pg, 300)   # :focus-visible comes with keyboard use
    h4 = pg.evaluate(HOV, P_RLH)
    check(h4[0] != 'rgba(0, 0, 0, 0)' and h4[1][1].startswith('rgba(255, 255, 255') and clear(h4[1][2]), f'keyboard focus on the name: the chip outlined, the name filled {h4}')
    # a corporation pressed: the Feed shows only it; again: everything; Near You never filtered
    ST = """() => [document.querySelector('[data-it-q]').value, document.querySelectorAll('#itNearList .it-nb').length,
      [...document.querySelectorAll('#itFeedList .it-fd')].map(r => [r.classList.contains('kill'), ((r.querySelector('.it-raw .raw') || {}).textContent || '')]),
      [...document.querySelectorAll('#itFeedList [data-it-grp][aria-pressed="true"]')].map(b => b.textContent)]"""
    s0 = pg.evaluate(ST)
    pg.click(sel(P_RLH, 'co')); tick(pg, 400)
    s1 = pg.evaluate(ST)
    check(s1[0] == '[RLH]' and s1[1] == s0[1] and [x[1] for x in s1[2]] == [L1[0]] and s1[3] and set(s1[3]) == {'[RLH]'} and len(s0[2]) >= 4,
          f'[RLH] pressed: the search box says [RLH], the Feed only its line, the button pressed, Near You unchanged {s1} (before {len(s0[2])} rows)')
    pg.click(sel(P_RLH, 'co')); tick(pg, 400)
    s2 = pg.evaluate(ST)
    check(s2[0] == '' and len(s2[2]) == len(s0[2]) and not s2[3], f'pressed again: everything {s2[0]!r} {len(s2[2])}')
    pg.click(sel(P_BLDF, 'al')); tick(pg, 400)
    s3 = pg.evaluate(ST)
    check(s3[0] == '<CRTS>' and sorted(x[1] for x in s3[2] if not x[0]) == sorted([L1[0], L1[1]]) and sum(1 for x in s3[2] if x[0]) == 1 and set(s3[3]) == {'<CRTS>'},
          f'<CRTS> pressed: both of its corporations\' lines and the kill its pilots made, not the Lantern Bay line {s3}')
    pg.fill('[data-it-q]', '[bldf]'); tick(pg, 400)
    s4 = pg.evaluate(ST)
    check(sorted(x[1] for x in s4[2] if not x[0]) == [L1[1]] and sum(1 for x in s4[2] if x[0]) == 1 and set(s4[3]) == {'[BLDF]'}, f'[bldf] typed: that corporation exactly, its button pressed {s4}')
    pg.fill('[data-it-q]', ''); tick(pg, 400)
    q0 = pg.evaluate("() => [document.querySelector('[data-it-q]').value, document.getElementById('tabIntel').style.display]")
    pg.click(sel(P_RLH, 'st')); tick(pg, 400)
    q1 = pg.evaluate("() => [document.querySelector('[data-it-q]').value, document.getElementById('tabIntel').style.display]")
    check(q0 == q1 == ['', q0[1]], f'the standing pressed: nothing happens {q0} {q1}')
    # reduced motion: no transitions
    pg.emulate_media(reduced_motion='reduce'); tick(pg, 100)
    rm = pg.evaluate("(name) => { const c = [...document.querySelectorAll('#itFeedList .it-chip.p')].find(x => x.querySelector('.nm').textContent === name); return [getComputedStyle(c).transitionDuration, getComputedStyle(c.querySelector('.grp')).transitionDuration]; }", P_RLH)
    pg.emulate_media(reduced_motion='no-preference')
    check(all(set(x.split(', ')) == {'0s'} for x in rm), f'reduced motion: no transitions {rm}')
    # without hover: first tap shows the parts, the second acts, elsewhere puts it back
    pg.set_viewport_size({'width': 390, 'height': 900}); pg.evaluate("() => { window.__nh = itNoHover; window.itNoHover = () => true; itRenderLists(); }"); tick(pg, 300)
    pg.click(sel(P_RLH, 'co')); tick(pg, 300)
    p1 = pg.evaluate("(name) => [document.querySelector('[data-it-q]').value, [...document.querySelectorAll('#itFeedList .it-chip.p')].find(x => x.querySelector('.nm').textContent === name).classList.contains('armed'), getComputedStyle([...document.querySelectorAll('#itFeedList .it-chip.p')].find(x => x.querySelector('.nm').textContent === name)).outlineColor]", P_RLH)
    pg.evaluate("() => itRenderLists()"); tick(pg, 200)   # the lists redraw as lines arrive: the chip stays shown
    pr = pg.evaluate("(name) => { const c = [...document.querySelectorAll('#itFeedList .it-chip.p')].find(x => x.querySelector('.nm').textContent === name); return [c.classList.contains('armed'), getComputedStyle(c).outlineColor]; }", P_RLH)
    pg.click(sel(P_RLH, 'co')); tick(pg, 400)
    p2 = pg.evaluate("() => document.querySelector('[data-it-q]').value")
    pg.click(sel(P_RLH, 'co')); tick(pg, 400)   # still shown (kept across the redraw): off at once
    pg.click(sel(P_BLDF, 'co')); tick(pg, 200); pg.click('#itFeedList', position={'x': 3, 'y': 3}); tick(pg, 200)
    p3 = pg.evaluate("() => [document.querySelector('[data-it-q]').value, document.querySelectorAll('#itFeedList .it-chip.armed').length]")
    ow = pg.evaluate("() => document.documentElement.scrollWidth")
    nh = pg.evaluate("() => Math.max(...[...document.querySelectorAll('#itFeedList .it-chip .nm')].map(n => Math.round(n.getBoundingClientRect().height / (parseFloat(getComputedStyle(n).fontSize) * 1.25))))   // lines (a flex item's text gives one rect however many lines)")
    check(p1[:2] == ['', True] and p1[2] != 'rgba(0, 0, 0, 0)' and pr[0] and pr[1] != 'rgba(0, 0, 0, 0)' and p2 == '[RLH]' and p3 == ['', 0] and ow <= 390 and nh == 1,
          f'without hover: the first tap shows the parts only, the second filters, a tap elsewhere puts it back; 390 px fits, every name on one line (the groups wrap instead) {p1} {pr} {p2!r} {p3} {ow} {nh}')
    pg.evaluate("() => { window.itNoHover = window.__nh; }"); pg.set_viewport_size({'width': 1440, 'height': 1000}); pg.evaluate("() => itRenderLists()"); tick(pg, 300)
    # the name: the Pilot Analyzer
    pg.click(sel(P_BLDF, 'nmb')); tick(pg, 800)
    pa = pg.evaluate("() => [document.getElementById('tabPilot').style.display !== 'none', document.getElementById('tabIntel').style.display === 'none']")
    check(pa == [True, True], f'the name: the Pilot Analyzer {pa}')
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
'''
exec(compile(_src + _tail, 'pilot_chip_check.py', 'exec'), _ns)
print(f"FAILURES: {_ns['fails']}")
sys.exit(1 if _ns['fails'] else 0)
