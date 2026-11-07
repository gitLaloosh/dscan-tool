"""Ships on Scan: the System Analyzer's scan rail with hover cards (v2026.11.02.2; Project doc roadmap/scan-rail-plan.md).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/scan_rail_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner: "a breakdown of hulls and their counts (no pilot association, just the hulls and their numbers)"; "placement of the new
card like B but the resistance info and weaknesses become a little hover card instead"; "I like option 1" (the rail beside Local's
results); before the build: D-Scan alone takes the full width; a press pins the card; a "-" distance is its own count; "Cyno
Capable" as a role, with a tag on combat hulls that can fit a cyno. The real page, ESI answered from pyfa's SDE (sa_mocks.route),
a made-up 52-line D-Scan (no real scan, no real names). Everything expected is worked out here, from the SDE:
  * the head: ships, hulls, on grid (≤ 10,000 km), off grid (AU, or more km), no reading ("-");
  * each hull's role from its group, the cyno role and tag from the cyno modules' canFitShipGroup / canFitShipType attributes, role
    order, rows by count then name, each row's count, on-grid count and weakest-type badge; the role bar's legend;
  * the footer: not ships (drones, probe, bubble, citadel), celestials, the unrecognized name;
  * the hover card for 4 hulls: resists weighted by shield / armor / hull HP (from the SDE here), weakest and second, the charge
    names with today's full sentence on hover, the drone, the cyno line, the grid line;
  * hover opens after a short delay and leaving closes it (the card itself can be hovered); focus opens, Esc closes and gives the
    focus back; a press pins it, a press elsewhere closes it; one card at a time; it sits above Local's cards and flips up near
    the bottom of the window; a resize moves it with its row (LESSON #128); no hidden cards built;
  * layouts: Local + D-Scan side by side with the rail sticky; Local only (no rail); D-Scan only (the rail full width, its hulls in
    columns); typed names (no distances: no grid text anywhere); 390 px (stacked, rail first, nothing off the page, rows 44 px, the
    card in place under its row);
  * the scan's ships still feed the Pilot rows (lastScanShips, sa.scanTypes); a fit pasted in the D-Scan box: DSCAN-01, no rail.
v2026.11.02.1 fails (no rail: one card per ship type).
"""
import sys, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from playwright.sync_api import sync_playwright
import sa_mocks as M
import pyfa_sde as P

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok
B = M.byname
# (type, [distances]); '-' = no reading
SHIPS = [('Ferox', ['1,200 km', '1,350 km', '980 km', '2,100 km', '3.2 AU', '3.4 AU', '12 AU', '-']),
         ('Scimitar', ['45 km', '52 km', '61 km', '4.1 AU', '4.0 AU']), ('Basilisk', ['48 km', '50 km', '6.2 AU', '6.0 AU']),
         ('Sabre', ['22 km', '25 km', '1.1 AU']), ('Stiletto', ['14,000 km', '9,999 km']), ('Devoter', ['31 km']),
         ('Curse', ['70 km', '2.2 AU']), ('Falcon', ['-']), ('Damnation', ['90 km']), ('Purifier', ['8.4 AU', '8.4 AU']),
         ('Vedmak', ['30 km', '31 km', '32 km', '7 AU', '7 AU', '7 AU']), ('Loki', ['44 km', '2 AU']), ('Rifter', ['3,039 m', '5 AU', '5 AU']),
         ('Badger', ['120 km']), ('Prowler', ['9 AU']), ('Venture', ['16 km']), ('Cheetah', ['-']), ('Hulk', ['27 km']),
         ('Ibis', ['3 AU']), ('Capsule', ['-', '40 km']), ('Amarr Shuttle', ['17 km'])]
OTHER = [('Warrior II', 6), ('Combat Scanner Probe I', 1), ('Mobile Large Warp Disruptor I', 1), ('Fortizar', 1)]
CELEST = ['Sun G5 (Yellow)', 'Planet (Barren)', 'Stargate (Caldari System)']
UNK = 'Totally Not A Ship'
lines = [f"{B[t]}\tSomeone's {t} {i}\t{t}\t{d}" for t, ds in SHIPS for i, d in enumerate(ds)]
lines += [f"{B[t]}\t{t}\t{t}\t{12 + i} km" for t, n in OTHER for i in range(n)]
lines += [f"\t{c}\t{c}\t{3 + i} AU" for i, c in enumerate(CELEST)] + [f"\t{UNK}\t{UNK}\t20 km"]
SCAN = '\n'.join(lines)
LOCAL = '\n'.join(sorted(v[0] for v in M.PILOTS.values() if v[1] in (98000003, 98000004)))   # a big Local (groups)

