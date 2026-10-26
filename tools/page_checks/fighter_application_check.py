"""Fighter damage application on the page (v2026.10.14.64; turret-application-plan.md D5 fighters, the owner 2026-10-25
"let's tackle fighter damage application", then "pyfa default" for the fighters' MWD and "Hover on Firepower").

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/fighter_application_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The numbers are checked against pyfa by tools/independent_checks/check_application.py (getFighterAbilityMult and every
input), check_damage_chart.py (the card's points) and check_matchup.py (the times); this checks the page around them:
  * a pasted carrier (Fit Analyzer): the Damage Application card charts its fighters -- no "Not in the chart yet: their
    fighters" note -- and its headline is pyfa's applied DPS of every weapon, drone and fighter ability at the card's
    point (the page's own PYFA CORE functions, weapons + drones alone would be less);
  * superiority fighters (Locust II) and heavy fighters (Cyclops II): their Firepower row's hover says what a ship takes
    of their missiles / torpedoes (5% / 10%, the SDE defaults pyfa reads); a light attack squadron (Templar II) has no
    such note; the raw Firepower numbers are unchanged (pyfa's raw DPS);
  * with a ship saved: the scoreboard's "DPS applied to you" is the card's headline and the times have no NaN / undefined;
  * the My Ship Perspective's Weaknesses picks (the carrier's) rank its fighters, one tile per class (v2026.10.14.72,
    fighter gaps delivery 4; checked against pyfa by check_weakness_picks.py and on the page by fighter_picks_check.py);
  * no page errors.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esi_from_sde import route_all
from playwright.sync_api import sync_playwright

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')),
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'index.html')))
CHROMIUM = os.environ.get('CHROMIUM_PATH') or ('/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') else None)
REVENANT = """[Revenant, fighters]

Omnidirectional Tracking Link II, Tracking Speed Script



Locust II x36
Cyclops II x12
"""
THANATOS = """[Thanatos, templars]

Drone Navigation Computer II



