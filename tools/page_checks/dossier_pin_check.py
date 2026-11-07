"""The Pilot Dossier always shows the hull asked for, first; "Show N more hulls" shows the rest (v2026.11.01.5).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/dossier_pin_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner (backlog bug "Pilot Dossier hides the hull they flew on the kill"): "if the ship the pilot flew on the killmail
isn't in their top 15 or whatever, the user wont see that hull in their list. we need to be able to see the reset of the
hulls". His picks in Claude outputs/dossier_hull_from_kill_mockup.html: A pinned first, all at once, C1 the kill added,
typed hulls pinned too. The real page with ESI and zKillboard answered from sa_mocks.py plus made-up pilots here:
"Wren Manyhull" flew 23 hulls in her newest 47 kills and 2 losses (the Ferox, 1 kill, is 13th), "Nell Freshling" has
nothing on zKillboard yet. Every expected row is worked out again here, in Python, from the mock:
  * from a kill on the Fleet tab (Wren in the Ferox): the Ferox row first, selected, tagged "On this kill" and
    "13th of 23 hulls"; the 8 busiest follow (the Ferox not repeated); "Show 14 more hulls" draws all 23, "Show fewer"
    folds them back, the button keeps focus; the Solo switch keeps the Ferox first ("0 of 1", "no solo kills in it");
  * a kill zKillboard's list for her doesn't have yet (Wren in a Kikimora): that killmail is added, the Kikimora row first
    with its real numbers (1 kill, usually 4), "not yet in zKillboard's list for them: added", the header "newest 47 kills
    + this one", All 48; the kill under the row opens that fleet on the Fleet tab;
  * a kill she lost (the victim's button): her Curse row first, "Lost on this kill" with its rank; nothing added;
  * a pilot with nothing on zKillboard (Nell, from the Fleet tab): her dossier from that kill alone, no PILOT-03;
  * a hull typed in that isn't among those read (Kikimora): a row of its own, first, "Asked for", "not in their newest 47
    kills or 2 losses", 0 kills, no ▾, Last "—", not counted among her 23 hulls; a typed hull that is (Ferox): "Asked for", "13th of 23 hulls";
  * no hull asked for: no tag, the 8 busiest and "Show 15 more hulls";
  * at 390 px nothing runs off the page; no page errors.
v2026.11.01.4 fails (no row for the Ferox, a grey "N more hulls with fewer" line, the Kikimora kill not counted).
"""
import sys, os, re, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from playwright.sync_api import sync_playwright
import sa_mocks as M
byname = M.byname

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok

# ---- made-up pilots and kills (names invented; IDs outside the other checks' ranges)
WREN, NELL = 92000101, 92000102
M.PILOTS[WREN] = ('Wren Manyhull', 98000042); M.NAME_ID['wren manyhull'] = WREN
M.PILOTS[NELL] = ('Nell Freshling', 98000042); M.NAME_ID['nell freshling'] = NELL
MATES = M.BIG_PILOTS
def kill(attackers, victim='Rifter', days=1.0):
    M._kid[0] += 1; k = M._kid[0]
    M.KM[k] = {'killmail_id': k, 'killmail_time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - days * 86400)), 'solar_system_id': 30004759,
               'victim': {'character_id': M.pick(98000013), 'corporation_id': 98000013, 'ship_type_id': byname[victim], 'damage_taken': 5000, 'items': [], 'position': {'x': 0, 'y': 0, 'z': 0}},
               'attackers': [dict(M.aff(c), final_blow=i == 0, damage_done=100, security_status=0, ship_type_id=byname[h], weapon_type_id=byname['125mm Gatling AutoCannon II']) for i, (c, h) in enumerate(attackers)]}
    M.H[k] = M.hashlib.sha1(str(k).encode()).hexdigest(); M.VALUE[k] = 40e6; return k
SPEC = [('Sabre', 6), ('Hurricane', 5), ('Stabber', 4), ('Rifter', 4), ('Svipul', 3), ('Hound', 3), ('Vagabond', 3), ('Loki', 2), ('Claw', 2), ('Thrasher', 2),
        ('Broadsword', 2), ('Muninn', 2), ('Huginn', 1), ('Jaguar', 1), ('Wolf', 1), ('Scythe', 1), ('Bellicose', 1), ('Breacher', 1), ('Talwar', 1), ('Probe', 1)]
EXP = {}   # hull -> {'k': [(players, days)], 'l': [days]}
WK, j = [], 0
for hull, n in SPEC:
    for c in range(n):
        j += 1; players = 1 + (j % 3) * 2; days = 1 + j * 0.7   # 1, 3 or 5 players
        WK.append(kill([(WREN, hull)] + [(MATES[i], 'Rifter') for i in range(players - 1)], days=days)); EXP.setdefault(hull, {'k': [], 'l': []})['k'].append((players, days))
