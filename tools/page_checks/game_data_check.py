"""Keeping up with EVE patches on the page (v2026.11.04.3, build queue 008, roadmap/game-data-update-plan.md sections 1 and 3).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/game_data_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner 2026-11-02: "Eve has an expansion releasing on Nov 10th ... How do we identify stat changes, new skills or modules,
etc."; from the mockup (Claude outputs/game_data_note_mockup.html): place and amber "this is fine", "keep the rule", the Fleet
tag "on the hull is fine", the status line "Item data refreshing". ESI answers come from pyfa's data (esi_from_sde.py); EVE's
server version (/status/) from a stand-in here, so each load can see a new build, the same one, a slow answer or none:
  * the item data kept in this browser (IndexedDB 'types' / 'groups') is dropped when the server version changes, before the
    first lookup (a made-up "stale" Rifter kept in the store must not come back), and only those stores ('zkb', 'killmails',
    'orgs' keep their entries); "Item data refreshing" where the version tag is, once; the version is remembered;
  * the first visit (nothing remembered) and the same version clear nothing and say nothing;
  * a /status/ answer slower than 3 s: the lookup goes ahead within about 3 s with the kept data, nothing is cleared, and the
    version isn't remembered (the next load asks again); a failed /status/ the same; one /status/ request per load;
  * the note on changed items, with a made-up list (Ferox, Damage Control II, Large Shield Extender II, Magnetic Field
    Stabilizer II, build 3690000) written into a copy of the page in the tools' own form (check_game_data_pending.line):
    the Fit Analyzer on a Ferox fit: "Changed in EVE's update: Ferox, Damage Control II, Magnetic Field Stabilizer II +1 more",
    the hover naming the build, all four and the pyfa sentence; a Rifter: no line; a Rifter carrying a listed module in its
    cargo: no line; a Pilot Analyzer loss with a listed module: its line; My Fit in the Matchup (a Drake): its own line;
    the Fleet tab: a "changed" tag after each listed hull, none on the others, nothing pressable in it; Ships on scan: the
    line in a listed hull's card only; every line and tag only in those places (never Intel, never page-wide);
  * the page as shipped (an empty list): no line on the same Ferox fit;
  * a phone (390 px): the line inside the page; no page errors.
v2026.11.04.2 fails (no version check, no note).
"""
import sys, os, re, time, json, tempfile, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from playwright.sync_api import sync_playwright
from esi_from_sde import route_all
import sa_mocks as M
from check_game_data_pending import RX, line as pending_line

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok

T = M.byname
BUILD = 3690000
PENDING = [T['Ferox'], T['Damage Control II'], T['Large Shield Extender II'], T['Magnetic Field Stabilizer II']]
FEROX = ('[Ferox, Check Ferox]\nDamage Control II\nMagnetic Field Stabilizer II\nMagnetic Field Stabilizer II\nTracking Enhancer II\n\n'
         '10MN Afterburner II\nLarge Shield Extender II\nLarge Shield Extender II\nMultispectrum Shield Hardener II\nWarp Disruptor II\n\n'
         + '\n'.join(['250mm Railgun II, Antimatter Charge M'] * 7) + '\n\nMedium Core Defense Field Extender I\nMedium Core Defense Field Extender I\n'
         'Medium Hybrid Burst Aerator I\n\nHammerhead II x5\n')
RIFTER = '[Rifter, Check Rifter]\nDamage Control I\n\n1MN Afterburner I\n\n200mm AutoCannon I, EMP S\n'
RIFTER_CARGO = RIFTER + '\n\nHammerhead II x2\nLarge Shield Extender II x2\n'
DRAKE = ('[Drake, My Drake]\nDamage Control II\nBallistic Control System II\nBallistic Control System II\n\n10MN Afterburner II\n'
         'Large Shield Extender II\nLarge Shield Extender II\nMultispectrum Shield Hardener II\nWarp Disruptor II\n\n'
         + '\n'.join(['Heavy Missile Launcher II, Scourge Heavy Missile'] * 6) + '\n\nMedium Core Defense Field Extender I\n'
         'Medium Core Defense Field Extender I\nMedium Core Defense Field Extender I\n\nHobgoblin II x5\n')
