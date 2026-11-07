"""zKillboard lists that are slow, not down (v2026.11.06.4, build queue 014; Project doc roadmap/zkb-slow-lists-plan.md).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/zkb_slow_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner, 2026-11-05: "the results are inconsistent but tend to lean toward one call timing out and preventing the rest from being
done." Never the real zKillboard: the page's own fetch() to zkillboard.com is answered in the page by a stand-in that follows
zKillboard's rule as its source has it (view/api.php, cron/9.queueAPI.php): a list takes T to work out, a request waits for it at
most a minute and then gets 503 "API result unavailable", asking while it's being worked out joins that work, and a finished list is
kept a minute. Its content comes from sa_mocks.py (made-up pilots and alliances). Every time is a tenth of the page's and zKillboard's
(the page is copied with ZKB_TIMEOUT_MS, ZKB_SERVER_WAIT_MS, ZKB_SLOW_RETRY_MS and ZKB_SLOW_NOTE_MS divided by 10; the starts stay
1 s apart). Checks:
  * the gate: never more than 3 in the air, starts 1 s apart; a list that takes 75 s: one 503, one retry 30 s later, answered;
    one that never finishes: exactly 2 requests and ZKB-06, no page pause; the 65 s backstop (no answer at all) is slow too, not a
    pause; three slow lists in a row pause the page; 502, 429, 420, 403, a redirect to blocked.json and an answer the browser
    can't read pause the page after 1 request; the budget counts every request, retries too;
  * the Fleet tab (48 pilots, 7 alliance-and-hull pairs): one list slow for 30 s: the workers spread over the other lists meanwhile,
    all 48 load; 75 s: the slow list's rows show the amber icon, "trying again in" counting down on hover, the Fit cell's countdown,
    "N waiting: zKillboard is slow" in the summary, then all load; never: its rows the red icon with ZKB-06, the rest load, no pause,
    the summary says so, a row's Load asks again; on a phone the icon is on the card's last line, nothing off the page;
  * D1: common fits ask exactly pastSeconds/604800/ first, all of history only for short weeks; D2: a list carrying whole
    killmails is read without asking ESI for them;
  * the Pilot Analyzer with a slow list: its busy line "zKillboard is slow right now: wait 0:0N", counting down; no pause.
"""
import sys, os, re, json, time, hashlib, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from playwright.sync_api import sync_playwright
import sa_mocks as M

SRC = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok

# the page, a tenth of the time
S = 10
page = open(SRC, encoding='utf-8').read()
for a, b in (('const ZKB_TIMEOUT_MS = 65000;', f'const ZKB_TIMEOUT_MS = {65000 // S};'), ('const ZKB_SERVER_WAIT_MS = 60000;', f'const ZKB_SERVER_WAIT_MS = {60000 // S};'),
             ('ZKB_SLOW_RETRY_MS = 30000,', f'ZKB_SLOW_RETRY_MS = {30000 // S},'), ('ZKB_SLOW_NOTE_MS = 10000;', f'ZKB_SLOW_NOTE_MS = {10000 // S};')):
    if page.count(a) != 1: print(f'FAIL the page has no {a!r} to scale'); print('FAILURES: 1'); sys.exit(1)
    page = page.replace(a, b)
TMP = tempfile.mkdtemp(prefix='zkbslow'); HTML = os.path.join(TMP, 'index.html')
open(HTML, 'w', encoding='utf-8').write(page)

