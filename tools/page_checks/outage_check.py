"""What's down, and one unreadable kill file (v2026.11.06.6, build queue 015 + 019; Project docs roadmap/outage-notices-plan.md,
roadmap/r2z2-unreadable-kill-plan.md; mockup Claude outputs/outage_notices_mockup.html).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/outage_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner, 2026-11-05: "we need to be able to identify this and let users know when it happens so they're not just looking at an
empty feed." Runs intel_check.py's start (its made-up Chatlogs folder, ESI and system names; you in 1DQ1-A) up to Intel turned on,
on a copy of the page whose waits are shorter (the read-back 60 kills, not 240; the reader's waits after a failure 3 s, not 30;
ESI's /status/ while down every 6 s, not 60); R2Z2 and ESI answered by stand-ins here (made-up kills, never the live services).
  * 019, the read-back: one unreadable published kill file: the rest read once each, that one asked exactly twice (the second 6 s
    later), then read past (kf.skipped 1), the reader reaches the newest, no 016 notice; a run of 40 unreadable: each asked at
    most twice, read past within a few passes; unreadable once then fine: read, not skipped; the whole feed unreadable: nothing
    read past, the notice after the third failure, gone on the next good read; every kill file unreadable with the index fine:
    the notice after three passes, gone once a kill file reads; zKillboard's 429 during a read-back: the hour's stop, nothing
    asked again or read past;
  * 015: ESI down (no answer the browser may read): one /status/ confirms it; the strip, the gauge's "ESI down", Intel's Feed note
    and status line; /status/ once a scaled minute while down, never more; ESI back: all of it gone; one failed lookup while
    /status/ answers: nothing shown; ESI down takes over from the unreadable feed; ESI down and zKillboard's pause: two lines, ESI
    first; EVE's daily downtime: "starts in 4:00" at 10:56 UTC, the downtime line from 11:00 with ESI down, nothing with ESI fine;
    zKillboard's pause: its line with ZKB-01's own text, counting down, gone at its end; the feed behind: 7 kills in 15 minutes:
    the strip, "Kills slow" and the Feed note; 60 kills and a stale sequence.json: nothing;
  * the strip's text written only when it changes; no page errors; Intel shows no error of its own.
"""
import sys, os, re, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
page = open(SRC, encoding='utf-8').read()
for a, b in (('const IT_KILL_BACK = 240;', 'const IT_KILL_BACK = 60;'), ('const IT_KILL_NET_WAIT_MS = 30000;', 'const IT_KILL_NET_WAIT_MS = 3000;'),
             ('Math.min(300000, 30000 * 2 ** (kf.fails - 1))', 'Math.min(300000, 3000 * 2 ** (kf.fails - 1))'), ('const ESI_DOWN_CHECK_MS = 60000;', 'const ESI_DOWN_CHECK_MS = 6000;')):
    if page.count(a) != 1: print(f'FAIL the page has no {a!r} to shorten'); print('FAILURES: 1'); sys.exit(1)
    page = page.replace(a, b)
SCALED = os.path.join(tempfile.mkdtemp(prefix='outage'), 'index.html'); open(SCALED, 'w', encoding='utf-8').write(page)

