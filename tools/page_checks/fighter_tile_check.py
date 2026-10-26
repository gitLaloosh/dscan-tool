"""The Weaknesses card's Fighter tile and the collapsible Missile / Fighter tiles (v2026.10.14.73; the owner: "yes please" to
fighters with no ship saved, "let's have those that do multiple rows be able to expand and collapse. default to
collapsed", then "B: names + how much lands" and "Count the bomb").

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/fighter_tile_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The numbers come from estimate.fighterRec, which tools/independent_checks/check_fighter_rec.py checks against the SDE
and pyfa (every golden fit). This checks the tiles built from it, with no ship saved, on four targets (a frigate and a
battleship with an MWD, a cruiser with an afterburner, a frigate with no prop module), at 1440, 390 and 320 px:
  * both tiles start collapsed (aria-expanded false, rows hidden). Fighter: "Fighter · <race>", the three names
    joined by " · ", and "light N% · heavy N% · bomber N%" (each share's one decimal, rounded half up). Missile:
    "N launchers" and "M of N land 95% or more", from the missile ranking with the prop module off;
  * the chevron opens a tile (rows shown, summary hidden) and closes it again; a keyboard Enter does the same;
  * open, the Fighter rows are Light / Heavy / Bomber with each name and % off and on (the prop column only with a
    prop module, headed MWD / AB), amber under 50%, and a hover naming the full type and both percentages (the
    bomber's "its attack and its bomb");
  * the open state belongs to the fit: it survives a re-render (closing and opening the Weaknesses card), and a new
    paste starts collapsed;
  * the card's info names the fighters; no sideways scroll, every row inside its tile, no NaN / undefined, no
    page errors.
v2026.10.14.72 fails (no Fighter tile, the Missile rows always shown).
"""
import sys, os, re, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esi_from_sde import route_all
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
CHROMIUM = os.environ.get('CHROMIUM_PATH') or ('/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') else None)
R = '#fitAnalyzerResults'
FITS = {
    'rifter_mwd': ('mwd', """[Rifter, Frigate target]
Damage Control II
Gyrostabilizer II

5MN Microwarpdrive II
Warp Scrambler II

200mm AutoCannon II, EMP S
200mm AutoCannon II, EMP S
200mm AutoCannon II, EMP S
"""),
    'megathron_mwd': ('mwd', """[Megathron, Battleship target]
Magnetic Field Stabilizer II
1600mm Steel Plates II

500MN Microwarpdrive II

Neutron Blaster Cannon II, Void L
Neutron Blaster Cannon II, Void L
Neutron Blaster Cannon II, Void L
"""),
    'caracal_ab': ('afterburner', """[Caracal, Cruiser target with an afterburner]
Ballistic Control System II

10MN Afterburner II
Medium Shield Extender II

Rapid Light Missile Launcher II, Scourge Light Missile
Rapid Light Missile Launcher II, Scourge Light Missile
Rapid Light Missile Launcher II, Scourge Light Missile
"""),
    'rifter_noprop': (None, """[Rifter, Frigate target without a prop module]
Damage Control II
Gyrostabilizer II

Warp Scrambler II

200mm AutoCannon II, EMP S
200mm AutoCannon II, EMP S
"""),
}
RACE = {'em': 'Amarr', 'therm': 'Gallente', 'kin': 'Caldari', 'exp': 'Minmatar'}
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok
def settle(pg, ms=400):
    pg.wait_for_timeout(ms); pg.wait_for_function("() => !document.querySelector('.fit-card-busy')", timeout=60000); pg.wait_for_timeout(ms)
def paste(pg, text):
    pg.evaluate("() => { const r = document.querySelector('#fitAnalyzerResults'); if(r) r.innerHTML = ''; }")
    pg.fill('#fitAnalyzerInput', text); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout', timeout=60000); settle(pg)
EST = f"""() => {{ const c = [...document.querySelectorAll('{R} .dmg-card')].find(c => c._dmg && c._dmg.side !== 'mine');
  return c ? {{fr: c._dmg.f.estimate.fighterRec, ma: c._dmg.f.estimate.missileApplication, prop: c._dmg.f.estimate.speed.propModType || null}} : null; }}"""
