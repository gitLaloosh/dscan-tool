"""Intel draws only when something changed and only while it can be seen; no endless repainting (v2026.11.01.4).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/intel_redraw_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner asked what the tool costs his machine next to EVE and RIFT ("one of my issues with using RIFT is that it seems to eat up a
lot of resources on my machine when i am trying to run the game at the same time"); the measurement (Project doc
roadmap/performance-2026-11-01.md) found the Intel card rebuilt and measured every 2 s whether anything changed or not, also with
another tab in front, and two endless animations repainting every frame. Runs intel_check.py's start (its made-up Chatlogs folder,
ESI and system names; you in 1DQ1-A), then:
  * with nothing new for 32 s (16 ticks): the card built to compare only when the age timer is due (at most 3 times), the page
    written only if a shown age changed; the status line kept current on its own;
  * a new report line: its row in both lists within a few seconds;
  * the ages move on their own timer (a line under a minute old: its age changes within ~10 s), without a new line;
  * another tab in front (the Pilot Analyzer): nothing in the card is drawn while lines arrive, a hostile line in range still
    alerts and the profile's Intel mark still follows; back on Intel, the new rows are there at once;
  * the browser tab hidden (document.hidden): the same; shown again (visibilitychange): drawn;
  * the header's sweeping line runs 3 times, not forever; every endless animation on the page animates only opacity or transform
    (the compositor's own work: no repaint every frame): the profile's in-system ring and the Intel switch's breathing (off) among
    them; the switch is still with reduced motion;
  * no page errors.
v2026.11.01.3 fails (the card rebuilt every tick, drawn with another tab in front, endless box-shadow animations).
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, 'intel_check.py'), encoding='utf-8').read()
_src = _src[:_src.index('    jumps = pg.evaluate("(names) => Object.fromEntries')]
_src = _src.replace("os.path.dirname(os.path.abspath(__file__))", repr(HERE), 1)
_ns = {'__file__': os.path.join(HERE, 'intel_check.py'), '__name__': 'intel_check_prefix'}
_tail = r'''
    P1, P2, P3 = M.PILOTS[M.pick(98000003)][0], M.PILOTS[M.pick(98000003, 1)][0], M.PILOTS[M.pick(98000004)][0]
    tick(pg, 3000)
    # watch the card: rebuilt (a new card element) or a list rewritten (a child list changed outside the status line)
    WATCH = """() => { const el = document.getElementById('intelPanel'); window.__card = el.firstElementChild; window.__mut = 0;
      if(window.__mo) window.__mo.disconnect();
      window.__mo = new MutationObserver(ms => { for(const m of ms){ const t = m.target.nodeType === 1 ? m.target : m.target.parentElement; if(!t || !t.closest('[data-it-status]')) window.__mut++; } });
      window.__mo.observe(el, {childList: true, subtree: true, characterData: true}); }"""
    SEEN = "() => [document.getElementById('intelPanel').firstElementChild === window.__card, window.__mut, (document.querySelector('#intelPanel [data-it-status]') || {}).textContent || '']"
    ROWS = "() => [[...document.querySelectorAll('#itNearList .it-nb .sys')].map(b => b.textContent), [...document.querySelectorAll('#itFeedList .it-fd .raw')].map(r => r.textContent)]"
    TXT = "() => [...document.querySelectorAll('#intelPanel .it-top, #intelPanel .it-feedcol, #intelPanel .it-head')].map(x => x.textContent).join('|')"
    pg.evaluate(WATCH); t0_ = pg.evaluate(TXT)
    pg.evaluate("() => { const f = itBuildAt; window.__builds = 0; window.itBuildAt = function(...a){ window.__builds++; return f.apply(this, a); }; }")   # how often the card is built to compare
    tick(pg, 32000)
    q = pg.evaluate(SEEN); sl = pg.evaluate("() => { const d = document.createElement('div'); d.innerHTML = itStatusLine(); return d.textContent; }")
    nb = pg.evaluate("() => window.__builds"); t1_ = pg.evaluate(TXT)
    check((q[1] == 0 or t1_ != t0_) and q[2] and q[2] == sl and nb <= 3, f'nothing new for 32 s (16 ticks): built {nb} times to compare (the age timer), the lists touched only if a shown age changed ({q[1]} changes, text changed: {t1_ != t0_}); the status line kept current on its own ({q[2]!r} / {sl!r})')
    # the age timer due on every tick for 10 s (made so here): built each time, but the page written only when a shown text changed
    pg.evaluate(WATCH); t0_ = pg.evaluate(TXT)
    pg.evaluate("() => { window.__agp = itAgePeriod; window.itAgePeriod = () => 1; }"); tick(pg, 10000)
    q2 = pg.evaluate(SEEN); t1_ = pg.evaluate(TXT); pg.evaluate("() => { window.itAgePeriod = window.__agp; }")
    check(q2[1] == 0 or t1_ != t0_, f'built on every tick (the age timer made due): the page written only when a shown text changed ({q2[1]} changes, text changed: {t1_ != t0_})')
    # a new line: drawn
    L1 = f'8WA-Z6 {P1} sabre'
    W(pg, F_INTEL, line(time.time(), 'Scout Alt', L1)); tick(pg, 3500)
    r1 = pg.evaluate(ROWS)
    check('8WA-Z6' in r1[0] and L1 in r1[1], f'a new report line: its row in Near You and the Feed within a few seconds {r1[0]} {r1[1][:3]}')
    # the ages move on their own timer: the newest row's age changes within ~10 s with nothing new
    AGE = "(raw) => { const r = [...document.querySelectorAll('#itFeedList .it-fd')].find(x => (x.querySelector('.raw') || {}).textContent === raw); return r ? r.querySelector('.it-age').textContent : null; }"
    a0 = pg.evaluate(AGE, L1); tick(pg, 13000); a1 = pg.evaluate(AGE, L1)
    check(a0 and a1 and a0 != a1, f'the ages move on their own (a line under a minute old): {a0!r} -> {a1!r}')
    # another tab in front: nothing drawn, alerts and the profile's mark still follow
    pg.click('#tabBtnPilot'); tick(pg, 300); pg.evaluate(WATCH)
    b0 = pg.evaluate("() => __fs.beeps"); m0 = pg.evaluate("() => document.getElementById('profile').dataset.s")
    L2 = f'1DQ1-A {P2} loki'
    W(pg, F_INTEL, line(time.time(), 'Scout Alt', L2)); tick(pg, 6000)
    h = pg.evaluate(SEEN); b1 = pg.evaluate("() => __fs.beeps"); m1 = pg.evaluate("() => [document.getElementById('profile').dataset.s, (document.getElementById('intelNearN') || {}).textContent]")
    check(h[0] and h[1] == 0 and b1 > b0 and m1[0] == 'in' and m0 != 'in', f'the Pilot tab in front: the Intel card not drawn ({h[1]} changes), the hostile in your system still alerts ({b0} -> {b1}) and the profile shows it ({m0} -> {m1})')
    pg.click('#tabBtnIntel'); tick(pg, 300)
    r2 = pg.evaluate(ROWS)
    check('1DQ1-A' in r2[0] and L2 in r2[1], f'back on Intel: the new rows at once {r2[0]} {r2[1][:2]}')
    # the browser tab hidden, then shown
    pg.evaluate("() => { Object.defineProperty(document, 'hidden', {configurable: true, get: () => true}); document.dispatchEvent(new Event('visibilitychange')); }")
    pg.evaluate(WATCH)
    L3 = f'D-W7F0 {P3} rifter'
    W(pg, F_INTEL, line(time.time(), 'Scout Alt', L3)); tick(pg, 6000)
    hh = pg.evaluate(SEEN)
    pg.evaluate("() => { Object.defineProperty(document, 'hidden', {configurable: true, get: () => false}); document.dispatchEvent(new Event('visibilitychange')); }"); tick(pg, 300)
    r3 = pg.evaluate(ROWS)
    check(hh[0] and hh[1] == 0 and 'D-W7F0' in r3[0] and L3 in r3[1], f'the browser tab hidden: nothing drawn ({hh[1]} changes); shown again: drawn {r3[0]}')
    # animations: none endless but opacity / transform; the header line 3 passes; the profile's in-system ring and the Intel switch's
    # breathing (off) by opacity
    AN = """() => document.getAnimations().map(a => { const e = a.effect, t = e && e.getTiming ? e.getTiming() : {}, k = e && e.getKeyframes ? e.getKeyframes() : [];
      const props = [...new Set(k.flatMap(f => Object.keys(f).filter(x => !['offset', 'computedOffset', 'easing', 'composite'].includes(x))))];
      return {name: a.animationName || '', target: e && e.target ? (e.target.id || e.target.className || e.target.tagName) + (e.pseudoElement || '') : '', iter: t.iterations, props}; })"""
    an0 = pg.evaluate(AN)
    ring = [a for a in an0 if a['name'] == 'pfring']
    bad0 = [a for a in an0 if (a['iter'] in (None, float('inf')) or str(a['iter']) == 'Infinity') and set(a['props']) - {'opacity', 'transform'}]
    check(ring and ring[0]['props'] == ['opacity'] and not bad0, f'Intel on, a hostile in your system: the profile\'s ring pulses by opacity; no endless animation on anything else {ring} {bad0}')
    pg.click('#intelSwLabel'); tick(pg, 800)
    an = pg.evaluate(AN)
    sweep = [a for a in an if a['name'] == 'sweep']
    endless = [a for a in an if a['iter'] in (None, float('inf')) or str(a['iter']) == 'Infinity']
    bad = [a for a in endless if set(a['props']) - {'opacity', 'transform'}]
    br = [a for a in an if a['name'] == 'itSwBreathe']
    check(sweep and all(a['iter'] == 3 for a in sweep), f'the header line: 3 passes, not endless {sweep}')
    check(not bad and br and br[0]['props'] == ['opacity'] and br[0]['target'].endswith('::before'), f'endless animations only on opacity or transform (no repaint every frame); the Intel switch breathes by opacity {bad} {br}')
    pg.emulate_media(reduced_motion='reduce'); tick(pg, 200)
    rm = pg.evaluate("() => getComputedStyle(document.getElementById('intelSw'), '::before').animationName")
    pg.emulate_media(reduced_motion='no-preference')
    check(rm == 'none', f'with reduced motion the switch is still ({rm})')
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
'''
exec(compile(_src + _tail, 'intel_redraw_check.py', 'exec'), _ns)
print(f"FAILURES: {_ns['fails']}")
sys.exit(1 if _ns['fails'] else 0)
