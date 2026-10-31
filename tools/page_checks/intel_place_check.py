"""Where a report is, when its line names more than one system; a linked word that is a pilot; the Intel switch's off state; the
condensed "How Intel works" (v2026.10.30.2).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/intel_place_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner: "the tool recorded a pilot as the system name even though a valid system name was in the entry"; "some players
actually name their pilots in a way that it will screw up the intel channel entries"; his rules: what the words around a name
say ("which neighboring system's gate they are on or which system they were heading into"), the system "inside the ring", a
linked word ('*'), "dont blindly" take the first or last. Runs intel_check.py's start (its made-up Chatlogs folder, ESI and
system names; you in 1DQ1-A) up to Intel turned on, then, with made-up lines and made-up one-word pilots "Jita" and "Clear":
  * "Jita Marrek T5ZI-S": Jita is a pilot (a pilot's name, and another system is named), the report is in T5ZI-S;
  * "Jita Ketter": one system named: Jita stays the system;
  * "8WA-Z6 Marrek on 5BTK-M gate": in 8WA-Z6, "on 5BTK-M gate" as a note (v2026.10.31.5: was D-W7F0, which isn't one of
    8WA-Z6's gates and is now a note "or D-W7F0?", intel_gates_check.py); "Y-OMTZ Ketter -> MO-GZ5": in Y-OMTZ (3 jumps)
    though MO-GZ5 (1) is nearer, "→ MO-GZ5"; "Ketter jumped to 5BTK-M from N-8YET": in 5BTK-M, "from N-8YET";
  * no words around them: "QX-LIJ Marrek E-VKJV" in the nearer E-VKJV, "or QX-LIJ?"; "FM-JK5 Ketter JP4-AA" (next to each other)
    in JP4-AA, "on FM-JK5 gate?"; "23G-XC Marrek 8-YNBE" (4 jumps each) in the first, 23G-XC;
  * "MO-GZ5 10+": a head count of ten hostiles (v2026.10.30.3); "+3" still three more;
  * "3-DMQT clear": clear, and "clear" never looked up; "4K-TRB Clear*": Clear, linked, is a pilot: a sighting, not clear;
  * the ring: Feed Distance 3: "QX-LIJ Marrek" (4 jumps) in the Feed, not in Near You, no alert; Distance 2 with the alert range
    3: "Y-OMTZ" (3 jumps) still in Near You (the ring is the larger of the two); Distance "any": no ring;
  * the Feed row shows the note after the system, no second jump count;
  * the switch: on, the usual teal, still; off, an amber edge, knob and "Off", breathing (itSwBreathe); with reduced motion, still;
    "Use in assessments" (off) unchanged;
  * How Intel works: 3 short paragraphs, each with a bold lead, and 7 folded headings (v2026.10.31.5: Gates and camps), closed; one opens on a click; no
    "slider" or "red row" left; no page errors.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, 'intel_check.py'), encoding='utf-8').read()
_src = _src[:_src.index('    jumps = pg.evaluate("(names) => Object.fromEntries')]
_src = _src.replace("os.path.dirname(os.path.abspath(__file__))", repr(HERE), 1)
_ns = {'__file__': os.path.join(HERE, 'intel_check.py'), '__name__': 'intel_check_prefix'}
_tail = r'''
    ONE_WORD.update({'Jita': 96000011, 'Clear': 96000012})   # made-up pilots named like a system and like an intel word
    lines = ['Jita Marrek T5ZI-S', 'Jita Ketter', '8WA-Z6 Marrek on 5BTK-M gate', 'Y-OMTZ Ketter -> MO-GZ5', 'Ketter jumped to 5BTK-M from N-8YET',
             'QX-LIJ Marrek E-VKJV', 'FM-JK5 Ketter JP4-AA', '23G-XC Marrek 8-YNBE', '3-DMQT clear', 'MO-GZ5 10+', 'N-8YET Marrek +3']
    t0 = time.time() - 30
    W(pg, F_INTEL, ''.join(line(t0 + i, 'Scout Alt', m) for i, m in enumerate(lines))); tick(pg, 3000)
    asked_clear = 'clear' in IDS_ASKED
    W(pg, F_INTEL, line(time.time() - 5, 'Scout Alt', '4K-TRB Clear*')); tick(pg, 3000)
    R = pg.evaluate("""(lines) => Object.fromEntries([...lines, '4K-TRB Clear*'].map(l => { const e = it.feed.find(x => x.raw === l); return [l, e ? {
      sys: e.p.sys.map(s => [itSysName(s.id), s.role || '']), pilots: e.pilots.map(x => x.name), kind: e.kind, near: !!it.near.get(e.p.sys[0].id) && it.near.get(e.p.sys[0].id).t === e.t} : null]; }))""", lines)
    def got(l): return R.get(l) or {'sys': [], 'pilots': [], 'kind': None}
    def where(l): return got(l)['sys'][0][0] if got(l)['sys'] else None
    g = got('Jita Marrek T5ZI-S')
    check(where('Jita Marrek T5ZI-S') == 'T5ZI-S' and 'Jita' in g['pilots'] and len(g['sys']) == 1, f'"Jita Marrek T5ZI-S": Jita, a pilot, isn\'t the system; the report is in T5ZI-S {g}')
    check(where('Jita Ketter') == 'Jita' and got('Jita Ketter')['pilots'] == ['Ketter'], f'"Jita Ketter": one system named, Jita stays the system {got("Jita Ketter")}')
    exp = {'8WA-Z6 Marrek on 5BTK-M gate': [['8WA-Z6', ''], ['5BTK-M', 'gate']], 'Y-OMTZ Ketter -> MO-GZ5': [['Y-OMTZ', ''], ['MO-GZ5', 'dest']],
           'Ketter jumped to 5BTK-M from N-8YET': [['5BTK-M', ''], ['N-8YET', 'from']], 'QX-LIJ Marrek E-VKJV': [['E-VKJV', ''], ['QX-LIJ', 'or']],
           'FM-JK5 Ketter JP4-AA': [['JP4-AA', ''], ['FM-JK5', 'pair']], '23G-XC Marrek 8-YNBE': [['23G-XC', ''], ['8-YNBE', 'or']]}
    for l, s in exp.items(): check(got(l)['sys'] == s, f'"{l}": {s[0][0]} with {s[1][0]} as "{s[1][1]}" {got(l)["sys"]}')
    check(got('3-DMQT clear')['kind'] == 'clear' and not asked_clear, f'"3-DMQT clear": clear, and "clear" never looked up as a pilot {got("3-DMQT clear")} {asked_clear}')
    # v2026.10.30.3 (the owner: '"10+" ... should be translated to "10 Hostiles"'): a head count; "+3" still three more
    pc = pg.evaluate("""() => { const e = it.feed.find(x => x.raw === 'MO-GZ5 10+'), f = it.feed.find(x => x.raw === 'N-8YET Marrek +3');
      const r = [...document.querySelectorAll('#itNearList .it-nb')].find(x => x.querySelector('.sys').textContent === 'MO-GZ5');
      const row = [...document.querySelectorAll('#itFeedList .it-fd')].find(x => (x.querySelector('.raw') || {}).textContent === 'MO-GZ5 10+');
      return [e && e.p.count, e && e.kind, r && r.querySelector('.st b').textContent, row && [...row.querySelectorAll('.it-chip.kw')].map(c => c.textContent), f && [f.p.extra, f.p.count]]; }""")
    check(pc[0] == {'n': 10, 'kind': 'red'} and pc[1] == 'seen' and pc[2] == '10 hostile' and pc[3] == ['10 red'] and pc[4] == [3, None] and '10+' not in IDS_ASKED,
          f'"MO-GZ5 10+": ten hostiles (chip "10 red", Near You "10 hostile"), never looked up; "+3" still three more {pc}')
    g = got('4K-TRB Clear*')
    check(g['kind'] == 'seen' and g['pilots'] == ['Clear'] and where('4K-TRB Clear*') == '4K-TRB', f'"4K-TRB Clear*": Clear, linked from Local, is a pilot: a sighting, not "clear" {g}')
    notes = pg.evaluate("""() => Object.fromEntries([...document.querySelectorAll('#itFeedList .it-fd')].map(r => [r.querySelector('.raw') ? r.querySelector('.raw').textContent : '',
      [r.querySelector('.fsys').innerText.replace(/\\s+/g, ' ').trim(), r.querySelectorAll('.fsys .j').length]]))""")
    want = {'8WA-Z6 Marrek on 5BTK-M gate': '8WA-Z6 on 5BTK-M gate', 'Y-OMTZ Ketter -> MO-GZ5': 'Y-OMTZ → MO-GZ5', 'Ketter jumped to 5BTK-M from N-8YET': '5BTK-M from N-8YET',
            'QX-LIJ Marrek E-VKJV': 'E-VKJV or QX-LIJ?', 'FM-JK5 Ketter JP4-AA': 'JP4-AA on FM-JK5 gate?'}
    check(all(notes.get(l, ['', 9])[0] == w and notes[l][1] == 0 for l, w in want.items()), f'the Feed: the note after the system, no second jump count {[(w, notes.get(l)) for l, w in want.items()]}')
    # ---- the ring ----
    beeps0 = pg.evaluate("() => __fs.beeps")
    pg.evaluate("() => { it.set.feed.dist = 3; }")
    W(pg, F_INTEL, line(time.time() - 4, 'Scout Alt', 'QX-LIJ Marrek')); tick(pg, 3000)
    q = pg.evaluate("() => { const e = it.feed.find(x => x.raw === 'QX-LIJ Marrek'); return [!!e, !!it.near.get(it.names.byLower.get('qx-lij'))]; }")
    check(q == [True, False] and pg.evaluate("() => __fs.beeps") == beeps0, f'Distance 3: "QX-LIJ Marrek" (4 jumps) in the Feed, not in Near You, no alert {q}')
    pg.evaluate("() => { it.set.feed.dist = 2; it.near.delete(it.names.byLower.get('y-omtz')); }")
    W(pg, F_INTEL, line(time.time() - 3, 'Scout Alt', 'Y-OMTZ Marrek')); tick(pg, 3000)
    y = pg.evaluate("() => !!it.near.get(it.names.byLower.get('y-omtz'))")
    check(y, f'Distance 2, alert range 3: "Y-OMTZ" (3 jumps) still in Near You: the ring is the larger of the two {y}')
    pg.evaluate("() => { it.set.feed.dist = 0; }")
    W(pg, F_INTEL, line(time.time() - 2, 'Scout Alt', 'QX-LIJ Ketter')); tick(pg, 3000)
    check(pg.evaluate("() => !!it.near.get(it.names.byLower.get('qx-lij'))"), 'Distance "any": no ring, "QX-LIJ Ketter" (4 jumps) in Near You')
    # ---- the switch ----
    SW = """() => { const s = document.querySelector('#intelSw'), c = getComputedStyle(s), k = getComputedStyle(s, '::after'), l = getComputedStyle(s.nextElementSibling);
      const u = document.querySelector('#myShipUse'), cu = getComputedStyle(u);
      return {on: s.checked, edge: c.borderTopColor, knob: k.backgroundColor, label: l.color, anim: c.animationName, use: [cu.borderTopColor, cu.animationName]}; }"""
    on = pg.evaluate(SW)
    check(on['on'] and on['edge'] == 'rgb(31, 111, 128)' and on['anim'] == 'none', f'the Intel switch on: the usual teal, still {on}')
    pg.click('#intelSwLabel'); pg.wait_for_timeout(400)
    off = pg.evaluate(SW); amber = 'rgb(217, 154, 60)'
    check(not off['on'] and off['edge'] == amber and off['knob'] == amber and off['label'] == amber and off['anim'] == 'itSwBreathe',
          f'off: an amber edge, knob and "Off", breathing (users: "the intel on/off blends in too much") {off}')
    check(off['use'][0] != amber and off['use'][1] == 'none', f'"Use in assessments", off, unchanged: only the Intel switch has an off state of its own {off["use"]}')
    pg.emulate_media(reduced_motion='reduce'); pg.wait_for_timeout(200)
    rm = pg.evaluate(SW)
    check(rm['anim'] == 'none' and rm['edge'] == amber, f'with reduced motion: still amber, no breathing {rm}')
    pg.emulate_media(reduced_motion='no-preference')
    # ---- How Intel works ----
    pg.click('#intelPanel .it-head .info-btn'); pg.wait_for_timeout(200)
    inf = pg.evaluate("""() => { const b = document.querySelector('#intelPanel .it-head .info-body'), ds = [...b.querySelectorAll('details.info-more')];
      return [[...b.children].filter(x => x.tagName === 'P').length, b.querySelectorAll(':scope > p b').length, ds.length, ds.filter(d => d.open).length, b.innerText.split(/\\s+/).length, b.textContent]; }""")
    pg.evaluate("() => { const s = document.querySelector('#intelPanel .it-head .info-body details.info-more summary'); if(s) s.click(); }"); pg.wait_for_timeout(100)
    op = pg.evaluate("() => [...document.querySelectorAll('#intelPanel .it-head .info-body details.info-more')].map(d => d.open)")
    check(inf[:4] == [3, 3, 7, 0] and inf[4] < 110 and op[0] and not any(op[1:]),
          f'How Intel works: 3 short paragraphs (each with a bold lead) and 7 folded headings, closed ({inf[4]} words shown); one opens on a click {inf[:5]} {op}')
    check('slider' not in inf[5] and 'red row' not in inf[5], 'no "slider" or "red row" left in it')
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
'''
exec(compile(_src + _tail, 'intel_place_check.py', 'exec'), _ns)
print(f"FAILURES: {_ns['fails']}")
sys.exit(1 if _ns['fails'] else 0)
