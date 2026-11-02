"""Kills and losses in the system over the past N hours (v2026.11.02.3; Project doc roadmap/system-activity-plan.md).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/system_activity_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner: "add combined losses and kills they've accrued in the past "N hours" in the system being analyzed (user's location or
system row linked from intel tab) ... provide two clickable links to losses and kills (provide total isk value of both) ... the
same with hull types"; "1,3,6,12,24,48,72 capped at 72"; "the number will be tied to the entity represented at the top level";
hull numbers "in the non-hover content"; before the build: gate systems only. Stand-ins only, never the real zKillboard: a made-up
system with 40 killmails over 80 h (zKillboard's list holds the 37 within its 72 h), invented pilots and alliances (sa_mocks.py).
Everything expected is worked out here from those killmails. Checks:
  * for N = 1, 6, 24, 72: the summary (kills, ISK destroyed), every alliance / corporation group's ▲ kills and ▼ losses with ISK, the
    corporations' and pilots' compact numbers, the hull lines in the scan rail; a kill counts once per entity with its whole
    value; NPC attackers count for nobody; an NPC's kill of a player is that player's group's loss; the NPC fold shows no total;
    a quiet group says so;
  * requests: 1 zKillboard request for the first Analyze, none for changing N or a second Analyze, 1 for another system and 1 for
    Refresh; ESI reads stop at the window (in steps of 10) or at 300;
  * caps: 412 kills in 20 h: "counted from the newest 300 of 412"; a full 1,000 list reaching back 31 h: "only reach back 31 h";
  * the system: an Intel Assess wins over the setting; My location from Intel (off with Intel off); a typed unknown name: SYS-03,
    not saved; no system: the note and no request; the links' exact addresses (alliance, corporation, hull, system);
  * settings kept across a reload, old saves get the defaults, Off: no request and no lines; the small-gang Pilots rows;
  * 390 px: nothing off the page, the links 44 px tall; the settings' close button top right, Esc, the focus back on ⚙.
v2026.11.02.2 fails (no line).
"""
import sys, os, re, json, time, hashlib, calendar
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from playwright.sync_api import sync_playwright
import sa_mocks as M

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok
B = M.byname
SYS, SYS2, SYS3, SYS4 = 30004759, 30002187, 30000142, 30003001   # 1DQ1-A, Amarr, Jita (made-up kills); a 4th for the full list
NAMES = {SYS: '1DQ1-A', SYS2: 'Amarr', SYS3: 'Jita', SYS4: 'Made-Up Four'}
crts = M._crts; void = M._void
lbt = [i for i, v in M.PILOTS.items() if v[1] == 98000013]   # Lantern Bay Traders: a corporation with no alliance
npc = [i for i, v in M.PILOTS.items() if v[1] == 1000167]
def iso(h): return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - h * 3600))
def pat(cid, hull, final=False): return dict(M.aff(cid), ship_type_id=B[hull], damage_done=100, final_blow=final, security_status=0)
NPC_ATT = {'faction_id': 500001, 'ship_type_id': B['Rifter'], 'damage_done': 5, 'final_blow': False, 'security_status': 0}
_k = [9900000]
VAL = {}
def mk(h, victim, vhull, atts, val, sysid=SYS):
    _k[0] += 1; k = _k[0]
    v = dict(M.aff(victim), ship_type_id=B[vhull], damage_taken=1000, items=[], position={'x': 0, 'y': 0, 'z': 0})
    M.KM[k] = {'killmail_id': k, 'killmail_time': iso(h), 'solar_system_id': sysid, 'victim': v, 'attackers': atts}
    M.H[k] = hashlib.sha1(str(k).encode()).hexdigest(); VAL[k] = val; return k