Templar II x18
"""
OSPREY = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'independent_checks', 'fits', 'osprey_navy_issue_mine.eft'), encoding='utf-8').read()
R = '#fitAnalyzerResults'
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok
def settle(pg, ms=400):
    pg.wait_for_timeout(ms); pg.wait_for_function("() => !document.querySelector('.fit-card-busy')", timeout=60000); pg.wait_for_timeout(ms)
def paste(pg, text):
    pg.evaluate("() => { const r = document.querySelector('#fitAnalyzerResults'); if(r) r.innerHTML = ''; }")
    pg.fill('#fitAnalyzerInput', text); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout', timeout=60000); settle(pg)
ROWS = f"""() => Object.fromEntries([...document.querySelectorAll('{R} .firepower-row')].map(r => [r.querySelector('.fp-name-t').textContent.trim(),
  [(r.querySelector('.fp-sub') || {{}}).title || '', r.querySelector('.fp-dps').textContent.trim()]]))"""
# the card's headline against PYFA CORE at the card's own point: all of the fit, and without its fighters
HEAD = """() => { const card = document.querySelector('#fitAnalyzerResults .fl-dmg .dmg-card'); if(!card || !card._dmg) return null;
  const c = card._dmg, m = dmgModel(c.f, c.T, c.f.dmg);
  const tgt = dmgTargetObj(c.T.pt, c.f.dmg.prop, c.f.dmg.sigPct / 100);
  const p = {distance: c.f.dmg.range, tgtSpeed: m.ySpeed, tgtAngle: c.f.dmg.mode === 'orbit' ? 90 : 0, atkSpeed: m.tSpeed, atkAngle: c.f.dmg.theirMode === 'orbit' ? 90 : 0, ignoreLockRange: true};
  const at = (app) => pyfaAppliedDpsProjected(app, tgt, p);
  const note = card.querySelector('.dmg-note');
  return {head: card.querySelector('[data-out="head"]').textContent, note: note ? note.textContent : '', cur: at(m.app), noFighters: at(Object.assign({}, m.app, {fighters: []})),
          fighters: (m.app.fighters || []).length, raw: c.f.estimate.fighterDpsBreakdown.map(g => [g.name, g.dps])}; }"""

with sync_playwright() as p:
    b = p.chromium.launch(**({'executable_path': CHROMIUM} if CHROMIUM else {}))
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML); pg.evaluate("localStorage.removeItem('dscanMyShip')"); pg.reload()
    pg.click('#tabBtnFit')
    paste(pg, REVENANT)
    rows = pg.evaluate(ROWS)
    loc, cyc = rows.get('Locust II ×36'), rows.get('Cyclops II ×12')
    check(loc and 'missiles are anti-fighter: a ship takes 5% of their damage' in loc[0], f'Locust II row hover: anti-fighter 5% ({loc})')
    check(cyc and "torpedoes are anti-capital: a ship that isn't a capital or freighter takes 10% of their damage" in cyc[0], f'Cyclops II row hover: anti-capital 10% ({cyc})')
    pg.wait_for_selector(f'{R} .fl-dmg [data-out="head"]:not(:empty)', timeout=60000)
    h = pg.evaluate(HEAD)
    raw = h['raw']
    check(raw and all(rows.get(f"{n} ×{q}", [0, ''])[1] == f'{d:,}' for (n, d), q in zip(sorted(raw), (12, 36))), f'raw Firepower numbers are the engine\'s raw fighter DPS (checked against pyfa by check_application.py) {raw}')
    check('fighters' not in h['note'], f'Damage Application charts the fighters (note "{h["note"]}")')
    check(h['fighters'] == 3 and h['cur'] > h['noFighters'] >= 0, f'headline includes the fighters: {h["cur"]} > {h["noFighters"]} without them ({h["fighters"]} abilities)')
    check(h['head'].split(' ')[0] == f"{round(h['cur']):,}", f'headline text "{h["head"]}" = {h["cur"]}')
    paste(pg, THANATOS)
    rows = pg.evaluate(ROWS)
    tem = rows.get('Templar II ×18')
    check(tem and 'anti-' not in tem[0] and 'takes' not in tem[0], f'Templar II row: no resistance note ({tem})')
    # with a ship saved: the scoreboard's DPS applied to you is the card's headline, the times are numbers
    pg.click('#myShipChip'); pg.fill('#myShipEft', OSPREY); pg.click('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-tiles'); pg.keyboard.press('Escape')
    paste(pg, REVENANT)
    pg.wait_for_function(f"() => {{ const b = document.querySelector('{R} .mys-board'); return b && !/…/.test(b.textContent); }}", timeout=60000); settle(pg, 600)
    cells = pg.evaluate(f"() => Object.fromEntries([...document.querySelector('{R} .mys-board').querySelectorAll('[data-cell]')].map(c => [c.dataset.cell, (c.querySelector('.mys-cell-v') || c).textContent]))")
    head = pg.inner_text(f'{R} .fl-dmg [data-out="head"]')
    board = pg.inner_text(f'{R} .mys-board')
    check(cells.get('their') == head and cells.get('their') not in ('0', ''), f'board "DPS applied to you" {cells.get("their")} = the card headline {head}')
    check(not any(x in board for x in ('NaN', 'undefined', 'Infinity')), f'board has no NaN / undefined ({cells})')
    why = pg.evaluate(f"() => [...document.querySelectorAll('.mys-why-sr')].map(x => x.textContent).join(' | ')")
    check(why and not any(x in why for x in ('NaN', 'undefined', 'Infinity')), f'why text has no NaN ({why[:160]})')
    # the My Ship Perspective's Weaknesses picks are the threat's (the carrier's) weapons on you
    pg.click(f'{R} .mys-sw-btn.is-mine'); pg.wait_for_selector(f'{R} .mys-mine-view .fit-layout'); settle(pg)
    pg.wait_for_selector(f'{R} .mys-mine-view .weak-picks[data-filled]', timeout=120000); settle(pg)
    labels = pg.evaluate(f"() => [...document.querySelectorAll('{R} .mys-mine-view .weak-picks .wp-stat .rec-label')].map(e => e.textContent)")
    check(any(l.startswith('Their ') and l.endswith(' fighters') for l in labels) and "Fighters aren't ranked yet" not in pg.inner_text(f'{R} .mys-mine-view'),
          f'Weaknesses picks (My Ship Perspective): the carrier\'s fighters ranked per class ({labels})')
    check(not errs, f'no page errors {errs}')
    ctx.close(); b.close()
print(f'FAILURES: {fails}')
