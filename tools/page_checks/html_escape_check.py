"""Text from outside the page is escaped for where it goes: quote marks too, in every attribute (v2026.11.07.2, build queue 021;
Project doc roadmap/sso-security-review.md "Present today: quote marks aren't escaped in attributes"; LESSON #144).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/html_escape_check.py [index.html]   -> 'FAILURES: N' (must be 0)

Before, escapeHtml left " and ', so a fit name with a " in it closed a title="..." and added its own attributes (an onmouseover
included); a fit saved in My Fits did it again on every load. Made-up text only, no network (ESI, zKillboard and R2Z2 are the
page checks' stand-ins; everything else refused). The marker "'><b data-pwn=TAG>x</b> adds a data-pwn attribute or element
wherever text gets out of its place; it runs nothing. Checks:
  * the marker through every route the review found or tried: Intel (pilot names, corporation and alliance names and tickers
    from ESI, a report's text and its reporter) and the Fleet tab opened from that kill; the Fit Analyzer (the fit's name, a module
    line, a cargo line); My Fits (the name, after a save and after a reload); Local; D-Scan (ship and structure names);
    a #pilotname= link. Nothing with data-pwn anywhere, and the marker shown as text where the page shows that text;
  * a fit named with an onmouseover in it, saved in My Fits: hovering every row and switch runs nothing;
  * escaped once, never twice: a made-up pilot "Kiera O'Brien" in "O'Brien & Sons Corp" [O'B&S], and a fit "O'Brien & Sons brawl":
    no attribute and no visible text holds a literal &#39; &quot; &amp; &lt; or &gt;, while the names are on the page as written;
  * escapeHtml itself: & < > " ' escaped, null and undefined give '', other values their String() (as the old one did);
  * no page errors.
v2026.11.07.1 fails (data-pwn in the Fit Analyzer, My Fits, Local, Intel's group buttons and the Fleet tab).
"""
import sys, os, re, json, time, pathlib
HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda t: '"\'><b data-pwn=' + t + '>x</b>'
SCAN = """() => [...document.querySelectorAll('[data-pwn]')].map(e => { const p = e.tagName === 'B' ? e.parentElement : e;
  return e.tagName + ' ' + (e.getAttribute('data-pwn') || '').slice(0, 8) + ' in ' + p.tagName + '.' + String(p.className).split(' ').filter(Boolean).join('.') + ' #' + ((p.closest('[id]') || {}).id || ''); })"""
# escaped twice: a literal entity in an attribute a person reads or the page reads back, or in the visible text
TWICE = r"""() => { const rx = /&(#39|#039|quot|amp|lt|gt);/, out = [];
  for(const e of document.querySelectorAll('body *')){
    // data-it-cap holds HTML kept for a later innerHTML: entities in it are that HTML's own, escaped once
    for(const a of e.attributes){ if(/^(style|class|id|src|href|d|viewBox|points|transform|data-it-cap)$/.test(a.name)) continue; if(rx.test(a.value)) out.push(e.tagName + '.' + String(e.className).split(' ')[0] + ' @' + a.name + ': ' + a.value.slice(0, 80)); }
  }
  const t = document.body.innerText; const m = t.match(new RegExp('.{0,30}' + rx.source + '.{0,30}', 'g')); if(m) out.push(...m.map(x => 'text: ' + x));
  return out; }"""
SHOWN = """(keys) => { const t = document.body.innerText; const A = [...document.querySelectorAll('body *')].flatMap(e => [...e.attributes].map(a => a.value)).join('\\n');
  return keys.filter(k => t.includes('data-pwn=' + k) || A.includes('data-pwn=' + k)); }"""   # on the page, as text or in an attribute (a hover)
ATTR_HAS = """(s) => [...document.querySelectorAll('body *')].some(e => [...e.attributes].some(a => a.value.includes(s)))"""

