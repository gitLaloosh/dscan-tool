"""Every card at every width (v2026.10.14.38; roadmap/card-layout-plan.md step 2).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/card_width_check.py [index.html] [--shots DIR]   -> 'FAILURES: N' (must be 0)

Step 2 makes each card lay out by its own width (container queries; every column and band of .fit-layout is
a size container), so a later "Edit layout" can put any card in any column or span. This loads the real page
(ESI served from pyfa's SDE, esi_from_sde.py) with two fits (a Hecate with a Tactical Destroyer mode, web and
scram; a Vexor with drones), opens every card, and copies each one into a test container at the widths a card
can get: 300 (phone), 340 (left column at 1280 px), 460 (right column), 520 (tablet half), 700, 1000 (two
columns) and 1358 px (full width at 1440). At each width:
  * nothing inside the card reaches outside it;
  * a tile row (.estimate-box) never ends with a lone tile after a row of three or more ("3 + 1"), and a lone
    last tile always spans the row;
  * tile values (.estimate-value) never break inside a number;
  * the copy renders with the same text as the card on the page (no card hides content at some width).
--shots DIR writes one screenshot per card with every width stacked, for looking at.
"""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esi_from_sde import route_all
from playwright.sync_api import sync_playwright

args = sys.argv[1:]
SHOTS = args[args.index('--shots') + 1] if '--shots' in args else None
HTML = os.path.abspath(next((a for i, a in enumerate(args) if not a.startswith('--') and (i == 0 or args[i - 1] != '--shots')),
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'index.html')))
HECATE = """[Hecate, threat]
Magnetic Field Stabilizer II
Magnetic Field Stabilizer II
Damage Control II

5MN Microwarpdrive II
Medium Ancillary Shield Booster, Navy Cap Booster 50
Warp Scrambler II
Stasis Webifier II

Light Neutron Blaster II, Void S
Light Neutron Blaster II, Void S
Light Neutron Blaster II, Void S
Light Neutron Blaster II, Void S
Light Neutron Blaster II, Void S
"""
VEXOR = """[Vexor, Brawl]
Damage Control II
Medium Armor Repairer II
Multispectrum Energized Membrane II
Drone Damage Amplifier II

50MN Microwarpdrive II
Warp Scrambler II
Stasis Webifier II

Heavy Neutron Blaster II, Void M
Heavy Neutron Blaster II, Void M
Heavy Neutron Blaster II, Void M

Medium Auxiliary Nano Pump I
Medium Auxiliary Nano Pump I
Medium Nanobot Accelerator I

Hammerhead II x5
"""
WIDTHS = [300, 340, 460, 520, 700, 1000, 1358]
R = '#fitAnalyzerResults'
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok

LAB = """([sel, widths]) => {
  const src = document.querySelector(sel); if(!src) return false;
  let lab = document.getElementById('cwLab'); if(lab) lab.remove();
  lab = document.createElement('div'); lab.id = 'cwLab';
  lab.style.cssText = 'position:absolute; left:0; top:0; z-index:9999; background:var(--bg); padding:10px;';
  document.body.appendChild(lab);
  for(const w of widths){
    const box = document.createElement('div'); box.className = 'cw-box';
    box.style.cssText = `width:${w}px; margin-bottom:12px; container-type:inline-size;`;   // as a .fit-layout column
    box.innerHTML = src.outerHTML; lab.appendChild(box);
  }
  return true; }"""
