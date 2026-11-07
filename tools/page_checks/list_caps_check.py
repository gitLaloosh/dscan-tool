"""Long lists that pushed the page down (v2026.11.07.5, build queue 011; Project doc roadmap/list-caps-plan.md, mockup approved
from list_caps_mockup.html; the owner: "look good", "i like the amber", "sure" to the corporation-line bug).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/list_caps_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The real page with sa_mocks.py's stand-ins and a big made-up Local (80 neutral corporations; a hostile alliance of 40
corporations and 30 small hostile alliances), a 46-hull D-Scan and a dossier pilot with 42 Sabre kills (made-up names only).
Checks, at 1440 x 1000 unless said:
  1. the Hostile and Neutral columns: each no taller than the window (less 24 px) and scrolling inside, its heading sticky;
     "+N more groups below" counts the groups whose top is below the column's visible bottom (worked out here from the
     boxes), empty once scrolled to the end; the wheel at the column's end goes on to the page (LESSON #96); opening a group
     near the bottom scrolls the column so the group shows, the page doesn't move (LESSON #143: a JS click); a redraw
     (saRender) keeps each column's scroll and the focus (LESSON #119);
  2. the 40-corporation group: 8 corporation lines, "Show 32 more corporations" with their pilots counted here; pressed:
     all 40 and "Show fewer", kept through a redraw, the focus on the button; pressed again: 8;
  3. corporation lines with kills and losses of 1, 2 and 3 digits: every ▲ starts at one x, every ▼ at one x, every pilot
     count ends at one x (the BUG folded into 011);
  4. the scan rail: no taller than the window (less 24 px), scrolling inside; the hover card is outside the rail (in
     #saOut), fully on screen and on top (elementFromPoint at its corners) for a row at the rail's visible bottom; it follows
     its row when the rail scrolls, closes when the row scrolls out; the rail's scroll survives scanRailRender;
  5. the dossier: Sabre opened and "Show 10 more" pressed 3 times: 40 rows in a box exactly 10 rows + the heading tall
     (the 11th row starts at its edge), the heading inside it and sticky; after a press the first new row is just under the
     heading; the box's scroll survives pdRender; "Show fewer": 10 rows, no box;
  6. the amber buttons: .pdk-more, .sa-cmore and (v2026.11.07.6) a corporation's "+N more" pilots in the page's amber, the same compact size;
  7. at 760 px nothing is capped: the columns and the rail have no max-height, no "+N more" line;
  no page errors. v2026.11.07.4 fails (nothing capped, no fold, the card in the rail).
"""
import sys, os, re, json, time, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from playwright.sync_api import sync_playwright
import sa_mocks as M

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok

byname = M.byname
random.seed(11)
A = ['Ash', 'Bright', 'Cold', 'Dawn', 'Ember', 'Frost', 'Gilded', 'Hollow', 'Iron', 'Jade', 'Keen', 'Lone', 'Mist', 'Night', 'Onyx', 'Pale', 'Quiet', 'Rust', 'Salt', 'Thorn']
B = ['Anchor', 'Bastion', 'Circle', 'Drift', 'Echo', 'Forge', 'Grove', 'Harbor', 'Isle', 'Junction', 'Keep', 'Lantern', 'Mesa', 'Orchard', 'Point', 'Reach']
F = ['Ari', 'Bex', 'Cato', 'Dara', 'Eli', 'Fen', 'Gia', 'Hale', 'Ivo', 'Juno', 'Kip', 'Lyle', 'Maro', 'Nia', 'Oto', 'Pia', 'Rook', 'Sana', 'Teo', 'Uma', 'Vale', 'Wyn', 'Xan', 'Yara', 'Zed']
L = ['Aldane', 'Bricker', 'Coldwell', 'Dunmore', 'Easton', 'Fairlow', 'Greer', 'Hawke', 'Inglis', 'Jarrow', 'Kestrel', 'Larkin', 'Mabry', 'Norwood', 'Orrick', 'Pryce',
     'Quarry', 'Redfern', 'Stroud', 'Tamsin', 'Upton', 'Vance', 'Whitlock', 'Yarrow', 'Zeller', 'Ashdown', 'Blythe', 'Corrin', 'Delane', 'Elsworth', 'Farrow', 'Gant', 'Holloway', 'Ives', 'Jessop', 'Kerr', 'Lisle', 'Merrow', 'Nash', 'Oakes']
