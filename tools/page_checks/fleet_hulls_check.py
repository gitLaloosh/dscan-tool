"""The Fleet tab's hull counts on each "Fleet N" heading, and one Intel kill shown like several (v2026.11.04.2).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/fleet_hulls_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner: "add a column to the "fleet N" summary row for Fleet on a kill that shows a count of each hull in the fleet" (Project doc
roadmap/fleet-hulls-plan.md); after mockups: "looks good", narrow headings "B · own line", the shortfall "Hover only", a solo fleet
"Show it", a phone "Only when opened"; and "let's start treating any single killmails being sent from the intel tab the same as we
do for multiple" ("fleet 1 is fine", "with 009 as one version"). Made-up pilots (sa_mocks.py), real hulls; the killmails are made
here and handed to the Fleet tab as a Near You badge hands them, so nothing is read from zKillboard. The counts are worked out
again here, in Python, from the attackers:
  * a made-up battle: Fleet 1, 48 pilots over 4 kills and 11 hulls (one pilot reshipped Ferox -> Muninn: once, in the Muninn;
    2 in pods, 1 manning an Astrahus and an NPC: not counted); Fleet 2, 8 pilots and 4 hulls (no "+N more"); Fleet 3, a solo
    Loki over 2 kills; 2 kills Not linked;
  * each fleet's strip: the hulls by count then name, the first 4 as icons with their counts, "+N more"; the hover: every
    hull with its ship class and count, "45 of 48 pilots in ships" and the rule; none on Not linked;
  * nothing while the hulls' types are still being looked up (their ESI answers held back 2.5 s in the page), then the strip, with the focus kept on the
    heading through that redraw; no request to zKillboard;
  * the strip is part of the heading: nothing inside it can be pressed, and pressing it opens and closes the fleet;
  * layout: one line at 1440 and 1100 px; at 1024 and 900 the hulls on their own line under the heading, all 4 still there,
    inside it; a phone (390): closed headings one line with no hulls, opened: 3 hulls and "+8 more" on their own line,
    nothing off the page;
  * one Intel kill: the kill list ("1 kill in Amamake from Intel · as it was when you opened this"), its Fleet 1 open and
    "analyzing", "6 pilots · 1 kill", its 3 hulls, "5 min ago" (no "newest"); a solo kill: "solo · 1 kill" and its one hull;
    a kill with no player: "NPCs · 1 kill", no hulls; the same kill opened from a Pilot Dossier: no list (unchanged);
  * no page errors.
v2026.11.04.1 fails (no hulls; one kill opens with no list).
"""
import sys, os, re, time, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from playwright.sync_api import sync_playwright
import sa_mocks as M

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok

# ---- the made-up battle (the mockup's, claude/roadmap/fleet-hulls-mockup/battle.py)
SYS = 30002537   # Amamake
IDS = sorted(i for i in M.PILOTS if i < 92000000)
pool = iter(IDS)
take = lambda n: [next(pool) for _ in range(n)]
T = M.byname
NOW = time.time() * 1000
_kid = [9800000]
def kill(att, victim, v, isk, mins, vship='Rifter'):
    _kid[0] += 1; k = _kid[0]; A = []
    for i, (c, ship) in enumerate(att):
        a = {'damage_done': 100 + i, 'final_blow': i == 0, 'security_status': 0, 'ship_type_id': T[ship]}
        if c: a.update(M.aff(c))
        else: a['faction_id'] = 500001   # an NPC
        A.append(a)
    km = {'killmail_id': k, 'killmail_time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(NOW / 1000 - mins * 60)), 'solar_system_id': SYS,
          'victim': {'character_id': victim, **{x: y for x, y in M.aff(victim).items() if x != 'character_id'}, 'ship_type_id': T[vship], 'damage_taken': 9000, 'items': [], 'position': {'x': 0, 'y': 0, 'z': 0}},
          'attackers': A}
    return {'id': k, 'hash': f'{k:040x}', 'km': km, 'name': M.PILOTS[victim][0], 'ship': vship, 'sys': 'Amamake', 'sysId': SYS,
            'ships': len([a for a in att if a[0]]), 't': NOW - mins * 60000, 'v': v, 'isk': isk}
