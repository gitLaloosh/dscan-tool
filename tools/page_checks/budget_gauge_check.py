"""The lookup budgets in the header, and the zKillboard pause counted down (v2026.11.04.4; build queue 012, Project doc
roadmap/budget-gauge-plan.md).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/budget_gauge_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner, 2026-11-03: "add info to the page that lets the user see what their ESI and zKill budgets are. update the number as it
changes ... so i know how quickly (and which actions) my budget's being used"; on the pause: "please show me how long the pause is
and count it down for me" and "they might mistakenly extend the wait time by constantly retrying the search if not given a warning
about doing so"; option A (Analyze stays pressable). ESI by kind of lookup (2026-11-04). Stand-ins only: ESI from pyfa's SDE
(esi_from_sde.py) with made-up rate-limit headers, zKillboard answered by this script (502 or empty), a made-up pilot; never the
real zKillboard or ESI. Checks:
  * the gauge beside the version tag: "zKill 37/100 · ESI ok" from 37 spends kept in this browser; "Used by" in order in the
    panel; amber from 80; at 100 "zKill full m:ss"; the counts survive a reload and a second page in the same browser sees them;
  * a Pilot Analyzer lookup records "Pilot Analyzer" as the caller; the zKillboard budget's own list keeps its old form (numbers);
  * the pause: zKillboard answers 502 (an outage; its own 503 "API result unavailable" is a slow list since v2026.11.06.4, ZKB-06) -> "zKill paused" counting down in the gauge, and the ZKB-01 text in the status line and on
    the Last Kill line says the time and the warning, and counts down; pressing Analyze during the pause sends no zKillboard
    request and doesn't move the pause's end; at its end the messages say zKillboard can be asked again; a second failure ->
    a 2 min pause and the panel says the next wait is 4 min; one answer resets it;
  * ESI: an answer's error limit (40 left -> "ESI 60 errors", amber), a route group low (100 of 600 -> "ESI low"), a 420 with
    Retry-After -> "ESI wait", and answers without headers -> "the page's own count"; the panel's "Last 15 min" by kind;
  * Intel's live kills: only while Intel is on, never counted in the zKillboard budget; a stop -> "Kills stopped 60:00" (the clock rounds up);
  * timers: nothing counting down and the panel closed -> no tick; a hidden tab -> no tick, and none starts there;
  * the panel: opens on a press with the focus on its ✕; Escape, ✕ and a press outside close it, the focus back on the gauge
    (not for the outside press); the gauge keeps the focus when its numbers change;
  * the colours: amber when near, full, paused or stopped, never the Hostile red;
  * a phone: a tap that closes the profile's sheet over the gauge doesn't open the panel (the sheet closes on the press);
  * 1440, 390, 320 px: the worst case (paused, wait and stopped at once) fits beside the version tag, nothing scrolls sideways,
    the gauge is 44 px tall on a phone; no page errors.
"""
import sys, os, re, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from esi_from_sde import handle as esi_handle
from playwright.sync_api import sync_playwright

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok

ST = {'zkb': '503', 'zkb_n': 0, 'esi_h': {}, 'esi_status': None}
CORS = {'access-control-allow-origin': '*'}
class Grab:   # esi_from_sde answers through route.fulfill: catch it, add this run's made-up headers
    def __init__(self, route): self.route = route; self.request = route.request
    def fulfill(self, **kw):
        h = dict(kw.pop('headers', {}) or {}); h.update(CORS); h.update(ST['esi_h'])
        if ST['esi_h']: h['access-control-expose-headers'] = ', '.join(ST['esi_h'].keys())
        if ST['esi_status']: kw['status'] = ST['esi_status']; kw['body'] = '{"error":"slow down"}'
        return self.route.fulfill(headers=h, **kw)
def esi(route):
    if '/universe/ids/' in route.request.url and 'Test Pilot' in (route.request.post_data or ''):
        return route.fulfill(status=200, content_type='application/json', headers=CORS, body=json.dumps({'characters': [{'id': 90000001, 'name': 'Test Pilot'}]}))
    if '/status/' in route.request.url:
        return Grab(route).fulfill(status=200, content_type='application/json', body=json.dumps({'server_version': '3624425', 'players': 1}))
    return esi_handle(Grab(route))