# zKillboard's rule, in the page (a route handler can't hold an answer back without holding up every other one)
STAND_IN = """(() => {
  const Z = window.__zk = {T: {}, mode: {}, lists: {}, calls: [], live: 0, maxLive: 0, done: {}, pend: {}, WAIT: %d, KEEP: %d};
  const real = window.fetch.bind(window);
  window.fetch = function(u, init){
    const url = String(u && u.url || u);
    if(!/^https:\\/\\/zkillboard\\.com\\//.test(url)) return real(u, init);
    const path = url.split('/api/')[1] || url, now = Date.now(), sig = init && init.signal;
    Z.calls.push([path, now]); Z.live++; Z.maxLive = Math.max(Z.maxLive, Z.live);
    return new Promise((res, rej) => {
      let over = false; const fin = (f) => { if(over) return; over = true; Z.live--; f(); };
      const m = Z.mode[path] !== undefined ? Z.mode[path] : Z.mode['*'];
      const answer = () => Z.lists[path] ? Promise.resolve(new Response(JSON.stringify(Z.lists[path]), {status: 200, headers: {'content-type': 'application/json'}})) : real(url);
      if(sig) sig.addEventListener('abort', () => fin(() => rej(new DOMException('The operation was aborted.', 'AbortError'))));
      if(m === 'unreadable') return setTimeout(() => fin(() => rej(new TypeError('Failed to fetch'))), 50);
      if(typeof m === 'number') return setTimeout(() => fin(() => res(new Response('<html>refused</html>', {status: m}))), 50);
      if(m === 'blocked') return setTimeout(() => fin(() => { const r = new Response('{"error":"blocked"}', {status: 200}); Object.defineProperty(r, 'redirected', {value: true}); Object.defineProperty(r, 'url', {value: 'https://zkillboard.com/api/blocked.json'}); res(r); }), 50);
      if(m === 'hang') return;   // no answer at all: only the page's own backstop ends it
      if(Z.done[path] && now - Z.done[path] <= Z.KEEP) return setTimeout(() => fin(() => answer().then(res, rej)), 30);
      let job = Z.pend[path];
      if(!job){ const t = Z.T[path] !== undefined ? Z.T[path] : (Z.T['*'] || 0); job = Z.pend[path] = {end: t < 0 ? Infinity : now + t}; }
      const t = setTimeout(() => {
        if(Date.now() >= job.end){ if(Z.pend[path] === job){ Z.done[path] = job.end; delete Z.pend[path]; } fin(() => answer().then(res, rej)); }
        else fin(() => res(new Response('{"error":"API result unavailable, please try again later"}', {status: 503, headers: {'content-type': 'application/json'}})));
      }, Math.max(0, Math.min(job.end - now, Z.WAIT)));
      if(sig) sig.addEventListener('abort', () => clearTimeout(t));
    });
  };
})();""" % (60000 // S, 60000 // S)

# the fleet (fleet_fit_budget_check.py's)
B = M.byname
crts = M._crts; void = M._void
npact = [i for i, v in M.PILOTS.items() if v[1] in (98000007, 98000008)]
qhc = [i for i, v in M.PILOTS.items() if v[1] == 98000012]
tpi = [i for i, v in M.PILOTS.items() if v[1] == 98000030]
npc = [i for i, v in M.PILOTS.items() if v[1] == 1000167]
PAIRS = [([crts[0], crts[1]] + crts[11:21], 'Curse'), ([crts[7]] + crts[21:26], 'Vedmak'), ([void[0]] + void[3:12], 'Loki'),
         ([M.THIRD_PILOT, M.ANNEX_PILOT, M.LONG_PILOT], 'Loki'), (npact[2:10], 'Rifter'), (qhc[:5], 'Curse'), (tpi[:2], 'Sabre')]
_k = [9850000]
def kill(members, victim='Megathron'):
    _k[0] += 1; k = _k[0]
    att = [dict(M.aff(cid), ship_type_id=B[hull], weapon_type_id=B['Acolyte II'], damage_done=9000 - 150 * (i // 2) if i % 7 else 300 + i, final_blow=i == 3, security_status=0) for i, (cid, hull) in enumerate(members)]
    M.KM[k] = {'killmail_id': k, 'killmail_time': M._diso(1, 20), 'solar_system_id': 30004759, 'attackers': att,
               'victim': {'character_id': M.pick(98000013), 'corporation_id': 98000013, 'ship_type_id': B[victim], 'damage_taken': sum(a['damage_done'] for a in att), 'items': [], 'position': {'x': 0, 'y': 0, 'z': 0}}}
    M.H[k] = hashlib.sha1(str(k).encode()).hexdigest(); return k
BIG = [(c, h) for ps, h in PAIRS for c in ps] + [(c, 'Ferox') for c in npc[:2]]
BIGK = kill(BIG)
CURSE = f"losses/allianceID/{M.ORGS[M.PILOTS[crts[0]][1]][3]}/shipTypeID/{B['Curse']}/pastSeconds/604800/"   # 12 pilots, 5 losses this week
CURSE_IDS = set([crts[0], crts[1]] + crts[11:21])
ESI_KM = []
def esi(route):
    if '/killmails/' in route.request.url: ESI_KM.append(route.request.url)
    return M.esi(route)

def zk(pg, **kw): pg.evaluate("(kw) => { const Z = window.__zk; for(const [k, v] of Object.entries(kw)) Object.assign(Z[k], v); }", kw)
def calls(pg, path=None): return [c for c in pg.evaluate("() => window.__zk.calls") if path is None or c[0] == path]
def open_kill(pg, k):
    pg.evaluate(f"() => fkOpen({k}, '{M.H[k]}', null, null, {{from: 'intel', km: {json.dumps(M.KM[k])}}})")
    pg.wait_for_function("() => document.querySelector('#fleetPanel .fk-card') && !fk.checking && fk.members.length && !fk.members.some(m => m.state === 'check')", timeout=60000); pg.wait_for_timeout(300)
def all_in(pg, timeout=120000):
    pg.wait_for_function("() => fk.members.length && fk.members.every(m => m.state === 'done' || (m.state === 'later' && m.fail)) && !fk.members.some(m => m.ownBusy)", timeout=timeout); pg.wait_for_timeout(400)
ST = """() => { const r = [...document.querySelectorAll('#fleetPanel .fk-card .fk-r:not(.fk-rh)')].map(r => { const b = r.querySelector('button.pr-row'), i = b.querySelector(':scope > .fk-st'), f = r.querySelector('.fk-fit button');
    return {id: +((r.querySelector('[data-fk-load]') || {}).dataset || {}).fkLoad || 0, pilot: b.dataset.fkPilot, st: i ? i.className.replace('fk-st', '').trim() : '', why: i ? i.title : '', label: i ? i.getAttribute('aria-label') : '', role: i ? i.getAttribute('role') : '',
      fit: f ? [f.disabled, f.textContent.trim(), f.title] : null, text: [...b.querySelectorAll('.fk-src')].map(e => e.textContent).join('|')}; });
  return {rows: r, ctx: ((document.querySelector('#fleetPanel .fk-sum:not(.fk-vic) .pr-head .ctx') || {}).textContent || ''), paused: zkbUnavailableUntil > Date.now(),
    states: fk.members.reduce((a, m) => (a[m.state + (m.fail ? '!' : '')] = (a[m.state + (m.fail ? '!' : '')] || 0) + 1, a), {}),
    curse: fk.members.filter(m => (%s).includes(m.id)).map(m => m.state + (m.fail ? '!' : ''))}; }""" % json.dumps(sorted(CURSE_IDS))

with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    def new_page(w=1440):
        ctx = b.new_context(bypass_csp=True, viewport={'width': w, 'height': 1000}, is_mobile=w < 600, has_touch=w < 600)
        ctx.add_init_script(STAND_IN)
        ctx.route(re.compile(r'https://esi\.evetech\.net/.*'), esi)
        ctx.route(re.compile(r'https://zkillboard\.com/.*'), M.zkb)
        ctx.route(re.compile(r'https://(images\.evetech\.net|fonts\.).*'), lambda r: r.fulfill(status=404, body=''))
        pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto('file://' + HTML); pg.wait_for_timeout(400)
        return ctx, pg
    def fresh(pg):   # a clean gate between the cases on one page
        pg.evaluate("() => { for(const k of ['dscanZkbPause', ZKB_SLOW_KEY, ZKB_BUDGET_KEY, 'dscanZkbWho']) try{ localStorage.removeItem(k); }catch(e){} zkbUnavailableUntil = 0; zkbFailStreak = 0; zkbSlowRun.clear(); zkbMem.clear && zkbMem.clear(); const Z = window.__zk; Z.calls.length = 0; Z.maxLive = 0; for(const k of ['T', 'mode', 'lists', 'done', 'pend']) Z[k] = {}; }")
    GET = "async (urls) => Promise.all(urls.map(u => zkbFetch(`${ZKB}/${u}`).then(r => ['ok', r.status], e => ['err', e.code || e.name, !!e.zkbUnavailable, !!e.zkbSlow, !!e.final, e.message])))"

    try:
        # ---- the gate
        ctx, pg = new_page()
        fresh(pg); zk(pg, T={'*': 4000})
        t0 = time.time(); r = pg.evaluate(GET, [f'losses/characterID/{90000200 + i}/' for i in range(6)]); dt = time.time() - t0
        c = calls(pg); st = sorted(x[1] for x in c); gap = min(y - x for x, y in zip(st, st[1:]))
        mx = pg.evaluate("() => window.__zk.maxLive")
        check(all(x[0] == 'ok' for x in r) and len(c) == 6 and mx == 3 and gap >= 950 and dt < 12, f'6 slow lists asked at once: at most 3 in the air ({mx}), starts {gap} ms apart at least, all answered in {dt:.1f} s (not one after another: 6 x 4 s)')
        # a list zKillboard couldn't finish: that list only; the next ask for it is its one retry, 30 s after, shared by every caller
        fresh(pg); u = 'losses/allianceID/99000005/shipTypeID/29990/'; zk(pg, T={u: 7500})
        r = pg.evaluate(GET, [u, u]); r2 = pg.evaluate(GET, [u]); c = calls(pg, u)
        check(r[0][:2] == ['err', 'ZKB-06'] and not r[0][4] and r[1] == r[0] and r2[0][0] == 'ok' and len(c) == 2 and 8500 <= c[1][1] - c[0][1] <= 9800 and not pg.evaluate("() => zkbUnavailableUntil > Date.now()"),
              f'a list that takes 75 s: 503 at 60 s for both callers (one request), the next ask waits to 30 s after and is answered, no pause ({r[0][1:5]}, {r2}, {[x[1] - c[0][1] for x in c]} ms)')
        check(pg.evaluate("(u) => !zkbSlowGet(`${ZKB}/${u}`) && !(localStorage.getItem(ZKB_SLOW_KEY) || '').includes(u)", u), 'its slow record is gone once it answered')
        fresh(pg); u = 'losses/allianceID/99000006/shipTypeID/29990/'; zk(pg, T={u: -1})
        b0 = pg.evaluate("() => zkbBudgetRead().length")
        r1 = pg.evaluate(GET, [u]); r2 = pg.evaluate(GET, [u]); r3 = pg.evaluate(GET, [u]); c = calls(pg, u)
        rec = pg.evaluate("(u) => JSON.parse(localStorage.getItem(ZKB_SLOW_KEY) || '{}')[`${ZKB}/${u}`]", u)
        check(r1[0][1] == 'ZKB-06' and not r1[0][4] and r2[0][1] == 'ZKB-06' and r2[0][4] and r3[0][1] == 'ZKB-06' and r3[0][4] and len(c) == 2 and not pg.evaluate("() => zkbUnavailableUntil > Date.now()") and rec and rec['n'] == 2,
              f'a list that never finishes: exactly 2 requests, then ZKB-06 without asking (kept in this browser, shared by tabs), no page pause ({len(c)} requests, {r1[0][1:5]} {r2[0][1:5]}, {rec})')
        check(pg.evaluate("() => zkbBudgetRead().length") - b0 == 2, f'the budget counts both, the retry too')
        r4 = pg.evaluate("async (u) => zkbFetch(`${ZKB}/${u}`, {again: true}).then(() => 'ok', e => e.code)", u)
        check(len(calls(pg, u)) == 3 and r4 == 'ZKB-06' and not pg.evaluate("() => zkbUnavailableUntil > Date.now()"), f'pressing again (o.again) asks it afresh, still no pause: one list slow again is not zKillboard swamped ({len(calls(pg, u))} requests, {r4})')
        fresh(pg); u = 'losses/characterID/90000300/'; zk(pg, mode={u: 'hang'})
        t0 = time.time(); r = pg.evaluate(GET, [u]); dt = time.time() - t0; r2 = pg.evaluate(GET, [u]); c = calls(pg, u)
        check(r[0][1] == 'ZKB-06' and not r[0][4] and r2[0][1] == 'ZKB-06' and r2[0][4] and len(c) == 2 and not pg.evaluate("() => zkbUnavailableUntil > Date.now()") and 6 <= dt <= 8,
              f'no answer at all: the 65 s backstop is slow, not down; its retry the same, then ZKB-06; no pause ({len(c)} requests, the first given up at {dt:.1f} s)')
        fresh(pg); U = [f'losses/characterID/{90000400 + i}/' for i in range(3)]; zk(pg, T={x: -1 for x in U})
        r = pg.evaluate(GET, U)
        check(pg.evaluate("() => zkbUnavailableUntil > Date.now()") and any(x[1] == 'ZKB-01' for x in r) and len(calls(pg)) == 3, f'three slow lists in a row pause the page ({[x[1] for x in r]})')
        for m in (502, 429, 420, 403, 'blocked', 'unreadable'):
            fresh(pg); zk(pg, mode={'*': m})
            r = pg.evaluate(GET, [f'losses/characterID/{90000500 + i}/' for i in range(4)])
            check(len(calls(pg)) == 1 and all(x[1] == 'ZKB-01' and x[2] for x in r) and pg.evaluate("() => zkbUnavailableUntil > Date.now()"),
                  f'{m}: the page pauses after 1 request, the other 3 not sent ({len(calls(pg))} requests, {[x[1] for x in r]})')
        # D2: a list that carries whole killmails needs no ESI reads; stubs still do
        fresh(pg)
        vl = M.FLEET_LOSSES[(M.VOIDR, 'Loki')]; wk = f"losses/allianceID/{M.VOIDR}/shipTypeID/{B['Loki']}/pastSeconds/604800/"
        zk(pg, lists={wk: [dict(M.KM[k], zkb={'hash': M.H[k]}) for k in vl]})
        ESI_KM.clear(); f1 = pg.evaluate("async ([a, h]) => { const r = await saHullFits({kind: 'alliance', id: a}, h); return r && !r.none && r.variants ? r.variants.length : JSON.stringify(Object.keys(r || {})); }", [M.VOIDR, B['Loki']])
        n1 = len(ESI_KM)
        cl = M.FLEET_LOSSES[(M.CRTS, 'Curse')]; wk2 = f"losses/allianceID/{M.CRTS}/shipTypeID/{B['Curse']}/pastSeconds/604800/"
        zk(pg, lists={wk2: [{'killmail_id': k, 'zkb': {'hash': M.H[k]}} for k in cl]})
        ESI_KM.clear(); pg.evaluate("async ([a, h]) => { await saHullFits({kind: 'alliance', id: a}, h); }", [M.CRTS, B['Curse']]); n2 = len(ESI_KM)
        check(f1 and n1 == 0 and n2 == len(cl) and [c[0] for c in calls(pg)] == [wk, wk2], f'D2: a list of whole killmails is read without ESI ({n1} ESI reads, {f1} variants); a list of IDs reads each ({n2} of {len(cl)}); D1: exactly pastSeconds/604800/ ({[c[0] for c in calls(pg)]})')
        ctx.close()

        # ---- the Fleet tab
        # one list 30 s: the other workers take other lists meanwhile; all load
        ctx, pg = new_page(); open_kill(pg, BIGK); zk(pg, T={CURSE: 3000})
        pg.click('#fleetPanel [data-fk-loadall]'); pg.wait_for_function("() => window.__zk.calls.length", timeout=10000)
        pg.wait_for_timeout(2600)
        c = calls(pg); seen = {x[0] for x in c}
        check(c[0][0] == CURSE and len(seen) >= 3, f'one list 30 s: while it works the other workers ask other lists ({len(seen)} lists asked in 2.6 s)')
        all_in(pg); R = pg.evaluate(ST)
        check(R['states'] == {'done': 48} and len(calls(pg, CURSE)) == 1 and not R['paused'], f'... all 48 load, the slow list asked once, no pause ({R["states"]})')
        ctx.close()
        # 75 s: amber icons and countdowns while it waits, then all load
        ctx, pg = new_page(); open_kill(pg, BIGK); zk(pg, T={CURSE: 7500})
        pg.click('#fleetPanel [data-fk-loadall]')
        pg.wait_for_function("() => document.querySelector('#fleetPanel .fk-card .pr-row > .fk-st.slow')", timeout=20000); pg.wait_for_timeout(400)
        R = pg.evaluate(ST); sl = [r for r in R['rows'] if r['st'] == 'slow']
        w = sl[0]['why'] if sl else ''
        mm = re.match(r'zKillboard is slow right now: trying again in 0:0(\d)\.$', w)
        check(len(sl) == 12 and {r['pilot'] for r in sl} == {M.PILOTS[i][0] for i in CURSE_IDS} and mm and all(r['label'] == r['why'] and r['role'] == 'img' for r in sl),
              f'75 s: every pilot on that list has the amber icon, "trying again in" on hover and for screen readers ({len(sl)} rows, {w!r})')
        check(all(r['fit'] and r['fit'][0] and re.match(r'0:0\d$', r['fit'][1]) and re.match(r'Trying again in 0:0\d$', r['fit'][2]) for r in sl) and not any(r['text'] for r in sl),
              f'... the Fit cell counts down to the retry, no text under the hull {sl[0]["fit"] if sl else None}')
        check(re.search(r' · 12 waiting: zKillboard is slow$', R['ctx']), f'... the summary says it once ({R["ctx"]!r})')
        pg.wait_for_timeout(1300); w2 = pg.evaluate("() => document.querySelector('#fleetPanel .fk-card .pr-row > .fk-st.slow').title")
        m2 = re.match(r'.*0:0(\d)\.$', w2)
        check(mm and m2 and int(m2.group(1)) < int(mm.group(1)), f'... the hover counts down ({w!r} -> {w2!r})')
        all_in(pg); R = pg.evaluate(ST)
        check(R['states'] == {'done': 48} and len(calls(pg, CURSE)) == 2 and not R['paused'] and not any(r['st'] for r in R['rows']), f'... then all 48 load: 2 requests for it, no pause, no icons left ({R["states"]})')
        ctx.close()
        # never: red icons with ZKB-06, the rest load, no pause; a row's Load asks again
        ctx, pg = new_page(); open_kill(pg, BIGK); zk(pg, T={CURSE: -1})
        b0 = pg.evaluate("() => zkbBudgetRead().length")
        pg.click('#fleetPanel [data-fk-loadall]'); all_in(pg); R = pg.evaluate(ST)
        er = [r for r in R['rows'] if r['st'] == 'err']
        check(R['states'] == {'done': 36, 'later!': 12} and len(calls(pg, CURSE)) == 2 and not R['paused'] and len(er) == 12
              and all(r['why'] == "zKillboard couldn't load this list. Try again later. (ZKB-06)" and r['fit'] == [False, 'Load', 'Load fit'] for r in er),
              f'never: exactly 2 requests for it, its 12 rows the red icon with ZKB-06 and Load, the other 36 loaded, no pause ({R["states"]}, {er[0]["why"] if er else None!r})')
        check(re.search(r" · 12 not loaded: zKillboard couldn't load their list$", R['ctx']), f'... the summary ({R["ctx"]!r})')
        check(pg.evaluate("() => zkbBudgetRead().length") - b0 == len(calls(pg)), f'... the budget counts every request ({len(calls(pg))})')
        pg.click(f'#fleetPanel [data-fk-load="{er[0]["id"]}"]'); pg.wait_for_timeout(300)
        pg.wait_for_function(f"() => !['wait', 'load'].includes(fk.members.find(m => m.id === {er[0]['id']}).state)", timeout=60000)
        check(len(calls(pg, CURSE)) == 4, f"... a row's Load asks that list afresh, with its one retry ({len(calls(pg, CURSE))} requests)")
        ctx.close()
        # a phone
        ctx, pg = new_page(390); open_kill(pg, BIGK); zk(pg, T={CURSE: -1})
        pg.click('#fleetPanel [data-fk-loadall]'); all_in(pg)
        L = pg.evaluate("""() => { const b = [...document.querySelectorAll('#fleetPanel .fk-card button.pr-row')].find(b => b.querySelector('.fk-st.err'));
          return [document.documentElement.scrollWidth, b && b.querySelector(':scope > .fk-st.err').checkVisibility(), b && b.querySelector('.pr-mob .fk-st.err').checkVisibility(),
                  [...document.querySelectorAll('#fleetPanel *')].filter(e => { const r = e.getBoundingClientRect(); return e.checkVisibility() && r.width && (r.right > innerWidth + 1 || r.left < -1); }).length]; }""")
        check(L[0] <= 390 and L[1] is False and L[2] is True and L[3] == 0, f'390 px: the icon on the card\'s last line (not its row cell), nothing off the page {L}')
        ctx.close()

        # ---- the Pilot Analyzer: a slow list says so on the busy line, counting down; no pause
        ctx, pg = new_page(); zk(pg, T={'*': 4000})
        nm = M.PILOTS[crts[0]][0]
        pg.click('#tabBtnPilot'); pg.fill('#pilotName', nm); pg.click('#fitBtn')
        pg.wait_for_function("() => /zKillboard is slow right now: wait 0:0\\d/.test(document.querySelector('#pilotBusy .busy-detail').textContent)", timeout=20000)
        d1 = pg.inner_text('#pilotBusy .busy-detail'); pg.wait_for_timeout(1200); d2 = pg.inner_text('#pilotBusy .busy-detail')
        check(d1 != d2 and d2.startswith('zKillboard is slow right now: wait 0:0'), f'the Pilot Analyzer: after 10 s the busy line says zKillboard is slow, counting down ({d1!r} -> {d2!r})')
        pg.wait_for_function("() => !document.getElementById('fitBtn').disabled", timeout=90000); pg.wait_for_timeout(300)
        st = pg.inner_text('#fitStatus')
        check(not pg.evaluate("() => zkbUnavailableUntil > Date.now()") and 'ZKB-' not in st and not pg.evaluate("() => document.querySelector('#pilotBusy').dataset.zkbSlow"),
              f'... it loads, no pause, the note gone ({st[:80]!r})')
        ctx.close()
    except Exception as e:
        check(False, f'the check stopped: {str(e)[:300]}')
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
