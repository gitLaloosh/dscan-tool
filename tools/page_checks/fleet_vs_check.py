"""The Fleet tab without a time to kill: what the fleet reaches instead; the victim; the standing icons (v2026.10.31.1).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/fleet_vs_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The name is from v2026.10.30.4's Against This Fleet card (the fleet against the victim or your ship), which the owner tested and
took out: "given the fluidity of ranges in fleet battles" and fits that are only a guess, "we probably should not be giving a time
to kill numbers" for a whole fleet (LESSON #108). Its one new fact, range, went into the cards that were already there. The real
page with ESI and zKillboard answered from sa_mocks.py (Orla Fleetwood's 6-ship kill of a Thanatos), a made-up Vexor as My Ship:
  * opened as from Intel: the head, the victim (v2026.10.31.2), the summary and the pilots, nothing else; no time to kill, no victim or my-ship switch, no
    range or MWD buttons, even with a ship saved;
  * the victim: a tag in the line under the title, neutral =, that opens them in the Pilot Analyzer;
  * Weapon reach: the nearest and farthest main weapon over the pilots with a fit, worked out here from each fit's own numbers
    (the weapon doing the most DPS; turrets optimal + falloff, missiles flight); the drone-only ships counted;
  * Tackle and EWAR: each kind's farthest optimal, worked out here from the modules;
  * each pilot row: its main weapon's range as the Pilot Analyzer writes it (weaponRangeText), "drones" for a drone boat; a fit
    with two weapons reaches as far as the one doing the more DPS;
    the EWAR badges' hover lists each module with its range;
  * the standing icons: friendly +, hostile −, neutral =, your own corporation a star; beside its own word an icon has no title;
  * v2026.10.31.2: the victim above the fleet, its numbers from the killmail's own fit; on a fit with weapons and tackle, its reach
    and each EWAR kind's farthest optimal as worked out here;
  * v2026.10.31.2: zKillboard not answering: one Retry in the pilots' head, disabled with a countdown while the page's pause is on;
    the summary says none could be looked up; each row says it short (all of it on hover); the pause kept for a reload; when it
    ends, Retry can be pressed and looks the pilots up again;
  * 390 px: nothing off the page, the range said once per row; no page errors.
"""
import sys, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from playwright.sync_api import sync_playwright
import sa_mocks as M

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok
VEXOR = open(os.path.join(HERE, 'damage_chart_check.py')).read().split('VEXOR = """')[1].split('"""')[0]
ORLA = M.PILOTS[M.ORLA][0]
SIDE = {'pilot': {'id': 90000001, 'name': 'Test Pilot'}, 'corp': {'id': M.CORP, 'name': 'Example Corp'}, 'alliance': {'id': M.ALLIANCE, 'name': 'Example Alliance'},
        'friendly': [{'id': M.THIRD, 'name': 'Random Third Party', 'kind': 'alliance'}], 'hostile': [{'id': M.CRTS, 'name': 'Crimson Tide Syndicate', 'kind': 'alliance'}], 'rows': 15}
def idle(pg):
    pg.wait_for_function("() => !document.querySelector('#fitBtn').disabled && document.querySelector('#pilotBusy').hidden", timeout=120000); pg.wait_for_timeout(400)
def fleet_done(pg, timeout=120000):
    # v2026.11.02.1: nothing is looked up on open; once the fits kept from the last hour are in, Load all (when anything is left)
    pg.wait_for_function("() => fk.ready && !fk.checking", timeout=timeout)
    if pg.query_selector('#fleetPanel [data-fk-loadall]:not([disabled])'): pg.click('#fleetPanel [data-fk-loadall]')
    # v2026.11.04.5: a failed lookup leaves the pilot unloaded (not "looked up"), so wait for nothing still being looked up
    pg.wait_for_function("() => { const c = document.querySelector('#fleetPanel .fk-sum .pr-head .ctx'); return c && /looked up/.test(c.textContent) && !fk.members.some(m => ['check', 'wait', 'load'].includes(m.state)); }", timeout=120000)
    pg.wait_for_timeout(600)
