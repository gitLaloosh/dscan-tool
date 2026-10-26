"""A hull's ship class beside its name (v2026.10.14.74; the owner: "need to add something to tell the user what class a hull
is in. if they dont know the hulls from memory, knowing the ship class would be nice", then option A of the mockup:
muted text beside every hull name).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/ship_class_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The class is the hull's SDE group name. This check reads it from the SDE itself (pyfa's dump) and compares it with the
page, with zKillboard and ESI mocked as in last_kill_check.py (Test Pilot's losses: Loki x2, Curse, Vedmak, Leshak; a last
kill in a Vedmak on a Curse with seven other attackers):
  * Pilot Analyzer: the hull button ("Loki Strategic Cruiser"), every row of the hull menu, the button after picking
    another hull, the Last Kill line (both ships), and each attacker's ship as a hover (its column has no room);
  * Fit Analyzer: the name line ("Megathron Battleship — ..."); with a ship saved: the Matchup board's threat and your
    ship (menu summary, its invisible twin, every menu row) and the "Viewing my ship" banner;
  * the name and the class are two words in the text (a screen reader, a copy);
  * a group that ESI can't return: no class, no error, the name still shown;
  * 1440, 390 and 320 px: no sideways scroll, the hull button and every menu row on one line.
v2026.10.14.73 fails (no class anywhere).
"""
import sys, os, re, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
# zKillboard / ESI mocks from last_kill_check.py, without running that check (only its part before the checks).
_src = open(os.path.join(HERE, 'last_kill_check.py'), encoding='utf-8').read()
_ns = {'__file__': os.path.join(HERE, 'last_kill_check.py'), '__name__': 'last_kill_mocks'}
exec(compile(_src.split('\ndef desktop(b):')[0], 'last_kill_check.py', 'exec'), _ns)
from pyfa_sde import types, groups, _en
from playwright.sync_api import sync_playwright

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
_ns['HTML'] = HTML
R = '#fitAnalyzerResults'
def cls(tid): return _en(groups[str(types[str(tid)]['groupID'])]['groupName'])
def tname(tid): v = types[str(tid)]; return _en(v.get('typeName') or v.get('name'))
MEGATHRON = """[Megathron, Battleship target]
Magnetic Field Stabilizer II
1600mm Steel Plates II

500MN Microwarpdrive II

Neutron Blaster Cannon II, Void L
Neutron Blaster Cannon II, Void L
"""
VEXOR = """[Vexor, Brawl]
Drone Damage Amplifier II
Medium Armor Repairer II

10MN Afterburner II
Stasis Webifier II

Medium Ion Blaster II, Void M

Hammerhead II x5
"""
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok
KM = _ns['KM']
VED, CURSE = KM[9100100]['attackers'][0]['ship_type_id'], KM[9100100]['victim']['ship_type_id']
def filled(pg, sel, tag):
    """wait until every class in `sel` has been looked up (a check, not a crash, when they never are)"""
    try: pg.wait_for_function(f"() => !document.querySelector({json.dumps(sel)})", timeout=20000); pg.wait_for_timeout(200); return True
    except Exception: check(False, f'{tag}: classes never filled in ({sel})'); return False
CLS_OF = "(sel) => [...document.querySelectorAll(sel)].map(e => { const c = e.querySelector('.hull-cls'); return {text: e.textContent.replace(/\\s+/g, ' ').trim(), cls: c ? c.textContent : null, shown: !!c && c.getClientRects().length > 0 && c.getBoundingClientRect().width > 0}; })"