# 40 kills, one every 2 h from 0.5 h ago (0.5, 2.5 ... 78.5): who on whom cycles through the cases
KILLS = [None] * 40
for i in reversed(range(40)):   # made oldest first: killmail IDs grow with time, as zKillboard's do (its list is newest first by ID)
    h = 0.5 + 2 * i; val = (i + 1) * 12_345_678
    c = i % 8
    if c == 0: KILLS[i] = mk(h, void[i % 5], 'Vedmak', [pat(crts[i % 7], 'Curse', True), pat(crts[(i + 1) % 7], 'Ferox')], val)       # CRTS kill VOIDR
    elif c == 1: KILLS[i] = mk(h, crts[i % 7], 'Ferox', [pat(void[i % 5], 'Vedmak', True), pat(void[(i + 2) % 5], 'Vedmak')], val)  # VOIDR kill CRTS (two VOIDR pilots: once)
    elif c == 2: KILLS[i] = mk(h, lbt[i % 3], 'Sabre', [pat(crts[i % 7], 'Curse', True), pat(void[i % 5], 'Vedmak')], val)          # both alliances on one kill
    elif c == 3: KILLS[i] = mk(h, crts[(i + 3) % 7], 'Capsule', [pat(void[i % 5], 'Vedmak', True)], val)                           # a pod
    elif c == 4: KILLS[i] = mk(h, void[i % 5], 'Vedmak', [dict(NPC_ATT, final_blow=True)], val)                                     # NPCs kill a player
    elif c == 5: KILLS[i] = mk(h, npc[0], 'Ferox', [pat(lbt[i % 3], 'Sabre', True), NPC_ATT], val)                                  # LBT kill an NPC-corp pilot (NPC helping)
    elif c == 6: KILLS[i] = mk(h, crts[i % 7], 'Curse', [pat(lbt[i % 3], 'Sabre', True), pat(npc[1], 'Ferox')], val)              # LBT + an NPC-corp pilot
    else: KILLS[i] = mk(h, lbt[i % 3], 'Sabre', [pat(crts[i % 7], 'Ferox', True)], val)
LIST = [k for k in KILLS if (0.5 + 2 * KILLS.index(k)) <= 72]
# caps: 412 kills in 20 h (Amarr); a full 1,000 list over 31 h (Made-Up Four)
BIG = [mk(19.9 * j / 411, crts[j % 7], 'Ferox', [pat(void[j % 5], 'Vedmak', True)], 1_000_000, SYS2) for j in reversed(range(412))]
FULL = [mk(31 * j / 999, crts[j % 7], 'Ferox', [pat(void[j % 5], 'Vedmak', True)], 1_000_000, SYS4) for j in reversed(range(1000))]
ZLISTS = {SYS: LIST, SYS2: BIG, SYS3: [], SYS4: FULL}
SYSCALLS, KMREADS = [], []
def sysroute(route):
    m = re.search(r'/kills/systemID/(\d+)/pastSeconds/(\d+)/', route.request.url)
    SYSCALLS.append(route.request.url)
    ids = ZLISTS.get(int(m.group(1)), []) if m and m.group(2) == '259200' else []
    route.fulfill(status=200, content_type='application/json', headers={'access-control-allow-origin': '*'},
                  body=json.dumps([{'killmail_id': k, 'zkb': {'hash': M.H[k], 'totalValue': VAL[k]}} for k in sorted(ids, reverse=True)]))
def kmroute(route):
    m = re.search(r'/killmails/(\d+)/', route.request.url)
    if m and int(m.group(1)) in VAL: KMREADS.append(int(m.group(1)))
    M.esi(route)

def isk(v): return f'{v / 1e9:.2f}B' if v >= 1e9 else f'{v / 1e6:.1f}M' if v >= 1e6 else f'{round(v / 1e3)}k' if v >= 1e3 else str(round(v))
def word(n, one, many): return f"{n} {one if n == 1 else many}"
def expected(N, kills=LIST):
    cut = time.time() - N * 3600
    E = {'kills': 0, 'isk': 0, 'a': {}, 'c': {}, 'p': {}, 'h': {}}
    def add(m, i, kill, v):
        if not i: return
        e = E[m].setdefault(i, [0, 0, 0, 0])
        if kill: e[0] += 1; e[1] += v
        else: e[2] += 1; e[3] += v
    for k in kills:
        km = M.KM[k]; t = calendar.timegm(time.strptime(km['killmail_time'], '%Y-%m-%dT%H:%M:%SZ'))
        if t < cut: continue
        v = VAL[k]; V = km['victim']; E['kills'] += 1; E['isk'] += v
        add('a', V.get('alliance_id'), False, v); add('c', V.get('corporation_id'), False, v); add('p', V.get('character_id'), False, v); add('h', V['ship_type_id'], False, v)
        P = [a for a in km['attackers'] if a.get('character_id')]
        for m, f in (('a', 'alliance_id'), ('c', 'corporation_id'), ('p', 'character_id'), ('h', 'ship_type_id')):
            for i in {a.get(f) for a in P if a.get(f)}: add(m, i, True, v)
    return E
