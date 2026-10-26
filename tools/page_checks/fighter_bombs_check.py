"""Fighter bombs: off by default, counted when switched on (v2026.10.14.71, fighter gaps delivery 3; the owner 2026-10-25 bombs
"Off, toggle per type (Recommended)", counted with pyfa's rule).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/fighter_bombs_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The numbers are checked against pyfa by tools/independent_checks/check_application.py (FighterAbility.getVolley from the
squadron's charge, getFighterAbilityMult's bomb branch, on the oracle) and the golden fit hel_constructed_ametat_bombs_on.
This checks the page around them, with a pasted Hel carrying Ametat II x12 (two heavy squadrons):
  * the Bomb button is a toggle, off by default; its hover names the charge and "3,840 damage per squadron every 60 s";
  * switched on: the Firepower row for the Ametat II goes up by the bombs (2 x 64 = 128 DPS), the Damage Application
    headline is PYFA CORE's with the bomb in the application (one entry, explosion radius 400 m), and the hover says
    it's counted; switched off again: back to the Attack DPS;
  * the bomb lands without a lock: beyond the carrier's lock range the bomb still counts in PYFA CORE (lock respected);
  * no page errors.
v2026.10.14.70 fails (the Bomb disabled, never counted).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esi_from_sde import route_all
from playwright.sync_api import sync_playwright

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')),
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'index.html')))
CHROMIUM = os.environ.get('CHROMIUM_PATH') or ('/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') else None)
HEL = """[Hel, bombers]



Ametat II x12
"""
R = '#fitAnalyzerResults'
AMETAT = 40560
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok
def settle(pg, ms=400):
    pg.wait_for_timeout(ms); pg.wait_for_function("() => !document.querySelector('.fit-card-busy')", timeout=60000); pg.wait_for_timeout(ms)
def paste(pg, text):
    pg.evaluate("() => { const r = document.querySelector('#fitAnalyzerResults'); if(r) r.innerHTML = ''; }")
    pg.fill('#fitAnalyzerInput', text); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout', timeout=60000); settle(pg)
    if pg.query_selector(f'{R} .fit-view-btn[data-view="list"]:not(.on)'):
        pg.click(f'{R} .fit-view-btn[data-view="list"]'); settle(pg)
STATE = f"""() => {{ const card = [...document.querySelectorAll('{R} .dmg-card')].find(e => e._dmg && e._dmg.side !== 'mine');
  const c = card._dmg, est = c.f.estimate, m = dmgModel(c.f, c.T, c.f.dmg);
  const tgt = dmgTargetObj(c.T.pt, c.f.dmg.prop, c.f.dmg.sigPct / 100);
  const p = {{distance: c.f.dmg.range, tgtSpeed: m.ySpeed, tgtAngle: c.f.dmg.mode === 'orbit' ? 90 : 0, atkSpeed: m.tSpeed, atkAngle: c.f.dmg.theirMode === 'orbit' ? 90 : 0, ignoreLockRange: true}};
  const far = Object.assign({{}}, p, {{distance: est.application.lockRange + 50000, ignoreLockRange: false}});
  const bombs = (est.application.fighters || []).filter(x => x.ability === 'fighterAbilityLaunchBomb');
  const btn = document.querySelector('{R} .fb-ab[data-type-id="{AMETAT}"][data-effect="6485"]');
  const row = [...document.querySelectorAll('{R} .firepower-row')].find(r => r.querySelector('.fp-name-t').textContent.includes('Ametat II'));
  return {{head: card.querySelector('[data-out="head"]').textContent, cur: pyfaAppliedDpsProjected(m.app, tgt, p),
    farBomb: bombs.reduce((s, b) => s + b.dps * pyfaGetFighterAbilityMult(est.application, b, Object.assign({{tgtSigRadius: 3000}}, far)), 0),
    bombs: bombs.map(b => [b.dps, b.explosionRadius, b.squadrons]), fighterDps: est.fighterDps,
    btn: btn ? [btn.classList.contains('on'), btn.disabled, btn.title] : null, row: row ? row.querySelector('.fp-dps').textContent : null}}; }}"""
def head_ok(s): return s['head'] == f"{round(s['cur']):,}"

with sync_playwright() as p:
    b = p.chromium.launch(**({'executable_path': CHROMIUM} if CHROMIUM else {}))
    pg = b.new_page(viewport={'width': 1440, 'height': 1000})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML); pg.evaluate("localStorage.clear()"); pg.reload()
    pg.click('#tabBtnFit'); paste(pg, HEL)
    pg.wait_for_selector(f'{R} .dmg-card [data-out="head"]:not(:empty)', timeout=60000); settle(pg)
    s0 = pg.evaluate(STATE)
    check(s0['btn'] and not s0['btn'][0] and not s0['btn'][1] and "off (pyfa's default)" in s0['btn'][2] and '3,840 damage per squadron every 60 s' in s0['btn'][2],
          f'Bomb: a toggle, off by default, hover with its numbers {s0["btn"]}')
    check(not s0['bombs'] and head_ok(s0), f'off: no bomb in the application, headline {s0["head"]} = PYFA CORE {s0["cur"]:.2f}')
    if not (s0['btn'] and not s0['btn'][1]):
        check(False, 'the Bomb button can be clicked'); print(f'FAILURES: {fails}'); sys.exit(1)
    pg.click(f'{R} .fb-ab[data-type-id="{AMETAT}"][data-effect="6485"]'); settle(pg, 700)
    s1 = pg.evaluate(STATE)
    check(s1['bombs'] == [[128, 400, 2]], f'on: the bomb in the application, 2 squadrons x 64 DPS, explosion radius 400 m: {s1["bombs"]}')
    check(abs(s1['fighterDps'] - s0['fighterDps'] - 128) <= 1 and s1['row'] and int(s1['row'].replace(',', '')) - int(s0['row'].replace(',', '')) in (127, 128, 129),
          f'Firepower: fighter DPS {s0["fighterDps"]} -> {s1["fighterDps"]}, Ametat row {s0["row"]} -> {s1["row"]}')
    check(head_ok(s1) and s1['cur'] > s0['cur'], f'Damage Application headline {s1["head"]} = PYFA CORE {s1["cur"]:.2f} (up from {s0["cur"]:.2f})')
    check(s1['btn'] and s1['btn'][0] and 'counted in its DPS' in s1['btn'][2], f'on: hover {s1["btn"] and s1["btn"][2]!r}')
    check(abs(s1['farBomb'] - 128) < 1e-6, f'beyond the lock range (lock respected) the bomb still lands: {s1["farBomb"]}')
    pg.click(f'{R} .fb-ab[data-type-id="{AMETAT}"][data-effect="6485"]'); settle(pg, 700)
    s2 = pg.evaluate(STATE)
    check(not s2['bombs'] and s2['row'] == s0['row'] and head_ok(s2), f'off again: back to {s2["row"]} (was {s0["row"]})')
    check(not errs, f'no page errors {errs[:2]}')
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