F1 = take(48)
plan1 = (['Ferox'] * 18 + ['Muninn'] * 6 + ['Basilisk'] * 6 + ['Scimitar'] * 3 + ['Sabre'] * 2 + ['Huginn'] * 2 + ['Lachesis'] * 2
         + ['Kikimora', 'Hurricane', 'Stiletto', 'Drake'] + ['Capsule'] * 2 + ['Astrahus'] + ['Ferox', 'Ferox'])
SHIP1 = dict(zip(F1, plan1)); RESHIP = F1[46]
V = take(14)
def att1(members, newest=False): return [(c, ('Muninn' if (c == RESHIP and newest) else SHIP1[c])) for c in members] + [(None, 'Rifter')]
K1 = [kill(att1(F1[:30]), V[0], 'n', 420e6, 4), kill(att1(F1[10:40]), V[1], 'h', 160e6, 7), kill(att1(F1[20:47]), V[2], 'n', 95e6, 9),   # F1[46]: a Ferox here, older
      kill(att1([F1[0], F1[1]] + F1[44:48], newest=True), V[3], 'n', 60e6, 2)]
F2 = take(8); SHIP2 = dict(zip(F2, ['Hecate', 'Hecate', 'Hecate', 'Sabre', 'Sabre', 'Svipul', 'Svipul', 'Stiletto']))
K2 = [kill([(c, SHIP2[c]) for c in F2[:6]], V[4], 'h', 55e6, 5), kill([(c, SHIP2[c]) for c in F2[2:8]], V[5], 'n', 38e6, 11),
      kill([(c, SHIP2[c]) for c in F2[0:3] + F2[6:8]], V[6], 'n', 22e6, 14)]
H = take(1)
K3 = [kill([(H[0], 'Loki')], V[7], 'n', 310e6, 3), kill([(H[0], 'Loki')], V[8], 'f', 140e6, 16)]
S1, S2 = take(3), take(2)
K4 = [kill([(c, 'Tengu') for c in S1], V[9], 'n', 900e6, 6), kill([(c, 'Raven') for c in S2], V[10], 'n', 250e6, 18)]
BATTLE = K1 + K2 + K3 + K4

# ---- the counts, worked out here (ships: category 6 and not a capsule; the Astrahus is a structure, the Capsule a capsule)
NOT_SHIP = {T['Capsule'], T['Astrahus']}
CLS = {'Ferox': 'Combat Battlecruiser', 'Muninn': 'Heavy Assault Cruiser', 'Basilisk': 'Logistics', 'Scimitar': 'Logistics', 'Huginn': 'Combat Recon Ship',
       'Lachesis': 'Combat Recon Ship', 'Sabre': 'Interdictor', 'Drake': 'Combat Battlecruiser', 'Hurricane': 'Combat Battlecruiser', 'Kikimora': 'Destroyer',
       'Stiletto': 'Interceptor', 'Hecate': 'Tactical Destroyer', 'Svipul': 'Tactical Destroyer', 'Loki': 'Strategic Cruiser'}   # the SDE's group names
NAME = {v: k for k, v in T.items() if k in CLS or k in ('Capsule', 'Astrahus')}
def hulls(kills):
    ship = {}
    for k in sorted(kills, key=lambda k: -k['t']):   # newest first: a pilot's ship on their newest kill here
        for a in k['km']['attackers']:
            if a.get('character_id') and a['character_id'] not in ship: ship[a['character_id']] = a['ship_type_id']
    n = {}
    for t in ship.values():
        if t not in NOT_SHIP: n[t] = n.get(t, 0) + 1
    lst = sorted(((NAME[t], c) for t, c in n.items()), key=lambda x: (-x[1], x[0]))
    return lst, sum(c for _, c in lst), len(ship)
EXP = [hulls(K1), hulls(K2), hulls(K3)]

OPEN = """([P, from_]) => { P = P.slice().sort((a, b) => b.t - a.t); for(const p of P){ const w = IT_KILL_WORD[p.v]; p.word = [w[0], w[1]]; }
  if(from_ === 'dossier') fkOpen(P[0].id, P[0].hash, 90000001, null, {km: P[0].km}); else fkOpen(P[0].id, P[0].hash, null, null, {from: 'intel', km: P[0].km, picks: P}); return P[0].id; }"""
