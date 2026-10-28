"""Intel, delivery 1 (v2026.10.14.96; roadmap/intel-plan.md).

    PYFA_SRC=/path/to/pyfa [EVE_RES=/path] python3 -I tools/page_checks/intel_check.py [index.html]   -> 'FAILURES: N' (must be 0)

the owner: "the tool actively polls the game's chat log for the intel channel and tracks neutral and hostile ships that are
reported via that channel"; "it needs to have an on/off mechanism"; mockup answers: the feed in a card on its own tab, a gear
for settings, "a slider for off/on similar just like 'use in assessments'", jumps from a built-in table that doesn't drift
from EVE. The real page with a made-up Chatlogs folder (the File System Access API replaced by an in-page folder of
UTF-16 LE files written the way EVE writes them: BOM on every line, CRLF, EVE time), ESI from sa_mocks.py, and the system
names: the real names of the 17 systems within 4 jumps of 1DQ1-A, Jita and New Caldari, a made-up "QX-LOO" far away, and
"N<id>" for the rest. Every pilot and character name is made up. Checks:
  * the Intel tab after the System Analyzer; the Intel slider beside Standings, off, the only on/off switch (v.97: none on
    the card); the card's four setup boxes;
  * Choose folder: the channels of the last 2 days (a 3-day-old Corp log left out), both characters with their systems;
  * the Intel slider turns it on; a worker ticks; the system names asked once (6 requests);
  * history: a line older than 15 minutes dropped, a recent one shown with no alert;
  * the stargate table: the page's jumps for 17 systems equal a breadth-first search over the table decoded here (and the
    client's jumps.static when EVE_RES is set), 1DQ1-A to Jita 42;
  * reports: linked names with '*', two pilots in a run, +3, ships with x2, Standings colours (hostile, neutral, friendly),
    nv keeps who was seen, clr, status? (no row), "QX-L" read as the nearest QX- system (QX-LIJ, not QX-LOO), the
    "Pilot (Ship) jumped A from B" shape, a Chinese ship name, "New Caldari" and "Jita" but not "jita", words left plain;
  * Near You: nearest first, a red row and an alert (sound + notification) for hostile/neutral within 3 jumps only, once per
    system; friendly-only hidden; the header's "N near";
  * your system follows a jump in Local (jumps redrawn); a relog's new file is read; settings kept;
  * off (the Intel slider): no more reading; INTEL-01 (no API), INTEL-03 (names fail), INTEL-04 (no logs), the build warning;
  * 390 px: nothing off the page; no page errors.
v2026.10.14.95 fails (no Intel tab).
"""
import sys, os, re, json, time, base64, struct, collections, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from playwright.sync_api import sync_playwright
import sa_mocks as M

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok

# ---- the page's stargate table, decoded here independently of the page ----
src = open(HTML, encoding='utf-8').read()
mj = re.search(r'^const INTEL_JUMPS = (.*);$', src, re.M)
if not mj: print('FAIL no INTEL_JUMPS in the page'); print('FAILURES: 1'); sys.exit(1)
J = json.loads(mj.group(1))
def u16(b64): b = base64.b64decode(b64); return struct.unpack('<%dH' % (len(b) // 2), b)
ids, prev = [], 30000000
for d in u16(J['sys']): prev += d; ids.append(prev)
E = u16(J['edges']); G = collections.defaultdict(set)
for i in range(0, len(E), 2): G[ids[E[i]]].add(ids[E[i + 1]]); G[ids[E[i + 1]]].add(ids[E[i]])
check(len(ids) == J['systems'] and len(E) // 2 == J['n'], f"the table: {J['n']} connections, {J['systems']} systems")
RES = os.environ.get('EVE_RES')
if RES:
    idx = open(os.path.join(RES, 'tq', 'resfileindex.txt'), encoding='utf-8', errors='replace').read()
    _, rel, md5, *_ = next(l for l in idx.splitlines() if l.startswith('res:/staticdata/jumps.static,')).split(',')
    b = open(os.path.join(RES, 'ResFiles', *rel.split('/')), 'rb').read()
    n = struct.unpack_from('<I', b, 0)[0]
    C = {tuple(sorted(struct.unpack_from('<4I', b, 4 + i * 65)[2:4])) for i in range(n)}
    P = {tuple(sorted((ids[E[i]], ids[E[i + 1]]))) for i in range(0, len(E), 2)}
    check(C == P and md5 == J['md5'], f'the table is the client\'s jumps.static ({len(C)} connections, md5 {md5[:8]}…)')
def bfs(s):
    d = {s: 0}; q = [s]
    for x in q:
        for y in G[x]:
            if y not in d: d[y] = d[x] + 1; q.append(y)
    return d

REAL = {30004025: "8-YNBE", 30004028: "E-VKJV", 30004714: "QX-LIJ", 30004716: "4K-TRB", 30004730: "D-W7F0", 30004731: "JP4-AA", 30004732: "FM-JK5",
        30004734: "23G-XC", 30004735: "T5ZI-S", 30004736: "4X0-8B", 30004759: "1DQ1-A", 30004760: "8WA-Z6", 30004761: "5BTK-M", 30004762: "N-8YET",
        30004763: "Y-OMTZ", 30004764: "3-DMQT", 30004765: "MO-GZ5", 30000142: 'Jita', 30000145: 'New Caldari', 30000001: 'QX-LOO'}
SYSNAME = {i: REAL.get(i, f'N{i}') for i in ids}
SYSID = {v: k for k, v in SYSNAME.items()}
D0 = bfs(SYSID['1DQ1-A'])
ONE_WORD = {'Marrek': 96000001, 'Ketter': 96000002}
NAMES_CALLS, STATUS = [], {'v': str(J['build']), 'names_fail': False}
def esi(route):
    url, body = route.request.url, route.request.post_data or ''
    if '/universe/names/' in url:
        q = json.loads(body)
        if q and all(isinstance(i, int) and 30000000 <= i < 31000000 for i in q):
            NAMES_CALLS.append(len(q))
            if STATUS['names_fail']: return route.fulfill(status=503, content_type='application/json', body='{"error":"down"}')
            return route.fulfill(status=200, content_type='application/json', body=json.dumps([{'id': i, 'name': SYSNAME[i], 'category': 'solar_system'} for i in q]))
    if '/universe/ids/' in url:   # two made-up one-word pilots, "Marrek" and "Ketter": "Marrek Ketter" must still read as one pilot
        q = [n.lower() for n in json.loads(body)]
        one = [{'id': i, 'name': n} for n, i in ONE_WORD.items() if n.lower() in q]
        if one:
            rest = [n for n in json.loads(body) if n.lower() not in {k.lower() for k in ONE_WORD}]
            out = {'characters': one}
            for n in rest:
                k = n.lower()
                if k in M.NAME_ID: out['characters'].append({'id': M.NAME_ID[k], 'name': M.PILOTS[M.NAME_ID[k]][0]})
            return route.fulfill(status=200, content_type='application/json', body=json.dumps(out))
    if '/characters/affiliation/' in url:
        q = json.loads(body)
        if any(i in ONE_WORD.values() for i in q):
            return route.fulfill(status=200, content_type='application/json', body=json.dumps([{'character_id': i, 'corporation_id': 98000013} if i in ONE_WORD.values() else M.aff(i) for i in q]))
    if re.search(r'/status/\?', url):
        return route.fulfill(status=200, content_type='application/json', body=json.dumps({'players': 1, 'server_version': STATUS['v'], 'start_time': '2026-10-27T11:00:00Z'}))
    return M.esi(route)
def route(ctx):
    ctx.route(re.compile(r'https://esi\.evetech\.net/.*'), esi)
    ctx.route(re.compile(r'https://zkillboard\.com/.*'), M.zkb)
    ctx.route(re.compile(r'https://(images\.evetech\.net|fonts\.).*'), lambda r: r.fulfill(status=404, body=''))

# ---- a made-up Chatlogs folder, written as EVE writes it ----
FS = r"""(() => {
  const files = {}; window.__fs = {files, perm: 'granted', beeps: 0, notes: []};
  const enc = (t) => { const a = new Uint8Array(t.length * 2); for(let i = 0; i < t.length; i++){ const c = t.charCodeAt(i); a[2 * i] = c & 255; a[2 * i + 1] = c >> 8; } return a; };
  __fs.write = (name, text) => { const old = files[name] ? files[name].bytes : new Uint8Array(0), add = enc(text), b = new Uint8Array(old.length + add.length); b.set(old); b.set(add, old.length); files[name] = {bytes: b, mtime: Date.now()}; };
  class FH { constructor(n){ this.kind = 'file'; this.name = n; } async getFile(){ const f = files[this.name]; if(!f) throw new DOMException('gone', 'NotFoundError'); return new File([f.bytes], this.name, {lastModified: f.mtime}); } }
  const dir = {kind: 'directory', name: 'Chatlogs', async *entries(){ for(const n of Object.keys(files)) yield [n, new FH(n)]; },
    async queryPermission(){ return __fs.perm; }, async requestPermission(){ return __fs.perm; }};
  window.showDirectoryPicker = window.__noFsApi ? undefined : async () => dir;   // Chromium has its own: replaced (or taken away)
  window.Notification = class { constructor(t, o){ __fs.notes.push([t, o && o.body]); } static get permission(){ return 'granted'; } static requestPermission(){ return Promise.resolve('granted'); } };
  window.AudioContext = class { constructor(){ this.currentTime = 0; this.destination = {}; }
    createOscillator(){ return {frequency: {}, connect: (g) => g, start(){ }, stop(){ }, set type(v){ }}; }
    createGain(){ const g = {gain: {setValueAtTime(){ }, exponentialRampToValueAtTime(){ }}, connect: () => g}; __fs.beeps += 0.5; return g; } };
})();"""
def eve(t): return time.strftime('%Y.%m.%d %H:%M:%S', time.gmtime(t))
def fname(chan, t, cid): return f"{chan}_{time.strftime('%Y%m%d_%H%M%S', time.gmtime(t))}_{cid}.txt"
def header(chan, listener, t):
    lines = ['', '', '        ---------------------------------------------------------------', '',
             f'          Channel ID:      -{abs(hash(chan)) % 99999999}', f'          Channel Name:    {chan}', f'          Listener:        {listener}',
             f"          Session started: {eve(t)}", '        ---------------------------------------------------------------', '', '']
    return ''.join('﻿' + l + '\r\n' for l in lines)
def line(t, who, msg): return f'﻿[ {eve(t)} ] {who} > {msg}\r\n'

MAIN, ALT = 95000001, 95000002   # made-up character IDs ("Your Main", "Your Alt")
NOW = time.time()
F_LOCAL_MAIN = fname('Local', NOW - 7200, MAIN); F_LOCAL_ALT = fname('Local', NOW - 5000, ALT)
F_INTEL = fname('region.intel', NOW - 7000, MAIN); F_OTHER = fname('other.intel', NOW - 6000, MAIN); F_CORP = fname('Corp', NOW - 3 * 86400, MAIN)
FRIEND = M.PILOTS[M.pick(M.CORP, 1)][0]
def W(pg, name, text): pg.evaluate("([n, t]) => __fs.write(n, t)", [name, text])
def setup_logs(pg):
    W(pg, F_LOCAL_MAIN, header('Local', 'Your Main', NOW - 7200) + line(NOW - 7190, 'EVE System', 'Channel changed to Local : 8WA-Z6*') + line(NOW - 4000, 'EVE System', 'Channel changed to Local : 1DQ1-A*'))
    W(pg, F_LOCAL_ALT, header('Local', 'Your Alt', NOW - 5000) + line(NOW - 4990, 'EVE System', 'Channel changed to Local : 8WA-Z6*'))
    W(pg, F_INTEL, header('region.intel', 'Your Main', NOW - 7000) + line(NOW - 6990, 'EVE System', 'Channel MOTD: welcome to region.intel, report with system first')
      + line(NOW - 2400, 'Gate Watcher', 'E-VKJV Seren Ketter sabre') + line(NOW - 300, 'Kai Rhenn', 'T5ZI-S* Kirra Longtail* loki'))
    W(pg, F_OTHER, header('other.intel', 'Your Main', NOW - 6000) + line(NOW - 5000, 'Someone', 'MO-GZ5 clr'))
    W(pg, F_CORP, header('Corp', 'Your Main', NOW - 3 * 86400) + line(NOW - 3 * 86400 + 60, 'Someone', 'hi'))
SIDE = {'pilot': {'id': 90000001, 'name': 'Test Pilot'}, 'corp': {'id': M.CORP, 'name': 'Example Corp'}, 'alliance': {'id': M.ALLIANCE, 'name': 'Example Alliance'},
        'friendly': [], 'hostile': [{'id': M.CRTS, 'name': 'Crimson Tide Syndicate', 'kind': 'alliance'}], 'rows': 15}
NEAR = """() => [...document.querySelectorAll('#intelPanel .it-nb')].map(r => [r.querySelector('.sys').textContent, r.querySelector('.j').textContent, r.querySelector('.st b').textContent, r.querySelector('.who').textContent, r.classList.contains('alert')])"""
FEED = """() => [...document.querySelectorAll('#intelPanel .it-fd')].map(r => ({chips: [...r.querySelectorAll('.it-chip')].map(c => [c.className.replace('it-chip ', '').replace(/^p /, ''), c.textContent]), left: (r.querySelector('.it-left') || {}).textContent || '', raw: r.querySelector('.raw').textContent}))"""
def tick(pg, ms=2600): pg.wait_for_timeout(ms)

with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []
    def new_ctx(w, init=''):
        ctx = b.new_context(viewport={'width': w, 'height': 1000}); ctx.on('page', lambda pg: pg.on('pageerror', lambda e: errs.append(str(e))))
        if init: ctx.add_init_script(init)
        ctx.add_init_script(FS); route(ctx); return ctx
    ctx = new_ctx(1440)
    pg = ctx.new_page(); pg.goto('file://' + HTML)
    pg.evaluate("(s) => { localStorage.setItem('dscanSide', JSON.stringify(s)); localStorage.removeItem('dscanIntel'); }", SIDE); pg.reload(); pg.wait_for_timeout(400)
    tabs = pg.evaluate("() => [...document.querySelectorAll('.tabs .tab-btn')].filter(b => b.checkVisibility()).map(b => b.textContent)")
    check(tabs == ['Pilot Analyzer', 'Fit Analyzer', 'System Analyzer', 'Intel'], f'the Intel tab after the System Analyzer {tabs}')
    hdr = pg.evaluate("() => { const l = document.querySelector('#intelHdrLabel'); return [l.nextElementSibling.id, l.nextElementSibling.nextElementSibling.id, l.querySelector('input.mys-sw').checked, document.querySelector('#intelNear').hidden, !!l.querySelector('#intelNear'), l.textContent.trim()]; }")
    check(hdr == ['intelNear', 'sideChip', False, True, False, 'Intel'], f'the Intel slider beside Standings, off; its pill outside the slider\'s label, hidden {hdr}')
    pg.click('#tabBtnIntel'); pg.wait_for_timeout(200)
    box = pg.evaluate("() => [...document.querySelectorAll('#intelPanel .it-setup .it-box .k')].map(k => k.textContent)")
    check(box == ['1 · Chat logs folder', '2 · Intel channels', '3 · You', '4 · Alerts'], f'the card: four setup boxes {box}')
    sws = pg.evaluate("() => [document.querySelectorAll('input.mys-sw[aria-label=\"Watch the intel channels\"]').length, document.querySelectorAll('#intelPanel input.mys-sw').length, (document.querySelector('#intelPanel .it-sub') || {}).textContent || '']")
    check(sws[0] == 1 and sws[1] == 0 and 'The Intel slider at the top, beside Standings, starts and stops it from any tab' in sws[2], f'one on/off switch: the Intel slider at the top, none on the card, and the card says so {sws[:2]}')
    setup_logs(pg)
    pg.click('[data-it-act="folder"]'); pg.wait_for_timeout(500)
    chans = pg.evaluate("() => [...document.querySelectorAll('[data-it-chan]')].map(c => [c.dataset.itChan, c.checked])")
    check(chans == [['other.intel', False], ['region.intel', False]], f'the channels of the last 2 days, the old Corp log left out, none guessed with two intel channels {chans}')
    me = pg.evaluate("() => [...document.querySelectorAll('[data-it-me]')].map(c => [c.closest('label').textContent.trim(), c.checked])")
    check(me == [['Your Alt 8WA-Z6', False], ['Your Main 1DQ1-A', False]], f'both characters with their systems from Local {me}')
    pg.check('[data-it-chan="region.intel"]'); pg.wait_for_timeout(100); pg.check(f'[data-it-me="{MAIN}"]'); pg.wait_for_timeout(100)
    st = pg.evaluate("() => JSON.parse(localStorage.getItem('dscanIntel'))")
    check(st['channels'] == ['region.intel'] and st['me'] == MAIN and st['range'] == 3 and st['notify'] and st['sound'], f'settings kept {st}')
    # ---- on, from the header slider ----
    pg.click('#intelHdrLabel'); tick(pg)
    on = pg.evaluate("() => [document.querySelector('#intelHdrSw').checked, document.querySelectorAll('#intelPanel input.mys-sw').length, it.ticker && it.ticker.kind]")
    check(on == [True, 0, 'worker'], f'the Intel slider turns it on (still no slider on the card), a worker ticks {on}')
    check(NAMES_CALLS == [1000] * (len(ids) // 1000) + [len(ids) % 1000], f'the system names asked once: {len(NAMES_CALLS)} requests {NAMES_CALLS}')
    status = pg.inner_text('#intelPanel [data-it-status]')
    check(status.startswith('Your Main in 1DQ1-A · region.intel · last line '), f'the status line ({status!r})')
    jumps = pg.evaluate("(names) => Object.fromEntries(names.map(n => [n, itJumps(it.names.byLower.get('1dq1-a'), it.names.byLower.get(n.toLowerCase()))]))", list(REAL.values()))
    want = {v: D0.get(k) for k, v in REAL.items()}
    check(jumps == want, f"the page's jumps from 1DQ1-A = a search over the table decoded here (Jita {jumps.get('Jita')}) {jumps}")
    near = pg.evaluate(NEAR)
    feed0 = [f['raw'] for f in pg.evaluate(FEED)]
    check(near == [['T5ZI-S', '1j', '1 neutral', 'Kirra Longtail · Loki', True]] and feed0 == ['Kai Rhenn > T5ZI-S* Kirra Longtail* loki'],
          f'history: the 40-minute-old line dropped (Near You and Feed), the 5-minute-old one shown {near} {feed0}')
    check(pg.evaluate("() => [__fs.beeps, __fs.notes.length]") == [0, 0], 'no alert for lines already in the log')
    # ---- new reports ----
    T = time.time()
    W(pg, F_INTEL, line(T, 'Scout Alt', '8WA-Z6*  Marrek Ketter*  Vesna Dossier +3  sabre vedmak x2 loki')
      + line(T + 1, 'Gate Watcher', 'Y-OMTZ Seren Ketter nv')
      + line(T + 2, 'Kai Rhenn', 'status N-8YET?')
      + line(T + 3, 'Scout Alt', '1DQ1-A clr')
      + line(T + 4, 'Gate Watcher', 'Anouk Morrow (Scimitar) jumped QX-L from 4K-TRB')
      + line(T + 5, 'Someone', 'D-W7F0 秃鹫级 x2')
      + line(T + 6, 'Someone', f'MO-GZ5 {FRIEND}')
      + line(T + 7, 'Someone', 'New Caldari Jita jita blorp zzt'))
    tick(pg, 3200)
    F = pg.evaluate(FEED)
    got = {f['raw']: f for f in F}
    def chips(raw): return got[raw]['chips'] if raw in got else None
    c = chips('Scout Alt > 8WA-Z6*  Marrek Ketter*  Vesna Dossier +3  sabre vedmak x2 loki')
    check(c == [['sys', '8WA-Z6 1j'], ['h', 'Marrek Ketter'], ['n', 'Vesna Dossier'], ['kw', '+3'], ['ship', 'Sabre'], ['ship', 'Vedmak ×2'], ['ship', 'Loki']],
          f'linked names, two pilots (Marrek Ketter one pilot though "Marrek" and "Ketter" are pilots too), +3, ships with x2, Standings colours {c}')
    c = chips('Gate Watcher > Y-OMTZ Seren Ketter nv'); check(c == [['sys', 'Y-OMTZ 3j'], ['h', 'Seren Ketter'], ['kw', 'no visual']], f'nv {c}')
    c = chips('Kai Rhenn > status N-8YET?'); check(c == [['sys', 'N-8YET 1j'], ['kw', 'status?']], f'status? {c}')
    c = chips('Gate Watcher > Anouk Morrow (Scimitar) jumped QX-L from 4K-TRB')
    check(c == [['sys', 'QX-LIJ 4j'], ['sys', '4K-TRB 3j'], ['n', 'Anouk Morrow'], ['ship', 'Scimitar'], ['kw', 'jumped']], f'"QX-L": the nearest QX- system; "Pilot (Ship) jumped A from B" {c}')
    c = chips('Someone > D-W7F0 秃鹫级 x2'); check(c == [['sys', 'D-W7F0 2j'], ['ship', 'Condor ×2']], f'a Chinese ship name {c}')
    c = chips(f'Someone > MO-GZ5 {FRIEND}'); check(c is None, f'a friendly-only line hidden (hide friendlies on) {c}')
    r = got.get('Someone > New Caldari Jita jita blorp zzt')
    check(r and r['chips'] == [['sys', f'New Caldari {D0[30000145]}j'], ['sys', f'Jita {D0[30000142]}j']] and r['left'] == 'jita blorp zzt',
          f'"New Caldari" and "Jita" but not "jita"; words left plain {r}')
    near = pg.evaluate(NEAR)
    wn = [['1DQ1-A', '0j', 'clear', 'reported clear by Scout Alt', False],
          ['8WA-Z6', '1j', '5 hostile', 'Marrek Ketter, Vesna Dossier +3 · Sabre, Vedmak ×2, Loki', True],
          ['T5ZI-S', '1j', '1 neutral', 'Kirra Longtail · Loki', True],
          ['D-W7F0', '2j', '2 hostile', 'Condor ×2', True],
          ['Y-OMTZ', '3j', 'no visual', 'Seren Ketter', True],
          ['QX-LIJ', '4j', '1 neutral', 'Anouk Morrow · Scimitar', False]]
    check(near == wn, f'Near You: nearest first, red within 3 jumps, nv keeps who was seen, clr, friendly-only hidden, status no row {near}')
    al = pg.evaluate("() => [__fs.beeps, __fs.notes.map(n => n[0])]")
    check(al == [3, ['8WA-Z6 · 1 jump', 'Y-OMTZ · 3 jumps', 'D-W7F0 · 2 jumps']], f'alerts: sound and notification for hostile/neutral within 3 jumps, not 4, not friendlies {al}')
    badge = pg.evaluate("() => [document.querySelector('#intelNear').hidden, document.querySelector('#intelNear').textContent]")
    check(badge == [False, '4 near'], f'the header: "4 near" {badge}')
    pg.click('#tabBtnPilot'); pg.click('#intelNear'); pg.wait_for_timeout(300)   # v.97: the pill opens Intel and doesn't switch it off
    pill = pg.evaluate("() => [it.on, document.querySelector('#intelHdrSw').checked, getComputedStyle(document.querySelector('#tabIntel')).display, document.querySelector('#intelNear').title]")
    check(pill[:3] == [True, True, 'block'] and pill[3] == '4 systems with a hostile or neutral report within 3 jumps: open Intel',
          f'pressing "4 near" opens the Intel tab and leaves Intel on (v.96: it turned Intel off) {pill}')
    W(pg, F_INTEL, line(time.time(), 'Scout Alt', '8WA-Z6 Marrek Ketter still'))
    tick(pg)
    check(pg.evaluate("() => __fs.beeps") == 3, 'one alert per system per 30 s')
    # ---- you jump; a relog ----
    W(pg, F_LOCAL_MAIN, line(time.time(), 'EVE System', 'Channel changed to Local : T5ZI-S*'))
    tick(pg)
    status = pg.inner_text('#intelPanel [data-it-status]')
    near = pg.evaluate(NEAR)
    D1 = bfs(SYSID['T5ZI-S'])
    jj = [r[:2] for r in near]
    check(status.startswith('Your Main in T5ZI-S') and jj[0] == ['T5ZI-S', '0j'] and all(j == f"{D1[SYSID[s]]}j" for s, j in jj)
          and [int(j[:-1]) for s, j in jj] == sorted(int(j[:-1]) for s, j in jj), f'your system follows your jump in Local; jumps redrawn ({status!r}, {jj})')
    F2 = fname('region.intel', time.time(), MAIN)
    W(pg, F2, header('region.intel', 'Your Main', time.time()) + line(time.time(), 'Scout Alt', '4X0-8B Rando Thirdparty'))
    pg.evaluate("() => { it.lastScan = 0; }"); tick(pg)
    F = pg.evaluate(FEED)
    check(F[0]['raw'] == 'Scout Alt > 4X0-8B Rando Thirdparty' and pg.evaluate("() => [...it.files.values()].map(f => f.name)") == [F2], 'a relog: the new file found and read')
    # ---- the gear ----
    pg.click('[data-it-act="gear"]'); pg.wait_for_timeout(200)
    pop = pg.evaluate("() => { const p = document.querySelector('.it-pop'); return p && [...p.querySelectorAll('.it-box .k')].map(k => k.textContent); }")
    check(pop == ['Chat logs folder', 'Intel channels', 'You', 'Alerts'], f'the gear opens the settings while watching {pop}')
    opt = pg.evaluate("""() => [...document.querySelectorAll('.it-pop select option')].map(o => { const c = getComputedStyle(o); return [c.backgroundColor, c.color]; })""")
    lum = lambda c: (lambda v: 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2])([int(x) for x in re.findall(r'\d+', c)[:3]])
    check(opt and all(re.match(r'rgb\(', bg) and lum(bg) < 60 and lum(fg) > 180 for bg, fg in opt),
          f'the open lists of the settings: light text on a dark background (v.96: light on white on Windows) {sorted(set(map(tuple, opt)))}')
    pg.select_option('.it-pop [data-it-set="range"]', '5'); pg.wait_for_timeout(100)
    check(pg.evaluate("() => JSON.parse(localStorage.getItem('dscanIntel')).range") == 5, 'alert range kept')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    check(pg.evaluate("() => !document.querySelector('.it-pop')"), 'Escape closes the settings')
    # ---- off ----
    pg.click('#tabBtnPilot'); pg.click('#intelHdrLabel'); pg.wait_for_timeout(300)   # off from another tab
    off = pg.evaluate("() => [document.querySelector('#intelHdrSw').checked, it.on, it.ticker, document.querySelector('#intelNear').hidden]")
    pg.click('#tabBtnIntel'); pg.wait_for_timeout(200)
    stopped = pg.inner_text('#intelPanel .it-sub')
    check(off == [False, False, None, True] and stopped == 'Stopped. The Intel slider at the top starts it again.', f'the Intel slider turns it off from another tab {off} ({stopped!r})')
    n0 = len(pg.evaluate(FEED))
    W(pg, F2, line(time.time(), 'Scout Alt', '4X0-8B Marrek Ketter')); tick(pg)
    check(len(pg.evaluate(FEED)) == n0, 'off: no more reading')
    NAMES_CALLS.clear(); pg.click('#intelHdrLabel'); tick(pg)
    check(NAMES_CALLS == [] and pg.evaluate("() => it.on"), 'on again: the system names not asked again')
    pg.click('#intelHdrLabel'); pg.wait_for_timeout(200)
    # ---- the build warning ----
    STATUS['v'] = str(J['build'] + 1); pg.reload(); pg.wait_for_timeout(300); pg.click('#tabBtnIntel')
    setup_logs(pg); pg.click('[data-it-act="folder"]'); pg.wait_for_timeout(300)   # the made-up folder can't be kept in IndexedDB: chosen again
    pg.click('#intelHdrLabel'); tick(pg)
    warn = pg.evaluate("() => [...document.querySelectorAll('#intelPanel .it-warn')].map(e => e.textContent)")
    check(any(w.startswith(f"EVE is on build {J['build'] + 1}; the jump table was checked on {J['build']}") for w in warn), f'EVE patched since the table was checked: said {warn}')
    STATUS['v'] = str(J['build'])
    shot_w = pg.evaluate("() => document.documentElement.scrollWidth")
    pg.screenshot(path='/tmp/intel_1440.png', full_page=True)
    ctx.close()
    # ---- errors ----
    ctx = new_ctx(1440, 'window.__noFsApi = true;'); pg = ctx.new_page(); pg.goto('file://' + HTML); pg.wait_for_timeout(300)
    pg.click('#tabBtnIntel'); pg.click('#intelHdrLabel'); pg.wait_for_timeout(300)
    e = pg.inner_text('#intelPanel .pr-msg.err')
    check(e.endswith('(INTEL-01)') and not pg.evaluate("() => document.querySelector('#intelHdrSw').checked"), f'no File System Access API: INTEL-01, the slider back off ({e!r})')
    ctx.close()
    ctx = new_ctx(1440); pg = ctx.new_page(); pg.goto('file://' + HTML); pg.wait_for_timeout(300); pg.click('#tabBtnIntel')
    W(pg, 'notes.txt', 'x'); pg.click('[data-it-act="folder"]'); pg.wait_for_timeout(300)
    e = pg.inner_text('#intelPanel .pr-msg.err'); check(e.endswith('(INTEL-04)'), f'a folder with no chat logs: INTEL-04 ({e!r})')
    ctx.close()
    STATUS['names_fail'] = True
    ctx = new_ctx(390); pg = ctx.new_page(); pg.goto('file://' + HTML); pg.wait_for_timeout(300)
    pg.evaluate("(s) => localStorage.setItem('dscanSide', JSON.stringify(s))", SIDE); pg.reload(); pg.wait_for_timeout(300)
    setup_logs(pg); pg.click('#tabBtnIntel'); pg.click('[data-it-act="folder"]'); pg.wait_for_timeout(300)
    pg.check('[data-it-chan="region.intel"]'); pg.check(f'[data-it-me="{MAIN}"]'); pg.click('#intelHdrLabel'); tick(pg)
    e = pg.inner_text('#intelPanel .pr-msg.err')
    check(e.endswith('(INTEL-03)') and not pg.evaluate("() => it.on"), f'the system names fail: INTEL-03, off ({e!r})')
    STATUS['names_fail'] = False
    pg.click('#intelHdrLabel'); tick(pg)
    W(pg, F_INTEL, line(time.time(), 'Scout Alt', '8WA-Z6 Marrek Ketter sabre')); tick(pg)
    over = pg.evaluate("() => [document.documentElement.scrollWidth, [...document.querySelectorAll('#intelPanel *, .tabs *')].filter(e => { const r = e.getBoundingClientRect(); return r.width && (r.right > innerWidth + 1 || r.left < -1); }).map(e => e.className || e.tagName).slice(0, 5)]")
    check(over[0] <= 390 and not over[1], f'390 px: nothing off the page {over}')
    pill = pg.evaluate("() => { const r = document.querySelector('#intelNearN').getBoundingClientRect(), b = document.querySelector('#intelNear').getBoundingClientRect(); return [document.querySelector('#intelNearN').textContent, Math.round(r.height), Math.round(b.height)]; }")
    check(pill[0].endswith(' near') and pill[1] <= 20 and pill[2] >= 44, f'390 px: the pill on one line, its button 44 px tall {pill}')
    gear = pg.evaluate("() => { const r = document.querySelector('[data-it-act=gear]').getBoundingClientRect(); return [r.width, r.height]; }")
    check(gear[0] >= 44 and gear[1] >= 44, f'390 px: the gear 44 px {gear}')
    pg.screenshot(path='/tmp/intel_390.png', full_page=True)
    ctx.close()
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