_src = open(os.path.join(HERE, 'intel_check.py'), encoding='utf-8').read()
_src = _src[:_src.index('    jumps = pg.evaluate("(names) => Object.fromEntries')]
_src = _src.replace("os.path.dirname(os.path.abspath(__file__))", repr(HERE), 1)
_src = re.sub(r"^HTML = .*$", "HTML = " + repr(SCALED), _src, count=1, flags=re.M)
_ns = {'__file__': os.path.join(HERE, 'intel_check.py'), '__name__': 'intel_check_prefix'}
_tail = r'''
    import json as _j, time as _t   # never time.sleep here: the stand-ins answer only while Playwright runs (pg.wait_for_timeout)
    ACAO = {'access-control-allow-origin': '*'}
    R = {'seq': 5000, 'last': 5000, 'bad': set(), 'once': set(), 'missing': set(), 'dead': False, 'r429': set(), 'age': {}}
    HITS = []
    def rec(n):
        age = R['age'].get(n, 60)
        u = int(_t.time() - age)
        return {'killmail_id': 7000000 + n, 'hash': 'h%d' % n, 'sequence_id': n, 'uploaded_at': u, 'zkb': {'hash': 'h%d' % n, 'npc': False},
                'esi': {'killmail_id': 7000000 + n, 'killmail_time': _t.strftime('%Y-%m-%dT%H:%M:%SZ', _t.gmtime(u - 120)), 'solar_system_id': 30000142,
                        'victim': {'ship_type_id': 587, 'character_id': 0}, 'attackers': []}}
    def r2(route):
        path = route.request.url.split('r2z2.zkillboard.com')[1]
        HITS.append((_t.time(), path))
        if path.endswith('/sequence.json'):
            if R['dead']: return route.abort('failed')
            return route.fulfill(status=200, content_type='application/json', headers=ACAO, body=_j.dumps({'sequence': R['seq']}))
        n = int(re.search(r'/(\d+)\.json', path).group(1))
        if n in R['r429']: return route.fulfill(status=429, headers=ACAO, body='')
        if R['dead'] or n in R['bad']: return route.abort('failed')
        if n in R['once']: R['once'].discard(n); return route.abort('failed')
        if n > R['last']: return route.abort('failed')   # not there yet: R2Z2's 404 without the header (LESSON #89)
        if n in R['missing']: return route.fulfill(status=404, headers=ACAO, body='')
        return route.fulfill(status=200, content_type='application/json', headers=ACAO, body=_j.dumps(rec(n)))
    pg.route(re.compile(r'https://r2z2\.zkillboard\.com/.*'), r2)
    E = {'down': False, 'one': False, 'status': []}
    def esi_page(route):
        u = route.request.url
        if '/status/' in u: E['status'].append(_t.time())
        if E['down']: return route.abort('failed')   # ESI's maintenance 503 carries no CORS header: the page sees no answer
        if E['one'] and '/universe/ids/' in u: E['one'] = False; return route.fulfill(status=503, headers=ACAO, body='{"error":"x"}')
        return route.fallback()
    pg.route(re.compile(r'https://esi\.evetech\.net/.*'), esi_page)
    def asked(n): return sum(1 for _, p in HITS if p == '/ephemeral/%d.json' % n)
    def restart(**kw):
        R.update({'seq': 5000, 'last': 5000, 'bad': set(), 'once': set(), 'missing': set(), 'dead': False, 'r429': set(), 'age': {}}); R.update(kw)
        HITS.clear()
        # a new generation, as turning Intel off and on does: a reader still running from the case before stops (it reads it.kf)
        pg.evaluate("() => { localStorage.removeItem('dscanR2Stop'); it.r2stop = null; it.gen++; it.kf = itKfNew(); it.kfNote = ''; itR2EverRead = true; }")
    def wait(js, s=60):
        try: pg.wait_for_function(js, timeout=s * 1000); return True
        except Exception: return False
    STRIP = "() => (document.getElementById('sysStrip') || {}).innerText || ''"
    def strip(): return pg.evaluate(STRIP)
    KF = "() => ({head: it.kf.head, seq: it.kf.seq, skipped: it.kf.skipped, blk: it.kf.blk, allSkip: it.kf.allSkip, down: !!itFeedDown(), ups: it.kf.ups.length, note: it.kfNote})"
    RANGE = range(4941, 5001)
    # ---- 019: one unreadable published kill file ----
    restart(bad={4950})
    t0 = _t.time(); ok = wait("() => it.kf && it.kf.head", 60); took = _t.time() - t0; k = pg.evaluate(KF)
    others = [asked(n) for n in RANGE if n != 4950]
    two = [u for u, p in HITS if p == '/ephemeral/4950.json']
    check(ok and asked(4950) == 2 and 5.5 <= (two[1] - two[0] if len(two) == 2 else 0) <= 12 and k['skipped'] == 1 and not k['down'] and all(x == 1 for x in others),
          f'one unreadable kill file: asked twice (the second {two[1] - two[0] if len(two) == 2 else 0:.1f} s later), read past, the other 59 read once each, the newest reached in {took:.0f} s, no notice {k} {sorted(set(others))}')
    check(k['ups'] == 59 and 'feed' not in strip(), f'... the 59 kills read (none thrown away), and no strip line ({k["ups"]}, {strip()!r})')
    # ---- a run of 40 ----
    restart(bad=set(range(4945, 4985)))
    t0 = _t.time(); ok = wait("() => it.kf && it.kf.head", 90); took = _t.time() - t0; k = pg.evaluate(KF)
    mx = max(asked(n) for n in range(4945, 4985))
    check(ok and k['skipped'] == 40 and mx <= 2 and took < 60 and not k['down'], f'40 unreadable in a row: read past within a few passes ({took:.0f} s), each asked at most twice ({mx}), no notice {k}')
    # ---- unreadable once, fine the second time ----
    restart(once={4960})
    ok = wait("() => it.kf && it.kf.head", 60); k = pg.evaluate(KF)
    check(ok and asked(4960) == 2 and k['skipped'] == 0 and k['ups'] == 60, f'unreadable once, fine on the retry: read, not skipped {k} ({asked(4960)} asks)')
    # ---- every kill file unreadable, the index fine ----
    restart(bad=set(range(4941, 5040)))
    ok = wait("() => it.kf && it.kf.allSkip >= 3", 90); k = pg.evaluate(KF); s1 = strip()
    check(ok and k['down'] and 'INTEL-06' in s1, f'every kill file unreadable, the index fine: the notice after three passes {k} {s1!r}')
    R['bad'] = set(); R['last'] = 5010
    ok = wait("() => !/INTEL-06/.test(document.getElementById('sysStrip').innerText)", 60); s2 = strip()
    check(ok and 'INTEL-06' not in s2, f'... a kill file read: it goes ({s2!r})')
    # ---- the whole feed unreadable ----
    restart(dead=True)
    ok = wait("() => !!itFeedDown()", 60); k = pg.evaluate(KF)
    check(ok and k['skipped'] == 0 and 'INTEL-06' in strip(), f'the whole feed unreadable: nothing read past, the notice after the third failure {k}')
    R['dead'] = False
    ok = wait("() => !/INTEL-06/.test(document.getElementById('sysStrip').innerText)", 150)   # the reader's own wait after several failures (3 s, 6 s, 12 s, 24 s here)
    check(ok, f'... readable again: it goes ({strip()!r})')
    # ---- zKillboard's stop during a read-back ----
    restart(r429={4955})
    ok = wait("() => !!it.kfNote && /INTEL-07/.test(it.kfNote)", 60); pg.wait_for_timeout(8000); k = pg.evaluate(KF)
    later = [p for u, p in HITS if p == '/ephemeral/4955.json']
    check(ok and k['skipped'] == 0 and len(later) == 1, f'zKillboard\'s 429 in a read-back: the hour\'s stop (INTEL-07), nothing asked again or read past {k} {len(later)}')
    pg.evaluate("() => { localStorage.removeItem('dscanR2Stop'); it.r2stop = null; it.kf.waitUntil = 0; it.kfNote = ''; }")
    # ---- 015: the feed behind ----
    restart(missing=set(n for n in RANGE if n % 9), age={})   # 7 kills in 60 numbers
    ok = wait("() => it.kf && it.kf.head", 60); pg.wait_for_timeout(600)
    pg.evaluate("() => { bgPaintNow(); itRender(); }"); pg.wait_for_timeout(300)
    s3 = strip(); g3 = pg.evaluate("() => document.getElementById('bgSegs').innerText.replace(/\\s+/g, ' ')")
    fn = pg.evaluate("() => (document.querySelector('#intelPanel [data-it-why]') || {}).innerText || ''")
    n7 = sum(1 for n in RANGE if not n % 9)
    check(ok and f"zKillboard's kill feed is behind: {n7} kills in the last 15 min" in s3 and 'Kills slow' in g3 and fn.startswith('Kills may be missing'),
          f'the feed behind ({n7} kills in 15 min): the strip, "Kills slow", the Feed note ({s3!r}, {g3!r}, {fn!r})')
    restart(seq=4900, last=5000)   # sequence.json 100 behind, every kill there and new
    ok = wait("() => it.kf && it.kf.head && it.kf.seq > 5000", 90); pg.evaluate("() => { bgPaintNow(); itRender(); }"); pg.wait_for_timeout(300)
    check(ok and 'behind' not in strip() and 'Kills slow' not in pg.evaluate("() => document.getElementById('bgSegs').innerText"), f'a stale sequence.json with the kills there: not behind ({strip()!r})')
    # ---- ESI down ----
    s_before = len(E['status'])
    E['one'] = True
    pg.evaluate("() => resolveNamesToIds(['Nobody Here Yet']).catch(() => 0)"); pg.wait_for_timeout(1500)
    check('ESI' not in strip() and len(E['status']) - s_before == 1, f'one failed lookup, /status/ answering: one /status/ asked, nothing shown ({strip()!r}, {len(E["status"]) - s_before})')
    E['down'] = True; s0 = len(E['status'])
    pg.evaluate("() => resolveNamesToIds(['Nobody Here Again']).catch(() => 0)")
    ok = wait("() => /ESI is down/.test(document.getElementById('sysStrip').innerText)", 10); t_on = _t.time()
    pg.evaluate("() => itRender()"); pg.wait_for_timeout(300)
    g = pg.evaluate("() => document.getElementById('bgSegs').innerText.replace(/\\s+/g, ' ')")
    fn = pg.evaluate("() => (document.querySelector('#intelPanel [data-it-why]') || {}).innerText || ''")
    stl = pg.inner_text('#intelPanel [data-it-status]')
    check(ok and len(E['status']) - s0 == 1 and 'ESI down' in g and fn.startswith("No new kills: EVE's ESI is down") and "kills: EVE's ESI is down" in stl,
          f'ESI down: one /status/ confirms it; the strip, "ESI down", the Feed note, the status line ({len(E["status"]) - s0}, {g!r}, {fn!r})')
    pg.evaluate("() => { it.kf.blk = 3; itRender(); sysStripPaint(); }"); pg.wait_for_timeout(300)
    s4 = strip()
    check('ESI is down' in s4 and 'INTEL-06' not in s4, f'ESI down takes over from the unreadable feed ({s4!r})')
    pg.evaluate("() => { it.kf.blk = 0; zkbUnavailableUntil = Date.now() + 40000; zkbPauseSave(); sysStripPaint(); }"); pg.wait_for_timeout(300)
    lines = pg.evaluate("() => [...document.querySelectorAll('#sysStrip .sys-l')].map(l => l.innerText)")
    check(len(lines) == 2 and 'ESI is down' in lines[0] and lines[1].startswith("zKillboard isn't responding.") and '(ZKB-01)' in lines[1], f'two at once: two lines, ESI first {lines}')
    pg.evaluate("() => { zkbUnavailableUntil = 0; zkbPauseSave(); sysStripPaint(); }")
    pg.wait_for_timeout(int(max(0, t_on + 13.5 - _t.time()) * 1000))
    n_down = len(E['status']) - s0
    check(2 <= n_down <= 3, f'while down, /status/ once a (scaled) minute: {n_down} in 13.5 s (1 + every 6 s)')
    E['down'] = False
    ok = wait("() => !/ESI is down/.test(document.getElementById('sysStrip').innerText)", 10); pg.evaluate("() => bgPaintNow()")
    g = pg.evaluate("() => document.getElementById('bgSegs').innerText.replace(/\\s+/g, ' ')")
    s5 = len(E['status']); pg.wait_for_timeout(7000)
    check(ok and 'ESI ok' in g and len(E['status']) == s5, f'ESI back: the strip and "ESI down" go, no more /status/ ({g!r}, {len(E["status"]) - s5} more)')
    # ---- EVE's daily downtime (the clock moved for the page only) ----
    DT = """(t) => { const real = Date.now; Date.now = () => t[0]; esiDown.on = t[1]; sysLastStrip = null; sysStripPaint(); const s = document.getElementById('sysStrip').innerText; Date.now = real; esiDown.on = false; sysLastStrip = null; sysStripPaint(); return s; }"""
    import calendar as _c
    d = _t.gmtime(); T = lambda h, m: _c.timegm((d.tm_year, d.tm_mon, d.tm_mday, h, m, 0)) * 1000
    a1, a2, a3 = pg.evaluate(DT, [T(10, 56), False]), pg.evaluate(DT, [T(11, 2), True]), pg.evaluate(DT, [T(11, 2), False])
    check("EVE's daily downtime starts in 4:00" in a1 and "EVE's daily downtime (11:00 UTC)" in a2 and 'maintenance' not in a2 and 'downtime' not in a3,
          f'the downtime: "starts in 4:00" at 10:56 UTC; from 11:00 with ESI failing the downtime line; with ESI fine nothing ({a1!r}, {a2!r}, {a3!r})')
    # ---- zKillboard's pause ----
    pg.evaluate("() => { zkbUnavailableUntil = Date.now() + 5000; zkbPauseSave(); sysStripPaint(); }")
    z1 = strip()
    pg.wait_for_function("(z) => document.getElementById('sysStrip').innerText !== z", arg=z1, timeout=4000); z2 = strip()
    check("zKillboard isn't responding. Wait 0:0" in z1 and "pressing again or reloading won't make it sooner. (ZKB-01)" in z1 and z1 != z2, f'zKillboard\'s pause: ZKB-01\'s own words, counting down ({z1!r} -> {z2!r})')
    w = pg.evaluate("() => { window.__sw = 0; const el = document.getElementById('sysStrip'), d = Object.getOwnPropertyDescriptor(Element.prototype, 'innerHTML'); Object.defineProperty(el, 'innerHTML', {set(v){ window.__sw++; d.set.call(this, v); }, get(){ return d.get.call(this); }}); return 1; }")
    pg.wait_for_timeout(2500); writes = pg.evaluate("() => window.__sw")
    ok = wait("() => !/zKillboard isn't responding/.test(document.getElementById('sysStrip').innerText)", 10)
    check(writes == 0 and ok, f"... the line written once (the countdown moves on its own), and gone at the pause's end ({writes} writes while it counted)")
    check(not errs, f'no page errors {errs[:3]}')
    ie = pg.evaluate("() => [it.err, it.note]")
    check(not ie[0], f'Intel shows no error of its own (LESSON #139) {ie}')
    b.close()
'''
exec(compile(_src + _tail, 'outage_check.py', 'exec'), _ns)
print(f"FAILURES: {_ns['fails']}")
sys.exit(1 if _ns['fails'] else 0)
