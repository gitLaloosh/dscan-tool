"""Gates and camps; short names for systems (v2026.10.31.5; roadmap/intel-plan.md).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/intel_gates_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner: "we need to come up with a clean way to communicate gate camps"; "people will often use shorthand to communicate
which gate enemies are on ... usually consists of three characters, one of which may be a "-" ... used in conjunction with
"gate""; one report is enough. From the mockup: "A: one tag", a camp is a report that places them on a gate and says camp words,
"toward you" yes, and kills: "can we visually differentiate between camp language from a report being the source or zkill
proximity being the source? maybe a slight color variation for now?". Plus two ideas from the intel-tool research: 4+ letters
before a system's dash (Telescope's rule) and your own shorthands. Runs intel_check.py's start (its made-up Chatlogs folder, ESI
and system names; you in 1DQ1-A), with three made-up names for far systems (ABCD-1, WXYZ-1, WXYZ-2), then made-up lines and
made-up kills. Checks:
  * "D-W7F0 gate camp on T5Z gate": in D-W7F0 (not T5ZI-S, the v2026.10.31.4 reading), on the T5ZI-S gate, a camp: the Feed's
    note and Camp tag; Near You's red tag "Camp · T5ZI-S gate" and "toward you";
  * two whole names before "gate", one gate apart ("Y-OMTZ gate camp on 5BTK-M gate"): the first named is where they are;
  * "5BT gate" and "MOG gate" (letters only) among 8WA-Z6's own gates: grey "MO-GZ5 gate" (no camp words), no "toward you";
  * "23G gate" not a gate of 1DQ1-A: a note "or 23G-XC?", no tag; "XYZ gate" not placed: left as typed;
  * "ABCD" is ABCD-1; "WXYZ" (two systems) is nothing;
  * kills at a stargate (zKillboard's locationID): the gate asked of ESI once, "at the 3-DMQT gate" in the Feed; 2 at one
    gate: Near You's tag in orange; 1 kill: no tag; a kill not at a gate: no note, no request; a report camp with a kill
    there: red, the kill in its hover;
  * your shorthands under the gear: each line checked (✓ / ✗), kept in this browser, and used for new lines;
  * none of the gate words or short names looked up as pilots; no page errors.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, 'intel_check.py'), encoding='utf-8').read()
_src = _src[:_src.index('    jumps = pg.evaluate("(names) => Object.fromEntries')]
_src = _src.replace("os.path.dirname(os.path.abspath(__file__))", repr(HERE), 1)
_extra = "30000001: 'QX-LOO', 30004713: 'ABCD-1', 30004712: 'WXYZ-1', 30004711: 'WXYZ-2'}"
assert _src.count("30000001: 'QX-LOO'}") == 1
_src = _src.replace("30000001: 'QX-LOO'}", _extra, 1)
_ns = {'__file__': os.path.join(HERE, 'intel_check.py'), '__name__': 'intel_check_prefix'}
_tail = r'''
    GATES = {50000001: 30004764, 50000002: 30004716, 50000003: 30004735}   # made-up stargate ids: to 3-DMQT, to 4K-TRB, to T5ZI-S
    SG = []
    def sg(route):
        gid = int(re.search(r'/stargates/(\d+)/', route.request.url).group(1)); SG.append(gid)
        if gid not in GATES: return route.fulfill(status=404, headers={'access-control-allow-origin': '*'}, body='{}')
        return route.fulfill(status=200, content_type='application/json', headers={'access-control-allow-origin': '*'}, body=json.dumps({'stargate_id': gid, 'destination': {'system_id': GATES[gid], 'stargate_id': 59999999}}))
    pg.route(re.compile(r'.*/universe/stargates/\d+/.*'), sg)
    L1 = ['D-W7F0 gate camp on T5Z gate Marrek Ketter* sabre +4', 'Y-OMTZ gate camp on 5BTK-M gate +2', '8WA-Z6 5 neuts on 5BT gate',
          '8WA-Z6 2 neuts on MOG gate', '1DQ1-A 3 reds on 23G gate', 'T5ZI-S 2 neuts on XYZ gate', 'ABCD 3 neuts', 'WXYZ 2 neuts']
    t0 = time.time() - 300
    body = ''.join(line(t0 + 10 * i, 'Scout Alt', m) for i, m in enumerate(L1))
    W(pg, F_INTEL, body); tick(pg, 3500)
    # made-up kills: 2 at the 3-DMQT gate in N-8YET, 1 at the 4K-TRB gate in QX-LIJ, 1 at a planet in Y-OMTZ, 1 at the T5ZI-S gate in D-W7F0
    pg.evaluate("""() => { const mk = (id, sys, loc, ago) => ({km: {killmail_id: id, killmail_time: new Date(Date.now() - ago).toISOString(), solar_system_id: sys,
        victim: {character_id: 91000045, corporation_id: 98000013, ship_type_id: 587}, attackers: [{character_id: 92000004, corporation_id: 98000013, ship_type_id: 22456, final_blow: true, damage_done: 100}]},
        z: {locationID: loc, totalValue: 1e7, attackerCount: 1, hash: 'x'}, t: Date.now() - ago});
      itAddKill(mk(9001, 30004762, 50000001, 90000)); itAddKill(mk(9002, 30004762, 50000001, 60000)); itAddKill(mk(9003, 30004714, 50000002, 50000));
      itAddKill(mk(9004, 30004763, 40000123, 40000)); itAddKill(mk(9005, 30004730, 50000003, 30000)); itRenderLists(); }""")
    tick(pg, 2500)
    NB = """() => Object.fromEntries([...document.querySelectorAll('#itNearList .it-nb')].map(r => { const g = r.querySelector('.it-gtag');
      return [r.querySelector('.sys').textContent, g ? [g.className.replace('it-gtag ', ''), g.textContent, !!r.querySelector('.it-tw'), g.title] : null]; }))"""
    FD = """() => [...document.querySelectorAll('#itFeedList .it-fd')].map(r => ({sys: (r.querySelector('.it-chip.sys') || {}).textContent, notes: [...r.querySelectorAll('.it-snote')].map(n => n.textContent),
      camp: !!r.querySelector('.it-fh .it-gtag.camp'), raw: ((r.querySelector('.it-raw .raw') || {}).textContent || ''), left: ((r.querySelector('.it-left') || {}).textContent || ''),
      chips: [...r.querySelectorAll('.it-chip.kw')].map(c => c.textContent), kill: r.classList.contains('kill')}))"""
    nb = pg.evaluate(NB); fd = pg.evaluate(FD)
    def row(raw): return next((x for x in fd if x['raw'] == raw), None)
    r = row(L1[0])
    check(r and r['sys'] == 'D-W7F0' and r['notes'] == ['on T5ZI-S gate'] and r['camp'] and 'camp' not in r['chips'] and 'gate' not in r['chips'],
          f'"D-W7F0 gate camp on T5Z gate": in D-W7F0, on the T5ZI-S gate, the Camp tag (no camp / gate chips) {r}')
    g = nb.get('D-W7F0')
    check(g and g[0] == 'camp' and g[1] == 'Camp · T5ZI-S gate' and g[2] and 'reported by Scout Alt' in g[3] and '1 kill at the T5ZI-S gate' in g[3],
          f"Near You D-W7F0: red 'Camp · T5ZI-S gate', toward you, a kill there in its hover {g}")
    r = row(L1[1]); g = nb.get('Y-OMTZ')
    check(r and r['sys'] == 'Y-OMTZ' and r['notes'] == ['on 5BTK-M gate'] and r['camp'] and g and g[:3] == ['camp', 'Camp · 5BTK-M gate', True],
          f'two names before "gate", one gate apart: the first is where they are {r} {g}')
    a, c = row(L1[2]), row(L1[3]); g = nb.get('8WA-Z6')
    check(a and a['notes'] == ['on 5BTK-M gate'] and not a['camp'] and c and c['notes'] == ['on MO-GZ5 gate'] and g and g[:3] == ['gt', 'MO-GZ5 gate', False],
          f'"5BT gate" and "MOG gate" among 8WA-Z6\'s gates; grey, the newest, no "toward you" {a} {c} {g}')
    a, c = row(L1[4]), row(L1[5])
    check(a and a['sys'] == '1DQ1-A' and a['notes'] == ['or 23G-XC?'] and nb.get('1DQ1-A') is None and c and c['notes'] == [] and c['left'] == 'XYZ' and nb.get('T5ZI-S') is None,
          f'"23G gate" not a gate of 1DQ1-A: a note, no tag; "XYZ gate" left as typed {a} {c} {nb.get("1DQ1-A")} {nb.get("T5ZI-S")}')
    a, c = row(L1[6]), row(L1[7])
    check(a and a['sys'] == 'ABCD-1' and c is None, f'"ABCD" is ABCD-1; "WXYZ" (two systems) makes no report {a} {c}')
    ks = {x['notes'][0] if x['notes'] else '' for x in fd if x['kill']}; g, q = nb.get('N-8YET'), nb.get('QX-LIJ')
    check(g and g[:2] == ['camp kz', 'Camp · 3-DMQT gate'] and '2 kills at the 3-DMQT gate' in g[3] and q is None and ks == {'at the 3-DMQT gate', 'at the 4K-TRB gate', 'at the T5ZI-S gate', ''}
          and sorted(SG) == [50000001, 50000002, 50000003] and nb.get('Y-OMTZ')[0] == 'camp',
          f'kills at a stargate: each gate asked once, the Feed says which gate; 2 at one gate: orange; 1: no tag; a planet: no note {g} {q} {ks} {SG}')
    cols = pg.evaluate("() => { const c = (sel) => { const e = document.querySelector(sel); return e ? getComputedStyle(e).color : null; }; return [c('#itNearList .it-gtag.camp:not(.kz)'), c('#itNearList .it-gtag.camp.kz'), c('#itNearList .it-gtag.gt')]; }")
    check(len(set(cols)) == 3 and None not in cols, f'a report camp, a kill camp and a gate: three colours {cols}')
    # your shorthands
    pg.evaluate("() => document.querySelector('#intelPanel .it-gear').click()"); tick(pg, 400)
    pg.fill('textarea[data-it-alias]', 'qq = abcd-1\nbogus = NOPE-1\nnot a line'); pg.dispatch_event('textarea[data-it-alias]', 'change'); tick(pg, 400)
    li = pg.evaluate("() => [...document.querySelectorAll('.it-alias li')].map(l => [l.className, l.textContent])")
    kept = pg.evaluate("() => JSON.parse(localStorage.getItem('dscanIntel')).alias")
    check(li == [['ok', '✓ qq → ABCD-1'], ['bad', '✗ bogus = NOPE-1: no system named NOPE-1'], ['bad', '✗ not a line: write it as word = system']] and kept.startswith('qq = abcd-1'),
          f'your shorthands: each line checked, kept in this browser {li} {kept!r}')
    pg.evaluate("() => document.querySelector('#intelPanel .it-pop .info-close').click()"); tick(pg, 300)
    W(pg, F_INTEL, body + line(time.time() - 5, 'Scout Alt', 'qq 4 neuts')); tick(pg, 3500)
    r = next((x for x in pg.evaluate(FD) if x['raw'] == 'qq 4 neuts'), None)
    check(r and r['sys'] == 'ABCD-1', f'"qq" read as ABCD-1 by your shorthand {r}')
    asked = {'t5z', '5bt', 'mog', '23g', 'xyz', 'abcd', 'wxyz', 'qq', 'camp', 'gate camp'} & IDS_ASKED
    check(not asked, f'no gate word or short name looked up as a pilot {sorted(asked)}')
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
'''
exec(compile(_src + _tail, 'intel_gates_check.py', 'exec'), _ns)
print(f"FAILURES: {_ns['fails']}")
sys.exit(1 if _ns['fails'] else 0)
