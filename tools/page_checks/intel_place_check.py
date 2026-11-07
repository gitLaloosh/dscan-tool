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
  * the Feed row shows the note after the system (v2026.10.31.6: among the line's tags), no second jump count;
  * the switch: on, the usual teal, still; off, an amber edge, knob and "Off", breathing (itSwBreathe); with reduced motion, still;
    "Use in assessments" (off) unchanged;
  * v2026.11.06.3 (build queue 018; Project doc roadmap/intel-surname-system-plan.md; the owner's screenshots: one scout reported
    eight times, in the system that is his surname): made-up pilots "Ressa Jita", "Jita Ressa", "Ressa E-VKJV", "Kel Ressa Jita" and
    "Tovan E-VKJV". No name looked up holds two systems. Two systems: "Ressa Jita T5ZI-S", "T5ZI-S Ressa Jita", "Jita Ressa T5ZI-S" in T5ZI-S with the pilot, no note,
    nothing left over; "(Sabre)" after the name paired with it; "Ressa Jita QX-LIJ*" in QX-LIJ; Distance 3, "Ressa E-VKJV QX-LIJ"
    in QX-LIJ (the pilot check before the ring), Feed only, no alert; "Kel Ressa Jita T5ZI-S" a three-word name; "Varro E-VKJV
    T5ZI-S" (not a pilot) as before. One system inside the name: "Ressa E-VKJV Sabre" and "... probably a sabre" make no row, no
    Near You change, no alert, still the last line. Kept as the system: "Varro Jita Sabre", "ressa e-vkjv Sabre" (other capitals),
    "Tovan E-VKJV Sabre" (Tovan alone a pilot, and "Tovan E-VKJV" one too), "E-VKJV", "E-VKJV clr". One /universe/ids/ batch for the lines written at once.
  * v2026.11.06.5 (build queue 020; Project doc roadmap/intel-filler-in-name-plan.md; made-up pilots "Tavi from Ash" and "Tavi"): a
    name with a filler word in it is looked up and read as one pilot in its own capitals or dragged in ("T5ZI-S* Tavi from Ash",
    "... Sabre", "... (Sabre)" paired, "tavi from ash*"); other capitals, a '*' inside, a filler at an edge ("Marrek from T5ZI-S"),
    4 words, over 37 characters and names that aren't pilots ("Varro of Ash") as before; one /universe/ids/ batch.
  * How Intel works: 3 short paragraphs, each with a bold lead, and 8 folded headings (v2026.10.31.5: Gates and camps; v2026.11.02.4:
    the map), closed; one opens on a click; no
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
      [(r.querySelector('.fsys').innerText + ' ' + [...r.querySelectorAll('.ftg .it-snote')].map(n => n.innerText).join(' ')).replace(/\\s+/g, ' ').trim(), r.querySelectorAll('.fsys .j, .ftg .j').length]]))""")   # v2026.10.31.6: the notes among the tags
    want = {'8WA-Z6 Marrek on 5BTK-M gate': '8WA-Z6 on 5BTK-M gate', 'Y-OMTZ Ketter -> MO-GZ5': 'Y-OMTZ → MO-GZ5', 'Ketter jumped to 5BTK-M from N-8YET': '5BTK-M from N-8YET',
            'QX-LIJ Marrek E-VKJV': 'E-VKJV or QX-LIJ?', 'FM-JK5 Ketter JP4-AA': 'JP4-AA on FM-JK5 gate?'}
    check(all(notes.get(l, ['', 9])[0] == w and notes[l][1] == 0 for l, w in want.items()), f'the Feed: the note after the system, no second jump count {[(w, notes.get(l)) for l, w in want.items()]}')
    # ---- v2026.11.06.3: a pilot whose surname is a system's name (build queue 018) ----
    ONE_WORD.update({'Ressa Jita': 96000021, 'Jita Ressa': 96000022, 'Ressa E-VKJV': 96000023, 'Kel Ressa Jita': 96000024, 'Tovan': 96000025, 'Tovan E-VKJV': 96000026})   # names never asked before here (a name is asked once)
    pg.evaluate("() => { it.set.feed.dist = 0; }")
    SN = ['Ressa Jita T5ZI-S', 'T5ZI-S Ressa Jita', 'Jita Ressa T5ZI-S', 'T5ZI-S Ressa Jita (Sabre)', 'Ressa Jita QX-LIJ*', 'Kel Ressa Jita T5ZI-S',
          'Varro E-VKJV T5ZI-S', 'Varro Jita Sabre', 'ressa e-vkjv Sabre', 'Tovan E-VKJV Sabre', 'E-VKJV', 'E-VKJV clr']
    LONE = ['Ressa E-VKJV Sabre', 'Ressa E-VKJV probably a sabre']
    near0 = pg.evaluate("() => JSON.stringify([...it.near.keys()].sort())"); beeps1 = pg.evaluate("() => __fs.beeps")
    pg.evaluate("() => { window.__ids = 0; const f = window.fetch; window.fetch = function(u, o){ if(String(u).includes('/universe/ids/')) window.__ids++; return f.apply(this, arguments); }; }")
    t1 = time.time() - 8   # the newest lines in the log, so the last of them is the channel's last line
    W(pg, F_INTEL, ''.join(line(t1 + i * 0.5, 'Scout Alt', m) for i, m in enumerate(SN + LONE))); tick(pg, 3000)
    S2 = pg.evaluate("""(lines) => Object.fromEntries(lines.map(l => { const e = it.feed.find(x => x.raw === l); return [l, e ? {
      sys: e.p.sys.map(s => [itSysName(s.id), s.role || '']), pilots: e.pilots.map(x => x.name), kind: e.kind, shape: itShape(e)} : null]; }))""", SN + LONE)
    def g2(l): return S2.get(l) or {'sys': [], 'pilots': [], 'shape': '', 'kind': None}
    for l in ['Ressa Jita T5ZI-S', 'T5ZI-S Ressa Jita']:
        check(g2(l)['sys'] == [['T5ZI-S', '']] and g2(l)['pilots'] == ['Ressa Jita'] and 'not placed' not in g2(l)['shape'],
              f'"{l}": in T5ZI-S, the pilot "Ressa Jita", no "or Jita?", nothing left over {g2(l)}')
    check(g2('Jita Ressa T5ZI-S')['sys'] == [['T5ZI-S', '']] and g2('Jita Ressa T5ZI-S')['pilots'] == ['Jita Ressa'], f'"Jita Ressa T5ZI-S": the surname first works too {g2("Jita Ressa T5ZI-S")}')
    pr = pg.evaluate("""() => { const e = it.feed.find(x => x.raw === 'T5ZI-S Ressa Jita (Sabre)'); return e ? [...(it.near.get(e.p.sys[0].id) || {pairs: new Map()}).pairs].map(([id, s]) => [id, s.name]) : null; }""")
    check(g2('T5ZI-S Ressa Jita (Sabre)')['pilots'] == ['Ressa Jita'] and pr and [96000021, 'Sabre'] in [list(x) for x in pr],
          f'"T5ZI-S Ressa Jita (Sabre)": the Sabre paired with "Ressa Jita" {g2("T5ZI-S Ressa Jita (Sabre)")} {pr}')
    check(g2('Ressa Jita QX-LIJ*')['sys'] == [['QX-LIJ', '']] and g2('Ressa Jita QX-LIJ*')['pilots'] == ['Ressa Jita'], f'"Ressa Jita QX-LIJ*" (dragged in): in QX-LIJ {g2("Ressa Jita QX-LIJ*")}')
    check(g2('Kel Ressa Jita T5ZI-S')['pilots'] == ['Kel Ressa Jita'] and g2('Kel Ressa Jita T5ZI-S')['sys'] == [['T5ZI-S', '']], f'"Kel Ressa Jita T5ZI-S": a three-word name {g2("Kel Ressa Jita T5ZI-S")}')
    v = g2('Varro E-VKJV T5ZI-S')
    check(v['sys'] == [['T5ZI-S', ''], ['E-VKJV', 'or']] and v['pilots'] == [] and 'not placed' in v['shape'], f'"Varro E-VKJV T5ZI-S" ("Varro E-VKJV" not a pilot): as before, the nearer T5ZI-S, "or E-VKJV?", Varro left over {v}')
    for l, w, pil in [('Varro Jita Sabre', 'Jita', []), ('ressa e-vkjv Sabre', 'E-VKJV', []), ('Tovan E-VKJV Sabre', 'E-VKJV', ['Tovan']), ('E-VKJV', 'E-VKJV', []), ('E-VKJV clr', 'E-VKJV', [])]:
        check(g2(l)['sys'][:1] == [[w, '']] and g2(l)['pilots'] == pil, f'"{l}": one system, not a pilot by the strict rules: stays in {w} {g2(l)}')
    near1 = pg.evaluate("() => JSON.stringify([...it.near.keys()].sort())")
    check(all(S2.get(l) is None for l in LONE) and pg.evaluate("(l) => !it.feed.some(x => x.raw === l[0] || x.raw === l[1])", LONE),
          f'"Ressa E-VKJV Sabre", "Ressa E-VKJV probably a sabre": the only system is inside a pilot\'s name: no Feed row {[S2.get(l) for l in LONE]}')
    last = pg.evaluate("() => it.lastLine")
    check(abs(last / 1000 - (t1 + (len(SN) + len(LONE) - 1) * 0.5)) < 1.5, f'... and the last of them still counts as the channel\'s last line ({last / 1000:.1f} vs {t1 + (len(SN) + len(LONE) - 1) * 0.5:.1f})')
    spans = sorted(n for n in IDS_ASKED if sum(x in n for x in ('t5zi-s', 'e-vkjv', 'jita', 'qx-lij')) >= 2 and n not in ('jita ressa', 'ressa jita'))
    check(not spans, f'no name looked up holds two systems ({spans})')
    ids = pg.evaluate("() => window.__ids")
    check(ids == 1, f'the lines written at once: one /universe/ids/ batch ({ids})')
    # the ring: the surname system inside it, the real one outside
    pg.evaluate("() => { it.set.feed.dist = 3; it.near.delete(it.names.byLower.get('qx-lij')); }"); beeps2 = pg.evaluate("() => __fs.beeps")
    W(pg, F_INTEL, line(time.time() - 6, 'Scout Alt', 'Ressa E-VKJV QX-LIJ')); tick(pg, 3000)
    rg = pg.evaluate("() => { const e = it.feed.find(x => x.raw === 'Ressa E-VKJV QX-LIJ'); return e ? [itSysName(e.p.sys[0].id), e.pilots.map(x => x.name), !!it.near.get(e.p.sys[0].id), !!it.near.get(it.names.byLower.get('e-vkjv'))] : null; }")
    check(rg and rg[:3] == ['QX-LIJ', ['Ressa E-VKJV'], False] and pg.evaluate("() => __fs.beeps") == beeps2,
          f'Distance 3, "Ressa E-VKJV QX-LIJ": in QX-LIJ (4 jumps; the pilot check comes before the ring), Feed only, no alert {rg}')
    pg.evaluate("() => { it.set.feed.dist = 0; }")
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
    # ---- v2026.11.06.5: a pilot whose name has a filler word in it (build queue 020; made-up names only) ----
    ONE_WORD.update({'Tavi from Ash': 96000031, 'Tavi': 96000032})
    FN = ['T5ZI-S* Tavi from Ash', 'T5ZI-S Tavi from Ash Sabre', 'T5ZI-S Tavi from Ash (Sabre)', 'T5ZI-S tavi from ash', 'T5ZI-S tavi from ash*',
          'T5ZI-S Tavi* from Ash', 'QX-LIJ Marrek from T5ZI-S', 'T5ZI-S Marrek in local', 'T5ZI-S Varro of Ash', 'T5ZI-S Tavi of the Ash',
          'T5ZI-S Abcdefghijklmnopq from Rstuvwxyzabcdefghij', 'T5ZI-S Brin* of Vale']   # the last: a '*' ends a name, so "Brin of Vale" isn't looked up
    pg.evaluate("() => { window.__ids = 0; }")
    W(pg, F_INTEL, ''.join(line(time.time() - 7 + i * 0.3, 'Scout Alt', m) for i, m in enumerate(FN))); tick(pg, 3000)
    S3 = pg.evaluate("""(lines) => Object.fromEntries(lines.map(l => { const e = it.feed.find(x => x.raw === l); return [l, e ? {
      sys: e.p.sys.map(s => [itSysName(s.id), s.role || '']), pilots: e.pilots.map(x => x.name), shape: itShape(e),
      pairs: [...(it.near.get(e.p.sys[0].id) || {pairs: new Map()}).pairs].map(([id, s]) => [id, s.name])} : null]; }))""", FN)
    def g3(l): return S3.get(l) or {'sys': [], 'pilots': [], 'shape': '', 'pairs': []}
    for l in ['T5ZI-S* Tavi from Ash', 'T5ZI-S Tavi from Ash Sabre', 'T5ZI-S Tavi from Ash (Sabre)']:
        check(g3(l)['sys'][:1] == [['T5ZI-S', '']] and g3(l)['pilots'] == ['Tavi from Ash'] and 'not placed' not in g3(l)['shape'] and g3(l)['shape'].split('  [')[0].count('PILOT') == 1,
              f'"{l}": in T5ZI-S, the pilot "Tavi from Ash" (not the one-word "Tavi"), nothing left over {g3(l)}')
    check([96000031, 'Sabre'] in [list(x) for x in g3('T5ZI-S Tavi from Ash (Sabre)')['pairs']], f'"T5ZI-S Tavi from Ash (Sabre)": the Sabre paired with the three-word pilot {g3("T5ZI-S Tavi from Ash (Sabre)")["pairs"]}')
    check(g3('T5ZI-S tavi from ash')['pilots'] == [], f'"T5ZI-S tavi from ash" (other capitals, typed): no three-word pilot, as before {g3("T5ZI-S tavi from ash")}')
    check(g3('T5ZI-S tavi from ash*')['pilots'] == ['Tavi from Ash'], f'"T5ZI-S tavi from ash*" (dragged in): the three-word pilot {g3("T5ZI-S tavi from ash*")}')
    check(g3('T5ZI-S Tavi* from Ash')['pilots'] == ['Tavi'], f'"T5ZI-S Tavi* from Ash": a \'*\' ends a name, so the pilot is "Tavi" {g3("T5ZI-S Tavi* from Ash")}')
    q = g3('QX-LIJ Marrek from T5ZI-S')
    check(q['sys'] == [['QX-LIJ', ''], ['T5ZI-S', 'from']] and q['pilots'] == ['Marrek'], f'"QX-LIJ Marrek from T5ZI-S": as before, Marrek in QX-LIJ, "from T5ZI-S" {q}')
    for l, pil in [('T5ZI-S Marrek in local', ['Marrek']), ('T5ZI-S Varro of Ash', []), ('T5ZI-S Tavi of the Ash', ['Tavi'])]:
        check(g3(l)['sys'][:1] == [['T5ZI-S', '']] and g3(l)['pilots'] == pil, f'"{l}": as before {g3(l)}')
    asked = sorted(n for n in IDS_ASKED if ' from ' in n or ' of ' in n or ' in ' in n or n.endswith(' from') or n.startswith('from '))
    want = ['tavi from ash', 'varro of ash']
    check(asked == want, f'looked up: only stretches with a filler word between two plain words, 3 words and at most 37 characters; no filler at an edge, no system, no 4 words, no \'*\' inside ({asked})')
    ids = pg.evaluate("() => window.__ids")
    check(ids == 1, f'... in the one /universe/ids/ batch for the lines written at once ({ids})')
    # ---- the switch ----
    SW = """() => { const s = document.querySelector('#intelSw'), c = getComputedStyle(s), k = getComputedStyle(s, '::after'), l = getComputedStyle(s.nextElementSibling);
      const u = document.querySelector('#myShipUse'), cu = getComputedStyle(u);
      return {on: s.checked, edge: c.borderTopColor, knob: k.backgroundColor, label: l.color, anim: getComputedStyle(s, '::before').animationName, use: [cu.borderTopColor, cu.animationName]}; }"""
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
      return [[...b.children].filter(x => x.tagName === 'P').length, b.querySelectorAll(':scope > p b').length, ds.length, ds.filter(d => d.open).length, b.innerText.split(/\\s+/).length - ((b.querySelector('.info-ex') || {}).innerText || '').split(/\\s+/).filter(Boolean).length, b.textContent]; }""")   # v2026.11.07.7: the "See an example" line is a control, not text to read
    pg.evaluate("() => { const s = document.querySelector('#intelPanel .it-head .info-body details.info-more summary'); if(s) s.click(); }"); pg.wait_for_timeout(100)
    op = pg.evaluate("() => [...document.querySelectorAll('#intelPanel .it-head .info-body details.info-more')].map(d => d.open)")
    check(inf[:4] == [3, 3, 8, 0] and inf[4] < 110 and op[0] and not any(op[1:]),
          f'How Intel works: 3 short paragraphs (each with a bold lead) and 8 folded headings (v2026.11.02.4: the map), closed ({inf[4]} words shown); one opens on a click {inf[:5]} {op}')
    check('slider' not in inf[5] and 'red row' not in inf[5], 'no "slider" or "red row" left in it')
    check(not errs, f'no page errors {errs[:3]}')
    ie = pg.evaluate("() => [it.err, it.note]")
    check(not ie[0], f'Intel shows no error of its own (it catches its reader\'s errors and shows them, APP-01; LESSON #139) {ie}')
    b.close()
'''
exec(compile(_src + _tail, 'intel_place_check.py', 'exec'), _ns)
print(f"FAILURES: {_ns['fails']}")
sys.exit(1 if _ns['fails'] else 0)
