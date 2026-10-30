"""zKillboard's live feed guarded (v2026.10.30.3; LESSON #106).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/intel_guard_check.py [index.html]   -> 'FAILURES: N' (must be 0)

zKillboard's developer (2026-06-04): R2Z2's limit cut from 20 to 15 requests a second, an automatic 1-hour ban for going over,
"if abuse continues I will likely reduce the rate limit some more". The owner: testing the fix must not get us blocked, so
nothing here reaches zKillboard: intel_kills_check.py's start (made-up logs and kills, R2Z2 answered by a stand-in) up to the
live end, then:
  * a fresh read-back paced at most 5 requests in any second (timed in the page), sequence.json first;
  * a 429 in the middle of a read-back: nothing more sent (the requests already queued dropped), the note INTEL-07 says until
    when (an hour), the stop kept in this browser (a second page of the site sees it and sends nothing either);
  * the hour over (the stop's time moved back): reading resumes;
  * a read that fails with nothing the page may read (a ban can look like this) in the middle of a read-back: nothing more
    sent in that pass, the same number asked again 30 s later at the earliest;
  * the tripwire: with the gate broken on purpose (itKillTurn a no-op), 8 requests at once: 5 sent, then the page stops
    itself for an hour (INTEL-08);
  * no page errors.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, 'intel_kills_check.py'), encoding='utf-8').read()
_src = _src[:_src.index("    # ---- v2026.10.29.3: the Feed's kill range")]
_src = _src.replace("os.path.dirname(os.path.abspath(__file__))", repr(HERE), 1)
_ns = {'__file__': os.path.join(HERE, 'intel_kills_check.py'), '__name__': 'intel_kills_prefix'}
_tail = r'''
    def calm():
        for _ in range(120):
            if pg.evaluate("() => it.kf.head && !it.kf.busy"): return True
            pg.wait_for_timeout(250)
        return False
    def sent_since(t): return [q for u, q, _ in REQS if u >= t]
    PER_S = "() => { const t = window.__r2t || []; let m = 0; for(let i = 0, j = 0; i < t.length; i++){ while(t[i] - t[j] >= 1000) j++; m = Math.max(m, i - j + 1); } return m; }"
    calm()
    # ---- a fresh read-back, at most 5 a second ----
    pg.evaluate("() => { window.__r2t = []; it.kf.seq = null; it.kf.head = false; it.kf.waitUntil = 0; }")
    t0 = time.time()
    for _ in range(40):
        if len(sent_since(t0)) >= 40: break
        pg.wait_for_timeout(250)
    ps = pg.evaluate(PER_S); q0 = sent_since(t0)
    span = pg.evaluate("() => { const t = window.__r2t || []; return t.length > 1 ? (t[t.length - 1] - t[0]) / 1000 : 0; }"); n0 = pg.evaluate("() => (window.__r2t || []).length")
    rate = (n0 - 1) / span if span else 99
    # the gate spaces starts 200 ms apart; fetch() itself is called a moment later, so in any one second up to 6 calls can show
    check(q0[:1] == ['/ephemeral/sequence.json'] and len(q0) >= 30 and ps <= 6 and rate <= 5.05,
          f'a read-back: sequence.json first, then {rate:.2f} requests a second on average, at most {ps} in any one second ({len(q0)} sent in {time.time() - t0:.0f} s)')
    # ---- a 429 in the middle of it ----
    SEQ['fail'] = 429; t1 = time.time()
    for _ in range(40):
        if any(s_ == 429 for u, _, s_ in REQS if u >= t1): break
        pg.wait_for_timeout(100)
    t429 = min((u for u, _, s_ in REQS if u >= t1 and s_ == 429), default=None)
    pg.wait_for_timeout(15000)
    after = [q for u, q, _ in REQS if t429 is not None and u > t429]
    st = pg.evaluate("() => [JSON.parse(localStorage.getItem('dscanR2Stop') || 'null'), (document.querySelector('[data-it-kfnote]') || {}).textContent || '']")
    stop, note = st[0] or {}, st[1]
    mins = ((stop.get('until') or 0) / 1000 - time.time()) / 60
    check(t429 is not None and after == [], f'a 429 in the middle of a read-back: nothing more sent in the next 15 s (the queued requests dropped) {after[:5]}')
    check(55 <= mins <= 61 and stop.get('why') == 'status 429' and 'INTEL-07' in note and 'until' in note,
          f'the stop: an hour ({mins:.1f} min), kept in this browser, the note INTEL-07 says until when {stop} {note[:120]!r}')
    pg2 = ctx.new_page(); pg2.goto('file://' + HTML); pg2.wait_for_timeout(800)
    t2 = time.time()
    other = pg2.evaluate("async () => { const a = itR2Stopped() > Date.now(); let b; try{ await itR2Fetch('/ephemeral/sequence.json'); b = 'sent'; }catch(e){ b = e.r2stop ? 'stopped' : String(e); } return [a, b]; }")
    pg2.wait_for_timeout(500)
    check(other[0] and other[1] == 'stopped' and sent_since(t2) == [], f'a second page of the site sees the stop and sends nothing {other} {sent_since(t2)}')
    pg2.close()
    # ---- the hour over ----
    SEQ['fail'] = None
    pg.evaluate("() => { localStorage.removeItem('dscanR2Stop'); it.r2stop = null; it.kf.waitUntil = 0; }")
    t3 = time.time()
    for _ in range(60):
        if len(sent_since(t3)) >= 5: break
        pg.wait_for_timeout(250)
    check(len(sent_since(t3)) >= 5, f'the hour over: reading resumes ({len(sent_since(t3))} sent)')
    # ---- a read that fails unreadably in the middle of a read-back ----
    pg.evaluate("() => { it.kf.seq = null; it.kf.head = false; it.kf.waitUntil = 0; }")
    t4 = time.time()
    for _ in range(40):
        if len(sent_since(t4)) >= 12: break
        pg.wait_for_timeout(100)
    SEQ['fail'] = 'abort'; t5 = time.time()
    for _ in range(40):
        if any(s_ == 0 for u, _, s_ in REQS if u >= t5): break
        pg.wait_for_timeout(100)
    tf = min((u for u, _, s_ in REQS if u >= t5 and s_ == 0), default=None)
    pg.wait_for_timeout(12000)
    after = [q for u, q, _ in REQS if tf is not None and u > tf]
    wu = pg.evaluate("() => (it.kf.waitUntil - Date.now()) / 1000")
    check(tf is not None and after == [] and wu > 10, f'a read that fails unreadably in a read-back: nothing more sent in that pass ({after[:5]}), the next try in {wu:.0f} s')
    SEQ['fail'] = None
    # ---- the tripwire ----
    pg.evaluate("() => { it.kf.waitUntil = Date.now() + 600000; }")   # the pump out of the way
    pg.wait_for_timeout(2500); pg.evaluate("() => { it.kf.halt = false; }")   # (the failed read above halted that pass)
    pg.wait_for_timeout(2500)
    t6 = time.time()
    tw = pg.evaluate("""async () => { const keep = itKillTurn; itKillTurn = async () => {};
      const r = await Promise.allSettled(Array.from({length: 8}, () => itR2Fetch('/ephemeral/sequence.json')));
      itKillTurn = keep; it.kf.waitUntil = 0; return [r.filter(x => x.status === 'fulfilled').length, r.filter(x => x.status === 'rejected' && x.reason.r2stop).length, JSON.parse(localStorage.getItem('dscanR2Stop') || 'null')]; }""")
    pg.evaluate("() => { it.kf.waitUntil = 0; }"); pg.wait_for_timeout(2500)
    note = pg.evaluate("() => (document.querySelector('[data-it-kfnote]') || {}).textContent || ''")
    sent = sent_since(t6)
    check(tw[0] == 5 and tw[1] == 3 and (tw[2] or {}).get('why') == 'self' and len(sent) == 5 and 'INTEL-08' in note,
          f'the tripwire, the gate broken on purpose: 5 sent, then the page stops itself for an hour (INTEL-08) {tw[:2]} {len(sent)} {note[:90]!r}')
    pg.evaluate("() => { localStorage.removeItem('dscanR2Stop'); it.r2stop = null; }")
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
'''
exec(compile(_src + _tail, 'intel_guard_check.py', 'exec'), _ns)
print(f"FAILURES: {_ns['NS']['fails']}")
sys.exit(1 if _ns['NS']['fails'] else 0)
