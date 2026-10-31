"""Pilot Dossier: their kills in a hull, under its row (v2026.10.14.93).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/dossier_kills_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner via todo-inbox: "in pilot analyzer > pilot dossier > hull row > add ability to expand/collapse. expanding shows a list
of their kills with that hull (shows 10 by default with 'show more' link that continues to load more). add a link to the
zKillboard entry for each one of those kills." Mockup Claude outputs/pilot_kills_list_mockup.html; his answers: "▶ button
per row", "Follow the switch", "Keep reading older kills", columns "As drawn". The real page with ESI and zKillboard
answered from sa_mocks.py; expected lines worked out here from the mock's killmails. Checks:
  * a ▶ on every row with kills (none on a hull only lost), closed;
  * ▶ opens that hull's kills under its row, newest first, 10: date and time in the browser's time zone, the victim's ship,
    class, pilot and corporation ticker, the players on the kill, the system, their weapon, who flew with them, zKillboard's
    value, the link to the kill; the row's hull isn't picked (the loss tabs stay); one open at a time;
  * Show 10 more: the rest of those already read, no request at all; then "all N ... in zKillboard's list", no button;
  * the switch: Small gang lists only small-gang kills ("10 of 12 small-gang Sabre kills");
  * a pilot with 60 kills (the dossier reads 50): Show 10 more reads the 10 older killmails from ESI (no zKillboard
    request) and lists the older Sabre kills; the dossier's own numbers don't change;
  * ESI failing on some older kills: what was read is listed, "N older kills couldn't be read (PILOT-09)" and Try again,
    which reads those once ESI answers;
  * 390 px: three lines per kill, ▶ and the links 40 px tall, nothing off the page; no page errors.
v2026.10.14.92 fails (no ▶).
"""
import sys, os, re, json
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone, timedelta
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from playwright.sync_api import sync_playwright
import sa_mocks as M

HTML = os.path.abspath(next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(HERE, '..', '..', 'index.html')))
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg); fails += not ok
TZ, TZ_H = 'Asia/Tokyo', 9
VESNA, KIRRA = M.PILOTS[M.DOSSIER_PILOT][0], M.PILOTS[M.LONG_PILOT][0]
NAME = {v: k for k, v in M.byname.items()}
SIZEW = {1: 'solo'}
def isk(v):   # the page's paIsk
    for n, u in ((1e12, 't'), (1e9, 'b'), (1e6, 'm'), (1e3, 'k')):
        if v >= n: return f"{Decimal(v / n).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}{u}"   # JS toFixed rounds an exact half up; Python's format to even
    return str(round(v))
def want_lines(cid, hull, size=None):
    out = []
    for k in M.HIST[cid]['kills']:
        km = M.KM[k]; players = [a for a in km['attackers'] if a.get('character_id')]
        me = next(a for a in players if a['character_id'] == cid)
        n = len(players); sz = 'solo' if n <= 1 else 'small' if n <= 10 else 'fleet'
        if NAME[me['ship_type_id']] != hull or (size and sz != size): continue
        t = datetime.strptime(km['killmail_time'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=TZ_H)))
        mates = {}
        for a in players:
            if a is not me: mates[NAME[a['ship_type_id']]] = mates.get(NAME[a['ship_type_id']], 0) + 1
        v = km['victim']
        out.append({'ts': t, 'id': k, 'day': f"{t.strftime('%b')} {t.day}", 'hm': t.strftime('%H:%M'), 'ship': NAME[v['ship_type_id']], 'pilot': M.PILOTS[v['character_id']][0],
                    'tk': M.ORGS[v['corporation_id']][2], 'n': n, 'sys': M.SYSTEMS[km['solar_system_id']], 'w': NAME[me['weapon_type_id']],
                    'with': ', '.join(f"{h}{f' ×{c}' if c > 1 else ''}" for h, c in sorted(mates.items(), key=lambda x: (-x[1], x[0]))) or 'alone',
                    'val': isk(M.VALUE[k]) if k in M.VALUE else '—'})
    return sorted(out, key=lambda x: (x['ts'], x['id']), reverse=True)   # newest first by time (the mock's IDs aren't in time order)