WHY = 'This tool checks its numbers against pyfa after pyfa updates; until then they may be off.'

# ---- a copy of the page with the made-up list, written in the tools' own form
src = open(HTML, encoding='utf-8').read()
tmpd = tempfile.mkdtemp(prefix='gdchk-')
LISTED = os.path.join(tmpd, 'index.html')
m = RX.search(src)
open(LISTED, 'w', encoding='utf-8').write(src[:m.start()] + pending_line(m.group(1), BUILD, PENDING) + src[m.end():] if m else src)
for d in ('img',):
    if os.path.isdir(os.path.join(os.path.dirname(HTML), d)): shutil.copytree(os.path.join(os.path.dirname(HTML), d), os.path.join(tmpd, d))

# ---- the made-up kill for the Fleet tab and the loss for the Pilot Analyzer
IDS = sorted(i for i in M.PILOTS if i < 92000000)
NOW = time.time() * 1000
SYS = sorted(M.SYSTEMS)[0]   # a system the stand-in names
def fleet_pick():
    att = [(IDS[0], 'Ferox'), (IDS[1], 'Muninn'), (IDS[2], 'Ferox'), (IDS[3], 'Drake')]
    A = [{'damage_done': 100 + i, 'final_blow': i == 0, 'security_status': 0, 'ship_type_id': T[s], **M.aff(c)} for i, (c, s) in enumerate(att)]
    victim = IDS[5]; k = 9890101
    km = {'killmail_id': k, 'killmail_time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(NOW / 1000 - 300)), 'solar_system_id': SYS,
          'victim': {'character_id': victim, **{x: y for x, y in M.aff(victim).items() if x != 'character_id'}, 'ship_type_id': T['Rifter'], 'damage_taken': 9000, 'items': [], 'position': {'x': 0, 'y': 0, 'z': 0}},
          'attackers': A}
    return {'id': k, 'hash': f'{k:040x}', 'km': km, 'name': M.PILOTS[victim][0], 'ship': 'Rifter', 'sys': M.SYSTEMS[SYS], 'sysId': SYS, 'ships': 4, 't': NOW - 300000, 'v': 'n', 'isk': 80e6}
OPEN = """(p) => { const w = IT_KILL_WORD[p.v]; p.word = [w[0], w[1]]; fkOpen(p.id, p.hash, null, null, {from: 'intel', km: p.km, picks: [p]}); return 1; }"""
def loss():
    items = []
    def it(name, flag): items.append({'item_type_id': T[name], 'flag': flag, 'quantity_destroyed': 1, 'singleton': 0})
    for i, n in enumerate(['Damage Control II', 'Gyrostabilizer II', 'Gyrostabilizer II']): it(n, 11 + i)
    for i, n in enumerate(['10MN Afterburner II', 'Warp Disruptor II']): it(n, 19 + i)
    for i in range(5): it('720mm Howitzer Artillery II', 27 + i); it('Republic Fleet EMP M', 27 + i)
    return {'killmail_id': 9890001, 'killmail_time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(NOW / 1000 - 86400)), 'solar_system_id': SYS,
            'victim': {'character_id': IDS[6], 'corporation_id': M.PILOTS[IDS[6]][1], 'ship_type_id': T['Muninn'], 'damage_taken': 18000, 'items': items, 'position': {'x': 0, 'y': 0, 'z': 0}}, 'attackers': []}

