"""Near You and the Feed laid out as the owner settled them on 2026-10-30 (v2026.10.30.1; mockup
Claude outputs/near_you_kills_mockup.html), and the tabs in the order of use.

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/intel_layout_check.py [index.html]   -> 'FAILURES: N' (must be 0)

Runs intel_kills_check.py's start (made-up logs and kills, R2Z2 and ESI mocked) up to its live kills, then:
  * the page opened on Intel; the tabs Intel, System Analyzer, Pilot Analyzer, Fit Analyzer;
  * Near You: the jump count first, then the system in a column as wide as the widest system name in the table (measured in the
    font the browser draws); the time and the kill badges at the right with the times lined up, then the toggle, Assess last;
    everything on the first line; the left edge amber (the "N near" alert's colour, now amber too) only within the alert range, no
    background on any row; a gang of 300 named in a report: "300 hostile", the names cut to 3 lines with "+N more";
  * a row opened: the reports behind it with who sent them and the line as typed, no channel name; several open at once;
  * the Feed: the jump count first, the time then the label at the right edge (the labels' right edges lined up), the lines below
    starting under the system name, no background on kill rows, the amber edge within the alert range;
  * v2026.10.31.2: Near You lists systems up to 5 jumps past the alert range and no farther, and its line says so;
  * v2026.10.31.1: at every width where the Intel card is split in two (905-1700 px), with this table's system column and with
    one 160 px wide: Near You's word on one line within its column, on the system's line when there's room, else under it;
    the times lined up either way;
  * 390 px: nothing off the page; Near You's toggle and Assess at least 40 px; the Feed's label under the system line;
  * no page errors.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, 'intel_kills_check.py'), encoding='utf-8').read()
_src = _src[:_src.index("    # ---- v2026.10.29.3: the Feed's kill range")]
_src = _src.replace("os.path.dirname(os.path.abspath(__file__))", repr(HERE), 1)
_ns = {'__file__': os.path.join(HERE, 'intel_kills_check.py'), '__name__': 'intel_kills_prefix'}
_tail = r'''
    L = []
    def chk(ok, msg): L.append((ok, msg)); check(ok, msg)
    # ---- the tabs ----
    tabs = pg.evaluate("() => [[...document.querySelectorAll('.tabs .tab-btn')].filter(b => b.offsetParent).map(b => b.textContent.trim()), ['tabIntel','tabDscan','tabPilot','tabFit'].filter(id => document.getElementById(id).style.display !== 'none')]")
    chk(tabs[0] == ['Intel', 'System Analyzer', 'Pilot Analyzer', 'Fit Analyzer'], f'the tabs in the order of use (the owner: "intel > system > pilot > fit") {tabs[0]}')
    pg.evaluate("() => { it.set.range = 3; itRenderLists(); }"); pg.wait_for_timeout(300)
    # ---- Near You ----
    G = pg.evaluate("""() => { const rows = [...document.querySelectorAll('#itNearList .it-nb')]; const R = (e) => e && e.getBoundingClientRect();
      const font = getComputedStyle(rows[0].querySelector('.sys')).font, c = document.createElement('canvas').getContext('2d'); c.font = font;
      let widest = 0, wn = ''; for(const n of it.names.byId.values()){ const w = c.measureText(n).width; if(w > widest){ widest = w; wn = n; } }
      return {widest, wn, rows: rows.map(r => { const j = R(r.querySelector('.j')), s = R(r.querySelector('.sys')), st = R(r.querySelector('.st')), a = R(r.querySelector('.age')), kb = r.querySelector('.kb'), tg = R(r.querySelector('[data-it-nbo]')), as = r.querySelector('.it-assess');
        const cs = getComputedStyle(r);
        return {sys: r.querySelector('.sys').textContent, jx: j.left, sx: s.left, sw: s.width, stx: st.left, top: [j.top, s.top, st.top, a.top].map(Math.round), ar: a.right, kbr: kb.getBoundingClientRect().right, kbn: kb.children.length,
          tgx: tg.left, asx: as ? as.getBoundingClientRect().left : null, alert: r.classList.contains('alert'), edge: cs.boxShadow, bg: cs.backgroundColor}; })}; }""")
    rows = G['rows']; r0 = rows[0]
    chk(all(r['jx'] < r['sx'] < r['stx'] for r in rows), f'Near You: the jump count first, then the system, then the word {[(r["sys"], round(r["jx"]), round(r["sx"]), round(r["stx"])) for r in rows][:3]}')
    chk(all(abs(r['sw'] - r0['sw']) < 0.5 for r in rows) and r0['sw'] >= G['widest'] - 0.5, f'the system column as wide as the widest system name in the table ({G["wn"]}, {G["widest"]:.1f} px): {r0["sw"]:.1f} px on every row')
    chk(len({round(r['ar']) for r in rows}) == 1 and all(r['tgx'] > r['kbr'] - 1 and (r['asx'] is None or r['asx'] > r['tgx']) for r in rows), f'the times lined up, then the kill badges, the toggle, Assess last {[(round(r["ar"]), round(r["kbr"]), round(r["tgx"]), r["asx"] and round(r["asx"])) for r in rows][:3]}')
    chk(all(max(r['top']) - min(r['top']) <= 3 for r in rows), f'jumps, system, word and time on the first line {[r["top"] for r in rows][:3]}')
    amber = 'rgb(217, 154, 60)'
    chk(all((amber in r['edge']) == r['alert'] for r in rows) and any(r['alert'] for r in rows) and len({r['bg'] for r in rows}) == 1,
        f'the amber edge only within the alert range, the same quiet background on every row {[(r["sys"], r["alert"], r["edge"][:22]) for r in rows]} {set(r["bg"] for r in rows)}')
    pill = pg.evaluate("() => { const p = document.querySelector('#intelNearN'); return [p.textContent, getComputedStyle(p).backgroundColor]; }")
    chk(pill[1] == amber, f'the "N near" alert in the same amber {pill}')
    # a gang of 300 named in one report: the word keeps the count, the names stop at 3 lines with "+N more"
    cap = pg.evaluate("""() => { const sys = it.names.byLower.get('d-w7f0'), now = Date.now();
      const pilots = Array.from({length: 300}, (_, i) => ({id: 97000000 + i, name: 'Gang Pilot ' + (i + 1), side: 'h', ship: null}));
      itNearAdd({id: 999999, kind: 'seen', t: now, who: 'Scout Alt', raw: 'D-W7F0 (300 names)', chan: '', history: true, pilots, pairs: new Map(),
        p: {sys: [{id: sys, at: 0, k: 1}], ships: [{id: 670, name: 'Capsule', n: 300}], kw: new Set(), extra: 0, W: [], used: []}}, sys);
      itRenderLists();
      const r = [...document.querySelectorAll('#itNearList .it-nb')].find(x => x.querySelector('.sys').textContent === 'D-W7F0'), w = r.querySelector('.who');
      return [r.querySelector('.st b').textContent, Math.round(w.getBoundingClientRect().height), parseFloat(getComputedStyle(w).lineHeight), w.textContent.slice(-40), (w.querySelector('.more') || {}).textContent]; }""")
    chk(cap[0] == '301 neutral' or cap[0].endswith(' hostile') and int(cap[0].split()[0]) >= 300, f'a gang of 300 in one report: the word keeps the count ({cap[0]})')
    chk(cap[1] <= cap[2] * 3 + 1 and cap[4] and cap[4].startswith('+') and cap[4].endswith(' more'), f'... the names stop at 3 lines ({cap[1]} px, line {cap[2]} px) with "{cap[4]}" ({cap[3]!r})')
    # opening rows: several at once; who sent each report and the line as typed; no channel name
    pg.click('#itNearList .it-nb:nth-child(1) [data-it-nbo]'); pg.wait_for_timeout(200)
    pg.evaluate("() => { const b = [...document.querySelectorAll('#itNearList [data-it-nbo]')].find(x => x.getAttribute('aria-expanded') === 'false'); b.click(); }"); pg.wait_for_timeout(200)
    op = pg.evaluate("() => [[...document.querySelectorAll('#itNearList .it-nbx')].length, [...document.querySelectorAll('#itNearList [data-it-nbo][aria-expanded=true]')].length, [...document.querySelectorAll('#itNearList .it-nbx .nbx-i')].map(x => x.textContent.replace(/\\s+/g, ' ').trim()).slice(0, 4), document.querySelector('#intelPanel').innerText.includes('region.intel')]")
    chk(op[0] == 2 and op[1] == 2 and op[2] and not op[3], f'two rows open at once, each listing what it is built from; no channel name {op}')
    # ---- the Feed ----
    F = pg.evaluate("""() => [...document.querySelectorAll('#itFeedList .it-fd')].slice(0, 8).map(r => { const R = (s) => { const e = r.querySelector(s); return e && e.getBoundingClientRect(); };
      const fj = R('.fj'), sy = R('.it-chip.sys'), ag = R('.it-age'), ty = R('.it-ty'), ch = R(':scope > .it-chips'), cs = getComputedStyle(r);
      return {kill: r.classList.contains('kill'), inr: r.classList.contains('inr'), fjx: fj.left, syx: sy.left, agr: ag.right, tyx: ty.left, tyr: ty.right, chx: ch ? ch.left : null, bg: cs.backgroundColor, edge: cs.boxShadow}; })""")
    chk(all(f['fjx'] < f['syx'] and f['agr'] <= f['tyx'] for f in F) and len({round(f['tyr']) for f in F}) == 1, f'the Feed: jumps first, the time then the label, the labels\' right edges lined up {[(round(f["fjx"]), round(f["syx"]), round(f["tyr"])) for f in F][:3]}')
    chk(all(f['chx'] is None or abs(f['chx'] - f['syx']) < 2 for f in F), f'the lines below start under the system name {[(round(f["syx"]), f["chx"] and round(f["chx"])) for f in F][:3]}')
    chk(len({f['bg'] for f in F}) == 1 and all((amber in f['edge']) == f['inr'] for f in F) and any(f['inr'] for f in F) and any(f['kill'] for f in F),
        f'no background on kill rows; the amber edge only within the alert range {set(f["bg"] for f in F)} {[(f["kill"], f["inr"]) for f in F]}')
    # ---- v2026.10.31.2 (the owner: "limit the range of what shows up in Near You to (alert range +5)") ----
    NR = pg.evaluate("""() => { const my = itMySys(), reach = it.set.range + 5, now = Date.now(); let at = null, past = null;
      for(const id of it.names.byId.keys()){ const j = itJumps(my, id); if(j === reach && !at) at = id; if(j !== null && j > reach && !past) past = id; if(at && past) break; }
      for(const [i, sys] of [[1, at], [2, past]]) itNearAdd({id: 998000 + i, kind: 'seen', t: now, who: 'Scout Alt', raw: 'far report', chan: '', history: true, pilots: [], pairs: new Map(),
        p: {sys: [{id: sys, at: 0, k: 1}], ships: [{id: 587, name: 'Rifter', n: 1}], kw: new Set(), extra: 0, W: [], used: []}}, sys);
      itRenderLists(); const shown = new Set([...document.querySelectorAll('#itNearList .it-nb')].map(r => Number(r.dataset.itSys)));
      return [reach, !!at, !!past, shown.has(at), shown.has(past), (document.querySelector('#intelPanel .it-h .ctx') || {}).textContent]; }""")
    chk(NR[1] and NR[2] and NR[3] and not NR[4] and f'within {NR[0]} jumps' in NR[5], f'Near You: up to 5 jumps past the alert range, no farther, and it says so {NR}')
    # ---- v2026.10.31.1: the word never squeezed (the owner: "text wrapping issue ... it's pretty annoying") ----
    # Every width where the Intel card is split in two, with this table's system column and with one as wide as a long real name:
    # the word on one line, never wider than its column; on the system's line when there is room, else under it (itNearFit).
    pg.evaluate("() => { const o = itSysWidths; window.__sysw = ''; itSysWidths = (el) => { o(el); if(window.__sysw) el.style.setProperty('--it-sys-w', window.__sysw); }; }")
    NW = []
    for sysw in ['', '160px']:
        pg.evaluate("(v) => { window.__sysw = v; }", sysw)
        for w in [905, 1000, 1100, 1200, 1290, 1340, 1440, 1700]:
            pg.set_viewport_size({'width': w, 'height': 1000}); pg.wait_for_timeout(450); pg.evaluate("() => itRenderLists()"); pg.wait_for_timeout(150)
            NW.append([sysw or 'table', w] + pg.evaluate("""() => { const l = document.querySelector('#itNearList');
              const R = [...l.querySelectorAll('.it-nb')].map(r => { const s = r.querySelector('.st'), b = s.firstElementChild.getBoundingClientRect(), y = r.querySelector('.sys').getBoundingClientRect();
                return {fits: b.width <= s.clientWidth + 0.5 && b.height <= 20, first: Math.abs(b.top - y.top) <= 3, ar: Math.round(r.querySelector('.age').getBoundingClientRect().right)}; });
              return [l.classList.contains('it-narrow'), R.every(x => x.fits), R.every(x => x.first), new Set(R.map(x => x.ar)).size === 1]; }"""))
    pg.evaluate("() => { window.__sysw = ''; }")
    chk(all(n[3] for n in NW), f'Near You at every split width: the word on one line, within its column {[n for n in NW if not n[3]]}')
    chk(all(n[5] for n in NW), f'... and the times lined up, stacked or not {[n for n in NW if not n[5]]}')
    chk(all(n[2] or n[4] for n in NW) and any(not n[2] for n in NW) and any(n[2] for n in NW) and not [n for n in NW if n[0] == 'table' and n[1] == 1700][0][2],
        f'... on the system\'s line when there is room, under it when not {[(n[0], n[1], "under" if n[2] else "line") for n in NW]}')
    pg.set_viewport_size({'width': 1440, 'height': 1000}); pg.wait_for_timeout(450)
    # ---- 390 px ----
    pg.set_viewport_size({'width': 390, 'height': 900}); pg.wait_for_timeout(600)
    ph = pg.evaluate("""() => { const r = document.querySelector('#itNearList .it-nb'), tg = r.querySelector('[data-it-nbo]').getBoundingClientRect(), as = r.querySelector('.it-assess'), f = document.querySelector('#itFeedList .it-fd');
      const sy = f.querySelector('.it-chip.sys').getBoundingClientRect(), ty = f.querySelector('.it-ty').getBoundingClientRect();
      return [document.documentElement.scrollWidth, Math.round(tg.height), as ? Math.round(as.getBoundingClientRect().height) : 40, ty.top >= sy.bottom - 2]; }""")
    chk(ph[0] <= 390 and ph[1] >= 40 and ph[2] >= 40 and ph[3], f'390 px: nothing off the page, the toggle and Assess 40 px, the Feed\'s label under the system line {ph}')
    pg.set_viewport_size({'width': 1440, 'height': 1000})
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
'''
exec(compile(_src + _tail, 'intel_layout_check.py', 'exec'), _ns)
print(f"FAILURES: {_ns['NS']['fails']}")
sys.exit(1 if _ns['NS']['fails'] else 0)
