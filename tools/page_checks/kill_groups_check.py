"""The Fleet tab's kill picker groups Intel's kills into fleets by shared pilots (v2026.11.01.6).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/kill_groups_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner's backlog item "Intel kills grouped by shared attackers", build spec in the Project doc roadmap/kill-groups-impact.md
section 0 ("go with 2 shared pilots", "keep the exception as you intended", "let's do the headers staying in place and add the
expand/collapse", "just have each fleet default to collapsed", "biggest first sounds good"; before the build: a lone group
"Open it", and on a phone ISK, age and victims on a "Second line when open"). Made-up battles only, no real pilots or kills: the
pilots are sa_mocks.py's, the killmails are made here and handed to the Fleet tab as a Near You badge hands them (fkOpen with the
picks), so nothing is read from zKillboard. The expected fleets are worked out again here, in Python, from the attackers:
  * a two-sided brawl with a third party on one kill of each side, a solo hunter's 2 kills, a pair's kill and a gank:
    Fleet 1 (gang A, 7 kills), Fleet 2 (the other side, 4: their victims are gang A's pilots, and victims never link), Fleet 3
    (the hunter, solo, by the 1-pilot exception, the newest kill: biggest first, not newest), "Not linked" (2); the line above
    says "3 fleets by shared pilots";
  * every group starts closed; the one holding the kill analyzed says "analyzing"; each heading: its pilots and kills, the ISK in
    amber (zKillboard's values added), the newest kill's age, the victims as Near You counts them; the rule in its hover;
  * a heading pressed opens its kills (newest first), aria-expanded, the focus on it, the heading where it was on screen;
    several open at once; a kill pressed is analyzed, its fleet stays open and now says "analyzing", the focus stays on that
    kill through the redraws; an open fleet's heading stays at the top of the list while its kills scroll under it, and closing
    it there leaves it where it was; a redraw keeps what's open; a new set of kills starts closed again;
  * a camp (5 kills by the same campers): one fleet, open from the start (a lone group);
  * 120 kills: 2 fleets of 55 and 10 not linked, in that order, closed; opened, about six and a half rows show and the rest
    scroll inside, a kill half under the pinned heading pressed shows whole below it, the wheel at the end moves the page on
    (LESSON #96); grouping them takes a few milliseconds;
  * 390 px: each heading one line, 44 px tall; opened, the ISK, age and victims on a second line; nothing off the page;
  * v2026.11.01.7 (the owner: "we should swap the fleet size and isk value placement"): each kill's pilots, then its ISK, wide
    and at 390 px;
  * no page errors.
v2026.11.01.5 fails (no fleets: every kill in one list).
"""
import sys, os, re, time, json, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from playwright.sync_api import sync_playwright
import sa_mocks as M

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok

SYS = 30004759   # 1DQ1-A in the mocks
IDS = sorted(i for i in M.PILOTS if i < 92000000)
pool = iter(IDS)
take = lambda n: [next(pool) for _ in range(n)]
RIFTER = M.byname['Rifter']
NOW = time.time() * 1000
_kid = [9700000]
def kill(att, victim, v, isk, mins, ship='Rifter'):
    _kid[0] += 1; k = _kid[0]
    km = {'killmail_id': k, 'killmail_time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(NOW / 1000 - mins * 60)), 'solar_system_id': SYS,
          'victim': {'character_id': victim, **{x: y for x, y in M.aff(victim).items() if x != 'character_id'}, 'ship_type_id': M.byname[ship], 'damage_taken': 900, 'items': [], 'position': {'x': 0, 'y': 0, 'z': 0}},
          'attackers': [dict(M.aff(c), final_blow=i == 0, damage_done=100, security_status=0, ship_type_id=RIFTER) for i, c in enumerate(att)]
                       + [{'faction_id': 500001, 'ship_type_id': RIFTER, 'damage_done': 5, 'final_blow': False, 'security_status': 0}]}   # an NPC on every kill: never links
    return {'id': k, 'hash': f'{k:040x}', 'km': km, 'name': M.PILOTS[victim][0], 'ship': ship, 'sys': '1DQ1-A', 'sysId': SYS, 'ships': len(att), 't': NOW - mins * 60000, 'v': v, 'isk': isk}