# ---------------- part 1: Intel and the Fleet tab (intel_kills_check.py's start: made-up logs and kills, stand-ins) ----------------
_src = open(os.path.join(HERE, 'intel_kills_check.py'), encoding='utf-8').read()
_src = _src[:_src.index("    # ---- v2026.10.29.3: the Feed's kill range")]
_src = _src.replace("os.path.dirname(os.path.abspath(__file__))", repr(HERE), 1)
_ns = {'__file__': os.path.join(HERE, 'intel_kills_check.py'), '__name__': 'intel_kills_prefix'}
_tail = r'''
    import time as _t
    print('---- html_escape_check: Intel and the Fleet tab ----')
    P = lambda t: '"\'><b data-pwn=' + t + '>x</b>'
    MC, MA, OB = 98000090, 99000090, 98000091   # made-up groups: two with the marker, one with ' and &
    M.ORGS[MA] = ('alliance', 'Ally' + P('aname'), 'A' + P('atick'), None)
    M.ORGS[MC] = ('corporation', 'Corp' + P('cname'), 'T' + P('ctick'), MA)
    M.ORGS[OB] = ('corporation', "O'Brien & Sons Corp", "O'B&S", None)
    PA, PV, PK = 93000001, 93000002, 93000003
    M.PILOTS[PA] = ('Atk' + P('pname'), MC); M.PILOTS[PV] = ('Vic' + P('vname'), MC); M.PILOTS[PK] = ("Kiera O'Brien", OB)
    for i in (PA, PV, PK): M.NAME_ID[M.PILOTS[i][0].lower()] = i
    n0 = max([SEQ['last']] + list(REC)) + 1
    K1 = km(9200501, '8WA-Z6', 20, M.aff(PV), 'Rifter', [(M.aff(PA), 'Sabre'), (M.aff(PK), 'Vedmak')], 5e6)
    K2 = km(9200502, '8WA-Z6', 15, M.aff(PK), 'Stabber', [(M.aff(PA), 'Sabre')], 7e6)
    for k in (K1, K2): M.KM[k['killmail_id']] = k['esi']; M.H[k['killmail_id']] = k['hash']
    REC[n0] = K1; REC[n0 + 1] = K2; SEQ['last'] = n0 + 1
    W(pg, F_INTEL, line(_t.time() - 5, 'Gate Watcher', '8WA-Z6 hostiles ' + P('msg')) + line(_t.time() - 4, 'Scout" data-pwn=who x="', 'T5ZI-S +2')
      + line(_t.time() - 3, 'Gate Watcher', "MO-GZ5 Kiera O'Brien Stabber"))
    for _ in range(90):
        if pg.evaluate("() => it.feed.filter(e => e.kind === 'kill' && e.kill && (e.kill.id === 9200501 || e.kill.id === 9200502)).length") == 2: break
        pg.wait_for_timeout(500)
    pg.wait_for_timeout(2500); pg.evaluate("() => { it.lastHtml = null; itRender(true); }"); pg.wait_for_timeout(800)
    pg.evaluate("() => { it.set.feed = Object.assign({}, it.set.feed, {types: 'all', dist: 0}); it.q = ''; it.fl = []; it.lastHtml = null; itRender(true); }"); pg.wait_for_timeout(800)   # every row
    pg.evaluate("() => { for(const e of it.feed) it.rawOpen.add(e.id); itRenderLists(); }"); pg.wait_for_timeout(800)   # every line as typed, shown
    inmodel = pg.evaluate("() => ['data-pwn=msg', 'data-pwn=who'].map(k => it.feed.some(e => JSON.stringify(e).includes(k)))")
    hits = pg.evaluate(SCAN); shown = pg.evaluate(SHOWN, ['msg', 'who', 'pname', 'vname'])
    check(all(inmodel), f'... the report and its reporter read into the Feed {inmodel}')
    check(not hits and len(shown) == 4, f'Intel: the marker in a report, its reporter, pilot, corporation and alliance names and tickers stays text {sorted(set(hits))[:6]} shown {shown}')
    tw = pg.evaluate(TWICE); ob = pg.evaluate("() => [document.body.innerText.includes(\"Kiera O'Brien\"), [...document.querySelectorAll('#intelPanel [title]')].some(e => e.title.includes(\"O'Brien & Sons Corp\"))]")
    check(not tw and all(ob), f"Intel: Kiera O'Brien and O'Brien & Sons Corp as written, nothing escaped twice {tw[:4]} {ob}")
    # the Fleet tab, from the 8WA-Z6 kills' badge in Near You
    pg.evaluate("() => itOpenKills(it.feed.filter(x => x.kind === 'kill' && x.kill && (x.kill.id === 9200501 || x.kill.id === 9200502)))")
    pg.wait_for_timeout(6000)
    fk = pg.evaluate("() => { const t = (document.querySelector('#fleetPanel') || document.body).innerText; return [t.includes('data-pwn=vname'), t.includes(\"Kiera O'Brien\")]; }")
    hits = pg.evaluate(SCAN); tw = pg.evaluate(TWICE)
    check(all(fk) and not hits, f'the Fleet tab, from those kills: their pilots listed, the marker text only {fk} {sorted(set(hits))[:6]}')
    check(not tw, f'... nothing escaped twice {tw[:4]}')
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
'''
_ns.update(SCAN=SCAN, SHOWN=SHOWN, TWICE=TWICE)
exec(compile(_src + _tail, 'html_escape_check.py (Intel)', 'exec'), _ns)
NS = _ns['NS']; check = _ns['check']; M = _ns['M']

