"""The Fighter bay: squadrons and abilities you choose (v2026.10.14.66; the owner 2026-10-25 "Ok lets get the fighter gaps
closed. Carriers need to be accurately assessed in the tool.", then "Damage first", bombs "Off, toggle per type", the
in-game ability icons, "Icon + short label", the bay "Open by default").

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/fighter_bay_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The numbers are checked against pyfa by tools/independent_checks/check_application.py (every ability on or off, every
speed ability's handler, the launched squadrons as inputs) and the golden fits nidhoggur_constructed_fighter_bay_states /
hel_constructed_fighter_bay_abilities; this checks the page around them, on the real page (ESI served from pyfa's SDE):
  * a pasted Nidhoggur (Einherji II x24, Dromi II x3, Siren II x3): the Fighter bay is open by default; the default launch
    is damage first (3 Einherji, the light limit), then support in the tube left (the Dromi: webs first), the Siren
    locked with its reason; the budget reads "Tubes 4 / 4 · Light 3 / 3 · Support 1 / 2";
  * each type's abilities in the approved order (damage, EWAR, propulsion) with pyfa's defaults on (Attack, Missiles,
    Web, Point, the Siren's AB) and off (the MWDs), each with the game's icon from img/fighter-abilities (loaded, 64 px);
  * MWD on: the Einherji's speed in the application goes up, and the Damage Application headline is still PYFA CORE's at
    the card's point; Missiles off: the Firepower row is the Attack ability's DPS alone (all 3 squadrons) and drops;
  * taking an Einherji squadron back frees a tube: the Siren's square unlocks and launches it; reset brings the defaults;
  * collapsed, the bay's row says "N / 4 tubes"; a bomber (Hel, Ametat II): "Attack" then "Bomb", the Bomb disabled;
  * the states are kept with My Ships (stored fighterStates; a reload restores the MWD);
  * phone (375 px): ability buttons 44 px tall, the bay doesn't scroll sideways. No page errors.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esi_from_sde import route_all
from playwright.sync_api import sync_playwright

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')),
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'index.html')))
CHROMIUM = os.environ.get('CHROMIUM_PATH') or ('/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') else None)
NIDHOGGUR = """[Nidhoggur, bay]

Drone Navigation Computer II



Einherji II x24
Dromi II x3
Siren II x3
"""
HEL = """[Hel, bombers]