names = iter(f'{f} {l}' for l in L for f in F)
pid = [93000000]
def pilot(corp):
    pid[0] += 1; n = next(names); M.PILOTS[pid[0]] = (n, corp); M.NAME_ID[n.lower()] = pid[0]; return n
LOCAL = []
for i in range(80):
    c = 98100000 + i; M.ORGS[c] = ('corporation', f'{A[i % 20]} {B[(i * 7) % 16]} Co', f'N{i:02d}', None)
    for _ in range(3 + (i * 5) % 7): LOCAL.append(pilot(c))
GRB = 99100001; M.ORGS[GRB] = ('alliance', 'Grand Red Bloc', 'GRB', None)
GRB_CORPS = []
for i in range(40):
    c = 98200000 + i; GRB_CORPS.append(c); M.ORGS[c] = ('corporation', f'Red {B[i % 16]} {A[(i * 3) % 20]}', f'R{i:02d}', GRB)
    for _ in range(2 + (i * 3) % 4): LOCAL.append(pilot(c))
HOST = [{'kind': 'alliance', 'id': GRB, 'name': 'Grand Red Bloc'}]
for i in range(30):
    a = 99200000 + i; c = 98300000 + i; M.ORGS[a] = ('alliance', f'{A[(i * 3 + 1) % 20]} {B[(i * 5) % 16]} Pact', f'H{i:02d}', None); M.ORGS[c] = ('corporation', f'{A[(i * 3 + 1) % 20]} Wing {i}', f'HW{i:02d}', a)
    HOST.append({'kind': 'alliance', 'id': a, 'name': M.ORGS[a][1]})
    for _ in range(3 + i % 5): LOCAL.append(pilot(c))
M.ORG_BY_NAME = {v[1].lower(): (k, v[0]) for k, v in M.ORGS.items()}
GRB_PILOTS = {c: sum(1 for v in M.PILOTS.values() if v[1] == c) for c in GRB_CORPS}
SIDE = {'pilot': {'id': 90000001, 'name': 'Test Pilot'}, 'corp': {'id': M.CORP, 'name': 'Example Corp', 'kind': 'corporation'}, 'alliance': {'id': M.ALLIANCE, 'name': 'Example Alliance', 'kind': 'alliance'},
        'friendly': [], 'hostile': HOST, 'rows': 15}
HULLS = [h for h in ['Ferox', 'Basilisk', 'Scimitar', 'Muninn', 'Cerberus', 'Eagle', 'Zealot', 'Sacrilege', 'Ishtar', 'Vagabond', 'Huginn', 'Lachesis', 'Rapier', 'Arazu', 'Falcon', 'Curse',
         'Sabre', 'Flycatcher', 'Heretic', 'Eris', 'Stiletto', 'Malediction', 'Crow', 'Ares', 'Hound', 'Manticore', 'Purifier', 'Nemesis', 'Vulture', 'Claymore', 'Damnation', 'Nighthawk',
         'Hurricane', 'Drake', 'Brutix', 'Harbinger', 'Megathron', 'Typhoon', 'Apocalypse', 'Rokh', 'Guardian', 'Oneiros', 'Kikimora', 'Svipul', 'Jackdaw', 'Hecate'] if h in byname]
lines = []
for k, h in enumerate(HULLS):
    for j in range(1 + (k * 7) % 12):
        d = f'{random.randint(2, 90) * 100:,} m' if j % 3 == 0 else f'{random.uniform(1, 12):.1f} AU'
        lines.append(f"{byname[h]}\tSomeone's {h}\t{h}\t{d}")