# ---- expected, worked out here ----
def gclass(d):
    m = re.fullmatch(r'(\d[\d,]*(?:\.\d+)?)\s*(m|km|au|ly)', d.strip(), re.I)
    if not m: return 'none'
    if m.group(2).lower() in ('au', 'ly'): return 'off'
    v = float(m.group(1).replace(',', '')) / (1000 if m.group(2).lower() == 'm' else 1)
    return 'on' if v <= 10000 else 'off'
ROLE_G = {'Logistics': 'Logistics', 'Logistics Frigate': 'Logistics', 'Force Auxiliary': 'Logistics', 'Interceptor': 'Tackle', 'Interdictor': 'Tackle',
          'Heavy Interdiction Cruiser': 'Tackle', 'Combat Recon Ship': 'EWAR', 'Force Recon Ship': 'EWAR', 'Electronic Attack Ship': 'EWAR',
          'Command Ship': 'Command', 'Command Destroyer': 'Command', 'Stealth Bomber': 'Bombers'}
NONCOMBAT = {'Mining Barge', 'Exhumer', 'Expedition Frigate', 'Industrial Command Ship', 'Capital Industrial Ship', 'Expedition Command Ship', 'Freighter',
             'Jump Freighter', 'Hauler', 'Blockade Runner', 'Deep Space Transport', 'Shuttle', 'Capsule', 'Corvette', 'Special Edition Yachts', 'Prototype Exploration Ship'}
ORDER = ['Logistics', 'Tackle', 'EWAR', 'Command', 'Bombers', 'Capitals', 'DPS', 'Cyno Capable', 'Non-combat']
def adict(t): return {P.aname(a['attributeID']): a['value'] for a in P.td.get(str(t), {}).get('dogmaAttributes', [])}
CYNO = {}   # kind -> (groups, types), from the SDE
for t, v in P.types.items():
    if v.get('published') and P.gname(int(t)) == 'Cynosural Field Generator':
        k = 'covert' if 'Covert' in P.name(int(t)) else 'industrial' if 'Industrial' in P.name(int(t)) else 'regular'
        a = adict(t); gs, ts = CYNO.setdefault(k, (set(), set()))
        gs.update(int(x) for n, x in a.items() if re.fullmatch(r'canFitShipGroup\d+', n)); ts.update(int(x) for n, x in a.items() if re.fullmatch(r'canFitShipType\d+', n))
def role(t):
    g = P.gname(B[t]); gid = P.types[str(B[t])]['groupID']
    base = ROLE_G.get(g) or ('Capitals' if g in ('Carrier', 'Dreadnought', 'Supercarrier', 'Titan', 'Lancer Dreadnought') else 'Non-combat' if g in NONCOMBAT else 'DPS')
    cy = sorted(k for k, (gs, ts) in CYNO.items() if gid in gs or B[t] in ts)
    if cy and base in ('DPS', 'Non-combat') and g not in ('Black Ops', 'Strategic Cruiser'): return 'Cyno Capable', cy, False
    return base, cy, bool(cy)
EXP = {}
for t, ds in SHIPS:
    r, cy, tag = role(t)
    c = [gclass(d) for d in ds]
    EXP[t] = {'role': r, 'cyno': cy, 'tag': tag, 'n': len(ds), 'on': c.count('on'), 'off': c.count('off'), 'none': c.count('none')}
N = sum(e['n'] for e in EXP.values()); ON = sum(e['on'] for e in EXP.values()); OFF = sum(e['off'] for e in EXP.values()); NONE = sum(e['none'] for e in EXP.values())
ROLES = [(r, sum(e['n'] for e in EXP.values() if e['role'] == r)) for r in ORDER if any(e['role'] == r for e in EXP.values())]
def resist(t):   # the old card's numbers: damage through each resist, weighted by shield / armor / hull HP, of the base hull
    a = adict(B[t]); sh, ar, hu = a.get('shieldCapacity', 0), a.get('armorHP', 0), a.get('hp', 0); tot = sh + ar + hu or 1
    n = {'em': 'Em', 'therm': 'Thermal', 'kin': 'Kinetic', 'exp': 'Explosive'}
    return {d: (a.get(f'shield{n[d]}DamageResonance', 1) * sh + a.get(f'armor{n[d]}DamageResonance', 1) * ar + a.get(f'{n[d].lower()}DamageResonance', 1) * hu) / tot for d in n}