def pilot(b, w):
    tag = f'{w}px pilot'
    ctx, pg, errs = _ns['start'](b, w, 900, w < 500)
    filled(pg, '.hull-pick-btn .hull-cls:not([data-filled])', tag)
    btn = pg.evaluate(CLS_OF, '.hull-pick-btn')[0]
    check(btn['cls'] == cls(29990) and btn['shown'] and btn['text'].startswith('Loki Strategic Cruiser'), f'{tag}: the hull button names the class ({btn["text"]!r})')
    mids = pg.evaluate("() => [...document.querySelectorAll('.hull-pick-btn > span')].filter(e => e.getBoundingClientRect().width > 0).map(e => { const r = e.getBoundingClientRect(); return [r.top + r.height / 2, r.height]; })")
    check(max(m[0] for m in mids) - min(m[0] for m in mids) < 4 and max(m[1] for m in mids) < 24, f'{tag}: the hull button stays one line (name, class, losses, caret: {[[round(x) for x in m] for m in mids]})')
    pg.click('.hull-pick-btn'); pg.wait_for_timeout(200)
    filled(pg, '.hull-menu .hull-cls:not([data-filled])', tag)
    rows = pg.evaluate("() => [...document.querySelectorAll('.hull-menu .candidate-btn')].map(b => ({id: Number(b.dataset.id), cls: (b.querySelector('.hull-cls') || {}).textContent, text: b.textContent.replace(/\\s+/g, ' ').trim(), h: b.getBoundingClientRect().height, fh: b.querySelector('.cfreq').getBoundingClientRect().height}))")
    bad = [r for r in rows if r['cls'] != cls(r['id']) or not r['text'].startswith(f"{tname(r['id'])} {cls(r['id'])}") or r['fh'] > 20]
    check(len(rows) == 4 and not bad, f'{tag}: every hull menu row names its class on one line ({[(r["text"], round(r["fh"])) for r in rows]})')
    if w == 1440:
        pg.locator('.candidate-btn[data-name="Curse"]').click(); _ns['wait_idle'](pg); pg.wait_for_timeout(300)
        btn = pg.evaluate(CLS_OF, '.hull-pick-btn')[0]
        check(btn['cls'] == cls(CURSE) and btn['text'].startswith('Curse Combat Recon Ship'), f'{tag}: picking the Curse, the button follows ({btn["text"]!r})')
    else:
        pg.keyboard.press('Escape')
    lk = pg.evaluate(CLS_OF.replace(".querySelector('.hull-cls')", ".querySelectorAll('.hull-cls')").replace('c ? c.textContent : null', 'c ? [...c].map(x => x.textContent) : null').replace("!!c && c.getClientRects().length > 0 && c.getBoundingClientRect().width > 0", "!!c && [...c].every(x => x.getBoundingClientRect().width > 0)"), '.lk-sum')[0]
    check(lk['cls'] == [cls(VED), cls(CURSE)] and lk['shown'] and f'Vedmak {cls(VED)}' in lk['text'] and f'Curse {cls(CURSE)}' in lk['text'], f'{tag}: the Last Kill line names both classes ({lk["text"]!r})')
    pg.click('.lk-sum'); pg.wait_for_selector('#attackerList .lk-att-row', timeout=30000)
    filled(pg, '.lk-att-ship[data-hull-cls-title]:not([data-filled])', tag)
    att = pg.evaluate("() => [...document.querySelectorAll('.lk-att-ship')].map(e => [e.textContent, e.title])")
    want = [(tname(a['ship_type_id']), cls(a['ship_type_id'])) for a in KM[9100100]['attackers'] if not (a['character_id'] == 90000001)]
    check(sorted(map(tuple, att)) == sorted(want) and 'Vedmak killed a Curse' in pg.inner_text('.lk-title'), f'{tag}: each attacker\'s ship has its class as a hover; the headline is unchanged ({att[:3]}...)')
    pg.keyboard.press('Escape')
    sc = pg.evaluate("[document.documentElement.scrollWidth, innerWidth]")
    check(sc[0] <= sc[1], f'{tag}: no sideways scroll {sc}')
    check(not errs, f'{tag}: no page errors {errs[:2]}')
    ctx.close()

