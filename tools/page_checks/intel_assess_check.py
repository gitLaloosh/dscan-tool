"""Intel delivery 2: from intel to assessment (v2026.10.14.98; roadmap/intel-plan.md, mockup
Claude outputs/intel_assess_mockup.html).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/intel_assess_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner's answers, all as recommended: "Paired ship" (a pilot link opens the Pilot Analyzer in the ship the line pairs them
with), "Everyone until clear" (a system keeps everyone reported there in the time set until a clear), "Intel's pairing
wins" (in the System Analyzer), "Add it" (copy a line's shape with names replaced). Uses intel_check.py's made-up folder,
mocks and system names (its first part, run here); every line, pilot and character is made up. Checks:
  * pairing: "Pilot (Ship)"; one pilot + one ship; none for two pilots, for x2, for +N;
  * Near You keeps everyone until a clear: two lines about 8WA-Z6 add up (the same ship type once, at its larger count),
    a clear empties it, a later report starts again; the time set drops old names (itLive an hour on);
  * a pilot link in the Feed: the Pilot Analyzer on that pilot in the paired ship (dossier on that hull), the "From Intel"
    line, Back to Intel; an unpaired one: no ship; another pilot typed by hand: the line goes; Near You's names link too;
  * Assess: the System Analyzer with the system's pilots as Local and its ships as D-Scan, analyzed; the From Intel line
    (pilots, +N, ships, the pairing, your paste replaced); Intel's pairing as that pilot's possible ship ("reported in it
    on Intel"), the unpaired pilot by the old rule; Restore my paste; typing in the boxes ends it; no Restore without a
    paste of your own; no Assess on a clear row;
  * the Feed keeps the time set (the owner: "drop entries older than 15 minutes"): an older line goes, from the page and memory;
  * copy shape: the clipboard holds the line with SYS / PILOT / WORD (one per multi-word name), ship names, counts,
    brackets, '*' and what was read; no system or pilot name in it;
  * 390 px: Assess, the line's toggle (v.100) and the copy button big enough, nothing off the page; no page errors.
v2026.10.14.97 fails.
"""
import sys, os, time, re, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
_src = open(os.path.join(HERE, 'intel_check.py'), encoding='utf-8').read()
_src = _src[:_src.index('with sync_playwright() as p:')]
NS = {'__file__': os.path.join(HERE, 'intel_check.py'), '__name__': 'intel_check_prefix'}
exec(compile(_src, 'intel_check.py (first part)', 'exec'), NS)   # the made-up folder, mocks, names; its table checks run too
globals().update({k: v for k, v in NS.items() if not k.startswith('__') and k not in ('check', 'fails')})
from playwright.sync_api import sync_playwright
check = NS['check']
NEAR2 = """() => [...document.querySelectorAll('#intelPanel .it-nb')].map(r => [r.querySelector('.sys').textContent, r.querySelector('.st b').textContent, r.querySelector('.who').textContent, !!r.querySelector('[data-it-assess]')])"""
def near_row(pg, name): return next((r for r in pg.evaluate(NEAR2) if r[0] == name), None)
def pa_done(pg):
    pg.wait_for_function("() => !document.querySelector('#fitBtn').disabled && document.querySelector('#pilotBusy').hidden", timeout=120000); pg.wait_for_timeout(500)
def sa_done(pg, n):
    pg.wait_for_function(f"() => {{ const c = document.querySelector('#tabDscan .pr-head .ctx'); return c && c.textContent.startsWith('{n} of {n} looked up'); }}", timeout=120000); pg.wait_for_timeout(500)
FEED_ONE = """(raw) => { const r = [...document.querySelectorAll('#intelPanel .it-fd')].find(f => (f.querySelector('.raw') || {}).textContent === raw && (f.querySelector('.it-raw .who') || {}).textContent === 'Gate Watcher');
  return r ? [...r.querySelectorAll('.it-chip')].map(c => [c.className.replace('it-chip ', '').replace(/^p /, ''), (c.querySelector('.nm') || c).textContent]) : null; }"""
SA_ROWS = """() => [...document.querySelectorAll('#tabDscan button.pr-row')].map(b => [b.querySelector('.pr-pilot .nm').firstChild.textContent.trim(), b.querySelector('.pr-hull .nm').firstChild.textContent.trim(), (b.querySelector('.pr-basis') || b.querySelector('.pr-hull .ctx') || {}).textContent || ''])"""

