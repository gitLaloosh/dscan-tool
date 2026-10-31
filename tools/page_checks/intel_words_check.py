"""Words in a report that real characters are also named; the ESS linked; ship names one letter off (v2026.10.31.4).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/intel_words_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner's reports: "Kill: <pilot> (<ship>) on <gate>" made "Kill" a pilot; "<sys> Gate Drag Bubbled Cormorrant Navy Fleet +9 Gate
is hot" and "<sys> proc tackled in the medium ark by the <group> rats" sent "DRAG", "Navy", "HOT", "Proc", "MediuM", "Rats" to the System
Analyzer as pilots; ""linked to ESS" is a warning to let people know that the hostile is linked to the system's ESS and about to rob
it. "linked" should not have been resolved as a pilot name." Runs intel_check.py's start (its made-up Chatlogs folder, ESI and system
names; you in 1DQ1-A) up to Intel turned on, with made-up characters named Kill, Linked, Navy, DRAG, HOT, Proc, MediuM and Rats (as real
ones are), then made-up lines:
  * "MO-GZ5 linked to ess 223m": no pilot, "223m" never looked up; a sighting: the Feed's chip "ESS linked"; Near You's row says
    "hostile" (no count was given) and is tagged "ESS linked";
  * "Y-OMTZ Gate Drag Bubbled Cormorrant Navy Fleet +9 Gate is hot": no pilot; the ship read as the Cormorant Navy Issue; +9;
  * "D-W7F0 proc tackled in the medium ark by the rats": no pilot, and "the medium ark" is an ore site, not the jump freighter; "T5ZI-S Kill: Marrek (Caracal Navy Issue)": Marrek only, in his
    Caracal Navy Issue;
  * a single word typed in other capitals than the name ("8WA-Z6 marrek") is not that pilot; the same word dragged in ("8WA-Z6
    Navy*", "QX-LIJ linked*") is; in its own capitals ("N-8YET Marrek") it is;
  * "Navy Cormorant": the Cormorant Navy Issue by its short name;
  * a dragged-in name ending in a report word ("Marrek Kill*") is that whole name, not Marrek;
  * no page errors.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, 'intel_check.py'), encoding='utf-8').read()
_src = _src[:_src.index('    jumps = pg.evaluate("(names) => Object.fromEntries')]
_src = _src.replace("os.path.dirname(os.path.abspath(__file__))", repr(HERE), 1)
_ns = {'__file__': os.path.join(HERE, 'intel_check.py'), '__name__': 'intel_check_prefix'}
_tail = r'''
    ONE_WORD.update({'Kill': 96000021, 'Linked': 96000022, 'Navy': 96000023, 'DRAG': 96000024, 'HOT': 96000025, 'Proc': 96000026, 'MediuM': 96000027, 'Rats': 96000028, 'Marrek Kill': 96000029})
    lines = ['MO-GZ5 linked to ess 223m', 'Y-OMTZ Gate Drag Bubbled Cormorrant Navy Fleet +9 Gate is hot', 'D-W7F0 proc tackled in the medium ark by the rats',
             'T5ZI-S Kill: Marrek (Caracal Navy Issue)', '8WA-Z6 marrek', '8WA-Z6 Navy*', 'QX-LIJ linked*', 'N-8YET Marrek', '4K-TRB Navy Cormorant', '8WA-Z6 Marrek Kill*']
    t0 = time.time() - 30
    W(pg, F_INTEL, ''.join(line(t0 + i, 'Scout Alt', m) for i, m in enumerate(lines))); tick(pg, 3500)
    R = pg.evaluate("""(lines) => Object.fromEntries(lines.map(l => { const e = it.feed.find(x => x.raw === l); return [l, e ? {
      pilots: e.pilots.map(x => x.name), ships: e.p.ships.map(s => [s.name, s.n]), kw: [...e.p.kw], extra: e.p.extra, pairs: [...e.pairs.values()].map(v => v.name)} : null]; }))""", lines)
    def got(l): return R.get(l) or {'pilots': None, 'ships': [], 'kw': [], 'extra': 0, 'pairs': []}
    g = got('MO-GZ5 linked to ess 223m')
    near = pg.evaluate("""() => { const r = [...document.querySelectorAll('#itNearList .it-nb')].find(x => x.querySelector('.sys').textContent === 'MO-GZ5');
      const f = [...document.querySelectorAll('#itFeedList .it-fd')].find(x => (x.querySelector('.raw') || {}).textContent === 'MO-GZ5 linked to ess 223m');
      return [r ? [(r.querySelector('.it-ess') || {}).textContent || '', r.querySelector('.st b').textContent] : null, f ? [...f.querySelectorAll('.it-chip.kw')].map(c => c.textContent) : null]; }""")
    check(g['pilots'] == [] and 'ESS linked' in g['kw'] and not {'223m', 'ess', 'linked to', 'to ess'} & IDS_ASKED and near[0] == ['ESS linked', 'hostile'] and 'ESS linked' in (near[1] or []),
          f"'linked to ess 223m': no pilot, '223m' never looked up; a sighting; the Feed says 'ESS linked', Near You's row is tagged {g} {near} {sorted({'linked', '223m'} & IDS_ASKED)}")
    g = got('Y-OMTZ Gate Drag Bubbled Cormorrant Navy Fleet +9 Gate is hot')
    check(g['pilots'] == [] and g['ships'] == [['Cormorant Navy Issue', 1]] and g['extra'] == 9 and not {'drag', 'hot', 'drag bubbled', 'is hot'} & IDS_ASKED,
          f'"Gate Drag Bubbled Cormorrant Navy Fleet +9 Gate is hot": no pilot, the Cormorant Navy Issue one letter off, +9 {g}')
    g = got('D-W7F0 proc tackled in the medium ark by the rats'); k = got('T5ZI-S Kill: Marrek (Caracal Navy Issue)')
    # "kill" is asked for the dragged-in "Marrek Kill*"; a character named Kill exists, so "Marrek only" shows "Kill:" wasn't read as one
    check(g['pilots'] == [] and g['ships'] == [] and k['pilots'] == ['Marrek'] and k['pairs'] == ['Caracal Navy Issue'] and not {'proc', 'medium', 'rats'} & IDS_ASKED,
          f'"proc tackled in the medium ark by the rats": no pilot, and "the medium ark" an ore site, not the Ark; "Kill: Marrek (Caracal Navy Issue)": Marrek only, in his ship {g} {k}')
    c = [got(l)['pilots'] for l in ('8WA-Z6 marrek', '8WA-Z6 Navy*', 'QX-LIJ linked*', 'N-8YET Marrek')]
    check(c == [[], ['Navy'], ['Linked'], ['Marrek']], f"one word typed in other capitals is not the pilot; dragged in, or in the name's own capitals, it is {c}")
    g = got('4K-TRB Navy Cormorant')
    check(g['ships'] == [['Cormorant Navy Issue', 1]] and g['pilots'] == [], f'"Navy Cormorant": the Cormorant Navy Issue by its short name {g}')
    g = got('8WA-Z6 Marrek Kill*')
    check(g['pilots'] == ['Marrek Kill'], f'a dragged-in name ending in a report word ("Marrek Kill*") is that whole name {g}')
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
'''
exec(compile(_src + _tail, 'intel_words_check.py', 'exec'), _ns)
print(f"FAILURES: {_ns['fails']}")
sys.exit(1 if _ns['fails'] else 0)
