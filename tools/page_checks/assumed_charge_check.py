"""A weapon with no charge loaded: the charge aboard that's their best against you is assumed (v2026.10.14.67; the owner via
the inbox: a pasted Nergal "shows zero dps" -- "the zero was on the matchup card"; then "Assume a charge" and "Their
best against you").

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/assumed_charge_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The numbers are checked against pyfa by tools/independent_checks/check_weakness_picks.py (the assumed charge is the one
its independent order puts first, and the Matchup board's four numbers are the whole fit's with it loaded) and the
golden nergal / ikitursa / babaroga max-spool fits; this checks the page around them, with the Nergal the owner pasted
(tools/independent_checks/fits/nergal_no_charge_loaded.eft):
  * Firepower keeps the range of every charge aboard (Occult S at pyfa's 642 with the Nergal's max spool-up bonus);
  * with no ship saved, Damage Application charts it: one amber line "Assumed loaded: <charge>" with the sentence on
    hover, no "Not in the chart yet ... no loaded charge" note, the headline = PYFA CORE at the card's point with the
    model's application (which holds the assumed charge), raw = that charge's DPS;
  * with a ship saved, the Matchup board isn't 0 / "holds" / "edge: you": "DPS applied to you" = the card's headline,
    marked (.is-assumed, the sentence on hover), the "you last" why text says which charge is assumed, and it is the
    charge the My Ship Perspective's picks name first ("What the Nergal should use against you");
  * moving the range doesn't move the headline's box (its width comes from every candidate);
  * no NaN / undefined, no page errors.
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esi_from_sde import route_all
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
CHROMIUM = os.environ.get('CHROMIUM_PATH') or ('/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') else None)
FITS = os.path.join(HERE, '..', 'independent_checks', 'fits')
NERGAL = open(os.path.join(FITS, 'nergal_no_charge_loaded.eft'), encoding='utf-8').read()
OSPREY = open(os.path.join(FITS, 'osprey_navy_issue_mine.eft'), encoding='utf-8').read()
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
CARD = f"""() => {{ const card = [...document.querySelectorAll('{R} .dmg-card')].find(c => c._dmg && c._dmg.side !== 'mine'); if(!card) return null;
  const c = card._dmg, m = dmgModel(c.f, c.T, c.f.dmg);
  const p = {{distance: c.f.dmg.range, tgtSpeed: m.ySpeed, tgtAngle: c.f.dmg.mode === 'orbit' ? 90 : 0, atkSpeed: m.tSpeed, atkAngle: c.f.dmg.theirMode === 'orbit' ? 90 : 0, ignoreLockRange: true}};
  const as = card.querySelector('.dmg-assumed'), note = card.querySelector('.dmg-note'), head = card.querySelector('[data-out="head"]');
  return {{head: head.textContent, headW: head.getBoundingClientRect().width, cur: pyfaAppliedDpsProjected(m.app, m.tgt, p), raw: m.raw,
    assumed: (m.app.assumed || []).map(a => a.charge), weapons: m.app.weapons.map(w => [w.ammoName, w.dps]),
    line: as ? [as.textContent, as.title, getComputedStyle(as).color] : null, note: note ? note.textContent : '', text: card.innerText}}; }}"""
ROWS = f"""() => Object.fromEntries([...document.querySelectorAll('{R} .ammo-dps-row')].map(r => [r.children[0].textContent.trim(), r.querySelector('.ammo-dps-value').textContent.trim()]))"""

with sync_playwright() as p:
    b = p.chromium.launch(**({'executable_path': CHROMIUM} if CHROMIUM else {}))
    ctx = b.new_context(viewport={'width': 1440, 'height': 1000}); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML); pg.evaluate("localStorage.clear()"); pg.reload()
    pg.click('#tabBtnFit'); paste(pg, NERGAL)
    rows = pg.evaluate(ROWS)
    check(rows.get('Occult S') == '642' and rows.get('Meson Exotic Plasma S') == '371', f'Firepower keeps every charge aboard, Occult S 642 with the max spool-up bonus ({rows})')
    pg.wait_for_selector(f'{R} .dmg-card [data-out="head"]:not(:empty)', timeout=60000)
    c = pg.evaluate(CARD)
    check(c and c['assumed'] and c['line'] and c['line'][0] == f"Assumed loaded: {c['assumed'][0]}" and 'has no charge loaded' in c['line'][1]
          and 'rgb(' in c['line'][2] and 'no loaded charge' not in c['note'], f'no ship saved: the card charts it, "{c and c["line"] and c["line"][0]}" ({c and c["note"]!r})')
    check(c and c['head'] == f"{round(c['cur']):,}" and int(c['head'].replace(',', '')) > 0, f'headline {c and c["head"]} = PYFA CORE {c and c["cur"]}')
    check(c and abs(c['raw'] - sum(w[1] for w in c['weapons'])) < 1e-6 and c['weapons'][0][0] == c['assumed'][0], f'raw = the assumed charge\'s DPS {c and c["weapons"]}')
    w0 = c['headW']
    pg.evaluate(f"""() => {{ const r = document.querySelector('{R} .dmg-card input[data-in="range"]'); r.value = 25000; r.dispatchEvent(new Event('input', {{bubbles: true}})); r.dispatchEvent(new Event('change', {{bubbles: true}})); }}""")
    pg.wait_for_timeout(500)
    c2 = pg.evaluate(CARD)
    check(abs(c2['headW'] - w0) < 0.5 and c2['head'] == f"{round(c2['cur']):,}", f'range 25 km: the headline box keeps its width ({w0} -> {c2["headW"]}), {c2["head"]} = PYFA CORE, assumed {c2["assumed"]}')
    check(not any(x in c2['text'] for x in ('NaN', 'undefined')), 'card has no NaN / undefined')
    # with a ship saved: the board
    pg.click('#myShipChip'); pg.fill('#myShipEft', OSPREY); pg.click('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-tiles'); pg.keyboard.press('Escape')
    pg.click('#tabBtnFit'); paste(pg, NERGAL)
    pg.wait_for_function(f"() => {{ const b = document.querySelector('{R} .mys-board'); return b && !/…/.test(b.textContent); }}", timeout=60000); settle(pg, 800)
    cells = pg.evaluate(f"() => Object.fromEntries([...document.querySelector('{R} .mys-board').querySelectorAll('[data-cell]')].map(c => [c.dataset.cell, [(c.querySelector('.mys-cell-v') || c).textContent, c.classList.contains('is-assumed'), c.title || '']]))")
    c = pg.evaluate(CARD)
    check(cells['their'][0] not in ('0', '') and cells['their'][0] == c['head'] and cells['youLast'][0] != 'holds', f'board: DPS applied to you {cells["their"][0]} = the card {c["head"]}, you last {cells["youLast"][0]}, {cells["edge"][0]}')
    check(cells['their'][1] and f"{c['assumed'][0]} from their cargo is assumed" in cells['their'][2], f'"DPS applied to you" marked, hover names {c["assumed"]} ({cells["their"][2][:90]})')
    why = pg.evaluate("() => [...document.querySelectorAll('.mys-why-sr')].map(x => x.textContent).join(' | ')")
    check('has no charge loaded' in why and c['assumed'][0] in why and not any(x in why for x in ('NaN', 'undefined')), 'the "you last" why says which charge is assumed')
    pg.click(f'{R} .mys-sw-btn.is-mine'); pg.wait_for_selector(f'{R} .mys-mine-view .fit-layout'); settle(pg)
    pg.wait_for_function(f"() => /should use against you/.test(document.querySelector('{R} .mys-mine-view').innerText)", timeout=60000)
    pick = pg.evaluate(f"() => {{ const t = [...document.querySelectorAll('{R} .mys-mine-view .wp-stat')].find(x => /Disintegrator/.test(x.textContent)); return t ? t.querySelector('.wp-value').textContent : null; }}")
    check(pick == c['assumed'][0], f'the assumed charge is the pick "What the Nergal should use against you": {pick} = {c["assumed"][0]}')
    check(not errs, f'no page errors {errs}')
    ctx.close(); b.close()
print(f'FAILURES: {fails}')
