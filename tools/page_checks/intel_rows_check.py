"""Near You and the Feed, layout D: what the rows say and do (v2026.10.31.6; Project doc roadmap/near-you-layout-d.md).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/intel_rows_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner walked layout D through one change at a time on the mockup (made-up data). Runs intel_check.py's start (its made-up
Chatlogs folder, ESI and system names; you in 1DQ1-A), then made-up lines and made-up kills. Checks:
  * the ESS: white "ESS" ("At the ESS: reported by ...") when someone is only at it, red "ESS" ("Linked to the ESS: reported by ...",
    nothing about robbing: the owner, "players likely wont" need it) when linked, only the red one when a system has both; the
    Feed's tags the same, no "ESS" / "ESS linked" chip;
  * a bubble that isn't a gate camp: a grey "Bubble" tag in both lists, no "bubble" chip;
  * a "clear": Near You's green Clear tag where the tags go and "reported clear by ..." under it; the Feed's green Clear tag; no
    REPORT label anywhere;
  * a system's name (Near You and the Feed): the Feed shows only that system (its name in the search box), pressed again
    everything; Near You never filtered (the owner: "we dont filter the Near You list though");
  * the analyze icon (radar rings, always the System Analyzer: the owner, "always system for now") sends the row to the System
    Analyzer; none on a row with nothing to analyze;
  * the Feed's kills (an NPC on most of them): the dossier's fleet size (the players on the killmail, NPCs left out: solo 1, small gang 2-10, fleet 11+, in
    the dossier's colours), none on a kill by NPCs only;
  * no page errors.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, 'intel_check.py'), encoding='utf-8').read()
_src = _src[:_src.index('    jumps = pg.evaluate("(names) => Object.fromEntries')]
_src = _src.replace("os.path.dirname(os.path.abspath(__file__))", repr(HERE), 1)
_ns = {'__file__': os.path.join(HERE, 'intel_check.py'), '__name__': 'intel_check_prefix'}
_tail = r'''
    H1, H2 = M.PILOTS[M.pick(98000003)][0], M.PILOTS[M.pick(98000004)][0]
    L1 = ['T5ZI-S 2 neuts at the ess', f'MO-GZ5 {H1}* linked to ess loki', '8WA-Z6 3 neuts at the ess', '8WA-Z6 2 reds linked to ess',
          'Y-OMTZ 2 reds bubbled at the sun', '4K-TRB clr', f'N-8YET {H2}* sabre']
    t0 = time.time() - 200
    W(pg, F_INTEL, ''.join(line(t0 + 10 * i, 'Scout Alt', m) for i, m in enumerate(L1))); tick(pg, 3500)
    # made-up kills: 1, 4 and 14 players on them, and one by NPCs only
    pg.evaluate("""([a, b]) => { const mk = (id, sys, ago, n) => ({km: {killmail_id: id, killmail_time: new Date(Date.now() - ago).toISOString(), solar_system_id: sys,
        victim: {character_id: 91000045, corporation_id: 98000013, ship_type_id: 587}, attackers: (n ? Array.from({length: n}, (_, i) => ({character_id: a + i, corporation_id: 98000004, ship_type_id: 22456, final_blow: i === 0, damage_done: 100})) : []).concat(n === 1 ? [] : [{corporation_id: 1000125, ship_type_id: 22456, final_blow: !n, damage_done: 100}])},
        z: {locationID: 40000001, totalValue: 1e7, attackerCount: n === 1 ? 1 : n + 1, hash: 'x', npc: !n}, t: Date.now() - ago});   // an NPC on each kill but the solo one: the fleet size counts players only
      itAddKill(mk(9101, 30004762, 90000, 1)); itAddKill(mk(9102, 30004762, 80000, 4)); itAddKill(mk(9103, 30004762, 70000, 14)); itAddKill(mk(9104, 30004762, 60000, 0)); itRenderLists(); }""", [91000000, 0])
    tick(pg, 800)
    NB = """() => Object.fromEntries([...document.querySelectorAll('#itNearList .it-nb')].map(r => [r.querySelector('.sys').textContent, {
      tags: [...r.querySelectorAll('.tg > *')].map(t => [t.className, t.textContent, t.title || '']), word: (r.querySelector('.wl .st b') || {}).textContent || '', who: r.querySelector('.who').textContent,
      an: !!r.querySelector('.it-an'), assess: !!r.querySelector('.it-assess')}]))"""
    FD = """() => [...document.querySelectorAll('#itFeedList .it-fd')].map(r => ({sys: (r.querySelector('.it-chip.sys') || {}).textContent, raw: ((r.querySelector('.it-raw .raw') || {}).textContent || ''), kill: r.classList.contains('kill'),
      tags: [...r.querySelectorAll('.ftg > *')].map(t => [t.className, t.textContent]), chips: [...r.querySelectorAll('.it-chip.kw')].map(c => c.textContent), report: [...r.querySelectorAll('.it-ty')].some(x => /report/i.test(x.textContent)),
      fsz: r.querySelector('.fsz') ? [r.querySelector('.fsz').title, r.querySelector('.fsz').textContent, getComputedStyle(r.querySelector('.fsz i')).backgroundColor] : null}))"""
    nb = pg.evaluate(NB); fd = pg.evaluate(FD)
    def row(raw): return next((x for x in fd if x['raw'] == raw), None)
    t, m, e = nb.get('T5ZI-S', {}).get('tags', []), nb.get('MO-GZ5', {}).get('tags', []), nb.get('8WA-Z6', {}).get('tags', [])
    check(t and t[0][1] == 'ESS' and 'it-essat' in t[0][0] and t[0][2].startswith('At the ESS: reported by Scout Alt')
          and m and m[0] == ['it-ess', 'ESS', m[0][2]] and m[0][2].startswith('Linked to the ESS: reported by Scout Alt') and 'rob' not in m[0][2].lower()
          and [x[1] for x in e] == ['ESS'] and e[0][0] == 'it-ess', f'the ESS: white when someone is at it, red when linked (no robbing in the hover), only the red one when a system has both {t} {m} {e}')
    a, c = row(L1[0]), row(L1[1])
    check(a and [x[1] for x in a['tags']] == ['ESS'] and 'it-essat' in a['tags'][0][0] and c and [x[1] for x in c['tags']] == ['ESS'] and c['tags'][0][0] == 'it-ess'
          and not {'ESS', 'ESS linked', 'ess'} & set(a['chips'] + c['chips']), f'the Feed: the same ESS tags, no ESS chip {a} {c}')
    y, r = nb.get('Y-OMTZ', {}), row(L1[4])
    check(y and [x[1] for x in y['tags']] == ['Bubble'] and r and [x[1] for x in r['tags']] == ['Bubble'] and 'bubble' not in r['chips'], f'a bubble (not a gate camp): a grey tag in both lists, no chip {y} {r}')
    k, r = nb.get('4K-TRB', {}), row(L1[5])
    check(k and [x[1] for x in k['tags']] == ['Clear'] and 'clr' in k['tags'][0][0] and k['word'] == '' and k['who'] == 'reported clear by Scout Alt'
          and r and [x[1] for x in r['tags']] == ['Clear'] and not any(x['report'] for x in fd), f'a clear: the green Clear tag where the tags go, who reported it under it; the Feed\'s too; no REPORT label {k} {r}')
    check(all(not v['assess'] for v in nb.values()) and nb['N-8YET']['an'] and not k['an'], f'the analyze icon on a row with someone to analyze, none on a clear row, no Assess {[(s, v["an"]) for s, v in nb.items()]}')
    ks = [x['fsz'] for x in fd if x['kill'] and x['fsz']]
    want = {'1 player on this kill: solo': ('1', 'rgb(79, 195, 217)'), '4 players on this kill: small gang': ('4', 'rgb(217, 154, 60)'), '14 players on this kill: fleet': ('14', 'rgb(166, 107, 217)')}
    got = {f[0]: (f[1].split('pilot')[0].strip(), f[2]) for f in ks}
    npc = [x for x in fd if x['kill'] and not x['fsz']]
    check(got == want and len(npc) == 1, f'the Feed\'s kills: the dossier\'s fleet size in its colours (solo, small gang, fleet); none by NPCs only {got} {len(npc)}')
    # a system's name: the Feed shows only it; again: everything; Near You never filtered
    n0, f0 = len(nb), len(fd)
    pg.evaluate("() => [...document.querySelectorAll('#itNearList .it-nb .sys')].find(b => b.textContent === '8WA-Z6').click()"); tick(pg, 300)
    S1 = pg.evaluate("""() => [document.querySelector('[data-it-q]').value, document.querySelectorAll('#itNearList .it-nb').length, [...document.querySelectorAll('#itFeedList .it-fd')].map(r => (r.querySelector('.it-chip.sys') || {}).textContent),
      [...document.querySelectorAll('#itNearList .it-nb .sys')].find(b => b.textContent === '8WA-Z6').getAttribute('aria-pressed')]""")
    pg.evaluate("() => [...document.querySelectorAll('#itFeedList .it-chip.sys')].find(b => b.textContent === '8WA-Z6').click()"); tick(pg, 300)
    S2 = pg.evaluate("() => [document.querySelector('[data-it-q]').value, document.querySelectorAll('#itFeedList .it-fd').length, document.querySelectorAll('#itNearList .it-nb').length]")
    check(S1[0] == '8WA-Z6' and S1[1] == n0 and S1[2] and set(S1[2]) == {'8WA-Z6'} and S1[3] == 'true' and S2 == ['', f0, n0],
          f'a system\'s name: the Feed shows only it (the search box says so), pressed again (here on the Feed) everything; Near You unchanged {S1} {S2} ({n0}, {f0})')
    # the analyze icon: the System Analyzer
    pg.evaluate("() => [...document.querySelectorAll('#itNearList .it-nb')].find(r => r.querySelector('.sys').textContent === 'N-8YET').querySelector('.it-an').click()"); tick(pg, 600)
    A = pg.evaluate("() => [document.getElementById('tabDscan').style.display !== 'none' && document.getElementById('tabIntel').style.display === 'none', !!sa.intel, (document.querySelector('#localInput') || {}).value || '']")
    check(A[0] and A[1] and A[2].strip(), f'the analyze icon sends the row to the System Analyzer {A[:2]} {A[2][:40]!r}')
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
'''
exec(compile(_src + _tail, 'intel_rows_check.py', 'exec'), _ns)
print(f"FAILURES: {_ns['fails']}")
sys.exit(1 if _ns['fails'] else 0)