with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []
    def new_ctx(w):
        ctx = b.new_context(viewport={'width': w, 'height': 1000}); ctx.on('page', lambda pg: pg.on('pageerror', lambda e: errs.append(str(e))))
        ctx.add_init_script(FS); route(ctx); ctx.grant_permissions(['clipboard-read', 'clipboard-write']); return ctx
    def start(w):
        ctx = new_ctx(w); pg = ctx.new_page(); pg.goto('file://' + HTML)
        pg.evaluate("(s) => { localStorage.setItem('dscanSide', JSON.stringify(s)); localStorage.setItem('dscanIntel', JSON.stringify({channels: ['region.intel'], me: 95000001, range: 3, sound: false, notify: false, forget: 15, hideFriendly: true})); localStorage.removeItem('dscanSaSize'); }", SIDE)
        pg.reload(); pg.wait_for_timeout(400)
        setup_logs(pg); pg.click('#tabBtnIntel'); pg.click('[data-it-act="folder"]'); pg.wait_for_timeout(300); pg.click('#intelSwLabel'); tick(pg)
        return ctx, pg
    ctx, pg = start(1440)
    T = time.time()
    LONG = '8WA-Z6*  Marrek Ketter*  Vesna Dossier +3  sabre vedmak x2 loki'
    W(pg, F_INTEL, line(T, 'Scout Alt', LONG)
      + line(T + 1, 'Gate Watcher', 'Anouk Morrow (Scimitar) jumped QX-L from 4K-TRB')
      + line(T + 2, 'Gate Watcher', 'Y-OMTZ Seren Ketter Kirra Longtail sabre')
      + line(T + 3, 'Someone', 'D-W7F0 Marrek Ketter vedmak x2')
      + line(T + 4, 'Someone', 'MO-GZ5 Vesna Dossier sabre +1')
      + line(T + 5, 'Scout Alt', '8WA-Z6 Vesna Dossier vedmak')
      + line(T + 6, 'Someone', 'New Caldari Jita jita blorp zzt')
      + line(T + 7, 'Gate Watcher', '5BTK-M Seren Ketter (Sabre) Kirra Longtail loki')
      + line(T + 8, 'Gate Watcher', 'inside 3-DMQT ess loki and curse Seren Ketter (Curse) Kirra Longtail (Loki)'))   # v.99: the shape of the owner's report
    tick(pg, 3200)
    pairs = pg.evaluate("() => Object.fromEntries(it.feed.map(e => [e.raw, [...e.pairs].map(([id, s]) => [e.pilots.find(x => x.id === id).name, s.name])]))")
    want = {LONG: [], 'Anouk Morrow (Scimitar) jumped QX-L from 4K-TRB': [['Anouk Morrow', 'Scimitar']], 'Y-OMTZ Seren Ketter Kirra Longtail sabre': [],
            'D-W7F0 Marrek Ketter vedmak x2': [], 'MO-GZ5 Vesna Dossier sabre +1': [], '8WA-Z6 Vesna Dossier vedmak': [['Vesna Dossier', 'Vedmak']], 'New Caldari Jita jita blorp zzt': [], '5BTK-M Seren Ketter (Sabre) Kirra Longtail loki': [['Seren Ketter', 'Sabre']],
            'inside 3-DMQT ess loki and curse Seren Ketter (Curse) Kirra Longtail (Loki)': [['Seren Ketter', 'Curse'], ['Kirra Longtail', 'Loki']],
            'T5ZI-S* Kirra Longtail* loki': [['Kirra Longtail', 'Loki']]}   # the setup's line already in the log: one pilot, one ship
    check(pairs == want, f'pairing: "Pilot (Ship)" (also beside another pilot and ship); one pilot + one ship; none for two pilots, x2 or +N {pairs}')
    r = near_row(pg, '8WA-Z6')
    check(r == ['8WA-Z6', '5 hostile', 'Marrek Ketter, Vesna Dossier +3 · Sabre, Vedmak ×2, Loki', True],
          f'Near You keeps everyone until a clear: two lines about 8WA-Z6 add up, the Vedmak once at ×2 {r}')
    gone = pg.evaluate("() => { const st = it.near.get(it.names.byLower.get('8wa-z6')); const L = itLive(st, Date.now() + 16 * 60000); return [L.pilots.length, L.ships.length, L.extra]; }")
    check(gone == [0, 0, 0], f'the time set drops old names and ships {gone}')
    # ---- a pilot link in the Feed: paired ----
    btn = pg.evaluate("() => { const r = [...document.querySelectorAll('#intelPanel .it-fd')].find(f => f.querySelector('.raw').textContent.endsWith('8WA-Z6 Vesna Dossier vedmak')); const c = r.querySelector('button.it-chip.p'); return [c.tagName, c.querySelector('.nm').textContent, c.title]; }")
    check(btn == ['BUTTON', 'Vesna Dossier', 'Neutral (Standings). Open Vesna Dossier in the Pilot Analyzer, in the Vedmak reported with them'], f'a pilot in the Feed is a button, its title names the paired ship {btn}')
    pg.evaluate("() => [...document.querySelectorAll('#intelPanel .it-fd')].find(f => f.querySelector('.raw').textContent.endsWith('8WA-Z6 Vesna Dossier vedmak')).querySelector('button.it-chip.p').click()")
    pa_done(pg)
    got = pg.evaluate("() => [getComputedStyle(document.querySelector('#tabPilot')).display, document.querySelector('#pilotName').value, document.querySelector('#manualShip').value, document.querySelector('#pilotFromIntel').hidden, document.querySelector('#pilotFromIntel').textContent]")
    check(got[:4] == ['block', 'Vesna Dossier', 'Vedmak', False] and re.match(r'From Intel · Vesna Dossier reported in a Vedmak at 8WA-Z6 \(1 jump\) · \d+ s ago← Back to Intel$', got[4]),
          f'a paired pilot: the Pilot Analyzer in the Vedmak, the From Intel line {got}')
    sel = pg.evaluate("() => [...document.querySelectorAll('#pilotDossier button.pd-row.sel .pd-hull')].map(e => e.textContent)")
    check(len(sel) == 1 and sel[0].startswith('Vedmak'), f'the dossier on the Vedmak {sel}')
    pg.click('#pilotFromIntel [data-fi-act="back"]'); pg.wait_for_timeout(200)
    check(pg.evaluate("() => getComputedStyle(document.querySelector('#tabIntel')).display") == 'block', 'Back to Intel')
    # unpaired: Marrek Ketter in the long line
    pg.evaluate(f"() => [...document.querySelectorAll('#intelPanel .it-fd')].find(f => f.querySelector('.raw').textContent.endsWith({json.dumps(LONG)})).querySelector('button.it-chip.p').click()")
    pa_done(pg)
    got = pg.evaluate("() => [document.querySelector('#pilotName').value, document.querySelector('#manualShip').value, document.querySelector('#pilotFromIntel').textContent]")
    check(got[:2] == ['Marrek Ketter', ''] and got[2].startswith('From Intel · Marrek Ketter reported at 8WA-Z6 (1 jump)'), f'an unpaired pilot: no ship, the dossier picks {got}')
    pg.fill('#pilotName', 'Kirra Longtail'); pg.fill('#manualShip', ''); pg.click('#fitBtn'); pa_done(pg)
    check(pg.evaluate("() => document.querySelector('#pilotFromIntel').hidden"), 'another pilot analyzed by hand: the From Intel line goes')
    pg.click('#tabBtnIntel'); pg.wait_for_timeout(200)
    nm = pg.evaluate("() => { const r = [...document.querySelectorAll('#intelPanel .it-nb')].find(x => x.querySelector('.sys').textContent === 'QX-LIJ'); const b = r.querySelector('button.it-pl'); return [b.textContent, b.title]; }")
    check(nm == ['Anouk Morrow', 'Neutral (Standings). Open Anouk Morrow in the Pilot Analyzer, in the Scimitar reported with them'], f'Near You: names are links, with the pairing {nm}')
    pg.evaluate("() => [...document.querySelectorAll('#intelPanel .it-nb')].find(x => x.querySelector('.sys').textContent === 'QX-LIJ').querySelector('button.it-pl').click()"); pa_done(pg)
    got = pg.evaluate("() => [document.querySelector('#pilotName').value, document.querySelector('#manualShip').value]")
    check(got == ['Anouk Morrow', 'Scimitar'], f'a Near You name opens that pilot in the paired ship {got}')
    # ---- Assess ----
    pg.click('#tabBtnDscan'); pg.fill('#localInput', 'Old Paste Pilot'); pg.fill('#dscanInput', 'Ferox'); pg.click('#tabBtnIntel'); pg.wait_for_timeout(200)
    M.ZKB_CALLS.clear()
    pg.click('[data-it-assess="%d"]' % SYSID['8WA-Z6']); sa_done(pg, 2)
    got = pg.evaluate("() => [getComputedStyle(document.querySelector('#tabDscan')).display, document.querySelector('#localInput').value, document.querySelector('#dscanInput').value, document.querySelector('#saFromIntel').textContent]")
    check(got[:3] == ['block', 'Marrek Ketter\nVesna Dossier', 'Sabre\nVedmak\nVedmak\nLoki'], f'Assess: the System Analyzer with the pilots as Local and the ships as D-Scan {got[:3]}')
    check(got[3] == 'From Intel · 8WA-Z6 (1 jump), reported in the last 15 min: 2 pilots +3 unnamed, 4 ships (Vesna Dossier in the Vedmak) · your own Local and D-Scan paste was replacedRestore my paste← Back to Intel',
          f'the From Intel line {got[3]!r}')
    rows = pg.evaluate(SA_ROWS)
    vd = next((x for x in rows if x[0] == 'Vesna Dossier'), None); mk = next((x for x in rows if x[0] == 'Marrek Ketter'), None)
    check(vd and vd[1] == 'Vedmak' and re.match(r'reported in it on Intel, \d+ min ago|reported in it on Intel, just now', vd[2]) and mk and 'Intel' not in mk[2],
          f"Intel's pairing is her possible ship; Marrek by the old rule {rows}")
    pg.click('#saFromIntel [data-fi-act="restore"]'); pg.wait_for_timeout(200)
    got = pg.evaluate("() => [document.querySelector('#localInput').value, document.querySelector('#dscanInput').value, document.querySelector('#saFromIntel').hidden, sa.intel]")
    check(got == ['Old Paste Pilot', 'Ferox', True, None], f'Restore my paste {got}')
    pg.click('#tabBtnIntel'); pg.click('#tabBtnDscan'); pg.click('#saClearBtn'); pg.click('#tabBtnIntel')
    pg.click('[data-it-assess="%d"]' % SYSID['QX-LIJ']); pg.wait_for_timeout(500)
    got = pg.evaluate("() => [document.querySelector('#saFromIntel').textContent, !!document.querySelector('#saFromIntel [data-fi-act=restore]')]")
    check(got[0].startswith('From Intel · QX-LIJ (4 jumps), reported in the last 15 min: 1 pilot, 1 ship (Anouk Morrow in the Scimitar)') and not got[1], f'no paste of your own: no Restore {got}')
    pg.type('#localInput', 'x'); pg.wait_for_timeout(200)
    check(pg.evaluate("() => [document.querySelector('#saFromIntel').hidden, sa.intel]") == [True, None], 'typing in the boxes ends it')
    pg.click('#tabBtnIntel')
    W(pg, F_INTEL, line(time.time(), 'Scout Alt', '8WA-Z6 clr')); tick(pg)
    r = near_row(pg, '8WA-Z6')
    check(r == ['8WA-Z6', 'clear', 'reported clear by Scout Alt', False], f'a clear empties the system; no Assess on it {r}')
    W(pg, F_INTEL, line(time.time(), 'Scout Alt', '8WA-Z6 Kirra Longtail')); tick(pg)
    r = near_row(pg, '8WA-Z6')
    check(r == ['8WA-Z6', '1 neutral', 'Kirra Longtail', True], f'after the clear a report starts again {r}')
    # ---- v.99 (the owner's report: "ESS refers to the Encounter Surveillance System"): place words never become pilots; a ship
    # named on its own and again in brackets after a pilot counts once
    ess = pg.evaluate(FEED_ONE, 'inside 3-DMQT ess loki and curse Seren Ketter (Curse) Kirra Longtail (Loki)')
    check(ess == [['sys', '3-DMQT 2 Jumps'], ['h', 'Seren Ketter'], ['n', 'Kirra Longtail'], ['ship', 'Loki'], ['ship', 'Curse'], ['kw', 'ESS']],
          f'"inside ... ess": no pilot "Inside" or "ESS" (real characters have those names); Loki and Curse once each, paired {ess}')
    # ---- the Feed keeps the time set (the owner: "drop entries older than 15 minutes") ----
    n0 = pg.evaluate("() => document.querySelectorAll('#intelPanel .it-fd').length")
    pg.evaluate("() => { const e = it.feed.find(x => x.raw === 'D-W7F0 Marrek Ketter vedmak x2'); e.t -= 16 * 60000; itRender(true); }")
    feed = pg.evaluate("() => [document.querySelectorAll('#intelPanel .it-fd').length, [...document.querySelectorAll('#intelPanel .it-fd .raw')].some(r => r.textContent.endsWith('D-W7F0 Marrek Ketter vedmak x2')), document.querySelector('#intelPanel .it-cols > div:last-child .it-h .ctx').textContent]")
    check(feed == [n0 - 1, False, 'last 15 min, reports and kills'], f'the Feed drops a line older than 15 minutes {feed} (was {n0})')
    W(pg, F_INTEL, line(time.time(), 'Scout Alt', 'T5ZI-S Kirra Longtail')); tick(pg)
    check(pg.evaluate("() => !it.feed.some(x => x.raw === 'D-W7F0 Marrek Ketter vedmak x2')"), 'and lets it go from memory with the next line')
    # ---- copy shape ----
    def shape(raw):
        pg.evaluate(f"() => [...document.querySelectorAll('#intelPanel .it-fd')].find(f => f.querySelector('.raw').textContent.endsWith({json.dumps(raw)})).querySelector('[data-it-shape]').click()")
        pg.wait_for_timeout(300)
        return pg.evaluate("() => navigator.clipboard.readText()"), pg.evaluate("() => (document.querySelector('#intelPanel .it-toast code') || {}).textContent")
    want = {LONG: 'SYS* PILOT* PILOT +3 sabre vedmak x2 loki  [read: 1 system, 2 pilots, +3, 4 ships]',
            'Anouk Morrow (Scimitar) jumped QX-L from 4K-TRB': 'PILOT (scimitar) jumped SYS from SYS  [read: 2 systems, 1 pilot, 1 ship, jumped, 1 paired]',
            'New Caldari Jita jita blorp zzt': 'SYS SYS WORD WORD WORD  [read: 2 systems, 0 pilots, 0 ships, 3 not placed]'}
    names = [v[0] for v in M.PILOTS.values()] + list(REAL.values())
    for raw, w in want.items():
        clip, toast = shape(raw)
        leak = [n for n in names if n.lower() in clip.lower()]
        check(clip == w and toast == w and not leak, f'copy shape: {clip!r} (toast {toast == w}, names in it {leak})')
    pg.screenshot(path='/tmp/intel98_1440.png', full_page=True)
    ctx.close()
    # ---- phone ----
    ctx, pg = start(390)
    W(pg, F_INTEL, line(time.time(), 'Scout Alt', LONG)); tick(pg, 3200)
    pg.click('#itFeedList [data-it-raw]'); pg.wait_for_timeout(200)   # v.100: the copy button is in the strip a toggle opens
    sz = pg.evaluate("() => { const a = document.querySelector('[data-it-assess]').getBoundingClientRect(), t = document.querySelector('#itFeedList [data-it-raw]').getBoundingClientRect(), b = document.querySelector('#itFeedList .it-fd.open [data-it-shape]'), s = b.getBoundingClientRect(); return [Math.round(a.height), Math.round(t.width), Math.round(t.height), Math.round(s.width), Math.round(s.height), +getComputedStyle(b).opacity >= 0.6]; }")
    check(sz[0] >= 40 and sz[1] >= 36 and sz[2] >= 32 and sz[3] >= 36 and sz[4] >= 36 and sz[5], f'390 px: Assess 40 px, the toggle 36 x 32 px, the copy button 36 px and shown {sz}')
    over = pg.evaluate("() => [document.documentElement.scrollWidth, [...document.querySelectorAll('#intelPanel *')].filter(e => { const r = e.getBoundingClientRect(); return r.width && (r.right > innerWidth + 1 || r.left < -1); }).map(e => e.className || e.tagName).slice(0, 5)]")
    check(over[0] <= 390 and not over[1], f'390 px: nothing off the page {over}')
    pg.screenshot(path='/tmp/intel98_390.png', full_page=True)
    ctx.close()
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f"FAILURES: {NS['fails']}")
sys.exit(1 if NS['fails'] else 0)