SCAN = '\n'.join(lines)
TALIA = 92000201; M.PILOTS[TALIA] = ('Talia Sabrewing', 98000042); M.NAME_ID['talia sabrewing'] = TALIA
MATES = M.BIG_PILOTS
def kill(att, victim, days):
    M._kid[0] += 1; k = M._kid[0]
    M.KM[k] = {'killmail_id': k, 'killmail_time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - days * 86400)), 'solar_system_id': 30004759,
               'victim': {'character_id': M.pick(98000013), 'corporation_id': 98000013, 'ship_type_id': byname[victim], 'damage_taken': 5000, 'items': [], 'position': {'x': 0, 'y': 0, 'z': 0}},
               'attackers': [dict(M.aff(c), final_blow=i == 0, damage_done=100, security_status=0, ship_type_id=byname[h], weapon_type_id=byname['125mm Gatling AutoCannon II']) for i, (c, h) in enumerate(att)]}
    M.H[k] = M.hashlib.sha1(str(k).encode()).hexdigest(); M.VALUE[k] = 25e6 + k % 7 * 9e6; return k
TK = [kill([(TALIA, 'Sabre')] + [(MATES[m], 'Rifter') for m in range(i % 6)], ['Rifter', 'Caracal', 'Vexor', 'Thorax'][i % 4], 0.2 + i * 0.5) for i in range(42)]
M.HIST[TALIA] = {'kills': TK, 'losses': [M._loss(TALIA, 'Curse', 9.5)]}
INIT = "localStorage.setItem('dscanSide', %s);" % json.dumps(json.dumps(SIDE))

COLS = """() => [...document.querySelectorAll('#saResults .sa-cols .sa-col')].map(c => { const r = c.getBoundingClientRect(), m = c.querySelector(':scope > .sa-more');
  const vb = r.bottom - (m && !m.hidden ? m.offsetHeight : 0);
  return {key: c.dataset.saCol, h: r.height, ch: c.clientHeight, sh: c.scrollHeight, st: c.scrollTop, mh: getComputedStyle(c).maxHeight,
    below: [...c.querySelectorAll(':scope > details.sa-g')].filter(g => g.getBoundingClientRect().top >= vb - 1).length, more: m ? (m.hidden ? '' : m.textContent) : null}; })"""

