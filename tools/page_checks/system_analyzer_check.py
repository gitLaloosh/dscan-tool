"""The System Analyzer, step 1 (v2026.10.14.81; roadmap/local-and-fleet-plan.md L1 + L2, decisions D1-D7).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/system_analyzer_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The real page with ESI and zKillboard answered from made-up data (sa_mocks.py). Every expected count, side and reason is
worked out here, in Python, from the same data -- not read back from the page. Checks:
  * the tab: "System Analyzer" in the D-Scan tab's place (last), two inputs; a D-Scan alone still shows its contacts
    under "On Scan"; Local pasted in the D-Scan box's place (a scan) or a fit refused with SYS-02;
  * Standings (Your Side until v.95; D7 "A: chip by My Ship"): the chip on every tab; your pilot sets corp + alliance (SIDE-01 for an unknown
    name); a friendly added by name; a pasted list (tickers ignored, not-found names named with SIDE-02); adding to one
    list takes a group off the other; pilot rows clamped to 1-30; everything back after a reload;
  * Local: counts per side, groups by alliance then corporation, largest first; a corporation entry beats its alliance
    (a hostile corp inside a friendly alliance); NPC corporations one neutral group; neutral groups of 1-2 folded past 6
    groups; names not found listed; 6 names per corporation then "+N more"; fleet / small gang by the threshold;
  * the zKillboard evidence (D2b): "Killed N of yours in 7 days" from the attackers on your side's losses (friendlies and
    NPCs never count); one zKillboard request, none on a second Analyze (kept an hour), one on Refresh;
  * suggested friendlies: co-attackers on 2+ of your kills, not already listed; Add puts one on the friendly list;
  * the zKillboard queue (D4): requests at least ~1 s apart; past the budget, ZKB-04 instead of a request;
  * a pilot's name opens the Pilot Analyzer, with the Friendly / Hostile tag beside the name;
  * at 390 px nothing runs off the page; no page errors.
v2026.10.14.80 fails (no System Analyzer).
"""
import sys, os, re, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from playwright.sync_api import sync_playwright
import sa_mocks as M

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok

def side_text(pg):
    return pg.evaluate("() => { const c = document.querySelector('#sideChip'); return c ? [...c.children].filter(e => !e.classList.contains('sa-mark') && e.checkVisibility()).map(e => e.innerText).join(' ').replace(/\\s+/g, ' ').trim() : null; }")
def open_side(pg):
    if pg.evaluate("() => document.querySelector('#sidePanel').hidden"): pg.click('#sideChip')
    pg.wait_for_selector('#sidePanel:not([hidden])')
def panel_msg(pg, which):
    return pg.evaluate(f"""() => {{ const f = document.querySelector('#sidePanel [data-side-list="{which}"]'); const m = f && f.querySelector('.side-msg'); return m ? m.textContent : ''; }}""")
def chips(pg, which):
    return pg.evaluate(f"""() => [...document.querySelectorAll('#sidePanel [data-side-list="{which}"] .side-chips > span .nm')].map(e => e.textContent)""")
def wait_idle(pg):
    pg.wait_for_function("() => document.querySelector('#saBusy').hidden && !document.querySelector('#analyzeBtn').disabled", timeout=60000); pg.wait_for_timeout(300)
def analyze(pg, local, scan=''):
    pg.click('#tabBtnDscan'); pg.fill('#localInput', local); pg.fill('#dscanInput', scan); pg.click('#analyzeBtn'); pg.wait_for_timeout(300); wait_idle(pg)