def zkb(route):
    ST['zkb_n'] += 1
    if ST['zkb'] == '503': return route.fulfill(status=502, content_type='text/html', headers=CORS, body='<html>Bad gateway</html>')   # an outage (v2026.11.06.4: its own 503 'unavailable' is a slow list)
    return route.fulfill(status=200, content_type='application/json', headers=CORS, body='[]')
def ctx_page(b, W=1440, ctx=None):
    ctx = ctx or b.new_context(viewport={'width': W, 'height': 800}, is_mobile=W < 600, has_touch=W < 600)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route(re.compile(r'https://esi\.evetech\.net/.*'), esi)
    pg.route(re.compile(r'https://zkillboard\.com/.*'), zkb)
    pg.route(re.compile(r'https://(images\.evetech\.net|fonts\.).*'), lambda r: r.fulfill(status=404, body=''))
    pg.goto('file://' + HTML); pg.wait_for_timeout(400)
    return ctx, pg, errs
SEGS = "() => document.getElementById('bgSegs').innerText.replace(/\\s+/g, ' ').trim()"   # what shows (a phone's short forms are hidden spans)
def segs(pg): return pg.evaluate(SEGS)
def seg_cls(pg): return pg.evaluate("() => [...document.querySelectorAll('#bgSegs .bg-seg')].map(s => s.className.replace('bg-seg', '').trim())")
def seed(pg, n, who=None, extra=''):
    pg.evaluate("""([n, who]) => { const now = Date.now(); localStorage.setItem('dscanZkbBudget', JSON.stringify(Array.from({length: n}, (_, i) => now - 120000 - (n - i) * 1000)));
        localStorage.setItem('dscanZkbWho', JSON.stringify(Array.from({length: n}, (_, i) => [now - 120000 - (n - i) * 1000, who ? who[i % who.length] : 'Other']))); }""", [n, who])