with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    def page(w=1440, h=1000):
        ctx = b.new_context(viewport={'width': w, 'height': h}, bypass_csp=True); ctx.add_init_script(INIT); M.route(ctx)
        pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:200])); pg.goto('file://' + HTML); pg.wait_for_timeout(600); return pg
    def analyze(pg):
        pg.click('#tabBtnDscan'); pg.fill('#localInput', '\n'.join(LOCAL)); pg.fill('#dscanInput', SCAN); pg.click('#analyzeBtn')
        pg.wait_for_selector('.sa-cols .sa-col', timeout=120000); pg.wait_for_selector('#scanRail:not([hidden]) .sr-row', timeout=120000); pg.wait_for_timeout(2500)
    def col(pg, k): return next(c for c in pg.evaluate(COLS) if c['key'] == k)

    pg = page(); analyze(pg)
    vh = pg.evaluate('innerHeight')
    # ---- 1. the columns ----
    C = pg.evaluate(COLS)
    check(len(C) == 2 and all(c['h'] <= vh - 24 + 1 and c['sh'] > c['ch'] + 50 for c in C), f'two columns, each no taller than the window less 24 px ({vh - 24}) and scrolling inside {[(c["key"], round(c["h"]), c["sh"]) for c in C]}')
    check(all(c['below'] > 0 and c['more'] == f"+{c['below']} more group{'' if c['below'] == 1 else 's'} below" for c in C), f'"+N more groups below" counts the groups under the visible bottom {[(c["below"], c["more"]) for c in C]}')
    pg.evaluate("() => { const c = document.querySelector('.sa-col[data-sa-col=\"n\"]'); c.scrollTop = 400; }"); pg.wait_for_timeout(300)
    hd = pg.evaluate("() => { const c = document.querySelector('.sa-col[data-sa-col=\"n\"]'); return [c.querySelector(':scope > .card-head').getBoundingClientRect().top - c.getBoundingClientRect().top]; }")
    n1 = col(pg, 'n')
    check(abs(hd[0]) <= 2 and n1['more'] == (f"+{n1['below']} more group{'' if n1['below'] == 1 else 's'} below" if n1['below'] else ''), f'scrolled 400 px: the heading stays at the top ({hd}), the "+N" line follows the scroll ({n1["below"]}, {n1["more"]!r})')
    pg.evaluate("() => { const c = document.querySelector('.sa-col[data-sa-col=\"n\"]'); c.scrollTop = c.scrollHeight; }"); pg.wait_for_timeout(300)
    check(col(pg, 'n')['more'] == '', f'scrolled to the end: no "+N" line ({col(pg, "n")["more"]!r})')
    # the wheel at the column's end goes on to the page
    pg.evaluate("window.scrollTo(0, document.querySelector('#saOut').getBoundingClientRect().top + scrollY - 10)"); pg.wait_for_timeout(200)
    y0 = pg.evaluate('scrollY'); bx = pg.evaluate("() => { const r = document.querySelector('.sa-col[data-sa-col=\"n\"]').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }")
    pg.mouse.move(bx[0], bx[1]); pg.mouse.wheel(0, 400); pg.wait_for_timeout(500)
    check(pg.evaluate('scrollY') > y0 + 100, f'the wheel at the column\'s end scrolls the page (not trapped: overscroll-behavior auto) {y0} -> {pg.evaluate("scrollY")}')
    # opening a group near the visible bottom scrolls the column, never the page
    pg.evaluate("() => { document.querySelector('.sa-col[data-sa-col=\"n\"]').scrollTop = 0; window.scrollTo(0, document.querySelector('#saOut').getBoundingClientRect().top + scrollY - 10); }"); pg.wait_for_timeout(300)
    gk = pg.evaluate("""() => { const c = document.querySelector('.sa-col[data-sa-col="n"]'), b = c.getBoundingClientRect().bottom - 40;
      const g = [...c.querySelectorAll(':scope > details.sa-g:not([open])')].filter(d => d.getBoundingClientRect().bottom < b).pop(); return g && g.dataset.saG; }""")
    y1, st1 = pg.evaluate('scrollY'), col(pg, 'n')['st']
    pg.evaluate("(k) => document.querySelector(`details.sa-g[data-sa-g=\"${k}\"] > summary`).click()", gk); pg.wait_for_timeout(500)
    G = pg.evaluate("""(k) => { const d = document.querySelector(`details.sa-g[data-sa-g="${k}"]`), c = d.closest('.sa-col'), m = c.querySelector(':scope > .sa-more'), h = c.querySelector(':scope > .card-head');
      const C = c.getBoundingClientRect(), r = d.getBoundingClientRect(); return {open: d.open, bottom: r.bottom, cb: C.bottom - (m.hidden ? 0 : m.offsetHeight), top: r.top, ct: C.top + h.offsetHeight}; }""", gk)
    check(G['open'] and abs(pg.evaluate('scrollY') - y1) < 1 and col(pg, 'n')['st'] > st1 and G['bottom'] <= G['cb'] + 6 and G['top'] >= G['ct'] - 1,
          f'a group opened at the column\'s bottom: the column scrolls to show it ({st1} -> {col(pg, "n")["st"]}), the page stays ({y1} -> {pg.evaluate("scrollY")}) {G}')
    # a redraw keeps the scroll and the focus
    pg.evaluate("() => { const c = document.querySelector('.sa-col[data-sa-col=\"n\"]'); c.scrollTop = 333; }")
    pg.evaluate("(k) => document.querySelector(`details.sa-g[data-sa-g=\"${k}\"] > summary`).focus({preventScroll: true})", gk)
    st2 = col(pg, 'n')['st']; pg.evaluate('saRender()'); pg.wait_for_timeout(300)
    kept = pg.evaluate("(k) => [document.querySelector('.sa-col[data-sa-col=\"n\"]').scrollTop, document.activeElement && document.activeElement.parentElement && document.activeElement.parentElement.dataset.saG === k]", gk)
    check(abs(kept[0] - st2) <= 1 and kept[1], f'saRender keeps the column\'s scroll ({st2} -> {kept[0]}) and the focus ({kept[1]}) (LESSON #119)')
    # ---- 2. the 40-corporation group ----
    gb = f'h:a{GRB}'
    pg.evaluate("(k) => { const d = document.querySelector(`details.sa-g[data-sa-g=\"${k}\"]`); d.querySelector('summary').click(); }", gb); pg.wait_for_timeout(400)
    CG = """(k) => { const d = document.querySelector(`details.sa-g[data-sa-g="${k}"]`), m = d.querySelector('.sa-cmore');
      return {corps: d.querySelectorAll('.sa-corp').length, btn: m && m.querySelector('button').textContent, exp: m && m.querySelector('button').getAttribute('aria-expanded'), ctx: m && m.querySelector('.ctx').textContent,
        names: [...d.querySelectorAll('.sa-corp > span:first-child')].map(s => s.textContent.trim().split(' ')[0])}; }"""
    srt = sorted(GRB_CORPS, key=lambda c: (-GRB_PILOTS[c], M.ORGS[c][1]))
    hid = sum(GRB_PILOTS[c] for c in srt[8:])
    g1 = pg.evaluate(CG, gb)
    check(g1['corps'] == 8 and g1['btn'] == 'Show 32 more corporations' and g1['exp'] == 'false' and g1['ctx'] == f'{hid} pilots',
          f'the 40-corporation group: 8 lines, "Show 32 more corporations", "{hid} pilots" {g1["corps"]} {g1["btn"]!r} {g1["ctx"]!r}')
    pg.evaluate("(k) => document.querySelector(`details.sa-g[data-sa-g=\"${k}\"] .sa-cmore button`).click()", gb); pg.wait_for_timeout(400)
    g2 = pg.evaluate(CG, gb); foc = pg.evaluate("() => document.activeElement && document.activeElement.dataset.saCorps")
    check(g2['corps'] == 40 and g2['btn'] == 'Show fewer' and g2['exp'] == 'true' and foc == gb, f'pressed: all 40 and "Show fewer", the focus on it {g2["corps"]} {g2["btn"]!r} {foc!r}')
    pg.evaluate('saRender()'); pg.wait_for_timeout(300)
    check(pg.evaluate(CG, gb)['corps'] == 40, f'... kept through a redraw ({pg.evaluate(CG, gb)["corps"]})')
    pg.evaluate("(k) => document.querySelector(`details.sa-g[data-sa-g=\"${k}\"] .sa-cmore button`).click()", gb); pg.wait_for_timeout(400)
    check(pg.evaluate(CG, gb)['corps'] == 8, f'pressed again: 8 ({pg.evaluate(CG, gb)["corps"]})')
    # ---- 3. corporation lines line up ----
    kms = []
    kid = 77700000
    for n, (kk, ll) in enumerate([(1, 0), (12, 3), (123, 45), (0, 7), (5, 210)]):
        cid = srt[n]
        for j in range(kk): kid += 1; kms.append({'killmail_id': kid, 'killmail_time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - 600)), 'victim': {'corporation_id': 98000013, 'ship_type_id': 587}, 'attackers': [{'character_id': 1, 'corporation_id': cid}]})
        for j in range(ll): kid += 1; kms.append({'killmail_id': kid, 'killmail_time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - 600)), 'victim': {'corporation_id': cid, 'ship_type_id': 587}, 'attackers': [{'character_id': 1, 'corporation_id': 98000013}]})
    pg.evaluate("""(kms) => { sa.act = {sysId: 30004759, name: 'Test System', list: kms.map(k => ({killmail_id: k.killmail_id, zkb: {totalValue: 1e6}})), kms, busy: false}; saRender(); }""", kms); pg.wait_for_timeout(400)
    AL = pg.evaluate("""(k) => [...document.querySelectorAll(`details.sa-g[data-sa-g="${k}"] .sa-corp`)].slice(0, 6).map(r => { const s = r.querySelectorAll('.sa-act-m > .s'), c = r.querySelector('.c');
      const x = (e) => { const a = e.querySelector('a'); return a ? Math.round(a.getBoundingClientRect().right) : null; };
      return {up: s[0] && x(s[0]), dn: s[1] && x(s[1]), upT: s[0] && s[0].textContent, dnT: s[1] && s[1].textContent, c: Math.round(c.getBoundingClientRect().right), s0: s[0] && Math.round(s[0].getBoundingClientRect().left), s1: s[1] && Math.round(s[1].getBoundingClientRect().left)}; })""", gb)
    ups = {a['up'] for a in AL if a['up']}; dns = {a['dn'] for a in AL if a['dn']}
    check(len(AL) == 6 and len(ups) == 1 and len(dns) == 1 and len({a['c'] for a in AL}) == 1 and len({a['s0'] for a in AL}) == 1 and len({a['s1'] for a in AL}) == 1
          and [a['upT'] for a in AL[:5]] == ['▲1', '▲12', '▲123', '', '▲5'] and [a['dnT'] for a in AL[:5]] == ['', '▼3', '▼45', '▼7', '▼210'],
          f'corporation lines: the ▲ column, the ▼ column and the pilot count each line up whatever the numbers and names {AL}')
    # ---- 6. amber ----
    AM = pg.evaluate("""() => { const b = document.querySelector('.sa-cmore button'), s = getComputedStyle(b), amber = getComputedStyle(document.documentElement).getPropertyValue('--amber').trim();
      const t = document.createElement('i'); t.style.color = amber; document.body.appendChild(t); const a = getComputedStyle(t).color; t.remove();
      return {color: s.color, amber: a, h: Math.round(b.getBoundingClientRect().height), font: s.fontSize}; }""")
    check(AM['color'] == AM['amber'] and 28 <= AM['h'] <= 32 and AM['font'] == '12px', f'"Show N more corporations" in the page\'s amber, compact ({AM})')
    # v2026.11.07.6 (the owner: "yes" to the other show-more buttons): a corporation's "+N more" pilots, the same amber button
    AP = pg.evaluate("""() => { const b = document.querySelector('.sa-pilots button.sa-link[data-more]'); if(!b) return null; const s = getComputedStyle(b), t = document.createElement('i'); t.style.color = 'var(--amber)'; document.body.appendChild(t); const a = getComputedStyle(t).color; t.remove();
      return {color: s.color, amber: a, border: s.borderTopColor !== 'rgba(0, 0, 0, 0)' && s.borderTopStyle === 'solid', h: Math.round(b.getBoundingClientRect().height), font: s.fontSize, text: b.textContent}; }""")
    check(AP and AP['color'] == AP['amber'] and AP['border'] and 28 <= AP['h'] <= 32 and AP['font'] == '12px' and AP['text'].startswith('+'), f'a corporation\'s "+N more" pilots: the same amber button ({AP})')
    # ---- 4. the scan rail ----
    pg.evaluate("window.scrollTo(0, document.querySelector('#saOut').getBoundingClientRect().top + scrollY - 10)"); pg.wait_for_timeout(300)
    R = pg.evaluate("() => { const r = document.querySelector('#scanRail'), b = r.getBoundingClientRect(); return {h: b.height, ch: r.clientHeight, sh: r.scrollHeight, mh: getComputedStyle(r).maxHeight}; }")
    check(R['h'] <= vh - 24 + 1 and R['sh'] > R['ch'] + 100, f'the scan rail: no taller than the window less 24 px, scrolling inside {R}')
    row = pg.evaluate("""() => { const r = document.querySelector('#scanRail'), B = r.getBoundingClientRect();
      const rows = [...r.querySelectorAll('button.sr-row')].filter(x => { const b = x.getBoundingClientRect(); return b.top > B.top && b.bottom < B.bottom - 2; }); return rows.pop().dataset.sr; }""")
    pg.hover(f'#scanRail button.sr-row[data-sr="{row}"]'); pg.wait_for_timeout(500)
    SC = """(id) => { const c = document.querySelector('#scanCard'), r = document.querySelector(`button.sr-row[data-sr="${id}"]`); if(!c || c.hidden) return null; const b = c.getBoundingClientRect(), rb = r.getBoundingClientRect();
      const top = (x, y) => { const e = document.elementFromPoint(x, y); return !!(e && e.closest('#scanCard')); };
      return {parent: c.parentElement.id, l: b.left, t: b.top, r: b.right, b: b.bottom, beside: b.top <= rb.top + 1 && b.bottom >= rb.bottom - 1, on: [top(b.left + 4, b.top + 4), top(b.right - 4, b.top + 4), top(b.left + 4, b.bottom - 4), top(b.right - 4, b.bottom - 4)]}; }"""
    c1 = pg.evaluate(SC, row)
    check(c1 and c1['parent'] == 'saOut' and c1['l'] >= 0 and c1['t'] >= 0 and c1['r'] <= 1440 and c1['b'] <= vh and all(c1['on']),
          f'the hover card for the rail\'s lowest visible row: outside the rail (in #saOut), fully on screen and on top of Local\'s cards {c1}')
    pg.evaluate("() => { document.querySelector('#scanRail').scrollTop += 30; }"); pg.wait_for_timeout(300)
    c2 = pg.evaluate(SC, row)
    check(c1 and c1['beside'] and c2 and c2['beside'] and c2['t'] != c1['t'], f'the rail scrolls 30 px: the card moves and stays beside its row ({c1 and round(c1["t"])} -> {c2 and round(c2["t"])}, {c2 and c2["beside"]})')
    pg.mouse.move(5, 5); pg.wait_for_timeout(300)
    first = pg.evaluate("() => { const r = document.querySelector('#scanRail'); r.scrollTop = 0; return r.querySelector('button.sr-row').dataset.sr; }"); pg.wait_for_timeout(200)
    pg.evaluate("(id) => scanCardOpen(document.querySelector(`button.sr-row[data-sr=\"${id}\"]`), true)", first); pg.wait_for_timeout(200)
    op = pg.evaluate(SC, first) is not None
    pg.evaluate("() => { document.querySelector('#scanRail').scrollTop += 2000; }"); pg.wait_for_timeout(300)
    check(op and pg.evaluate(SC, first) is None, f'its row scrolled out of the rail\'s view: the card closes (open before {op})')
    pg.evaluate("() => { document.querySelector('#scanRail').scrollTop = 250; scanRailRender(); }"); pg.wait_for_timeout(200)
    check(abs(pg.evaluate("document.querySelector('#scanRail').scrollTop") - 250) <= 1 and pg.evaluate("document.querySelectorAll('#scanCard').length") == 1,
          f'scanRailRender keeps the rail\'s scroll ({pg.evaluate("document.querySelector(\'#scanRail\').scrollTop")}) and one card')
    pg.context.close()

    # ---- 5. the dossier ----
    pg = page(1440, 1100)
    pg.click('#tabBtnPilot'); pg.fill('#pilotName', 'Talia Sabrewing'); pg.click('#fitBtn')
    pg.wait_for_function("() => !document.querySelector('#fitBtn').disabled && document.querySelector('#pilotBusy').hidden", timeout=180000); pg.wait_for_timeout(800)
    sab = byname['Sabre']
    pg.click(f'#pilotDossier [data-pd-exp="{sab}"]'); pg.wait_for_timeout(600)
    DB = f"""() => {{ const k = document.querySelector('#pdk-{sab}'), kl = k.querySelector('.pd-kl'), rows = [...k.querySelectorAll('.pdk[data-pdk]')];
      const fewer = k.querySelector('[data-pd-fewer]');
      if(!kl) return {{rows: rows.length, box: false, fewer: !!fewer}};
      const B = kl.getBoundingClientRect(), H = kl.querySelector(':scope > .pdk-h'), r10 = rows[10].getBoundingClientRect();
      return {{rows: rows.length, box: true, fewer: !!fewer, head: !!H && H.parentElement === kl, edge: Math.round(rows[10].offsetTop - kl.clientHeight), st: kl.scrollTop, sh: kl.scrollHeight, ch: kl.clientHeight}}; }}"""
    d0 = pg.evaluate(DB)
    check(d0['rows'] == 10 and not d0['box'] and not d0['fewer'], f'10 Sabre kills: no box, no "Show fewer" {d0}')
    for i in range(3):
        pg.click(f'#pdk-{sab} [data-pd-more]'); pg.wait_for_timeout(800)
        if i == 0:
            fn = pg.evaluate(f"""() => {{ const kl = document.querySelector('#pdk-{sab} .pd-kl'), H = kl.querySelector(':scope > .pdk-h'), r = kl.querySelectorAll('.pdk[data-pdk]')[10];
              return Math.round(r.getBoundingClientRect().top - H.getBoundingClientRect().bottom); }}""")
            check(abs(fn) <= 2, f'after "Show 10 more": the first new row just under the box\'s heading ({fn} px)')
    d1 = pg.evaluate(DB)
    stk = pg.evaluate(f"() => {{ const kl = document.querySelector('#pdk-{sab} .pd-kl'); kl.scrollTop = 200; const H = kl.querySelector(':scope > .pdk-h'); return Math.round(H.getBoundingClientRect().top - kl.getBoundingClientRect().top); }}")
    check(d1['rows'] == 40 and d1['box'] and d1['head'] and abs(d1['edge']) <= 1 and d1['sh'] > d1['ch'] + 100 and d1['fewer'] and abs(stk) <= 1,
          f'40 Sabre kills: in a box exactly 10 rows + the heading tall (the 11th row at its edge), the heading inside and sticky ({stk}), "Show fewer" {d1}')
    pg.evaluate("() => pdRender()"); pg.wait_for_timeout(300)
    check(abs(pg.evaluate(f"document.querySelector('#pdk-{sab} .pd-kl').scrollTop") - 200) <= 1, f'pdRender keeps the box\'s scroll ({pg.evaluate(f"document.querySelector(\'#pdk-{sab} .pd-kl\').scrollTop")})')
    AM2 = pg.evaluate("""() => { const b = document.querySelector('.pdk-more button'), s = getComputedStyle(b), t = document.createElement('i'); t.style.color = 'var(--amber)'; document.body.appendChild(t); const a = getComputedStyle(t).color; t.remove();
      return {color: s.color, amber: a, h: Math.round(b.getBoundingClientRect().height), font: s.fontSize}; }""")
    check(AM2['color'] == AM2['amber'] and 28 <= AM2['h'] <= 32 and AM2['font'] == '12px', f'the dossier\'s "Show 10 more" in the page\'s amber, the same compact size ({AM2})')
    pg.click(f'#pdk-{sab} [data-pd-fewer]'); pg.wait_for_timeout(400)
    d2 = pg.evaluate(DB)
    check(d2['rows'] == 10 and not d2['box'] and not d2['fewer'], f'"Show fewer": 10 rows, no box {d2}')
    pg.context.close()

    # ---- 7. 760 px: nothing capped ----
    pg = page(760, 1000); analyze(pg)
    N = pg.evaluate("""() => ({cols: [...document.querySelectorAll('.sa-cols .sa-col')].map(c => getComputedStyle(c).maxHeight), rail: getComputedStyle(document.querySelector('#scanRail')).maxHeight,
      more: [...document.querySelectorAll('.sa-more')].map(m => getComputedStyle(m).display)})""")
    check(all(x == 'none' for x in N['cols']) and N['rail'] == 'none' and all(x == 'none' for x in N['more']), f'760 px: the columns and the rail uncapped, no "+N" line {N}')
    pg.context.close()
    b.close()
check(not errs, f'no page errors {errs[:3]}')
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