FK = kill([(WREN, 'Ferox')] + [(MATES[i], 'Rifter') for i in range(13)], 'Megathron', 0.02)   # the fleet kill: 14 players, newest
EXP['Ferox'] = {'k': [(14, 0.02)], 'l': []}
WL = [M._loss(WREN, 'Curse', 9.5), M._loss(WREN, 'Vedmak', 12.5)]
EXP['Curse'] = {'k': [], 'l': [9.5]}; EXP['Vedmak'] = {'k': [], 'l': [12.5]}
M.HIST[WREN] = {'kills': WK + [FK], 'losses': WL}
FK2 = kill([(WREN, 'Kikimora'), (MATES[0], 'Rifter'), (MATES[1], 'Rifter'), (MATES[2], 'Rifter')], 'Caracal', 0.01)   # not in her zKillboard list yet
FK3 = M._loss(WREN, 'Curse', 0.01)   # she lost a Curse minutes ago (not in her list yet)
FK4 = kill([(NELL, 'Rifter'), (MATES[3], 'Rifter')], 'Heron', 0.01)   # Nell has nothing on zKillboard
NK, NL = len(WK) + 1, len(WL)
size = lambda n: 'solo' if n <= 1 else 'small' if n <= 10 else 'fleet'
def order(mode='all'):
    rows = []
    for h, e in EXP.items():
        ks = [k for k in e['k'] if mode == 'all' or size(k[0]) == mode]
        if mode != 'all' and not ks: continue
        last = min([k[1] for k in e['k']] + e['l'])
        rows.append((-(len(e['k']) + len(e['l']) if mode == 'all' else len(ks)), last, h))
    return [h for _, _, h in sorted(rows)]
ALL = order()
ORD = lambda n: f"{n}{'th' if 11 <= n % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"
FEROX_RANK = ALL.index('Ferox') + 1
CURSE_RANK = ALL.index('Curse') + 1

ROWS = """() => [...document.querySelectorAll('#pilotDossier button.pd-row')].map(b => ({hull: b.querySelector('.pd-hull .nm').firstChild.textContent,
  k: b.querySelector('.pd-n.k').textContent, gang: b.querySelector('.pd-gang > span:last-child').textContent, last: b.querySelector('.pd-last').textContent,
  sel: b.getAttribute('aria-pressed') === 'true', tag: (b.querySelector('.pd-pin .pd-tag') || {}).textContent || null,
  where: (b.querySelector('.pd-pin .pd-pin-r') || {}).textContent || null, exp: !!b.parentElement.querySelector('[data-pd-exp]')}))"""
MORE = "() => { const m = document.querySelector('#pilotDossier .pd-more'); const b = m && m.querySelector('button'); return m ? [b ? b.textContent : null, b ? b.getAttribute('aria-expanded') : null, m.textContent.replace(b ? b.textContent : '', '').trim()] : null; }"
CTX = "() => document.querySelector('#pilotDossier .pd-head .ctx').textContent"
def idle(pg):
    pg.wait_for_function("() => !document.querySelector('#fitBtn').disabled && document.querySelector('#pilotBusy').hidden", timeout=120000); pg.wait_for_timeout(400)
def analyze(pg, name, ship=''):
    pg.click('#tabBtnPilot'); pg.fill('#pilotName', name); pg.fill('#manualShip', ship); pg.click('#fitBtn'); pg.wait_for_timeout(300); idle(pg)
def from_fleet(pg, kid, name, victim=False):
    pg.evaluate("([k, h]) => fkOpen(k, h, null)", [kid, M.H[kid]])
    sel = '.fk-vbtn' if victim else f'#fleetPanel [data-fk-pilot="{name}"]:not(.fk-vbtn)'
    pg.wait_for_selector(sel, timeout=60000); pg.wait_for_timeout(300)
    pg.click(sel); pg.wait_for_timeout(300); idle(pg)

