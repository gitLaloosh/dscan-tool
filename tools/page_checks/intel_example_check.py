"""Intel for new users: an example of Intel at work (v2026.11.07.7, build queue 017; Project docs roadmap/intel-example-plan.md and
roadmap/intel-example-build-review.md; mockup Claude outputs/intel_example_mockup.html).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/intel_example_check.py [index.html]   -> 'FAILURES: N' (must be 0)

intel_check.py's stand-ins (its made-up Chatlogs folder, ESI and system names, the R2Z2 stand-in), then:
  * a new user (nothing saved): the example under the setup steps, before "Log Chat to File": the EXAMPLE tag, its title, the
    page's own rows from IT_EXAMPLE (7 Near You rows, the Feed's first 5), the map as a picture, the notes 1-5 and the foot line;
    each of the 5 markers on its target (within 4 px of the target's left edge, or the picture's corner) at 1440 and 390;
  * no leaks: drawing it asks nothing of anyone (only ship icons from images.evetech.net), writes nothing to localStorage, plays no
    sound, shows no notification, leaves Intel's state (its lists, filters, names, Standings) and the map's state as they were;
  * inert: Tab never lands inside it, a press on its kill badge or a pilot opens nothing; every chip's corporation and alliance has
    its emblem (an inline image, no empty logo box) and ticker;
  * 390 px: no sideways scroll, Near You as a list (no map), note 3's phone wording;
  * the bug found at 017's review (the owner: "why would we allow intel to be turned out if no intel channels have been linked and
    chosen?"): the folder chosen, no channel ticked, the switch: Intel stays off and says to choose the channels; on with a channel,
    unticking the last one stops it;
  * a quiet start (on, nothing reported yet): the empty lists on top and the example below them; the first real report: gone, and
    remembered (dscanItExGone) while the folder is linked; the window emptied: still gone; reloaded with the folder: gone; with no
    folder linked: shown again; "See an example" in the info panel: shown with the shared close button, which takes it away again;
  * a browser without the folder picker: the amber note above the steps (Chrome or Edge), the example still shown; Brave (a stand-in
    navigator.brave): the Brave line with brave://flags/#file-system-access-api as text (no link, no button), and INTEL-01 on the
    button press says the same; the picker there too (the flag on): no note.
v2026.11.07.6 fails (no example, and the switch turns on with no channel).
"""
import sys, os, re, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
_src = open(os.path.join(HERE, 'intel_check.py'), encoding='utf-8').read()
_src = _src[:_src.index('with sync_playwright() as p:')]
NS = {'__file__': os.path.join(HERE, 'intel_check.py'), '__name__': 'intel_check_prefix'}
exec(compile(_src, 'intel_check.py (first part)', 'exec'), NS)
globals().update({k: v for k, v in NS.items() if not k.startswith('__') and k not in ('check', 'fails')})
check = NS['check']
from playwright.sync_api import sync_playwright

REQ = []
SPY = r"""(() => { window.__ls = []; const s = Storage.prototype.setItem; Storage.prototype.setItem = function(k, v){ window.__ls.push(k); return s.call(this, k, v); }; })();"""
STATE = """() => JSON.stringify({feed: it.feed.length, near: it.near.size, fl: it.fl.length, q: it.q, names: !!it.names, set: JSON.stringify(it.set), me: JSON.stringify(it.me),
  side: JSON.stringify(side.rec), pins: [...itm.pinned].length, home: itm.home, draws: itm.draws, layouts: itm.layouts, cv: !!itm.cv && itm.cv.isConnected, ex: itExOrg})"""
MARKS = """() => { const f = document.querySelector('#intelPanel .itx'); if(!f) return null; const E = (s) => f.querySelector(s);
  const al = f.querySelectorAll('.itx-near .it-nb.alert'), T = {1: E('.itx-feed .it-fd.rep'), 2: E('.itx-near .it-nb'), 3: E('.itx-map img[src]'), 4: al[1] || al[0], 5: E('.itx-near .it-kl')};
  const phone = innerWidth < 600, F = f.getBoundingClientRect();
  return [1, 2, 3, 4, 5].map(n => { const m = f.querySelector(`[data-itx-mk="${n}"]`), r = m.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    if(m.hidden) return [n, 'hidden'];
    const inF = r.left >= F.left - 1 && r.right <= F.right + 1 && r.top >= F.top - 1 && r.bottom <= F.bottom + 1;
    if(n === 3 && phone){ const h = E('.it-nearcol > .it-h'), b = h.getBoundingClientRect(); return [n, inF && cy >= b.top && cy <= b.bottom]; }
    const t = T[n]; if(!t) return [n, 'no target']; const b = t.getBoundingClientRect();
    const ok = n === 5 ? Math.abs(cx - (b.right + 16)) <= 4 && Math.abs(cy - (b.top + 7)) <= 4 : Math.abs(cx - b.left - (n === 3 ? 14 : 0)) <= 4 && cy >= b.top - 2 && cy <= b.bottom + 2;
    return [n, inF && ok]; }); }"""