# ---- helpers in the page
STORE = """async (o) => { const db = await openDscanCacheDb(); const n = {}; for(const s of ['types', 'groups', 'zkb', 'killmails', 'orgs']) n[s] = await new Promise(res => { const r = db.transaction(s).objectStore(s).count(); r.onsuccess = () => res(r.result); r.onerror = () => res(-1); }); return n; }"""
PLANT = """async () => { await dscanCacheSet('types', 587, {type_id: 587, name: 'STALE Rifter', group_id: 25, dogma_attributes: [], dogma_effects: []});
  await dscanCacheSet('groups', 25, {group_id: 25, name: 'STALE Frigate', category_id: 6, types: [587]});
  for(const s of ['zkb', 'killmails', 'orgs']) await dscanCacheSet(s, 'gdchk', {kept: 1}); await new Promise(r => setTimeout(r, 300)); return 1; }"""
# [name, ms the lookup took, ms from the page sending /status/ to the answer]. v2026.11.06.2 (LESSON #115): the page's 3 s wait runs
# from /status/ being sent, as the late answer does; timing only from the lookup's own start failed under load, when the check
# reached the page seconds after it had loaded (the 1.5 s answer already in, the 3 s wait already over).
LOOKUP = """async () => { const t0 = performance.now(); const t = await Promise.race([getType(587), new Promise(r => setTimeout(() => r({name: 'NO ANSWER IN 8 S'}), 8000))]); const t1 = performance.now(); return [t.name, Math.round(t1 - t0), window.__gdT0 == null ? -1 : Math.round(t1 - window.__gdT0)]; }"""

def section1(b):
    print('-- item data kept in the browser, and a new EVE build')
    ctx = b.new_context(viewport={'width': 1440, 'height': 1000})
    # /status/ answers held back in the page itself (a sleep in the route handler would hold up this script too). v2026.11.06.2 (LESSON #138): the
    # delay comes in the address (?gdchk=ms); kept in sessionStorage it was sometimes gone after the next goto, and the answer came at once.
    ctx.add_init_script("""(() => { const ms = Number(new URLSearchParams(location.search).get('gdchk') || 0); if(!ms) return; const f = window.fetch;
      window.fetch = (u, o) => /\\/status\\//.test(String(u && u.url || u)) ? (window.__gdT0 = performance.now(), f(u, o)).then(r => new Promise(res => setTimeout(() => res(r), ms))) : f(u, o); })();""")
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg)
    st = {'v': None, 'delay': 0, 'fail': False, 'n': 0}
    def status(route):
        st['n'] += 1
        if st['fail']: return route.abort()
        route.fulfill(status=200, content_type='application/json', body=json.dumps({'players': 1, 'server_version': st['v'], 'start_time': '2026-11-10T11:00:00Z'}))
    pg.route(re.compile(r'https://esi\.evetech\.net/.*/status/.*'), status)
    def load(v=None, delay=0, fail=False, wait=1500):
        st.update(v=v, fail=fail, n=0)
        pg.goto('file://' + HTML + (f'?gdchk={int(delay * 1000)}' if delay else '')); pg.wait_for_timeout(wait)
    shown = lambda: pg.evaluate("() => { const e = document.getElementById('cacheStatus'); return e && !e.hidden ? e.textContent : ''; }")
    remembered = lambda: pg.evaluate("() => localStorage.getItem('dscanServerVersion')")
    # load 0: /status/ fails; a stale Rifter is kept (the store as an old visit left it)
    load(fail=True)
    pg.evaluate(PLANT)
    check(remembered() is None, 'a failed /status/ remembers no version')
    # load 1: the first visit with a version: remember it, clear nothing
    load('3667080')
    r = pg.evaluate(LOOKUP)
    check(r[0] == 'STALE Rifter', f'first visit: the kept item data is used, nothing cleared (got {r[0]!r})')
    check(remembered() == '3667080', f'first visit: the version is remembered ({remembered()!r})')
    check(shown() == '', f'first visit: nothing said ({shown()!r})')
    check(st['n'] == 1, f'one /status/ request per load ({st["n"]})')
    # load 2: the same version: nothing cleared
    load('3667080')
    r = pg.evaluate(LOOKUP)
    check(r[0] == 'STALE Rifter' and shown() == '', f'same version: nothing cleared or said ({r[0]!r}, {shown()!r})')
    # load 3: a new version, its answer 1.5 s late: the first lookup waits for it, then gets fresh data; only types and groups cleared
    load('3690000', delay=1.5, wait=100)
    r = pg.evaluate(LOOKUP)
    check(r[0] == 'Rifter' and r[2] >= 1400, f'new version: the first lookup waits for the check (1.5 s after /status/ was sent) and gets fresh data, not the kept one ({r})')
    n = pg.evaluate(STORE)
    check(n['zkb'] >= 1 and n['killmails'] >= 1 and n['orgs'] >= 1, f'new version: zKillboard answers, killmails and organisations kept ({n})')
    g = pg.evaluate("async () => (await getGroup(25)).name")
    check(g != 'STALE Frigate', f'new version: groups cleared too (got {g!r})')
    pg.wait_for_timeout(300)
    check(shown() == 'Item data refreshing', f'new version: "Item data refreshing" shown ({shown()!r})')
    check(remembered() == '3690000', f'new version: remembered ({remembered()!r})')
    pg.wait_for_timeout(5500)
    check(shown() == '', f'the status line goes away and the version tag comes back ({shown()!r})')
    # load 4: a slow answer (6 s) with a newer version: the lookup doesn't wait for it; nothing cleared or remembered
    pg.evaluate(PLANT)
    load('3700000', delay=6, wait=100)
    r = pg.evaluate(LOOKUP)
    check(r[0] == 'STALE Rifter' and (r[1] < 1500 or 0 <= r[2] < 4500), f'slow /status/: the lookup went ahead with the kept data within ~3 s of /status/ being sent ({r})')
    pg.wait_for_timeout(6500)
    check(remembered() == '3690000' and pg.evaluate(LOOKUP)[0] == 'STALE Rifter', f'slow /status/: nothing cleared or remembered when it came late ({remembered()!r})')
    # load 5: /status/ fails: nothing cleared, carry on
    load('3710000', fail=True, wait=200)
    r = pg.evaluate(LOOKUP)
    check(r[0] == 'STALE Rifter' and r[1] < 2500 and remembered() == '3690000', f'failed /status/: the kept data, at once ({r}, {remembered()!r})')
    check(not errs, f'no page errors ({errs[:2]})')
    ctx.close()