RESULT = """() => {
  const col = (k) => { const c = document.querySelector(`.sa-col[data-sa-col="${k}"]`); if(!c) return null;
    return {n: +c.querySelector('.sa-n').textContent, groups: [...c.querySelectorAll(':scope > details.sa-g')].map(d => ({
      name: d.querySelector('.nm').childNodes[0].textContent.trim(), tk: (d.querySelector('.nm .tk') || {}).textContent || '', n: +d.querySelector('.sa-gn').textContent,
      why: (d.querySelector('.sa-why') || {}).textContent || '', sub: (d.querySelector('.sa-gname .ctx') || {}).textContent || '',
      corps: [...d.querySelectorAll('.sa-corp')].map(c => [c.querySelector('span').textContent.trim(), +c.querySelector('.c').textContent]),
      pilots: [...d.querySelectorAll('.sa-pilots')].map(p => [[...p.querySelectorAll('button.sa-pilot')].map(b => b.textContent), (p.querySelector('[data-more]') || {}).textContent || ''])}))}; };
  const fr = document.querySelector('details.sa-friendly');
  return {total: +(document.querySelector('.sa-total') || {}).textContent, keys: [...document.querySelectorAll('.sa-key')].map(k => k.textContent.replace(/\\s+/g, ' ').trim()),
    mode: (document.querySelector('.sa-mode') || {}).textContent || '', warns: [...document.querySelectorAll('.sa-warn .warn-title')].map(w => w.textContent),
    nf: (document.querySelector('.sa-warn .ctx') || {}).title || '', h: col('h'), n: col('n'), f: fr ? +fr.querySelector('.sa-gn').textContent : null,
    fgroups: fr ? [...fr.querySelectorAll('.sa-friendly-body > details.sa-g .nm')].map(e => e.childNodes[0].textContent.trim()) : [],
    status: document.querySelector('#localStatus').textContent};
}"""