INFO = """() => { const f = document.querySelector('#intelPanel .itx'); if(!f) return null; const p = f.parentElement;
  const setup = document.querySelector('#intelPanel .it-setup'), log = [...document.querySelectorAll('#intelPanel .it-sub')].find(x => /Log Chat to File/.test(x.textContent));
  return {tag: f.querySelector('.itx-tag').textContent, title: f.querySelector('.itx-t').textContent, ctx: (f.querySelector('.itx-h .ctx') || {}).textContent,
    near: f.querySelectorAll('.itx-near .it-nb').length, feed: f.querySelectorAll('.itx-feed .it-fd').length, img: (f.querySelector('.itx-map img') || {}).naturalWidth || 0,
    notes: [...f.querySelectorAll('.itx-notes li')].map(l => l.textContent.trim()), foot: f.querySelector('.itx-foot').textContent,
    afterSetup: !!setup && !!(setup.compareDocumentPosition(f) & 4), beforeLog: !!log && !!(f.compareDocumentPosition(log) & 4), inert: f.querySelector('.itx-body').inert,
    role: f.getAttribute('role'), label: f.getAttribute('aria-label'), close: !!f.querySelector('button.x-close'),
    logos: [...f.querySelectorAll('.it-seg.grp')].map(g => [!!g.querySelector('.it-lg img[src^="data:image/svg+xml"]'), (g.querySelector('.tk') || {}).textContent || '']),
    emptyLogo: f.querySelectorAll('.it-lg:not(:has(img))').length, tkFor: f.querySelectorAll('[data-tk-for]').length, sw: document.documentElement.scrollWidth}; }"""
NOTES = ['1A report from your intel channel: read as your scouts type it: who, what they fly, where.', '2How far, in jumps: Near You lists everything within reach, nearest first.',
         '3The map: reports and kills around you; hover one for its route to you.', '4Inside your alert range: a sound, a desktop notice, and an amber mark on your profile, from any tab.',
         '5Kills nearby: from zKillboard as they happen; press one to see the attacking fleet and its fits.']