STRIPS = """() => [...document.querySelectorAll('#fleetPanel button.fk-kg-h')].map(h => { const s = h.querySelector('.fk-kg-hulls');
  return {t: h.querySelector('.fk-kg-t').textContent, m: h.querySelector('.fk-kg-m').textContent, open: h.getAttribute('aria-expanded'), here: !!h.querySelector('.fk-kg-here'),
    age: (h.querySelector('.fk-kg-a') || {}).textContent || '', title: h.title,
    shown: s ? [...s.querySelectorAll('.fk-kg-hl')].filter(x => x.getClientRects().length).map(x => [x.querySelector('img').alt, x.querySelector('b').textContent]) : null,
    more: s ? ([...s.querySelectorAll('.fk-kg-more')].find(x => x.getClientRects().length) || {textContent: ''}).textContent : null,
    tip: s ? s.title : null, inner: s ? s.querySelectorAll('button, a, input, select, [tabindex]').length + (s.matches('button, a, [tabindex]') ? 1 : 0) : 0,
    h: Math.round(h.getBoundingClientRect().height)}; })"""
GEOM = """(key) => { const h = document.querySelector(`#fleetPanel [data-fk-kg="${key}"]`), s = h.querySelector('.fk-kg-hulls'), t = h.querySelector('.fk-kg-t');
  const r = (e) => { const b = e.getBoundingClientRect(); return [b.left, b.top, b.right, b.bottom]; }; return [r(h), s && s.getClientRects().length ? r(s) : null, r(t)]; }"""
def strip_want(lst, n):
    shown = [[nm, f'×{c}'] for nm, c in lst[:n]]
    return shown, (f'+{len(lst) - n} more' if len(lst) > n else '')

