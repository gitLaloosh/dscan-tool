"""Against Your Ship (v2026.10.14.85; roadmap/local-and-fleet-plan.md L5, decision D10).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/vs_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The real page with ESI and zKillboard answered from sa_mocks.py (the fleet view's golden-fit groups: Crimson Tide's
Curse x19 and Vedmak x10, Void Runners' Loki x13, 4 Curses on the D-Scan) and a Vexor saved in My Ship. Every number
the card shows is worked out again here, in the page but from the outside:
  * each kill-first row against the Matchup's own mysMatchup (their DPS on you, "they last") at the card's fight;
  * their DPS on you = sum of count x each ship's, the counts as sa_mocks.expected_fleet() (on scan: min(scan, count));
  * your capacitor: pyfa's capSim (capSimPyfa) on your fit's drains plus their neuts / nosferatus in reach, written
    here from pyfa (Fit.addDrain via Effect6187 / 6197: amount x calculateRangeFactor(optimal, falloff, distance),
    cycle = duration, one drain per module copy per ship); "you last" = ttkSeconds with that capacitor time;
  * the T / C counts, logistics, the kill order (logistics first, then their DPS on you / the time you take to break
    one), the verdict;
  * the settings: the default range is the step nearest your guns' best range; range, MWD and On scan change the
    numbers as above; a hull marked as logistics goes first ("repairs the others");
  * no ship saved: the card asks for My Ship (its button opens the panel); "Use in assessments" off: it says so;
  * the Pilots view: the card above the rows, each row with a fit counted once ("fit unknown" not);
  * at 390 px nothing runs off the page; no page errors.
v2026.10.14.84 fails (no card).
"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from playwright.sync_api import sync_playwright
import sa_mocks as M

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok
SIDE = {'pilot': {'id': 90000001, 'name': 'Test Pilot'}, 'corp': {'id': M.CORP, 'name': 'Example Corp'}, 'alliance': {'id': M.ALLIANCE, 'name': 'Example Alliance'},
        'friendly': [{'id': M.BCM, 'name': 'Blue Coalition Member', 'kind': 'alliance'}, {'id': M.ALLIED, 'name': 'Allied Wing', 'kind': 'alliance'}],
        'hostile': [{'id': M.CRTS, 'name': 'Crimson Tide Syndicate', 'kind': 'alliance'}, {'id': M.TURNCOAT, 'name': 'Turncoat Corp', 'kind': 'corporation'}], 'rows': 15}
SCAN = M.SCAN + '\n' + '\n'.join(f"{M.byname['Curse']}\tSomeone's Curse {i}\tCurse\t2.1 AU" for i in range(4))
VEXOR = open(os.path.join(HERE, 'damage_chart_check.py')).read().split('VEXOR = """')[1].split('"""')[0]
EF = M.expected_fleet()

# In the page, from the outside: every unit's numbers through the Matchup's mysMatchup, the totals, the capacitor with
# their drains written from pyfa, the time you last, the kill order and the verdict.
RECOMPUTE = r"""(o) => {
  const mf = myShip.f, st = {range: o.km * 1000, mode: o.prop ? 'orbit' : 'still', speedPct: 100, prop: o.prop, sigPct: 100, theirPct: 100, theirMode: 'still', axis: 'distance'};
  const units = [];
  if(o.kind === 'fleet'){
    for(const [gk, r] of sa.fleet) for(const h of (r.hulls || [])){
      const v = h.variants && h.variants[h.pick]; if(!v) continue;
      const g = [...sa.lastGroups.h, ...sa.lastGroups.n].find(x => x.key === gk);
      const n = Math.round(h.share * g.n); if(!n) continue;
      units.push({key: `${gk}|${h.typeId}`, name: h.name, logi: h.logi, f: {estimate: v.est, input: {shipTypeId: h.typeId, tally: v.built.tally, cargoItemIds: v.built.cargoItemIds, highSlotByFlag: v.built.highSlotByFlag, midSlotByFlag: v.built.midSlotByFlag}},
        n: o.scan ? Math.min(lastScanCounts.get(h.typeId) || 0, n) : n});
    }
  }else{
    for(const [id, r] of sa.rows){
      if(r.state !== 'done' || r.fitUnknown) continue;
      units.push({key: `p${id}`, name: r.hull, logi: false, f: {estimate: r.est, input: {shipTypeId: r.typeId, tally: r.built.tally, cargoItemIds: r.built.cargoItemIds, highSlotByFlag: r.built.highSlotByFlag, midSlotByFlag: r.built.midSlotByFlag}},
        n: o.scan ? (sa.scanTypes.has(r.typeId) ? 1 : 0) : 1});
    }
  }
  // pyfa eos/calc.py calculateRangeFactor (restrictedRange)
  const rf = (opt, fall, d) => fall > 0 ? (d > opt + 3 * fall ? 0 : Math.pow(0.5, Math.pow(Math.max(0, d - opt) / fall, 2))) : (d <= opt ? 1 : 0);
  const typed = {em: 0, therm: 0, kin: 0, exp: 0}, drains = [], rows = [];
  let ships = 0, dps = 0, T = 0, Cn = 0, logi = 0, partial = 0;
  for(const u of units){
    const m = mysMatchup(u.f, mf, st), F = mysFight(u.f, mf, st);
    const inc = dmgTypedPoint(F.tApp, F.me, F.qIn);
    const pr = F.tApp.projected || {};
    const webs = [...(pr.webMods || []), ...(pr.webDrones || []), ...(pr.webFighters || [])].map(w => w.optimal);
    const holds = (pr.scramRange > 0 && st.range <= pr.scramRange) || webs.some(w => w > 0 && st.range <= w);
    const dr = (u.f.estimate.ewarModules || []).filter(e => (e.kind === 'neut' || e.kind === 'nos') && e.running !== false)
      .map(e => ({ms: Math.round(1000 * e.capPerCycle / e.capPerSec), gj: e.capPerCycle * rf(e.rangeM, e.falloffM, st.range), q: e.qty || 1, f: rf(e.rangeM, e.falloffM, st.range)})).filter(d => d.gj > 0);
    if(dr.some(d => d.f < 1)) partial++;
    rows.push({key: u.key, name: u.name, n: u.n, logi: u.logi, theirDps: m.theirDps, theyLast: m.theyLast, dpsText: dmgFmt(m.theirDps), lastText: ttkText(m.theyLast), score: m.theyLast === Infinity ? 0 : m.theirDps / Math.max(m.theyLast, 0.1)});
    if(!u.n) continue;
    ships += u.n; dps += u.n * m.theirDps;
    for(const d of ['em', 'therm', 'kin', 'exp']) typed[d] += u.n * inc.typed[d];
    if(holds) T += u.n;
    if(dr.length) Cn += u.n;
    if(u.logi) logi += u.n;
    for(const d of dr) for(let i = 0; i < u.n * d.q; i++) drains.push([d.ms, d.gj, 0, false, 0, false]);
  }
  const si = mf.estimate.capacitor.simInputs, def = ttkDefense(mf.estimate), own = def.capSec;
  let capSec = own;
  if(drains.length){ const sim = capSimPyfa(si.capacity, si.rechargeMs, [...si.best, ...drains]); capSec = sim.stable ? Infinity : sim.timeToEmptyExactSec; }
  def.capSec = capSec;
  const youLast = ships ? ttkSeconds(def, typed) : Infinity;
  const order = rows.filter(r => r.n > 0).sort((a, b) => (b.logi - a.logi) || (b.score - a.score) || (b.theirDps - a.theirDps));
  let t = 0, k = 0; out: for(const r of order) for(let i = 0; i < r.n; i++){ if(r.theyLast === Infinity || t + r.theyLast > youLast) break out; t += r.theyLast; k++; }
  const verdict = youLast === Infinity ? 'You hold against all of it here.' : youLast < order[0].theyLast ? "Don't take this fight."
    : k >= ships ? 'You could break all of them first.' : `You'd break about ${k} before you go.`;
  return {ships, dps, dpsText: dmgFmt(dps), youLast, lastText: ttkText(youLast), capSec, ownCap: own, capText: capSec === Infinity ? 'Stable' : ttkText(capSec), T, C: Cn, logi, drains: drains.length, partial,
          order: order.map(r => [r.key, r.n, r.dpsText, r.lastText]), verdict, units: rows.length};
}"""
CARD = r"""() => { const c = document.querySelector('#saVs'); if(!c) return null;
  const t = (s) => (c.querySelector(s) || {}).textContent || '';
  return {title: t('.vs-head h3'), ship: t('.vs-ship'), last: t('[data-vs=last]'), dps: t('[data-vs=dps]').replace(/[≈,]/g, ''), cap: t('[data-vs=cap]'), logi: t('[data-vs=logi]').replace('≈', ''),
    hold: [...c.querySelectorAll('[data-vs=hold] > span')].map(s => s.textContent.replace(/[TC≈]/g, '')), verdict: t('.vs-vt b'),
    youLastAttr: c.dataset.youLast, dpsAttr: c.dataset.dps, pressed: [...c.querySelectorAll('[data-vs-set][aria-pressed=true]')].map(b => b.dataset.vsSet),
    ctx: [...c.querySelectorAll('.vs-stat .ctx')].map(e => e.textContent),
    rows: [...c.querySelectorAll('.vs-kr[data-vs-unit]')].map(r => [r.dataset.vsUnit, Number(r.querySelector('.vs-c3').textContent || 1), r.querySelector('.vs-c4').textContent, r.querySelector('[data-vs-they]').textContent]),
    why: [...c.querySelectorAll('.vs-kr[data-vs-unit] .vs-why')].map(e => e.textContent), msg: t('.vs-msg')}; }"""
def card(pg): return pg.evaluate(CARD)
def same_card(pg, label, o):
    c, r = card(pg), pg.evaluate(RECOMPUTE, o)
    check(c['dps'] == r['dpsText'].replace(',', '') and c['last'] == r['lastText'] and c['cap'] == r['capText'],
          f"{label}: DPS {c['dps']} = {r['dpsText']}, you last {c['last']} = {r['lastText']}, capacitor {c['cap']} = {r['capText']} ({r['drains']} neut drains)")
    want_rows = r['order'][:6]
    got_rows = [[k, n if o['kind'] == 'fleet' else 1, d, t] for k, n, d, t in c['rows']]
    check(got_rows == [[k, n if o['kind'] == 'fleet' else 1, d, t] for k, n, d, t in want_rows], f"{label}: kill first, each row as the Matchup has it:\n      page {got_rows}\n      want {want_rows}")
    check(c['hold'] == [str(r['T']), str(r['C'])] and c['logi'] == str(r['logi']) and c['verdict'] == r['verdict'],
          f"{label}: holding you T {c['hold']} = {r['T']} / C {r['C']}, logistics {c['logi']}, verdict {c['verdict']!r} = {r['verdict']!r}")
    return c, r
def setv(pg, v):
    pg.click(f'#saVs [data-vs-set="{v}"]'); pg.wait_for_timeout(250)
def save_ship(pg):
    pg.click('#myShipChip'); pg.fill('#myShipEft', VEXOR); pg.click('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-tiles'); pg.keyboard.press('Escape')
def setup(ctx, ship=True):
    pg = ctx.new_page(); pg.goto('file://' + HTML)
    pg.evaluate("(s) => localStorage.setItem('dscanSide', JSON.stringify(s))", SIDE); pg.reload(); pg.wait_for_timeout(300)
    if ship: save_ship(pg)
    return pg
def analyze(pg, local, scan):
    pg.click('#tabBtnDscan'); pg.fill('#localInput', local); pg.fill('#dscanInput', scan); pg.click('#analyzeBtn'); pg.wait_for_timeout(300)
    pg.wait_for_function("() => document.querySelector('#saBusy').hidden && !document.querySelector('#analyzeBtn').disabled", timeout=60000)

with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []
    def new_ctx(w=1440, h=1000):
        ctx = b.new_context(viewport={'width': w, 'height': h}); ctx.on('page', lambda pg: pg.on('pageerror', lambda e: errs.append(str(e)))); M.route(ctx); return ctx
    ctx = new_ctx()
    pg = setup(ctx)
    analyze(pg, M.LOCAL, SCAN)
    pg.wait_for_function("() => { const c = document.querySelector('#saFleet .fl-sum .pr-head .ctx'); return c && c.textContent === '5 of 5 groups looked up'; }", timeout=150000)
    pg.wait_for_function("() => document.querySelector('#saVs [data-vs=last]')", timeout=60000); pg.wait_for_timeout(500)
    c = card(pg)
    place = pg.evaluate("() => { const v = document.querySelector('#saFleet #saVs'); return !!v && v.previousElementSibling.classList.contains('fl-sum'); }")
    check(place and c['title'] == 'Against Your Ship' and c['ship'] == 'VexorBrawl', f"the card under “Their fleet, estimated”, your ship named ({c['title']!r}, {c['ship']!r})")
    best = pg.evaluate("() => { const b = dmgDefaultRangeM(myShip.f.estimate.application) / 1000; return [b, [5, 10, 20, 30, 50].reduce((a, k) => Math.abs(k - b) < Math.abs(a - b) ? k : a)]; }")
    check(c['pressed'] == [f'range:{best[1]}', 'prop:0', 'count:all'], f"starts at the step nearest your guns' best range ({best[0]:.1f} km -> {best[1]} km), Still, All {c['pressed']}")
    want_n = {f"a{g}|{M.byname[h]}": n for g, rows in EF['rows'].items() for h, _, n in rows if h in EF['dps'] and not (str(g) == str(M.CRTS) and h == 'Loki')}
    got_n = {k: n for k, n, *_ in c['rows']}
    check(got_n == {k: v for k, v in want_n.items()}, f"the ≈ counts as the fleet view's ({got_n}; want {want_n}; Crimson Tide's Lokis have no loss: no fit, not counted)")
    o = {'kind': 'fleet', 'km': best[1], 'prop': False, 'scan': False}
    c1, r1 = same_card(pg, f"fleet, {best[1]} km, still, all", o)
    check(float(c1['dpsAttr']) > 0 and abs(float(c1['dpsAttr']) - r1['dps']) < 1e-6 * r1['dps'] and r1['ships'] == EF['ships'],
          f"their DPS on you = sum of count x each ship's ({float(c1['dpsAttr']):.3f} vs {r1['dps']:.3f}), {r1['ships']} ships")
    check(r1['drains'] > 0 and r1['capSec'] < r1['ownCap'], f"their neuts in reach drain you: {r1['drains']} drains, capacitor {r1['capSec']:.1f} s (your fit alone: {r1['ownCap']})")
    # on scan
    setv(pg, 'count:scan')
    o_s = dict(o, scan=True)
    c2, r2 = same_card(pg, 'on scan', o_s)
    onscan_n = {k: n for k, n, *_ in c2['rows']}
    check(r2['ships'] == 4 and onscan_n == {f"a{M.CRTS}|{M.byname['Curse']}": 4} and r2['youLast'] >= r1['youLast'] and c2['ctx'][0] == f"all of them: {r1['lastText']}",
          f"On scan: only the 4 Curses on your D-Scan ({onscan_n}); you last {r2['lastText']} (all of them {r1['lastText']}, said beside: {c2['ctx'][0]!r})")
    setv(pg, 'count:all')
    # ranges: 30 km puts the Curse's neuts in falloff; 50 km past most reach
    for km in (30, 50):
        setv(pg, f'range:{km}')
        c3, r3 = same_card(pg, f'{km} km', dict(o, km=km))
        if km == 30: check(r3['partial'] > 0 and c3['ctx'][1].endswith('at 30 km'), f"30 km: a neut in its falloff drains less (pyfa's range factor; {r3['partial']} ships) and the context says {c3['ctx'][1]!r}")
        if km == 50: check(c3['cap'] == ('Stable' if r3['ownCap'] == float('inf') else c3['cap']) and (r3['drains'] > 0 or c3['ctx'][3] == 'no neuts in reach'), f"50 km: {r3['drains']} drains, capacitor {c3['cap']} ({c3['ctx'][3]!r})")
    setv(pg, 'prop:1')
    same_card(pg, '50 km, MWD on', dict(o, km=50, prop=True))
    setv(pg, f'range:{best[1]}'); setv(pg, 'prop:0')
    # a logistics hull goes first
    pg.evaluate(f"() => {{ for(const r of sa.fleet.values()) for(const h of (r.hulls || [])) if(h.name === 'Curse') h.logi = true; saRefreshVs(); }}"); pg.wait_for_timeout(300)
    c4, r4 = same_card(pg, 'a hull marked logistics', o)
    check(c4['rows'][0][0] == f"a{M.CRTS}|{M.byname['Curse']}" and c4['why'][0] == 'repairs the others' and c4['logi'] == '19', f"logistics first: {c4['rows'][0][0]} ({c4['why'][0]!r}), Their logistics {c4['logi']}")
    pg.evaluate(f"() => {{ for(const r of sa.fleet.values()) for(const h of (r.hulls || [])) if(h.name === 'Curse') h.logi = false; saRefreshVs(); }}"); pg.wait_for_timeout(300)
    # a variant pick follows
    pg.locator('#saFleet summary.fl-varbtn').first.click(); pg.wait_for_timeout(200)
    pg.locator('#saFleet details.fl-pick[open] button.fl-opt').nth(1).click(); pg.wait_for_timeout(400)
    same_card(pg, 'Curse variant 2 picked', o)
    # Use in assessments off, then on
    pg.click('#myShipChip'); pg.uncheck('#myShipUse'); pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    off = card(pg)['msg']
    pg.click('#myShipChip'); pg.check('#myShipUse'); pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    pg.wait_for_function("() => document.querySelector('#saVs [data-vs=last]')", timeout=30000)
    check(off.startswith('Turn on “Use in assessments”') and card(pg)['last'], f"“Use in assessments” off: {off[:60]!r}; on again: the numbers")
    # phone
    pg.set_viewport_size({'width': 390, 'height': 844}); pg.wait_for_timeout(300)
    over = pg.evaluate("() => [document.documentElement.scrollWidth, [...document.querySelectorAll('#saVs *')].filter(e => { const r = e.getBoundingClientRect(); return e.checkVisibility() && r.width && (r.right > innerWidth + 1 || r.left < -1); }).map(e => e.className || e.tagName).slice(0, 5)]")
    check(over[0] <= 390 and not over[1], f'390 px: nothing runs off the page {over}')
    ctx.close()

    # no ship saved
    ctx = new_ctx()
    pg = setup(ctx, ship=False)
    analyze(pg, M.LOCAL, SCAN)
    pg.wait_for_function("() => document.querySelector('#saVs .vs-msg')", timeout=60000)
    msg = card(pg)['msg']
    pg.click('#saVs [data-vs-myship]'); pg.wait_for_timeout(300)
    check(msg.startswith('Save your ship in My Ship') and pg.is_visible('#myShipPanel'), f"no ship saved: {msg[:48]!r}, its button opens My Ship")
    ctx.close()

    # the Pilots view
    ctx = new_ctx()
    pg = setup(ctx)
    analyze(pg, '\n'.join(M.SMALL_LOCAL), M.SCAN_ROWS)
    pg.wait_for_function("() => { const c = document.querySelector('#saPilots .pr-head .ctx'); return c && c.textContent === '7 of 7 looked up'; }", timeout=120000)
    pg.wait_for_function("() => document.querySelector('#saVsHost #saVs [data-vs=last]')", timeout=60000); pg.wait_for_timeout(500)
    above = pg.evaluate("() => document.querySelector('#saVsHost').nextElementSibling.id")
    po = {'kind': 'pilots', 'km': best[1], 'prop': False, 'scan': False}
    cp, rp = same_card(pg, 'Pilots view', po)
    fits = sum(1 for _, h, d in M.expected_rows() if d is not None)
    allb = pg.evaluate("() => document.querySelector('#saVs [data-vs-set=\"count:all\"]').textContent")
    check(above == 'saPilots' and rp['ships'] == fits and allb == f'All {fits}', f"Pilots view: the card above the rows, each row with a fit once ({allb!r}, {fits} rows with a fit)")
    setv(pg, 'count:scan')
    same_card(pg, 'Pilots view, on scan', dict(po, scan=True))
    ctx.close()
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