LINES = """(hid) => [...document.querySelectorAll(`#pdk-${hid} .pdk[data-pdk]`)].map(e => ({id: Number(e.dataset.pdk),
  t: e.querySelector('.pdk-t').innerText.replace(/\\s+/g, ' ').trim(), ship: e.querySelector('.pdk-v b').textContent,
  cls: e.querySelector('.pdk-v > span:first-child .pd-dim').textContent, who: e.querySelector('.pdk-v > span:last-child').innerText.replace(/\\s+/g, ' ').trim(),
  g: e.querySelector('.pdk-g').childNodes[1].textContent, sys: e.querySelector('.pdk-s').textContent, w: e.querySelector('.pdk-w').childNodes[0].textContent,
  x: e.querySelector('.pdk-x').textContent, val: e.querySelector('.pdk-val').textContent, href: e.querySelector('.pdk-l a').getAttribute('href')}))"""
MORE = """(hid) => { const m = document.querySelector(`#pdk-${hid} .pdk-more`); return m ? [!!m.querySelector('button'), m.querySelector('span:last-child').textContent] : null; }"""
def idle(pg):
    pg.wait_for_function("() => !document.querySelector('#fitBtn').disabled && document.querySelector('#pilotBusy').hidden", timeout=120000); pg.wait_for_timeout(400)
def analyze(pg, name):
    pg.click('#tabBtnPilot'); pg.fill('#pilotName', name); pg.fill('#manualShip', ''); pg.click('#fitBtn'); pg.wait_for_timeout(300); idle(pg)
def settled(pg):   # the Pilot Affiliation box's zKillboard stats request (v.87) comes after the analysis
    pg.wait_for_function("() => { const b = document.querySelector('#pilotAff'); return b.hidden || !b.querySelector('.busy-spin'); }", timeout=60000); pg.wait_for_timeout(300)
def names_in(pg, hid):
    pg.wait_for_function(f"() => [...document.querySelectorAll('#pdk-{hid} .pdk-v > span:last-child')].every(e => !e.textContent.startsWith('…') && e.querySelector('[data-org-tk]') && e.querySelector('[data-org-tk]').textContent)", timeout=30000)
    pg.wait_for_timeout(200)

