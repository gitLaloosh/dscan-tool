"""Weaknesses picks for fighters: one pick per class (v2026.10.14.72, fighter gaps delivery 4; the owner: "One tile per class",
abilities "As set in the Fighter bay").

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/fighter_picks_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The numbers are checked against pyfa by tools/independent_checks/check_weakness_picks.py (the nyx pairs: every light and
heavy type flown in its class's squadrons, an oracle fit per candidate, the strip's time to kill); this checks the page:
  * a Nyx saved as My Ship (Einherji II, Firbolg II, Templar II, Gram II light; Mantis II, Ametat II heavy) against a pasted
    Omen: the threat view shows "Your light fighters" and "Your heavy fighters" tiles, each "<type> ×<squadrons>", equal to
    the page's own wpRank; no "Fighters aren't ranked yet"; the light squadrons fill the tubes the heavies leave (3 + 2 = 5);
    each hover names the next best;
  * an Ametat's Bomb switched on in my ship's Fighter bay: the heavy pick follows (the abilities as set) and is still the
    page's own wpRank;
  * the My ship view with the Nyx pasted as the threat and the Omen as my ship: "Their light fighters" / "Their heavy fighters";
  * the collapsed Weaknesses row names the fighter picks; the card's info names fighters;
  * 390 px: tiles inside the card, no sideways scroll. No page errors.
v2026.10.14.71 fails (no fighter tiles, "Fighters aren't ranked yet").
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esi_from_sde import route_all
from playwright.sync_api import sync_playwright

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')),
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'index.html')))
CHROMIUM = os.environ.get('CHROMIUM_PATH') or ('/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') else None)
NYX = """[Nyx, fighters]
Damage Control II
Drone Damage Amplifier II
Drone Damage Amplifier II
Fighter Support Unit II



Einherji II x18
Firbolg II x18
Templar II x6
Mantis II x12
Ametat II x12
Gram II x12
"""
OMEN = """[Omen, lasers]
Heat Sink II
Heat Sink II
Damage Control II
800mm Steel Plates II

10MN Afterburner II
Warp Scrambler II
Stasis Webifier II