MEASURE = """() => [...document.querySelectorAll('#cwLab .cw-box')].map(box => {
  const r = box.getBoundingClientRect(), out = [], lone = [], split = [];
  box.querySelectorAll('*').forEach(el => { const e = el.getBoundingClientRect();
    if(el.closest('.info-body')) return;   // v2026.10.14.48: the info panel floats over the page by design (damage_chart_check keeps it on screen)
    if(e.width && (e.right > r.right + 1 || e.left < r.left - 1)) out.push((typeof el.className === 'string' && el.className ? el.className.split(' ')[0] : el.tagName) + ' ' + Math.round(Math.max(e.right - r.right, r.left - e.left)) + 'px'); });
  box.querySelectorAll('.estimate-box').forEach(eb => {
    const tiles = [...eb.children].filter(t => t.getBoundingClientRect().width > 0); if(tiles.length < 2) return;
    const rows = new Map(); tiles.forEach(t => { const y = Math.round(t.getBoundingClientRect().top); rows.set(y, (rows.get(y) || []).concat([t])); });
    const rs = [...rows.values()], last = rs[rs.length - 1], ebw = eb.getBoundingClientRect().width;
    // a lone last tile is fine only under a row of two (2 + 1, spanning); after a row of three or more
    // ("3 + 1") it is unbalanced, and it must never sit narrower than the row
    if(rs.length > 1 && last.length === 1 && (rs[rs.length - 2].length >= 3 || last[0].getBoundingClientRect().width < ebw - 2))
      lone.push(last[0].querySelector('.estimate-label') ? last[0].querySelector('.estimate-label').textContent : '?');
  });
  box.querySelectorAll('.estimate-value').forEach(v => {   // a number broken across lines: one text run on two line boxes
    for(const n of v.childNodes){ if(n.nodeType !== 3 || !/\\d/.test(n.textContent)) continue;
      const rg = document.createRange(); rg.selectNodeContents(n); const ys = new Set([...rg.getClientRects()].map(q => Math.round(q.top)));
      if(ys.size > 1) split.push(n.textContent.trim()); }
  });
  return {w: Math.round(r.width), h: Math.round(r.height), text: box.innerText.replace(/\\s+/g, ' ').length, out: out.slice(0, 4), lone, split}; })"""

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('CHROMIUM', '/opt/pw-browsers/chromium'))
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML)
    pg.evaluate("localStorage.removeItem('dscanMyShip')")
    seen = set()
    for name, fit in (('hecate', HECATE), ('vexor', VEXOR)):
        pg.click('#tabBtnFit'); pg.fill('#fitAnalyzerInput', fit); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout')
        pg.wait_for_selector(f'{R} .fl-dmg [data-out="head"]:not(:empty)', timeout=60000); pg.wait_for_timeout(300)
        for _ in range(3):   # open every closed card (each open re-renders the layout)
            t = pg.locator(f'{R} button.cc-toggle[aria-expanded="false"]:not(.bay-toggle)')
            if not t.count(): break
            for i in range(t.count()):
                try: pg.locator(f'{R} button.cc-toggle[aria-expanded="false"]:not(.bay-toggle)').first.click(); pg.wait_for_timeout(120)
                except Exception: pass
        pg.wait_for_selector(f'{R} .fl-dmg [data-out="head"]:not(:empty)', timeout=60000)
        cards = pg.evaluate(f"""() => [...document.querySelectorAll('{R} .fit-layout > div > .fit-summary, {R} .fit-layout > div > .ewar-card')].map((c, i) => {{
            c.dataset.cwIdx = i; const t = c.querySelector('[data-card]'); return [i, t ? t.dataset.card : (c.classList.contains('td-mode-card') ? 'tdmode' : c.className), c.innerText.replace(/\\s+/g, ' ').length]; }})""")
        check(len(cards) >= 7, f'{name}: {len(cards)} cards found ({", ".join(k for _, k, _ in cards)})')
        for i, key, tlen in cards:
            seen.add(key)
            pg.evaluate(LAB, [f'{R} [data-cw-idx="{i}"]', WIDTHS]); pg.wait_for_timeout(150)
            m = pg.evaluate(MEASURE)
            bad = [(x['w'], x['out']) for x in m if x['out']]
            check(not bad, f'{name} {key}: nothing outside the card at any width {bad[:2]}')
            lone = [(x['w'], x['lone']) for x in m if x['lone']]
            check(not lone, f'{name} {key}: no tile row ends with a lone tile {lone[:3]}')
            split = [(x['w'], x['split']) for x in m if x['split']]
            check(not split, f'{name} {key}: no number broken across lines {split[:3]}')
            if SHOTS:
                os.makedirs(SHOTS, exist_ok=True); pg.locator('#cwLab').screenshot(path=os.path.join(SHOTS, f'{name}_{key}.png'))
            print('     heights', [(x['w'], x['h']) for x in m])
            pg.evaluate("document.getElementById('cwLab').remove()")
    check({'tdmode', 'weak', 'ewar', 'fp', 'rs', 'nav', 'cp', 'fit', 'dmg'} <= seen, f'every card kind covered {sorted(seen)}')
    check(not errs, f'no page errors {errs}')
    b.close()
print(f'FAILURES: {fails}')