# ---- battle 1: a brawl, a third party, a solo hunter, a pair, a gank
A, B, X, H, C, Y, VN = take(14), take(9), take(1), take(1), take(2), take(3), take(12)
pk = lambda arr, idx: [arr[i] for i in idx]
B1 = [kill(pk(A, range(8)), VN[0], 'n', 180e6, 3), kill(pk(A, [0, 2, 4, 6, 8, 9]) + X, VN[1], 'n', 95e6, 2), kill(pk(A, [1, 3, 5, 10, 11]), VN[2], 'n', 60e6, 3),
      kill(A, VN[3], 'n', 240e6, 4), kill(pk(A, [6, 7, 12, 13]), VN[4], 'n', 70e6, 6), kill(pk(A, [6, 7]), VN[5], 'n', 2e6, 6.5, 'Capsule'), kill(pk(A, [2, 3, 9, 11, 12]), VN[6], 'n', 85e6, 9),
      kill(pk(B, range(6)), A[2], 'h', 310e6, 2.5), kill(pk(B, [1, 2, 6, 7]) + X, A[7], 'h', 75e6, 3.5), kill(pk(B, [0, 3, 4, 8]), A[10], 'h', 280e6, 5), kill(pk(B, [5, 6, 7, 8]), A[12], 'h', 40e6, 8),
      kill(H, VN[7], 'n', 8e6, 1.9), kill(H, VN[8], 'n', 12e6, 13), kill(C, VN[9], 'f', 30e6, 7), kill(Y, VN[10], 'n', 25e6, 14)]
# ---- battle 2: a camp, the same 4 campers (and a fifth now and then)
CAMP, VC = take(5), take(5)
B2 = [kill(CAMP[:4] + ([CAMP[4]] if i % 2 else []), VC[i], 'n', 20e6 + i, 2 + i * 3) for i in range(5)]
# ---- battle 3: 120 kills, two gangs of 30 and 10 kills by strangers
random.seed(5)
G1, G2 = take(30), take(30)
B3 = []
for i in range(110):
    g = G1 if i % 2 == 0 else G2
    B3.append(kill(random.sample(g, random.randint(5, 10)), random.choice(VN + VC), 'n' if i % 3 else 'h', 10e6 + i * 1e5, 1 + i * 0.4))
for i in range(10): B3.append(kill(take(3), random.choice(VN), 'n', 5e6, 50 + i))

def groups(P):
    """The rule, again, in Python: 2 shared player attackers (1 when either kill had 1-2) link two kills; chains; the rest Not linked."""
    att = [set(a['character_id'] for a in p['km']['attackers'] if a.get('character_id')) for p in P]
    parent = list(range(len(P)))
    def find(i):
        while parent[i] != i: i = parent[i]
        return i
    for i in range(len(P)):
        for j in range(i + 1, len(P)):
            if len(att[i] & att[j]) >= (1 if min(len(att[i]), len(att[j])) <= 2 else 2): parent[find(i)] = find(j)
    by = {}
    for i in range(len(P)): by.setdefault(find(i), []).append(i)
    mk = lambda idx: {'ids': [P[i]['id'] for i in sorted(idx, key=lambda i: -P[i]['t'])], 'pilots': len(set().union(*[att[i] for i in idx])), 'isk': sum(P[i]['isk'] for i in idx), 'newest': max(P[i]['t'] for i in idx),
                      'vic': {v: sum(1 for i in idx if P[i]['v'] == v) for v in 'hnf'}}
    fl = sorted([mk(l) for l in by.values() if len(l) > 1], key=lambda g: (-g['pilots'], -len(g['ids']), -g['newest']))
    lone = [i for l in by.values() if len(l) == 1 for i in l]
    return fl, (mk(lone) if lone else None)

OPEN = """(P) => { P = P.slice().sort((a, b) => b.t - a.t); for(const p of P){ const w = IT_KILL_WORD[p.v]; p.word = [w[0], w[1]]; }
  window.__P = P; fkOpen(P[0].id, P[0].hash, null, null, {from: 'intel', km: P[0].km, picks: P}); return P[0].id; }"""
