"""Support fighters: the Dromi's web applied, every support ability shown on the EWAR card (v2026.10.14.70, fighter gaps
delivery 2; the owner 2026-10-25 "Webs applied, rest shown").

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/support_fighters_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The numbers are checked against pyfa by tools/independent_checks/check_projected.py (pyfa's getProjFighterData and
calc/projected.py unmodified on oracle attributes, the tool's launched squadrons and abilities as inputs) and the golden
fits nidhoggur_constructed_fighter_bay_states (Dromi web, tackled pins), nidhoggur_constructed_dromi_web_off,
archon_constructed_cenobite_neut and chimera_constructed_scarab_ecm. This checks the page around them:
  * a pasted Nidhoggur (Einherji II x24, Dromi II x3, Siren II x3; the default launch puts the Dromi out): the EWAR card
    shows a "Dromi II" chip with its range and web ("20 km · -49.5% speed", = the estimate's entry) and "1 squadron";
    the web is in the projected inputs (one mobile web, its boost = the chip's), the Damage Application chart's T zone
    reaches 20 km, and the headline is PYFA CORE's with it;
  * switching the Dromi's web off in the Fighter bay: no web in the inputs, no Dromi chip, the headline changes and is
    still PYFA CORE's; the web's hover says what it does, on and off;
  * the Siren launched instead of the Dromi: a "Siren II" chip, "16 km · scramble strength 3", not in the inputs;
  * a pasted Archon with Cenobite II: a "Cenobite II" chip "12.5+5 km · 297 GJ/cycle (49.5 GJ/s)", the chart's C zone
    reaches 12.5 km, the neutralizer's hover says it is shown, not counted;
  * 390 px: the chips stay inside the card; no page errors.
v2026.10.14.69 fails (no fighter web in the inputs, no fighter chips).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esi_from_sde import route_all
from playwright.sync_api import sync_playwright

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')),
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'index.html')))
CHROMIUM = os.environ.get('CHROMIUM_PATH') or ('/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') else None)
NIDHOGGUR = """[Nidhoggur, support fighters]

Drone Navigation Computer II



Einherji II x24
Dromi II x3
Siren II x3
"""
ARCHON = """[Archon, support fighters]
Drone Damage Amplifier II



