"""From an Intel kill to the fleet that got it (v2026.10.30.4).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/intel_fleet_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner: "killmails on the intel feed and near you should link to a fleet tab that assesses the fleet that got the kill.
include victims"; several kills on one badge: option A; a solo kill: "send them to the pilot dossier". Runs intel_kills_check.py's
start (made-up logs and kills, R2Z2 and ESI answered by stand-ins), then:
  * the Feed: Fleet ▸ on every kill with 2 or more pilots in ships, Pilot ▸ on a solo kill, neither on a kill with none;
  * Near You's kill badges are buttons;
  * a badge for one kill by 3 pilots: the Fleet tab, "From Intel", the killmail the feed gave (no ESI killmail request), the
    pilots in ships; Close: back to Intel, the Fleet tab hidden;
  * a badge for one solo kill: the Pilot Analyzer on that pilot;
  * a badge for 2 kills: the row opens on them, each with its Fleet ▸;
  * no page errors.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, 'intel_kills_check.py'), encoding='utf-8').read()
_src = _src[:_src.index("    # ---- v2026.10.29.3: the Feed's kill range")]
_src = _src.replace("os.path.dirname(os.path.abspath(__file__))", repr(HERE), 1)
_ns = {'__file__': os.path.join(HERE, 'intel_kills_check.py'), '__name__': 'intel_kills_prefix'}
_tail = r'''
    pg.wait_for_timeout(1000)
    F = pg.evaluate("""() => it.feed.filter(e => e.kind === 'kill').map(e => { const r = document.querySelector(`#itFeedList [data-it-fleet="${e.id}"], #itFeedList [data-it-solo="${e.id}"]`);
      return [e.kill.ships, r ? (r.dataset.itFleet ? 'fleet' : 'solo') : null, r ? r.textContent : '']; })""")
    want = [[n, 'fleet' if n >= 2 else 'solo' if n == 1 else None] for n, _, _ in F]
    check(F and [[n, k] for n, k, _ in F] == want and all(t in ('Fleet ▸', 'Pilot ▸', '') for _, _, t in F) and any(n >= 2 for n, _, _ in F) and any(n == 1 for n, _, _ in F),
          f'the Feed: Fleet ▸ on kills with 2+ pilots in ships, Pilot ▸ on a solo kill {F}')
    B = pg.evaluate("() => [...document.querySelectorAll('#itNearList .kb .it-kl')].map(b => [b.tagName, b.dataset.itKb || '', b.textContent])")
    check(B and all(t == 'BUTTON' and k for t, k, _ in B), f"Near You's kill badges are buttons {B}")
    # one kill by 3 pilots
    pg.evaluate("() => { window.__kmReq = []; const f = window.fetch; window.fetch = function(u){ if(String(u).includes('/killmails/')) window.__kmReq.push(String(u)); return f.apply(this, arguments); }; }")
    kb = pg.evaluate("""() => { const b = [...document.querySelectorAll('#itNearList [data-it-kb]')].find(b => { const [s, v] = b.dataset.itKb.split(':'); const st = it.near.get(Number(s));
      const ks = it.feed.filter(e => e.kind === 'kill' && (st.kills || []).some(k => k.id === e.kill.id && k.v === v)); return ks.length === 1 && ks[0].kill.ships >= 2; }); if(b){ b.click(); return b.dataset.itKb; } return null; }""")
    pg.wait_for_timeout(2500)
    fl = pg.evaluate("() => [document.querySelector('.tab-btn.active').textContent, !document.querySelector('#fleetTabWrap').hidden, fk.from, (document.querySelector('#fleetPanel .fk-sub') || {}).textContent || '', window.__kmReq.filter(u => u.includes(`/killmails/${fk.killId}/`)).length, fk.members.length]")
    check(kb and fl[0] == 'Fleet' and fl[1] and fl[2] == 'intel' and fl[3].startswith('From Intel') and fl[4] == 0 and fl[5] >= 2,
          f'a badge for one kill by several pilots: the Fleet tab, from Intel, the killmail the feed gave (no ESI request for it), its pilots in ships {kb} {fl}')
    pg.click('#fleetPanel [data-fk-close]'); pg.wait_for_timeout(400)
    cl = pg.evaluate("() => [document.querySelector('.tab-btn.active').textContent, document.querySelector('#fleetTabWrap').hidden]")
    check(cl == ['Intel', True], f'Close: back to Intel, the Fleet tab hidden {cl}')
    # one solo kill
    so = pg.evaluate("""() => { const b = [...document.querySelectorAll('#itNearList [data-it-kb]')].find(b => { const [s, v] = b.dataset.itKb.split(':'); const st = it.near.get(Number(s));
      const ks = it.feed.filter(e => e.kind === 'kill' && (st.kills || []).some(k => k.id === e.kill.id && k.v === v)); return ks.length === 1 && ks[0].kill.ships === 1; });
      if(!b) return null; const [s, v] = b.dataset.itKb.split(':'), st = it.near.get(Number(s)); const e = it.feed.find(x => x.kind === 'kill' && st.kills.some(k => k.id === x.kill.id && k.v === v));
      b.click(); return e.pilots.find(x => x.ship).name; }""")
    pg.wait_for_timeout(1500)
    pa = pg.evaluate("() => [document.querySelector('.tab-btn.active').textContent, document.querySelector('#pilotName').value]")
    check(so and pa == ['Pilot Analyzer', so], f'a badge for one solo kill: the Pilot Analyzer on its pilot ({so}) {pa}')
    pg.click('#tabBtnIntel'); pg.wait_for_timeout(400)
    # two kills on one badge
    two = pg.evaluate("""() => { const e0 = it.feed.find(x => x.kind === 'kill' && x.kill.ships >= 2); const km = JSON.parse(JSON.stringify(e0.kill.km)); km.killmail_id += 777777;
      itAddKill({km, z: {hash: 'a'.repeat(40), totalValue: 2e6}, t: Date.now() - 1000, history: true}); itRenderLists(); return [e0.p.sys[0].id, e0.kill.victim.side]; }""")
    pg.wait_for_timeout(300)
    ex = pg.evaluate("""(a) => { const [sys, v] = a; const b = document.querySelector(`#itNearList [data-it-kb="${sys}:${v}"]`); if(!b) return null; const label = b.textContent; b.click();
      return [label, it.nearOpen.has(sys), [...document.querySelectorAll(`#itNearList .it-nbx [data-it-fleet]`)].length, document.querySelector('.tab-btn.active').textContent]; }""", two)
    pg.wait_for_timeout(300)
    check(ex and ex[0].startswith('2 ') and ex[1] and ex[2] >= 2 and ex[3] == 'Intel', f'a badge for 2 kills: the row opens on them, each with Fleet ▸ {ex}')
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
'''
exec(compile(_src + _tail, 'intel_fleet_check.py', 'exec'), _ns)
print(f"FAILURES: {_ns['NS']['fails']}")
sys.exit(1 if _ns['NS']['fails'] else 0)
