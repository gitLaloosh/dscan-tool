"""From an Intel kill to the Fleet tab (v2026.10.30.4; v2026.10.31.2: every kill, its label, the kill to pick on the Fleet tab).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/intel_fleet_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner: "killmails on the intel feed and near you should link to a fleet tab that assesses the fleet that got the kill.
include victims"; then (v2026.10.31.2) "move the 'which kill to analyze' decision to the fleet tab", "kills in the feed should be
links as well. same mechanic", solo kills to the "Fleet tab too", and no separate Fleet ▸ / Pilot ▸ button. Runs
intel_kills_check.py's start (made-up logs and kills, R2Z2 and ESI answered by stand-ins), then:
  * the Feed: every kill's label is the button (data-it-fleet), no Fleet ▸ / Pilot ▸ anywhere;
  * Near You's kill badges are buttons;
  * a badge for one kill by several pilots: the Fleet tab, "From Intel", the killmail the feed gave (no ESI killmail request),
    the pilots in ships, no list to pick from; Close: back to Intel, the Fleet tab hidden;
  * a badge for one solo kill: the Fleet tab too, its one pilot;
  * a badge for 2 kills: the Fleet tab on the newer, both listed to pick from, the newer pressed; a new kill in Intel doesn't
    change the list; picking the other shows it, the list kept;
  * a Feed kill's label: that kill in the Fleet tab; a Near You row opened: each kill's label opens it too;
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
    F = pg.evaluate("() => it.feed.filter(e => e.kind === 'kill').map(e => { const b = document.querySelector(`#itFeedList button.it-ty[data-it-fleet=\"${e.id}\"]`); return [!!e.kill.km, !!b, b ? b.textContent : '']; })")
    check(F and all(k == b for k, b, _ in F) and all(t in ('Hostile killed', 'Neutral killed', 'Friendly lost') for k, b, t in F if b)
          and not pg.evaluate("() => !!document.querySelector('#intelPanel [data-it-solo], #intelPanel .it-fl')"), f"the Feed: every kill's label is the button, no Fleet ▸ / Pilot ▸ {F}")
    B = pg.evaluate("() => [...document.querySelectorAll('#itNearList .kb .it-kl')].map(b => [b.tagName, b.dataset.itKb || '', b.textContent])")
    check(B and all(t == 'BUTTON' and k for t, k, _ in B), f"Near You's kill badges are buttons {B}")
    BADGE = """(want) => { const b = [...document.querySelectorAll('#itNearList [data-it-kb]')].find(b => { const [s, v] = b.dataset.itKb.split(':'); const st = it.near.get(Number(s));
      const ks = it.feed.filter(e => e.kind === 'kill' && (st.kills || []).some(k => k.id === e.kill.id && k.v === v)); return ks.length === 1 && (want === 'solo' ? ks[0].kill.ships === 1 : ks[0].kill.ships >= 2); });
      if(b){ b.click(); return b.dataset.itKb; } return null; }"""
    STATE = "() => [document.querySelector('.tab-btn.active').textContent, !document.querySelector('#fleetTabWrap').hidden, fk.from, (document.querySelector('#fleetPanel .fk-sub') || {}).textContent || '', window.__kmReq.filter(u => u.includes(`/killmails/${fk.killId}/`)).length, fk.members.length, document.querySelectorAll('#fleetPanel .fk-pk').length]"
    pg.evaluate("() => { window.__kmReq = []; const f = window.fetch; window.fetch = function(u){ if(String(u).includes('/killmails/')) window.__kmReq.push(String(u)); return f.apply(this, arguments); }; }")
    kb = pg.evaluate(BADGE, 'fleet'); pg.wait_for_timeout(2500)
    fl = pg.evaluate(STATE)
    check(kb and fl[0] == 'Fleet' and fl[1] and fl[2] == 'intel' and fl[3].startswith('From Intel') and fl[4] == 0 and fl[5] >= 2 and fl[6] == 0,
          f'a badge for one kill by several pilots: the Fleet tab from Intel, the killmail the feed gave (no ESI request), its pilots, nothing to pick {kb} {fl}')
    pg.click('#fleetPanel [data-fk-close]'); pg.wait_for_timeout(400)
    cl = pg.evaluate("() => [document.querySelector('.tab-btn.active').textContent, document.querySelector('#fleetTabWrap').hidden]")
    check(cl == ['Intel', True], f'Close: back to Intel, the Fleet tab hidden {cl}')
    so = pg.evaluate(BADGE, 'solo'); pg.wait_for_timeout(2500)
    fs = pg.evaluate(STATE)
    check(so and fs[0] == 'Fleet' and fs[2] == 'intel' and fs[5] == 1, f'a badge for one solo kill: the Fleet tab too, its one pilot {so} {fs}')
    pg.click('#fleetPanel [data-fk-close]'); pg.wait_for_timeout(400)
    # two kills on one badge: the newer opens, both listed to pick from
    two = pg.evaluate("""() => { const e0 = it.feed.find(x => x.kind === 'kill' && x.kill.ships >= 2); const km = JSON.parse(JSON.stringify(e0.kill.km)); km.killmail_id += 777777;
      itAddKill({km, z: {hash: 'a'.repeat(40), totalValue: 2e6}, t: Date.now() - 1000, history: true}); itRenderLists(); return [e0.p.sys[0].id, e0.kill.victim.side, e0.kill.id, km.killmail_id]; }""")
    pg.wait_for_timeout(300)
    lbl = pg.evaluate("(a) => { const b = document.querySelector(`#itNearList [data-it-kb=\"${a[0]}:${a[1]}\"]`); if(!b) return null; const t = b.textContent; b.click(); return t; }", two); pg.wait_for_timeout(2500)
    P = pg.evaluate("() => [fk.killId, [...document.querySelectorAll('#fleetPanel .fk-pk')].map(b => b.getAttribute('aria-pressed')), (document.querySelector('#fleetPanel .fk-pk-h') || {}).textContent || '']")
    check(lbl and lbl.startswith('2 ') and P[0] == two[3] and P[1] == ['true', 'false'] and P[2].startswith('2 kills'), f'a badge for 2 kills: the Fleet tab on the newer, both listed, the newer pressed ({lbl}) {P}')
    pg.evaluate("""() => { const e0 = it.feed.find(x => x.kind === 'kill' && x.kill.ships >= 2); const km = JSON.parse(JSON.stringify(e0.kill.km)); km.killmail_id += 888888;
      itAddKill({km, z: {hash: 'b'.repeat(40), totalValue: 3e6}, t: Date.now(), history: true}); itRenderLists(); }"""); pg.wait_for_timeout(300)
    n2 = pg.evaluate("() => document.querySelectorAll('#fleetPanel .fk-pk').length")
    pg.click('#fleetPanel .fk-pk[data-fk-pick=\"1\"]'); pg.wait_for_timeout(2500)
    P2 = pg.evaluate("() => [fk.killId, [...document.querySelectorAll('#fleetPanel .fk-pk')].map(b => b.getAttribute('aria-pressed')), fk.members.length]")
    check(n2 == 2 and P2[0] == two[2] and P2[1] == ['false', 'true'] and P2[2] >= 2, f'a new kill in Intel leaves the list as it was ({n2}); picking the other shows it, the list kept {P2}')
    pg.click('#fleetPanel [data-fk-close]'); pg.wait_for_timeout(400)
    # the Feed's label, and a Near You row opened
    fe = pg.evaluate("() => { const b = document.querySelector('#itFeedList button.it-ty[data-it-fleet]'); const e = it.feed.find(x => x.id === Number(b.dataset.itFleet)); b.click(); return e.kill.id; }"); pg.wait_for_timeout(2500)
    ff = pg.evaluate("() => [document.querySelector('.tab-btn.active').textContent, fk.killId, fk.from]")
    check(ff == ['Fleet', fe, 'intel'], f"a Feed kill's label: that kill in the Fleet tab {ff}")
    pg.click('#fleetPanel [data-fk-close]'); pg.wait_for_timeout(400)
    nb = pg.evaluate("(sys) => { document.querySelector(`#itNearList [data-it-nbo=\"${sys}\"]`).click(); return null; }", two[0]); pg.wait_for_timeout(300)
    no = pg.evaluate("(sys) => { const b = [...document.querySelectorAll('#itNearList .it-nbx button.it-kl[data-it-fleet]')]; if(!b.length) return null; const e = it.feed.find(x => x.id === Number(b[0].dataset.itFleet)); b[0].click(); return [b.length, e.kill.id]; }", two[0]); pg.wait_for_timeout(2500)
    nf = pg.evaluate("() => [document.querySelector('.tab-btn.active').textContent, fk.killId]")
    check(no and no[0] >= 2 and nf == ['Fleet', no[1]], f"a Near You row opened: each kill's label opens it {no} {nf}")
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
'''
exec(compile(_src + _tail, 'intel_fleet_check.py', 'exec'), _ns)
print(f"FAILURES: {_ns['NS']['fails']}")
sys.exit(1 if _ns['NS']['fails'] else 0)
