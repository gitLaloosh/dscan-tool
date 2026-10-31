"""Intel, delivery 1 (v2026.10.14.96; roadmap/intel-plan.md).

    PYFA_SRC=/path/to/pyfa [EVE_RES=/path] python3 -I tools/page_checks/intel_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner: "the tool actively polls the game's chat log for the intel channel and tracks neutral and hostile ships that are
reported via that channel"; "it needs to have an on/off mechanism"; mockup answers: the feed in a card on its own tab, a gear
for settings, "a slider for off/on similar just like 'use in assessments'", jumps from a built-in table that doesn't drift
from EVE. The real page with a made-up Chatlogs folder (the File System Access API replaced by an in-page folder of
UTF-16 LE files written the way EVE writes them: BOM on every line, CRLF, EVE time), ESI from sa_mocks.py, and the system
names: the real names of the 17 systems within 4 jumps of 1DQ1-A, Jita and New Caldari, a made-up "QX-LOO" far away, and
"N<id>" for the rest. Every pilot and character name is made up. Checks:
  * the Intel tab after the System Analyzer; the one on/off switch on the Intel card beside the gear, off (v.97 to v.104: in
    the header; v2026.10.29.1: back on the card, the header keeps the "N near" pill); the card's four setup boxes;
  * Choose folder: the channels of the last 2 days (a 3-day-old Corp log left out), both characters with their systems;
  * the switch on the card turns it on; a worker ticks; the system names asked once (6 requests);
  * history: a line older than 15 minutes dropped, a recent one shown with no alert;
  * the stargate table: the page's jumps for 17 systems equal a breadth-first search over the table decoded here (and the
    client's jumps.static when EVE_RES is set), 1DQ1-A to Jita 42;
  * reports: linked names with '*', two pilots in a run, +3, ships with x2, Standings colours (hostile, neutral, friendly),
    nv keeps who was seen, clr, status? (no row), "QX-L" read as the nearest QX- system (QX-LIJ, not QX-LOO), the
    "Pilot (Ship) jumped A from B" shape, a Chinese ship name, "New Caldari" and "Jita" but not "jita", words left plain;
  * v2026.10.14.102 (the owner: no "report" without a valid system name): "78 status?", a bare "clr" and "<pilot> loc?"
    make no Feed row and change nothing in Near You, their words are never looked up, and they still count as the last
    line; every report row in the Feed names a system;
  * v2026.10.14.104 (the owner's report: "1red" and "Recently" shown as pilots, both real character names): "1red" and
    "2 neuts" are head counts (chips "1 red", "2 neut"; Near You "1 hostile", "2 neutral"), "A (recently seen as sabre) B (loki)"
    pairs each pilot with the ship in their brackets, and none of those words is looked up as a pilot;
  * Near You: nearest first, a red row and an alert (sound + notification) for hostile/neutral within 3 jumps only, once per
    system; friendly-only hidden; the header's "N near";
  * your system follows a jump in Local (jumps redrawn); a relog's new file is read; settings kept;
  * off (the switch on the card): no more reading; INTEL-01 (no API), INTEL-03 (names fail), INTEL-04 (no logs), no build warning (v2026.10.29.5);
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
ONE_WORD = {'Marrek': 96000001, 'Ketter': 96000002, 'Inside': 96000003, 'ESS': 96000004, '1red': 96000005, 'Recently': 96000006, 'As': 96000007}   # v.104: so are "1red" and "Recently"   # v.99: real characters have such names; a place word must never reach them
NAMES_CALLS, STATUS = [], {'v': str(J['build']), 'names_fail': False}
IDS_ASKED = set()   # v.102: every name sent to /universe/ids/
def esi(route):
    url, body = route.request.url, route.request.post_data or ''
    if '/universe/names/' in url:
        q = json.loads(body)
        if q and all(isinstance(i, int) and 30000000 <= i < 31000000 for i in q):
            NAMES_CALLS.append(len(q))
            if STATUS['names_fail']: return route.fulfill(status=503, content_type='application/json', body='{"error":"down"}')
            return route.fulfill(status=200, content_type='application/json', body=json.dumps([{'id': i, 'name': SYSNAME[i], 'category': 'solar_system'} for i in q]))
    if '/universe/ids/' in url: IDS_ASKED.update(n.lower() for n in json.loads(body))
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
        STATUS['asked'] = STATUS.get('asked', 0) + 1
        return route.fulfill(status=200, content_type='application/json', body=json.dumps({'players': 1, 'server_version': STATUS['v'], 'start_time': '2026-10-27T11:00:00Z'}))
    return M.esi(route)
def route(ctx):
    ctx.route(re.compile(r'https://esi\.evetech\.net/.*'), esi)
    ctx.route(re.compile(r'https://zkillboard\.com/.*'), M.zkb)
    ctx.route(re.compile(r'https://(images\.evetech\.net|fonts\.).*'), lambda r: r.fulfill(status=404, body=''))
    # v.99: zKillboard's live feed (R2Z2), quiet here: a sequence, then nothing new (intel_kills_check.py feeds it kills).
    # v.100: as the real one answers: sequence.json readable; a missing kill a 404 without the CORS header, which the page
    # sees as a network error (aborted here: Playwright's route.fulfill() skips the CORS check; LESSON #89)
    ctx.route(re.compile(r'https://r2z2\.zkillboard\.com/.*'), lambda r: r.fulfill(status=200, content_type='application/json', headers={'access-control-allow-origin': '*'}, body='{"sequence": 1000}')
              if r.request.url.endswith('/sequence.json') else r.abort('failed'))

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
# v.100: jumps read back as "Nj" here ("3 Jumps", "1 Jump", "In system" on the page; the exact words are checked on their own);
# the line as typed is "who > line" (v.100: who, the line and the channel in the strip that opens under a row)
JN = "const jn = (t) => t.replace(/ ?(\\d+) Jumps?$/, (m, n) => (m.startsWith(' ') ? ' ' : '') + n + 'j').replace(/ ?In system$/, (m) => (m.startsWith(' ') ? ' ' : '') + '0j');"
NEAR = """() => { """ + JN + """ return [...document.querySelectorAll('#intelPanel .it-nb')].map(r => [r.querySelector('.sys').textContent, jn(r.querySelector('.j').textContent), r.querySelector('.st b').textContent, r.querySelector('.who').textContent, r.classList.contains('alert')]); }"""
FEED = """() => { """ + JN + """ return [...document.querySelectorAll('#intelPanel .it-fd')].map(r => { const fj = ((r.querySelector('.fj') || {}).textContent || '').trim(); const cs = [...r.querySelectorAll('.it-chip')]; const s0 = cs.find(c => c.classList.contains('sys')); return ({chips: cs.map(c => [c.className.replace('it-chip ', '').replace(/^p /, ''), c.classList.contains('sys') ? jn(c.textContent.trim() + (c === s0 && fj ? ' ' + fj : '')) : (c.querySelector('.nm') || c).textContent]), left: (r.querySelector('.it-left') || {}).textContent || '', raw: ((r.querySelector('.it-raw .who') || {}).textContent || '') + ' > ' + r.querySelector('.raw').textContent}); }); }"""   # v2026.10.30.1: the first system's jump count is in its own column (.fj)
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
    check(tabs == ['Intel', 'System Analyzer', 'Pilot Analyzer', 'Fit Analyzer'], f'the tabs in the order of use, Intel first (v2026.10.30.1, the owner: "intel > system > pilot > fit") {tabs}')
    hdr = pg.evaluate("() => { const b = document.querySelector('#intelNear'); return [b.nextElementSibling.id, b.hidden, document.querySelectorAll('#myShipBar input[aria-label=\"Watch the intel channels\"]').length]; }")
    check(hdr == ['sideChip', True, 0], f'v2026.10.29.1: no Intel switch in the header, only the "N near" pill beside Standings, hidden {hdr}')
    pg.click('#tabBtnIntel'); pg.wait_for_timeout(200)
    box = pg.evaluate("() => [...document.querySelectorAll('#intelPanel .it-setup .it-box .k')].map(k => k.textContent)")
    check(box == ['1 · Chat logs folder', '2 · Intel channels', '3 · You', '4 · Range and alerts'], f'the card: four setup boxes {box}')
    sws = pg.evaluate("() => { const l = document.querySelector('#intelSwLabel'); return [document.querySelectorAll('input.mys-sw[aria-label=\"Watch the intel channels\"]').length, !!l && !!l.closest('#intelPanel .it-head'), l && l.nextElementSibling && l.nextElementSibling.dataset.itAct, l && l.querySelector('input').checked, l && l.textContent.trim(), (document.querySelector('#intelPanel .it-sub') || {}).textContent || '']; }")
    check(sws[:5] == [1, True, 'gear', False, 'Off'] and 'The switch beside the gear starts and stops it' in sws[5], f'v2026.10.29.1 (the owner: users "didn\'t see how to turn intel on while on the intel tab"): one on/off switch, on the Intel card beside the gear, off; the card says so {sws[:5]}')
    setup_logs(pg)
    pg.click('[data-it-act="folder"]'); pg.wait_for_timeout(500)
    chans = pg.evaluate("() => [...document.querySelectorAll('[data-it-chan]')].map(c => [c.dataset.itChan, c.checked])")
    check(chans == [['other.intel', False], ['region.intel', False]], f'the channels of the last 2 days, the old Corp log left out, none guessed with two intel channels {chans}')
    me = pg.evaluate("() => [...document.querySelectorAll('[data-it-me]')].map(c => [c.closest('label').textContent.trim(), c.checked])")
    check(me == [['Your Alt 8WA-Z6', False], ['Your Main 1DQ1-A', False]], f'both characters with their systems from Local {me}')
    pg.check('[data-it-chan="region.intel"]'); pg.wait_for_timeout(100); pg.check(f'[data-it-me="{MAIN}"]'); pg.wait_for_timeout(100)
    st = pg.evaluate("() => JSON.parse(localStorage.getItem('dscanIntel'))")
    check(st['channels'] == ['region.intel'] and st['me'] == MAIN and st['range'] == 3 and st['notify'] and st['sound'], f'settings kept {st}')
    # ---- on, from the card's switch ----
    pg.click('#intelSwLabel'); tick(pg)
    on = pg.evaluate("() => [document.querySelector('#intelSw').checked, document.querySelectorAll('input.mys-sw[aria-label=\"Watch the intel channels\"]').length, document.querySelector('#intelSwLabel').textContent.trim(), it.ticker && it.ticker.kind]")
    check(on == [True, 1, 'On', 'worker'], f'the switch on the card turns it on ("On"), still one switch, a worker ticks {on}')
    check(NAMES_CALLS == [1000] * (len(ids) // 1000) + [len(ids) % 1000], f'the system names asked once: {len(NAMES_CALLS)} requests {NAMES_CALLS}')
    status = pg.inner_text('#intelPanel [data-it-status]')
    check(status.startswith('Your Main in 1DQ1-A · 1 channel · last line '), f'the status line, the channel counted, not named (v2026.10.30.1) ({status!r})')
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
      + line(T + 7, 'Someone', 'New Caldari Jita jita blorp zzt')
      + line(T + 8, 'Kai Rhenn', '78 status?')            # v.102: no system the page can read (the owner's live report shape)
      + line(T + 9, 'Scout Alt', 'clr')
      + line(T + 10, 'Gate Watcher', 'Zorvan Quill loc?'))
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
    NOTE = "(raw) => { const r = [...document.querySelectorAll('#intelPanel .it-fd')].find(x => x.querySelector('.raw').textContent === raw); return r ? [...r.querySelectorAll('.it-snote')].map(n => n.textContent) : null; }"
    nt = pg.evaluate(NOTE, 'Anouk Morrow (Scimitar) jumped QX-L from 4K-TRB')
    # v2026.10.30.2: "from 4K-TRB" says where they came from, so the report is in QX-LIJ (4 jumps) though 4K-TRB (3) is nearer; 4K-TRB a note
    check(c == [['sys', 'QX-LIJ 4j'], ['n', 'Anouk Morrow'], ['ship', 'Scimitar'], ['kw', 'jumped']] and nt == ['from 4K-TRB'], f'"QX-L": the nearest QX- system; "Pilot (Ship) jumped A from B": in A, "from B" a note {c} {nt}')
    c = chips('Someone > D-W7F0 秃鹫级 x2'); check(c == [['sys', 'D-W7F0 2j'], ['ship', 'Condor ×2']], f'a Chinese ship name {c}')
    c = chips(f'Someone > MO-GZ5 {FRIEND}'); check(c is None, f'a friendly-only line hidden (hide friendlies on) {c}')
    r = got.get('Someone > New Caldari Jita jita blorp zzt')
    nt = pg.evaluate(NOTE, 'New Caldari Jita jita blorp zzt')   # v2026.10.30.2: two systems next to each other, the same distance away: the first, "on Jita gate?"
    check(r and r['chips'] == [['sys', f'New Caldari {D0[30000145]}j']] and nt == ['on Jita gate?'] and r['left'] == 'jita blorp zzt',
          f'"New Caldari" and "Jita" but not "jita" ("on Jita gate?": next door); words left plain {r} {nt}')
    nosys = ['Kai Rhenn > 78 status?', 'Scout Alt > clr', 'Gate Watcher > Zorvan Quill loc?']
    last = pg.evaluate("() => it.lastLine")
    check(not [r for r in nosys if r in got] and all(any(c[0] == 'sys' for c in f['chips']) for f in F if f['chips'] is not None)
          and not {'zorvan quill', 'zorvan', 'quill', 'loc'} & IDS_ASKED and abs(last / 1000 - (T + 10)) < 1.5,
          f'no system, no report: "78 status?", "clr", "Zorvan Quill loc?" make no Feed row and are not looked up; still the last line ({[r for r in nosys if r in got]}, {sorted({"zorvan quill", "zorvan", "quill", "loc"} & IDS_ASKED)})')
    near = pg.evaluate(NEAR)
    wn = [['1DQ1-A', '0j', 'clear', 'reported clear by Scout Alt', False],
          ['8WA-Z6', '1j', '5 hostile', 'Marrek Ketter, Vesna Dossier +3 · Sabre, Vedmak ×2, Loki', True],
          ['T5ZI-S', '1j', '1 neutral', 'Kirra Longtail · Loki', True],
          ['D-W7F0', '2j', '2 hostile', 'Condor ×2', True],
          ['Y-OMTZ', '3j', 'no visual', 'Seren Ketter', True],
          ['QX-LIJ', '4j', '1 neutral', 'Anouk Morrow · Scimitar', False]]
    check(near == wn, f'Near You: nearest first, red within 3 jumps, nv keeps who was seen, clr, friendly-only hidden, status no row {near}')
    # v.100 (the owner: "x Jumps", "a callout like 'IN SYSTEM'", the standing icons, the line as typed behind a toggle)
    jw = pg.evaluate("() => [[...document.querySelectorAll('#intelPanel .it-nb .j')].map(j => j.textContent), !!document.querySelector('#intelPanel .it-nb .j .it-here'), [...document.querySelectorAll('#itFeedList .it-fd')].map(r => r.querySelector('.it-chip.sys .it-sn').textContent + ' ' + r.querySelector('.fj').textContent).filter(t => /^(8WA-Z6|1DQ1-A|Y-OMTZ) /.test(t))]")
    jw.append(pg.evaluate("() => [document.querySelectorAll('#itFeedList .it-fd.clr').length, document.querySelectorAll('#itFeedList .it-fd.clr .it-chip.clr').length]"))
    check(jw[0] == ['In system', '1 Jump', '1 Jump', '2 Jumps', '3 Jumps', '4 Jumps'] and jw[1] and jw[2][:3] == ['1DQ1-A In system', 'Y-OMTZ 3 Jumps', '8WA-Z6 1 Jump'] and jw[3] == [1, 0],
          f'the words: "1 Jump", "3 Jumps", and "In system" (a tag) for your own system, in Near You and the Feed; "Clear" once on a clear row {jw}')
    ic = pg.evaluate("() => Object.fromEntries([...document.querySelectorAll('#itFeedList .it-chip.p')].map(c => [c.querySelector('.nm').textContent, [c.querySelector('svg.it-st').getAttribute('class'), c.querySelector('svg.it-st title').textContent]]))")
    check(ic.get('Marrek Ketter') == ['it-st bad sa-mark h', 'Hostile'] and ic.get('Vesna Dossier') == ['it-st neu sa-mark n', 'Neutral'] and not pg.evaluate("() => !!document.querySelector('#intelPanel .it-mk')"),
          f'standing icons: hostile "-", neutral "=" (v.99: an empty ring) {ic}')
    RAWQ = """(raw) => { const r = [...document.querySelectorAll('#itFeedList .it-fd')].find(f => (f.querySelector('.raw') || {}).textContent === raw); const t = r.querySelector('[data-it-raw]'), s = r.querySelector('.it-raw');
      return [t.getAttribute('aria-expanded'), s.hidden, s.checkVisibility(), (s.querySelector('.who') || {}).textContent, (s.querySelector('.ch') || {}).textContent, !!s.querySelector('[data-it-shape]'), r.classList.contains('open')]; }"""
    L8 = '8WA-Z6*  Marrek Ketter*  Vesna Dossier +3  sabre vedmak x2 loki'
    r0 = pg.evaluate(RAWQ, L8)
    shut = pg.evaluate("() => [...document.querySelectorAll('#itFeedList .it-fd:not(.kill)')].every(f => f.querySelector('[data-it-raw]') && f.querySelector('.it-raw').hidden)")
    pg.evaluate(f"(raw) => [...document.querySelectorAll('#itFeedList .it-fd')].find(f => f.querySelector('.raw').textContent === raw).querySelector('[data-it-raw]').click()", L8); pg.wait_for_timeout(150)
    r1 = pg.evaluate(RAWQ, L8)
    pg.evaluate("() => itRender(true)"); r2 = pg.evaluate(RAWQ, L8)
    pg.evaluate(f"(raw) => [...document.querySelectorAll('#itFeedList .it-fd')].find(f => f.querySelector('.raw').textContent === raw).querySelector('[data-it-raw]').click()", L8); pg.wait_for_timeout(150)
    r3 = pg.evaluate(RAWQ, L8)
    check(shut and r0[:3] == ['false', True, False] and r1 == ['true', False, True, 'Scout Alt', None, True, True] and r2 == r1 and r3[:3] == ['false', True, False],
          f'the line as typed: hidden behind a toggle on every report; opened it shows who sent it, the line and the copy button, no channel (v2026.10.30.1); stays open through a redraw; closes {r0} {r1} {r3}')
    # v2026.10.30.1 (the owner: "do not include the intel channel name in any of the output for now. security reasons. I am aware that
    # the channel names are in the settings"): with the gear closed, no channel name anywhere on the page, text or hover
    leak = pg.evaluate("() => { const h = document.documentElement; const txt = h.innerText; const attrs = [...document.querySelectorAll('[title],[aria-label]')].map(e => (e.getAttribute('title') || '') + ' ' + (e.getAttribute('aria-label') || '')).join(' '); return ['region.intel', 'other.intel'].filter(c => txt.includes(c) || attrs.includes(c)); }")
    check(not pg.evaluate("() => !!document.querySelector('.it-pop:not([hidden])')") and leak == [], f'no intel channel name shown outside the gear (text or hover) {leak}')
    al = pg.evaluate("() => [__fs.beeps, __fs.notes.map(n => n[0])]")
    check(al == [3, ['8WA-Z6 · 1 jump', 'Y-OMTZ · 3 jumps', 'D-W7F0 · 2 jumps']], f'alerts: sound and notification for hostile/neutral within 3 jumps, not 4, not friendlies {al}')
    badge = pg.evaluate("() => [document.querySelector('#intelNear').hidden, document.querySelector('#intelNear').textContent]")
    check(badge == [False, '4 near'], f'the header: "4 near" {badge}')
    pg.click('#tabBtnPilot'); pg.click('#intelNear'); pg.wait_for_timeout(300)   # v.97: the pill opens Intel and doesn't switch it off
    pill = pg.evaluate("() => [it.on, document.querySelector('#intelSw').checked, getComputedStyle(document.querySelector('#tabIntel')).display, document.querySelector('#intelNear').title]")
    check(pill[:3] == [True, True, 'block'] and pill[3] == '4 systems with a hostile or neutral report within 3 jumps: open Intel',
          f'pressing "4 near" opens the Intel tab and leaves Intel on (v.96: it turned Intel off) {pill}')
    W(pg, F_INTEL, line(time.time(), 'Scout Alt', '8WA-Z6 Marrek Ketter still'))
    tick(pg)
    check(pg.evaluate("() => __fs.beeps") == 3, 'one alert per system per 30 s')
    # ---- v.104: head counts, and the words around a sighting (the owner's report) ----
    T2 = time.time()
    W(pg, F_INTEL, line(T2, 'Gate Watcher', 'JP4-AA* 1red') + line(T2 + 1, 'Kai Rhenn', 'FM-JK5 Kirra Longtail (recently seen as sabre) Seren Ketter (loki)') + line(T2 + 2, 'Scout Alt', '3-DMQT 2 neuts'))
    tick(pg, 3200)
    got = {f['raw']: f for f in pg.evaluate(FEED)}
    c1, c2, c3 = got.get('Gate Watcher > JP4-AA* 1red'), got.get('Kai Rhenn > FM-JK5 Kirra Longtail (recently seen as sabre) Seren Ketter (loki)'), got.get('Scout Alt > 3-DMQT 2 neuts')
    nr = {r[0]: r for r in pg.evaluate(NEAR)}
    pr = pg.evaluate("() => { const st = it.near.get(it.names.byLower.get('fm-jk5')); return st ? Object.fromEntries([...st.pairs].map(([id, s]) => [st.pilots.find(x => x.id === id).name, s.name])) : null; }")
    asked = sorted({'1red', 'recently', 'as', 'recently seen', 'seen as'} & IDS_ASKED)
    check(c1 and c1['chips'] == [['sys', f'JP4-AA {D0[SYSID["JP4-AA"]]}j'], ['kw', '1 red']] and c3 and c3['chips'] == [['sys', f'3-DMQT {D0[SYSID["3-DMQT"]]}j'], ['kw', '2 neut']]
          and c2 and c2['chips'] == [['sys', f'FM-JK5 {D0[SYSID["FM-JK5"]]}j'], ['n', 'Kirra Longtail'], ['h', 'Seren Ketter'], ['ship', 'Sabre'], ['ship', 'Loki']] and c2['left'] == '' and not asked and pr == {'Kirra Longtail': 'Sabre', 'Seren Ketter': 'Loki'}
          and nr.get('JP4-AA', [0, 0, 0])[2] == '1 hostile' and nr.get('3-DMQT', [0, 0, 0])[2] == '2 neutral',
          f'"1red" and "2 neuts": head counts, not pilots; "Kirra Longtail (recently seen as sabre) Seren Ketter (loki)": each pilot paired with the ship in their brackets; none looked up ({c1 and c1["chips"]}, {c3 and c3["chips"]}, {c2 and c2["chips"]}, {c2 and c2["left"]!r}, {asked}, {pr}, {nr.get("JP4-AA")}, {nr.get("3-DMQT")})')
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
    check(pop == ['Chat logs folder', 'Intel channels', 'You', 'Range and alerts'], f'the gear opens the settings while watching {pop}')
    opt = pg.evaluate("""() => [...document.querySelectorAll('.it-pop select option')].map(o => { const c = getComputedStyle(o); return [c.backgroundColor, c.color]; })""")
    lum = lambda c: (lambda v: 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2])([int(x) for x in re.findall(r'\d+', c)[:3]])
    check(opt and all(re.match(r'rgb\(', bg) and lum(bg) < 60 and lum(fg) > 180 for bg, fg in opt),
          f'the open lists of the settings: light text on a dark background (v.96: light on white on Windows) {sorted(set(map(tuple, opt)))}')
    pg.select_option('.it-pop [data-it-set="range"]', '5'); pg.wait_for_timeout(100)
    check(pg.evaluate("() => JSON.parse(localStorage.getItem('dscanIntel')).range") == 5, 'alert range kept')
    kr = pg.evaluate("() => [document.querySelector('.it-pop [data-it-set=\"killRange\"]').value, [...document.querySelectorAll('.it-pop [data-it-set=\"killRange\"] option')].map(o => o.value).join(',')]")
    pg.select_option('.it-pop [data-it-set="killRange"]', '15'); pg.wait_for_timeout(100)
    check(kr == ['10', '3,5,7,10,15,20,30'] and pg.evaluate("() => [JSON.parse(localStorage.getItem('dscanIntel')).killRange, itKillRange()]") == [15, 15],
          f'v2026.10.29.3: the Feed\'s kill range under the gear, 10 jumps unless changed, kept (15) {kr}')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    check(pg.evaluate("() => !document.querySelector('.it-pop')"), 'Escape closes the settings')
    # ---- off ----
    pg.click('#intelSwLabel'); pg.wait_for_timeout(300)
    off = pg.evaluate("() => [document.querySelector('#intelSw').checked, it.on, it.ticker, document.querySelector('#intelNear').hidden]")
    stopped = pg.inner_text('#intelPanel .it-sub')
    check(off == [False, False, None, True] and stopped == 'Stopped. The switch beside the gear starts it again.', f'the switch on the card turns it off; the pill goes {off} ({stopped!r})')
    n0 = len(pg.evaluate(FEED))
    W(pg, F2, line(time.time(), 'Scout Alt', '4X0-8B Marrek Ketter')); tick(pg)
    check(len(pg.evaluate(FEED)) == n0, 'off: no more reading')
    NAMES_CALLS.clear(); pg.click('#intelSwLabel'); tick(pg)
    check(NAMES_CALLS == [] and pg.evaluate("() => it.on"), 'on again: the system names not asked again')
    pg.click('#intelSwLabel'); pg.wait_for_timeout(200)
    # ---- v2026.10.29.5: no build warning ----
    STATUS['v'] = str(J['build'] + 1); pg.reload(); pg.wait_for_timeout(300); pg.click('#tabBtnIntel')
    setup_logs(pg); pg.click('[data-it-act="folder"]'); pg.wait_for_timeout(300)   # the made-up folder can't be kept in IndexedDB: chosen again
    pg.click('#intelSwLabel'); tick(pg)
    warn = pg.evaluate("() => [...document.querySelectorAll('#intelPanel .it-warn')].map(e => e.textContent)")
    info = pg.evaluate("() => CARD_INFO.intel.join(' ')")
    # v2026.10.29.5 (the owner: "is there a way to automate the update so the user never has to see it?"): EVE on a newer build
    # than the table's says nothing and asks ESI nothing; the GitHub Action keeps the table current (tools/jump_table_update.py)
    check(not any('jump table' in w for w in warn) and not STATUS.get('asked') and 'checked against each new EVE build every day' in info,
          f'EVE on a newer build than the jump table: no warning, no /status/ request ({STATUS.get("asked", 0)}), the info panel says the table is checked daily {warn}')
    STATUS['v'] = str(J['build'])
    shot_w = pg.evaluate("() => document.documentElement.scrollWidth")
    pg.screenshot(path='/tmp/intel_1440.png', full_page=True)
    ctx.close()
    # ---- errors ----
    ctx = new_ctx(1440, 'window.__noFsApi = true;'); pg = ctx.new_page(); pg.goto('file://' + HTML); pg.wait_for_timeout(300)
    pg.click('#tabBtnIntel'); pg.click('#intelSwLabel'); pg.wait_for_timeout(300)
    e = pg.inner_text('#intelPanel .pr-msg.err')
    check(e.endswith('(INTEL-01)') and not pg.evaluate("() => document.querySelector('#intelSw').checked"), f'no File System Access API: INTEL-01, the slider back off ({e!r})')
    ctx.close()
    ctx = new_ctx(1440); pg = ctx.new_page(); pg.goto('file://' + HTML); pg.wait_for_timeout(300); pg.click('#tabBtnIntel')
    W(pg, 'notes.txt', 'x'); pg.click('[data-it-act="folder"]'); pg.wait_for_timeout(300)
    e = pg.inner_text('#intelPanel .pr-msg.err'); check(e.endswith('(INTEL-04)'), f'a folder with no chat logs: INTEL-04 ({e!r})')
    ctx.close()
    STATUS['names_fail'] = True
    ctx = new_ctx(390); pg = ctx.new_page(); pg.goto('file://' + HTML); pg.wait_for_timeout(300)
    pg.evaluate("(s) => localStorage.setItem('dscanSide', JSON.stringify(s))", SIDE); pg.reload(); pg.wait_for_timeout(300)
    setup_logs(pg); pg.click('#tabBtnIntel'); pg.click('[data-it-act="folder"]'); pg.wait_for_timeout(300)
    pg.check('[data-it-chan="region.intel"]'); pg.check(f'[data-it-me="{MAIN}"]'); pg.click('#intelSwLabel'); tick(pg)
    e = pg.inner_text('#intelPanel .pr-msg.err')
    check(e.endswith('(INTEL-03)') and not pg.evaluate("() => it.on"), f'the system names fail: INTEL-03, off ({e!r})')
    STATUS['names_fail'] = False
    pg.click('#intelSwLabel'); tick(pg)
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