with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    def new_ctx(w, init=''):
        ctx = b.new_context(bypass_csp=True, viewport={'width': w, 'height': 1000}); ctx.on('page', lambda pg: pg.on('pageerror', lambda e: errs.append(str(e)[:200])))
        ctx.add_init_script(SPY)
        if init: ctx.add_init_script(init)
        ctx.add_init_script(FS); route(ctx)
        ctx.on('request', lambda r: REQ.append(r.url) if not r.url.startswith('file:') else None)
        return ctx
    def fresh(ctx):
        pg = ctx.new_page(); pg.goto('file://' + HTML)
        pg.evaluate("(s) => { localStorage.clear(); localStorage.setItem('dscanSide', JSON.stringify(s)); }", SIDE); pg.reload(); pg.wait_for_timeout(500)
        return pg

    # ---- a new user, 1440 ----
    ctx = new_ctx(1440); pg = fresh(ctx)
    pg.wait_for_timeout(1500)   # the page's own start-up writes (lookup counts, saved at most once a second) are done
    s0 = pg.evaluate(STATE); pg.evaluate("() => { window.__ls = []; }"); n0 = len(REQ)
    pg.click('#tabBtnIntel'); pg.wait_for_timeout(1500)
    I = pg.evaluate(INFO)
    check(I and I['tag'] == 'EXAMPLE' and I['title'] == 'What Intel looks like once it’s running' and I['ctx'] == 'made-up pilots on real systems' and I['afterSetup'] and I['beforeLog']
          and I['role'] == 'region' and I['label'] == 'Example: what Intel shows once it’s running' and not I['close'],
          f'a new user: the example under the setup steps, before "Log Chat to File", tagged EXAMPLE, its title and context, a region, no close button {I and {k: I[k] for k in ("tag", "title", "afterSetup", "beforeLog", "close")}}')
    check(I and I['near'] == 7 and I['feed'] == 5 and I['img'] > 100 and I['notes'] == NOTES and I['foot'] == 'Your own reports replace this example as soon as the first one arrives.',
          f'the page\'s own rows (7 Near You, the Feed\'s first 5), the map as a picture, the notes 1-5 and the foot line {I and (I["near"], I["feed"], I["img"], I["notes"][:1])}')
    M1 = pg.evaluate(MARKS)
    check(M1 and all(ok is True for _, ok in M1), f'1440: each marker on its target {M1}')
    check(I and I['logos'] and all(a and re.fullmatch(r'[\[<][A-Z]{3,5}[\]>]', t) for a, t in I['logos']) and I['emptyLogo'] == 0 and I['tkFor'] == 0,
          f'every corporation and alliance on a chip: its emblem (an inline image) and its ticker; no empty logo box, no ticker left to look up ({len(I["logos"]) if I else 0} groups)')
    asked = [u for u in REQ[n0:] if not re.match(r'https://images\.evetech\.net/types/\d+/icon', u)]
    s1 = pg.evaluate(STATE); ls = pg.evaluate("() => window.__ls"); snd = pg.evaluate("() => [__fs.beeps, __fs.notes.length]")
    check(not asked and s0 == s1 and not ls and snd == [0, 0] and pg.evaluate("() => document.querySelector('#profile').dataset.it || ''") in ('', 'off'),
          f'no leaks: nothing asked but ship icons {asked[:3]}, Intel\'s and the map\'s state unchanged {s0 == s1}, no storage write {ls}, no sound or notice {snd}')
    # inert: Tab never lands inside, a press does nothing
    inside = []
    for _ in range(60):
        pg.keyboard.press('Tab'); inside.append(pg.evaluate("() => !!(document.activeElement && document.activeElement.closest('.itx-body'))"))
    kb = pg.evaluate("() => { const r = document.querySelector('.itx .itx-near .it-kl').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }")
    pg.mouse.click(kb[0], kb[1]); pg.wait_for_timeout(400)
    pn = pg.evaluate("() => { const r = document.querySelector('.itx .itx-feed .it-seg.nmb').getBoundingClientRect(); return [r.left + 5, r.top + r.height / 2]; }")
    pg.mouse.click(pn[0], pn[1]); pg.wait_for_timeout(400)
    tab = pg.evaluate("() => [document.querySelector('.tab-btn.active').id, !document.querySelector('#tabBtnFleet') || document.querySelector('#tabBtnFleet').hidden || !document.querySelector('#tabBtnFleet').checkVisibility()]")
    check(not any(inside) and tab[0] == 'tabBtnIntel' and tab[1], f'inert: Tab never lands inside the example ({sum(inside)} of 60), a press on its kill badge or a pilot opens nothing {tab}')
    pg.close()

    # ---- the bug: no channel, no Intel ----
    pg = fresh(ctx); pg.click('#tabBtnIntel'); setup_logs(pg); pg.click('[data-it-act="folder"]'); pg.wait_for_timeout(500)
    pg.click('#intelSwLabel'); pg.wait_for_timeout(600)
    off = pg.evaluate("() => [it.on, document.querySelector('#intelSw').checked, document.querySelector('#itNotes').textContent]")
    check(off[0] is False and off[1] is False and 'Choose your intel channels first (2 below).' in off[2], f'the folder chosen, no channel ticked: the switch leaves Intel off and says why {off}')
    pg.check('[data-it-chan="region.intel"]'); pg.check(f'[data-it-me="{MAIN}"]'); pg.wait_for_timeout(100)
    pg.click('#intelSwLabel'); pg.wait_for_timeout(2500)
    on = pg.evaluate("() => it.on")
    pg.click('[data-it-act="gear"]'); pg.wait_for_timeout(300); pg.evaluate("() => document.querySelector('.it-pop [data-it-chan=\"region.intel\"]').click()"); pg.wait_for_timeout(500)   # a click: the box is redrawn away as it stops
    st = pg.evaluate("() => [it.on, document.querySelector('#itNotes').textContent]")
    check(on is True and st[0] is False and 'no intel channel is ticked' in st[1], f'on with a channel, then the last one unticked: Intel stops and says why {on} {st}')
    pg.close()

    # ---- a quiet start, then the first real report ----
    pg = fresh(ctx); pg.click('#tabBtnIntel')
    W(pg, F_LOCAL_MAIN, header('Local', 'Your Main', NOW - 7200) + line(NOW - 4000, 'EVE System', 'Channel changed to Local : 1DQ1-A*'))
    W(pg, F_INTEL, header('region.intel', 'Your Main', NOW - 7000) + line(NOW - 6990, 'EVE System', 'Channel MOTD: hi'))
    pg.click('[data-it-act="folder"]'); pg.wait_for_timeout(500)
    pg.check('[data-it-chan="region.intel"]'); pg.check(f'[data-it-me="{MAIN}"]'); pg.wait_for_timeout(100)
    pg.click('#intelSwLabel'); pg.wait_for_timeout(3000)
    q = pg.evaluate("() => { const f = document.querySelector('#intelPanel .itx'), l = document.querySelector('#itFeedList'); return [it.on, it.feed.length, !!f, !!f && !!l && !!(l.compareDocumentPosition(f) & 4), !!f && !!f.querySelector('button.x-close')]; }")
    check(q == [True, 0, True, True, False], f'a quiet start (on, nothing reported): the empty lists on top and the example below them, no close button {q}')
    # drawn again with Intel on (the example's alert-range rows would alert if they were live): no sound, notice or alert state; Standings back
    lk = pg.evaluate("""() => { const a = [__fs.beeps, __fs.notes.length, it.alerted.size, it.alerts || 0, JSON.stringify(side.rec)]; itEx.html = null; itEx.map = null; itRender(true);
      return [a, [__fs.beeps, __fs.notes.length, it.alerted.size, it.alerts || 0, JSON.stringify(side.rec)], (side.rec && side.rec.corp || {}).id]; }""")
    check(lk[0] == lk[1] and lk[2] == M.CORP, f'the example drawn again while Intel is on: no sound, notice or alert, your Standings as they were {lk[0][:4]} -> {lk[1][:4]}, Standings same {lk[0][4] == lk[1][4]}, yours {lk[2]}')
    pg.evaluate("() => { window.__ls = []; }")
    W(pg, F_INTEL, line(time.time() - 5, 'Kai Rhenn', 'T5ZI-S Seren Ketter sabre')); pg.wait_for_timeout(3500)
    g = pg.evaluate("() => [it.feed.length > 0, !!document.querySelector('#intelPanel .itx'), localStorage.getItem('dscanItExGone'), window.__ls.filter(k => k === 'dscanItExGone').length]")
    check(g == [True, False, '1', 1], f'the first real report: the example gone, remembered once (dscanItExGone) {g}')
    pg.evaluate("() => { it.feed = []; it.near = new Map(); itRender(true); }"); pg.wait_for_timeout(300)
    check(not pg.evaluate("() => !!document.querySelector('#intelPanel .itx')"), 'the window emptied later: it stays gone')
    # "See an example": shown with the close button; closed: gone
    pg.evaluate("() => { const d = document.querySelector('#intelPanel .it-head details.info-pop'); d.open = true; }")
    pg.evaluate("() => document.querySelector('#intelPanel .it-head [data-it-act=\"example\"]').click()"); pg.wait_for_timeout(800)
    v = pg.evaluate("() => { const f = document.querySelector('#intelPanel .itx'); return [!!f, !!f && !!f.querySelector('button.x-close'), !!document.querySelector('#intelPanel details.info-pop[open]'), document.activeElement && document.activeElement.matches('.itx button.x-close')]; }")
    pg.evaluate("() => document.querySelector('#intelPanel .itx button.x-close').click()"); pg.wait_for_timeout(500)
    v2 = pg.evaluate("() => !!document.querySelector('#intelPanel .itx')")
    check(v == [True, True, False, True] and v2 is False, f'"See an example" in the info panel: shown with the shared close button (focused), the panel closed; closed: gone {v} {v2}')
    # the stand-in folder can't be kept in IndexedDB as a real one is (a plain object): after the reload it is put back by hand, as the
    # page's start-up does with the kept handle
    pg.reload(); pg.wait_for_timeout(1500); pg.click('#tabBtnIntel'); pg.wait_for_timeout(500)
    rl = pg.evaluate("() => { it.dir = {kind: 'directory', name: 'Chatlogs'}; itRender(true); return [!!it.dir, !!document.querySelector('#intelPanel .itx')]; }")
    check(rl == [True, False], f'reloaded with the folder still linked: still gone {rl}')
    pg.close()
    ctx.close()
    ctx = new_ctx(1440); pg = ctx.new_page(); pg.goto('file://' + HTML); pg.evaluate("() => { localStorage.clear(); localStorage.setItem('dscanItExGone', '1'); }"); pg.reload(); pg.wait_for_timeout(800)
    pg.click('#tabBtnIntel'); pg.wait_for_timeout(1200)
    check(pg.evaluate("() => [!!it.dir, !!document.querySelector('#intelPanel .itx')]") == [False, True], 'remembered as gone, but no folder linked (another browser, the folder unlinked): shown again')
    ctx.close()

    # ---- 390 px ----
    ctx = new_ctx(390); pg = fresh(ctx); pg.click('#tabBtnIntel'); pg.wait_for_timeout(1500)
    I = pg.evaluate(INFO); M2 = pg.evaluate(MARKS)
    vis = pg.evaluate("() => getComputedStyle(document.querySelector('.itx .it-mapcol')).display")
    check(I and I['sw'] <= 390 and vis == 'none' and I['notes'][2] == '3The map: switch Near You to Map to see reports and kills around you.' and all(ok is True for _, ok in M2),
          f'390 px: no sideways scroll ({I and I["sw"]}), Near You as a list (map {vis}), note 3\'s phone wording, each marker on its target {M2}')
    ctx.close()

    # ---- a browser without the folder picker; Brave ----
    NOTE = "() => { const n = document.querySelector('#intelPanel .it-nofs'), s = document.querySelector('#intelPanel .it-setup'); return n ? [n.textContent, !!(n.compareDocumentPosition(s) & 4), n.querySelectorAll('a, button').length, (n.querySelector('code') || {}).textContent || '', !!document.querySelector('#intelPanel .itx')] : [null, !!document.querySelector('#intelPanel .itx')]; }"
    ctx = new_ctx(1440, "window.__noFsApi = true;"); pg = fresh(ctx); pg.click('#tabBtnIntel'); pg.wait_for_timeout(1000)
    n1 = pg.evaluate(NOTE)
    check(n1[0] and n1[0].startswith('Intel needs Chrome or Edge on a computer.') and n1[1] and n1[2] == 0 and n1[4], f'no folder picker (Firefox, Safari): the amber note above the steps, the example still shown {n1}')
    ctx.close()
    ctx = new_ctx(390, "window.__noFsApi = true; navigator.brave = {isBrave: () => Promise.resolve(true)};"); pg = fresh(ctx); pg.click('#tabBtnIntel'); pg.wait_for_timeout(1000)
    n2 = pg.evaluate(NOTE); sw = pg.evaluate("() => document.documentElement.scrollWidth")
    pg.click('[data-it-act="folder"]'); pg.wait_for_timeout(400)
    e1 = pg.evaluate("() => document.querySelector('#itNotes').textContent")
    check(n2[0] and n2[0].startswith('Brave turns off the folder picker Intel needs.') and n2[3] == 'brave://flags/#file-system-access-api' and n2[2] == 0 and n2[4] and sw <= 390
          and 'brave://flags/#file-system-access-api' in e1 and '(INTEL-01)' in e1,
          f'Brave without the picker: its own line, the flag\'s address as text (no link or button), no sideways scroll at 390 ({sw}); INTEL-01 says the same {n2[:1]} {e1[:80]}')
    ctx.close()
    ctx = new_ctx(1440, "navigator.brave = {isBrave: () => Promise.resolve(true)};"); pg = fresh(ctx); pg.click('#tabBtnIntel'); pg.wait_for_timeout(1000)
    n3 = pg.evaluate(NOTE)
    check(n3[0] is None and n3[1], f'Brave with the flag on (the picker there): no note, the example shown {n3}')
    ctx.close()
    b.close()
check(not errs, f'no page errors {errs[:3]}')
print(f"FAILURES: {NS['fails']}")
sys.exit(1 if NS['fails'] else 0)