HEADS = """() => [...document.querySelectorAll('#fleetPanel .fk-picks button.fk-kg-h')].map(h => ({key: h.dataset.fkKg, t: h.querySelector('.fk-kg-t').textContent, m: h.querySelector('.fk-kg-m').textContent,
  open: h.getAttribute('aria-expanded'), ctl: h.getAttribute('aria-controls'), here: !!h.querySelector('.fk-kg-here'), title: h.title,
  isk: (h.querySelector('.it-isk') || {}).textContent || '', iskC: h.querySelector('.it-isk') ? getComputedStyle(h.querySelector('.it-isk')).color : '',
  age: (h.querySelector('.fk-kg-a') || {}).textContent || '', vic: [...h.querySelectorAll('.it-kl')].map(x => x.textContent),
  rows: [...h.parentElement.querySelectorAll('button.fk-pk')].map(b => fk.picks[Number(b.dataset.fkPick)].id)}))"""
Y_OF = "(key) => { const L = document.querySelector('#fleetPanel .fk-picks'), h = L.querySelector(`[data-fk-kg=\"${key}\"]`); return h.getBoundingClientRect().top - L.getBoundingClientRect().top; }"
FOCUS = "() => { const a = document.activeElement; return a ? (a.dataset.fkKg ? 'kg:' + a.dataset.fkKg : a.dataset.fkPick !== undefined ? 'pick:' + fk.picks[Number(a.dataset.fkPick)].id : a.tagName) : null; }"
def isk(pg, v): return pg.evaluate('(v) => itIsk(v)', v)
def ago(pg, t): return pg.evaluate('(t) => itAgo(t)', t)