LBL = {'em': 'EM', 'therm': 'Therm', 'kin': 'Kin', 'exp': 'Exp'}

RAIL = """() => { const r = document.querySelector('#scanRail'); if(!r || r.hidden) return null;
  return {total: r.querySelector('.sr-total').textContent, sub: r.querySelector('.sr-sub').textContent, leg: [...r.querySelectorAll('.sr-leg > span')].map(s => s.textContent.replace(/\\s+/g, ' ').trim()),
    groups: [...r.querySelectorAll('.sr-grp')].map(g => ({h: g.querySelector('.sr-rh').textContent.replace(/\\s+/g, ' ').trim(), rows: [...g.querySelectorAll('button.sr-row')].map(b => ({nm: b.querySelector('.nm').textContent,
      tag: !!b.querySelector('.sr-cy'), wb: b.querySelector('.sr-wb').textContent, og: b.querySelector('.sr-og').textContent, n: b.querySelector('.sr-n').textContent}))})),
    foot: [...r.querySelectorAll('.sr-foot > div')].map(d => d.textContent.replace(/\\s+/g, ' ').trim()), cards: document.querySelectorAll('#saOut .sr-card, #resultsGrid').length}; }"""
CARD = """() => { const c = document.querySelector('#scanCard'); if(!c || c.hidden) return null; const b = c.getBoundingClientRect();
  return {nm: c.querySelector('.sr-ct .nm').textContent, cn: c.querySelector('.sr-cn').textContent, w: c.querySelector('.sr-cw .dmg-badge').className.split(' ')[1], cw: c.querySelector('.sr-cw').textContent,
    bars: [...c.querySelectorAll('.sr-br')].map(x => [x.firstChild.textContent, x.querySelector('b').textContent, x.classList.contains('w')]),
    ammo: [...c.querySelectorAll('.sr-ca > div:not(.sr-alt)')].map(x => [x.querySelector('span').textContent, x.querySelector('b').textContent, x.querySelector('b').title]),
    cyno: (c.querySelector('.sr-ccy') || {}).textContent || '', cf: c.querySelector('.sr-cf').textContent, pinned: c.classList.contains('pinned'), up: c.classList.contains('up'), inline: c.classList.contains('inline'),
    top: b.top, bottom: b.bottom, left: b.left, right: b.right, z: document.elementFromPoint(b.left + b.width / 2, b.top + 20) && document.elementFromPoint(b.left + b.width / 2, b.top + 20).closest('#scanCard') !== null}; }"""
def run(pg, local, scan):
    pg.click('#tabBtnDscan'); pg.fill('#localInput', local); pg.fill('#dscanInput', scan); pg.click('#analyzeBtn'); pg.wait_for_timeout(400)
    pg.wait_for_function("() => !document.querySelector('#analyzeBtn').disabled && (document.querySelector('#saBusy') || {hidden: true}).hidden", timeout=120000); pg.wait_for_timeout(600)
def row(t): return f'#scanRail button.sr-row[data-sr="{B[t]}"]'

