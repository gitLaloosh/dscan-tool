"""The Weaknesses card's Missile tile: the best ammo for each launcher (v2026.10.14.69; the owner: "let's do #3" -- picks for
each missile size instead of one pick across every size -- then option A from the mockup and "Keep it" for the prop
column).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/missile_picks_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The numbers come from estimate.missileApplication, which tools/independent_checks/check_missile_application.py
recomputes from the SDE with pyfa's skill handlers (every golden fit, 0 mismatches). This checks the tile built from it,
with no ship saved, on four targets (a frigate and a battleship with an MWD, a cruiser with an afterburner, a frigate
with no prop module):
  * six rows in launcher order Rocket, Light, HAM, Heavy, Torpedo, Cruise; each row's tier and whole-number % are the
    FIRST entry of that launcher in the cruising ranking (the ranking is already best first);
  * the prop column: headed MWD / AB as fitted, absent with no prop module; its % is that launcher's first entry in the
    boosted ranking, and it names the tier only when it differs (the Megathron's Cruise: Precision);
  * under 50% is amber, 50% and over is not;
  * each row's hover names the full ammo ("Inferno Precision Light Missile") and both percentages unrounded;
  * 1440, 390 and 320 px wide: no sideways scroll, every row inside the tile, the tier never cut to nothing;
  * no NaN / undefined, no page errors.
v2026.10.14.68 fails (one pick, no rows).
"""
import sys, os, re
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
ORDER = [('Rocket', 'Rocket'), ('Light Missile', 'Light'), ('Heavy Assault Missile', 'HAM'), ('Heavy Missile', 'Heavy'),
         ('Torpedo', 'Torpedo'), ('Cruise Missile', 'Cruise')]
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok
def settle(pg, ms=400):
    pg.wait_for_timeout(ms); pg.wait_for_function("() => !document.querySelector('.fit-card-busy')", timeout=60000); pg.wait_for_timeout(ms)
def paste(pg, text):
    pg.evaluate("() => { const r = document.querySelector('#fitAnalyzerResults'); if(r) r.innerHTML = ''; }")
    pg.fill('#fitAnalyzerInput', text); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout', timeout=60000); settle(pg)
# The estimate the card was drawn from (the Damage Application card keeps it; it's open at 1440 px).
EST = f"""() => {{ const c = [...document.querySelectorAll('{R} .dmg-card')].find(c => c._dmg && c._dmg.side !== 'mine');
  return c ? {{ma: c._dmg.f.estimate.missileApplication, prop: c._dmg.f.estimate.speed.propModType || null}} : null; }}"""
TILE = f"""() => {{ const t = document.querySelector('{R} .weak-generic .rec-stat-missile'); if(!t) return null;
  const tr = t.getBoundingClientRect();
  const rows = [...t.querySelectorAll('.mis-row:not(.mis-head)')].map(r => {{
    const q = s => r.querySelector(s), rr = r.getBoundingClientRect(), v = q('.mis-v');
    return {{launcher: r.dataset.launcher, k: q('.mis-k').textContent, v: v.textContent, vW: v.getBoundingClientRect().width,
      p: q('.mis-p').textContent, pLow: q('.mis-p').classList.contains('is-low'), pColor: getComputedStyle(q('.mis-p')).color,
      bt: q('.mis-bt') ? q('.mis-bt').textContent : null, bp: q('.mis-bp') ? q('.mis-bp').textContent : null,
      bpLow: q('.mis-bp') ? q('.mis-bp').classList.contains('is-low') : null, title: r.title,
      inside: [...r.children].every(c => {{ const b = c.getBoundingClientRect(); return b.left >= tr.left - 0.5 && b.right <= tr.right + 0.5; }}),
      rowInside: rr.right <= tr.right + 0.5}}; }});
  const head = t.querySelector('.mis-head');
  return {{rows, head: head ? [...head.children].map(c => c.textContent) : null, label: t.querySelector('.rec-label').textContent,
    amber: getComputedStyle(document.documentElement).getPropertyValue('--amber').trim(), text: t.innerText,
    scroll: [document.documentElement.scrollWidth, innerWidth]}}; }}"""