# Worked out here, not with the page's fkReach / fkSummary: each fit's main weapon is its range entry whose ammo does the most DPS
# (confirmedAmmoBreakdown); a turret reaches optimal + falloff, a missile its flight; no range entry but drone or fighter DPS: drones.
WANT = """() => { const km = (m) => pyRound(m / 1000, 1).toFixed(1);
  const out = {reach: [], drones: 0, rows: {}, kinds: {}, ew: {}, kindsOf: {}, reachOf: {}};
  for(const m of fk.members){
    if(m.state !== 'done' || m.fitUnknown) continue;
    const e = m.est, name = fk.info.get(m.id);
    let best = null;
    for(const r of e.rangeEstimates || []){ const a = (e.confirmedAmmoBreakdown || []).find(a => a.name === r.ammoName); if(a && (!best || a.dps > best.d)) best = {r, d: a.dps}; }
    if(best){ const r = best.r, x = r.exactM || {};
      out.reach.push(r.kind === 'missile' ? (x.travel ?? r.travelDistanceM) : (x.optimal ?? r.optimalM) + (r.falloffM > 0 ? (x.falloff ?? r.falloffM) : 0));
      out.rows[name] = weaponRangeText(r).short; }
    else if((e.droneDps || 0) + (e.fighterDps || 0) > 0){ out.drones++; out.rows[name] = 'drones'; }
    out.ew[name] = (e.ewarModules || []).map(x => `${x.name}${x.qty > 1 ? ` ×${x.qty}` : ''}: ${x.falloffM > 0 ? `${km(x.rangeM)} + ${km(x.falloffM)} km` : `${km(x.rangeM)} km`}`).join('\\n');
    const mine = {};
    for(const x of e.ewarModules || []){ const k = x.kind === 'scram' ? (/scrambl/i.test(x.name) ? 'scram' : 'point') : x.kind; out.kinds[k] = Math.max(out.kinds[k] || 0, x.rangeM || 0); mine[k] = Math.max(mine[k] || 0, x.rangeM || 0); }
    out.kindsOf[name] = Object.fromEntries(Object.entries(mine).map(([k, v]) => [k, `to ${km(v)} km`]));
    if(best) out.reachOf[name] = `${km(out.reach[out.reach.length - 1])} km`;
  }
  const lo = Math.min(...out.reach), hi = Math.max(...out.reach);
  out.reachText = km(lo) === km(hi) ? `${km(hi)} km` : `${km(lo)}–${km(hi)} km`;
  out.kindText = Object.fromEntries(Object.entries(out.kinds).map(([k, v]) => [k, `to ${km(v)} km`]));
  return out; }"""
SEEN = """() => { const p = document.querySelector('#fleetPanel'), sum = p.querySelector('.fk-sum');
  const stat = (k) => { const s = [...sum.querySelectorAll('.fl-stat')].find(s => s.querySelector('.k').textContent === k); return s ? {v: (s.querySelector('.v') || s.querySelector('.fk-ewl')).textContent, ctx: (s.querySelector('.ctx') || {}).textContent || ''} : null; };
  const L = Object.fromEntries(FK_EWAR_KINDS.map(([k, l]) => [l, k]));
  return {cards: [...p.children].map(c => c.className), text: p.innerText, vs: !!p.querySelector('#fkVs, [data-fk-side], [data-vs-set], [data-vs-myship]'),
    reach: stat('Weapon reach'), kinds: Object.fromEntries([...sum.querySelectorAll('.fk-ewl > span')].map(s => [L[s.firstChild.textContent], (s.querySelector('.fk-rng') || {}).textContent || ''])),
    rows: Object.fromEntries([...p.querySelectorAll('.fk-card button.pr-row')].map(b => [b.querySelector('.pr-pilot .nm').firstChild.textContent, (b.querySelector('.pr-dps .pr-rng') || {}).textContent || ''])),
    ew: Object.fromEntries([...p.querySelectorAll('.fk-card button.pr-row')].map(b => [b.querySelector('.pr-pilot .nm').firstChild.textContent, (b.querySelector('.pr-ew') || {}).title || ''])),
    victim: (() => { const v = p.querySelector('.fk-sub .fk-vbtn'); return v ? [v.querySelector('.nm').textContent, v.querySelector('svg.it-st').classList[1], v.dataset.fkType] : null; })()}; }"""

