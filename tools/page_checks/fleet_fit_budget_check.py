"""The Fleet tab's fits load on request, with common fits for big fleets (v2026.11.02.1; Project doc roadmap/fleet-fit-budget-plan.md).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/fleet_fit_budget_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner: "figure out how we can best avoid hitting our 10 minute cap on zkill requests when dealing with fleets this large";
"what if we didn't automatically load the fits? default to ship type/weapon and damage on the kill"; "a column added to the far
right that has a Load All button/link and the rows have a Load button/link"; "give an option to use common fits for large fleets";
"anything above small gang should prob go into the common/alliance fits default"; "25 seems like a good starting point"; the damage
in its own column beside the ship (his screenshot); rows stay put until all load. Made-up killmails only (sa_mocks.py's invented
pilots and alliances), ESI and zKillboard answered by stand-ins that count every zKillboard request; never the real zKillboard.
A 48-pilot kill: 7 alliance-and-hull pairs (Crimson Tide's Curse and Vedmak, Void Runners' Loki, Random Third Party's Loki,
Northern Pact's Rifter, Quiet Harbor's Curse, a corporation's Sabre) and 2 pilots of an NPC corporation. Checks:
  * open: no zKillboard request; every row unloaded, with the damage it did on the kill in its own column beside the ship (and the
    final blow), sorted by that damage; the summary shows what's free (48 pilots, the hulls, the damage) and asks for Load all;
    no button inside a button;
  * Load all, common fits (the default above 10): the label says 7 requests and 100 left; pressing makes exactly the 7 pair
    lookups; the 5 pilots who are victims in those lists get their own fit (found in alliance losses), the rest their alliance's,
    lists with no loss and the NPC-corporation pilots unknown, those two with own?; the summary's fits line says so; once all are
    in the rows sort by DPS; own? makes exactly 1 request;
  * kept fits: a reload within the hour reopens the fleet with no request and the same fits; an hour later they're unloaded again;
    Refresh losses still asks;
  * the reserve: with 70 of the 100 already spent, Load all stops at exactly 75 with the countdown and the button disabled; a
    row's Load still asks (76); when the oldest stamps age out it carries on by itself and finishes, with no ZKB-04;
  * own fits (the default up to 10; 11 is common, and the choice can be changed): "N requests, up to M", and pressing makes no
    more than M, N for the pilots;
  * a share link: its fits load with no zKillboard request, the pilots it doesn't carry stay unloaded;
  * a row still opens the Pilot Analyzer, its Load doesn't; the focus stays on a row through redraws;
  * 390 px: nothing off the page, Load and Load all 44 px; no page errors.
v2026.11.01.8 fails (the fleet is looked up on open, 15 at a time).
"""
import sys, os, re, json, time, hashlib
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
crts = M._crts; void = M._void
npact = [i for i, v in M.PILOTS.items() if v[1] in (98000007, 98000008)]
qhc = [i for i, v in M.PILOTS.items() if v[1] == 98000012]
tpi = [i for i, v in M.PILOTS.items() if v[1] == 98000030]
npc = [i for i, v in M.PILOTS.items() if v[1] == 1000167]
PAIRS = [   # (pilots, hull); the first ones of the first four are victims in their alliance's list (FLEET_LOSSES)
    ([crts[0], crts[1]] + crts[11:21], 'Curse'), ([crts[7]] + crts[21:26], 'Vedmak'), ([void[0]] + void[3:12], 'Loki'),
    ([M.THIRD_PILOT, M.ANNEX_PILOT, M.LONG_PILOT], 'Loki'), (npact[2:10], 'Rifter'), (qhc[:5], 'Curse'), (tpi[:2], 'Sabre')]