Ametat II x12
"""
R = '#fitAnalyzerResults'
EIN, DROMI, SIREN = 40559, 40571, 40570
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
BAY = f"""() => {{ const row = document.querySelector('{R} .fb-row'); if(!row) return null; const g = row.closest('.fitgroup');
  return {{budget: (g.querySelector('.ds-budget') || {{}}).textContent || '',
    types: Object.fromEntries([...g.querySelectorAll('.fb-row')].map(r => {{ const id = r.querySelector('.fb-pip').dataset.typeId;
      return [id, {{on: r.querySelectorAll('.fb-pip.on').length, locked: [...r.querySelectorAll('.fb-pip.locked')].map(p => p.title),
        abs: [...r.querySelectorAll('.fb-ab')].map(b => ({{t: b.textContent.trim(), on: b.classList.contains('on'), dis: b.disabled, title: b.title,
          img: b.querySelector('img') ? [b.querySelector('img').getAttribute('src'), b.querySelector('img').naturalWidth] : null}}))}}]; }}))}}; }}"""
FIT = f"() => [...document.querySelectorAll('{R} *')].find(e => e._dmg)._dmg.f"
APP = f"""() => {{ const f = ({FIT})(); return {{states: f.fighterStates, app: (f.estimate.application.fighters || []).map(x => [x.typeId, x.ability, x.speed, x.dps, x.squadrons]),
  fs: f.estimate.fighterStates.items.map(i => [i.typeId, i.active, i.dpsEach])}}; }}"""
HEAD = f"""() => {{ const card = [...document.querySelectorAll('{R} *')].find(e => e._dmg); const c = card._dmg, m = dmgModel(c.f, c.T, c.f.dmg);
  const tgt = dmgTargetObj(c.T.pt, c.f.dmg.prop, c.f.dmg.sigPct / 100);
  const p = {{distance: c.f.dmg.range, tgtSpeed: m.ySpeed, tgtAngle: c.f.dmg.mode === 'orbit' ? 90 : 0, atkSpeed: m.tSpeed, atkAngle: c.f.dmg.theirMode === 'orbit' ? 90 : 0, ignoreLockRange: true}};
  return {{head: card.querySelector('[data-out="head"]').textContent, cur: pyfaAppliedDpsProjected(m.app, tgt, p)}}; }}"""
ROWS = f"""() => Object.fromEntries([...document.querySelectorAll('{R} .firepower-row')].map(r => [r.querySelector('.fp-name-t').textContent.trim(), r.querySelector('.fp-dps').textContent.trim()]))"""
def click(pg, sel):
    pg.click(sel); settle(pg)

with sync_playwright() as p:
    b = p.chromium.launch(**({'executable_path': CHROMIUM} if CHROMIUM else {}))
    ctx = b.new_context(viewport={'width': 1440, 'height': 1000}); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML); pg.evaluate("localStorage.clear()"); pg.reload()
    pg.click('#tabBtnFit')
    paste(pg, NIDHOGGUR)
    bay = pg.evaluate(BAY)
    check(bay is not None and not pg.query_selector(f'{R} .cc-closed [data-card="bay:fighter"]'), 'Fighter bay open by default')
    t = bay['types'] if bay else {}
    check(bay and ' '.join(bay['budget'].split()) == 'Tubes 4 / 4 · Light 3 / 3 · Support 1 / 2', f'budget "{bay and bay["budget"]}"')
    check(t.get(str(EIN), {}).get('on') == 3 and t.get(str(DROMI), {}).get('on') == 1 and t.get(str(SIREN), {}).get('on') == 0,
          f'default launch: 3 Einherji, then the Dromi in the tube left, no Siren ({ {k: v["on"] for k, v in t.items()} })')
    check(any('all 4 tubes are in use' in x for x in t.get(str(SIREN), {}).get('locked', [])), f'the Siren is locked: {t.get(str(SIREN), {}).get("locked")}')
    abs_ = {k: [(a['t'], a['on']) for a in v['abs']] for k, v in t.items()}
    check(abs_.get(str(EIN)) == [('Attack', True), ('Missiles', True), ('MWD', False)] and abs_.get(str(DROMI)) == [('Web', True), ('MWD', False)]
          and abs_.get(str(SIREN)) == [('Point', True), ('AB', True)], f'abilities, order and pyfa defaults: {abs_}')
    imgs = [a['img'] for v in t.values() for a in v['abs']]
    check(imgs and all(i and i[0].startswith('img/fighter-abilities/') and i[1] == 64 for i in imgs), f'every ability shows its game icon, loaded: {imgs}')
    # v2026.10.14.70 (fighter gaps delivery 2): the web is applied now -- its hover says so (support_fighters_check.py checks the numbers)
    check(any('slows the target in' in a['title'] for a in t.get(str(DROMI), {}).get('abs', [])), 'the web says it slows the target')
    a0 = pg.evaluate(APP)
    s0 = {(x[0], x[1]): x[2] for x in a0['app']}
    click(pg, f'{R} .fb-ab[data-type-id="{EIN}"][data-effect="6441"]')
    a1 = pg.evaluate(APP)
    s1 = {(x[0], x[1]): x[2] for x in a1['app']}
    check(a1['states'] and a1['states'][str(EIN)]['ab']['6441'] is True and all(s1[k] > s0[k] * 1.5 for k in s0 if k[0] == EIN),
          f'MWD on: the Einherji are faster in the application ({s0} -> {s1})')
    pg.wait_for_selector(f'{R} [data-out="head"]:not(:empty)', timeout=60000)
    h = pg.evaluate(HEAD)
    check(h['head'].split(' ')[0] == f"{round(h['cur']):,}", f'Damage Application headline "{h["head"]}" = PYFA CORE {h["cur"]}')
    r0 = pg.evaluate(ROWS)
    click(pg, f'{R} .fb-ab[data-type-id="{EIN}"][data-effect="6431"]')
    a2 = pg.evaluate(APP); r1 = pg.evaluate(ROWS)
    appDps = sum(x[3] for x in a2['app'] if x[0] == EIN)
    check([x[1] for x in a2['app'] if x[0] == EIN] == ['fighterAbilityAttackMissile'] and r1.get('Einherji II ×18') == f'{round(appDps):,}'
          and int(r1['Einherji II ×18'].replace(',', '')) < int(r0['Einherji II ×18'].replace(',', '')),
          f'Missiles off: only Attack in the application, Firepower {r0.get("Einherji II ×18")} -> {r1.get("Einherji II ×18")} = its Attack DPS {appDps}')
    click(pg, f'{R} .fb-pip[data-type-id="{EIN}"].on:nth-child(3)')
    bay = pg.evaluate(BAY); t = bay['types']
    check(t[str(EIN)]['on'] == 2 and not t[str(SIREN)]['locked'], f'one Einherji back: the Siren unlocks ({t[str(EIN)]["on"]}, {t[str(SIREN)]["locked"]})')
    click(pg, f'{R} .fb-pip[data-type-id="{SIREN}"]')
    bay = pg.evaluate(BAY); t = bay['types']
    check(t[str(SIREN)]['on'] == 1 and ' '.join(bay['budget'].split()).startswith('Tubes 4 / 4 · Light 2 / 3 · Support 2 / 2'), f'the Siren launched ({bay["budget"]})')
    check(pg.query_selector(f'{R} button.ms-reset.is-custom') is not None, 'reset is active after a Fighter bay change')
    # kept with My Ships, restored after a reload
    pg.click(f'{R} button.mys-set'); pg.wait_for_function("() => { try { return JSON.parse(localStorage.getItem('dscanMyShips')).fits.length === 1; } catch(e) { return false; } }", timeout=60000)
    stored = pg.evaluate("() => JSON.parse(localStorage.getItem('dscanMyShips')).fits[0].fighterStates")
    check(stored and stored[str(EIN)]['n'] == 2 and stored[str(EIN)]['ab']['6441'] is True and stored[str(SIREN)]['n'] == 1, f'My Ships keeps the Fighter bay states: {stored}')
    click(pg, f'{R} button.ms-reset')
    bay = pg.evaluate(BAY); t = bay['types']
    check(t[str(EIN)]['on'] == 3 and t[str(SIREN)]['on'] == 0 and [(a['t'], a['on']) for a in t[str(EIN)]['abs']] == [('Attack', True), ('Missiles', True), ('MWD', False)]
          and pg.evaluate(f"() => ({FIT})().fighterStates") is None, 'reset: the default launch and abilities again')
    click(pg, f'{R} [data-card="bay:fighter"]')
    summ = pg.inner_text(f'{R} .cc-closed [data-card="bay:fighter"]')
    check('4 / 4 tubes' in summ, f'collapsed row: "{summ}"')
    pg.reload(); pg.wait_for_timeout(500)
    pg.click('#myShipChip'); pg.wait_for_selector('#myShipPanel .mys-tiles', timeout=60000)
    restored = pg.evaluate("async () => { const f = await myShipEnsureFit(); return f && f.estimate.application.fighters.filter(x => x.typeId === 40559).map(x => [x.squadrons, x.activeAbilities]); }")
    check(restored and all(x[0] == 2 and 6441 in x[1] for x in restored), f'after a reload my ship has the stored states: {restored}')
    pg.keyboard.press('Escape')
    # a bomber: Attack then Bomb, the Bomb disabled (counted in a coming update)
    pg.click('#tabBtnFit'); paste(pg, HEL)
    bay = pg.evaluate(BAY); ab = bay['types']['40560']['abs']
    check([(a['t'], a['on'], a['dis']) for a in ab] == [('Attack', True, False), ('Bomb', False, True)] and 'coming update' in ab[1]['title'], f'bomber: {[(a["t"], a["on"], a["dis"]) for a in ab]}')
    check(not errs, f'no page errors {errs}')
    ctx.close()
    # phone
    ctx = b.new_context(viewport={'width': 375, 'height': 900}, device_scale_factor=2); pg = ctx.new_page()
    errs2 = []; pg.on('pageerror', lambda e: errs2.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML); pg.evaluate("localStorage.clear()"); pg.reload()
    pg.click('#tabBtnFit'); paste(pg, NIDHOGGUR)
    m = pg.evaluate(f"""() => {{ const g = document.querySelector('{R} .fb-row').closest('.fitgroup');
      return {{h: Math.min(...[...g.querySelectorAll('.fb-ab')].map(b => b.getBoundingClientRect().height)), over: g.scrollWidth - g.clientWidth,
              doc: document.documentElement.scrollWidth - window.innerWidth}}; }}""")
    check(m['h'] >= 44 and m['over'] <= 0 and m['doc'] <= 0, f'phone: ability buttons {m["h"]} px tall, no sideways scroll ({m})')
    check(not errs2, f'no page errors on the phone {errs2}')
    ctx.close(); b.close()
print(f'FAILURES: {fails}')