with sync_playwright() as p:
    b = p.chromium.launch()
    errs, zk = [], []
    def new_ctx(w, phone=False):
        kw = dict(viewport={'width': w, 'height': 1000})
        if phone: kw = dict(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, device_scale_factor=2)
        ctx = b.new_context(bypass_csp=True, **kw); ctx.on('page', lambda pg: pg.on('pageerror', lambda e: errs.append(str(e))))
        ctx.on('request', lambda r: zk.append(r.url) if 'zkillboard.com' in r.url else None)
        M.route(ctx); return ctx
    # ---- types held back: nothing first, then the strip, the focus kept
    ctx = b.new_context(bypass_csp=True, viewport={'width': 1440, 'height': 1000}); ctx.on('page', lambda pg: pg.on('pageerror', lambda e: errs.append(str(e)))); M.route(ctx)
    pg = ctx.new_page(); pg.goto('file://' + HTML); pg.wait_for_timeout(600)
    pg.evaluate("""() => { const f = window.fetch; window.__hold = true; window.fetch = function(u){ if(window.__hold && /\\/universe\\/(types|groups)\\//.test(String(u))) return new Promise(r => setTimeout(() => r(f.apply(this, arguments)), 2500)); return f.apply(this, arguments); }; }""")
    pg.evaluate(OPEN, [BATTLE, 'intel']); pg.wait_for_timeout(500)
    pg.focus('#fleetPanel [data-fk-kg="f0"]')
    early = pg.evaluate(STRIPS); spin = pg.evaluate("() => !!document.querySelector('#fleetPanel .fk-kg-h .busy-spin')")
    late = None
    for _ in range(40):   # types, then groups, each held 2.5 s
        pg.wait_for_timeout(250); late = pg.evaluate(STRIPS)
        if late[0]['shown']: break
    fo = pg.evaluate("() => document.activeElement && document.activeElement.dataset.fkKg")
    check(all(s['shown'] is None for s in early) and not spin and late[0]['shown'] and fo == 'f0',
          f'the hulls\' types still being looked up: no strip and no spinner; then the strip, the focus still on Fleet 1 ({[s["shown"] is None for s in early]} -> {bool(late[0]["shown"])}, focus {fo})')
    ctx.close()
    # ---- the battle at 1440
    ctx = new_ctx(1440); pg = ctx.new_page(); pg.goto('file://' + HTML); pg.wait_for_timeout(600)
    pg.evaluate(OPEN, [BATTLE, 'intel']); pg.wait_for_timeout(3000)
    S = pg.evaluate(STRIPS)
    check([s['t'] for s in S] == ['Fleet 1', 'Fleet 2', 'Fleet 3', 'Not linked'], f'(the battle: 3 fleets and Not linked) {[s["t"] for s in S]}')
    for i, (lst, ships, pilots) in enumerate(EXP):
        shown, more = strip_want(lst, 4)
        check(S[i]['shown'] == shown and S[i]['more'] == more, f'{S[i]["t"]}: the hulls by count then name, the first 4 shown, "{more or "no more"}"\n      page {S[i]["shown"]} {S[i]["more"]!r}\n      want {shown} {more!r}')
        lines = (S[i]['tip'] or '').split('\n')
        want = [f'{nm} ({CLS[nm]}) ×{c}' for nm, c in lst] + [f'{ships} of {pilots} pilot{"" if pilots == 1 else "s"} in ships. Hulls: each pilot once, in the ship from their newest kill in the fleet; pods, NPCs and structures left out.']
        check(lines == want, f'{S[i]["t"]}: the hover lists every hull with its class and count, then "{ships} of {pilots} ..."\n      page {lines}\n      want {want}')
    check(EXP[0][1:] == (45, 48) and ('Muninn', 7) in EXP[0][0] and ('Ferox', 19) in EXP[0][0] and any(a.get('character_id') == RESHIP and a['ship_type_id'] == T['Ferox'] for a in K1[2]['km']['attackers']), f'(worked out here: Fleet 1 45 of 48 in ships, Ferox 19, Muninn 7 with the reshipped pilot) {EXP[0]}')
    check(S[3]['shown'] is None and S[3]['tip'] is None, 'Not linked: no hulls')
    check(all(s['inner'] == 0 for s in S[:3]) and pg.evaluate("() => document.querySelectorAll('#fleetPanel button.fk-kg-h button').length") == 0,
          'the strip is part of the heading: nothing inside it can be pressed, no button in the button')
    pg.click('#fleetPanel [data-fk-kg="f1"] .fk-kg-hulls'); pg.wait_for_timeout(300); o1 = pg.evaluate(STRIPS)[1]['open']
    pg.click('#fleetPanel [data-fk-kg="f1"] .fk-kg-hulls'); pg.wait_for_timeout(300); o2 = pg.evaluate(STRIPS)[1]['open']
    check(o1 == 'true' and o2 == 'false', f'pressing the hulls opens and closes the fleet, as anywhere on its heading ({o1}, {o2})')
    check('The pilots on this one kill' not in S[0]['title'] and 'Hulls: each pilot once' in S[0]['title'] and 'Hulls:' not in S[3]['title'], 'the heading\'s hover: the grouping rule and the hull rule (not on Not linked)')
    ctx.close()
    # ---- widths
    for w, own in ((1440, False), (1100, False), (1024, True), (900, True)):
        ctx = new_ctx(w); pg = ctx.new_page(); pg.goto('file://' + HTML); pg.wait_for_timeout(500)
        pg.evaluate(OPEN, [BATTLE, 'intel']); pg.wait_for_timeout(2500)
        S = pg.evaluate(STRIPS); h, s, t = pg.evaluate(GEOM, 'f0')
        ok = S[0]['shown'] == strip_want(EXP[0][0], 4)[0] and s and s[0] >= h[0] and s[2] <= h[2] + 0.5 and s[3] <= h[3] + 0.5
        if own: ok = ok and s[1] >= t[3] - 1 and S[0]['h'] > 40
        else: ok = ok and S[0]['h'] <= 36 and s[1] < t[3]
        check(ok and pg.evaluate('document.documentElement.scrollWidth') <= w, f'{w} px: ' + ('the hulls on their own line under the heading, all 4, inside it' if own else 'one line') + f' (heading {S[0]["h"]} px) {S[0]["shown"]}')
        ctx.close()
    # ---- a phone
    ctx = new_ctx(0, phone=True); pg = ctx.new_page(); pg.goto('file://' + HTML); pg.wait_for_timeout(500)
    pg.evaluate(OPEN, [BATTLE, 'intel']); pg.wait_for_timeout(2500)
    S0 = pg.evaluate(STRIPS); vis0 = pg.evaluate("() => [...document.querySelectorAll('#fleetPanel .fk-kg-hulls')].map(s => s.getClientRects().length)")
    pg.click('#fleetPanel [data-fk-kg="f0"]'); pg.wait_for_timeout(500)
    S1 = pg.evaluate(STRIPS); h, s, t = pg.evaluate(GEOM, 'f0')
    check(all(v == 0 for v in vis0) and all(x['h'] <= 46 for x in S0) and S1[0]['shown'] == strip_want(EXP[0][0], 3)[0] and S1[0]['more'] == '+8 more' and s and s[1] >= t[3] - 1 and pg.evaluate('document.documentElement.scrollWidth') <= 390,
          f'a phone: closed headings one line, no hulls; Fleet 1 opened: 3 hulls and "+8 more" on their own line; nothing off the page {S1[0]["shown"]} {S1[0]["more"]!r}')
    ctx.close()
    # ---- one Intel kill: a gang, a solo pilot, NPCs only; and from a Pilot Dossier
    ctx = new_ctx(1440); pg = ctx.new_page(); pg.goto('file://' + HTML); pg.wait_for_timeout(600)
    LINE = "() => (document.querySelector('#fleetPanel .fk-pk-h') || {}).textContent || ''"
    pg.evaluate(OPEN, [[K2[0]], 'intel']); pg.wait_for_timeout(2500)
    S = pg.evaluate(STRIPS); line = pg.evaluate(LINE); rows = pg.evaluate("() => [...document.querySelectorAll('#fleetPanel .fk-pk')].map(b => b.getAttribute('aria-pressed'))")
    lst, ships, pilots = hulls([K2[0]])
    check(line == '1 kill in Amamake from Intel · as it was when you opened this' and len(S) == 1 and S[0]['t'] == 'Fleet 1' and S[0]['m'] == '6 pilots · 1 kill' and S[0]['open'] == 'true' and S[0]['here']
          and S[0]['shown'] == strip_want(lst, 4)[0] and re.fullmatch(r'\d+ min ago', S[0]['age']) and rows == ['true'] and 'The pilots on this one kill' in S[0]['title'],
          f'one Intel kill by a gang: the kill list, "1 kill in Amamake from Intel", its Fleet 1 open and "analyzing", "6 pilots · 1 kill", its hulls, the age without "newest", the kill pressed\n      {line!r} {[(s["t"], s["m"], s["open"], s["here"], s["shown"], s["age"], s["title"]) for s in S]} {rows} want hulls {strip_want(lst, 4)[0]}')
    pg.evaluate(OPEN, [[K3[0]], 'intel']); pg.wait_for_timeout(2000)
    S = pg.evaluate(STRIPS)
    check(len(S) == 1 and S[0]['m'] == 'solo · 1 kill' and S[0]['shown'] == [['Loki', '×1']] and S[0]['more'] == '', f'one solo kill: "solo · 1 kill", its one hull {[(s["m"], s["shown"]) for s in S]}')
    npc = json.loads(json.dumps(K3[0])); npc['id'] += 7; npc['ships'] = 0
    npc['km']['attackers'] = [{'faction_id': 500001, 'ship_type_id': a['ship_type_id'], 'damage_done': 100, 'final_blow': a['final_blow'], 'security_status': 0} for a in npc['km']['attackers']]
    pg.evaluate(OPEN, [[npc], 'intel']); pg.wait_for_timeout(2000)
    S = pg.evaluate(STRIPS)
    check(len(S) == 1 and S[0]['m'] == 'NPCs · 1 kill' and S[0]['shown'] is None, f'one kill with no player on it: "NPCs · 1 kill", no hulls {[(s["m"], s["shown"]) for s in S]}')
    pg.evaluate(OPEN, [[K2[0]], 'dossier']); pg.wait_for_timeout(2000)
    check(pg.evaluate(LINE) == '' and not pg.evaluate(STRIPS) and pg.evaluate('fk.from') == 'dossier', 'the same kill opened from a Pilot Dossier: no kill list, as before')
    ctx.close()
    check(not zk, f'no request to zKillboard {zk[:3]}')
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