Templar II x18
Cenobite II x6
"""
R = '#fitAnalyzerResults'
DROMI, SIREN, CENOBITE = 40571, 40570, 40568
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
def click(pg, sel):
    pg.click(sel); settle(pg, 600)
STATE = f"""() => {{ const card = [...document.querySelectorAll('{R} .dmg-card')].find(e => e._dmg && e._dmg.side !== 'mine');
  const c = card._dmg, est = c.f.estimate, m = dmgModel(c.f, c.T, c.f.dmg);
  const tgt = dmgTargetObj(c.T.pt, c.f.dmg.prop, c.f.dmg.sigPct / 100);
  const p = {{distance: c.f.dmg.range, tgtSpeed: m.ySpeed, tgtAngle: c.f.dmg.mode === 'orbit' ? 90 : 0, atkSpeed: m.tSpeed, atkAngle: c.f.dmg.theirMode === 'orbit' ? 90 : 0, ignoreLockRange: true}};
  const marks = dmgRangeMarks(m.app, est, 1e9, false);
  const ew = document.querySelector('{R} .ewar-card');
  const chips = ew ? [...ew.querySelectorAll('.ewar-chip')].map(ch => {{ const r = ch.getBoundingClientRect(), cr = ew.getBoundingClientRect();
    return {{name: ch.querySelector('.chip-name').textContent.trim(), badge: ch.querySelector('.ewar-badge').textContent.trim(),
      detail: ch.querySelector('.chip-detail').textContent.trim(), inside: r.left >= cr.left - 0.5 && r.right <= cr.right + 0.5}}; }}) : [];
  return {{webs: est.application.projected.webFighters, ewar: est.ewarModules.filter(x => x.fighter),
    head: card.querySelector('[data-out="head"]').textContent, cur: pyfaAppliedDpsProjected(m.app, tgt, p),
    zones: marks.zones.map(z => [z.short, z.x]), chips, count: ew ? ew.querySelector('.ewar-card-count').textContent.trim() : null,
    abTitles: Object.fromEntries([...document.querySelectorAll('{R} .fb-ab')].map(b => [b.dataset.typeId + ':' + b.dataset.effect, b.title]))}}; }}"""
def head_ok(s): return s['head'] == f"{round(s['cur']):,}"

with sync_playwright() as p:
    b = p.chromium.launch(**({'executable_path': CHROMIUM} if CHROMIUM else {}))
    pg = b.new_page(viewport={'width': 1440, 'height': 1000})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML); pg.evaluate("localStorage.clear()"); pg.reload()
    pg.click('#tabBtnFit')
    paste(pg, NIDHOGGUR)
    pg.wait_for_selector(f'{R} .dmg-card [data-out="head"]:not(:empty)', timeout=60000); settle(pg)
    s = pg.evaluate(STATE)
    dro = [c for c in s['chips'] if c['name'] == 'Dromi II']
    e = [x for x in s['ewar'] if x['name'] == 'Dromi II']
    check(len(dro) == 1 and dro[0]['badge'] == 'T' and dro[0]['detail'] == '20 km · -49.5% speed' and e and e[0]['speedBonusPct'] == -49.5,
          f'EWAR card: Dromi II chip {dro} = the estimate {e}')
    check(s['count'] == '1 squadron', f'card count "{s["count"]}"')
    check(len(s['webs']) == 1 and abs(s['webs'][0]['boost'] - (-49.5)) < 1e-9 and s['webs'][0]['optimal'] == 20000, f'one fighter web in the projected inputs: {s["webs"]}')
    check(['web', 20000] in s['zones'], f'the chart\'s T web zone reaches 20 km: {s["zones"]}')
    check(head_ok(s) and s['cur'] > 0, f'headline {s["head"]} = PYFA CORE {s["cur"]:.2f} with the web')
    t_on = s['abTitles'].get(f'{DROMI}:6435', '')
    check('slows the target in' in t_on and 'Click to switch it off' in t_on, f'web hover (on): {t_on!r}')
    click(pg, f'{R} .fb-ab[data-type-id="{DROMI}"][data-effect="6435"]')
    s2 = pg.evaluate(STATE)
    check(not s2['webs'] and not [c for c in s2['chips'] if c['name'] == 'Dromi II'] and 'web' not in [z[0] for z in s2['zones']],
          f'web off: no fighter web, no Dromi chip, no web zone ({s2["webs"]}, {s2["chips"]}, {s2["zones"]})')
    check(head_ok(s2) and s2['cur'] != s['cur'], f'web off: headline {s2["head"]} = PYFA CORE {s2["cur"]:.2f}, changed from {s["cur"]:.2f}')
    t_off = s2['abTitles'].get(f'{DROMI}:6435', '')
    check('off' in t_off and 'slows the target' in t_off, f'web hover (off): {t_off!r}')
    click(pg, f'{R} .fb-ab[data-type-id="{DROMI}"][data-effect="6435"]')
    # the Siren instead of the Dromi: take the Dromi back, launch the Siren
    click(pg, f'{R} .fb-pip[data-type-id="{DROMI}"].on')
    click(pg, f'{R} .fb-pip[data-type-id="{SIREN}"]')
    s3 = pg.evaluate(STATE)
    sir = [c for c in s3['chips'] if c['name'] == 'Siren II']
    check(len(sir) == 1 and sir[0]['badge'] == 'T' and sir[0]['detail'] == '16 km · scramble strength 3' and not s3['webs'] and head_ok(s3),
          f'Siren launched: chip {sir}, no fighter web ({s3["webs"]}), headline = PYFA CORE')
    t_pt = s3['abTitles'].get(f'{SIREN}:6436', '')
    check('not counted in the times' in t_pt, f'point hover: {t_pt!r}')
    # an Archon with Cenobites: the neutralizer
    paste(pg, ARCHON)
    pg.wait_for_selector(f'{R} .dmg-card [data-out="head"]:not(:empty)', timeout=60000); settle(pg)
    s4 = pg.evaluate(STATE)
    cen = [c for c in s4['chips'] if c['name'] == 'Cenobite II']
    check(len(cen) == 1 and cen[0]['badge'] == 'C' and cen[0]['detail'] == '12.5+5 km · 297 GJ/cycle (49.5 GJ/s)', f'Archon: Cenobite II chip {cen}')
    check(['neut', 12500] in s4['zones'] and not s4['webs'], f'the chart\'s C neut zone reaches 12.5 km, no web: {s4["zones"]}')
    t_n = s4['abTitles'].get(f'{CENOBITE}:6434', '')
    check('Shown on' in t_n and 'not counted in the times' in t_n, f'neutralizer hover: {t_n!r}')
    check(not errs, f'no page errors {errs[:2]}')
    pg.close()
    # phone
    pg = b.new_page(viewport={'width': 390, 'height': 900}, is_mobile=True, has_touch=True, device_scale_factor=2)
    errs2 = []; pg.on('pageerror', lambda e: errs2.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML); pg.evaluate("localStorage.clear()"); pg.reload()
    pg.click('#tabBtnFit'); paste(pg, ARCHON)
    pg.evaluate(f"() => {{ const b = document.querySelector('{R} button.cc-row[data-card=\"ewar\"]'); if(b) b.click(); }}"); settle(pg)
    ph = pg.evaluate(f"""() => {{ const ew = document.querySelector('{R} .ewar-card'); if(!ew) return null; const cr = ew.getBoundingClientRect();
      return {{chips: [...ew.querySelectorAll('.ewar-chip')].map(ch => {{ const r = ch.getBoundingClientRect(); return r.left >= cr.left - 0.5 && r.right <= cr.right + 0.5; }}),
        scroll: [document.documentElement.scrollWidth, innerWidth]}}; }}""")
    check(ph and ph['chips'] and all(ph['chips']) and ph['scroll'][0] <= ph['scroll'][1], f'390 px: chips inside the card, no sideways scroll {ph}')
    check(not errs2, f'phone: no page errors {errs2[:2]}')
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
