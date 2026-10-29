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
SEQ = {'stale': 2000, 'last': 5000, 'fail': False}   # v.100: sequence.json says 2000 while kills exist to 5000 (R2Z2 on 2026-10-28)
START = SEQ['last'] + 1 - 240                          # where the page should start reading (240 before the newest)
REC = {}
REQS = []   # (time, path, status)
ACAO = {'access-control-allow-origin': '*'}
def filler(n):   # every number up to the newest is a kill: here an NPC kill in Jita (left out); before START, uploaded 2 h ago
    r = km(9300000 + n, 'Jita', 7300 if n < START else 120, who('Corvin Morrow'), 'Rifter', [(who('Marrek Ketter'), 'Vedmak')], 1e6, npc=True)
    r['uploaded_at'] = int(time.time() - (7200 if n < START else 60)); return r
def r2z2(route):
    url = route.request.url; path = url.split('r2z2.zkillboard.com')[1]
    if SEQ['fail']: REQS.append((time.time(), path, 503)); return route.abort('failed')   # down: the page sees a network error
    if path.endswith('/sequence.json'):
        REQS.append((time.time(), path, 200)); return route.fulfill(status=200, content_type='application/json', headers=ACAO, body=json.dumps({'sequence': SEQ['stale']}))
    m = re.search(r'/ephemeral/(\d+)\.json$', path)
    n = int(m.group(1)) if m else -1
    if n in REC or 0 < n <= SEQ['last']:
        REQS.append((time.time(), path, 200)); return route.fulfill(status=200, content_type='application/json', headers=ACAO, body=json.dumps(dict(REC.get(n) or filler(n), sequence_id=n)))
    # The real one answers 404 without the CORS header, so the browser reports a network error and the page never sees the
    # 404. Playwright's route.fulfill() skips the CORS check (a header-less 404 reaches the page as a 404), so the double
    # aborts the request instead: what the page sees is then what it sees on the real feed (LESSON #89).
    REQS.append((time.time(), path, 404)); return route.abort('failed')
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
ROWS = """() => [...document.querySelectorAll('#intelPanel #itFeedList .it-fd')].map(r => ({ty: (r.querySelector('.it-ty') || {}).textContent, sys: (r.querySelector('.it-chip.sys') || {}).textContent, cls: r.className,
  lines: [...r.querySelectorAll(':scope > .it-chips')].map(c => [...c.children].map(x => x.classList.contains('it-chip') ? (x.querySelector('.nm') || x).textContent.trim() : x.textContent.trim()))}))"""