LOCAL = '\n'.join(sorted({M.PILOTS[i][0] for i in crts[:7] + void[:5] + lbt[:3] + npc[:2]} | {v[0] for v in M.PILOTS.values() if v[1] == 98000004}))
SCAN = '\n'.join(f"{B[t]}\tSomeone's {t}\t{t}\t{12 + i} km" for i, t in enumerate(['Ferox', 'Vedmak', 'Curse', 'Sabre', 'Capsule', 'Rifter']))
G = """() => Object.fromEntries([...document.querySelectorAll('#saResults details.sa-g[data-sa-g]')].filter(d => d.dataset.saG !== 'friendly').map(d => [d.dataset.saG,
  {act: [...d.querySelectorAll(':scope > summary .sa-act-g a.zk-t')].map(a => [a.textContent, a.getAttribute('href')]), quiet: (d.querySelector(':scope > summary .sa-act-g.quiet') || {}).textContent || '',
   corps: [...d.querySelectorAll('.sa-corp')].map(c => [...c.querySelectorAll('.sa-act-m a')].map(a => [a.textContent, a.getAttribute('href')])),
   pilots: Object.fromEntries([...d.querySelectorAll('.sa-pilot')].map(b => [b.dataset.pilot, (b.querySelector('.sa-act-m') || {}).textContent || '']))}]))"""
H = """() => Object.fromEntries([...document.querySelectorAll('#scanRail .sr-r')].map(r => [r.querySelector('button.sr-row').dataset.sr, [...r.querySelectorAll('.sr-act a')].map(a => [a.textContent, a.getAttribute('href')])]))"""
SUM = "() => { const e = document.querySelector('#saAct'); return e && !e.hidden ? e.innerText.replace(/\\s+/g, ' ').trim() : null; }"
def wait_act(pg, timeout=60000):
    pg.wait_for_function("() => sa.act && !sa.act.busy && (sa.act.list || sa.act.none || sa.act.err)", timeout=timeout); pg.wait_for_timeout(300)
def analyze(pg, local=LOCAL, scan=SCAN):
    pg.click('#tabBtnDscan'); pg.fill('#localInput', local); pg.fill('#dscanInput', scan); pg.click('#analyzeBtn'); pg.wait_for_timeout(300)
    pg.wait_for_function("() => !document.querySelector('#analyzeBtn').disabled", timeout=120000); wait_act(pg)
def gear(pg):
    if pg.evaluate("() => document.querySelector('#saPop').hidden"): pg.click('#saGear'); pg.wait_for_timeout(150)
def setwin(pg, n):
    gear(pg); pg.select_option('#saPop select[data-sa-set="win"]', str(n)); pg.wait_for_timeout(200); wait_act(pg)
SEED = """(n) => { const byId = new Map(Object.entries(n).map(([k, v]) => [Number(k), v])); it.names = {byId, byLower: new Map([...byId].map(([k, v]) => [v.toLowerCase(), k]))}; }"""
def fresh(b, w=1440, h=1000, sett=None):
    ctx = b.new_context(viewport={'width': w, 'height': h}); M.route(ctx); ctx.route(re.compile(r'https://zkillboard\.com/api/kills/systemID/.*'), sysroute)
    ctx.route(re.compile(r'https://esi\.evetech\.net/.*/killmails/.*'), kmroute)
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('file://' + HTML)
    pg.evaluate(f"(s) => localStorage.setItem('dscanSaSet', JSON.stringify(s))", sett or {'src': 'typed', 'typed': '1DQ1-A'})
    pg.reload(); pg.wait_for_timeout(300); pg.evaluate(SEED, {str(k): v for k, v in NAMES.items()})
    return ctx, pg