# ---------------- part 2: the Fit Analyzer, My Fits, Local, D-Scan, #pilotname= ----------------
from playwright.sync_api import sync_playwright
PAGE = pathlib.Path(os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', '..', 'index.html'))).as_uri()
FIT = f"[Rifter, Fit{P('eftname')}]\n200mm AutoCannon II\nGyrostabilizer II\nUnknown Module{P('eftmod')}\n\n1MN Afterburner II\n\nEMP S x100\nThing{P('eftcargo')} x3\n"
RUN = '[Rifter, Brawl" onmouseover="window.__ran=1" x="]\n200mm AutoCannon II\n'
OBF = "[Rifter, O'Brien & Sons brawl]\n200mm AutoCannon II\n"
def router(ctx):
    ctx.route(re.compile(r'https://esi\.evetech\.net/.*'), M.esi)
    ctx.route(re.compile(r'https://zkillboard\.com/.*'), M.zkb)
    ctx.route(re.compile(r'https://(?!esi\.evetech\.net|zkillboard\.com).*'), lambda r: r.abort())
print('---- html_escape_check: the Fit Analyzer, My Fits, Local, D-Scan, #pilotname= ----')
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 1440, 'height': 1000}); router(ctx); errs = []
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(PAGE); pg.wait_for_function("() => typeof escapeHtml === 'function' && typeof switchTab === 'function'"); pg.wait_for_timeout(1500)
    # escapeHtml itself
    eh = pg.evaluate(r"""() => [escapeHtml('a"b\'c<d>&e'), escapeHtml(null), escapeHtml(undefined), escapeHtml(0), escapeHtml(12), escapeHtml(false), escapeHtml('')]""")
    check(eh == ['a&quot;b&#39;c&lt;d&gt;&amp;e', '', '', '0', '12', 'false', ''], f'escapeHtml: & < > " \' escaped; null and undefined give \'\', other values their String() {eh}')
    # the Fit Analyzer
    pg.evaluate("() => switchTab('fit')"); pg.fill('#fitAnalyzerInput', FIT); pg.click('#fitAnalyzerBtn')
    pg.wait_for_timeout(500); pg.wait_for_function("() => !document.querySelector('#fitAnalyzerResults .fit-card-busy')", timeout=60000); pg.wait_for_timeout(1500)
    hits = pg.evaluate(SCAN); shown = pg.evaluate(SHOWN, ['eftname'])
    check(not hits and shown, f'the Fit Analyzer: the fit\'s name, a module line and a cargo line stay text {sorted(set(hits))[:6]} shown {shown}')
    pg.fill('#fitAnalyzerInput', OBF); pg.click('#fitAnalyzerBtn'); pg.wait_for_timeout(500)
    pg.wait_for_function("() => !document.querySelector('#fitAnalyzerResults .fit-card-busy')", timeout=60000); pg.wait_for_timeout(1500)
    tw = pg.evaluate(TWICE); ok = pg.evaluate("() => document.body.innerText.includes(\"O'Brien & Sons brawl\")") and pg.evaluate(ATTR_HAS, "O'Brien & Sons brawl")
    check(not tw and ok, f"... a fit named O'Brien & Sons brawl as written, in the text and its titles, nothing escaped twice {tw[:4]} {ok}")
    # My Fits: the marker, and a name with an onmouseover in it; saved, then the page loaded again
    def save_fit(text):
        pg.evaluate("() => openMyShipPanel(undefined, {})"); pg.wait_for_timeout(500)
        pg.evaluate("() => { const a = document.querySelector('[data-act=\"add\"]'); if(a) a.click(); }"); pg.wait_for_timeout(300)
        pg.fill('#myShipEft', text); pg.evaluate("() => document.querySelector('[data-act=\"save\"]').click()"); pg.wait_for_timeout(3000)
    save_fit(FIT.replace('eftname', 'myname')); save_fit(RUN); save_fit(OBF.replace('brawl', 'kite'))
    def my_fits(when):
        pg.evaluate("() => openMyShipPanel(undefined, {})"); pg.wait_for_timeout(800)
        for el in pg.query_selector_all('#myShipPanel button, #myShipPanel .mys-switch-host, .mys-switch-host, .mys-row-main'):
            try: el.hover(timeout=500)
            except Exception: pass
        n = pg.evaluate("() => document.querySelectorAll('#myShipPanel .mys-row-main').length")
        hits = pg.evaluate(SCAN); ran = pg.evaluate("() => window.__ran"); shown = pg.evaluate(SHOWN, ['myname'])
        check(n >= 3 and not hits and ran is None and shown, f'My Fits ({when}): {n} fits, the marker text only, hovering every row ran nothing {sorted(set(hits))[:6]} ran {ran} shown {shown}')
        tw = pg.evaluate(TWICE)
        check(not tw and pg.evaluate("() => document.body.innerText.includes(\"O'Brien & Sons kite\")"), f"... O'Brien & Sons kite as written, nothing escaped twice {tw[:4]}")
        pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    my_fits('after a save')
    pg.reload(); pg.wait_for_function("() => typeof switchTab === 'function'"); pg.wait_for_timeout(2500)
    hits = pg.evaluate(SCAN); ran = pg.evaluate("() => window.__ran")
    check(not hits and ran is None, f'... the page loaded again with those fits saved: nothing out of place on load {sorted(set(hits))[:6]} ran {ran}')
    my_fits('after a reload')
    # Local and D-Scan
    pg.evaluate("() => switchTab('dscan')"); pg.wait_for_timeout(300)
    pg.fill('#localInput', f"Bad{P('local')}\nKiera O'Brien\nTest Pilot\n")
    pg.fill('#dscanInput', f"587\tShip{P('dsname')}\tRifter\t1,234 km\n35832\tCitadel{P('dsstruct')}\tAstrahus\t-\n")
    pg.click('#analyzeBtn'); pg.wait_for_timeout(7000)
    hits = pg.evaluate(SCAN); shown = pg.evaluate(SHOWN, ['local'])
    check(not hits and shown, f'Local and D-Scan: a pasted name, ship and structure names stay text {sorted(set(hits))[:6]} shown {shown}')
    tw = pg.evaluate(TWICE); ob = [pg.evaluate("() => document.body.innerText.includes(\"Kiera O'Brien\")"), pg.evaluate(ATTR_HAS, "O'Brien & Sons Corp") or pg.evaluate("() => document.body.innerText.includes(\"O'Brien & Sons Corp\")")]
    check(not tw and all(ob), f"... Kiera O'Brien and her corporation as written, nothing escaped twice {tw[:4]} {ob}")
    # a #pilotname= link
    pn = '#pilotname=' + ''.join('%%%02X' % ord(c) if c in ' "\'<>' else c for c in 'Bad' + P('link'))
    pg2 = ctx.new_page(); pg2.on('pageerror', lambda e: errs.append(str(e)[:160])); pg2.goto(PAGE + pn); pg2.wait_for_timeout(4000)
    hits = pg2.evaluate(SCAN)
    check(not hits, f'a #pilotname= link with the marker: nothing out of place {sorted(set(hits))[:6]}')
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f"FAILURES: {NS['fails']}")
sys.exit(1 if NS['fails'] else 0)