with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []
    def page(w, h=1000):
        ctx = b.new_context(bypass_csp=True, viewport={'width': w, 'height': h}); M.route(ctx); pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e))); pg.goto('file://' + HTML); return ctx, pg
    ctx, pg = page(1440)
    run(pg, LOCAL, SCAN)
    R = pg.evaluate(RAIL)
    check(R and R['total'] == str(N) and R['sub'] == f"{len(SHIPS)} hulls · {ON} on grid · {OFF} off grid · {NONE} no reading",
          f"the head: {N} ships, {len(SHIPS)} hulls, {ON} on grid, {OFF} off grid, {NONE} no reading ({R and (R['total'], R['sub'])})")
    check(R and R['leg'] == [f'{r} {n}' for r, n in ROLES], f"the role bar's legend, in order {R and R['leg']} = {ROLES}")
    want_groups = []
    for r, n in ROLES:
        hs = sorted([t for t in EXP if EXP[t]['role'] == r], key=lambda t: (-EXP[t]['n'], t))
        want_groups.append({'h': f'{r} {n}', 'rows': [{'nm': t, 'tag': EXP[t]['tag'], 'wb': LBL[max(resist(t).items(), key=lambda kv: kv[1])[0]],
                                                         'og': f"{EXP[t]['on']} on grid" if EXP[t]['on'] else '', 'n': str(EXP[t]['n'])} for t in hs]})
    got = [{'h': g['h'].upper(), 'rows': g['rows']} for g in R['groups']] if R else []
    wantU = [{'h': g['h'].upper(), 'rows': g['rows']} for g in want_groups]
    check(got == wantU, 'every hull in its role (cyno role and tags from the SDE), by count then name, with its weakest type, on-grid count and count\n      page ' + str(got)[:600] + '\n      want ' + str(wantU)[:600])
    cy = {t for t in EXP if EXP[t]['role'] == 'Cyno Capable'}; tags = {t for t in EXP if EXP[t]['tag']}
    check(cy == {'Badger', 'Prowler', 'Venture', 'Cheetah'} and tags == {'Devoter', 'Falcon', 'Purifier', 'Loki'} and EXP['Hulk']['role'] == 'Non-combat' and EXP['Capsule']['role'] == 'Non-combat',
          f'the SDE says what was decided: Cyno Capable {sorted(cy)}, tagged {sorted(tags)}, the Hulk and capsules Non-combat')
    F = R['foot'] if R else []
    check(len(F) == 3 and F[0].startswith('Not ships:') and all(f'{t} ×{n}' in F[0] for t, n in OTHER) and F[1] == f'Celestials: {len(CELEST)}, skipped'
          and F[2].startswith(f'Unrecognized: {UNK} ×1'), f'the footer: not ships, celestials, the unrecognized name {F}')
    check(R and R['cards'] == 1, f'one card element, no hidden cards and no old grid ({R and R["cards"]})')
    L = pg.evaluate("""() => { const o = document.querySelector('#saOut'), r = document.querySelector('#scanRail').getBoundingClientRect(), s = document.querySelector('#saResults').getBoundingClientRect();
      return [o.classList.contains('rail'), o.classList.contains('wide'), Math.round(r.width), r.right <= s.left, getComputedStyle(document.querySelector('#scanRail')).position, !!document.querySelector('#saResults .sa-sum')]; }""")
    check(L[:2] == [True, False] and 300 <= L[2] <= 340 and L[3] and L[4] == 'sticky' and L[5], f"Local and D-Scan: the rail (~320 px, sticky) left of Local's results {L}")
    ships = pg.evaluate("() => [lastScanShips.map(s => s.name).sort(), [...sa.scanTypes].length]")
    check(ships[0] == sorted(t for t, _ in SHIPS) and ships[1] == len(SHIPS), f'the scan still feeds the Pilot rows: lastScanShips and sa.scanTypes {ships[1]}')
    # the hover card
    for t in ('Ferox', 'Scimitar', 'Devoter', 'Venture'):
        pg.hover(row(t)); pg.wait_for_timeout(350)
        C = pg.evaluate(CARD)
        rs = resist(t); w = max(rs.items(), key=lambda kv: kv[1])[0]; w2 = max(((d, v) for d, v in rs.items() if d != w), key=lambda kv: kv[1])[0]
        full = {'em': 'EM', 'therm': 'Thermal', 'kin': 'Kinetic', 'exp': 'Explosive'}
        bars = [[LBL[d], f'{round(min(1, rs[d]) * 100)}%', d == w] for d in ('em', 'therm', 'kin', 'exp')]
        ref = pg.evaluate(f"""() => {{ const w = '{w}', w2 = '{w2}', t = buildTurretRecs(w, w2), s = scanData.ships.find(x => x.name === '{t}'), I = scanHullInfo(s), dr = I.drones;
          return [RECS[w].missile, ...['laser', 'hybrid', 'projectile'].map(k => turretRecText(t[k], w, w2)), `${{dr.primary.name}} (${{dr.primary.size}})`]; }}""")
        e = EXP[t]
        cf = ' · '.join(x for x in [f"{e['on']} on grid" if e['on'] else '', f"{e['off']} off grid" if e['off'] else '', f"{e['none']} no reading" if e['none'] else ''] if x) + ' · base hull, no fit (D-Scan shows no fits)'
        ok = (C and C['nm'] == t and C['cn'] == f"×{e['n']}" and C['w'] == w and C['cw'].endswith(f'weakest, then {full[w2]}') and C['bars'] == bars
              and [a[2] for a in C['ammo'][:4]] == ref[:4] and C['ammo'][0][1] == ref[0].split(' (')[0] and C['ammo'][4][1] == ref[4]
              and all((a[1] == 'no good charge') == a[2].startswith('no answer') for a in C['ammo'][1:4]) and C['cf'] == cf
              and (('Can fit' in C['cyno']) == bool(e['cyno'])) and C['z'] and not C['pinned'])
        check(ok, f"hover {t}: weighted resists {bars}, weakest {w} then {w2}, charges (today's sentence on hover), drone, cyno line, grid line; above Local\n      {C}")
    pg.mouse.move(5, 5); pg.wait_for_timeout(400)
    check(pg.evaluate(CARD) is None, 'leaving the row closes it')
    pg.hover(row('Ferox')); pg.wait_for_timeout(350); box = pg.locator('#scanCard').bounding_box()
    pg.mouse.move(box['x'] + 30, box['y'] + 30, steps=40); pg.wait_for_timeout(400)   # small steps: the pointer crosses the gap between row and card
    check(pg.evaluate(CARD) is not None, 'the card itself can be hovered: moving into it keeps it open')
    pg.mouse.move(5, 5); pg.wait_for_timeout(400)
    pg.focus(row('Sabre')); pg.wait_for_timeout(100)
    c1 = pg.evaluate(CARD); pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    c2 = pg.evaluate("() => [!!document.querySelector('#scanCard:not([hidden])'), document.activeElement && document.activeElement.dataset.sr]")
    check(c1 and c1['nm'] == 'Sabre' and c2 == [False, str(B['Sabre'])], f'focus opens it, Esc closes it and keeps the focus on the row {c2}')
    pg.click(row('Vedmak')); pg.mouse.move(5, 5); pg.wait_for_timeout(400)
    c3 = pg.evaluate(CARD); pg.hover(row('Rifter')); pg.wait_for_timeout(350); c4 = pg.evaluate(CARD)
    pg.click(row('Rifter')); pg.wait_for_timeout(200); c5 = pg.evaluate(CARD)
    n_open = pg.evaluate("() => document.querySelectorAll('#scanRail button.sr-row[aria-expanded=true]').length")
    pg.mouse.click(1400, 980); pg.wait_for_timeout(200)
    check(c3 and c3['pinned'] and c3['nm'] == 'Vedmak' and c4 and c4['nm'] == 'Vedmak' and c5 and c5['nm'] == 'Rifter' and n_open == 1 and pg.evaluate(CARD) is None,
          'a press pins the card (hovering another row leaves it); pressing another moves it there; one at a time; a press elsewhere closes it')
    pg.click(row('Rifter')); pg.wait_for_timeout(200); pg.click(row('Rifter')); pg.wait_for_timeout(200)
    check(pg.evaluate(CARD) is None, 'a second press on the same row closes it')
    pg.click(row('Curse')); pg.wait_for_timeout(200); pg.set_viewport_size({'width': 1300, 'height': 900}); pg.wait_for_timeout(300)
    C = pg.evaluate(CARD); rr = pg.evaluate(f"() => document.querySelector('{row('Curse')}').getBoundingClientRect().right")
    check(C and C['nm'] == 'Curse' and C['pinned'] and abs(C['left'] - rr - 10) < 2, f'a resize (a phone\'s address bar, a window dragged) moves the open card with its row, it stays open ({C and round(C["left"])} vs {round(rr)})')
    pg.set_viewport_size({'width': 1440, 'height': 1000})
    ctx.close()
    # near the bottom of the window: it flips up
    ctx, pg = page(1440, 700); run(pg, LOCAL, SCAN)
    last = R['groups'][-1]['rows'][-1]['nm']
    pg.locator(row(last)).scroll_into_view_if_needed(); pg.evaluate(f"() => {{ const r = document.querySelector('{row(last)}').getBoundingClientRect(); window.scrollBy(0, r.bottom - innerHeight + 30); }}"); pg.wait_for_timeout(200)
    pg.hover(row(last)); pg.wait_for_timeout(350); C = pg.evaluate(CARD)
    check(C and C['up'] and C['bottom'] <= 700, f'near the bottom of the window the card flips up and stays in it ({C and (C["up"], round(C["bottom"]))})')
    ctx.close()
    # Local only; D-Scan only; typed names; a fit
    ctx, pg = page(1440)
    run(pg, LOCAL, '')
    lo = pg.evaluate("() => [document.querySelector('#scanRail').hidden, document.querySelector('#saOut').classList.contains('rail'), Math.round(document.querySelector('#saResults').getBoundingClientRect().width)]")
    check(lo[0] and not lo[1] and lo[2] > 1200, f'Local only: no rail, Local takes the full width {lo}')
    run(pg, '', SCAN)
    w = pg.evaluate("""() => { const r = document.querySelector('#scanRail').getBoundingClientRect(), xs = new Set([...document.querySelectorAll('#scanRail button.sr-row')].map(b => Math.round(b.getBoundingClientRect().left)));
      return [document.querySelector('#saOut').classList.contains('wide'), Math.round(r.width), xs.size, getComputedStyle(document.querySelector('#scanRail')).position]; }""")
    check(w[0] and w[1] > 1200 and 2 <= w[2] <= 3 and w[3] != 'sticky', f'D-Scan only: the rail takes the full width, its hulls in 2–3 columns {w}')
    pg.hover(row('Ibis')); pg.wait_for_timeout(350); C = pg.evaluate(CARD)
    check(C and C['right'] <= 1440 and C['left'] >= 0, f'... a card from a right-hand column stays in the window ({C and (round(C["left"]), round(C["right"]))})')
    run(pg, '', 'Purifier\nPurifier\nVedmak')
    R2 = pg.evaluate(RAIL); txt = pg.inner_text('#scanRail')
    pg.hover(row('Vedmak')); pg.wait_for_timeout(350); C = pg.evaluate(CARD)
    check(R2 and R2['sub'] == '2 hulls' and 'grid' not in txt and 'reading' not in txt and C and 'grid' not in C['cf'] and 'reading' not in C['cf'],
          f'typed names (no distances): no grid or reading text anywhere ({R2 and R2["sub"]!r}, card {C and C["cf"]!r})')
    run(pg, '', '[Rifter, test]\nDamage Control I\n\n1MN Afterburner I')
    f = pg.evaluate("() => [document.querySelector('#scanRail').hidden, document.querySelector('#scanStatus').textContent]")
    check(f[0] and '(DSCAN-01)' in f[1], f'a fit in the D-Scan box: DSCAN-01, no rail {f}')
    pg.click('#saClearBtn'); pg.wait_for_timeout(200)
    check(pg.evaluate("() => document.querySelector('#scanRail').hidden && !scanData"), 'Clear hides the rail')
    ctx.close()
    # phone
    ctx, pg = page(390); run(pg, LOCAL, SCAN)
    Ph = pg.evaluate("""() => { const r = document.querySelector('#scanRail').getBoundingClientRect(), s = document.querySelector('#saResults').getBoundingClientRect();
      return [document.documentElement.scrollWidth, r.bottom <= s.top + 1, Math.min(...[...document.querySelectorAll('#scanRail button.sr-row')].map(b => b.getBoundingClientRect().height)),
        [...document.querySelectorAll('#scanRail *')].filter(e => { const b = e.getBoundingClientRect(); return e.checkVisibility() && b.width && (b.right > innerWidth + 1 || b.left < -1); }).map(e => e.className).slice(0, 3)]; }""")
    pg.click(row('Ferox')); pg.wait_for_timeout(200)
    C = pg.evaluate(CARD); after = pg.evaluate(f"() => document.querySelector('{row('Ferox')}').nextElementSibling && document.querySelector('{row('Ferox')}').nextElementSibling.id")
    sw = pg.evaluate("() => document.documentElement.scrollWidth")
    check(Ph[0] <= 390 and Ph[1] and Ph[2] >= 44 and not Ph[3] and C and C['inline'] and after == 'scanCard' and sw <= 390,
          f'390 px: the rail first, then Local; rows 44 px; a tap opens the card in place under its row; nothing off the page {Ph} {after}')
    ctx.close()
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
