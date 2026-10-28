"""Intel: kills nearby in the Feed, who's who, the Feed's filters (v2026.10.14.99; roadmap/intel-plan.md N1/N2, mockup
Claude outputs/intel_feed_kills_mockup.html).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/intel_kills_check.py [index.html]   -> 'FAILURES: N' (must be 0)

the owner's answers, all as recommended: kills in the Feed "within range" from zKillboard's live feed (R2Z2); "Mark and alert"
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
v2026.10.14.98 fails.
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
SEQ = {'head': 5000, 'fail': False}
REC = {}
REQS = []   # (time, path, status)
def r2z2(route):
    url = route.request.url; path = url.split('r2z2.zkillboard.com')[1]
    if SEQ['fail']: REQS.append((time.time(), path, 503)); return route.fulfill(status=503, body='')
    if path.endswith('/sequence.json'):
        REQS.append((time.time(), path, 200)); return route.fulfill(status=200, content_type='application/json', headers={'access-control-allow-origin': '*'}, body=json.dumps({'sequence': SEQ['head']}))
    m = re.search(r'/ephemeral/(\d+)\.json$', path)
    n = int(m.group(1)) if m else -1
    if n in REC:
        REQS.append((time.time(), path, 200)); return route.fulfill(status=200, content_type='application/json', headers={'access-control-allow-origin': '*'}, body=json.dumps(dict(REC[n], sequence_id=n)))
    REQS.append((time.time(), path, 404)); return route.fulfill(status=404, body='')
SEC = {'Jita': 0.946, 'New Caldari': 0.95}
def esi2(route):
    m = re.search(r'/universe/systems/(\d+)/', route.request.url)
    if m:
        i = int(m.group(1)); nm = SYSNAME.get(i, '')
        return route.fulfill(status=200, content_type='application/json', body=json.dumps({'system_id': i, 'name': nm, 'security_status': SEC.get(nm, -0.31)}))
    return esi(route)
B0 = SEQ['head'] - 240   # where the page starts reading (IT_KILL_BACK)
K_HIST = km(9200001, 'D-W7F0', 300, who('Anouk Morrow'), 'Venture', [(who('Kirra Longtail'), 'Sabre')], 4.1e6)
REC.update({B0: K_HIST,
            B0 + 1: km(9200002, 'Jita', 200, who('Seren Morrow'), 'Rifter', [(who('Seren Ketter'), 'Sabre')], 1e6),            # 42 jumps: out
            B0 + 2: km(9200003, '8WA-Z6', 150, who('Corvin Morrow'), 'Rifter', [(who('Marrek Ketter'), 'Vedmak')], 2e6, npc=True),   # NPC: out
            B0 + 3: km(9200004, 'T5ZI-S', 2400, who('Corvin Morrow'), 'Rifter', [(who('Marrek Ketter'), 'Vedmak')], 2e6),        # 40 min old: out
            B0 + 4: km(9200005, 'QX-LIJ', 100, who('Corvin Morrow'), 'Rifter', [(who('Marrek Ketter'), 'Vedmak')], 2e6)})         # 4 jumps: out
LIVE = km(9200010, '8WA-Z6', 40, who(FRIEND), 'Sabre', [(who('Marrek Ketter'), 'Vedmak'), (who('Seren Ketter'), 'Sabre')], 62.4e6)
LIVE['esi']['attackers'].append({'corporation_id': 1000125, 'ship_type_id': M.byname['Rifter'], 'final_blow': False, 'damage_done': 5})   # an NPC attacker
LIVE['zkb']['attackerCount'] = 3
FRIENDLY = km(9200011, 'MO-GZ5', 30, who('Seren Morrow'), 'Rifter', [(who(FRIEND2), 'Loki')], 3e6)
ROWS = """() => [...document.querySelectorAll('#intelPanel #itFeedList .it-fd')].map(r => ({ty: (r.querySelector('.it-ty') || {}).textContent, sys: (r.querySelector('.it-chip.sys') || {}).textContent,
  lines: [...r.querySelectorAll(':scope > .it-chips')].map(c => [...c.children].map(x => x.classList.contains('it-chip') ? (x.querySelector('.nm') || x).textContent.trim() : x.textContent.trim()))}))"""
def gaps_ok():
    eph = [(t, s) for t, p, s in REQS if '/ephemeral/' in p and not p.endswith('/sequence.json')]
    after404 = [eph[i + 1][0] - eph[i][0] for i in range(len(eph) - 1) if eph[i][1] == 404]
    per_s = max((sum(1 for u, _, _ in REQS if t <= u < t + 1) for t, _, _ in REQS), default=0)
    return after404, per_s

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
    pg.wait_for_timeout(5000)
    seq = [p_ for _, p_, _ in REQS]
    check(seq[:2] == ['/ephemeral/sequence.json', f'/ephemeral/{B0}.json'] and seq[2:7] == [f'/ephemeral/{B0 + i}.json' for i in range(1, 6)],
          f'R2Z2: sequence.json, then the numbered files one by one from about 15 minutes back {seq[:8]}')
    R = pg.evaluate(ROWS)
    kills = [r for r in R if r['ty'] == 'Kill']
    check([r['sys'] for r in kills] == ['D-W7F0 2j'], f'kept: the kill within range; left out: Jita (42 j), the NPC kill, the 40-minute-old one, QX-LIJ (4 j) {[r["sys"] for r in kills]}')
    check(kills and kills[0]['lines'] == [['Anouk Morrow', 'lost a', 'Venture', '4.1M ISK'], ['by', 'Kirra Longtail', 'Sabre', 'solo', 'zKillboard ↗']], f'a solo kill row {kills[:1]}')
    al0 = pg.evaluate("() => [__fs.beeps, __fs.notes.length]")
    check(al0 == [0, 0], f'kills read at the start: shown, no alert {al0}')
    # ---- live ----
    REC[SEQ['head'] - 240 + 5] = LIVE; REC[SEQ['head'] - 240 + 6] = FRIENDLY; REC[SEQ['head'] - 240 + 7] = LIVE   # the last: a reprocessed copy
    pg.wait_for_timeout(9000)
    after404, per_s = gaps_ok()
    check(after404 and min(after404) >= 5.9 and per_s <= 15, f'after a 404 nothing for 6 s ({[round(x, 1) for x in after404][:4]}); at most {per_s} requests in any second')
    R = pg.evaluate(ROWS)
    k8 = [r for r in R if r['ty'] == 'Kill' and r['sys'] == '8WA-Z6 1j']
    check(len(k8) == 1 and k8[0]['lines'] == [[FRIEND, 'lost a', 'Sabre', '62.4M ISK'], ['by', 'Marrek Ketter', 'Vedmak', '+2 more', 'zKillboard ↗']],
          f'the live kill: victim lost a Sabre and its ISK; by the final blow in a Vedmak, +2 more; the reprocessed copy not again {k8}')
    check(not any(r['sys'] and r['sys'].startswith('MO-GZ5') and r['ty'] == 'Kill' for r in R), 'a kill by friendlies only: hidden (hide friendlies on)')
    look = pg.evaluate("""() => { const r = [...document.querySelectorAll('#itFeedList .it-fd.kill')].find(x => x.querySelector('.it-chip.sys').textContent.startsWith('8WA-Z6'));
      const c = [...r.querySelectorAll('.it-chip.p')].find(x => x.querySelector('.nm').textContent === 'Marrek Ketter'), v = r.querySelector('.it-chip.p');
      return [c.className, !!c.querySelector('.it-mk.h'), c.querySelectorAll('.it-lg').length, c.querySelector('.it-tks').textContent, v.className.includes(' f'), r.querySelector('.it-sn').className, r.querySelector('a.it-zk').href]; }""")
    check(look == ['it-chip p h', True, 2, '[RLH]<CRTS>', True, 'it-sn ns', 'https://zkillboard.com/kill/9200010/'],
          f"who's who: standing mark, corp and alliance logos, name coloured, tickers; the victim friendly; system coloured by security; the zKillboard link {look}")
    near = pg.evaluate("() => [...document.querySelectorAll('#itNearList .it-nb')].map(r => [r.querySelector('.sys').textContent, r.querySelector('.st').textContent, r.querySelector('.who').textContent, r.classList.contains('alert')])")
    n8 = next((r for r in near if r[0] == '8WA-Z6'), None); nd = next((r for r in near if r[0] == 'D-W7F0'), None)
    check(n8 == ['8WA-Z6', '2 hostile 1 kill', 'Marrek Ketter, Seren Ketter · Vedmak, Sabre', True] and nd == ['D-W7F0', '1 neutral 1 kill', 'Kirra Longtail · Sabre', True] and not any(r[0] == 'MO-GZ5' for r in near),
          f'Near You: a kill marks its system with the attackers and their ships, "1 kill"; the friendly-only kill not {near}')
    al = pg.evaluate("() => [__fs.beeps, __fs.notes]")
    check(al[0] == 1 and al[1] == [['8WA-Z6 · 1 jump', f'Kill: {FRIEND} lost a Sabre (62.4M ISK)']], f'the live kill alerts: sound and notification; the friendly-only kill does not {al}')
    pr = pg.evaluate("() => { const st = it.near.get(it.names.byLower.get('8wa-z6')); return Object.fromEntries([...st.pairs].map(([id, s]) => [st.pilots.find(x => x.id === id).name, s.name])); }")
    check(pr == {'Marrek Ketter': 'Vedmak', 'Seren Ketter': 'Sabre'}, f'each attacker paired with their ship {pr}')
    pg.evaluate("() => [...document.querySelectorAll('#itFeedList .it-fd.kill .it-chip.p')].find(x => x.querySelector('.nm').textContent === 'Marrek Ketter').click()")
    pg.wait_for_function("() => !document.querySelector('#fitBtn').disabled && document.querySelector('#pilotBusy').hidden", timeout=120000); pg.wait_for_timeout(300)
    got = pg.evaluate("() => [document.querySelector('#pilotName').value, document.querySelector('#manualShip').value]")
    check(got == ['Marrek Ketter', 'Vedmak'], f'a pilot on a kill opens in the ship they flew {got}')
    pg.click('#tabBtnIntel'); pg.wait_for_timeout(300)
    # ---- the filters ----
    def rows(): return pg.evaluate(ROWS)
    pg.select_option('[data-it-f="types"]', 'kills'); pg.wait_for_timeout(200)
    check(all(r['ty'] == 'Kill' for r in rows()) and len(rows()) == 2, f'Types: kills only {[r["ty"] for r in rows()]}')
    pg.select_option('[data-it-f="types"]', 'reports'); pg.wait_for_timeout(200)
    check(rows() and all(r['ty'] != 'Kill' for r in rows()), 'Types: reports only')
    pg.select_option('[data-it-f="types"]', 'all'); pg.select_option('[data-it-f="dist"]', '1'); pg.wait_for_timeout(200)
    js = [int(re.search(r'(\d+)j$', r['sys']).group(1)) for r in rows() if r['sys']]
    check(js and max(js) <= 1, f'Distance ≤ 1 jump {js}')
    pg.select_option('[data-it-f="dist"]', '0'); pg.select_option('[data-it-f="sort"]', 'near'); pg.wait_for_timeout(200)
    js = [int(re.search(r'(\d+)j$', r['sys']).group(1)) for r in rows() if r['sys'] and re.search(r'\dj$', r['sys'])]
    check(js == sorted(js) and len(js) >= 3, f'Sort: nearest first {js}')
    pg.select_option('[data-it-f="sort"]', 'new')
    pg.fill('[data-it-q]', 'ketter'); pg.wait_for_timeout(200)
    check(rows() and all('Ketter' in json.dumps(r) for r in rows()), f'Search by name: "ketter" {len(rows())} rows')
    pg.fill('[data-it-q]', 'crts'); pg.wait_for_timeout(200)
    kk = [r for r in rows() if r['ty'] == 'Kill']
    check(len(kk) == 1 and kk[0]['sys'] == '8WA-Z6 1j', f'Search by ticker: "crts" finds the kill by Crimson Tide pilots {[r["sys"] for r in kk]}')
    pg.focus('[data-it-q]'); pg.keyboard.type('x'); pg.wait_for_timeout(4500)
    foc = pg.evaluate("() => [document.activeElement.matches('[data-it-q]'), document.activeElement.value, document.activeElement.selectionStart]")
    check(foc == [True, 'crtsx', 5], f'the search box keeps its focus and text while the lists redraw {foc}')
    pg.fill('[data-it-q]', ''); pg.select_option('[data-it-f="types"]', 'kills')
    st = pg.evaluate("() => JSON.parse(localStorage.getItem('dscanIntel')).feed")
    check(st == {'types': 'kills', 'dist': 0, 'sort': 'new'}, f'the filters kept in this browser {st}')
    pg.select_option('[data-it-f="types"]', 'all')
    # ---- R2Z2 failing, then back; off: no requests ----
    SEQ['fail'] = True; pg.evaluate("() => { it.kf.waitUntil = 0; }"); pg.wait_for_timeout(3000)
    note = pg.evaluate("() => (document.querySelector('[data-it-kfnote]') || {}).textContent || ''")
    W(pg, F_INTEL, line(time.time(), 'Scout Alt', 'T5ZI-S Kirra Longtail loki')); pg.wait_for_timeout(2600)
    still = pg.evaluate("() => [...document.querySelectorAll('#itFeedList .raw')].some(r => r.textContent.endsWith('T5ZI-S Kirra Longtail loki'))")
    check(note.endswith('(INTEL-05)') and still, f'R2Z2 failing: INTEL-05, reports carry on ({note!r})')
    SEQ['fail'] = False; pg.evaluate("() => { it.kf.waitUntil = 0; }"); pg.wait_for_timeout(3000)
    check(pg.evaluate("() => !document.querySelector('[data-it-kfnote]')"), 'R2Z2 back: the note goes')
    pg.click('#intelHdrLabel'); pg.wait_for_timeout(500); n0 = len(REQS); pg.wait_for_timeout(8000)
    check(len(REQS) == n0, f'off: no requests to R2Z2 ({len(REQS) - n0})')
    pg.screenshot(path='/tmp/intel99_1440.png', full_page=True)
    ctx.close()
    # ---- phone ----
    REQS.clear(); ctx, pg = start(390); pg.wait_for_timeout(9000)
    over = pg.evaluate("() => [document.documentElement.scrollWidth, [...document.querySelectorAll('#intelPanel *')].filter(e => { const r = e.getBoundingClientRect(); return r.width && (r.right > innerWidth + 1 || r.left < -1); }).map(e => e.className || e.tagName).slice(0, 5), Math.min(...[...document.querySelectorAll('.it-fbar select, .it-fbar input')].map(e => e.getBoundingClientRect().height))]")
    check(over[0] <= 390 and not over[1] and over[2] >= 40, f'390 px: nothing off the page, the bar 40 px {over}')
    pg.screenshot(path='/tmp/intel99_390.png', full_page=True)
    ctx.close()
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f"FAILURES: {NS['fails']}")
sys.exit(1 if NS['fails'] else 0)