with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []
    def new_ctx(w):
        ctx = b.new_context(bypass_csp=True, viewport={'width': w, 'height': 1000}); ctx.on('page', lambda pg: pg.on('pageerror', lambda e: errs.append(str(e)))); M.route(ctx); return ctx
    ctx = new_ctx(1480)
    pg = ctx.new_page(); pg.goto('file://' + HTML); pg.wait_for_timeout(600)
    # ---- battle 1
    first = pg.evaluate(OPEN, B1); pg.wait_for_timeout(1500)
    fl, lone = groups(B1)
    check([len(g['ids']) for g in fl] == [7, 4, 2] and lone and len(lone['ids']) == 2 and fl[2]['pilots'] == 1, f'(the made-up brawl: 7 / 4 / 2 + 2 not linked) {[len(g["ids"]) for g in fl]}')
    hs = pg.evaluate(HEADS)
    want = [[f'Fleet {i + 1}', 'solo · 2 kills' if g['pilots'] == 1 else f"{g['pilots']} pilots · {len(g['ids'])} kills"] for i, g in enumerate(fl)] + [['Not linked', '2 kills']]
    check([[h['t'], h['m']] for h in hs] == want, f'the brawl: gang A, the other side (their victims are gang A: victims never link) and the solo hunter (the 1-pilot exception) as fleets, biggest first, then Not linked\n      page {[[h["t"], h["m"]] for h in hs]}\n      want {want}')
    line = pg.evaluate("() => document.querySelector('#fleetPanel .fk-pk-h').textContent")
    check(line == '15 kills in 1DQ1-A from Intel · 3 fleets by shared pilots · as they were when you opened this', f'the line above: "3 fleets by shared pilots" {line!r}')
    here0 = [first in g['ids'] for g in fl + [lone]]
    check(here0 == [False, False, True, False] and all(h['open'] == 'false' and not h['rows'] for h in hs) and [h['here'] for h in hs] == here0 and pg.evaluate("() => fk.killId") == first,
          f'every group closed; "analyzing" on the fleet holding the newest kill, the one analyzed {[(h["open"], len(h["rows"]), h["here"]) for h in hs]}')
    wx = [[isk(pg, g['isk']), f"newest {ago(pg, g['newest'])} ago", [f"{g['vic'][v]} {pg.evaluate('([v, n]) => IT_KILL_WORD[v][n === 1 ? 2 : 3]', [v, g['vic'][v]])}" for v in 'hnf' if g['vic'][v]]] for g in fl + [lone]]
    check([[h['isk'], h['age'], h['vic']] for h in hs] == wx and all(h['iskC'] == 'rgb(217, 154, 60)' for h in hs),
          f'each heading: the ISK added up (amber), the newest kill\'s age, the victims as Near You counts them\n      page {[[h["isk"], h["age"], h["vic"]] for h in hs]}\n      want {wx}')
    check(all('share at least 2 pilots' in h['title'] and 'Victims never link' in h['title'] for h in hs[:3]) and 'fewer than 2 pilots' in hs[3]['title'], f'the rule in each heading\'s hover {hs[0]["title"]!r} {hs[3]["title"]!r}')
    # open Fleet 2
    y0 = pg.evaluate(Y_OF, 'f1'); pg.click('#fleetPanel [data-fk-kg="f1"]'); pg.wait_for_timeout(300)
    hs = pg.evaluate(HEADS); y1 = pg.evaluate(Y_OF, 'f1'); fo = pg.evaluate(FOCUS)
    ctl = pg.evaluate("(id) => !!document.getElementById(id)", hs[1]['ctl'] or 'x')
    ORDER = "() => [...document.querySelectorAll('#fleetPanel .fk-kg-r button.fk-pk')].map(b => { const a = b.querySelector('.fk-pk-a').getBoundingClientRect(), i = b.querySelector('.fk-pk-i').getBoundingClientRect(); return [a.right <= i.left + 1, Math.abs(a.top - i.top) < 3]; })"
    od = pg.evaluate(ORDER); hi = pg.evaluate("() => { const h = document.querySelector('#fleetPanel [data-fk-kg=\"f1\"] .it-isk').getBoundingClientRect(), r = document.querySelector('#fleetPanel .fk-kg-r button.fk-pk .fk-pk-i').getBoundingClientRect(); return Math.round(h.right - r.right); }")
    check(od and all(x == [True, True] for x in od), f'v2026.11.01.7 ("swap the fleet size and isk value placement"): each kill\'s pilots, then its ISK (under the heading\'s ISK, {hi} px apart) {od[:2]}')
    check(hs[1]['open'] == 'true' and hs[1]['rows'] == fl[1]['ids'] and ctl and abs(y1 - y0) <= 1 and fo == 'kg:f1' and all(h['open'] == 'false' for i, h in enumerate(hs) if i != 1),
          f'Fleet 2 opened: its kills newest first, aria-expanded, the focus on the heading, the heading where it was ({y0} -> {y1}, {fo}) {hs[1]["rows"]} want {fl[1]["ids"]}')
    # a kill in it pressed: analyzed; the fleet still open, now "analyzing"; the focus kept through the redraws
    k2 = fl[1]['ids'][1]
    pg.click(f'#fleetPanel [data-fk-pick="{pg.evaluate("(id) => fk.picks.findIndex(p => p.id === id)", k2)}"]'); pg.wait_for_timeout(3000)
    hs = pg.evaluate(HEADS); fo = pg.evaluate(FOCUS)
    check(pg.evaluate("() => fk.killId") == k2 and hs[1]['open'] == 'true' and [h['here'] for h in hs] == [False, True, False, False] and fo == f'pick:{k2}',
          f'a kill pressed: analyzed, its fleet still open and now "analyzing", the focus still on it after the redraws ({fo}) {[(h["open"], h["here"]) for h in hs]}')
    # several open; a pinned heading
    pg.click('#fleetPanel [data-fk-kg="f0"]'); pg.wait_for_timeout(300)
    hs = pg.evaluate(HEADS)
    check(hs[0]['open'] == 'true' and hs[1]['open'] == 'true', 'several fleets open at once')
    pin = pg.evaluate("""() => { const L = document.querySelector('#fleetPanel .fk-picks'), g = L.querySelector('[data-fk-kg="f0"]').parentElement;
      L.scrollTop = g.offsetTop - L.offsetTop + 70; const h = g.querySelector('.fk-kg-h'), r = g.querySelector('button.fk-pk:last-child');
      return [h.getBoundingClientRect().top - L.getBoundingClientRect().top, L.scrollTop, getComputedStyle(h).position]; }""")
    pg.wait_for_timeout(100)
    check(pin[2] == 'sticky' and abs(pin[0]) <= 1.5 and pin[1] > 60, f'an open fleet scrolled into: its heading stays at the top of the list while its kills scroll under it {pin}')
    yp = pg.evaluate(Y_OF, 'f0'); pg.click('#fleetPanel [data-fk-kg="f0"]'); pg.wait_for_timeout(300)
    yq = pg.evaluate(Y_OF, 'f0'); fo = pg.evaluate(FOCUS); hs = pg.evaluate(HEADS)
    check(hs[0]['open'] == 'false' and abs(yq - yp) <= 2 and fo == 'kg:f0', f'the pinned heading pressed: closed, left where it was on screen ({yp} -> {yq}), the focus on it ({fo})')
    pg.evaluate("() => fkRender()"); pg.wait_for_timeout(200)
    check([h['open'] for h in pg.evaluate(HEADS)] == ['false', 'true', 'false', 'false'], 'a redraw keeps what\'s open')
    pg.click('#fleetPanel [data-fk-kg="nl"]'); pg.wait_for_timeout(300)
    hs = pg.evaluate(HEADS)
    check(hs[3]['rows'] == lone['ids'], f'Not linked opened: its kills, newest first {hs[3]["rows"]} (want {lone["ids"]})')
    # a new set of kills: closed again
    pg.evaluate(OPEN, B1); pg.wait_for_timeout(1200)
    check([h['open'] for h in pg.evaluate(HEADS)] == ['false'] * 4, 'a new set of kills (another badge) starts closed again')
    # ---- battle 2: a camp
    pg.evaluate(OPEN, B2); pg.wait_for_timeout(1200)
    hs = pg.evaluate(HEADS); line = pg.evaluate("() => document.querySelector('#fleetPanel .fk-pk-h').textContent")
    fl2, lone2 = groups(B2)
    check(len(fl2) == 1 and not lone2 and [(h['t'], h['m'], h['open'], h['here']) for h in hs] == [('Fleet 1', '5 pilots · 5 kills', 'true', True)] and hs[0]['rows'] == fl2[0]['ids'] and '· 1 fleet by shared pilots ·' in line,
          f'a camp: one fleet, open from the start (a lone group) {[(h["t"], h["m"], h["open"]) for h in hs]} {line!r}')
    # ---- battle 3: 120 kills
    pg.evaluate(OPEN, B3); pg.wait_for_timeout(1500)
    hs = pg.evaluate(HEADS); fl3, lone3 = groups(B3)
    check([(h['t'], h['m'], h['open']) for h in hs] == [(f'Fleet {i + 1}', f"{g['pilots']} pilots · {len(g['ids'])} kills", 'false') for i, g in enumerate(fl3)] + [('Not linked', '10 kills', 'false')]
          and [len(g['ids']) for g in fl3] == [55, 55], f'120 kills: two fleets of 55 and 10 not linked, in order, all closed {[(h["t"], h["m"], h["open"]) for h in hs]}')
    ms = pg.evaluate("() => { const t = performance.now(); for(let i = 0; i < 20; i++) fkGroupKills(fk.picks); return (performance.now() - t) / 20; }")
    check(ms < 15, f'grouping 120 kills: {ms:.2f} ms')
    pg.click('#fleetPanel [data-fk-kg="f0"]'); pg.wait_for_timeout(400)
    sc = pg.evaluate("""() => { const L = document.querySelector('#fleetPanel .fk-picks'), B = L.querySelectorAll('button.fk-pk'), h = B[0].getBoundingClientRect().height;
      return {rows: +(L.clientHeight / (h + 4)).toFixed(2), n: B.length, scrolls: L.scrollHeight > L.clientHeight + 4, ob: getComputedStyle(L).overscrollBehaviorY}; }""")
    check(sc['n'] == 55 and 6.0 <= sc['rows'] <= 7.2 and sc['scrolls'] and sc['ob'] == 'auto', f'Fleet 1 opened: about six and a half rows show, the rest scroll inside {sc}')
    # a kill half under the pinned heading, pressed: scrolled so it shows whole, below the heading
    hu = pg.evaluate("""() => { const L = document.querySelector('#fleetPanel .fk-picks'), B = [...L.querySelectorAll('button.fk-pk')], r = B[10];
      L.scrollTop = r.offsetTop - L.offsetTop - 20; const h = L.querySelector('[data-fk-kg="f0"]'), q = r.getBoundingClientRect(), hb = h.getBoundingClientRect().bottom;
      return [Number(r.dataset.fkPick), q.top < hb, q.left + 60, (Math.max(hb, q.top) + q.bottom) / 2]; }""")
    pg.mouse.click(hu[2], hu[3]); pg.wait_for_timeout(2500)
    hv = pg.evaluate("(i) => { const L = document.querySelector('#fleetPanel .fk-picks'), b = L.querySelector(`[data-fk-pick=\"${i}\"]`), h = L.querySelector('[data-fk-kg=\"f0\"]'); return [b.getAttribute('aria-pressed'), b.getBoundingClientRect().top - h.getBoundingClientRect().bottom]; }", hu[0])
    check(hu[1] and hv[0] == 'true' and hv[1] >= -1, f'a kill half under the pinned heading, pressed: it shows whole, below the heading {hu[:2]} {hv}')
    pg.evaluate("() => { window.scrollTo(0, 0); const L = document.querySelector('#fleetPanel .fk-picks'); L.scrollTop = L.scrollHeight; }"); pg.wait_for_timeout(200)
    bx = pg.evaluate("() => { const r = document.querySelector('#fleetPanel .fk-picks').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }")
    pg.mouse.move(*bx); pg.mouse.wheel(0, 300); pg.wait_for_timeout(500)
    wy = pg.evaluate("() => window.scrollY"); pg.evaluate("() => window.scrollTo(0, 0)")
    check(wy > 50, f'the wheel at the end of the list moves the page on ({wy} px)')
    # wide: one line
    pg.evaluate(OPEN, B1); pg.wait_for_timeout(1200)
    wl = pg.evaluate("() => { const h = document.querySelector('#fleetPanel [data-fk-kg=\"f0\"]'), t = h.querySelector('.fk-kg-t').getBoundingClientRect(), x = h.querySelector('.fk-kg-x').getBoundingClientRect(); return [Math.abs(t.top + t.height / 2 - (x.top + x.height / 2)) < 6, Math.round(h.getBoundingClientRect().height)]; }")
    check(wl[0] and wl[1] <= 40, f'a wide window: each heading on one line {wl}')
    ctx.close()
    # ---- phone
    ctx = new_ctx(390); pg = ctx.new_page(); pg.goto('file://' + HTML); pg.wait_for_timeout(600)
    pg.evaluate(OPEN, B1); pg.wait_for_timeout(1500)
    ph = pg.evaluate("() => [...document.querySelectorAll('#fleetPanel button.fk-kg-h')].map(h => [Math.round(h.getBoundingClientRect().height), getComputedStyle(h.querySelector('.fk-kg-x')).display])")
    pg.click('#fleetPanel [data-fk-kg="f0"]'); pg.wait_for_timeout(300)
    po = pg.evaluate("() => { const h = document.querySelector('#fleetPanel [data-fk-kg=\"f0\"]'), t = h.querySelector('.fk-kg-t').getBoundingClientRect(), x = h.querySelector('.fk-kg-x'), r = x.getBoundingClientRect(); return [getComputedStyle(x).display, r.top >= t.bottom - 1, h.querySelector('.it-isk').checkVisibility(), r.right <= h.getBoundingClientRect().right + 1]; }")
    ow = pg.evaluate("() => [document.documentElement.scrollWidth, [...document.querySelectorAll('#fleetPanel .fk-picks *')].filter(e => { const r = e.getBoundingClientRect(); return e.checkVisibility() && r.width && r.right > innerWidth + 1; }).length]")
    pod = pg.evaluate("() => [...document.querySelectorAll('#fleetPanel .fk-kg-r button.fk-pk')].map(b => { const a = b.querySelector('.fk-pk-a').getBoundingClientRect(), i = b.querySelector('.fk-pk-i').getBoundingClientRect(); return a.right <= i.left + 1 && Math.abs(a.top - i.top) < 3; })")
    check(pod and all(pod), f'390 px: the pilots, then the ISK, on the second line {pod[:3]}')
    check(all(h[0] >= 44 and h[0] <= 48 and h[1] == 'none' for h in ph) and po == ['flex', True, True, True] and ow[0] <= 390 and ow[1] == 0,
          f'390 px: each heading one line, 44 px; opened, the ISK, age and victims on a second line; nothing off the page {ph} {po} {ow}')
    ctx.close()
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