TILES = f"""() => {{ const out = {{}};
  for(const kind of ['missile', 'fighter']){{
    const t = document.querySelector('{R} .weak-generic .rec-stat-' + kind); if(!t){{ out[kind] = null; continue; }}
    const tr = t.getBoundingClientRect(), vis = el => !!el && el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden';
    const tog = t.querySelector('.rec-tog'), rowsBox = t.querySelector('.mis-rows');
    const rows = [...t.querySelectorAll('.mis-row:not(.mis-head)')].map(r => {{ const q = s => r.querySelector(s);
      return {{cls: r.dataset.class || r.dataset.launcher, k: q('.mis-k').textContent, v: q('.mis-v').textContent, p: q('.mis-p').textContent,
        pLow: q('.mis-p').classList.contains('is-low'), bp: q('.mis-bp') ? q('.mis-bp').textContent : null,
        bpLow: q('.mis-bp') ? q('.mis-bp').classList.contains('is-low') : null, hasB: !!q('.mis-b'), title: r.title,
        inside: [...r.children].every(c => {{ const b = c.getBoundingClientRect(); return b.width === 0 || (b.left >= tr.left - 0.5 && b.right <= tr.right + 0.5); }})}}; }});
    const head = t.querySelector('.mis-head');
    const sums = [...t.querySelectorAll('.rec-sum')];
    out[kind] = {{label: t.querySelector('.rec-label').textContent.trim(), expanded: tog && tog.getAttribute('aria-expanded'), open: t.classList.contains('is-open'),
      rowsShown: vis(rowsBox), sumShown: sums.length > 0 && sums.every(vis), sum: sums.map(s => s.textContent.trim()),
      head: head ? [...head.children].map(c => c.textContent) : null, rows, text: t.innerText, inTile: tr.right <= innerWidth + 0.5 && tr.left >= -0.5}};
  }}
  out.scroll = [document.documentElement.scrollWidth, innerWidth];
  return out; }}"""
def one(v): return round(v * 1000) / 10 if v is not None else None   # Math.round(v * 1000) / 10: v * 1000 is never on .5 here
def js(x): return str(int(x)) if x == int(x) else str(x)   # a JS number in a template string: 38, 44.1
def jsround(x): return int(math.floor(x + 0.5))
def pct(v): return f'{jsround(one(v))}%'

