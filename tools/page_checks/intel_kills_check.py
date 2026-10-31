"""Intel: kills nearby in the Feed, who's who, the Feed's filters (v2026.10.14.99; roadmap/intel-plan.md N1/N2, mockup
Claude outputs/intel_feed_kills_mockup.html). v2026.10.14.100: R2Z2 as it really answers, and kills by who died.

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/intel_kills_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner's answers, all as recommended: kills in the Feed "within range" from zKillboard's live feed (R2Z2); "Mark and alert"
(a kill marks its system in Near You, attackers as reported, same alert rule); who's who "As drawn" (standing mark, corp
and alliance logos, name coloured by standing, tickers); the filter bar (Types, Distance, Sort, Search). R2Z2 is answered
here with made-up killmails (pilots, corporations and alliances from sa_mocks.py; no real data); everything else as
intel_check.py (its first part runs here). Checks:
  * R2Z2 as its docs ask: sequence.json, then one numbered file at a time; after a 404 nothing for 6 s; never over 15
    requests a second; the last ~15 minutes read at the start (history: shown, no alert);
  * kept: kills within the alert range; left out: far away, NPC kills, older than the time set, a reprocessed copy;
  * a kill row: system (coloured by security), Kill, the victim (standing mark, logos, name, tickers) "lost a" ship and
    its ISK; "by" the final blow and their ship, "+N more" / solo; the zKillboard link;
  * Near You: the system marked with the attackers and their ships, "1 kill"; the alert (sound + notification "Kill: ...");
    a friendly-only kill hidden and silent; each attacker paired with their ship (a pilot link opens it);
  * the filters: Types (kills / reports), Distance, Sort nearest, Search by name and by ticker; kept in this browser; a
    focused search box keeps its focus and text while the lists redraw;
  * R2Z2 failing: INTEL-05, reports carry on; then it recovers; off: no requests;
  * 390 px: nothing off the page, the bar's controls 40 px; no page errors.
v2026.10.14.100 (the owner: "are we actually capturing kills right now?"): R2Z2 is answered here as the real one answers (checked
from the GitHub Pages address, 2026-10-28): sequence.json lags far behind (here it says 2000 while kills are numbered to 5000);
a missing kill answers 404 WITHOUT the header that lets a page read it (the browser reports a network error; here the
request is aborted, since Playwright's route.fulfill() skips the CORS check). Checks:
  * the page finds the newest kill itself (sequence.json, then steps and halving, at most 30 requests) and reads from 240
    before it; the kill in range shows within 30 s; no INTEL-05 note while the feed is up; a missing file not asked for
    again within 6 s; never over 15 requests a second; far behind (a sleeping tab): it finds the newest again;
  * kills by who died (the owner: H2): Friendly lost / Hostile killed / Neutral killed, the row's colour; a kill of a hostile or
    a neutral by friendlies only shows (the owner: "Definitely show enemy kills as well"), still no alert and no Near You row;
    Near You's badges in the same words; the notification "Friendly lost: ...";
  * the standing icons (your corporation's star, hostile -), the system's security tenth and its title.
v2026.10.14.98 and v2026.10.14.99 fail.
v2026.10.14.103 (the owner: "the intel feed is still not showing any kills"; read live from his browser 2026-10-29): numbers
missing between kills, and a hidden tab's timers firing late and together. Checks:
  * holes: two missing numbers early in the read-back and one where finding the newest would stop (4992); the page finds
    the real newest (5000), reads past every hole, and a number missing when first read (the live neutral kill) is
    skipped, asked for again and shown;
  * never over 12 requests in any second, here and in a tab whose timers fire only every 2 s (as a hidden tab's do),
    where the read-back still finishes (v.100 started 28 at once there; zKillboard blocks an address over 15 a second).
v2026.10.14.102 fails.
v2026.10.29.3 (the owner: "i definitely want to see kills well before enemies reach the alert range"): the first part runs with
the kill range set to 3 (the v.99 rule: kills only within the alert range); then the gear sets it to 10, and a kill 9 jumps away
shows in the Feed and Near You without an alert while one 12 jumps away doesn't. v2026.10.29.2 fails.
v2026.10.29.4 (the owner: "i still have not seen a single killmail show up in the feed"; recorded live from his machine: 4 numbers
missing for good, 100274284-287, with kills after them): four missing in a row, then kills. After a minute with no kill read
(set, not waited) the page looks further ahead, finds them and reads on, the kill 7 jumps away shown, at most 12 requests a
second; then 40 missing (wider than a read-back batch of 28), read past too, at most 40 of them kept to ask again; the
status line says "last kill read N s ago", and after 5 minutes without one "no kill read for N min" in amber.
v2026.10.29.3 fails (it waits at the gap for ever).
v2026.10.29.5 (the owner: "it looks like that last kill feed fix didn't work"; his page's state, read in his console, and the
feed's numbers from 12:30 UTC that day): 19 missing after where the page is, and missing ones between kills at every number
v.29.4 looked at; after 30 s with no kill the page reads on number by number and shows the kill. Then nothing new anywhere:
one look costs at most 32 + 56 requests and the next comes a minute later (the wait doubles to 5 minutes). A start with 19
missing in a row near the newest (his restart stopped there): the newest found past them. Requests per second are timed in the
page (window.__r2t), not by the route handler, whose times bunch under load. v2026.10.29.4 fails.
v2026.10.29.6 (the owner's console line and a probe of his feed at 14:47-14:53 UTC): wide gaps read through (replaced below).
v2026.10.29.8 (zKillboard's developer changed Cloudflare on 2026-10-29: sequence.json current for every website, no stuck 404s;
checked from the owner's browser): the RIFT-style reader. R2Z2 is answered here as it now answers: sequence.json 30 behind
the newest, a missing file a readable 404. Checks:
  * the start: sequence.json, then from 240 before its number, nothing asked to find the newest; two gaps before
    sequence.json's number read past and asked for once only;
  * live: a missing number asked for again only after 6 s and nothing past it asked meanwhile ("too soon");
  * a gap while live: after a minute with no kill, sequence.json once; past the gap, so read past it, the kill after it shown;
    not past it: the same number waited on, sequence.json not read again within the minute; then the kill shows;
  * 40 missing then 20 kills, sequence.json past them: read through at once; a 404 without the permission header (LESSON
    #89) still "not there yet"; a sleeping tab far behind sequence.json: only the last 240 read;
  * R2Z2 answering 503: INTEL-05; answering nothing the page may read (CORS, sequence.json too): INTEL-06; both go when it answers;
  * a hidden tab (timers bunched): at most 12 a second, 19 in a row missing before sequence.json's number read past.
v2026.10.29.7 fails (it reads ahead past sequence.json and looks for the newest by steps).
"""
import sys, os, time, re, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
_src = open(os.path.join(HERE, 'intel_check.py'), encoding='utf-8').read()
_src = _src[:_src.index('with sync_playwright() as p:')]
NS = {'__file__': os.path.join(HERE, 'intel_check.py'), '__name__': 'intel_check_prefix'}
exec(compile(_src, 'intel_check.py (first part)', 'exec'), NS)
globals().update({k: v for k, v in NS.items() if not k.startswith('__') and k not in ('check', 'fails')})
from playwright.sync_api import sync_playwright
check = NS['check']
from datetime import datetime, timezone