def jsround(v): return int(v + 0.5)   # the tile rounds the ranking's one-decimal % half up (Math.round), as its hover reads
def first_by_launcher(ranking):
    out = {}
    for x in ranking or []:
        out.setdefault(x['classLabel'], x)
    return out

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
            e = seen[key]
            t = pg.evaluate(TILE)
            tag = f'{vw}px {key}'
            if not t:
                check(False, f'{tag}: no Missile tile with rows'); continue
            if vw == 1440:
                check(e['prop'] == prop, f'{tag}: the fit\'s prop module is {e["prop"]} (expected {prop})')
                off, on = first_by_launcher(e['ma']['cruising']), first_by_launcher(e['ma']['boosted'])
                race = e['ma']['ammoName']
                check(t['label'] == f'Missile · {race}', f'{tag}: label "{t["label"]}"')
                check([r['launcher'] for r in t['rows']] == [c for c, _ in ORDER] and [r['k'] for r in t['rows']] == [s for _, s in ORDER],
                      f'{tag}: six rows in launcher order ({[r["k"] for r in t["rows"]]})')
                want_head = None if prop is None else ['', 'AB' if prop == 'afterburner' else 'MWD', 'off', 'on']
                check(t['head'] == want_head, f'{tag}: prop column header {t["head"]} (expected {want_head})')
                bad = []
                for r, (cls, _) in zip(t['rows'], ORDER):
                    x, y = off[cls], (on or {}).get(cls)
                    full = lambda z: f"{race} {'' if z['tier'] == 'T1' else z['tier'] + ' '}{cls}"
                    if r['v'] != x['tier'] or r['p'] != f"{jsround(x['applicationPct'])}%": bad.append(f"{cls}: {r['v']} {r['p']} vs {x['tier']} {x['applicationPct']}")
                    if r['pLow'] != (x['applicationPct'] < 50) or (r['pLow'] and r['pColor'] == 'rgb(238, 242, 244)'): bad.append(f'{cls}: amber {r["pLow"]} at {x["applicationPct"]}')
                    if full(x) not in r['title'] or f"{x['applicationPct']}%" not in r['title']: bad.append(f'{cls}: hover {r["title"]!r}')
                    if prop is None:
                        if r['bp'] is not None: bad.append(f'{cls}: prop column with no prop module')
                    else:
                        if y is None or r['bp'] != f"{jsround(y['applicationPct'])}%": bad.append(f"{cls}: prop on {r['bp']} vs {y and y['applicationPct']}")
                        elif (r['bt'] or None) != (y['tier'] if y['tier'] != x['tier'] else None): bad.append(f"{cls}: prop tier {r['bt']} vs {y['tier']} (off {x['tier']})")
                        elif r['bpLow'] != (y['applicationPct'] < 50): bad.append(f'{cls}: prop amber {r["bpLow"]} at {y["applicationPct"]}')
                        elif f"{y['applicationPct']}%" not in r['title'] or (y['tier'] != x['tier'] and full(y) not in r['title']): bad.append(f'{cls}: hover {r["title"]!r}')
                check(not bad, f'{tag}: every row = that launcher\'s first entry off / on, amber under 50%, hover names it ({bad or "6 rows"})')
                if key == 'megathron_mwd':
                    cr = t['rows'][5]
                    check(cr['bt'] == 'Precision' and cr['v'] == 'T1', f'{tag}: Cruise names Precision with the MWD on (T1 off): {cr["v"]} / {cr["bt"]} {cr["bp"]}')
                if key == 'rifter_mwd':
                    check(any(r['pLow'] for r in t['rows']) and any(not r['pLow'] for r in t['rows']), f'{tag}: both amber and plain rows ({[r["p"] for r in t["rows"]]})')
            check(t['scroll'][0] <= t['scroll'][1] and all(r['inside'] and r['rowInside'] for r in t['rows']) and all(r['vW'] >= 20 for r in t['rows']),
                  f'{tag}: no sideways scroll {t["scroll"]}, every row inside the tile, tier shown (min width {min(r["vW"] for r in t["rows"]):.0f} px)')
            check(not any(x in t['text'] for x in ('NaN', 'undefined')), f'{tag}: no NaN / undefined')
        check(not errs, f'{vw}px: no page errors {errs[:2]}')
        pg.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
