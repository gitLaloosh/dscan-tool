"""The Fit card's ring as a Workbench-style track (v2026.10.14.75, roadmap/charges-plan.md delivery 1; the owner: "Workbench-
style track", and a weapon shows its charge's icon: "A: charge icon").

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/ring_track_check.py [index.html]   -> 'FAILURES: N' (must be 0)

Pasted fits (ESI served from the SDE) and a killmail (Pilot Analyzer, zKillboard mocked as in last_kill_check.py):
  * one position per slot the hull has: each rack's tiles plus its empty-slot outlines = estimate.slots (pyfa's counts,
    checked by check_slots.py), a T3 Tengu's subsystem slots included;
  * every weapon copy shows the charge in its own slot: a Drake with 3 Scourge, 2 Nova and 1 empty launcher shows those
    icons in that order, and the empty one shows the launcher; the hover names weapon, charge and state; a Loki killmail
    shows the charge on each autocannon's flag; a module that isn't a weapon keeps its own icon;
  * each tile is turned along the circle (its turn = its position's angle, never upside down) and its icon is upright;
  * the tiles stay buttons that set the state (a click recalculates);
  * 1440, 390 and 320 px: no sideways scroll; no page errors.
v2026.10.14.74 fails (no empty slots, no charge icons, upright frames).
"""
import sys, os, re, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
_src = open(os.path.join(HERE, 'last_kill_check.py'), encoding='utf-8').read()
_ns = {'__file__': os.path.join(HERE, 'last_kill_check.py'), '__name__': 'last_kill_mocks'}
exec(compile(_src.split('\ndef desktop(b):')[0], 'last_kill_check.py', 'exec'), _ns)
from esi_from_sde import route_all, icon_route
from playwright.sync_api import sync_playwright

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
_ns['HTML'] = HTML
R = '#fitAnalyzerResults'
DRAKE = """[Drake, Mixed charges]
Ballistic Control System II
Ballistic Control System II
Damage Control II

Large Shield Extender II
Large Shield Extender II
10MN Afterburner II

Heavy Missile Launcher II, Scourge Heavy Missile
Heavy Missile Launcher II, Scourge Heavy Missile
Heavy Missile Launcher II, Scourge Heavy Missile
Heavy Missile Launcher II, Nova Heavy Missile
Heavy Missile Launcher II, Nova Heavy Missile
Heavy Missile Launcher II

Medium Core Defense Field Extender I
"""
TENGU = """[Tengu, Subsystems]
Ballistic Control System II

Large Shield Extender II
10MN Afterburner II

Heavy Assault Missile Launcher II, Scourge Heavy Assault Missile
Heavy Assault Missile Launcher II, Scourge Heavy Assault Missile

Medium Core Defense Field Extender I

Tengu Core - Augmented Graviton Reactor
Tengu Defensive - Covert Reconfiguration
Tengu Offensive - Accelerated Ejection Bay
Tengu Propulsion - Interdiction Nullifier
"""
SCOURGE, NOVA, HML = 209, 206, 2410
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok
# Every tile / empty slot: its rack (data / title), its position angle, its frame's turn and its icon's net turn.
RING = """(R) => {
  const ring = document.querySelector(R + ' .fit-ring'); if(!ring) return null;
  const rb = ring.getBoundingClientRect(), cx = rb.left + rb.width / 2, cy = rb.top + rb.height / 2;
  const ang = m => Math.atan2(m.b, m.a) * 180 / Math.PI;
  const est = (() => { const c = [...document.querySelectorAll(R + ' .dmg-card')].find(c => c._dmg && c._dmg.side !== 'mine'); return c ? c._dmg.f.estimate : null; })();
  const tiles = [...ring.querySelectorAll('.ms-tile, .fr-empty')].map(e => {
    const b = e.getBoundingClientRect(), x = b.left + b.width / 2 - cx, y = b.top + b.height / 2 - cy, img = e.querySelector('img');
    const turn = ang(new DOMMatrix(getComputedStyle(e).transform));
    return {empty: e.classList.contains('fr-empty'), rack: e.classList.contains('fr-empty') ? e.title.replace(/^Empty (\\w+) slot$/, '$1') : null,
      typeId: Number(e.dataset.typeId || 0), copy: Number(e.dataset.copy || 0), charge: Number(e.dataset.chargeId || 0), src: img ? img.src : '', title: e.title || '',
      pos: Math.atan2(y, x) * 180 / Math.PI, turn, net: img ? turn + ang(new DOMMatrix(getComputedStyle(img).transform)) : 0, tag: e.tagName,
      shown: !!img && img.complete && img.naturalWidth > 0 && getComputedStyle(img).display !== 'none'};
  });
  return {tiles, slots: est && est.slots, items: est ? est.moduleStates.items.map(i => ({typeId: i.typeId, slot: i.slot, qty: i.qty, name: i.name})) : [],
    scroll: [document.documentElement.scrollWidth, innerWidth]};
}"""
def layout_total(pg):   # the Firepower card's total as shown (layout_check.py's total_dps)
    return pg.evaluate("""(scope) => { const c = document.querySelector(scope + ' .fl-stats');
      const row = c.querySelector('button.cc-row[data-card="fp"]');
      if(row) return row.querySelector('.cc-sum').textContent.split(' DPS')[0];
      return c.innerText.split('TOTAL DPS')[1].trim().split(/\\s+/)[0]; }""", R)