ID = lambda n: next(i for i, v in M.PILOTS.items() if v[0] == n)
def who(n):
    i = ID(n); corp = M.PILOTS[i][1]; al = M.ORGS[corp][3]
    return {'character_id': i, 'corporation_id': corp, **({'alliance_id': al} if al else {})}
FRIEND = M.PILOTS[M.pick(M.CORP, 1)][0]; FRIEND2 = M.PILOTS[M.pick(M.CORP, 2)][0]
def iso(t): return datetime.fromtimestamp(t, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def km(kid, sysname, ago, victim, vship, atts, value, npc=False, sysid=None):
    sid = sysid or SYSID[sysname]
    A = [dict(a, ship_type_id=M.byname[s], final_blow=(k == 0), damage_done=1000 - 100 * k) for k, (a, s) in enumerate(atts)]
    return {'killmail_id': kid, 'hash': f'{kid:040x}', 'esi': {'killmail_id': kid, 'killmail_time': iso(time.time() - ago), 'solar_system_id': sid,
            'victim': dict(victim, ship_type_id=M.byname[vship]), 'attackers': A},
            'zkb': {'totalValue': value, 'npc': npc, 'solo': len(A) == 1, 'attackerCount': len(A), 'href': f'https://esi.evetech.net/killmails/{kid}/x/'}}
SEQ = {'seq': 4970, 'last': 5000, 'fail': None}  # v2026.10.29.8: sequence.json 30 behind the newest (uploaded every ~51); fail: None, 503, or 'abort'
START = SEQ['seq'] + 1 - 240                          # where the page should start reading (240 before sequence.json's number)
HOLES = {START + 10, START + 11}                      # gaps before sequence.json's number: published numbers that aren't there
LATE = {}                                             # number -> the time it appears (not there before)
NOCORS = {'on': False}
OLD = {'from': 0, 'to': -1}                           # numbers uploaded 5 minutes ago (a sleeping tab's backlog)                                # LESSON #89: a 404 without the permission header (the browser sees a network error)
REC = {}
REQS = []   # (time, path, status)
ACAO = {'access-control-allow-origin': '*'}
def filler(n):   # every number up to the newest is a kill: here an NPC kill in Jita (left out); before START, uploaded 2 h ago
    r = km(9300000 + n, 'Jita', 7300 if n < START else 120, who('Corvin Morrow'), 'Rifter', [(who('Marrek Ketter'), 'Vedmak')], 1e6, npc=True)
    r['uploaded_at'] = int(time.time() - (7200 if n < START else 300 if OLD['from'] <= n <= OLD['to'] else 60)); return r
def r2z2(route):
    url = route.request.url; path = url.split('r2z2.zkillboard.com')[1]
    if SEQ['fail'] == 'abort': REQS.append((time.time(), path, 0)); return route.abort('failed')   # nothing the page may read (CORS, no connection)
    if SEQ['fail']: REQS.append((time.time(), path, SEQ['fail'])); return route.fulfill(status=SEQ['fail'], headers=ACAO, body='')
    if path.endswith('/sequence.json'):
        REQS.append((time.time(), path, 200)); return route.fulfill(status=200, content_type='application/json', headers=ACAO, body=json.dumps({'sequence': SEQ['seq']}))
    m = re.search(r'/ephemeral/(\d+)\.json$', path)
    n = int(m.group(1)) if m else -1
    if not (n in HOLES or time.time() < LATE.get(n, 0)) and (n in REC or 0 < n <= SEQ['last']):
        REQS.append((time.time(), path, 200)); return route.fulfill(status=200, content_type='application/json', headers=ACAO, body=json.dumps(dict(REC.get(n) or filler(n), sequence_id=n)))
    REQS.append((time.time(), path, 404))
    # Since 2026-10-29 a 404 carries the permission header and the page reads it. Before, it didn't: the browser reported a network
    # error. Playwright's route.fulfill() skips the CORS check, so that case is an aborted request here (LESSON #89).
    if NOCORS['on']: return route.abort('failed')
    return route.fulfill(status=404, headers=ACAO, body='')
SEC = {'Jita': 0.946, 'New Caldari': 0.95}
def esi2(route):
    m = re.search(r'/universe/systems/(\d+)/', route.request.url)
    if m:
        i = int(m.group(1)); nm = SYSNAME.get(i, '')
        return route.fulfill(status=200, content_type='application/json', body=json.dumps({'system_id': i, 'name': nm, 'security_status': SEC.get(nm, -0.31)}))
    return esi(route)
B0 = SEQ['last'] - 4   # the newest five kills when the page starts (read back: shown, no alert)
K_HIST = km(9200001, 'D-W7F0', 300, who('Anouk Morrow'), 'Venture', [(who('Kirra Longtail'), 'Sabre')], 4.1e6)
REC.update({B0: K_HIST,
            B0 + 1: km(9200002, 'Jita', 200, who('Seren Morrow'), 'Rifter', [(who('Seren Ketter'), 'Sabre')], 1e6),            # 42 jumps: out
            B0 + 2: km(9200003, '8WA-Z6', 150, who('Corvin Morrow'), 'Rifter', [(who('Marrek Ketter'), 'Vedmak')], 2e6, npc=True),   # NPC: out
            B0 + 3: km(9200004, 'T5ZI-S', 2400, who('Corvin Morrow'), 'Rifter', [(who('Marrek Ketter'), 'Vedmak')], 2e6),        # 40 min old: out
            B0 + 4: km(9200005, 'QX-LIJ', 100, who('Corvin Morrow'), 'Rifter', [(who('Marrek Ketter'), 'Vedmak')], 2e6)})         # 4 jumps: out
LIVE = km(9200010, '8WA-Z6', 40, who(FRIEND), 'Sabre', [(who('Marrek Ketter'), 'Vedmak'), (who('Seren Ketter'), 'Sabre')], 62.4e6)
LIVE['esi']['attackers'].append({'corporation_id': 1000125, 'ship_type_id': M.byname['Rifter'], 'final_blow': False, 'damage_done': 5})   # an NPC attacker
LIVE['zkb']['attackerCount'] = 3
FRIENDLY = km(9200011, 'MO-GZ5', 30, who('Seren Morrow'), 'Rifter', [(who(FRIEND2), 'Loki')], 3e6)                     # a neutral killed by friendlies
HKILL = km(9200012, 'Y-OMTZ', 25, who('Marrek Ketter'), 'Vedmak', [(who(FRIEND2), 'Loki'), (who('Jask Varos'), 'Sabre')], 188.6e6)   # v.100: a hostile killed by friendlies
LABELS = ('Friendly lost', 'Hostile killed', 'Neutral killed')
# v2026.10.30.1: the jump count has its own column (.fj) before the system; 'sys' keeps the old "8WA-Z6 1 Jump" form for the checks
ROWS = """() => [...document.querySelectorAll('#intelPanel #itFeedList .it-fd')].map(r => ({ty: (r.querySelector('.it-ty') || {}).textContent, sys: [((r.querySelector('.it-chip.sys') || {}).textContent || '').trim(), ((r.querySelector('.fj') || {}).textContent || '').trim()].filter(Boolean).join(' ') || null, cls: r.className,
  lines: [...r.querySelectorAll(':scope > .it-chips')].map(c => [...c.children].filter(x => !x.classList.contains('it-fl')).map(x => x.classList.contains('it-chip') ? (x.querySelector('.nm') || x).textContent.trim() : x.classList.contains('fsz') ? x.title : x.textContent.trim()))}))"""   # v2026.10.31.6: the fleet size by its hover
NOTE = "() => (document.querySelector('[data-it-kfnote]') || {}).textContent || ''"
def jof(t):
    m = re.search(r'(\d+) Jumps?$', t or ''); return int(m.group(1)) if m else 0 if (t or '').endswith('In system') else None
def per_s_page(pg):   # v2026.10.29.5: the most R2Z2 requests the page started in any one second
    return pg.evaluate("() => { const t = window.__r2t || []; let m = 0; for(let i = 0, j = 0; i < t.length; i++){ while(t[i] - t[j] >= 1000) j++; m = Math.max(m, i - j + 1); } return m; }")
def gaps_ok():
    miss = [(t, p_) for t, p_, s_ in REQS if s_ == 404]
    again = [min((u - t for u, q, _ in REQS if q == p_ and u > t), default=99) for t, p_ in miss]   # each missing file: how long until it was asked for again
    per_s = max((sum(1 for u, _, _ in REQS if t <= u < t + 1) for t, _, _ in REQS), default=0)
    return again, per_s

with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []
    def new_ctx(w):
        ctx = b.new_context(viewport={'width': w, 'height': 1000}); ctx.on('page', lambda pg: pg.on('pageerror', lambda e: errs.append(str(e))))
        ctx.add_init_script(FS)
        # v2026.10.29.5: each R2Z2 request's start, timed in the page (the route handler's own times can bunch under load)
        ctx.add_init_script("(() => { const f = window.fetch; window.__r2t = []; window.fetch = function(u, o){ if(String(u).includes('r2z2.zkillboard.com')) window.__r2t.push(Date.now()); return f.apply(this, arguments); }; })();")
        ctx.route(re.compile(r'https://esi\.evetech\.net/.*'), esi2)
        ctx.route(re.compile(r'https://zkillboard\.com/.*'), M.zkb)
        ctx.route(re.compile(r'https://(images\.evetech\.net|fonts\.).*'), lambda r: r.fulfill(status=404, body=''))
        ctx.route(re.compile(r'https://r2z2\.zkillboard\.com/.*'), r2z2)
        return ctx
    def start(w, init=None):
        ctx = new_ctx(w)
        if init: ctx.add_init_script(init)
        pg = ctx.new_page(); pg.goto('file://' + HTML)
        pg.evaluate("(s) => { localStorage.setItem('dscanSide', JSON.stringify(s)); localStorage.setItem('dscanIntel', JSON.stringify({channels: ['region.intel'], me: 95000001, range: 3, killRange: 3, sound: true, notify: true, forget: 15, hideFriendly: true})); }", SIDE)
        pg.reload(); pg.wait_for_timeout(400)
        setup_logs(pg); pg.click('#tabBtnIntel'); pg.click('[data-it-act="folder"]'); pg.wait_for_timeout(300); pg.click('#intelSwLabel')
        return ctx, pg
    REQS.clear()
    ctx, pg = start(1440)
    t0 = time.time()
    for _ in range(160):   # v2026.10.30.3: 5 a second, so the 240 read back take about twice as long
        if any(r['sys'] and r['sys'].startswith('D-W7F0') and r['ty'] in LABELS for r in pg.evaluate(ROWS)): break
        pg.wait_for_timeout(500)
    took = time.time() - t0
    seq = [p_ for _, p_, _ in REQS]
    i0 = seq.index(f'/ephemeral/{START}.json') if f'/ephemeral/{START}.json' in seq else -1
    once = [sum(1 for q in seq if q == f'/ephemeral/{h}.json') for h in sorted(HOLES)]
    check(seq[:1] == ['/ephemeral/sequence.json'] and i0 == 1 and seq[i0:i0 + 6] == [f'/ephemeral/{START + i}.json' for i in range(6)] and once == [1, 1] and took < 80,
          f'R2Z2: sequence.json ({SEQ["seq"]}), then read from 240 before it ({START}) with nothing asked to find the newest; two gaps before its number read past, each asked for once {once}; the kill in range shown after {took:.0f} s')
    pg.wait_for_timeout(3000)
    R = pg.evaluate(ROWS)
    kills = [r for r in R if r['ty'] in LABELS]
    check([r['sys'] for r in kills] == ['D-W7F0 2 Jumps'], f'kept: the kill within range; left out: Jita (42 j), the NPC kills, the 40-minute-old one, QX-LIJ (4 j) {[r["sys"] for r in kills]}')
    check(kills and kills[0]['ty'] == 'Neutral killed' and kills[0]['lines'] == [['Anouk Morrow', 'lost a', 'Venture', '4.1M ISK'], ['by', 'Kirra Longtail', 'Sabre', '1 player on this kill: solo', 'zK']] and ' kn' in kills[0]['cls'],
          f'a solo kill row: "Neutral killed" (v.100: by who died) {kills[:1]}')
    al0 = pg.evaluate("() => [__fs.beeps, __fs.notes.length]")
    check(al0 == [0, 0], f'kills read at the start: shown, no alert {al0}')
    # ---- live ----
    for _ in range(60):   # v.103: the page idle at the live end, its next read more than 2 s away
        st = pg.evaluate("() => [it.kf.head && !it.kf.busy, it.kf.waitUntil - Date.now(), it.kf.waitUntil]")
        if st[0] and st[1] > 2000: break
        pg.wait_for_timeout(250)
    SEQ['last'] += 4; L0 = B0 + 5
    LATE[L0 + 1] = st[2] / 1000 + 3   # v.103: missing when next read while the ones after it are there: a hole, asked for again
    REC[L0] = LIVE; REC[L0 + 1] = FRIENDLY; REC[L0 + 2] = LIVE; REC[L0 + 3] = HKILL   # the third: a reprocessed copy
    pg.wait_for_timeout(15000)
    note = pg.evaluate(NOTE)
    check(note == '', f'the feed up and nothing new: no INTEL-05 note (v.99: a missing kill read as the feed being down) {note!r}')
    again, per_s = gaps_ok(); per_s = per_s_page(pg)
    check(again and min(again) >= 5.9 and per_s <= 12, f'a missing kill not asked for again within 6 s ({sorted(round(x, 1) for x in again)[:4]}); at most {per_s} requests in any second')
    R = pg.evaluate(ROWS)
    k8 = [r for r in R if r['ty'] in LABELS and r['sys'] == '8WA-Z6 1 Jump']
    check(len(k8) == 1 and k8[0]['ty'] == 'Friendly lost' and ' kf' in k8[0]['cls'] and k8[0]['lines'] == [[FRIEND, 'lost a', 'Sabre', '62.4M ISK'], ['by', 'Marrek Ketter', 'Vedmak', '2 players on this kill: small gang', 'zK']],
          f'the live kill: "Friendly lost"; victim lost a Sabre and its ISK; by the final blow in a Vedmak, 2 players on it (v2026.10.31.6: the dossier fleet size, NPCs left out; was +2 more from the zKillboard count); the reprocessed copy not again {k8}')
    kn = [(r['ty'], next((c for c in r['cls'].split() if c in ('kf', 'kh', 'kn')), '')) for r in R if r['sys'] and r['sys'].startswith(('MO-GZ5', 'Y-OMTZ')) and r['ty'] in LABELS]
    check(sorted(kn) == [('Hostile killed', 'kh'), ('Neutral killed', 'kn')], f'kills by friendlies only of a hostile and of a neutral: shown with "hide friendly" on (the owner: "Definitely show enemy kills as well") {kn}')
    look = pg.evaluate("""() => { const r = [...document.querySelectorAll('#itFeedList .it-fd.kill')].find(x => x.querySelector('.it-chip.sys').textContent.startsWith('8WA-Z6'));
      const c = [...r.querySelectorAll('.it-chip.p')].find(x => x.querySelector('.nm').textContent === 'Marrek Ketter'), v = r.querySelector('.it-chip.p');
      return [c.className, c.querySelector('svg.it-st').getAttribute('class'), c.querySelectorAll('.it-lg').length, c.querySelector('.it-tks').textContent, v.className.includes(' f'), v.querySelector('svg.it-st').getAttribute('class'), r.querySelector('.it-sn').className, r.querySelector('.it-chip.sys').title, r.querySelector('a.zk-ic').href]; }""")
    # v2026.10.30.4: one set of standing icons site-wide (standIcon); they also carry sa-mark h / n / f
    check(look == ['it-chip p h', 'it-st bad sa-mark h', 2, '[RLH]<CRTS>', True, 'it-st corp sa-mark f', 'it-sn ns s0', 'Show only 8WA-Z6 in the Feed (8WA-Z6 (security -0.3))', 'https://zkillboard.com/kill/9200010/'],
          f"who's who: standing icons (hostile -, your corporation's star), logos, name coloured, tickers; the system's security tenth and title; the zKillboard link {look}")
    tenths = pg.evaluate("() => [1.0, 0.96, 0.946, 0.5, 0.45, 0.449, 0.15, 0.04, 0.0, -0.31].map((v, i) => { it.sec.set(-1 - i, v); const r = [itSecClass(-1 - i), itSecText(-1 - i)]; it.sec.delete(-1 - i); return r; })")
    check(tenths == [['hs s10', '1.0'], ['hs s10', '1.0'], ['hs s9', '0.9'], ['hs s5', '0.5'], ['hs s5', '0.5'], ['ls s4', '0.4'], ['ls s2', '0.2'], ['ls s1', '0.1'], ['ns s0', '0.0'], ['ns s0', '-0.3']],
          f"security as EVE shows it: the nearest tenth, and above 0.0 but under 0.05 shows 0.1 (low-sec) {tenths}")
    near = pg.evaluate("() => [...document.querySelectorAll('#itNearList .it-nb')].map(r => [r.querySelector('.sys').textContent, r.querySelector('.st').textContent, r.querySelector('.who').textContent, r.classList.contains('alert'), [...r.querySelectorAll('.it-kl')].map(k => k.className)])")
    n8 = next((r for r in near if r[0] == '8WA-Z6'), None); nd = next((r for r in near if r[0] == 'D-W7F0'), None)
    check(n8 == ['8WA-Z6', '2 hostile', 'Marrek Ketter, Seren Ketter · Vedmak, Sabre', True, ['it-kl kf']] and nd == ['D-W7F0', '1 neutral', 'Kirra Longtail · Sabre', True, ['it-kl kn']],
          f"Near You: a kill marks its system with the attackers and their ships; the badge (at the right, v2026.10.30.1) in the Feed's words and colour {near}")
    # v2026.10.30.1 (the owner: "killmails within specified kill range show in feed but not in 'Near You' list", then "even if a hostile
    # is killed by a friendly, it means there are potentially MORE hostiles there"): a kill by friendlies only of a neutral or a hostile
    # is a sighting of the victim's side: counted and coloured as such, "X lost a Ship · by <your pilots>", the kill's badge, and it
    # alerts within the alert range like a report
    fr = sorted([r[0], r[1], r[2], r[3], r[4]] for r in near if r[0] in ('MO-GZ5', 'Y-OMTZ'))
    check(fr == [['MO-GZ5', '1 neutral', f'Seren Morrow lost a Rifter · by {FRIEND2}', True, ['it-kl kn']], ['Y-OMTZ', '1 hostile', f'Marrek Ketter lost a Vedmak · by {FRIEND2}, Jask Varos', True, ['it-kl kh']]],
          f"kills by friendlies only of a neutral and of a hostile: a sighting of the victim's side, 'X lost a ship · by' your pilots, the badge, in the alert range (v2026.10.29.8: no row; the draft: 'friendly', no alert) {fr}")
    wc = pg.evaluate("() => Object.fromEntries([...document.querySelectorAll('#itNearList .it-nb')].map(r => [r.querySelector('.sys').textContent, [r.querySelector('.st b').textContent, getComputedStyle(r.querySelector('.st b')).color]]))")
    check(wc.get('8WA-Z6') == ['2 hostile', 'rgb(198, 91, 78)'] and wc.get('T5ZI-S') == ['1 neutral', 'rgb(215, 222, 227)'] and wc.get('Y-OMTZ') == ['1 hostile', 'rgb(198, 91, 78)'],
          f"Near You's word in its standing's colour (the owner, 2026-10-30): hostile as hostile names, neutral a bright grey {wc}")
    al = pg.evaluate("() => [__fs.beeps, __fs.notes]")
    check(al[0] == 3 and al[1] == [['8WA-Z6 · 1 jump', f'Friendly lost: {FRIEND} lost a Sabre (62.4M ISK)'], ['MO-GZ5 · 1 jump', 'Neutral killed: Seren Morrow lost a Rifter (3.0M ISK)'], ['Y-OMTZ · 3 jumps', 'Hostile killed: Marrek Ketter lost a Vedmak (188.6M ISK)']],
          f'the live kills alert: sound and notification "Friendly lost: ..."; enemies killed by friendlies alert too (a sighting, v2026.10.30.1) {al}')
    pr = pg.evaluate("() => { const st = it.near.get(it.names.byLower.get('8wa-z6')); return Object.fromEntries([...st.pairs].map(([id, s]) => [st.pilots.find(x => x.id === id).name, s.name])); }")
    check(pr == {'Marrek Ketter': 'Vedmak', 'Seren Ketter': 'Sabre'}, f'each attacker paired with their ship {pr}')
    # ---- v2026.10.29.3: the Feed's kill range (the owner: "feed range as the ring of awareness, alert range is my ring of being alert") ----
    pg.click('[data-it-act="gear"]'); pg.wait_for_timeout(200)
    has_kr = pg.locator('.it-pop [data-it-set="killRange"]').count() == 1
    check(has_kr, 'the gear has the Feed\'s kill range')
    if has_kr: pg.select_option('.it-pop [data-it-set="killRange"]', '10'); pg.wait_for_timeout(200)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    S9 = next(i for i, d in sorted(D0.items()) if d == 9 and i in SYSNAME); S12 = next(i for i, d in sorted(D0.items()) if d == 12 and i in SYSNAME)
    for _ in range(60):
        st = pg.evaluate("() => [it.kf.head && !it.kf.busy, it.kf.waitUntil - Date.now()]")
        if st[0]: break
        pg.wait_for_timeout(250)
    b0 = pg.evaluate("() => __fs.beeps")
    REC[L0 + 4] = km(9200020, None, 30, who('Corvin Morrow'), 'Rifter', [(who('Marrek Ketter'), 'Vedmak')], 2e6, sysid=S9)
    REC[L0 + 5] = km(9200021, None, 30, who('Corvin Morrow'), 'Rifter', [(who('Marrek Ketter'), 'Vedmak')], 2e6, sysid=S12)
    used = {SYSID[n] for n in ('8WA-Z6', 'MO-GZ5', 'Y-OMTZ', 'D-W7F0', 'T5ZI-S', 'QX-LIJ', '1DQ1-A') if n in SYSID}
    SFF = next(i for i, d in sorted(D0.items()) if d == 2 and i in SYSNAME and i not in used)
    REC[L0 + 6] = km(9200022, None, 30, who(FRIEND), 'Rifter', [(who(FRIEND2), 'Loki')], 1e6, sysid=SFF)   # a friendly killed by friendlies only
    SEQ['last'] += 3
    pg.wait_for_timeout(9000)
    R = pg.evaluate(ROWS)
    k9 = [r['sys'] for r in R if r['ty'] in LABELS and (r['sys'] or '').startswith(SYSNAME[S9] + ' ')]
    k12 = [r['sys'] for r in R if r['ty'] in LABELS and (r['sys'] or '').startswith(SYSNAME[S12] + ' ')]
    near9 = pg.evaluate("(n) => [...document.querySelectorAll('#itNearList .it-nb')].filter(r => r.querySelector('.sys').textContent === n).map(r => r.classList.contains('alert'))", SYSNAME[S9])
    # v2026.10.31.2: Near You stops at the alert range + 5 (3 + 5 = 8 here), so the kill 9 jumps away is in the Feed only
    check(k9 == [f'{SYSNAME[S9]} 9 Jumps'] and not k12 and near9 == [] and pg.evaluate("() => __fs.beeps") == b0 and pg.evaluate("() => itKillRange()") == 10,
          f'the kill range set to 10 under the gear: a kill 9 jumps away shows in the Feed (not Near You: past the alert range + 5; no alert); one 12 jumps away does not ({k9}, {k12}, {near9})')
    ff = [[r['sys'] for r in R if (r['sys'] or '').startswith(SYSNAME[SFF] + ' ')], pg.evaluate("(n) => [...document.querySelectorAll('#itNearList .it-nb .sys')].filter(x => x.textContent === n).length", SYSNAME[SFF])]
    check(ff == [[], 0] and pg.evaluate("(id) => it.feed.some(e => e.kind === 'kill' && e.p.sys[0].id === id)", SFF),
          f'a friendly killed by friendlies only: read, but hidden in the Feed and in Near You with "hide friendlies" on {ff}')
    # ---- v2026.10.29.8: the reader as documented (and as RIFT reads) ----
    def idle():
        for _ in range(80):
            if pg.evaluate("() => it.kf.head && !it.kf.busy"): return True
            pg.wait_for_timeout(250)
        return False
    def nums(r0):   # the numbered files asked for since REQS[r0], and how often sequence.json was
        out = [int(re.search(r'/(\d+)\.json$', q).group(1)) for _, q, _ in REQS[r0:] if re.search(r'/(\d+)\.json$', q)]
        return out, sum(1 for _, q, _ in REQS[r0:] if q.endswith('/sequence.json'))
    def s7():
        return [r['sys'] for r in pg.evaluate(ROWS) if r['ty'] in LABELS and (r['sys'] or '').startswith(SYSNAME[S7] + ' ')]
    def wait_s7(k, extra='true', n=60):
        t0 = time.time()
        for _ in range(n):
            if len(s7()) == k and pg.evaluate(f"() => it.kf.head && !it.kf.busy && ({extra})"): break
            pg.wait_for_timeout(500)
        return time.time() - t0
    idle()
    s1 = pg.evaluate("() => (document.querySelector('[data-it-status]') || {}).textContent || ''")
    check(re.search(r' · last kill read \d+ s ago$', s1) is not None, f'the status line says when a kill was last read {s1!r}')
    S7 = next(i for i, d in sorted(D0.items()) if d == 7 and i in SYSNAME)
    # a gap while live (4 never published), then kills; sequence.json past them once they're uploaded
    G0 = SEQ['last'] + 1
    HOLES.update(range(G0, G0 + 4))
    REC[G0 + 4] = km(9200030, None, 30, who('Corvin Morrow'), 'Rifter', [(who('Marrek Ketter'), 'Vedmak')], 3e6, sysid=S7)
    SEQ['last'] = G0 + 9; SEQ['seq'] = G0 + 9
    r0 = len(REQS); pg.wait_for_timeout(13000)
    asked, sq = nums(r0)
    check(asked and set(asked) == {G0} and 2 <= len(asked) <= 3 and sq == 0,
          f'a missing number while live: only it asked for, every 6 s, nothing past it and no sequence.json within the minute ({asked}, sequence.json {sq} times)')
    pg.evaluate("() => { it.kf.lastGot = Date.now() - 61000; it.kf.seqAt = 0; }")   # a minute with no kill read (set, not waited)
    r0 = len(REQS); took = wait_s7(1, f"it.kf.seq > {SEQ['last']}")
    asked, sq = nums(r0); st = pg.evaluate("() => [it.kf.seq, it.kf.target]"); per_s = per_s_page(pg)
    check(s7() == [f'{SYSNAME[S7]} 7 Jumps'] and st[0] == SEQ['last'] + 1 and sq == 1 and len(asked) <= 10 + 28 + 2 and per_s <= 12,
          f'a minute without a kill: sequence.json read once ({sq}), past the gap, so the gap read past and the kill 7 jumps away shown {took:.0f} s later; now at {st[0]} (newest {SEQ["last"]}), {len(asked)} files asked, at most {per_s} in any second')
    # too soon: sequence.json not past the number waited on: keep waiting, sequence.json not read again within the minute
    idle(); N0 = SEQ['last'] + 1
    pg.evaluate("() => { it.kf.lastGot = Date.now() - 61000; it.kf.seqAt = 0; }")
    r0 = len(REQS); pg.wait_for_timeout(13000)
    asked, sq = nums(r0); st = pg.evaluate("() => it.kf.seq")
    check(sq == 1 and set(asked) == {N0} and st == N0, f'"too soon" (sequence.json not past it): sequence.json read once ({sq}), the same number waited on ({sorted(set(asked))}, at {st})')
    REC[N0] = km(9200031, None, 20, who('Corvin Morrow'), 'Rifter', [(who('Marrek Ketter'), 'Vedmak')], 5e6, sysid=S7)
    SEQ['last'] = N0
    took = wait_s7(2, n=30)
    check(len(s7()) == 2 and took < 9, f'published: shown at the next ask, {took:.0f} s later')
    # 40 missing in a row, then 20 kills published together; sequence.json past them (the shape of the owner's feed at 14:53)
    idle(); Q0 = SEQ['last'] + 1
    HOLES.update(range(Q0, Q0 + 40))
    REC[Q0 + 50] = km(9200033, None, 10, who('Corvin Morrow'), 'Rifter', [(who('Marrek Ketter'), 'Vedmak')], 6e6, sysid=S7)
    SEQ['last'] = Q0 + 59; SEQ['seq'] = Q0 + 59
    pg.wait_for_timeout(7000)
    pg.evaluate("() => { it.kf.lastGot = Date.now() - 61000; it.kf.seqAt = 0; }")
    r0 = len(REQS); took = wait_s7(3, f"it.kf.seq > {SEQ['last']}")
    asked, sq = nums(r0); st = pg.evaluate("() => it.kf.seq"); per_s = per_s_page(pg)
    check(len(s7()) == 3 and st == SEQ['last'] + 1 and len(asked) <= 60 + 28 + 2 and per_s <= 12,
          f'40 missing, then 20 kills, sequence.json past them: read through at once, the kill shown {took:.0f} s later, now at {st} (newest {SEQ["last"]}), {len(asked)} files asked, at most {per_s} in any second')
    # LESSON #89: a 404 without the permission header (a network error to the page) is still "not there yet": no note
    idle(); NOCORS['on'] = True; N1 = SEQ['last'] + 1
    REC[N1] = km(9200034, None, 10, who('Corvin Morrow'), 'Rifter', [(who('Marrek Ketter'), 'Vedmak')], 7e6, sysid=S7)
    LATE[N1] = time.time() + 4; SEQ['last'] = N1
    took = wait_s7(4, n=40); note = pg.evaluate(NOTE)
    check(len(s7()) == 4 and note == '', f'a 404 the browser may not read (LESSON #89): "not there yet", the kill shown when published ({took:.0f} s), no note {note!r}')
    NOCORS['on'] = False
    # a sleeping tab far behind: sequence.json 1000 past it: only the last 240 read
    idle(); F0 = SEQ['last'] + 1
    SEQ['last'] = F0 + 999; SEQ['seq'] = F0 + 999; OLD.update({'from': F0, 'to': SEQ['last'] - 240})
    REC[SEQ['last'] - 20] = km(9200035, None, 10, who('Corvin Morrow'), 'Rifter', [(who('Marrek Ketter'), 'Vedmak')], 8e6, sysid=S7)
    pg.evaluate("() => { it.kf.seqAt = 0; }")   # (sequence.json last read over a minute ago)
    r0 = len(REQS); took = wait_s7(5, f"it.kf.seq > {SEQ['last']}", n=240)   # 240 at the gate's 5 a second (v2026.10.30.3): ~50 s
    asked, sq = nums(r0); st = pg.evaluate("() => it.kf.seq")
    skipped = [n for n in asked if F0 + 12 <= n < SEQ['seq'] + 1 - 240]
    check(len(s7()) == 5 and st == SEQ['last'] + 1 and not skipped and len(asked) <= 12 + 240 + 28 + 2,
          f'a sleeping tab woken 1000 behind: the first kill read was uploaded 5 min ago, so sequence.json read and only the last 240 read ({len(asked)} files, {len(skipped)} in the backlog past the first tick), the kill shown {took:.0f} s later')
    pg.evaluate("() => { it.kf.lastGot = Date.now() - 6 * 60000; }")
    pg.wait_for_timeout(1200)
    s2 = pg.evaluate("() => { const e = document.querySelector('[data-it-status] .it-kslow'); return e ? [e.textContent, getComputedStyle(e).color] : null; }")
    check(s2 is not None and s2[0] == 'no kill read for 6 min' and s2[1] == 'rgb(217, 154, 60)', f'no kill read for 5 minutes or more: the status line says so in amber {s2}')
    pg.evaluate("() => { it.kf.lastGot = Date.now(); }")
    pg.evaluate("() => [...[...document.querySelectorAll('#itFeedList .it-fd.kill')].find(x => x.querySelector('.it-chip.sys').textContent.startsWith('8WA-Z6')).querySelectorAll('.it-chip.p')].find(x => x.querySelector('.nm').textContent === 'Marrek Ketter').click()")
    pg.wait_for_function("() => !document.querySelector('#fitBtn').disabled && document.querySelector('#pilotBusy').hidden", timeout=120000); pg.wait_for_timeout(300)
    got = pg.evaluate("() => [document.querySelector('#pilotName').value, document.querySelector('#manualShip').value]")
    check(got == ['Marrek Ketter', 'Vedmak'], f'a pilot on a kill opens in the ship they flew {got}')
    pg.click('#tabBtnIntel'); pg.wait_for_timeout(300)
    # ---- the filters ----
    def rows(): return pg.evaluate(ROWS)
    pg.select_option('[data-it-f="types"]', 'kills'); pg.wait_for_timeout(200)
    check(all(r['ty'] in LABELS for r in rows()) and len(rows()) == 10, f'Types: kills only {[r["ty"] for r in rows()]}')
    pg.select_option('[data-it-f="types"]', 'reports'); pg.wait_for_timeout(200)
    check(rows() and all(r['ty'] not in LABELS for r in rows()), 'Types: reports only')
    pg.select_option('[data-it-f="types"]', 'all'); pg.select_option('[data-it-f="dist"]', '1'); pg.wait_for_timeout(200)
    js = [jof(r['sys']) for r in rows() if r['sys']]
    check(js and None not in js and max(js) <= 1, f'Distance ≤ 1 jump {js}')
    pg.select_option('[data-it-f="dist"]', '0'); pg.select_option('[data-it-f="sort"]', 'near'); pg.wait_for_timeout(200)
    js = [jof(r['sys']) for r in rows() if r['sys'] and jof(r['sys']) is not None]
    check(js == sorted(js) and len(js) >= 3, f'Sort: nearest first {js}')
    pg.select_option('[data-it-f="sort"]', 'new')
    pg.fill('[data-it-q]', 'ketter'); pg.wait_for_timeout(200)
    check(rows() and all('Ketter' in json.dumps(r) for r in rows()), f'Search by name: "ketter" {len(rows())} rows')
    pg.fill('[data-it-q]', 'crts'); pg.wait_for_timeout(200)
    kk = sorted(r['sys'] for r in rows() if r['ty'] in LABELS)
    check(kk == sorted(['8WA-Z6 1 Jump', 'Y-OMTZ 3 Jumps', f'{SYSNAME[S9]} 9 Jumps', f'{SYSNAME[S7]} 7 Jumps', f'{SYSNAME[S7]} 7 Jumps', f'{SYSNAME[S7]} 7 Jumps', f'{SYSNAME[S7]} 7 Jumps', f'{SYSNAME[S7]} 7 Jumps']), f'Search by ticker: "crts" finds the kills with Crimson Tide pilots in them {kk}')
    pg.focus('[data-it-q]'); pg.keyboard.type('x'); pg.wait_for_timeout(4500)
    foc = pg.evaluate("() => [document.activeElement.matches('[data-it-q]'), document.activeElement.value, document.activeElement.selectionStart]")
    check(foc == [True, 'crtsx', 5], f'the search box keeps its focus and text while the lists redraw {foc}')
    pg.fill('[data-it-q]', ''); pg.select_option('[data-it-f="types"]', 'kills')
    st = pg.evaluate("() => JSON.parse(localStorage.getItem('dscanIntel')).feed")
    check(st == {'types': 'kills', 'dist': 0, 'sort': 'new'}, f'the filters kept in this browser {st}')
    pg.select_option('[data-it-f="types"]', 'all')
    # ---- R2Z2 failing, then back; off: no requests ----
    for _ in range(60):   # caught up first (reading back has its own check of sequence.json), so this tests the live path
        if pg.evaluate("() => it.kf.head && !it.kf.busy"): break
        pg.wait_for_timeout(500)
    SEQ['fail'] = 503; pg.evaluate("() => { it.kf.waitUntil = 0; }")
    for _ in range(30):
        note = pg.evaluate(NOTE)
        if note: break
        pg.wait_for_timeout(500)
    W(pg, F_INTEL, line(time.time(), 'Scout Alt', 'T5ZI-S Kirra Longtail loki')); pg.wait_for_timeout(2600)
    still = pg.evaluate("() => [...document.querySelectorAll('#itFeedList .raw')].some(r => r.textContent.endsWith('T5ZI-S Kirra Longtail loki'))")
    check(note.endswith('(INTEL-05)') and 'status 503' in note and still, f'R2Z2 answering 503: INTEL-05, reports carry on ({note!r})')
    SEQ['fail'] = None; pg.evaluate("() => { it.kf.waitUntil = 0; }")
    for _ in range(20):
        if pg.evaluate("() => !document.querySelector('[data-it-kfnote]')"): break
        pg.wait_for_timeout(500)
    check(pg.evaluate("() => !document.querySelector('[data-it-kfnote]')"), f'R2Z2 back: the note goes {pg.evaluate("() => [it.kf.busy, it.kf.head, it.kf.fails, it.kf.waitUntil - Date.now()]")}')
    # v2026.10.29.8: nothing the page may read, sequence.json too (2026-10-29: answers without the permission header): INTEL-06
    idle(); SEQ['fail'] = 'abort'
    pg.evaluate("() => { it.kf.lastGot = Date.now() - 61000; it.kf.seqAt = 0; it.kf.waitUntil = 0; }")
    for _ in range(30):
        note = pg.evaluate(NOTE)
        if note: break
        pg.wait_for_timeout(500)
    check(note.endswith('(INTEL-06)') and "can't read zKillboard's live kill feed" in note, f'nothing readable from R2Z2, sequence.json too (CORS): INTEL-06 within the minute\'s check ({note!r})')
    SEQ['fail'] = None; pg.evaluate("() => { it.kf.waitUntil = 0; }")
    for _ in range(20):
        if pg.evaluate("() => !document.querySelector('[data-it-kfnote]')"): break
        pg.wait_for_timeout(500)
    check(pg.evaluate("() => !document.querySelector('[data-it-kfnote]')"), 'readable again: INTEL-06 goes')
    pg.click('#intelSwLabel'); pg.wait_for_timeout(500); n0 = len(REQS); pg.wait_for_timeout(8000)
    check(len(REQS) == n0, f'off: no requests to R2Z2 ({len(REQS) - n0})')
    pg.screenshot(path=os.environ.get('INTEL_SHOT', '/tmp/intel100_1440.png'), full_page=True)
    ctx.close()
    # ---- v.103: a hidden tab: its timers fire only every 2 s, together ----
    COALESCE = """(() => { const st = window.setTimeout; window.setTimeout = (fn, ms, ...a) => { const at = Math.ceil((Date.now() + (+ms || 0)) / 2000) * 2000; return st(fn, Math.max(0, at - Date.now()), ...a); }; })();"""
    S2 = SEQ['seq'] + 1 - 240
    HOLES.clear(); HOLES.update({S2 + 10, S2 + 11}); HOLES.update(range(SEQ['seq'] - 40, SEQ['seq'] - 21))   # two gaps, and 19 in a row before sequence.json's number
    REQS.clear(); ctx, pg = start(1440, COALESCE); t0 = time.time()
    for _ in range(180):
        if pg.evaluate("() => !!(it.kf && it.kf.head)"): break
        pg.wait_for_timeout(500)
    took = time.time() - t0; per_s = per_s_page(pg)
    st = pg.evaluate("() => it.kf && [it.kf.seq, it.kf.head]")
    once = max(sum(1 for _, q, _ in REQS if q == f'/ephemeral/{h}.json') for h in HOLES)
    check(st == [SEQ['last'] + 1, True] and once == 1, f'starting with 19 missing in a row before sequence.json\'s number: read past them, each asked for once, now at {st} (newest {SEQ["last"]})')
    check(per_s <= 6 and took < 90, f'a hidden tab (timers every 2 s, together): at most {per_s} requests in any second (v.100: 28 at once), and the read-back still done in {took:.0f} s')
    ctx.close()
    # ---- phone ----
    REQS.clear(); ctx, pg = start(390); pg.wait_for_timeout(20000)
    over = pg.evaluate("() => [document.documentElement.scrollWidth, [...document.querySelectorAll('#intelPanel *')].filter(e => { const r = e.getBoundingClientRect(); return r.width && (r.right > innerWidth + 1 || r.left < -1); }).map(e => e.className || e.tagName).slice(0, 5), Math.min(...[...document.querySelectorAll('.it-fbar select, .it-fbar input')].map(e => e.getBoundingClientRect().height))]")
    check(over[0] <= 390 and not over[1] and over[2] >= 40, f'390 px: nothing off the page, the bar 40 px {over}')
    pg.screenshot(path='/tmp/intel100_390.png', full_page=True)
    ctx.close()
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f"FAILURES: {NS['fails']}")
sys.exit(1 if NS['fails'] else 0)