def section3(b):
    print('-- the note on changed items (made-up list)')
    ctx = b.new_context(viewport={'width': 1440, 'height': 1000})
    ctx.add_init_script("""(() => { const now = new Date().toISOString(); try{ localStorage.setItem('dscanMyShips', JSON.stringify({v: 2, inUse: 'gd1', use: true,
      fits: [{v: 1, id: 'gd1', eft: %s, shipName: 'Drake', fitName: 'My Drake', savedAt: now, usedAt: now, use: true}]})); }catch(e){} })();""" % json.dumps(DRAKE))
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    M.route(ctx)
    pg.goto('file://' + LISTED); pg.wait_for_timeout(1200)
    def fa(eft):
        pg.evaluate("(t) => { switchTab('fit'); document.getElementById('fitAnalyzerResults').innerHTML = ''; document.getElementById('fitAnalyzerInput').value = t; document.getElementById('fitAnalyzerBtn').click(); }", eft)
        pg.wait_for_selector('#fitAnalyzerResults .fit-layout', timeout=60000); pg.wait_for_timeout(300)
    notes = lambda sel: pg.evaluate("(s) => [...document.querySelectorAll(s)].filter(e => e.offsetParent).map(e => [e.textContent.trim(), e.title || ''])", sel)
    fa(FEROX)
    n = notes('#fitAnalyzerResults .mys-threat-view .gd-note')
    check(len(n) == 1 and n[0][0] == "Changed in EVE's update: Ferox, Damage Control II, Magnetic Field Stabilizer II +1 more", f'Fit Analyzer, Ferox: the line ({n})')
    check(bool(n) and n[0][1] == f"Changed in EVE's update (build {BUILD}): Ferox, Damage Control II, Magnetic Field Stabilizer II, Large Shield Extender II. {WHY}", f'Fit Analyzer, Ferox: the hover ({n[0][1] if n else None})')
    pos = pg.evaluate("() => { const n = document.querySelector('#fitAnalyzerResults .gd-note'), l = document.querySelector('#fitAnalyzerResults .fit-layout'); return n && l ? [n.getBoundingClientRect().bottom <= l.getBoundingClientRect().top + 1, getComputedStyle(n).borderLeftColor] : null; }")
    amber = pg.evaluate("() => { const d = document.createElement('div'); d.style.color = 'var(--amber)'; document.body.appendChild(d); const c = getComputedStyle(d).color; d.remove(); return c; }")
    check(bool(pos) and pos[0] and pos[1] == amber, f'the line sits above the cards with an amber edge ({pos}, amber {amber})')
    # My Fit in the Matchup
    b2 = pg.wait_for_selector('#fitAnalyzerResults button.mys-sw-btn[data-view="mine"]', timeout=30000); b2.click()
    pg.wait_for_selector('#fitAnalyzerResults .mys-mine-view:not([hidden]) .fit-layout', timeout=60000); pg.wait_for_timeout(300)
    n = notes('#fitAnalyzerResults .mys-mine-view .gd-note')
    check(len(n) == 1 and n[0][0] == "Changed in EVE's update: Damage Control II, Large Shield Extender II", f'My Fit (Drake): its own line ({n})')
    pg.click('#fitAnalyzerResults button.mys-sw-btn[data-view="threat"]'); pg.wait_for_timeout(200)
    fa(RIFTER)
    check(not notes('#fitAnalyzerResults .mys-threat-view .gd-note'), 'Fit Analyzer, Rifter (nothing listed): no line')
    fa(RIFTER_CARGO)
    cargo = pg.evaluate("async (t) => { const p = await parseEftFit(t); return Object.keys(p.tally['Cargo'] || {}).map(Number).includes(%d); }" % T['Large Shield Extender II'], RIFTER_CARGO)
    check(not notes('#fitAnalyzerResults .mys-threat-view .gd-note') and cargo, f'Rifter with a listed module in its cargo: no line (the module is in the cargo: {cargo})')
    # Pilot Analyzer: a loss
    pg.evaluate("""async (km) => { switchTab('pilot'); const {fits, idToName} = await buildLossFits([{km}], km.victim.ship_type_id); renderFitTabs('Check Pilot', 'Muninn', fits, idToName); }""", loss())
    pg.wait_for_selector('#fitResults .fit-layout', timeout=60000)
    n = notes('#fitResults .gd-note')
    check(len(n) == 1 and n[0][0] == "Changed in EVE's update: Damage Control II", f'Pilot Analyzer, a Muninn loss: its line ({n})')
    # the Fleet tab
    pg.evaluate(OPEN, fleet_pick()); pg.wait_for_selector('#fleetPanel .pr-row', timeout=60000)
    try: pg.wait_for_function("() => [...document.querySelectorAll('#fleetPanel .pr-hn .nm')].every(n => !/^type \\d/.test(n.textContent))", timeout=20000)
    except Exception: pass   # names not in: the check below says what it saw
    pg.wait_for_timeout(300)
    rows = pg.evaluate("() => [...document.querySelectorAll('#fleetPanel .pr-row')].map(r => [r.querySelector('.pr-hn .nm').childNodes[0].textContent, (r.querySelector('.gd-mark') || {}).textContent || '', (r.querySelector('.gd-mark') || {}).title || '', r.querySelectorAll('.gd-mark button, .gd-mark a, .gd-mark [tabindex], button.gd-mark, a.gd-mark, .gd-mark[tabindex]').length])")
    want = {('Ferox', 'changed'), ('Muninn', ''), ('Drake', '')}
    check({(r[0], r[1]) for r in rows} == want and sum(r[0] == 'Ferox' for r in rows) == 2, f'Fleet tab: "changed" on each Ferox, none on the others ({rows})')
    check(all(r[2] == f"Changed in EVE's update (build {BUILD}): Ferox. {WHY}" for r in rows if r[1]), 'Fleet tab: the sentence on hover')
    check(all(r[3] == 0 for r in rows), 'Fleet tab: nothing pressable inside the tag')
    # Ships on scan
    pg.evaluate("(s) => { switchTab('dscan'); document.getElementById('dscanInput').value = s; document.getElementById('analyzeBtn').click(); }",
                '\n'.join(f"{T[t]}\tSomeone's {t}\t{t}\t{d}" for t, d in [('Ferox', '420 km'), ('Ferox', '3.2 AU'), ('Drake', '380 km')]))
    row = pg.wait_for_selector(f'#scanRail .sr-row[data-sr="{T["Ferox"]}"]', timeout=60000)
    pg.evaluate(f"() => scanCardOpen(document.querySelector('#scanRail .sr-row[data-sr=\"{T['Ferox']}\"]'), true)"); pg.wait_for_timeout(200)
    n = notes('#scanCard .gd-note')
    check(len(n) == 1 and n[0][0] == "Changed in EVE's update: Ferox", f'Ships on scan: the Ferox card has the line ({n})')
    pg.evaluate(f"() => scanCardOpen(document.querySelector('#scanRail .sr-row[data-sr=\"{T['Drake']}\"]'), true)"); pg.wait_for_timeout(200)
    check(not notes('#scanCard .gd-note'), 'Ships on scan: the Drake card has none')
    stray = pg.evaluate("""() => [...document.querySelectorAll('.gd-note, .gd-mark')].filter(e => !e.closest('#fitAnalyzerResults, #fitResults, #scanRail, #fleetPanel')).map(e => e.parentElement.id || e.parentElement.className)""")
    intel = pg.evaluate("() => document.querySelectorAll('#tabIntel .gd-note, #tabIntel .gd-mark, header .gd-note').length")
    check(not stray and intel == 0, f'the line and tag only in those places, none on Intel or page-wide ({stray}, {intel})')
    # a phone
    pg.set_viewport_size({'width': 390, 'height': 800}); fa(FEROX)
    w = pg.evaluate("() => { const n = document.querySelector('#fitAnalyzerResults .gd-note').getBoundingClientRect(); return [Math.round(n.left), Math.round(n.right), document.documentElement.scrollWidth]; }")
    check(w[0] >= 0 and w[1] <= 390 and w[2] <= 390, f'phone: the line inside the page, nothing off it ({w})')
    check(not errs, f'no page errors ({errs[:2]})')
    ctx.close()

def shipped(b):
    print('-- the page as shipped (an empty list)')
    ctx = b.new_context(viewport={'width': 1440, 'height': 1000}); pg = ctx.new_page(); M.route(ctx)
    pg.goto('file://' + HTML); pg.wait_for_timeout(800)
    pg.evaluate("(t) => { switchTab('fit'); document.getElementById('fitAnalyzerInput').value = t; document.getElementById('fitAnalyzerBtn').click(); }", FEROX)
    pg.wait_for_selector('#fitAnalyzerResults .fit-layout', timeout=60000)
    check(pg.evaluate("() => document.querySelectorAll('.gd-note, .gd-mark').length") == 0, 'empty list: no line on the Ferox fit')
    ctx.close()

try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        for part in (section1, section3, shipped):
            try: part(b)
            except Exception as e: check(False, f'{part.__name__} stopped: {type(e).__name__}: {str(e)[:300]}')
        b.close()
finally:
    shutil.rmtree(tmpd, ignore_errors=True)
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