FOUND = {crts[0], crts[1], crts[7], void[0], M.THIRD_PILOT}
NPC = npc[:2]
_k = [9800000]
def kill(members, victim='Megathron'):   # members: [(id, hull)]; damage falls with the order given, a few ties; the 4th lands the final blow
    _k[0] += 1; k = _k[0]
    att = []
    for i, (cid, hull) in enumerate(members):
        att.append(dict(M.aff(cid), ship_type_id=B[hull], weapon_type_id=B['Acolyte II'], damage_done=9000 - 150 * (i // 2) if i % 7 else 300 + i, final_blow=i == 3, security_status=0))
    att.append({'faction_id': 500001, 'ship_type_id': B['Rifter'], 'damage_done': 7, 'final_blow': False, 'security_status': 0})
    M.KM[k] = {'killmail_id': k, 'killmail_time': M._diso(1, 20), 'solar_system_id': 30004759, 'attackers': att,
               'victim': {'character_id': M.pick(98000013), 'corporation_id': 98000013, 'ship_type_id': B[victim], 'damage_taken': sum(a['damage_done'] for a in att), 'items': [], 'position': {'x': 0, 'y': 0, 'z': 0}}}
    M.H[k] = hashlib.sha1(str(k).encode()).hexdigest(); return k
BIG = [(c, h) for ps, h in PAIRS for c in ps] + [(c, 'Ferox') for c in NPC]
assert len(BIG) == 48, len(BIG)
BIGK = kill(BIG)
TEN = [(c, 'Curse') for c in crts[11:15]] + [(c, 'Rifter') for c in npact[2:6]] + [(c, 'Ferox') for c in NPC]
TENK = kill(TEN, 'Thanatos')
ELEVENK = kill(TEN + [(qhc[0], 'Curse')], 'Thanatos')
DMG = {a['character_id']: a['damage_done'] for a in M.KM[BIGK]['attackers'] if a.get('character_id')}
FB = next(a['character_id'] for a in M.KM[BIGK]['attackers'] if a.get('final_blow'))
TOT = M.KM[BIGK]['victim']['damage_taken']
PAIR_URLS = {f"losses/allianceID/{M.ORGS[M.PILOTS[ps[0]][1]][3]}/shipTypeID/{B[h]}/" if M.ORGS[M.PILOTS[ps[0]][1]][3] else f"losses/corporationID/{M.PILOTS[ps[0]][1]}/shipTypeID/{B[h]}/" for ps, h in PAIRS}
assert len(PAIR_URLS) == 7
NAME = lambda i: M.PILOTS[i][0]
calls = lambda: [c[0].split('/api/')[1] for c in M.ZKB_CALLS]

ROWS = """() => [...document.querySelectorAll('#fleetPanel .fk-card .fk-r:not(.fk-rh)')].map(r => { const b = r.querySelector('button.pr-row'), f = r.querySelector('.fk-fit');
  return {pilot: b.querySelector('.pr-pilot .nm').firstChild.textContent, dmg: (b.querySelector('.fk-dmg .pr-num') || {}).textContent || '', dk: (b.querySelector('.fk-dk') || {}).textContent || '',
    dps: (b.querySelector('.pr-dps .pr-num') || {}).textContent || '', load: !!f.querySelector('button[data-fk-load]'), fs: (f.querySelector('.fk-fs') || {}).textContent || '',
    fsT: (f.querySelector('.fk-fs') || {}).title || '', own: !!f.querySelector('[data-fk-own]'), spin: !!f.querySelector('.busy-spin')}; })"""
LA = "() => { const b = document.querySelector('#fleetPanel [data-fk-loadall]'), s = document.querySelector('#fleetPanel select[data-fk-mode]'), a = document.querySelector('#fleetPanel .fk-all'); return {t: b ? b.textContent.trim() : '', dis: b ? b.disabled : null, mode: s ? s.value : '', all: a ? a.textContent.trim() : ''}; }"
def open_kill(pg, k):
    pg.evaluate(f"() => fkOpen({k}, '{M.H[k]}', null, null, {{from: 'intel', km: {json.dumps(M.KM[k])}}})")
    pg.wait_for_function("() => document.querySelector('#fleetPanel .fk-card') && !fk.checking && fk.members.length && !fk.members.some(m => m.state === 'check')", timeout=60000); pg.wait_for_timeout(300)
def all_in(pg, timeout=180000):
    pg.wait_for_function("() => fk.members.length && fk.members.every(m => ['done', 'err'].includes(m.state)) && !fk.members.some(m => m.ownBusy)", timeout=timeout); pg.wait_for_timeout(500)
def stamps(pg): return pg.evaluate("() => zkbBudgetRead().length")

with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []
    def new_ctx(w, clip=False):
        ctx = b.new_context(viewport={'width': w, 'height': 1000}); ctx.on('page', lambda pg: pg.on('pageerror', lambda e: errs.append(str(e)))); M.route(ctx)
        if clip: ctx.grant_permissions(['clipboard-read', 'clipboard-write'])
        return ctx
    ctx = new_ctx(1440, True); pg = ctx.new_page(); pg.goto('file://' + HTML); pg.wait_for_timeout(500)
    M.ZKB_CALLS.clear()
    open_kill(pg, BIGK)
    R = pg.evaluate(ROWS)
    order = sorted(BIG, key=lambda x: (-DMG[x[0]], BIG.index(x)))
    check(not M.ZKB_CALLS and len(R) == 48 and all(r['load'] and not r['dps'] for r in R), f'open: no zKillboard request, 48 rows, each with Load and no fit ({len(M.ZKB_CALLS)} calls)')
    check([r['pilot'] for r in R] == [NAME(c) for c, _ in order], 'unloaded rows sorted by the damage on the kill (ties in the killmail order)')
    r0 = next(r for r in R if r['pilot'] == NAME(FB))
    check(all(r['dmg'] == f"{DMG[c]:,}" for r, (c, _) in zip(R, order)) and r0['dk'] == f"{round(DMG[FB] / TOT * 100)}% · final blow", f"each row's damage on the kill, its share and the final blow ({r0})")
    H = pg.evaluate("""() => { const h = [...document.querySelectorAll('#fleetPanel .fk-rh .pr-cols > span')].map(s => s.textContent), r = document.querySelector('#fleetPanel .fk-card .fk-r:not(.fk-rh)');
      const x = (sel) => r.querySelector(sel).getBoundingClientRect();
      return {h, fit: document.querySelector('#fleetPanel .fk-rh > .fk-fit').textContent, order: x('.pr-hull').left < x('.fk-dmg').left && x('.fk-dmg').right <= x('.pr-dps').left && x('.pr-dps').right < x('.fk-fit').left,
              nested: document.querySelectorAll('#fleetPanel button button, #fleetPanel button a').length}; }""")
    check(H['h'][:4] == ['Pilot', 'Ship on the kill', 'Damage', 'DPS'] and H['fit'] == 'Fit' and H['order'] and H['nested'] == 0, f'the Damage column beside the ship, before DPS; Fit on the far right; no button inside a button {H}')
    S = pg.evaluate("() => { const s = document.querySelector('#fleetPanel .fk-sum'); return {st: [...s.querySelectorAll('.fl-stat')].map(e => [e.querySelector('.k').textContent, (e.querySelector('.v') || e.querySelector('.fk-ewl')).innerText.replace(/\\s+/g, ' ')]), msg: (s.querySelector('.fl-msg') || {}).textContent || '', ctx: s.querySelector('.pr-head .ctx').textContent}; }")
    st = dict(S['st'])
    check(st.get('Pilots in ships') == '48' and st.get('Damage on the kill') == f"{sum(DMG.values()):,}" and st.get('Hulls') == 'Curse17 Loki13 Rifter8 Vedmak6 Sabre2 Ferox2' and st.get('Logistics') == '0'
          and S['msg'] == 'Fleet DPS, tank and EWAR need fits: Load all in the pilots list.' and S['ctx'] == '0 of 48 looked up, 48 not yet', f'the summary: what the killmail gives, and Load all for the rest {S}')
    la = pg.evaluate(LA)
    check(la == {'t': 'Load all (7 requests · 100 left)', 'dis': False, 'mode': 'common', 'all': ''}, f'Load all: common fits by default above 10, the exact cost and what is left {la}')
    # Load all, common fits
    pg.click('#fleetPanel [data-fk-loadall]'); all_in(pg)
    c = calls()
    check(len(c) == 7 and set(c) == PAIR_URLS, f'Load all made exactly the 7 pair lookups ({c})')
    R = pg.evaluate(ROWS); by = {r['pilot']: r for r in R}
    found = {n for n, r in by.items() if r['fs'] == 'own'}
    ally = {n for n, r in by.items() if r['fs'] == 'alliance'}
    unk = {n for n, r in by.items() if r['fs'] == 'unknown'}
    want_ally = {NAME(c) for ps, h in PAIRS[:4] for c in ps} - {NAME(c) for c in FOUND}
    want_unk = {NAME(c) for ps, h in PAIRS[4:] for c in ps} | {NAME(c) for c in NPC}
    check(found == {NAME(c) for c in FOUND} and all('found among their alliance' in by[n]['fsT'] for n in found), f'own fits found free in the alliance lists: {sorted(found)}')
    check(ally == want_ally and unk == want_unk, f"the rest: their alliance's common fit ({len(ally)}), no loss in the list or an NPC corporation: unknown ({len(unk)})")
    check({n for n, r in by.items() if r['own']} == {NAME(c) for c in NPC} | ({NAME(c) for ps, h in PAIRS[:7] for c in ps} - {NAME(c) for c in FOUND}), 'own? on every row without their own fit')
    cov = pg.inner_text('#fleetPanel .fk-cov')
    check(cov.startswith("fits: 5 their own (found in alliance losses) · 26 their alliance's common fit · 17 unknown (no DPS counted)"), f'the fits line ({cov})')
    dps = [int(r['dps'].replace(',', '')) if r['dps'] else -1 for r in R]
    check(dps == sorted(dps, reverse=True) and pg.evaluate(LA)['all'] == 'All loaded' and pg.inner_text('#fleetPanel .fk-card .pr-head .ctx') == 'most DPS first',
          f'all in: sorted by DPS, All loaded ({pg.evaluate(LA)})')
    M.ZKB_CALLS.clear()
    pg.click(f'#fleetPanel [data-fk-own="{NPC[0]}"]'); all_in(pg)
    r1 = next(r for r in pg.evaluate(ROWS) if r['pilot'] == NAME(NPC[0]))
    check(calls() == [f'losses/characterID/{NPC[0]}/shipTypeID/{B["Ferox"]}/'] and not r1['own'] and 'No Ferox loss of their own either' in r1['fsT'], f'own?: exactly 1 request, their own losses ({calls()}, {r1})')
    # share link: everything loaded, copied; a hand-cut one with one pilot
    pg.click('#fleetPanel [data-fk-share]'); pg.wait_for_timeout(300)
    link = pg.evaluate("() => navigator.clipboard.readText()")
    ent = link.split('#fleet=')[1].split('/')
    one = [e for e in ent[2].split('~') if e.startswith(f'{crts[0]}.')]
    ents = dict(e.split('.', 1) for e in ent[2].split('~'))
    check(one and one[0].split('.')[1] == 'o' and len(ents) == 48 and ents.get(str(NPC[1])) == 'u', f'the share link: own found free is plain own, an NPC pilot unknown ({one[:1]}, {len(ents)})')
    # kept fits: a reload within the hour
    M.ZKB_CALLS.clear()
    pg.reload(); pg.wait_for_timeout(500)
    open_kill(pg, BIGK)
    R2 = {r['pilot']: r['fs'] for r in pg.evaluate(ROWS)}
    check(not M.ZKB_CALLS and {n: f for n, f in R2.items() if n != NAME(NPC[1])} == {n: r['fs'] for n, r in by.items() if n != NAME(NPC[1])} and R2[NAME(NPC[1])] == '' and R2[NAME(NPC[0])] == 'unknown',
          f'a reload within the hour: no request, the same fits; the NPC pilot never looked up still unloaded ({len(M.ZKB_CALLS)} calls)')
    la = pg.evaluate(LA)
    check(la['t'] == 'Load all (0 requests · 92 left)' or la['t'].startswith('Load all (0 requests'), f'Load all for the one left: 0 requests (an NPC corporation has no pair) {la}')
    pg.evaluate("() => fetchLossesStubs(%d, %d, true)" % (crts[0], B['Curse'])); pg.wait_for_timeout(1500)
    check(len(M.ZKB_CALLS) == 1, f'Refresh losses (forceRefresh) still asks ({calls()})')
    # an hour later
    pg.evaluate("""() => new Promise(res => { const q = indexedDB.open(DSCAN_CACHE_DB_NAME); q.onsuccess = () => { const db = q.result, tx = db.transaction('zkb', 'readwrite'), os = tx.objectStore('zkb');
      os.openCursor().onsuccess = (e) => { const c = e.target.result; if(!c) return; const v = c.value; v.ts -= 61 * 60 * 1000; c.update(v); c.continue(); }; tx.oncomplete = () => res(); }; })""")
    M.ZKB_CALLS.clear(); pg.reload(); pg.wait_for_timeout(500); open_kill(pg, BIGK)
    R3 = pg.evaluate(ROWS)
    check(not M.ZKB_CALLS and all(r['load'] for r in R3) and pg.evaluate(LA)['t'].startswith('Load all (7 requests'), f'an hour later: every fit unloaded again, Load all 7 requests ({len(M.ZKB_CALLS)} calls, {sum(r["load"] for r in R3)} unloaded)')
    # a hand-cut link with one pilot's fit: it loads with no zKillboard request, the rest stay unloaded
    M.ZKB_CALLS.clear()
    pg.close(); pg = ctx.new_page(); pg.goto('file://' + HTML + '#fleet=' + ent[0] + '/' + ent[1] + '/' + one[0]); pg.wait_for_timeout(300)
    pg.wait_for_function("() => fk.members.length === 48 && !fk.checking && fk.members.some(m => m.state === 'done')", timeout=60000); pg.wait_for_timeout(400)
    R4 = pg.evaluate(ROWS)
    check(not M.ZKB_CALLS and sum(not r['load'] for r in R4) == 1 and next(r for r in R4 if r['pilot'] == NAME(crts[0]))['fs'] == 'own', f'a share link: its fit loaded with no zKillboard request, the 47 it doesn\'t carry unloaded ({len(M.ZKB_CALLS)} calls)')
    # a row opens the Pilot Analyzer; its Load doesn't; the focus stays on a row through redraws
    M.ZKB_CALLS.clear()
    rb = f'#fleetPanel button.pr-row[data-fk-pilot="{NAME(crts[12])}"]'
    pg.focus(rb)
    pg.click(f'#fleetPanel [data-fk-load="{crts[11]}"]'); pg.wait_for_timeout(200); pg.focus(rb)
    pg.wait_for_function(f"() => fk.members.find(m => m.id === {crts[11]}).state === 'done'", timeout=60000); pg.wait_for_timeout(300)
    f = pg.evaluate(f"() => [document.activeElement && document.activeElement.dataset.fkPilot, document.querySelector('#tabBtnFleet').classList.contains('active')]")
    check(f == [NAME(crts[12]), True] and len(M.ZKB_CALLS) == 2, f'a row\'s Load: the Fleet tab stays, the focus stays on the row pressed before through the redraws; own list, then the pair ({f}, {calls()})')
    pg.click(rb); pg.wait_for_timeout(600)
    check(pg.evaluate("() => [document.querySelector('#tabBtnPilot').classList.contains('active'), document.querySelector('#pilotName').value]") == [True, NAME(crts[12])], 'the row itself still opens the Pilot Analyzer')
    ctx.close()

    # the reserve: 70 of the 100 spent; 3 of them age out about 25 s from now
    ctx = new_ctx(1440); pg = ctx.new_page(); pg.goto('file://' + HTML); pg.wait_for_timeout(300)
    pg.evaluate("() => { const n = Date.now(), a = []; for(let i = 0; i < 3; i++) a.push(n - ZKB_BUDGET_WINDOW_MS + 25000 + i); for(let i = 0; i < 67; i++) a.push(n - 60000); localStorage.setItem(ZKB_BUDGET_KEY, JSON.stringify(a)); }")
    M.ZKB_CALLS.clear(); open_kill(pg, BIGK)
    check(pg.evaluate(LA)['t'] == 'Load all (7 requests · 30 left)', f'with 70 spent: 30 left {pg.evaluate(LA)}')
    pg.click('#fleetPanel [data-fk-loadall]')
    pg.wait_for_function("() => fk.pause && !fk.members.some(m => ['wait', 'load'].includes(m.state))", timeout=60000); pg.wait_for_timeout(300)
    la = pg.evaluate(LA); n1 = len(M.ZKB_CALLS); st1 = stamps(pg)
    check(n1 == 5 and st1 == 75 and la['dis'] and re.match(r'^Paused to keep 25 lookups · continues in 0:[0-2]\d$', la['t']) and 'ZKB-04' not in pg.inner_text('#fleetPanel'),
          f'Load all stops at exactly 75, paused with the countdown, disabled ({n1} calls, {st1} spent, {la})')
    t1 = pg.evaluate("() => document.querySelector('#fleetPanel [data-fk-loadall] .zkb-cd').textContent"); pg.wait_for_timeout(2100)
    t2 = pg.evaluate("() => document.querySelector('#fleetPanel [data-fk-loadall] .zkb-cd').textContent")
    check(t1 != t2, f'the countdown runs ({t1} -> {t2})')
    pg.click(f'#fleetPanel [data-fk-load="{NPC[1]}"]'); pg.wait_for_function(f"() => fk.members.find(m => m.id === {NPC[1]}).state === 'done'", timeout=60000)
    check(len(M.ZKB_CALLS) == 6 and stamps(pg) == 76, f'a row\'s Load still asks while Load all waits ({len(M.ZKB_CALLS)} calls, {stamps(pg)} spent)')
    pg.wait_for_function("() => !fk.pause && !fk.members.some(m => ['later', 'wait', 'load'].includes(m.state))", timeout=60000); pg.wait_for_timeout(400)
    check(len(M.ZKB_CALLS) == 8 and stamps(pg) <= 75 and 'ZKB-04' not in pg.inner_text('#fleetPanel') and not pg.evaluate("() => fk.members.some(m => m.state === 'err')"),
          f'when the oldest stamps age out it carries on by itself: the last 2 pairs, no error ({len(M.ZKB_CALLS)} calls, {stamps(pg)} spent)')
    ctx.close()

    # own fits up to 10, common from 11
    ctx = new_ctx(1440); pg = ctx.new_page(); pg.goto('file://' + HTML); pg.wait_for_timeout(300)
    M.ZKB_CALLS.clear(); open_kill(pg, ELEVENK)
    la11 = pg.evaluate(LA)
    pg.select_option('#fleetPanel select[data-fk-mode]', 'own'); pg.wait_for_timeout(200)
    la11o = pg.evaluate(LA)
    check(la11o['mode'] == 'own' and la11o['t'] == 'Load all (11 requests, up to 14 · 100 left)', f'choosing Own fits: the label follows, 11 own lists, up to 3 pairs more {la11o}')
    open_kill(pg, TENK); la = pg.evaluate(LA)
    check(la11['mode'] == 'common' and la['mode'] == 'own' and la['t'] == 'Load all (10 requests, up to 12 · 100 left)' and not M.ZKB_CALLS, f'11 pilots: common fits; 10: own fits, "10 requests, up to 12" ({la11}, {la})')
    pg.click('#fleetPanel [data-fk-loadall]'); all_in(pg)
    c = calls()
    check(len(c) <= 12 and len([x for x in c if '/characterID/' in x]) == 10, f'own fits: 10 own lists and no more than 12 in all ({len(c)}: {c})')
    ctx.close()

    # phone
    ctx = new_ctx(390); pg = ctx.new_page(); pg.goto('file://' + HTML); pg.wait_for_timeout(300)
    open_kill(pg, TENK)
    L = pg.evaluate("""() => [document.documentElement.scrollWidth, document.querySelector('#fleetPanel [data-fk-load]').getBoundingClientRect().height, document.querySelector('#fleetPanel [data-fk-loadall]').getBoundingClientRect().height,
      document.querySelector('#fleetPanel select[data-fk-mode]').getBoundingClientRect().height, document.querySelector('#fleetPanel .fk-card .pr-mob').innerText,
      [...document.querySelectorAll('#fleetPanel *')].filter(e => { const b = e.getBoundingClientRect(); return e.checkVisibility() && b.width && (b.right > innerWidth + 1 || b.left < -1); }).map(e => e.className || e.tagName).slice(0, 4)]""")
    check(L[0] <= 390 and L[1] >= 44 and L[2] >= 44 and L[3] >= 44 and 'dmg' in L[4] and not L[5], f'390 px: nothing off the page, Load, Load all and its choice 44 px, the damage in the card {L}')
    ctx.close()
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