NOTE = "() => (document.querySelector('[data-it-kfnote]') || {}).textContent || ''"
def jof(t):
    m = re.search(r'(\d+) Jumps?$', t or ''); return int(m.group(1)) if m else 0 if (t or '').endswith('In system') else None
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
        ctx.route(re.compile(r'https://esi\.evetech\.net/.*'), esi2)
        ctx.route(re.compile(r'https://zkillboard\.com/.*'), M.zkb)
        ctx.route(re.compile(r'https://(images\.evetech\.net|fonts\.).*'), lambda r: r.fulfill(status=404, body=''))
        ctx.route(re.compile(r'https://r2z2\.zkillboard\.com/.*'), r2z2)
        return ctx
    def start(w):
        ctx = new_ctx(w); pg = ctx.new_page(); pg.goto('file://' + HTML)
        pg.evaluate("(s) => { localStorage.setItem('dscanSide', JSON.stringify(s)); localStorage.setItem('dscanIntel', JSON.stringify({channels: ['region.intel'], me: 95000001, range: 3, sound: true, notify: true, forget: 15, hideFriendly: true})); }", SIDE)
        pg.reload(); pg.wait_for_timeout(400)
        setup_logs(pg); pg.click('#tabBtnIntel'); pg.click('[data-it-act="folder"]'); pg.wait_for_timeout(300); pg.click('#intelHdrLabel')
        return ctx, pg
    REQS.clear()
    ctx, pg = start(1440)
    t0 = time.time()
    for _ in range(80):
        if any(r['sys'] and r['sys'].startswith('D-W7F0') and r['ty'] in LABELS for r in pg.evaluate(ROWS)): break
        pg.wait_for_timeout(500)
    took = time.time() - t0
    seq = [p_ for _, p_, _ in REQS]
    i0 = seq.index(f'/ephemeral/{START}.json') if f'/ephemeral/{START}.json' in seq else -1
    check(seq[:1] == ['/ephemeral/sequence.json'] and 0 < i0 <= 30 and seq[i0:i0 + 6] == [f'/ephemeral/{START + i}.json' for i in range(6)] and took < 30,
          f'R2Z2: sequence.json (stale: {SEQ["stale"]}), the newest kill found in {i0 - 1} requests, then read one by one from 240 before it ({START}); the kill in range shown after {took:.0f} s')
    pg.wait_for_timeout(3000)
    R = pg.evaluate(ROWS)
    kills = [r for r in R if r['ty'] in LABELS]
    check([r['sys'] for r in kills] == ['D-W7F0 2 Jumps'], f'kept: the kill within range; left out: Jita (42 j), the NPC kills, the 40-minute-old one, QX-LIJ (4 j) {[r["sys"] for r in kills]}')
    check(kills and kills[0]['ty'] == 'Neutral killed' and kills[0]['lines'] == [['Anouk Morrow', 'lost a', 'Venture', '4.1M ISK'], ['by', 'Kirra Longtail', 'Sabre', 'solo', 'zKillboard ↗']] and ' kn' in kills[0]['cls'],
          f'a solo kill row: "Neutral killed" (v.100: by who died) {kills[:1]}')
    al0 = pg.evaluate("() => [__fs.beeps, __fs.notes.length]")
    check(al0 == [0, 0], f'kills read at the start: shown, no alert {al0}')
    # ---- live ----
    SEQ['last'] += 4; L0 = B0 + 5
    REC[L0] = LIVE; REC[L0 + 1] = FRIENDLY; REC[L0 + 2] = LIVE; REC[L0 + 3] = HKILL   # the third: a reprocessed copy
    pg.wait_for_timeout(9000)
    note = pg.evaluate(NOTE)
    check(note == '', f'the feed up and nothing new: no INTEL-05 note (v.99: a missing kill read as the feed being down) {note!r}')
    again, per_s = gaps_ok()
    check(again and min(again) >= 5.9 and per_s <= 15, f'a missing kill not asked for again within 6 s ({sorted(round(x, 1) for x in again)[:4]}); at most {per_s} requests in any second')
    R = pg.evaluate(ROWS)
    k8 = [r for r in R if r['ty'] in LABELS and r['sys'] == '8WA-Z6 1 Jump']
    check(len(k8) == 1 and k8[0]['ty'] == 'Friendly lost' and ' kf' in k8[0]['cls'] and k8[0]['lines'] == [[FRIEND, 'lost a', 'Sabre', '62.4M ISK'], ['by', 'Marrek Ketter', 'Vedmak', '+2 more', 'zKillboard ↗']],
          f'the live kill: "Friendly lost"; victim lost a Sabre and its ISK; by the final blow in a Vedmak, +2 more; the reprocessed copy not again {k8}')
    kn = [(r['ty'], r['cls'].split()[-1]) for r in R if r['sys'] and r['sys'].startswith(('MO-GZ5', 'Y-OMTZ')) and r['ty'] in LABELS]
    check(sorted(kn) == [('Hostile killed', 'kh'), ('Neutral killed', 'kn')], f'kills by friendlies only of a hostile and of a neutral: shown with "hide friendly" on (the owner: "Definitely show enemy kills as well") {kn}')
    look = pg.evaluate("""() => { const r = [...document.querySelectorAll('#itFeedList .it-fd.kill')].find(x => x.querySelector('.it-chip.sys').textContent.startsWith('8WA-Z6'));
      const c = [...r.querySelectorAll('.it-chip.p')].find(x => x.querySelector('.nm').textContent === 'Marrek Ketter'), v = r.querySelector('.it-chip.p');
      return [c.className, c.querySelector('svg.it-st').getAttribute('class'), c.querySelectorAll('.it-lg').length, c.querySelector('.it-tks').textContent, v.className.includes(' f'), v.querySelector('svg.it-st').getAttribute('class'), r.querySelector('.it-sn').className, r.querySelector('.it-chip.sys').title, r.querySelector('a.it-zk').href]; }""")
    check(look == ['it-chip p h', 'it-st bad', 2, '[RLH]<CRTS>', True, 'it-st corp', 'it-sn ns s0', '8WA-Z6 (security -0.3)', 'https://zkillboard.com/kill/9200010/'],
          f"who's who: standing icons (hostile -, your corporation's star), logos, name coloured, tickers; the system's security tenth and title; the zKillboard link {look}")
    tenths = pg.evaluate("() => [1.0, 0.96, 0.946, 0.5, 0.45, 0.449, 0.15, 0.04, 0.0, -0.31].map((v, i) => { it.sec.set(-1 - i, v); const r = [itSecClass(-1 - i), itSecText(-1 - i)]; it.sec.delete(-1 - i); return r; })")
    check(tenths == [['hs s10', '1.0'], ['hs s10', '1.0'], ['hs s9', '0.9'], ['hs s5', '0.5'], ['hs s5', '0.5'], ['ls s4', '0.4'], ['ls s2', '0.2'], ['ls s1', '0.1'], ['ns s0', '0.0'], ['ns s0', '-0.3']],
          f"security as EVE shows it: the nearest tenth, and above 0.0 but under 0.05 shows 0.1 (low-sec) {tenths}")
    near = pg.evaluate("() => [...document.querySelectorAll('#itNearList .it-nb')].map(r => [r.querySelector('.sys').textContent, r.querySelector('.st').textContent, r.querySelector('.who').textContent, r.classList.contains('alert'), [...r.querySelectorAll('.it-kl')].map(k => k.className)])")
    n8 = next((r for r in near if r[0] == '8WA-Z6'), None); nd = next((r for r in near if r[0] == 'D-W7F0'), None)
    check(n8 == ['8WA-Z6', '2 hostile 1 friendly lost', 'Marrek Ketter, Seren Ketter · Vedmak, Sabre', True, ['it-kl kf']] and nd == ['D-W7F0', '1 neutral 1 neutral killed', 'Kirra Longtail · Sabre', True, ['it-kl kn']]
          and not any(r[0] in ('MO-GZ5', 'Y-OMTZ') for r in near),
          f"Near You: a kill marks its system with the attackers and their ships; the badge in the Feed's words and colour; kills by friendlies only no row {near}")
    al = pg.evaluate("() => [__fs.beeps, __fs.notes]")
    check(al[0] == 1 and al[1] == [['8WA-Z6 · 1 jump', f'Friendly lost: {FRIEND} lost a Sabre (62.4M ISK)']], f'the live kill alerts: sound and notification "Friendly lost: ..."; kills by friendlies only do not {al}')
    pr = pg.evaluate("() => { const st = it.near.get(it.names.byLower.get('8wa-z6')); return Object.fromEntries([...st.pairs].map(([id, s]) => [st.pilots.find(x => x.id === id).name, s.name])); }")
    check(pr == {'Marrek Ketter': 'Vedmak', 'Seren Ketter': 'Sabre'}, f'each attacker paired with their ship {pr}')
    pg.evaluate("() => [...[...document.querySelectorAll('#itFeedList .it-fd.kill')].find(x => x.querySelector('.it-chip.sys').textContent.startsWith('8WA-Z6')).querySelectorAll('.it-chip.p')].find(x => x.querySelector('.nm').textContent === 'Marrek Ketter').click()")
    pg.wait_for_function("() => !document.querySelector('#fitBtn').disabled && document.querySelector('#pilotBusy').hidden", timeout=120000); pg.wait_for_timeout(300)
    got = pg.evaluate("() => [document.querySelector('#pilotName').value, document.querySelector('#manualShip').value]")
    check(got == ['Marrek Ketter', 'Vedmak'], f'a pilot on a kill opens in the ship they flew {got}')
    pg.click('#tabBtnIntel'); pg.wait_for_timeout(300)
    # ---- far behind (a sleeping tab): the page finds the newest again ----
    pg.evaluate(f"() => {{ it.kf.seq = {START - 1500}; it.kf.found = 0; it.kf.head = true; it.kf.waitUntil = 0; }}")
    pg.wait_for_timeout(9000)
    kf = pg.evaluate("() => [it.kf.seq, it.kf.found > 0, it.kf.head]")
    check(kf[0] >= SEQ['last'] - 240 and kf[1], f'far behind (kills uploaded 2 h ago): it finds the newest again and reads from there {kf} (newest {SEQ["last"]})')
    # ---- the filters ----
    def rows(): return pg.evaluate(ROWS)
    pg.select_option('[data-it-f="types"]', 'kills'); pg.wait_for_timeout(200)
    check(all(r['ty'] in LABELS for r in rows()) and len(rows()) == 4, f'Types: kills only {[r["ty"] for r in rows()]}')
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
    check(kk == ['8WA-Z6 1 Jump', 'Y-OMTZ 3 Jumps'], f'Search by ticker: "crts" finds the kills with Crimson Tide pilots in them {kk}')
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
    SEQ['fail'] = True; pg.evaluate("() => { it.kf.waitUntil = 0; }"); pg.wait_for_timeout(3000)
    note = pg.evaluate(NOTE)
    W(pg, F_INTEL, line(time.time(), 'Scout Alt', 'T5ZI-S Kirra Longtail loki')); pg.wait_for_timeout(2600)
    still = pg.evaluate("() => [...document.querySelectorAll('#itFeedList .raw')].some(r => r.textContent.endsWith('T5ZI-S Kirra Longtail loki'))")
    check(note.endswith('(INTEL-05)') and still, f'R2Z2 failing (sequence.json too): INTEL-05, reports carry on ({note!r})')
    SEQ['fail'] = False; pg.evaluate("() => { it.kf.waitUntil = 0; }")
    for _ in range(20):
        if pg.evaluate("() => !document.querySelector('[data-it-kfnote]')"): break
        pg.wait_for_timeout(500)
    check(pg.evaluate("() => !document.querySelector('[data-it-kfnote]')"), f'R2Z2 back: the note goes {pg.evaluate("() => [it.kf.busy, it.kf.head, it.kf.fails, it.kf.waitUntil - Date.now()]")}')
    pg.click('#intelHdrLabel'); pg.wait_for_timeout(500); n0 = len(REQS); pg.wait_for_timeout(8000)
    check(len(REQS) == n0, f'off: no requests to R2Z2 ({len(REQS) - n0})')
    pg.screenshot(path='/tmp/intel100_1440.png', full_page=True)
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