Focused Medium Pulse Laser II, Scorch M
Focused Medium Pulse Laser II, Scorch M
Focused Medium Pulse Laser II, Scorch M
Focused Medium Pulse Laser II, Scorch M
"""
R = '#fitAnalyzerResults'
TV, MV = f'{R} .mys-threat-view', f'{R} .mys-mine-view'
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok
def settle(pg, ms=400):
    pg.wait_for_timeout(ms); pg.wait_for_function("() => !document.querySelector('.fit-card-busy')", timeout=60000); pg.wait_for_timeout(ms)
EXPECT = """async ([scope, side]) => {
  const host = document.querySelector(scope + ' .mys-switch-host'); const tf = mysStripThreatF(host);
  const st = tf.dmg || dmgDefaults(tf.estimate.application); const F = mysFight(tf, myShip.f, st);
  const c = await wpCandidates(side === 'yours' ? myShip.f : tf);
  const r = side === 'yours' ? wpRank(c, F.mApp, F.them, F.qOut, tf.estimate) : wpRank(c, F.tApp, F.me, F.qIn, myShip.f.estimate);
  const d = document.createElement('div'); d.innerHTML = wpCardHtml(r, side, 'x', '');
  return [...d.querySelectorAll('.wp-stat')].map(t => [...t.querySelectorAll('.rec-label, .wp-value, .wp-sub')].map(e => e.textContent));
}"""
def tiles(pg, sel):
    return pg.evaluate(f"() => [...document.querySelectorAll('{sel} .weak-picks .wp-stat')].map(t => [...t.querySelectorAll('.rec-label, .wp-value, .wp-sub')].map(e => e.textContent))")
def titles(pg, sel):
    return pg.evaluate(f"() => [...document.querySelectorAll('{sel} .weak-picks .wp-stat')].map(t => t.title)")

with sync_playwright() as p:
    b = p.chromium.launch(**({'executable_path': CHROMIUM} if CHROMIUM else {}))
    pg = b.new_page(viewport={'width': 1440, 'height': 1000})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML); pg.evaluate("localStorage.clear()"); pg.reload()
    pg.click('#myShipChip'); pg.fill('#myShipEft', NYX); pg.click('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-tiles', timeout=60000); pg.keyboard.press('Escape')
    pg.click('#tabBtnFit'); pg.fill('#fitAnalyzerInput', OMEN); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout', timeout=60000)
    pg.wait_for_selector(f'{TV} .weak-picks[data-filled]', timeout=120000); settle(pg, 800)
    t1 = tiles(pg, TV)
    labels = [x[0] for x in t1]
    check(labels == ['Your light fighters', 'Your heavy fighters'] and t1 == pg.evaluate(EXPECT, [R, 'yours']), f'threat view: a light and a heavy tile, the page\'s own wpRank ({t1})')
    import re
    cnt = [int(re.search(r'×(\d+)', x[1]).group(1)) for x in t1] if len(t1) == 2 else []
    check(cnt == [3, 2], f'light squadrons fill the tubes the heavies leave: {cnt}')
    ti = titles(pg, TV)
    check(len(ti) == 2 and all('Then ' in x for x in ti) and 'as set in the Fighter bay' in ti[0], f'hovers name the next best: {[x[:90] for x in ti]}')
    check("Fighters aren't ranked yet" not in pg.inner_text(f'{TV} .weak-picks'), 'no "Fighters aren\'t ranked yet"')
    info = pg.evaluate("() => CARD_INFO.weak.join(' ')")
    check('Only the ammo, drones and fighters aboard' in info and 'one pick per class' in info, 'the card\'s info names fighters')
    # the Ametat's bomb on in my ship's Fighter bay (My ship view): back in the threat view the heavy pick follows
    before = t1[1] if len(t1) == 2 else None
    pg.click(f'{R} .mys-sw-btn.is-mine'); pg.wait_for_selector(f'{MV} .fb-ab[data-type-id="40560"][data-effect="6485"]', timeout=60000); settle(pg)
    pg.click(f'{MV} .fb-ab[data-type-id="40560"][data-effect="6485"]'); settle(pg, 1200)
    pg.click(f'{R} .mys-sw-btn.is-threat'); pg.wait_for_selector(f'{TV} .weak-picks[data-filled]', timeout=120000); settle(pg, 1500)
    t2 = tiles(pg, TV)
    exp2 = pg.evaluate(EXPECT, [R, 'yours'])
    bomb_on = pg.evaluate("() => (myShip.f.estimate.fighterStates.items.find(i => i.name === 'Ametat II').abilities.find(a => a.effectId === 6485) || {}).on")
    check(bool(bomb_on) and t2 == exp2 and len(t2) == 2, f'bomb on in my Fighter bay: heavy pick {before} -> {t2[1] if len(t2) == 2 else t2} = the page\'s own wpRank')
    # collapsed row
    pg.click(f'{TV} button.cc-toggle[data-card="weak"]'); settle(pg, 600)
    summ = pg.evaluate(f"() => {{ const s = document.querySelector('{TV} button.cc-row[data-card=\"weak\"] .wp-sum'); return s ? s.textContent : null; }}")
    names = [x[1].split(' ×')[0] for x in t2]
    check(summ and all(n in summ for n in names), f'collapsed row names the fighter picks: "{summ}"')
    pg.click(f'{TV} button.cc-row[data-card="weak"]'); settle(pg, 400)
    # My ship view: the Nyx as the threat, the Omen as my ship
    pg.evaluate("localStorage.clear()"); pg.reload()
    pg.click('#myShipChip'); pg.fill('#myShipEft', OMEN); pg.click('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-tiles', timeout=60000); pg.keyboard.press('Escape')
    pg.click('#tabBtnFit'); pg.fill('#fitAnalyzerInput', NYX); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout', timeout=60000); settle(pg, 800)
    pg.click(f'{R} .mys-sw-btn.is-mine'); pg.wait_for_selector(f'{MV} .weak-picks[data-filled]', timeout=120000); settle(pg, 800)
    m1 = tiles(pg, MV)
    check([x[0] for x in m1] == ['Their light fighters', 'Their heavy fighters'] and m1 == pg.evaluate(EXPECT, [R, 'theirs']) and 'What the Nyx should use against you' in pg.inner_text(f'{MV} .wp-head'),
          f'My ship view: their light and heavy fighters, the page\'s own wpRank ({m1})')
    check(not errs, f'no page errors {errs[:2]}')
    pg.close()
    # phone
    pg = b.new_page(viewport={'width': 390, 'height': 900}, is_mobile=True, has_touch=True, device_scale_factor=2)
    errs2 = []; pg.on('pageerror', lambda e: errs2.append(str(e)))
    route_all(pg); pg.goto('file://' + HTML); pg.evaluate("localStorage.clear()"); pg.reload()
    pg.tap('#myShipChip'); pg.fill('#myShipEft', NYX); pg.tap('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-tiles', timeout=60000); pg.keyboard.press('Escape')
    pg.tap('#tabBtnFit'); pg.fill('#fitAnalyzerInput', OMEN); pg.tap('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout', timeout=60000)
    pg.wait_for_selector(f'{TV} .weak-picks[data-filled]', timeout=120000); settle(pg, 800)
    ph = pg.evaluate(f"""() => {{ const card = document.querySelector('{TV} .weak-picks').closest('.fit-summary'); const cr = card.getBoundingClientRect();
      return {{inside: [...card.querySelectorAll('.wp-stat')].map(t => {{ const r = t.getBoundingClientRect(); return r.left >= cr.left - 0.5 && r.right <= cr.right + 0.5; }}),
        scroll: [document.documentElement.scrollWidth, innerWidth]}}; }}""")
    check(ph['inside'] and all(ph['inside']) and ph['scroll'][0] <= ph['scroll'][1], f'390 px: tiles inside the card, no sideways scroll {ph}')
    check(not errs2, f'phone: no page errors {errs2[:2]}')
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