E = M.expected()   # worked out in Python from the made-up data

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 1440, 'height': 1000})
    errs = []
    ctx.on('page', lambda pg: pg.on('pageerror', lambda e: errs.append(str(e))))
    M.route(ctx)
    pg = ctx.new_page()
    pg.goto('file://' + HTML)
    GROUPS_VIEW = "() => { sa.view = 'groups'; }"   # v.82/.83: this check reads the columns; Pilots / Fleet (and their zKillboard lookups) have their own checks
    pg.evaluate(GROUPS_VIEW)
    pg.wait_for_timeout(300)
    # --- the tab ---
    tabs = pg.evaluate("() => [...document.querySelectorAll('.tabs .tab-btn')].filter(b => b.checkVisibility()).map(b => b.textContent.trim())")   # v.94: the Fleet tab is hidden until a fleet is open
    check(tabs == ['Pilot Analyzer', 'Fit Analyzer', 'System Analyzer', 'Intel'], f'the tabs: System Analyzer in the D-Scan tab\'s place, then Intel (v.96) {tabs}')
    pg.click('#tabBtnDscan')
    ins = pg.evaluate("() => [!!document.querySelector('#localInput'), !!document.querySelector('#dscanInput'), document.querySelector('#tabDscan h2').textContent]")
    check(ins == [True, True, 'System Analyzer'], f'two inputs, the heading from CARD_NAMES {ins}')
    # D-Scan alone: today's contacts under On Scan
    analyze(pg, '', M.SCAN)
    pg.wait_for_function("() => document.querySelectorAll('#resultsGrid > .card').length >= 2", timeout=60000)
    scan = pg.evaluate("() => ({shown: getComputedStyle(document.querySelector('#resultsWrap')).display !== 'none', head: document.querySelector('.sa-onscan-head h2').textContent, cards: [...document.querySelectorAll('#resultsGrid .cname')].map(e => e.textContent), local: document.querySelector('#saResults').innerHTML.trim()})")
    check(scan['shown'] and scan['head'] == 'On Scan' and set(scan['cards']) >= {'Ferox', 'Scimitar'} and scan['local'] == '', f"a D-Scan alone: its contacts under On Scan, no Local result {scan['cards']}")
    # the wrong box
    analyze(pg, M.SCAN)
    st = pg.inner_text('#localStatus')
    check('(SYS-02)' in st and 'D-Scan box' in st, f'a scan in the Local box: SYS-02 ({st!r})')
    analyze(pg, M.FIT)
    st = pg.inner_text('#localStatus')
    check('(SYS-02)' in st and 'Fit Analyzer' in st, f'a fit in the Local box: SYS-02 ({st!r})')
    # --- Local with Standings not set: everyone neutral (no zKillboard request) ---
    M.ZKB_CALLS.clear()
    analyze(pg, M.LOCAL)
    r = pg.evaluate(RESULT)
    check(r['total'] == E['found'] and r['h']['n'] == 0 and r['f'] == 0 and r['n']['n'] == E['found'] and any('Set your Standings' in w for w in r['warns']) and not M.ZKB_CALLS,
          f"Standings not set: all {E['found']} found pilots neutral, a note to set it, no zKillboard request ({r['keys']}, {r['warns']}, {len(M.ZKB_CALLS)})")
    # --- Standings ---
    check(side_text(pg) == 'Standings' and pg.evaluate("() => document.querySelector('#sideChip').classList.contains('is-empty')"), f'the chip, not set: "Standings" ({side_text(pg)!r})')
    for t in ('#tabBtnPilot', '#tabBtnFit'):
        pg.click(t); check(pg.is_visible('#sideChip'), f'the chip shows on {t}')
    open_side(pg)
    pg.fill('#sidePilot', 'Nobody Here'); pg.click('[data-side-act="pilot"]'); pg.wait_for_timeout(500)
    m = pg.evaluate("() => (document.querySelector('#sidePanel .side-msg') || {}).textContent || ''")
    check('(SIDE-01)' in m, f'an unknown pilot: SIDE-01 ({m!r})')
    pg.fill('#sidePilot', 'Test Pilot'); pg.press('#sidePilot', 'Enter'); pg.wait_for_timeout(800)
    res = pg.evaluate("() => (document.querySelector('#sidePanel .side-res') || {}).textContent || ''")
    check('Example Corp' in res and '[EXMPL]' in res and 'Example Alliance' in res and '<EXA>' in res, f'your pilot sets corp + alliance with tickers ({res.strip()!r})')
    # one friendly by name, then a pasted list (tickers ignored, one not found, one already hostile-listed moves)
    pg.fill('[data-side-add="hostile"]', 'Crimson Tide Syndicate'); pg.click('[data-side-act="add:hostile"]'); pg.wait_for_timeout(500)
    pg.fill('[data-side-add="hostile"]', 'Allied Wing'); pg.click('[data-side-act="add:hostile"]'); pg.wait_for_timeout(500)
    pg.fill('[data-side-add="hostile"]', 'Turncoat Corp'); pg.click('[data-side-act="add:hostile"]'); pg.wait_for_timeout(500)
    pg.click('[data-side-act="paste:friendly"]')
    pg.fill('[data-side-paste="friendly"]', 'Blue Coalition Member <BCM>\n[AW] Allied Wing\nNot A Real Group\nExample Alliance')
    pg.click('[data-side-act="addall:friendly"]'); pg.wait_for_timeout(800)
    fr, ho, msg = chips(pg, 'friendly'), chips(pg, 'hostile'), panel_msg(pg, 'friendly')
    check(fr == ['Blue Coalition Member', 'Allied Wing'] and ho == ['Crimson Tide Syndicate', 'Turncoat Corp'] and 'Not A Real Group' in msg and '(SIDE-02)' in msg and 'yours already: Example Alliance' in msg,
          f'a pasted list: tickers ignored, Allied Wing moved off the hostile list, not found named, your own alliance refused ({fr}, {ho}, {msg!r})')
    # remove + re-add Allied Wing via suggestions later: remove it now
    pg.click('[data-side-rm="friendly:alliance:%d"]' % M.ALLIED); pg.wait_for_timeout(200)
    check(chips(pg, 'friendly') == ['Blue Coalition Member'], f"× removes a group ({chips(pg, 'friendly')})")
    # pilot rows clamped
    pg.fill('#sideRows', '99'); pg.press('#sideRows', 'Enter'); pg.wait_for_timeout(200)
    v1 = pg.input_value('#sideRows'); pg.fill('#sideRows', '20'); pg.press('#sideRows', 'Enter'); pg.wait_for_timeout(200)
    check(v1 == '30' and pg.input_value('#sideRows') == '20', f'pilot rows: 99 becomes 30 (the most); 20 kept ({v1}, {pg.input_value("#sideRows")})')
    # suggestions: co-attackers on 2+ of your kills, not listed
    M.ZKB_CALLS.clear()
    pg.click('[data-side-act="suggest"]'); pg.wait_for_function("() => !document.querySelector('#sidePanel .status') || !/Checking/.test(document.querySelector('#sidePanel').textContent)", timeout=30000); pg.wait_for_timeout(500)
    sug = pg.evaluate("() => [...document.querySelectorAll('#sidePanel .side-sug')].map(s => [s.querySelector('.nm').childNodes[0].textContent.trim(), s.querySelector('.ctx').textContent])")
    check(sug == E['suggest'] and len(M.ZKB_CALLS) == 1 and '/kills/allianceID/%d/pastSeconds/604800/' % M.ALLIANCE in M.ZKB_CALLS[0][0],
          f"suggested friendlies = co-attackers on 2+ kills, not listed ({sug} vs {E['suggest']}; {[c[0] for c in M.ZKB_CALLS]})")
    pg.click('[data-side-act="sugadd:alliance:%d"]' % M.ALLIED); pg.wait_for_timeout(300)
    check(chips(pg, 'friendly') == ['Blue Coalition Member', 'Allied Wing'], f"Add puts a suggestion on the friendly list ({chips(pg, 'friendly')})")
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    check(pg.evaluate("() => document.querySelector('#sidePanel').hidden"), 'Escape closes the panel')
    chip = side_text(pg)
    check(chip.startswith('Example Alliance') and '+2 friendly' in chip and '2 hostile' in chip, f'the chip: your alliance, +2 friendly, 2 hostile ({chip!r})')
    # reload: all kept
    pg.reload(); pg.wait_for_timeout(500)
    pg.evaluate(GROUPS_VIEW)
    open_side(pg)
    kept = (chips(pg, 'friendly'), chips(pg, 'hostile'), pg.input_value('#sideRows'), pg.input_value('#sidePilot'))
    check(kept == (['Blue Coalition Member', 'Allied Wing'], ['Crimson Tide Syndicate', 'Turncoat Corp'], '20', 'Test Pilot'), f'everything kept after a reload {kept}')
    pg.keyboard.press('Escape')
    # set the D3 threshold back to 15 for the fleet check
    open_side(pg); pg.fill('#sideRows', '15'); pg.press('#sideRows', 'Enter'); pg.keyboard.press('Escape')
    # --- Local with Standings ---
    M.ZKB_CALLS.clear()
    analyze(pg, M.LOCAL, M.SCAN)
    r = pg.evaluate(RESULT)
    exp_keys = [f"Hostile {E['n']['h']}", f"Neutral {E['n']['n']}", f"Friendly {E['n']['f']}"]
    r['keys'] = [k.lstrip('−+ ') for k in r['keys']]
    check(r['keys'] == exp_keys and r['total'] == E['found'], f"counts per side {r['keys']} vs {exp_keys}")
    hg = [(g['name'], g['n'], g['why']) for g in r['h']['groups']]
    check(hg == E['hostile'], f"hostile groups, largest first, with the reason:\n      page {hg}\n      want {E['hostile']}")
    ng = [(g['name'], g['n']) for g in r['n']['groups']]
    check(ng == E['neutral'], f"neutral groups (NPC corporations one group, smaller groups folded):\n      page {ng}\n      want {E['neutral']}")
    check(r['fgroups'] == E['friendly'] and r['f'] == E['n']['f'], f"friendly line: {r['f']} pilots, groups {r['fgroups']} vs {E['friendly']}")
    crts = next(g for g in r['h']['groups'] if g['name'] == 'Crimson Tide Syndicate')
    check(crts['tk'] == '<CRTS>' and [tuple(c) for c in crts['corps']] == E['crts_corps'] and crts['pilots'][0][0] == E['crts_first6'] and crts['pilots'][0][1] == f"+{E['crts_more']} more",
          f"a group's corporations, 6 names then \"+N more\", the ticker filled ({crts['tk']}, {crts['corps']}, {crts['pilots'][0]})")
    nthreat = E['n']['h'] + E['n']['n']
    check('%d hostile + neutral' % nthreat in r['mode'] and 'Fleet' not in r['mode'] and 'over 15' in r['mode'] and not pg.query_selector('.sa-mode [data-sa-view]'),
          f"over 15 (v.89, the fleet view switched off): '{nthreat} hostile + neutral, over 15: shown by group', no Fleet / Groups switch ({r['mode']!r})")
    check(r['nf'].endswith(', '.join(M.NOT_FOUND)) and any('2 names not found' == w for w in r['warns']), f"names not found listed ({r['warns']}, {r['nf']!r})")
    zl = [c[0] for c in M.ZKB_CALLS]
    check(len(zl) == 1 and '/losses/allianceID/%d/pastSeconds/604800/' % M.ALLIANCE in zl[0], f'the evidence: one zKillboard request, your alliance\'s losses in 7 days {zl}')
    # "+N more" shows the rest
    pg.click('details.sa-g[data-sa-g="h:a%d"] > summary' % M.CRTS); pg.wait_for_timeout(100)
    pg.click('details.sa-g[data-sa-g="h:a%d"] [data-more]' % M.CRTS); pg.wait_for_timeout(200)
    n_all = pg.evaluate("(k) => document.querySelector(`details.sa-g[data-sa-g=\"${k}\"] .sa-pilots`).querySelectorAll('button.sa-pilot').length", 'h:a%d' % M.CRTS)
    check(n_all == E['crts_corps'][0][1], f'"+N more" shows every name ({n_all})')
    # second Analyze: kept an hour, no request; Refresh: one
    M.ZKB_CALLS.clear(); analyze(pg, M.LOCAL)
    n2 = len(M.ZKB_CALLS)
    pg.click('.sa-mode [data-sa-act="refresh"]'); pg.wait_for_timeout(300); wait_idle(pg)
    check(n2 == 0 and len(M.ZKB_CALLS) == 1, f'a second Analyze asks zKillboard nothing (kept an hour); Refresh asks once ({n2}, {len(M.ZKB_CALLS)})')
    # small gang
    analyze(pg, '\n'.join(M.SMALL_LOCAL))
    sw = pg.evaluate("() => [...document.querySelectorAll('.sa-mode [data-sa-view]')].map(b => [b.textContent, b.getAttribute('aria-pressed')])")
    check(sw == [['Pilots', 'false'], ['Groups', 'true']] and not pg.query_selector('#saPilots'), f'small gang in Groups: the columns, no pilot rows looked up {sw}')
    r2 = pg.evaluate(RESULT)
    check('Small gang: %d hostile + neutral' % E['small_threat'] in r2['mode'], f"15 or fewer: small gang ({r2['mode']!r})")
    # --- the queue: spacing and budget ---
    M.ZKB_CALLS.clear()
    pg.evaluate("async () => { await Promise.all(['a', 'b', 'c'].map(x => zkbFetch(`https://zkillboard.com/api/test/${x}/`).catch(() => null))); }")
    ts = [c[1] for c in M.ZKB_CALLS]
    gaps = [round(b - a, 2) for a, b in zip(ts, ts[1:])]
    check(len(ts) == 3 and all(g >= 0.9 for g in gaps), f'the zKillboard queue: one at a time, ~1 s apart {gaps}')
    M.ZKB_CALLS.clear()
    dup = pg.evaluate("async () => { const r = await Promise.all([1, 2].map(() => zkbFetch('https://zkillboard.com/api/test/same/').then(r => r.json()))); return r.length; }")
    check(dup == 2 and len(M.ZKB_CALLS) == 1, f'the same request twice at once is asked once ({len(M.ZKB_CALLS)})')
    pg.evaluate("() => localStorage.setItem('dscanZkbBudget', JSON.stringify(Array.from({length: 100}, () => Date.now())))")
    M.ZKB_CALLS.clear()
    err = pg.evaluate("async () => { try{ await zkbFetch('https://zkillboard.com/api/test/over/'); return 'no error'; }catch(e){ return e.message + ' (' + e.code + ')'; } }")
    check('(ZKB-04)' in err and not M.ZKB_CALLS and 'More in 10 min' in err, f'past 100 in 10 minutes: ZKB-04, no request ({err!r})')
    pg.evaluate("() => localStorage.removeItem('dscanZkbBudget')")
    # --- a pilot's name opens the Pilot Analyzer, tagged ---
    analyze(pg, M.LOCAL)
    pg.click('details.sa-friendly > summary'); pg.wait_for_timeout(100)
    pg.click('details.sa-g[data-sa-g="f:a%d"] > summary' % M.BCM); pg.wait_for_timeout(100)
    pg.click('details.sa-g[data-sa-g="f:a%d"] button.sa-pilot' % M.BCM)
    pg.wait_for_function("() => document.querySelector('#pilotSideTag').textContent.length > 0", timeout=30000)
    tag = pg.evaluate("() => [document.querySelector('#pilotName').value, [...document.querySelectorAll('#pilotSideTag .side-tag > :not(.sa-mark)')].map(e => e.textContent).join(' '), document.querySelector('#tabPilot').style.display]")
    check(tag[1].startswith('Friendly · Blue Coalition Member') and '<BCM>' in tag[1] and tag[2] != 'none', f'a name opens the Pilot Analyzer, tagged Friendly {tag}')
    pg.fill('#pilotName', M.TURNCOAT_PILOT); pg.click('#fitBtn')
    pg.wait_for_function("() => /Hostile/.test(document.querySelector('#pilotSideTag').textContent)", timeout=30000)
    t2 = pg.evaluate("() => [...document.querySelectorAll('#pilotSideTag .side-tag > :not(.sa-mark)')].map(e => e.textContent).join(' ')")
    check('Hostile · your hostile list' in t2, f'a hostile corp inside a friendly alliance: tagged Hostile ({t2!r})')
    # --- phone ---
    pg.set_viewport_size({'width': 390, 'height': 844}); pg.click('#tabBtnDscan'); pg.wait_for_timeout(300)
    over = pg.evaluate("() => [document.documentElement.scrollWidth, [...document.querySelectorAll('#tabDscan *, #sideChip')].filter(e => { const r = e.getBoundingClientRect(); return e.checkVisibility() && r.width && (r.right > innerWidth + 1 || r.left < -1); }).map(e => [e.className || e.tagName, e.parentElement.className, Math.round(e.getBoundingClientRect().left), Math.round(e.getBoundingClientRect().right), e.closest('details') && e.closest('details').open]).slice(0, 5)]")
    check(over[0] <= 390 and not over[1], f'390 px: nothing runs off the page {over}')
    open_side(pg)
    sheet = pg.evaluate("() => { const r = document.querySelector('#sidePanel').getBoundingClientRect(); return [Math.round(r.left), Math.round(r.right), Math.round(r.bottom)]; }")
    check(sheet == [0, 390, 844], f'390 px: Standings is a sheet from the bottom {sheet}')
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