with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []
    def new_ctx(w):
        ctx = b.new_context(viewport={'width': w, 'height': 1000}); ctx.on('page', lambda pg: pg.on('pageerror', lambda e: errs.append(str(e)))); M.route(ctx); return ctx
    def open_fleet(pg, ship=True):
        pg.goto('file://' + HTML); pg.evaluate("(s) => localStorage.setItem('dscanSide', JSON.stringify(s))", SIDE); pg.reload(); pg.wait_for_timeout(400)
        if ship:
            pg.click('#profileBtn', position={'x': 12, 'y': 14}); pg.fill('#myShipEft', VEXOR); pg.click('#myShipPanel [data-act="save"]'); pg.wait_for_selector('#myShipPanel .mys-tiles'); pg.keyboard.press('Escape')
        pg.click('#tabBtnPilot'); pg.fill('#pilotName', ORLA); pg.fill('#manualShip', ''); pg.click('#fitBtn'); pg.wait_for_timeout(300); idle(pg)
        pg.click(f'#pilotDossier [data-pd-exp="{M.byname["Curse"]}"]'); pg.wait_for_timeout(500)
        pg.click(f'[data-pd-fleet="{M.FLEET_KILL}"]'); pg.wait_for_timeout(300); fleet_done(pg)
        pg.evaluate("() => fkOpen(fk.killId, fk.hash, null, null, {from: 'intel', km: fk.km})"); pg.wait_for_timeout(300); fleet_done(pg)
    ctx = new_ctx(1440); pg = ctx.new_page(); open_fleet(pg)
    S = pg.evaluate(SEEN); W = pg.evaluate(WANT)
    low = S['text'].lower()
    check(S['cards'] == ['card fk-head', 'card fl-sum fk-vic', 'card fl-sum fk-sum', 'card pr-card fk-card'] and not S['vs'] and 'against this fleet' not in low
          and not any(w in low for w in ('you last', 'they last', 'kill first', 'mwd on')),
          f'with a ship saved: the head, the victim, the summary and the pilots, no time to kill and nothing to set {S["cards"]}')
    v = S['victim']
    vt = pg.evaluate("() => [String(fk.victim.type), fk.info.get(fk.victim.id)]")
    check(v and v[0] == vt[1] and v[1] == 'neu' and v[2] == vt[0], f'the victim: a tag under the title, neutral = {v}')
    check(S['reach'] and S['reach']['v'] == W['reachText'] and S['reach']['ctx'] == f"{W['drones']} on drones or fighters only" and W['drones'] == 2,
          f"Weapon reach: {S['reach']} = {W['reachText']}, {W['drones']} drone boats")
    check(S['kinds'] == W['kindText'] and 'point' in S['kinds'] and 'neut' in S['kinds'], f'Tackle and EWAR: each kind\'s farthest optimal {S["kinds"]} = {W["kindText"]}')
    want_rows = {n: W['rows'].get(n, '') for n in S['rows']}
    check(S['rows'] == want_rows and 'drones' in S['rows'].values() and any(x.startswith('~') for x in S['rows'].values()) and any('+' in x for x in S['rows'].values()),
          f'each pilot: the main weapon\'s range as the Pilot Analyzer writes it {S["rows"]}')
    want_ew = {n: W['ew'].get(n, '') for n in S['ew']}
    check(S['ew'] == want_ew and any('+' in t for t in S['ew'].values()), f'the EWAR badges\' hover: each module and its range {list(S["ew"].values())[:1]}')
    # a fit with two weapons: its reach is the one doing the more DPS, wherever it sits in the list (the mocks' fits carry one each)
    two = pg.evaluate("""() => { const e = (a, b) => ({confirmedAmmoBreakdown: [{name: 'Ammo A', dps: a}, {name: 'Ammo B', dps: b}], droneDps: 0, fighterDps: 0,
        rangeEstimates: [{kind: 'turret', weaponName: 'Gun A', ammoName: 'Ammo A', optimalM: 5000, falloffM: 2000}, {kind: 'missile', weaponName: 'Launcher B', ammoName: 'Ammo B', travelDistanceM: 40000}]});
      const r1 = fkReach(e(100, 300)), r2 = fkReach(e(300, 100)); return [r1.short, Math.round(r1.m), r2.short, Math.round(r2.m)]; }""")
    check(two == ['~40.0 km', 40000, '5.0 + 2.0 km', 7000], f'two weapons: the reach of the one doing the more DPS {two}')
    # v2026.10.31.2: the victim, from the killmail's own fit, above the fleet
    V = pg.evaluate("""async () => { const b = buildLossTally(fk.km), e = await estimateHpAndDps(fk.km.victim.ship_type_id, b.tally, b.cargoItemIds, b.highSlotByFlag, 'sharpshooter', b.midSlotByFlag);
      const c = document.querySelector('#fleetPanel .fk-vic'), st = (k) => { const s = [...c.querySelectorAll('.fl-stat')].find(s => s.querySelector('.k').textContent === k); return s ? (s.querySelector('.v') || s.querySelector('.fk-ewl')).textContent : null; };
      return {order: [...document.querySelectorAll('#fleetPanel > .card')].map(x => x.classList.contains('fk-vic') ? 'victim' : x.classList.contains('fk-head') ? 'head' : x.classList.contains('fk-card') ? 'pilots' : 'fleet'),
        dps: st('Raw DPS'), want: Math.round(saRowDps(e).v).toLocaleString(), ehp: st('EHP'), wantEhp: saFmtK(e.totalHP), weak: st('Weakest to'), wantWeak: DMG_FULL[e.weakest], title: c.querySelector('h3').textContent}; }""")
    check(V['order'] == ['head', 'victim', 'fleet', 'pilots'] and V['title'] == 'The victim' and V['dps'] == V['want'] and V['ehp'] == V['wantEhp'] and V['weak'] == V['wantWeak'],
          f"the victim above the fleet, from the killmail's own fit {V}")
    # the victim card on a fit with weapons and tackle (a pilot's from this kill): the reach and EWAR as worked out above
    L = pg.evaluate("""() => { const m = fk.members.find(m => m.state === 'done' && !m.fitUnknown && (m.est.ewarModules || []).some(x => x.kind === 'web')); const keep = fk.victimF; fk.victimF = {est: m.est};
      const d = document.createElement('div'); d.innerHTML = fkVictimHtml(); fk.victimF = keep; const L = Object.fromEntries(FK_EWAR_KINDS.map(([k, l]) => [l, k]));
      const st = (k) => [...d.querySelectorAll('.fl-stat')].find(s => s.querySelector('.k').textContent === k);
      return [fk.info.get(m.id), st('Weapon reach').querySelector('.v').textContent, Object.fromEntries([...st('Tackle and EWAR').querySelectorAll('.fk-ewl > span')].map(s => [L[s.firstChild.textContent], s.querySelector('.fk-rng').textContent]))]; }""")
    one = {k: v for k, v in W['kindsOf'][L[0]].items()}
    check(L[1] == W['reachOf'][L[0]] and L[2] == one, f'... a fit with weapons: its reach and each EWAR kind\'s farthest optimal {L} = {W["reachOf"][L[0]]} {one}')
    ic = pg.evaluate("""() => [...document.querySelectorAll('#fleetPanel .fk-card button.pr-row')].map(b => b.querySelector('.pr-pilot svg.it-st').classList[1])""")
    check('bad' in ic and 'good' in ic and all(k in ('bad', 'good', 'neu', 'corp', 'all') for k in ic), f'the standing icons on the rows: hostile −, friendly + {ic}')
    pg.click('#fleetPanel .fk-sub .fk-vbtn'); pg.wait_for_timeout(1500)
    vp = pg.evaluate("() => [document.querySelector('.tab-btn.active').textContent, document.querySelector('#pilotName').value]")
    check(vp == ['Pilot Analyzer', v[0]], f"the victim's tag opens them in the Pilot Analyzer {vp}")
    st = pg.evaluate("() => [standKind('f', side.rec.corp.id, null), standKind('f', 1, side.rec.alliance.id), standKind('f', 1, 2), standKind('h', 1, 2), standKind('n', 1, 2), (standIcon('corp').match(/class=\"([^\"]+)\"/) || [])[1]]")
    check(st == ['corp', 'all', 'good', 'bad', 'neu', 'it-st corp sa-mark f'], f'your own corporation and alliance a star, then +, −, = (one set site-wide) {st}')
    # an icon beside its own word is decoration: no title, so the word is read once ("HostileHostile", caught by system_analyzer_check)
    bw = pg.evaluate("() => [standIcon('bad', true).includes('<title>'), standIcon('bad', true).includes('aria-hidden=\"true\"'), standIcon('bad').includes('<title>Hostile</title>'), SIDE_MARK_BY_WORD.h.includes('<title>')]")
    check(bw == [False, True, True, False], f'an icon beside its word: no title, hidden from readers; alone: titled {bw}')
    # v2026.10.31.2 (the owner: "we need a refresh / retry icon ... even if we need to add a timer"): zKillboard not answering
    # v2026.11.04.7: like zkbFetchNow, the first lookup reaches zKillboard and fails, the ones after it are held back (notSent)
    pg.evaluate("() => { window.__fls = fetchLossesStubs; fetchLossesStubs = async (c, h, f, o = {}) => { if(o.cacheOnly) return null; const held = zkbUnavailableUntil > Date.now(); if(!held){ zkbUnavailableUntil = Date.now() + 3000; zkbPauseSave(); } throw Object.assign(new Error(zkbUnavailableText()), {code: 'ZKB-01', zkbUnavailable: true, notSent: held}); }; lossStubCache.clear(); zkbMem.clear(); }   // v2026.11.04.5: the pause starts when a lookup fails, as zkbFetchNow does")
    pg.evaluate("() => fkOpen(fk.killId, fk.hash, null, null, {from: 'intel', km: fk.km})"); pg.wait_for_timeout(300); fleet_done(pg)
    # v2026.11.04.5 (the owner: "retry should probably be the same Load and Load All buttons ... modify the message to indicate the
    # nature of the issue and show the retry timer on the buttons themselves"): no Retry in the head; each row says what happened and
    # keeps its Load, Load all covers them; both count down while zKillboard can't be asked
    LS = """() => { const rows = [...document.querySelectorAll('#fleetPanel .fk-card .fk-src.err, #fleetPanel .fk-card .fk-src.held')], held = [...document.querySelectorAll('#fleetPanel .fk-card .fk-src.held')], ld = [...document.querySelectorAll('#fleetPanel .fk-card button.fk-ld')],
        la = document.querySelector('#fleetPanel .fk-card button.fk-la');
      return {head: !!document.querySelector('#fleetPanel .fk-card .pr-head .zkb-retry'), rows: rows.length, text: rows.filter(r => r.classList.contains('err')).map(r => r.textContent)[0], hover: rows.filter(r => r.classList.contains('err')).map(r => r.title)[0],
        nErr: rows.length - held.length, held: held.map(r => [r.textContent, r.title.startsWith('Not sent.') && r.title.includes("isn't blocked"), getComputedStyle(r).color]), dim: (() => { const d = document.createElement('i'); d.style.color = 'var(--text-dim)'; document.body.appendChild(d); const c = getComputedStyle(d).color; d.remove(); return c; })(),
        load: ld.map(b => [b.disabled, b.textContent.trim()]), box: ld.map(b => { const r = b.getBoundingClientRect(), row = b.closest('.fk-row, .pr-wrap, li, tr') || b.parentElement.parentElement, q = row.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.right), r.right <= q.right + 0.5]; }), all: la && [la.disabled, la.textContent.trim()], allLoaded: !!document.querySelector('#fleetPanel .fk-card .fk-all'),
        sum: (document.querySelector('#fleetPanel .fk-sum:not(.fk-vic) .pr-msg') || {}).textContent || '', n: fk.members.length,
        later: fk.members.filter(m => m.state === 'later').length, failed: fk.members.filter(m => m.state === 'later' && m.fail).length, done: fk.members.filter(m => m.state === 'done').length}; }"""
    R1 = pg.evaluate(LS)
    check(not R1['head'] and R1['failed'] > 0 and R1['rows'] == R1['failed'] and R1['text'] == "zKillboard isn't answering (ZKB-01)" and R1['hover'].endswith('(ZKB-01)') and 'reloading' in R1['hover'],
          f'zKillboard not answering: no Retry in the head; each failed row says what happened, short (all of it on hover) {R1["head"]} {R1["rows"]} of {R1["failed"]} failed ({R1["done"]} loaded from what was kept) {R1["text"]!r}')
    # v2026.11.04.7 (the owner: "it's giving the impression that that tool just doesn't work"): one lookup reached zKillboard and
    # failed (red); the ones held back by the pause say they weren't sent, dim, with why on hover
    check(R1['nErr'] == 1 and len(R1['held']) == R1['failed'] - 1 and all(t == 'Not sent: zKillboard needs a rest (ZKB-01)' and w and c == R1['dim'] for t, w, c in R1['held']),
          f'... one lookup failed (red), the rest say they were not sent (dim, why on hover) {R1["nErr"]} failed, {len(R1["held"])} held {R1["held"][:1]}')
    check(R1['load'] and all(d and re.match(r'0:0\d$', t) for d, t in R1['load']) and R1['all'] and R1['all'][0] and re.match(r'Load all in 0:0\d$', R1['all'][1])
          and not R1['allLoaded'] and R1['later'] == R1['failed'] and (R1['done'] > 0 or R1['sum'].startswith(f'None of the {R1["n"]} could be looked up yet (zKillboard')),
          f'... their Load and Load all wait out the pause with a countdown on the button; never "All loaded" {R1["load"][:2]} {R1["all"]} {R1["sum"][:70]!r}')
    gate = pg.evaluate("""async () => { const u0 = zkbUnavailableUntil, s0 = zkbFailStreak; zkbUnavailableUntil = Date.now() + 5000; let e1;
        try{ await zkbFetchNow('https://zkillboard.com/api/losses/characterID/1/'); }catch(e){ e1 = e; } zkbUnavailableUntil = u0; zkbFailStreak = s0; zkbPauseSave();
        const keep = fk.members; fk.members = [{state: 'later', fail: 'x (ZKB-01)', held: false}, ...Array.from({length: 10}, () => ({state: 'later', fail: 'x (ZKB-01)', held: true}))];
        const sum = fkFailSum(11); fk.members = keep; return [!!(e1 && e1.notSent), e1 && e1.code, sum]; }""")
    check(gate[0] and gate[1] == 'ZKB-01' and gate[2].startswith("zKillboard isn't answering: 1 lookup failed and the other 10 weren't sent"),
          f'the gate marks a lookup held back by the pause as not sent; with none loaded the summary says 1 failed, 10 not sent {gate}')
    fs = pg.evaluate("() => [fkFailShort(zkbUnavailableText() + ' (ZKB-01)'), fkFailShort(zkbBudgetError().message + ' (ZKB-04)'), fkFailShort('Killmail 1 fetch: not found (status 404) (ESI-05)')]")
    check(fs == ["zKillboard isn't answering (ZKB-01)", 'zKillboard limit reached in this browser (ZKB-04)', 'Killmail 1 fetch: not found (status 404) (ESI-05)'], f'a row names the issue: zKillboard down, the page\'s limit, anything else as its message says {fs}')
    pg2 = ctx.new_page(); pg2.goto('file://' + HTML); pg2.wait_for_timeout(300)
    w2 = pg2.evaluate("() => zkbWaitMs()"); pg2.close()
    check(w2 > 0, f'the pause is kept for a reload or another tab ({w2} ms left there)')
    pg.wait_for_timeout(3600)
    R2 = pg.evaluate(LS)
    pg.evaluate("() => { fetchLossesStubs = window.__fls; }")
    pg.click('#fleetPanel .fk-card button.fk-la'); pg.wait_for_timeout(300); fleet_done(pg)
    R3 = pg.evaluate(LS); dn = pg.evaluate("() => fk.members.filter(m => m.state === 'done').length")
    check(all(not d and t == 'Load' for d, t in R2['load']) and R2['all'] and not R2['all'][0] and R2['all'][1].startswith('Load all (') and R2['rows'] == R1['failed']
          and dn == R3['n'] and R3['allLoaded'] and not R3['rows'] and not pg.evaluate("() => !!document.querySelector('#fleetPanel .zkb-retry')"),
          f'... when the pause ends Load and Load all can be pressed with their own labels; Load all looks them up, then "All loaded" {R2["load"][:2]} {R2["all"]} {dn}/{R3["n"]}')
    # v2026.11.04.6 (the owner: "load button for individual rows alignment issue. let's drop the "Load in" text while the timer is
    # active"): the countdown is only the time, and Load and its countdown are one width at one right edge, inside the row
    w1, w2 = {b[0] for b in R1['box']}, {b[0] for b in R2['box']}
    check(len(w1) == 1 and w1 == w2 and {b[1] for b in R1['box']} == {b[1] for b in R2['box']} and all(b[2] for b in R1['box'] + R2['box']),
          f'... the countdown and "Load" are one width at one right edge, inside the row (widths {sorted(w1)} -> {sorted(w2)})')
    ctx.close()
    # phone
    ctx = new_ctx(390); pg = ctx.new_page(); open_fleet(pg)
    L = pg.evaluate("""() => [document.documentElement.scrollWidth, [...document.querySelectorAll('#fleetPanel *')].filter(e => { const b = e.getBoundingClientRect(); return e.checkVisibility() && b.width && (b.right > innerWidth + 1 || b.left < -1); }).map(e => e.className || e.tagName).slice(0, 5),
      [...document.querySelectorAll('#fleetPanel .fk-card button.pr-row')].map(r => [...r.querySelectorAll('.pr-rng')].filter(e => e.checkVisibility()).length)]""")
    check(L[0] <= 390 and not L[1] and all(n <= 1 for n in L[2]) and any(n == 1 for n in L[2]), f'390 px: nothing off the page, each range said once {L}')
    ctx.close()
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
