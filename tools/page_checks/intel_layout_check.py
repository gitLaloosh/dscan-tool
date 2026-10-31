"""Near You and the Feed laid out as the owner settled them on 2026-10-30 (v2026.10.30.1; mockup
Claude outputs/near_you_kills_mockup.html), and the tabs in the order of use.

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/intel_layout_check.py [index.html]   -> 'FAILURES: N' (must be 0)

Runs intel_kills_check.py's start (made-up logs and kills, R2Z2 and ESI mocked) up to its live kills, then:
  * the page opened on Intel; the tabs Intel, System Analyzer, Pilot Analyzer, Fit Analyzer;
  * Near You, layout D (v2026.10.31.6; the owner's layout, Project doc roadmap/near-you-layout-d.md), with the analyze icon in its
    own column after the jumps (v2026.10.31.7, the owner's idea): line 1 the jump count (a column wide enough for "88 Jumps" and the
    In system callout), the analyze icon, the system in a column as wide as the widest system name in the table (measured in the font
    the browser draws), the tags, the time at the right (lined up); the icon right against its system; line 2 the kill badges under the system, only when there are kills; then the toggle
    under the jumps and the word and names from under the system; no Assess column; nothing overlaps; the left edge amber (the "N near"
    alert's colour) only within the alert range, no background on any row; a gang of 300 named in a report: "300 hostile", the
    names cut to 3 lines with "+N more";
  * a row opened: the reports behind it with who sent them and the line as typed, no channel name; several open at once;
  * the Feed, to match: line 1 the jump count, the analyze icon on reports (v2026.10.31.7), the system, the notes and tags, the time
    at the right (lined up); the system names the same distance from each list's left edge in both lists; no REPORT label, a
    kill's label among the tags, its fleet size the dossier's; the lines below starting under the system name; no background on
    kill rows, the amber edge within the alert range;
  * v2026.10.31.2: Near You lists systems up to 5 jumps past the alert range and no farther, and its line says so;
  * a busy row (a camp, the ESS, a bubble, kills and pilots of all three standings) at every width where the Intel card is split
    in two (905-1700 px), with this table's system column and with one 160 px wide (as wide as the longest real names: the made-up
    names here are short, which is how v2026.10.31.6's icon floating past the column went unseen): nothing overlaps or leaves a row,
    line 1 one line, the word on one line, the icon right against its system, the kill badges and the names under the system;
  * 390 px: nothing off the page; Near You's toggle and analyze icon at least 32 px, the icon under the jumps beside the toggle
    (v2026.10.31.7: what was reported keeps its width), in the Feed too; the tags on their own line under the system in both lists;
    the busy row whole;
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
    # ---- Near You: layout D (v2026.10.31.6; the owner's layout, Project doc roadmap/near-you-layout-d.md) ----
    GEO = """(sel) => { const R = (e) => e && e.getBoundingClientRect(); const rows = [...document.querySelectorAll('#itNearList .it-nb')];
      return rows.map(r => { const q = (s) => R(r.querySelector(':scope > ' + s)), j = q('.j'), s = q('.sys'), an = q('.it-an') || q('.it-an-none'), tg = q('.tg'), a = q('.age'), kb = q('.kb'), rt = q('.it-rawt'), wl = q('.wl'), cs = getComputedStyle(r);
        const b = r.querySelector('.wl .st b'), rr = R(r);
        const kids = [...r.children].filter(c => c.getBoundingClientRect().width > 0).map(R);
        let overlap = 0; for(let x = 0; x < kids.length; x++) for(let y = x + 1; y < kids.length; y++){ const A = kids[x], B = kids[y]; if(A.left < B.right - 1 && B.left < A.right - 1 && A.top < B.bottom - 1 && B.top < A.bottom - 1) overlap++; }
        const cy = (e) => e.top + e.height / 2;
        return {sys: r.querySelector('.sys').textContent, jx: j.left, jr: j.right, jtxt: r.querySelector('.j').textContent, jw: parseFloat(cs.gridTemplateColumns.split(' ')[0]), anr: an.right, gap: parseFloat(cs.columnGap), sx: s.left, sw: parseFloat(cs.gridTemplateColumns.split(' ')[2]), sb: s.bottom, l1b: Math.max(j.bottom, s.bottom, an.bottom, tg.height ? tg.bottom : 0, a.bottom), rg: parseFloat(cs.rowGap), ax: an.left, tgx: tg.left, ar: Math.round(a.right),
          line1: Math.max(...[j, s, a].map(e => Math.abs(cy(e) - cy(s)))), anc: r.querySelector(':scope > .it-an') ? Math.abs(cy(an) - cy(s)) : 0,
          kb: kb ? [kb.top, kb.left, kb.bottom] : null, rt: [rt.left, rt.top], wl: [wl.left, wl.top], word1: b ? b.getBoundingClientRect().height <= 20 : true,
          inside: kids.every(k => k.left >= rr.left - 1 && k.right <= rr.right + 1), overlap, alert: r.classList.contains('alert'), edge: cs.boxShadow, bg: cs.backgroundColor,
          an: (r.querySelector(':scope > .it-an') || {}).title || '', assess: !!r.querySelector('.it-assess')}; }); }"""
    G = pg.evaluate("""() => { const c = document.createElement('canvas').getContext('2d'); c.font = getComputedStyle(document.querySelector('#itNearList .it-nb .sys')).font;
      let widest = 0, wn = ''; for(const n of it.names.byId.values()){ const w = c.measureText(n).width; if(w > widest){ widest = w; wn = n; } } return {widest, wn}; }""")
    rows = pg.evaluate(GEO); r0 = rows[0]
    chk(all(r['jx'] < r['ax'] < r['sx'] < r['tgx'] for r in rows), f'Near You line 1: the jump count, the analyze icon, the system, the tags {[(r["sys"], round(r["jx"]), round(r["ax"]), round(r["sx"]), round(r["tgx"])) for r in rows][:3]}')
    chk(all(abs(r['sx'] - r['anr'] - r['gap']) < 1 for r in rows if r['an']), f'the icon right against its system (one column gap) {[(r["sys"], round(r["sx"] - r["anr"], 1)) for r in rows if r["an"]]}')
    JW = pg.evaluate("""() => { const j = document.querySelector('#itNearList .it-nb .j'), w = []; for(const t of ['88 Jumps', '<span class="it-here">In system</span>']){
      const x = j.cloneNode(false); x.innerHTML = t; x.style.cssText = 'position:absolute; visibility:hidden; display:inline-block'; j.parentNode.appendChild(x); w.push(x.getBoundingClientRect().width); x.remove(); } return w; }""")
    chk(all(r['jw'] >= max(JW) - 0.5 and r['jr'] <= r['ax'] + 0.5 for r in rows), f'the jump column fits "88 Jumps" and In system ({[round(x, 1) for x in JW]} px): {rows[0]["jw"]} px; no jump count runs into the icon {[(r["jtxt"], round(r["jr"]), round(r["ax"])) for r in rows][:4]}')
    chk(all(r['line1'] <= 4 and r['anc'] <= 4 for r in rows) and len({r['ar'] for r in rows}) == 1, f'... and the time at the right, all on one line, the times lined up {[(r["sys"], round(r["line1"], 1), r["ar"]) for r in rows]}')
    chk(all(abs(r['sw'] - r0['sw']) < 0.5 for r in rows) and r0['sw'] >= G['widest'] - 0.5, f'the system column as wide as the widest system name in the table ({G["wn"]}, {G["widest"]:.1f} px): {r0["sw"]:.1f} px on every row')
    chk(len({round(r['ax']) for r in rows}) == 1 and len({round(r['tgx']) for r in rows}) == 1, f'the icons and the tags start at the same place on every row {sorted({round(r["ax"]) for r in rows})} {sorted({round(r["tgx"]) for r in rows})}')
    kr = [r for r in rows if r['kb']]
    chk(kr and all(r['kb'][0] >= r['sb'] - 1 and abs(r['kb'][1] - r['sx']) < 1.5 and r['wl'][1] >= r['kb'][2] - 1 for r in kr) and not [r for r in rows if not r['kb'] and r['wl'][1] - r['l1b'] > r['rg'] + 1.5],
          f'the kill badges on line 2 under the system name, only when there are kills (rows without them: no empty line) {[(r["sys"], r["kb"] and [round(x) for x in r["kb"]], round(r["sb"]), [round(x) for x in r["wl"]]) for r in rows]}')
    chk(all(abs(r['rt'][0] - r['jx']) < 2 and r['rt'][1] >= r['sb'] - 1 and abs(r['wl'][0] - r['sx']) < 1.5 for r in rows), f'the toggle under the jump count, then the word and the names from under the system {[(r["sys"], [round(x) for x in r["rt"]], [round(x) for x in r["wl"]]) for r in rows][:3]}')
    chk(not any(r['assess'] for r in rows) and all(r['an'].startswith('Analyze ') for r in rows if r['an']) and any(r['an'] for r in rows), f'no Assess column; the analyze icon instead {[(r["sys"], r["an"][:30]) for r in rows]}')
    chk(all(r['overlap'] == 0 and r['inside'] for r in rows), f'nothing overlaps or sticks out of its row {[(r["sys"], r["overlap"], r["inside"]) for r in rows if r["overlap"] or not r["inside"]]}')
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
      const r = [...document.querySelectorAll('#itNearList .it-nb')].find(x => x.querySelector('.sys').textContent === 'D-W7F0'), w = r.querySelector('.who'), l = r.querySelector('.wl');
      return [r.querySelector('.st b').textContent, Math.round(l.getBoundingClientRect().height), parseFloat(getComputedStyle(l).lineHeight), w.textContent.slice(-40), (w.querySelector('.more') || {}).textContent]; }""")
    chk(cap[0] == '301 neutral' or cap[0].endswith(' hostile') and int(cap[0].split()[0]) >= 300, f'a gang of 300 in one report: the word keeps the count ({cap[0]})')
    chk(cap[1] <= cap[2] * 3 + 1 and cap[4] and cap[4].startswith('+') and cap[4].endswith(' more'), f'... the names stop at 3 lines ({cap[1]} px, line {cap[2]} px) with "{cap[4]}" ({cap[3]!r})')
    # opening rows: several at once; who sent each report and the line as typed; no channel name
    pg.click('#itNearList .it-nb:nth-child(1) [data-it-nbo]'); pg.wait_for_timeout(200)
    pg.evaluate("() => { const b = [...document.querySelectorAll('#itNearList [data-it-nbo]')].find(x => x.getAttribute('aria-expanded') === 'false'); b.click(); }"); pg.wait_for_timeout(200)
    op = pg.evaluate("() => [[...document.querySelectorAll('#itNearList .it-nbx')].length, [...document.querySelectorAll('#itNearList [data-it-nbo][aria-expanded=true]')].length, [...document.querySelectorAll('#itNearList .it-nbx .nbx-i')].map(x => x.textContent.replace(/\\s+/g, ' ').trim()).slice(0, 4), document.querySelector('#intelPanel').innerText.includes('region.intel')]")
    chk(op[0] == 2 and op[1] == 2 and op[2] and not op[3], f'two rows open at once, each listing what it is built from; no channel name {op}')
    # ---- the Feed, to match (v2026.10.31.6) ----
    F = pg.evaluate("""() => [...document.querySelectorAll('#itFeedList .it-fd')].slice(0, 10).map(r => { const R = (s) => { const e = r.querySelector(s); return e && e.getBoundingClientRect(); };
      const fj = R('.fj'), sy = R('.it-chip.sys'), tg = R('.ftg'), ag = R('.it-age'), ch = R(':scope > .it-chips'), cs = getComputedStyle(r), cy = (e) => e.top + e.height / 2;
      const ty = r.querySelector('.it-ty');
      const an = R('.it-an');
      return {kill: r.classList.contains('kill'), inr: r.classList.contains('inr'), fjx: fj.left, anx: an ? an.left : null, syx: sy.left, tgx: tg.left, agr: Math.round(ag.right), line1: Math.abs(cy(ag) - cy(sy)), chx: ch ? ch.left : null,
        report: [...r.querySelectorAll('.it-ty')].some(x => /report/i.test(x.textContent)), label: ty ? !!ty.closest('.ftg') : null, fsz: (r.querySelector('.fsz') || {}).title || '',
        bg: cs.backgroundColor, edge: cs.boxShadow}; })""")
    chk(all(f['fjx'] < f['syx'] < f['tgx'] and f['line1'] <= 4 and (f['anx'] is None or f['fjx'] < f['anx'] < f['syx']) for f in F) and len({f['agr'] for f in F}) == 1 and any(f['anx'] for f in F),
        f'the Feed line 1: jumps, the analyze icon (reports), the system, the notes and tags, the time at the right (lined up) {[(round(f["fjx"]), f["anx"] and round(f["anx"]), round(f["syx"]), round(f["tgx"]), f["agr"]) for f in F][:3]}')
    XL = pg.evaluate("() => ['#itNearList .it-nb .sys', '#itFeedList .it-fd .it-chip.sys', '#itNearList .it-nb .it-an', '#itFeedList .it-fd .it-an'].map(q => { const e = document.querySelector(q), l = e.closest('#itNearList, #itFeedList'); return e.getBoundingClientRect().left - l.getBoundingClientRect().left; })")
    chk(abs(XL[0] - XL[1]) < 1 and abs(XL[2] - XL[3]) < 1 and len({round(f['syx']) for f in F}) == 1, f'the system names and the icons the same distance from each list\'s left edge in Near You and the Feed, every Feed row alike {[round(x, 1) for x in XL]}')
    chk(all(f['chx'] is None or abs(f['chx'] - f['syx']) < 2 for f in F), f'the lines below start under the system name {[(round(f["syx"]), f["chx"] and round(f["chx"])) for f in F][:3]}')
    chk(not any(f['report'] for f in F) and all(f['label'] for f in F if f['kill']) and all(re.match(r'^\d+ players? on this kill: (solo|small gang|fleet)$', f['fsz']) for f in F if f['kill']),
        f'no REPORT label; a kill\'s label among the tags; its fleet size (the dossier\'s) {[(f["kill"], f["report"], f["label"], f["fsz"]) for f in F]}')
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
    # ---- a busy row (Project doc: "Add a busy row to the layout check"): a camp on a gate, the ESS, a bubble, kills of all three standings and
    # pilots of all three standings, at every width where the Intel card is split in two (905-1700 px), with this table's system column and
    # with one 160 px wide, and on a phone: nothing overlaps or leaves its row, line 1 stays one line, the word never wraps ----
    pg.evaluate("""() => { const sys = it.names.byLower.get('n-8yet'), now = Date.now(), gate = itNeighbours(sys)[0];
      const P = (id, side) => ({id, name: 'Busy Pilot ' + id, side, ship: null});
      itNearAdd({id: 997001, kind: 'seen', t: now, who: 'Scout Alt', raw: 'busy', chan: '', history: true, pilots: [P(96500001, 'h'), P(96500002, 'n'), P(96500003, 'f'), P(96500004, 'h')], pairs: new Map(),
        p: {sys: [{id: sys, at: 0, k: 1}], ships: [{id: 22456, name: 'Sabre', n: 2}, {id: 587, name: 'Rifter', n: 1}], kw: new Set(['ESS']), extra: 3, W: [], used: [], ess: true, gate, camp: true}}, sys);
      const st = it.near.get(sys); st.bub.push({t: now, who: 'Scout Alt'}); for(const v of ['f', 'h', 'n']) st.kills.push({t: now, id: 990000 + v.charCodeAt(0), v});
      itRenderLists(); }""")
    BUSY = """() => { const r = [...document.querySelectorAll('#itNearList .it-nb')].find(x => x.querySelector('.sys').textContent === 'N-8YET'); const R = (e) => e.getBoundingClientRect(), rr = R(r);
      const kids = [...r.children].filter(c => R(c).width > 0).map(R); let overlap = 0;
      for(let x = 0; x < kids.length; x++) for(let y = x + 1; y < kids.length; y++){ const A = kids[x], B = kids[y]; if(A.left < B.right - 1 && B.left < A.right - 1 && A.top < B.bottom - 1 && B.top < A.bottom - 1) overlap++; }
      const s = R(r.querySelector('.sys')), a = R(r.querySelector('.age')), cy = (e) => e.top + e.height / 2, an = R(r.querySelector('.it-an')), kb = R(r.querySelector('.kb')), wl = R(r.querySelector('.wl')), gap = parseFloat(getComputedStyle(r).columnGap);
      return [r.querySelectorAll('.tg .it-gtag, .tg .it-ess').length, r.querySelectorAll('.kb .it-kl').length, overlap, kids.every(k => k.left >= rr.left - 1 && k.right <= rr.right + 1),
        Math.abs(cy(a) - cy(s)) <= 4, R(r.querySelector('.wl .st b')).height <= 20, document.documentElement.scrollWidth <= innerWidth,
        innerWidth < 600 || (Math.abs(s.left - an.right - gap) < 1 && Math.abs(kb.left - s.left) < 1.5 && Math.abs(wl.left - s.left) < 1.5)]; }"""
    pg.evaluate("() => { const o = itSysWidths; window.__sysw = ''; itSysWidths = (el) => { o(el); if(window.__sysw) el.style.setProperty('--it-sys-w', window.__sysw); }; }")
    NW = []
    for sysw in ['', '160px']:
        pg.evaluate("(v) => { window.__sysw = v; }", sysw)
        for w in [905, 1000, 1100, 1200, 1290, 1340, 1440, 1700]:
            pg.set_viewport_size({'width': w, 'height': 1000}); pg.wait_for_timeout(450); pg.evaluate("() => itRenderLists()"); pg.wait_for_timeout(150)
            NW.append([sysw or 'table', w] + pg.evaluate(BUSY) + [all(r['overlap'] == 0 and r['inside'] and r['word1'] for r in pg.evaluate(GEO))])
    pg.evaluate("() => { window.__sysw = ''; }")
    chk(NW[0][2] >= 3 and NW[0][3] == 3, f'the busy row has the camp, ESS and bubble tags and all three kill badges {NW[0][:4]}')
    chk(all(n[4] == 0 and n[5] and n[6] and n[7] and n[8] and n[9] and n[10] for n in NW), f'at every split width, both system columns: nothing overlaps or leaves a row, line 1 one line, the word on one line, nothing off the page, the icon against its system, the badges and names under the system {[n for n in NW if not (n[4] == 0 and n[5] and n[6] and n[7] and n[8] and n[9] and n[10])]}')
    pg.set_viewport_size({'width': 1440, 'height': 1000}); pg.wait_for_timeout(450)
    # ---- 390 px ----
    pg.set_viewport_size({'width': 390, 'height': 900}); pg.wait_for_timeout(600); pg.evaluate("() => itRenderLists()"); pg.wait_for_timeout(200)
    ph = pg.evaluate("""() => { const r = [...document.querySelectorAll('#itNearList .it-nb')].find(x => x.querySelector('.sys').textContent === 'N-8YET'), R = (e) => e.getBoundingClientRect();
      const tg = R(r.querySelector('[data-it-nbo]')), an = R(r.querySelector('.it-an')), sy = R(r.querySelector('.sys')), tags = R(r.querySelector('.tg')), wl = R(r.querySelector('.wl')), j = R(r.querySelector('.j'));
      const f = [...document.querySelectorAll('#itFeedList .it-fd')].find(x => x.querySelector('.ftg').children.length), fs = R(f.querySelector('.it-chip.sys')), ft = R(f.querySelector('.ftg'));
      const g = [...document.querySelectorAll('#itFeedList .it-fd')].find(x => x.querySelector('.it-an') && x.querySelector('.it-rawt')), ga = R(g.querySelector('.it-an')), gt = R(g.querySelector('.it-rawt')), gs = R(g.querySelector('.it-chip.sys')), gc = g.querySelector(':scope > .it-chips');
      const beside = (a, t, s, x0) => a.left >= t.right - 0.5 && a.right <= s.left + 0.5 && Math.abs((a.top + a.bottom) / 2 - (t.top + t.bottom) / 2) <= 2 && a.top >= s.bottom - 1 && a.left >= x0 - 0.5;
      return [document.documentElement.scrollWidth, Math.round(tg.height), Math.round(an.height), tags.top >= sy.bottom - 2, ft.top >= fs.bottom - 2,
        beside(an, tg, sy, j.left) && Math.abs(wl.left - sy.left) < 1.5, beside(ga, gt, gs, R(g.querySelector('.fj')).left) && (!gc || Math.abs(R(gc).left - gs.left) < 1.5)]; }""")
    b390 = pg.evaluate(BUSY)
    chk(ph[0] <= 390 and ph[1] >= 32 and ph[2] >= 32 and ph[3] and ph[4] and b390[2] == 0 and b390[3], f'390 px: nothing off the page, the toggle and the analyze icon at least 32 px, the tags on their own line under the system (Near You and the Feed), the busy row whole {ph} {b390}')
    chk(ph[5] and ph[6], f'390 px: the analyze icon under the jumps beside the toggle, what was reported starting under the system (Near You, the Feed) {ph[5:]}')
    pg.set_viewport_size({'width': 1440, 'height': 1000})
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
'''
exec(compile(_src + _tail, 'intel_layout_check.py', 'exec'), _ns)
print(f"FAILURES: {_ns['NS']['fails']}")
sys.exit(1 if _ns['NS']['fails'] else 0)