with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []
    def new_ctx(w):
        ctx = b.new_context(bypass_csp=True, viewport={'width': w, 'height': 1000}); ctx.on('page', lambda pg: pg.on('pageerror', lambda e: errs.append(str(e)))); M.route(ctx); return ctx
    ctx = new_ctx(1480)
    pg = ctx.new_page(); pg.goto('file://' + HTML); pg.wait_for_timeout(500)
    if not pg.query_selector('#fleetPanel'):
        check(False, 'the Fleet tab\'s panel is #fleetPanel (update this check)')
    # 1. from the Fleet tab, Wren in the Ferox (13th of 23)
    name = M.PILOTS[WREN][0]
    from_fleet(pg, FK, name)
    r = pg.evaluate(ROWS); mo = pg.evaluate(MORE); ctxt = pg.evaluate(CTX)
    want_rest = [h for h in ALL if h != 'Ferox'][:8]
    check(len(ALL) == 23 and FEROX_RANK > 8, f'(the mock: 23 hulls, the Ferox {FEROX_RANK}th)')
    check(r and r[0]['hull'] == 'Ferox' and r[0]['sel'] and r[0]['tag'] == 'On this kill' and r[0]['where'] == f'{ORD(FEROX_RANK)} of 23 hulls',
          f'from a kill on the Fleet tab: the hull she flew on it first, selected, "On this kill · {ORD(FEROX_RANK)} of 23 hulls" {r[:1]}')
    check([x['hull'] for x in r[1:]] == want_rest and not any(x['tag'] for x in r[1:]), f'the 8 busiest follow, the Ferox not repeated\n      page {[x["hull"] for x in r[1:]]}\n      want {want_rest}')
    check(mo == ['Show 14 more hulls', 'false', 'with fewer kills and losses'] and ctxt.startswith(f'newest {NK} kills, {NL} losses'), f'"Show 14 more hulls" under them; the header unchanged {mo} {ctxt!r}')
    st = pg.inner_text('#fitStatus')
    check('Ferox' in st, f'the Ferox is what\'s shown under the dossier ({st!r})')
    pg.click('#pilotDossier [data-pd-allhulls]'); pg.wait_for_timeout(200)
    r2 = pg.evaluate(ROWS); mo2 = pg.evaluate(MORE); foc = pg.evaluate("() => document.activeElement && document.activeElement.dataset.pdAllhulls")
    check([x['hull'] for x in r2] == ['Ferox'] + [h for h in ALL if h != 'Ferox'] and mo2 == ['Show fewer', 'true', f'all 23 hulls in their newest {NK} kills and {NL} losses'] and foc == '0',
          f'Show 14 more hulls: all 23 (the Ferox still first), "Show fewer", the button keeps focus {len(r2)} {mo2} {foc}')
    pg.click('#pilotDossier [data-pd-allhulls]'); pg.wait_for_timeout(200)
    r3 = pg.evaluate(ROWS); mo3 = pg.evaluate(MORE)
    check(len(r3) == 9 and mo3 and mo3[0] == 'Show 14 more hulls', f'Show fewer: back to 9 rows {len(r3)} {mo3}')
    pg.click('#pilotDossier [data-pd-mode="solo"]'); pg.wait_for_timeout(200)
    r4 = pg.evaluate(ROWS); solo = order('solo')
    check(r4[0]['hull'] == 'Ferox' and r4[0]['k'] == '0 of 1' and r4[0]['where'] == 'no solo kills in it' and r4[0]['sel'] and [x['hull'] for x in r4[1:]] == solo[:8],
          f'Solo: the Ferox still first ("0 of 1", "no solo kills in it"), then the solo busiest {r4[:1]} {[x["hull"] for x in r4[1:]]} (want {solo[:8]})')
    pg.click('#pilotDossier [data-pd-mode="all"]'); pg.wait_for_timeout(200)
    # 2. a kill not in her zKillboard list yet: added
    from_fleet(pg, FK2, name)
    r = pg.evaluate(ROWS); ctxt = pg.evaluate(CTX); seg = pg.evaluate("() => document.querySelector('#pilotDossier [data-pd-mode=all] b').textContent")
    check(r[0]['hull'] == 'Kikimora' and r[0]['k'] == '1' and r[0]['gang'] == 'usually 4' and r[0]['tag'] == 'On this kill' and r[0]['where'] == 'not yet in zKillboard’s list for them: added' and r[0]['sel'],
          f'a kill zKillboard\'s list doesn\'t have yet: added, its hull first with its real numbers {r[:1]}')
    check(ctxt.startswith(f'newest {NK} kills + this one, {NL} losses') and seg == str(NK + 1), f'the header says + this one; All counts it ({ctxt!r}, {seg})')
    pg.click(f'#pilotDossier [data-pd-exp="{byname["Kikimora"]}"]'); pg.wait_for_timeout(300)
    pdk = pg.evaluate("() => [...document.querySelectorAll('#pilotDossier .pd-kills .pdk[data-pdk]')].map(x => Number(x.dataset.pdk))")
    check(pdk == [FK2], f'its kill under the row {pdk}')
    pg.evaluate("() => { window.__fkCalls = []; const f = fkOpen; window.fkOpen = function(...a){ window.__fkCalls.push([a[0], a[1]]); return f.apply(this, a); }; }")
    pg.click(f'#pilotDossier [data-pd-fleet="{FK2}"]'); pg.wait_for_timeout(600)
    fid = pg.evaluate("() => [window.__fkCalls, fk.killId, getComputedStyle(document.querySelector('#tabFleet')).display]")
    check(fid[0] == [[FK2, M.H[FK2]]] and fid[1] == FK2 and fid[2] != 'none', f'its fleet icon opens that kill (its hash from the Fleet tab) on the Fleet tab {fid}')
    # 3. a kill she lost: the victim's button
    from_fleet(pg, FK3, name, victim=True)
    r = pg.evaluate(ROWS); ctxt = pg.evaluate(CTX)
    check(r[0]['hull'] == 'Curse' and r[0]['tag'] == 'Lost on this kill' and r[0]['where'] == f'{ORD(CURSE_RANK)} of 23 hulls' and r[0]['sel'] and '+ this one' not in ctxt,
          f'a kill she lost: her Curse first, "Lost on this kill · {ORD(CURSE_RANK)} of 23 hulls", nothing added {r[:1]} {ctxt!r}')
    # 4. nothing on zKillboard yet
    from_fleet(pg, FK4, M.PILOTS[NELL][0])
    r = pg.evaluate(ROWS); st = pg.inner_text('#fitStatus'); hid = pg.evaluate("() => document.querySelector('#pilotDossier').hidden")
    ctxt = pg.evaluate(CTX) if not hid else ''
    check(not hid and 'PILOT-03' not in st and [x['hull'] for x in r] == ['Rifter'] and r[0]['k'] == '1' and r[0]['tag'] == 'On this kill' and ctxt.startswith('newest 0 kills + this one, 0 losses'),
          f'a pilot with nothing on zKillboard yet: her dossier from that kill, no PILOT-03 {r} {ctxt!r} {st!r}')
    # 5. a hull typed in that isn't among those read
    analyze(pg, name, 'Kikimora')
    r = pg.evaluate(ROWS); mo = pg.evaluate(MORE); seg = pg.evaluate("() => document.querySelector('#pilotDossier [data-pd-mode=all] b').textContent")
    check(r and r[0]['hull'] == 'Kikimora' and r[0]['tag'] == 'Asked for' and r[0]['where'] == f'not in their newest {NK} kills or {NL} losses' and r[0]['k'] == '0' and not r[0]['exp'] and r[0]['last'] == '—' and r[0]['sel'],
          f'a typed hull not among those read: a row of its own, first, "Asked for", no numbers, no ▾ {r[:1]}')
    check([x['hull'] for x in r[1:]] == ALL[:8] and mo and mo[0] == 'Show 15 more hulls' and seg == str(NK), f'it isn\'t counted: the 8 busiest, "Show 15 more hulls", All {NK} ({mo}, {seg})')
    pg.click('#pilotDossier [data-pd-allhulls]'); pg.wait_for_timeout(200)
    r2 = pg.evaluate(ROWS); mo2 = pg.evaluate(MORE)
    check(len(r2) == 24 and r2[0]['hull'] == 'Kikimora' and mo2 and mo2[2] == f'all 23 hulls in their newest {NK} kills and {NL} losses', f'opened: hers 23 + the one asked for, "all 23 hulls" {len(r2)} {mo2}')
    # 6. a typed hull that is
    analyze(pg, name, 'Ferox')
    r = pg.evaluate(ROWS)
    check(r[0]['hull'] == 'Ferox' and r[0]['tag'] == 'Asked for' and r[0]['where'] == f'{ORD(FEROX_RANK)} of 23 hulls' and r[0]['sel'], f'a typed hull among those read: first, "Asked for", its rank {r[:1]}')
    # 7. no hull asked for
    analyze(pg, name)
    r = pg.evaluate(ROWS); mo = pg.evaluate(MORE)
    check([x['hull'] for x in r] == ALL[:8] and not any(x['tag'] for x in r) and mo and mo[0] == 'Show 15 more hulls' and r[0]['sel'], f'no hull asked for: the 8 busiest, no tag, the busiest selected, "Show 15 more hulls" {[x["hull"] for x in r]} {mo}')
    ctx.close()
    # phone
    ctx = new_ctx(390); pg = ctx.new_page(); pg.goto('file://' + HTML); pg.wait_for_timeout(500)
    from_fleet(pg, FK, name)
    pg.click('#pilotDossier [data-pd-allhulls]'); pg.wait_for_timeout(200)
    over = pg.evaluate("() => [document.documentElement.scrollWidth, [...document.querySelectorAll('#pilotDossier *')].filter(e => { const r = e.getBoundingClientRect(); return e.checkVisibility() && r.width && (r.right > innerWidth + 1 || r.left < -1); }).map(e => e.className || e.tagName).slice(0, 5)]")
    first = pg.evaluate("() => { const t = document.querySelector('#pilotDossier .pd-pin'); const b = document.querySelector('#pilotDossier [data-pd-allhulls]'); return [!!t && t.checkVisibility(), b ? b.getBoundingClientRect().height : 0]; }")
    check(over[0] <= 390 and not over[1] and first[0] and first[1] >= 40, f'390 px: the tag shown, nothing runs off the page, the button 40 px tall {over} {first}')
    ctx.close()
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