def analyze(pg):
    pg.click('#tabBtnPilot'); pg.fill('#pilotName', 'Test Pilot'); pg.click('#fitBtn')
    pg.wait_for_function("() => !document.getElementById('fitBtn').disabled", timeout=90000)

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('CHROMIUM', '/opt/pw-browsers/chromium'))

    def section_1():
        # ---- the zKillboard count, who used it, kept across reloads and tabs
        ctx, pg, errs = ctx_page(b)
        seed(pg, 37, ['System Analyzer'] * 20 + ['Pilot Analyzer'] * 11 + ['Fleet tab'] * 6); pg.reload(); pg.wait_for_timeout(500)
        s0 = segs(pg)
        check(s0.startswith('zKill 37/100') and 'ESI ok' in s0 and 'Kills' not in s0, f'the gauge from 37 kept spends, Intel off ({s0!r})')
        tag = pg.evaluate("() => { const g = document.getElementById('bgGauge').getBoundingClientRect(), t = document.querySelector('header.hero .build-tag').getBoundingClientRect(); return [g.right <= t.left, Math.abs((g.top + g.bottom) / 2 - (t.top + t.bottom) / 2) < 6]; }")
        check(tag == [True, True], f'the gauge sits beside the version tag, on its line {tag}')
        pg.click('#bgGauge'); pg.wait_for_timeout(200)
        by = pg.evaluate("() => [...document.querySelectorAll('#bgBody .bg-by')][0].innerText.replace(/\\s+/g, ' ')")
        foc = pg.evaluate("() => [document.getElementById('bgPop').hidden, document.activeElement.matches('#bgPop .x-close'), document.getElementById('bgGauge').getAttribute('aria-expanded')]")
        check(by == 'Used by: System Analyzer 20 Pilot Analyzer 11 Fleet tab 6', f'the panel: "Used by" highest first ({by!r})')
        check(foc == [False, True, 'true'], f'the panel opens with the focus on its close button {foc}')
        pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
        foc = pg.evaluate("() => [document.getElementById('bgPop').hidden, document.activeElement.id]")
        check(foc == [True, 'bgGauge'], f'Escape closes it, the focus back on the gauge {foc}')
        pg.click('#bgGauge'); pg.click('#bgPop .x-close'); pg.wait_for_timeout(100)
        foc = pg.evaluate("() => [document.getElementById('bgPop').hidden, document.activeElement.id]")
        check(foc == [True, 'bgGauge'], f'its ✕ closes it, the focus back on the gauge {foc}')
        pg.click('#bgGauge'); pg.mouse.click(300, 600); pg.wait_for_timeout(100)
        check(pg.evaluate("() => document.getElementById('bgPop').hidden"), 'a press outside closes it')
        # the gauge keeps the focus while its numbers change (LESSON #119)
        pg.wait_for_timeout(1300)   # the closed panel's tick stops on its next beat
        t_before = pg.evaluate("() => bgTimer")
        pg.focus('#bgGauge'); pg.evaluate("() => bgZkbWho('Fleet tab')"); pg.wait_for_timeout(200)
        check(pg.evaluate("() => document.activeElement.id") == 'bgGauge' and segs(pg).startswith('zKill 37/100'), f'a changed number keeps the focus on the gauge ({segs(pg)!r})')
        t_after = pg.evaluate("() => bgTimer")
        check(t_before == 0 and t_after == 0, f'a changed number with nothing counting down starts no tick (looked at at once: a tick that stops itself a second later still counts) {[t_before, t_after]}')
        seed(pg, 80); pg.reload(); pg.wait_for_timeout(400)
        check(segs(pg).startswith('zKill 80/100') and seg_cls(pg)[0] == 'warn', f'80 of 100: amber ({segs(pg)!r}, {seg_cls(pg)})')
        seed(pg, 100); pg.reload(); pg.wait_for_timeout(400)
        s1 = segs(pg)
        check(re.match(r'zKill full [0-9]:[0-5]\d', s1) and seg_cls(pg)[0] == 'warn', f'100 of 100: "zKill full m:ss" ({s1!r})')
        # a second page in the same browser sees the same numbers
        pg2 = ctx.new_page(); pg2.route(re.compile(r'https://.*'), lambda r: r.fulfill(status=404, body='')); pg2.goto('file://' + HTML); pg2.wait_for_timeout(400)
        check(segs(pg2).startswith('zKill full'), f'another tab shows the same count ({segs(pg2)!r})')
        pg2.close(); ctx.close()

    def section_2():
        # ---- the pause
        ST['zkb'] = '503'; ST['zkb_n'] = 0
        ctx, pg, errs = ctx_page(b)
        analyze(pg)
        g = segs(pg); st = pg.inner_text('#fitStatus'); lk = pg.inner_text('#lastKillInfo')
        who = pg.evaluate("() => [JSON.parse(localStorage.getItem('dscanZkbWho') || '[]').map(x => x[1]), JSON.parse(localStorage.getItem('dscanZkbBudget') || '[]').every(t => typeof t === 'number')]")
        check(who[0] and set(who[0]) == {'Pilot Analyzer'} and who[1], f'the lookup is recorded as the Pilot Analyzer\'s, the budget list keeps its form {who}')
        check(re.match(r'zKill paused (0:5\d|1:00)', g) and seg_cls(pg)[0] == 'stop', f'502: the gauge says paused and counts ({g!r})')
        rx = r"isn't responding\. Wait (\d):(\d\d) and try again; pressing again or reloading won't make it sooner"
        m1, m2 = re.search(rx, st), re.search(rx, lk)
        check(bool(m1) and '(ZKB-01)' in st, f'the status line says the time and the warning ({st[:160]!r})')
        check(bool(m2) and '(ZKB-01)' in lk, f'so does the Last Kill line ({lk[:120]!r})')
        pg.wait_for_timeout(2200)
        st2 = pg.inner_text('#fitStatus'); m3 = re.search(rx, st2)
        t = lambda m: int(m.group(1)) * 60 + int(m.group(2))
        check(m1 and m3 and 1 <= t(m1) - t(m3) <= 3, f'the message counts down ({m1 and m1.group(1)}:{m1 and m1.group(2)} -> {m3 and m3.group(1)}:{m3 and m3.group(2)})')
        until0 = pg.evaluate("() => JSON.parse(localStorage.getItem('dscanZkbPause')).until"); n0 = ST['zkb_n']
        pg.click('#fitBtn'); pg.wait_for_function("() => !document.getElementById('fitBtn').disabled", timeout=60000); pg.wait_for_timeout(300)
        until1 = pg.evaluate("() => JSON.parse(localStorage.getItem('dscanZkbPause')).until")
        check(ST['zkb_n'] == n0 and until1 == until0, f'Analyze during the pause: no zKillboard request ({ST["zkb_n"] - n0}) and the same end ({until1 - until0} ms)')
        pg.click('#bgGauge'); pg.wait_for_timeout(200)
        note = pg.inner_text('#bgBody')
        check("isn't responding" in note and "doesn't add time" in note and 'next wait is 2 min' in note and '1 failure' in note, f'the panel\'s pause note ({" ".join(note.split())[:200]!r})')
        a = pg.inner_text('#bgBody'); pg.wait_for_timeout(1300); b2 = pg.inner_text('#bgBody')
        check(a != b2, 'the open panel counts down too')
        pg.keyboard.press('Escape')
        # the pause ends
        pg.evaluate("() => { zkbUnavailableUntil = Date.now() + 1200; localStorage.setItem('dscanZkbPause', JSON.stringify({until: zkbUnavailableUntil, streak: zkbFailStreak})); }")
        pg.wait_for_timeout(2600)
        st3, lk3, g3 = pg.inner_text('#fitStatus'), pg.inner_text('#lastKillInfo'), segs(pg)
        check('zKillboard can be asked again' in st3 and 'zKillboard can be asked again' in lk3 and g3.startswith('zKill 1/100'), f'at its end: "can be asked again", the gauge back to the count ({st3[:80]!r}, {g3!r})')
        # a second failure: 2 min, the next 4 min
        analyze(pg); g4 = segs(pg)
        pg.click('#bgGauge'); pg.wait_for_timeout(200); note = ' '.join(pg.inner_text('#bgBody').split()); pg.keyboard.press('Escape')
        check(re.match(r'zKill paused (1:5\d|2:00)', g4) and 'next wait is 4 min' in note and '2 failures in a row' in note, f'a second failure: 2 min, the next 4 ({g4!r})')
        # one answer resets it
        ST['zkb'] = 'ok'
        pg.evaluate("() => { zkbUnavailableUntil = 0; localStorage.setItem('dscanZkbPause', JSON.stringify({until: 0, streak: zkbFailStreak})); }")
        analyze(pg)
        check(pg.evaluate("() => JSON.parse(localStorage.getItem('dscanZkbPause')).streak") == 0 and segs(pg).startswith('zKill'), f'one answer resets the failures ({segs(pg)!r})')
        check(not errs, f'no page errors {errs}')
        ctx.close()

    def section_3():
        # ---- ESI's numbers
        ctx, pg, errs = ctx_page(b)
        TYPES = iter([587, 588, 589, 590, 591, 592])   # a type not looked up yet each time, so ESI is asked (not the page's cache)
        def esi_after(h, status=None):
            ST['esi_h'] = h; ST['esi_status'] = status
            pg.evaluate("(id) => getType(id).catch(() => null)", next(TYPES)); pg.wait_for_timeout(300)
            ST['esi_h'] = {}; ST['esi_status'] = None
            return segs(pg)
        pg.evaluate("() => clearDscanCache()"); pg.wait_for_timeout(200)
        s = esi_after({'x-esi-error-limit-remain': '40', 'x-esi-error-limit-reset': '30'})
        check('ESI 60 errors' in s and seg_cls(pg)[1] == 'warn', f'error limit 40 left: "ESI 60 errors", amber ({s!r})')
        pg.click('#bgGauge'); pg.wait_for_timeout(150); body = ' '.join(pg.inner_text('#bgBody').split()); pg.keyboard.press('Escape')
        check('60 of 100 errors' in body and "ESI's own count" in body and 'refuses every request' in body and 'Item data' in body, f'the panel: ESI\'s count, the 420 note, by kind ({body[body.find("ESI"):][:200]!r})')
        pg.evaluate("() => { localStorage.removeItem('dscanEsiUse'); bgEsiPend = null; }")
        s = esi_after({'x-ratelimit-group': 'universe', 'x-ratelimit-limit': '600/15m', 'x-ratelimit-remaining': '100', 'x-ratelimit-used': '500'})
        check('ESI low' in s and seg_cls(pg)[1] == 'warn', f'a route group at 100 of 600: "ESI low" ({s!r})')
        pg.click('#bgGauge'); pg.wait_for_timeout(150); body = ' '.join(pg.inner_text('#bgBody').split()); pg.keyboard.press('Escape')
        check('universe is down to 100 of 600 per 15 min' in body, f'the panel names the group ({body[body.find("ESI"):][:220]!r})')
        pg.evaluate("() => { localStorage.removeItem('dscanEsiUse'); bgEsiPend = null; }")
        s = esi_after({'retry-after': '30', 'x-esi-error-limit-remain': '0', 'x-esi-error-limit-reset': '30'}, 420)
        check(re.search(r'ESI wait 0:(2\d|30)', s) and seg_cls(pg)[1] == 'stop', f'a 420 with Retry-After 30: "ESI wait" ({s!r})')
        pg.evaluate("() => { localStorage.removeItem('dscanEsiUse'); bgEsiPend = null; }")
        s = esi_after({})
        pg.click('#bgGauge'); pg.wait_for_timeout(150); body = ' '.join(pg.inner_text('#bgBody').split()); pg.keyboard.press('Escape')
        check('ESI ok' in s and "The page's own count" in body, f'answers without headers: the page\'s own count ({s!r})')
        kept = pg.evaluate("() => { bgEsiFlush(); const u = JSON.parse(localStorage.getItem('dscanEsiUse') || 'null'); return !!u && Object.values(u.m).some(k => k.types); }")
        check(kept, 'ESI\'s counts are saved in this browser (dscanEsiUse), by kind')
        # Intel's live kills
        pg.evaluate("() => { it.on = true; bgPaint(); }"); pg.wait_for_timeout(150)
        check('Kills ok' in segs(pg), f'Intel on: Kills ok ({segs(pg)!r})')
        z0 = pg.evaluate("() => zkbBudgetRead().length"); pg.evaluate("() => { for(let i = 0; i < 5; i++) bgR2Note(); }")
        check(pg.evaluate("() => zkbBudgetRead().length") == z0, 'Intel\'s live-kill reads are not counted in the zKillboard budget (a separate host and gate)')
        pg.evaluate("() => itR2Stop('status 429')"); pg.wait_for_timeout(150)
        s = segs(pg)
        check(re.search(r'Kills stopped (59:5\d|60:00)', s) and seg_cls(pg)[2] == 'stop', f'a stop: "Kills stopped 59:5x" ({s!r})')
        pg.evaluate("() => { it.on = false; localStorage.removeItem('dscanR2Stop'); it.r2stop = null; bgPaint(); }"); pg.wait_for_timeout(150)
        check('Kills' not in segs(pg), f'Intel off: no Kills part ({segs(pg)!r})')
        # the colours: amber, never the Hostile red
        col = pg.evaluate("""() => { const t = document.createElement('span'); t.className = 'bg-seg stop'; document.getElementById('bgSegs').appendChild(t); const c = getComputedStyle(t).color; t.remove();
            const probe = (v) => { const d = document.createElement('i'); d.style.color = `var(${v})`; document.body.appendChild(d); const x = getComputedStyle(d).color; d.remove(); return x; };
            return [c, probe('--amber'), probe('--danger')]; }""")
        check(col[0] == col[1] and col[0] != col[2], f'paused/stopped is amber, not the Hostile red {col}')
        # timers
        pg.evaluate("() => { localStorage.removeItem('dscanEsiUse'); bgEsiPend = null; localStorage.removeItem('dscanZkbPause'); zkbUnavailableUntil = 0; bgPaint(); }"); pg.wait_for_timeout(1500)
        check(pg.evaluate("() => bgTimer") == 0, 'nothing counting down, the panel closed: no tick running')
        hid = pg.evaluate("() => { Object.defineProperty(document, 'hidden', {configurable: true, get: () => true}); document.dispatchEvent(new Event('visibilitychange')); zkbUnavailableUntil = Date.now() + 60000; zkbPauseSave(); bgTickStart(true); return bgTimer; }")
        pg.wait_for_timeout(1200)
        check(hid == 0 and pg.evaluate("() => bgTimer") == 0, f'a hidden tab: no tick, and none starts there (at once: {hid})')
        pg.evaluate("() => { Object.defineProperty(document, 'hidden', {configurable: true, get: () => false}); document.dispatchEvent(new Event('visibilitychange')); }"); pg.wait_for_timeout(1200)
        check(pg.evaluate("() => bgTimer") != 0 and segs(pg).startswith('zKill paused'), f'shown again: the countdown carries on ({segs(pg)!r})')
        check(not errs, f'no page errors {errs}')
        ctx.close()

    def section_4():
        # ---- the worst case at three widths
        for W in (1440, 390, 320):
            ctx, pg, errs = ctx_page(b, W)
            pg.evaluate("() => { const now = Date.now(); localStorage.setItem('dscanZkbPause', JSON.stringify({until: now + 599000, streak: 4})); localStorage.setItem('dscanR2Stop', JSON.stringify({until: now + 3599000, why: 'x'})); localStorage.setItem('dscanEsiUse', JSON.stringify({m: {}, err: null, grp: {}, wait: now + 59000})); }")
            pg.reload(); pg.wait_for_timeout(400); pg.evaluate("() => { it.on = true; bgPaint(); }"); pg.wait_for_timeout(200)
            r = pg.evaluate("""() => { const g = document.getElementById('bgGauge').getBoundingClientRect(), t = document.querySelector('header.hero .build-tag').getBoundingClientRect(), h = document.querySelector('header.hero').getBoundingClientRect(), n = document.querySelector('header.hero h1').getBoundingClientRect();
                return {gap: t.left - g.right, inside: t.right <= h.right + 0.5 && g.left >= h.left - 0.5, h: g.height, sw: document.documentElement.scrollWidth, overName: g.bottom > n.top && g.left < n.right}; }""")
            check(r['gap'] > 0 and r['inside'] and r['sw'] <= W and not r['overName'] and (W >= 600 or abs(r['h'] - 44) < 1), f'{W}: paused, wait and stopped at once fit beside the tag ({r}; {segs(pg)!r})')
            if W < 600:
                # the profile's sheet closes on the press: that tap's click must not open the panel under it (the gauge sits there on a phone)
                pg.evaluate("() => { localStorage.removeItem('dscanZkbPause'); localStorage.removeItem('dscanR2Stop'); }"); pg.reload(); pg.wait_for_timeout(400)
                pg.tap('#profileBtn', position={'x': 12, 'y': 14}); pg.wait_for_timeout(300)
                gb = pg.evaluate("() => { const r = document.getElementById('bgGauge').getBoundingClientRect(); return [r.left + 10, r.top + r.height / 2]; }")
                pg.tap('#sideBackdrop', position={'x': gb[0], 'y': gb[1]}); pg.wait_for_timeout(300)
                st = pg.evaluate("() => [document.getElementById('profilePanel').hidden, document.getElementById('bgPop').hidden]")
                pg.tap('#bgGauge'); pg.wait_for_timeout(200); t1 = pg.evaluate("() => document.getElementById('bgPop').hidden")
                pg.keyboard.press('Escape'); pg.focus('#bgGauge'); pg.keyboard.press('Enter'); pg.wait_for_timeout(200); k1 = pg.evaluate("() => document.getElementById('bgPop').hidden")
                check(st == [True, True] and t1 is False and k1 is False, f'{W}: a tap that closes the profile over the gauge closes only the profile; a tap or Enter on the gauge opens it {st} {t1} {k1}')
            check(not errs, f'{W}: no page errors {errs}')
            ctx.close()
    for fn, what in ((section_1, 'the zKillboard count, who used it, kept across reloads and tabs'), (section_2, 'the pause'), (section_3, "ESI's numbers"), (section_4, 'the worst case at three widths'),):
        try: fn()
        except Exception as e: check(False, f'{what}: the check stopped: {str(e).splitlines()[0][:160]}')   # a crash is a FAIL, the next section still runs
    b.close()
print(f'FAILURES: {fails}')