def norm(a): return (a + 180) % 360 - 180
def want_turn(pos):   # fitRingTileTurn: along the circle, never upside down
    r = norm(pos + 90)
    return r - 180 if r > 90 else r + 180 if r < -90 else r
def rack_of(t, items):
    if t['empty']: return t['rack']
    return next((i['slot'] for i in items if i['typeId'] == t['typeId']), None)

def common(tag, g, rack_counts=True, icons=True):
    if not g: check(False, f'{tag}: no ring'); return
    tiles, slots, items = g['tiles'], g['slots'] or {}, g['items']
    if rack_counts:
        got = {}
        for t in tiles: r = rack_of(t, items); got[r] = got.get(r, 0) + 1
        fitted = {}
        for i in items: fitted[i['slot']] = fitted.get(i['slot'], 0) + round(i['qty'])
        want = {r: max(int(round(slots.get(r, 0))), fitted.get(r, 0)) for r in ('high', 'mid', 'low', 'rig', 'subsystem') if max(int(round(slots.get(r, 0))), fitted.get(r, 0))}
        check(got == want, f'{tag}: one position per slot, fitted + empty per rack {got} = the hull\'s slots {want}')
    bad_turn = [round(t['turn'] - want_turn(t['pos']), 1) for t in tiles if abs(norm(t['turn'] - want_turn(t['pos']))) > 1]
    bad_up = [round(t['net'], 1) for t in tiles if icons and not t['empty'] and (not t['shown'] or abs(norm(t['net'])) > 1)]
    check(not bad_turn and not bad_up, f'{tag}: every frame turned along the circle ({bad_turn or "ok"}), every icon upright ({bad_up or "ok"})')
    check(g['scroll'][0] <= g['scroll'][1], f'{tag}: no sideways scroll {g["scroll"]}')