with sync_playwright() as p:
    b = p.chromium.launch(**({'executable_path': CHROMIUM} if CHROMIUM else {}))
    seen = {}
    for vw in (1440, 390, 320):
        pg = b.new_page(viewport={'width': vw, 'height': 1000})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        route_all(pg); pg.goto('file://' + HTML); pg.evaluate("localStorage.clear()"); pg.reload()
        pg.click('#tabBtnFit')
        for key, (prop, eft) in FITS.items():
            paste(pg, eft)
            if vw == 1440:
                pg.wait_for_selector(f'{R} .dmg-card', timeout=60000); settle(pg)
                seen[key] = pg.evaluate(EST)
            e = seen[key]; tag = f'{vw}px {key}'
            t = pg.evaluate(TILES)
            if not t['fighter'] or not t['missile']:
                check(False, f'{tag}: Missile and Fighter tiles ({bool(t["missile"])}, {bool(t["fighter"])})'); continue
            fr, ma = e['fr'], e['ma']
            F, M = t['fighter'], t['missile']
            # collapsed by default
            check(F['expanded'] == 'false' and not F['open'] and not F['rowsShown'] and F['sumShown'] and M['expanded'] == 'false' and not M['rowsShown'] and M['sumShown'],
                  f'{tag}: both tiles start collapsed (rows hidden, summary shown)')
            names = ' · '.join(r['name'] for r in fr['rows'])
            sub = ' · '.join(f"{r['cls']} {pct(r['cruising'])}" for r in fr['rows'])
            check(F['label'] == f"Fighter · {RACE[fr['damageType']]}" and F['sum'] == [names, sub], f'{tag}: Fighter collapsed {F["label"]!r} {F["sum"]}  (expected {names!r} {sub!r})')
            off = {}
            for x in ma['cruising']: off.setdefault(x['classLabel'], x)
            most = sum(1 for x in off.values() if x['applicationPct'] >= 95)
            check(M['sum'] == [f'{len(off)} launchers', f'{most} of {len(off)} land 95% or more'], f'{tag}: Missile collapsed {M["sum"]} (expected {len(off)} launchers, {most} of them 95%+)')
            if vw == 1440 and key == 'rifter_mwd':
                check(most < len(off), f'{tag}: the count is not trivially all ({most} of {len(off)})')
            # open the Fighter tile
            pg.click(f'{R} .weak-generic .rec-stat-fighter .rec-tog'); pg.wait_for_timeout(150)
            t = pg.evaluate(TILES); F = t['fighter']
            check(F['expanded'] == 'true' and F['open'] and F['rowsShown'] and not F['sumShown'] and not t['missile']['rowsShown'],
                  f'{tag}: the chevron opens the Fighter tile only (rows shown, summary hidden)')
            want_head = None if prop is None else ['', 'AB' if prop == 'afterburner' else 'MWD', 'off', 'on']
            bad = []
            if F['head'] != want_head: bad.append(f'header {F["head"]} vs {want_head}')
            if [r['k'] for r in F['rows']] != ['Light', 'Heavy', 'Bomber']: bad.append(f'rows {[r["k"] for r in F["rows"]]}')
            for r, x in zip(F['rows'], fr['rows']):
                if r['v'] != x['name'] or r['p'] != pct(x['cruising']) or r['pLow'] != (one(x['cruising']) < 50): bad.append(f"{x['cls']}: {r['v']} {r['p']} low {r['pLow']} vs {x['name']} {one(x['cruising'])}")
                if f"{x['name']} II" not in r['title'] or f"{js(one(x['cruising']))}%" not in r['title']: bad.append(f"{x['cls']}: hover {r['title']!r}")
                if x['cls'] == 'bomber' and 'its attack and its bomb' not in r['title']: bad.append(f'bomber hover {r["title"]!r}')
                if prop is None:
                    if r['hasB'] or x['boosted'] is not None: bad.append(f"{x['cls']}: a prop column with no prop module")
                elif r['bp'] != pct(x['boosted']) or r['bpLow'] != (one(x['boosted']) < 50) or f"{js(one(x['boosted']))}% with it on" not in r['title']:
                    bad.append(f"{x['cls']}: prop on {r['bp']} low {r['bpLow']} vs {one(x['boosted'])}; hover {r['title']!r}")
            check(not bad, f'{tag}: Fighter rows = estimate.fighterRec, amber under 50%, hovers ({bad or "3 rows"})')
            if vw == 1440 and key in ('megathron_mwd', 'rifter_mwd'):
                lows = [r['pLow'] for r in F['rows']]
                check(any(lows) and (key == 'rifter_mwd' or not all(lows)), f'{tag}: amber where under half lands ({[r["p"] for r in F["rows"]]})')
            # the open state survives a re-render of the card (collapse and expand Weaknesses), Missile opens too
            pg.click(f'{R} .weak-generic .rec-stat-missile .rec-tog'); pg.wait_for_timeout(150)
            pg.click(f'{R} button.cc-toggle[data-card="weak"]'); pg.wait_for_timeout(200)
            pg.click(f'{R} button.cc-toggle[data-card="weak"]'); pg.wait_for_timeout(300)
            t = pg.evaluate(TILES)
            check(t['fighter']['rowsShown'] and t['missile']['rowsShown'] and t['fighter']['expanded'] == 'true', f'{tag}: both stay open through a re-render of the card')
            check(t['scroll'][0] <= t['scroll'][1] and all(r['inside'] for k in ('fighter', 'missile') for r in t[k]['rows']) and t['fighter']['inTile'],
                  f'{tag}: open, no sideways scroll {t["scroll"]}, every row inside its tile')
            check(not any(x in t['fighter']['text'] + t['missile']['text'] for x in ('NaN', 'undefined')), f'{tag}: no NaN / undefined')
            # closes again, by keyboard
            pg.focus(f'{R} .weak-generic .rec-stat-fighter .rec-tog'); pg.keyboard.press('Enter'); pg.wait_for_timeout(150)
            t = pg.evaluate(TILES)
            check(t['fighter']['expanded'] == 'false' and not t['fighter']['rowsShown'] and t['fighter']['sumShown'] and t['missile']['rowsShown'],
                  f'{tag}: Enter on the chevron closes the Fighter tile (the Missile tile stays open)')
            check(t['scroll'][0] <= t['scroll'][1], f'{tag}: collapsed, no sideways scroll {t["scroll"]}')
        # a new paste starts collapsed
        paste(pg, FITS['rifter_mwd'][1]); t = pg.evaluate(TILES)
        check(bool(t['fighter']) and not t['fighter']['rowsShown'] and not t['missile']['rowsShown'], f'{vw}px: a new paste starts collapsed')
        if vw == 1440:
            info = pg.evaluate("() => CARD_INFO.weak.join(' ')")
            check(pg.locator(f'{R} details.info-pop[data-info="weak"]').count() >= 1 and 'Fighters: the T2 light fighter, heavy fighter and bomber' in info and 'open it for each class' in info, 'the Weaknesses info names the fighters')
        check(not errs, f'{vw}px: no page errors {errs[:2]}')
        pg.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