with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []
    def new_ctx(w):
        ctx = b.new_context(viewport={'width': w, 'height': 1000}, timezone_id=TZ); ctx.on('page', lambda pg: pg.on('pageerror', lambda e: errs.append(str(e)))); M.route(ctx); return ctx
    ctx = new_ctx(1440); pg = ctx.new_page(); pg.goto('file://' + HTML)
    km_req = []
    pg.on('request', lambda r: km_req.append(r.url) if '/killmails/' in r.url else None)
    analyze(pg, VESNA)
    sab, ved, curse = M.byname['Sabre'], M.byname['Vedmak'], M.byname['Curse']
    st = pg.evaluate("() => [...document.querySelectorAll('#pilotDossier .pd-rh')].map(r => [r.querySelector('button.pd-row').dataset.pdHull, r.querySelector('[data-pd-exp]') ? r.querySelector('[data-pd-exp]').getAttribute('aria-expanded') : null])")
    check(all(e == 'false' for h, e in st if int(h) != curse) and dict(st)[str(curse)] is None and len(st) == 6, f'a closed ▶ on every row with kills, none on the Curse (only lost) {st}')
    tabs0 = pg.evaluate("() => document.querySelector('#fitResults').innerHTML.length")
    pg.click(f'#pilotDossier [data-pd-exp="{ved}"]'); pg.wait_for_timeout(300)
    vsel = pg.evaluate(f"() => [document.querySelector('[data-pd-hull=\"{ved}\"]').getAttribute('aria-pressed'), document.querySelector('[data-pd-exp=\"{ved}\"]').getAttribute('aria-expanded'), document.querySelectorAll('.pd-kills').length, document.querySelector('#fitResults').innerHTML.length]")
    check(vsel[0] == 'false' and vsel[1] == 'true' and vsel[2] == 1 and vsel[3] == tabs0, f'▶ opens the list without picking the hull (the loss tabs stay) {vsel}')
    # the Sabre's kills (All)
    settled(pg); M.ZKB_CALLS.clear(); km_req.clear()
    pg.click(f'#pilotDossier [data-pd-exp="{sab}"]'); pg.wait_for_timeout(300); names_in(pg, sab)
    W = want_lines(M.DOSSIER_PILOT, 'Sabre')
    got = pg.evaluate(LINES, sab)
    CLS = {'Rifter': 'Frigate', 'Caracal': 'Cruiser', 'Megathron': 'Battleship', 'Stabber': 'Cruiser'}
    exp = [{'id': w['id'], 't': f"{w['day']} {w['hm']} your time", 'ship': w['ship'], 'cls': CLS[w['ship']],
            'who': f"{w['pilot']} [{w['tk']}]", 'g': f"{w['n']:,}",   # v2026.10.31.3: the count alone, under "Fleet size"
             'sys': w['sys'], 'w': w['w'], 'x': w['with'], 'val': w['val'],
            'href': f"https://zkillboard.com/kill/{w['id']}/"} for w in W[:10]]
    one = pg.evaluate("() => document.querySelectorAll('.pd-kills').length")
    after = pg.evaluate(f"() => document.querySelector('#pdk-{sab}').previousElementSibling.querySelector('button.pd-row').dataset.pdHull")
    check(got == exp, f"the Sabre's kills: 10, newest first, every column as the killmails say" + next((f"\n      line {i}: page {g}\n      want {e}" for i, (g, e) in enumerate(zip(got, exp)) if g != e), f" ({len(got)} lines, want {len(exp)})"))
    check(one == 1 and after == str(sab), f'one list open at a time, under its own row ({one}, under {after})')
    check(pg.evaluate(MORE, sab) == [True, '10 of 14 Sabre kills'], f'Show 10 more, "10 of 14 Sabre kills" {pg.evaluate(MORE, sab)}')
    pg.click(f'#pdk-{sab} [data-pd-more]'); pg.wait_for_timeout(400); names_in(pg, sab)
    got = pg.evaluate(LINES, sab)
    check([g['id'] for g in got] == [w['id'] for w in W] and pg.evaluate(MORE, sab) == [False, "all 14 Sabre kills in zKillboard's list"] and not M.ZKB_CALLS and not km_req,
          f"Show 10 more: the rest, no button, no request at all ({len(got)} lines, {pg.evaluate(MORE, sab)}, {len(M.ZKB_CALLS)} zKillboard, {len(km_req)} killmails)")
    # the switch
    pg.click('#pilotDossier [data-pd-mode="small"]'); pg.wait_for_timeout(300); names_in(pg, sab)
    Ws = want_lines(M.DOSSIER_PILOT, 'Sabre', 'small')
    got = pg.evaluate(LINES, sab)
    check([g['id'] for g in got] == [w['id'] for w in Ws] and len(Ws) == 12 and pg.evaluate(MORE, sab) == [False, "all 12 small-gang Sabre kills in zKillboard's list"],
          f"the switch: only her 12 small-gang Sabre kills ({len(got)} lines, {pg.evaluate(MORE, sab)})")
    pg.click(f'#pilotDossier [data-pd-exp="{sab}"]'); pg.wait_for_timeout(200); pg.click(f'#pilotDossier [data-pd-exp="{sab}"]'); pg.wait_for_timeout(300)
    check(pg.evaluate(MORE, sab) == [True, '10 of 12 small-gang Sabre kills'] and len(pg.evaluate(LINES, sab)) == 10, f"closed and opened again: 10 again ({pg.evaluate(MORE, sab)})")
    # a pilot with 60 kills: older ones from ESI
    analyze(pg, KIRRA)
    head0 = pg.evaluate("() => document.querySelector('#pilotDossier .pd-head .ctx').textContent")
    check(pg.evaluate("() => document.querySelectorAll('.pd-kills').length") == 0, 'another pilot: no list open')
    settled(pg); M.ZKB_CALLS.clear(); km_req.clear()
    pg.click(f'#pilotDossier [data-pd-exp="{sab}"]'); pg.wait_for_timeout(300); names_in(pg, sab)
    Wl = want_lines(M.LONG_PILOT, 'Sabre')
    got = pg.evaluate(LINES, sab)
    check([g['id'] for g in got] == [w['id'] for w in Wl[:2]] and pg.evaluate(MORE, sab) == [True, '2 Sabre kills in their newest 50'], f"60 kills: the 2 Sabre kills among the newest 50, Show 10 more {pg.evaluate(MORE, sab)}")
    pg.click(f'#pdk-{sab} [data-pd-more]')
    pg.wait_for_function(f"() => {{ const b = document.querySelector('#pdk-{sab} .pdk-more'); return b && !b.querySelector('button[disabled]'); }}", timeout=60000); pg.wait_for_timeout(300); names_in(pg, sab)
    got = pg.evaluate(LINES, sab)
    head1 = pg.evaluate("() => document.querySelector('#pilotDossier .pd-head .ctx').textContent")
    check([g['id'] for g in got] == [w['id'] for w in Wl] and len(Wl) == 12 and pg.evaluate(MORE, sab) == [False, "all 12 Sabre kills in zKillboard's list"] and len(km_req) == 10 and not M.ZKB_CALLS and head1 == head0,
          f"Show 10 more reads the 10 older killmails from ESI (no zKillboard request) and lists the older Sabre kills; the dossier's numbers stay ({len(got)} lines, {len(km_req)} killmails, {len(M.ZKB_CALLS)} zKillboard, {head1!r})")
    ctx.close()
    # ESI failing on some older kills
    ctx = new_ctx(1440); pg = ctx.new_page()
    bad = set(sorted(M.LONG_KILLS)[:3])   # the 3 oldest
    ctx.route(re.compile(r'https://esi\.evetech\.net/.*/killmails/(\d+)/.*'), lambda rt: rt.fulfill(status=502, body='') if int(re.search(r'/killmails/(\d+)/', rt.request.url).group(1)) in bad else M.esi(rt))
    pg.goto('file://' + HTML); analyze(pg, KIRRA)
    pg.click(f'#pilotDossier [data-pd-exp="{sab}"]'); pg.wait_for_timeout(300)
    pg.click(f'#pdk-{sab} [data-pd-more]')
    pg.wait_for_function(f"() => {{ const b = document.querySelector('#pdk-{sab} .pdk-more'); return b && !b.querySelector('button[disabled]'); }}", timeout=60000); pg.wait_for_timeout(300)
    got = pg.evaluate(LINES, sab); mo = pg.evaluate(MORE, sab)
    check(len(got) == 9 and mo == [True, "9 Sabre kills in their newest 57 · 3 older kills couldn't be read (PILOT-09)"] and pg.inner_text(f'#pdk-{sab} [data-pd-more]') == 'Try again',
          f'ESI failing on 3 older kills: the other 9 listed, PILOT-09 said, Try again ({len(got)} lines, {mo})')
    bad.clear()   # ESI answers again
    pg.click(f'#pdk-{sab} [data-pd-more]')
    pg.wait_for_function(f"() => {{ const b = document.querySelector('#pdk-{sab} .pdk-more'); return b && !b.querySelector('button[disabled]'); }}", timeout=60000); pg.wait_for_timeout(300)
    got = pg.evaluate(LINES, sab); mo = pg.evaluate(MORE, sab)
    check(len(got) == 12 and mo == [False, "all 12 Sabre kills in zKillboard's list"], f'Try again reads those 3: all 12 listed ({len(got)} lines, {mo})')
    ctx.close()
    # phone
    ctx = new_ctx(390); pg = ctx.new_page(); pg.goto('file://' + HTML); analyze(pg, VESNA)
    pg.click(f'#pilotDossier [data-pd-exp="{sab}"]'); pg.wait_for_timeout(300); names_in(pg, sab)
    L = pg.evaluate(f"""() => {{ const k = document.querySelector('#pdk-{sab} .pdk[data-pdk]'), r = (s) => k.querySelector(s).getBoundingClientRect();
      const tops = new Set(['.pdk-v', '.pdk-g', '.pdk-w'].map(s => Math.round(r(s).top)));   // the link sits beside the first line
      return [tops.size, document.querySelector('[data-pd-exp="{sab}"]').getBoundingClientRect().height, r('.pdk-l a').height, document.documentElement.scrollWidth,
        [...document.querySelectorAll('#pdk-{sab} *')].filter(e => {{ const b = e.getBoundingClientRect(); return e.checkVisibility() && b.width && (b.right > innerWidth + 1 || b.left < -1); }}).length,
        k.querySelector('.pdk-v > span:last-child').innerText]; }}""")
    check(L[0] == 3 and L[1] >= 40 and L[2] >= 32 and L[3] <= 390 and L[4] == 0 and W[0]['hm'] in L[5], f'390 px: three lines per kill (time with the pilot), ▶ 40 px and the zK icon 32 px tall, nothing off the page {L}')
    ctx.close()
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