errs = []
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx, pg = fresh(b)
    SYSCALLS.clear(); KMREADS.clear()
    analyze(pg)
    n_first = len(SYSCALLS)
    reads24 = len(KMREADS)
    i_old = next((i for i, k in enumerate(LIST) if 0.5 + 2 * i > 24), len(LIST))
    want_reads = min(len(LIST), ((i_old // 10) + 1) * 10)
    check(n_first == 1 and SYSCALLS[0].endswith(f'/kills/systemID/{SYS}/pastSeconds/259200/') and reads24 == want_reads,
          f'the first Analyze: 1 zKillboard request (the system, 72 h); ESI reads stop past the 24 h window, in steps of 10 ({n_first}, {reads24} reads, want {want_reads})')
    for N in (24, 1, 6, 72):
        if N != 24: setwin(pg, N)
        E = expected(N)
        S = pg.evaluate(SUM)
        if E['kills']:
            ok = S and S.startswith(f"Last {N} h in 1DQ1-A · {word(E['kills'], 'kill', 'kills')} · {isk(E['isk'])} ISK destroyed")
        else:
            ok = S and S.startswith(f'Last {N} h in 1DQ1-A: no kills or losses')
        check(ok, f'N={N}: the summary ({S!r}; want {E["kills"]} kills, {isk(E["isk"])})')
        g = pg.evaluate(G)
        def grp(key, kind, gid):
            e = E['a' if kind == 'alliance' else 'c'].get(gid)
            if not e: return {'act': [], 'quiet': f'quiet here in {N} h'}
            out = []
            if e[0]: out.append([f"▲ {word(e[0], 'kill', 'kills')} · {isk(e[1])}", f'https://zkillboard.com/{kind}/{gid}/system/{SYS}/kills/'])
            if e[2]: out.append([f"▼ {word(e[2], 'loss', 'losses')} · {isk(e[3])}", f'https://zkillboard.com/{kind}/{gid}/system/{SYS}/losses/'])
            return {'act': out, 'quiet': ''}
        want = {'n:a99000003': grp('n:a99000003', 'alliance', M.CRTS), 'n:a99000004': grp('n:a99000004', 'alliance', M.VOIDR), 'n:c98000013': grp('n:c98000013', 'corporation', 98000013)}
        got = {k: {'act': g[k]['act'], 'quiet': g[k]['quiet']} for k in want if k in g}
        check(got == want, f'N={N}: each group\'s ▲ kills and ▼ losses with ISK and links (whole value, once per group)\n      page {got}\n      want {want}')
        npcg = g.get('n:npc', {})
        check(npcg and not npcg['act'] and not npcg['quiet'], f'N={N}: the NPC corporations fold shows no total ({npcg and (npcg["act"], npcg["quiet"])})')
        # the corporations' and pilots' compact numbers
        cgot = pg.evaluate("""() => Object.fromEntries([...document.querySelectorAll('#saResults .sa-corp')].map(c => [(c.querySelector('[data-tk-for]') || c).textContent.trim() + '|' + [...c.querySelectorAll('.sa-act-m a')].map(a => a.getAttribute('href')).join(' '),
          [...c.querySelectorAll('.sa-act-m a')].map(a => a.textContent).join(' ')]))""")
        cwant = {}
        for cid in (98000003, 98000004, 98000005, 98000013, 1000167):
            e = E['c'].get(cid)
            if not e: continue
            hrefs = ([f'https://zkillboard.com/corporation/{cid}/system/{SYS}/kills/'] if e[0] else []) + ([f'https://zkillboard.com/corporation/{cid}/system/{SYS}/losses/'] if e[2] else [])
            cwant[' '.join(hrefs)] = ' '.join(([f'▲{e[0]}'] if e[0] else []) + ([f'▼{e[2]}'] if e[2] else []))
        cg = {k.split('|', 1)[1]: v for k, v in cgot.items() if k.split('|', 1)[1]}
        check(cg == cwant, f'N={N}: each corporation\'s compact ▲ ▼ with its links {cg} = {cwant}')
        pgot = {}
        for d in g.values(): pgot.update(d['pilots'])
        pwant = {}
        for pid in crts[:7] + void[:5] + lbt[:3] + npc[:2]:
            e = E['p'].get(pid); nm = M.PILOTS[pid][0]
            pwant[nm] = (f'▲{e[0]}' if e and e[0] else '') + (' ' if e and e[0] and e[2] else '') + (f'▼{e[2]}' if e and e[2] else '')
        pg_ = {k: v for k, v in pgot.items() if k in pwant}; pwant = {k: pwant[k] for k in pg_}
        check(pg_ == pwant and len(pg_) >= 8, f'N={N}: each pilot\'s compact numbers (shown pilots) {sum(1 for v in pg_.values() if v)} with numbers')
        hz = pg.evaluate(H)
        hwant = {}
        for t in ('Ferox', 'Vedmak', 'Curse', 'Sabre', 'Capsule', 'Rifter'):
            e = E['h'].get(B[t]); out = []
            if e and e[2]: out.append([f'▼ {e[2]} lost · {isk(e[3])}', f'https://zkillboard.com/ship/{B[t]}/system/{SYS}/losses/'])
            if e and e[0]: out.append([f"▲ on {word(e[0], 'kill', 'kills')} · {isk(e[1])}", f'https://zkillboard.com/ship/{B[t]}/system/{SYS}/kills/'])
            hwant[str(B[t])] = out
        check(hz == hwant, f'N={N}: the scan rail\'s hull lines (lost, on kills) with links\n      page {hz}\n      want {hwant}')
    check(len(SYSCALLS) == 1, f'changing N asked zKillboard nothing ({len(SYSCALLS)} requests)')
    sl = pg.evaluate("() => document.querySelector('#saAct a.zk-ic').getAttribute('href')")
    check(sl == f'https://zkillboard.com/system/{SYS}/', f'the summary\'s zK icon: the system on zKillboard ({sl})')
    analyze(pg)
    check(len(SYSCALLS) == 1, f'a second Analyze within the hour asks nothing ({len(SYSCALLS)})')
    pg.click('#saResults [data-sa-act="refresh"]') if pg.query_selector('#saResults [data-sa-act="refresh"]') else pg.evaluate("() => runSystemAnalyzer(true)")
    pg.wait_for_timeout(300); pg.wait_for_function("() => !document.querySelector('#analyzeBtn').disabled", timeout=60000); wait_act(pg)
    check(len(SYSCALLS) == 2, f'Refresh asks again ({len(SYSCALLS)})')
    # another system, typed; a typed unknown name; Off
    gear(pg); pg.fill('#saPop input[data-sa-set="typed"]', 'amarr'); pg.press('#saPop input[data-sa-set="typed"]', 'Enter'); pg.wait_for_timeout(300); wait_act(pg)
    S = pg.evaluate(SUM)
    check(len(SYSCALLS) == 3 and S.startswith('Last 72 h in Amarr · 300 kills') and 'counted from the newest 300 of 412' in S and len([k for k in KMREADS if k in BIG]) == 301,
          f'another system: 1 request; 412 kills there: counted from the newest 300 of 412, 300 read (+1: the oldest listed, how far back the list reaches) ({len(SYSCALLS)}, {len([k for k in KMREADS if k in BIG])} reads, {S!r})')
    setwin(pg, 24); S = pg.evaluate(SUM)
    check('counted from the newest 300 of 412' in S, f'... at 24 h too (all 412 are within 20 h) ({S!r})')
    gear(pg); pg.fill('#saPop input[data-sa-set="typed"]', 'Made-Up Four'); pg.press('#saPop input[data-sa-set="typed"]', 'Enter'); pg.wait_for_timeout(300); setwin(pg, 72); wait_act(pg)
    S = pg.evaluate(SUM)
    check('the newest 1,000 kills only reach back 31 h' in S and 'counted from the newest 300 of 1,000' in S, f'a full 1,000 list: how far back it reaches ({S!r})')
    gear(pg); pg.fill('#saPop input[data-sa-set="typed"]', 'Not A System'); pg.press('#saPop input[data-sa-set="typed"]', 'Enter'); pg.wait_for_timeout(300)
    msg = pg.inner_text('#saPop'); kept = pg.evaluate("() => JSON.parse(localStorage.getItem('dscanSaSet')).typed")
    check('(SYS-03)' in msg and kept == 'Made-Up Four', f'a typed name the page doesn\'t know: SYS-03, not saved ({kept})')
    n0 = len(SYSCALLS)
    pg.uncheck('#saPop input[data-sa-set="act"]'); pg.wait_for_timeout(200); analyze_off = None
    pg.click('#analyzeBtn'); pg.wait_for_timeout(300); pg.wait_for_function("() => !document.querySelector('#analyzeBtn').disabled", timeout=60000); pg.wait_for_timeout(500)
    check(len(SYSCALLS) == n0 and pg.evaluate(SUM) is None and not pg.query_selector('#saResults .sa-act-g, #scanRail .sr-act'), 'Off: no request and no lines')
    ctx.close()
    # settings across a reload; old saves get the defaults; no system; My location; an Assess wins
    ctx, pg = fresh(b, sett={'src': 'typed', 'typed': 'Jita', 'win': 6})
    st = pg.evaluate("() => [saSet.act, saSet.win, saSet.src, saSet.typed]")
    pg.evaluate("() => localStorage.setItem('dscanSaSet', JSON.stringify({}))"); pg.reload(); pg.wait_for_timeout(200)
    d = pg.evaluate("() => [saSet.act, saSet.win, saSet.src, saSet.typed]")
    check(st == [True, 6, 'typed', 'Jita'] and d == [True, 24, 'me', ''], f'settings kept across a reload {st}; an old save gets the defaults {d}')
    pg.evaluate(SEED, {str(k): v for k, v in NAMES.items()}); SYSCALLS.clear()
    analyze(pg)
    S = pg.evaluate(SUM)
    check(not SYSCALLS and S and 'Turn Intel on' in S, f'My location with Intel off: the note, no request ({S!r})')
    gear(pg); dis = pg.evaluate("() => document.querySelector('#saPop input[value=me]').disabled")
    check(dis, 'My location is disabled with Intel off')
    pg.evaluate("() => { it.on = true; it.me = {sys: '1DQ1-A'}; }")
    analyze(pg); S = pg.evaluate(SUM)
    check(len(SYSCALLS) == 1 and S.startswith('Last 24 h in 1DQ1-A (your location)'), f'My location from Intel: that system ({S!r})')
    pg.evaluate(f"() => {{ sa.intel = {{sys: {SYS3}, pairs: new Map()}}; runSystemAnalyzer(false); }}"); pg.wait_for_timeout(300); wait_act(pg); S = pg.evaluate(SUM)
    check(S.startswith('Last 24 h in Jita (from Intel): no kills or losses') and len(SYSCALLS) == 2, f'an Intel Assess wins over the setting; a quiet system says so ({S!r})')
    pg.evaluate("() => { sa.intel = null; it.on = false; it.me = null; saSet.src = 'typed'; saSet.typed = ''; }"); SYSCALLS.clear(); analyze(pg); S = pg.evaluate(SUM)
    check(not SYSCALLS and S == 'Pick a system in ⚙ to see kills and losses here', f'no system: the note and no request ({S!r})')
    # a small gang: the Pilots rows get the compact numbers
    pg.evaluate("() => { saSet.typed = '1DQ1-A'; }")
    analyze(pg, '\n'.join(M.PILOTS[i][0] for i in crts[:3]), SCAN)
    rows = pg.evaluate("() => Object.fromEntries([...document.querySelectorAll('#saPilots button.pr-row')].map(b => [b.querySelector('.pr-pilot .nm').firstChild.textContent, (b.querySelector('.sa-act-m') || {}).textContent || '']))")
    E = expected(24)
    rw = {M.PILOTS[i][0]: (f'▲{E["p"][i][0]}' if i in E['p'] and E['p'][i][0] else '') + (' ' if i in E['p'] and E['p'][i][0] and E['p'][i][2] else '') + (f'▼{E["p"][i][2]}' if i in E['p'] and E['p'][i][2] else '') for i in crts[:3]}
    check(rows == rw, f'a small gang: each pilot row\'s compact numbers {rows} = {rw}')
    ctx.close()
    # phone
    ctx, pg = fresh(b, 390); analyze(pg)
    L = pg.evaluate("""() => [document.documentElement.scrollWidth, Math.min(...[...document.querySelectorAll('#saAct a.zk-t, #scanRail .sr-act a, #saResults .sa-act-g a')].filter(a => a.checkVisibility()).map(a => a.getBoundingClientRect().height)),
      [...document.querySelectorAll('#saAct *, #scanRail *')].filter(e => { const b = e.getBoundingClientRect(); return e.checkVisibility() && b.width && (b.right > innerWidth + 1 || b.left < -1); }).map(e => e.className).slice(0, 3)]""")
    gear(pg); gb = pg.evaluate("() => { const b = document.querySelector('#saPop').getBoundingClientRect(); return [Math.round(b.left), Math.round(b.right), document.querySelector('#saGear').getBoundingClientRect().height]; }")
    check(L[0] <= 390 and L[1] >= 44 and not L[2] and gb[0] >= 0 and gb[1] <= 390 and gb[2] >= 44, f'390 px: nothing off the page, links 44 px, the settings inside the window, gear 44 px {L} {gb}')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    check(pg.evaluate("() => document.querySelector('#saPop').hidden && document.activeElement && document.activeElement.id === 'saGear'"), 'Esc closes the settings, the focus back on ⚙')
    gear(pg); xb = pg.evaluate("() => { const x = document.querySelector('#saPop button.x-close'), p = document.querySelector('#saPop').getBoundingClientRect(), b = x.getBoundingClientRect(); return [Math.round(b.height), b.right > p.right - 40, b.top < p.top + 40]; }")
    pg.click('#saPop button.x-close'); pg.wait_for_timeout(150)
    check(xb[0] >= 44 and xb[1] and xb[2] and pg.evaluate("() => document.querySelector('#saPop').hidden && document.activeElement.id === 'saGear'"), f'the shared close button, top right (44 px on a phone), closes it {xb}')
    ctx.close()
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