def fit(b, w):
    tag = f'{w}px fit'
    ctx, pg, errs = _ns['start'](b, w, 900, w < 500)
    pg.click('#tabBtnFit')
    pg.fill('#fitAnalyzerInput', MEGATHRON); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout', timeout=60000); pg.wait_for_timeout(300)
    head = pg.evaluate(CLS_OF, f'{R} .mys-fa-head .cmeta')[0]
    check(head['cls'] == cls(641) and head['shown'] and head['text'] == 'Megathron Battleship — Battleship target', f'{tag}: the name line ({head["text"]!r})')
    pg.click('#myShipChip'); pg.fill('#myShipEft', VEXOR); pg.click('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-tiles'); pg.keyboard.press('Escape')
    pg.wait_for_function(f"() => {{ const b = document.querySelector('{R} .mys-board'); return b && !/…/.test(b.textContent); }}", timeout=60000); pg.wait_for_timeout(500)
    th = pg.evaluate(CLS_OF, f'{R} button.mys-half.is-threat .mys-sw-v')[0]
    su = pg.evaluate(CLS_OF, f'{R} details.mys-pick > summary')[0]
    gh = pg.evaluate(CLS_OF, f'{R} .mys-pick-ghost')[0]
    ghc = pg.evaluate(f"() => {{ const e = document.querySelector('{R} .mys-pick-ghost .hull-cls'); return e ? getComputedStyle(e).color : null; }}")
    check(th['text'] == 'Megathron Battleship · Battleship target' and th['shown'], f'{tag}: the board\'s threat ({th["text"]!r})')
    check(su['text'] == 'Vexor Cruiser · Brawl' and su['shown'] and gh['text'] == su['text'] and ghc == 'rgba(0, 0, 0, 0)', f'{tag}: your ship on the board, its menu and the invisible twin ({su["text"]!r} / {gh["text"]!r}, twin colour {ghc})')
    a, g = pg.locator(f'{R} details.mys-pick > summary').bounding_box(), pg.locator(f'{R} .mys-pick-ghost').bounding_box()
    check(abs(a['x'] - g['x']) < 1 and abs(a['width'] - g['width']) < 1 and abs(a['height'] - g['height']) < 1, f'{tag}: the menu still lies on its twin ({a["width"]:.0f}x{a["height"]:.0f} / {g["width"]:.0f}x{g["height"]:.0f})')
    pg.click(f'{R} details.mys-pick > summary'); pg.wait_for_timeout(200)
    opts = pg.evaluate(CLS_OF, f'{R} .mys-pick-opt:not(.mys-pick-manage) .mys-pick-name')
    check(opts and all(o['cls'] == cls(626) for o in opts), f'{tag}: the board\'s ship menu rows ({[o["text"] for o in opts]})')
    pg.keyboard.press('Escape')
    sc = pg.evaluate("[document.documentElement.scrollWidth, innerWidth]")
    check(sc[0] <= sc[1], f'{tag}: no sideways scroll {sc}')
    if w == 1440:
        pg.click('#myShipChip'); pg.click('#myShipPanel [data-act="open"]'); pg.wait_for_selector(f'{R} .mys-banner .mys-banner-v')
        ban = pg.evaluate(CLS_OF, f'{R} .mys-banner-v')[0]
        check(ban['text'] == 'Vexor Cruiser · Brawl' and ban['shown'], f'{tag}: the "Viewing my ship" banner ({ban["text"]!r})')
    check(not errs, f'{tag}: no page errors {errs[:2]}')
    ctx.close()

def no_group(b):
    """ESI can't return the Strategic Cruiser group: the Loki's class is left out, nothing else breaks."""
    gid = types['29990']['groupID']
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    def esi(route):
        if f'/universe/groups/{gid}/' in route.request.url: return route.fulfill(status=404, body='{"error":"Group not found"}')
        return _ns['esi'](route)
    pg.route(re.compile(r'https://esi\.evetech\.net/.*'), esi)
    pg.route(re.compile(r'https://zkillboard\.com/.*'), _ns['zkb'])
    pg.route(re.compile(r'https://(images\.evetech\.net|fonts\.).*'), lambda r: r.fulfill(status=404, body=''))
    pg.goto('file://' + HTML); pg.evaluate("localStorage.removeItem('dscanMyShip')")
    pg.click('#tabBtnPilot'); pg.fill('#pilotName', 'Test Pilot'); pg.click('#fitBtn')
    pg.wait_for_selector('.hull-pick-btn', timeout=60000); pg.wait_for_timeout(1500)
    btn = pg.evaluate(CLS_OF, '.hull-pick-btn')[0]
    pg.click('.hull-pick-btn'); pg.wait_for_timeout(800)
    rows = pg.evaluate(CLS_OF, '.hull-menu .candidate-btn')
    check(btn['text'].startswith('Loki') and not btn['shown'] and rows[1]['cls'] == cls(CURSE) and not errs,
          f'no group from ESI: the Loki shows no class, the Curse still does, no page errors ({btn["text"]!r}; {errs[:1]})')
    ctx.close()

with sync_playwright() as p:
    b = p.chromium.launch(**({'executable_path': _ns['CHROMIUM']} if _ns.get('CHROMIUM') else {}))
    for w in (1440, 390, 320):
        pilot(b, w)
        fit(b, w)
    no_group(b)
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