SEEN = {}
with sync_playwright() as p:
    b = p.chromium.launch(**({'executable_path': _ns['CHROMIUM']} if _ns.get('CHROMIUM') else {}))
    for w in (1440, 390, 320):
        pg = b.new_page(viewport={'width': w, 'height': 1000})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        route_all(pg); pg.route(re.compile(r'https://images\.evetech\.net/.*'), icon_route)   # the icons load (their own turn is checked)
        pg.goto('file://' + HTML); pg.evaluate("localStorage.clear(); localStorage.setItem('dscanFitView', 'ring')"); pg.reload()
        pg.click('#tabBtnFit')
        for name, eft in (('drake', DRAKE), ('tengu', TENGU)):
            pg.evaluate("() => { const r = document.querySelector('#fitAnalyzerResults'); if(r) r.innerHTML = ''; }")
            pg.fill('#fitAnalyzerInput', eft); pg.click('#fitAnalyzerBtn'); pg.wait_for_selector(f'{R} .fit-layout', timeout=60000)
            if w == 1440: pg.wait_for_selector(f'{R} .dmg-card', state='attached', timeout=60000)
            pg.wait_for_timeout(800)
            if not pg.locator(f'{R} .fit-ring').count() or not pg.locator(f'{R} .fit-ring').is_visible():
                pg.click(f'{R} button.cc-toggle[data-card="fit"]'); pg.wait_for_timeout(400)
            g = pg.evaluate(RING, R); tag = f'{w}px {name}'
            if g and w == 1440: SEEN[name] = (g['slots'], g['items'])   # the estimate (the Damage Application card keeps it; it's drawn at 1440)
            elif g: g['slots'], g['items'] = SEEN[name]
            common(tag, g)
            if not g: continue
            if name == 'drake':
                hml = sorted([t for t in g['tiles'] if t['typeId'] == HML], key=lambda t: t['copy'])
                ch = [t['charge'] or None for t in hml]
                srcs = [int(re.search(r'/types/(\d+)/', t['src']).group(1)) if re.search(r'/types/(\d+)/', t['src']) else None for t in hml]
                check(ch == [SCOURGE] * 3 + [NOVA] * 2 + [None] and srcs == [SCOURGE] * 3 + [NOVA] * 2 + [HML],
                      f'{tag}: each launcher shows the charge in its own slot, the empty one the launcher ({ch}, icons {srcs})')
                t0 = hml[0]['title'] if hml else ''
                check(t0.startswith('Heavy Missile Launcher II · Scourge Heavy Missile: Active.') and hml[-1]['title'].startswith('Heavy Missile Launcher II: Active.'),
                      f'{tag}: the hover names weapon, charge and state ({t0[:70]!r} / {hml[-1]["title"][:40] if hml else ""!r})')
                others = [t for t in g['tiles'] if not t['empty'] and t['typeId'] != HML]
                check(all(t['charge'] == 0 and f"/types/{t['typeId']}/" in t['src'] for t in others), f'{tag}: modules that aren\'t weapons keep their own icon')
                if w == 1440:
                    d0 = layout_total(pg)
                    # two launchers to online (the engine counts active copies per type; one of the six has no charge)
                    pg.locator(f'{R} .fit-ring button.ms-tile[data-type-id="{HML}"][data-from="active"]').first.click()
                    pg.wait_for_function("() => !document.querySelector('#fitAnalyzerResults .fit-card-busy')", timeout=30000); pg.wait_for_timeout(300)
                    pg.locator(f'{R} .fit-ring button.ms-tile[data-type-id="{HML}"][data-from="active"]').first.click()
                    pg.wait_for_function("() => document.querySelector('#fitAnalyzerResults button.ms-reset.is-custom') && !document.querySelector('#fitAnalyzerResults .fit-card-busy')", timeout=30000); pg.wait_for_timeout(300)
                    d1 = layout_total(pg)
                    g2 = pg.evaluate(RING, R)
                    check(d1 != d0 and any(t['charge'] == SCOURGE for t in g2['tiles']), f'{tag}: a launcher tile still sets its state ({d0} -> {d1} DPS), charges still shown')
            else:
                # pyfa's count is the hull's maxSubSystems (5; four are fitted), as pyfa's own fitting view draws it
                check((g['slots'] or {}).get('subsystem') == 5 and any(t['empty'] and t['rack'] == 'subsystem' for t in g['tiles']) and (g['slots'] or {}).get('high', 0) > 0,
                      f'{tag}: the Tengu\'s subsystem slots and the high slots its subsystems give ({g["slots"]})')
        check(not errs, f'{w}px: no page errors {errs[:2]}')
        pg.close()
    # a killmail: the Loki loss of last_kill_check.py's mocks, autocannons with their flags' charges
    ctx, pg, errs = _ns['start'](b, 1440, 1000)
    pg.evaluate("localStorage.setItem('dscanFitView', 'ring')")
    pg.wait_for_selector('#fitResults .fit-ring', timeout=60000); pg.wait_for_timeout(600)
    g = pg.evaluate(RING, '#fitResults .subtab-panel:not([style*="none"])')
    km = _ns['KM'][9100001]['victim']['items']
    flags = {}
    for it in km:
        if 27 <= it['flag'] <= 34: flags.setdefault(it['flag'], []).append(it['item_type_id'])
    if g:
        wid = next((t['typeId'] for t in g['tiles'] if t['charge']), None)
        want = [next((x for x in flags[f] if x != wid), None) for f in sorted(flags) if wid in flags[f]]
        got = [t['charge'] for t in sorted([t for t in g['tiles'] if t['typeId'] == wid], key=lambda t: t['copy'])]
        check(wid is not None and got == want, f'killmail Loki: each autocannon shows its own flag\'s charge ({got} = {want})')
        common('killmail Loki', g, rack_counts=False, icons=False)   # its mocks serve no icons; the pasted fits check them
    else: check(False, 'killmail Loki: no ring')
    check(not errs, f'killmail: no page errors {errs[:2]}')
    ctx.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
