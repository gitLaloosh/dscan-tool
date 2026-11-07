"""zKillboard's kill feed can't be read: said plainly, on every tab (v2026.11.06.1, build queue 016; Project doc
roadmap/outage-notices-plan.md section 7; the owner's mockup scene e7_feed_unreadable, Claude outputs/outage_notices_mockup.html).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/feed_down_check.py [index.html]   -> 'FAILURES: N' (must be 0)

2026-11-06 zKillboard's R2Z2 sent 'Access-Control-Allow-Origin: *, *' (the header twice), so every browser threw its answers away
and Intel showed an empty feed with the reason only in a long note. Playwright's route.fulfill() skips the browser's CORS check, so
R2Z2 is a real HTTPS stand-in here (a self-signed certificate, the browser's resolver mapping r2z2.zkillboard.com to it): the
browser checks its header for real. Made-up kills only. Checks:
  * at load, the header doubled: nothing after the first and the second sequence.json read; from the third, the strip under the
    header (on every tab), the Feed note, "Kills down" in the gauge, INTEL-06 on Intel's status line, the profile's mark not
    working; never read since the page opened, so the words add "or something in this browser blocking it"; the reader's own
    waits (30 s, then 60 s, then 120 s) and one request per try, nothing extra; no sideways scroll at 390 px;
  * fixed: everything goes at the next answer the page can read;
  * live, then the header missing: unreadable kill files alone (normal, "not there yet", LESSON #89) show nothing; three
    sequence.json reads do, without the blocker words (the feed was read before);
  * reading back when the header breaks: the published kills that can't be read count;
  * offline: nothing shown (not zKillboard's side); online again: shown; written only when the text changes;
  * Intel off: the strip goes, no requests.
The reader's waits are skipped here (its next read moved to now), never shortened in the page.
"""
import sys, os, time, re, json, ssl, threading, subprocess, tempfile
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
_src = open(os.path.join(HERE, 'intel_kills_check.py'), encoding='utf-8').read()
_src = _src[:_src.index('\nwith sync_playwright() as p:')]   # the line itself, not the same words in its own exec line
NS = {'__file__': os.path.join(HERE, 'intel_kills_check.py'), '__name__': 'intel_kills_prefix'}
exec(compile(_src, 'intel_kills_check.py (first part)', 'exec'), NS)
globals().update({k: v for k, v in NS.items() if not k.startswith('__') and k not in ('check', 'fails')})
check = NS['check']
from playwright.sync_api import sync_playwright

# ---- the R2Z2 stand-in: real HTTPS, so the browser checks the permission header itself ----
MODE = {'acao': 'ok'}   # ok: '*'; double: the header twice ('*, *' to the browser); none: no header
HITS = []               # (time, path)
NEWEST = {'seq': 7000}
class R2(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        path = self.path; HITS.append((time.time(), path))
        if path.endswith('/sequence.json'): code, body = 200, json.dumps({'sequence': NEWEST['seq']})
        else:
            m = re.search(r'/ephemeral/(\d+)\.json$', path); n = int(m.group(1)) if m else -1
            code, body = (200, json.dumps(dict(filler(n), sequence_id=n))) if 0 < n <= NEWEST['seq'] else (404, '')
        self.send_response(code); self.send_header('Content-Type', 'application/json')
        if MODE['acao'] in ('ok', 'double'): self.send_header('Access-Control-Allow-Origin', '*')
        if MODE['acao'] == 'double': self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body.encode())
TMP = tempfile.mkdtemp()
KEY, CRT = os.path.join(TMP, 'k.pem'), os.path.join(TMP, 'c.pem')
subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', KEY, '-out', CRT, '-days', '1', '-subj', '/CN=r2z2.zkillboard.com'], check=True, capture_output=True)
SRV = ThreadingHTTPServer(('127.0.0.1', 0), R2)
sc = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); sc.load_cert_chain(CRT, KEY); SRV.socket = sc.wrap_socket(SRV.socket, server_side=True)
threading.Thread(target=SRV.serve_forever, daemon=True).start()
PORT = SRV.server_address[1]

STRIP = "() => (document.getElementById('sysStrip') || {}).textContent || ''"
STATE = """() => ({strip: (document.getElementById('sysStrip') || {}).textContent || '', shown: !!(document.getElementById('sysStrip') || {}).offsetHeight,
  why: (document.querySelector('#itFeedList [data-it-why]') || {}).textContent || '', gauge: (document.getElementById('bgSegs') || {}).textContent || '',
  stop: [...document.querySelectorAll('#bgSegs .bg-seg.stop')].map(x => x.textContent), status: (document.querySelector('[data-it-status]') || {}).textContent || '',
  mark: itMarkState(), blk: it.kf ? it.kf.blk : -1, busy: it.kf ? it.kf.busy : false, wait: it.kf ? it.kf.waitUntil - Date.now() : 0, head: it.kf ? it.kf.head : null,
  seq: it.kf ? it.kf.seq : null, kfnote: !!document.querySelector('[data-it-kfnote]'), sw: document.documentElement.scrollWidth, vw: innerWidth})"""

with sync_playwright() as p:
    # the stand-in on this machine: the resolver sends r2z2.zkillboard.com to it, past any proxy this machine has, and Chromium's
    # private-network rule (a page may not reach a loopback address) is turned off for it; everything else is answered by routes
    b = p.chromium.launch(args=[f'--host-resolver-rules=MAP r2z2.zkillboard.com 127.0.0.1:{PORT}',
        '--disable-features=BlockInsecurePrivateNetworkRequests,PrivateNetworkAccessSendPreflights,PrivateNetworkAccessRespectPreflightResults,LocalNetworkAccessChecks'],
        proxy={'server': os.environ.get('HTTPS_PROXY') or 'http://127.0.0.1:9', 'bypass': 'r2z2.zkillboard.com'})
    errs = []
    def start(w):
        ctx = b.new_context(viewport={'width': w, 'height': 1000}, ignore_https_errors=True)
        ctx.on('page', lambda pg: pg.on('pageerror', lambda e: errs.append(str(e))))
        ctx.add_init_script(FS)
        ctx.route(re.compile(r'https://esi\.evetech\.net/.*'), esi2)
        ctx.route(re.compile(r'https://zkillboard\.com/.*'), M.zkb)
        ctx.route(re.compile(r'https://(images\.evetech\.net|fonts\.).*'), lambda r: r.fulfill(status=404, body=''))
        pg = ctx.new_page(); pg.goto('file://' + HTML)
        pg.evaluate("(s) => { localStorage.setItem('dscanSide', JSON.stringify(s)); localStorage.setItem('dscanIntel', JSON.stringify({channels: ['region.intel'], me: 95000001, range: 3, killRange: 3, sound: false, notify: false, forget: 15, hideFriendly: true})); }", SIDE)
        pg.reload(); pg.wait_for_timeout(400)
        setup_logs(pg); pg.click('#tabBtnIntel'); pg.click('[data-it-act="folder"]'); pg.wait_for_timeout(300)
        return ctx, pg
    def settle(pg, t=15):   # the reader idle (not mid-read)
        for _ in range(t * 4):
            if not pg.evaluate("() => it.kf && it.kf.busy"): return
            pg.wait_for_timeout(250)
    def skip(pg, live_seq=False):   # its next read now (the wait skipped, not shortened); live_seq: a minute with no kill read
        settle(pg)
        pg.evaluate("(ls) => { if(ls){ it.kf.lastGot = Date.now() - 61000; it.kf.seqAt = 0; } it.kf.waitUntil = 0; itKillPump(); }", live_seq)
        pg.wait_for_timeout(700); settle(pg)
    def seqs(h0): return [q for _, q in HITS[h0:] if q.endswith('/sequence.json')]

    # ---- 1. at load, the header doubled; 390 px ----
    MODE['acao'] = 'double'; HITS.clear()
    ctx, pg = start(390)
    pg.click('#intelSwLabel'); pg.wait_for_timeout(1500); settle(pg)
    s1 = pg.evaluate(STATE); h1 = len(HITS)
    skip(pg); s2 = pg.evaluate(STATE); h2 = len(HITS)
    check(s1['blk'] == 1 and not s1['strip'] and not s1['why'] and 'down' not in s1['gauge'] and s2['blk'] == 2 and not s2['strip'] and not s2['why'] and not s1['kfnote'],
          f'the first and the second unreadable sequence.json: nothing shown yet ({s1["blk"]}, {s2["blk"]}, {s1["strip"]!r}, {s2["strip"]!r})')
    check(25000 < s1['wait'] <= 30500 and 55000 < s2['wait'] <= 60500, f"the reader's own waits after each failure: 30 s, then 60 s ({s1['wait']}, {s2['wait']})")
    skip(pg); s3 = pg.evaluate(STATE); h3 = len(HITS)
    check(s3['blk'] == 3 and s3['strip'] == "zKillboard's kill feed can't be read right now (a problem on zKillboard's side, or something in this browser blocking it). New kills will show when it's fixed. (INTEL-06)",
          f'the third: the strip, with the blocker words (never read since the page opened) ({s3["strip"]!r})')
    check(s3['why'] == "No new kills: zKillboard's kill feed can't be read right now (a problem on zKillboard's side, or something in this browser blocking it).", f'the Feed note ({s3["why"]!r})')
    check(any(x.strip().endswith('down') for x in s3['stop']) and 'INTEL-06' in s3['status'] and s3['mark'] == 'broken' and not s3['kfnote'],
          f'"Kills down" in the gauge (stop style), INTEL-06 on the status line, the profile\'s mark not working, no long note ({s3["stop"]}, {s3["status"][-80:]!r}, {s3["mark"]})')
    check(115000 < s3['wait'] <= 120500 and [len(seqs(0)), h1, h2 - h1, h3 - h2] == [3, 1, 1, 1], f'one request per try, sequence.json only, the third wait 120 s ({len(seqs(0))}, {h1}, {h2 - h1}, {h3 - h2}, {s3["wait"]})')
    check(s3['shown'] and s3['sw'] <= s3['vw'], f'390 px: the strip shown, no sideways scroll ({s3["sw"]} / {s3["vw"]})')
    pg.screenshot(path=os.environ.get('FEED_DOWN_SHOT', '/tmp/feed_down_390.png'))
    pg.click('#tabBtnPilot'); pg.wait_for_timeout(300)
    check(pg.evaluate("() => !!document.getElementById('sysStrip').offsetHeight"), 'on another tab (Pilot Analyzer): the strip still shown')
    # written only when the text changes
    pg.evaluate("() => { window.__sw = 0; new MutationObserver((l) => { window.__sw += l.length; }).observe(document.getElementById('sysStrip'), {childList: true, subtree: true, characterData: true}); }")
    pg.click('#tabBtnIntel'); pg.evaluate("() => { for(let i = 0; i < 5; i++){ itRender(true); bgPaintNow(); } }"); pg.wait_for_timeout(1200)
    check(pg.evaluate("() => window.__sw") == 0, f'the strip written only when its text changes ({pg.evaluate("() => window.__sw")} writes over 5 redraws)')
    # offline: not zKillboard's side
    ctx.set_offline(True); pg.wait_for_timeout(400)
    off = pg.evaluate(STATE)
    ctx.set_offline(False); pg.wait_for_timeout(400)
    on = pg.evaluate(STATE)
    check(not off['strip'], f'offline: no strip ({off["strip"]!r})')
    check(bool(on['strip']), f'online again: the strip back ({on["strip"]!r})')
    # ---- 2. fixed: all of it goes at the next readable answer ----
    MODE['acao'] = 'ok'; skip(pg)
    f = pg.evaluate(STATE)
    check(not f['strip'] and not f['why'] and 'down' not in f['gauge'] and 'INTEL-06' not in f['status'] and f['blk'] == 0 and f['mark'] != 'broken',
          f'fixed: the strip, the Feed note, "Kills down" and INTEL-06 go at the next answer ({f["strip"]!r}, {f["gauge"]!r}, {f["blk"]})')
    ctx.close()

    # ---- 3. live, then the header missing ----
    MODE['acao'] = 'ok'; HITS.clear(); NEWEST['seq'] = 7000
    ctx, pg = start(1440)
    pg.click('#intelSwLabel')
    for _ in range(240):
        if pg.evaluate("() => it.kf && it.kf.head && !it.kf.busy"): break
        pg.wait_for_timeout(500)
    live = pg.evaluate("() => it.kf.head")
    MODE['acao'] = 'none'; h0 = len(HITS)
    for _ in range(3):   # the next kill isn't readable: "not there yet", asked again later; a kill was read recently, so no sequence.json
        settle(pg); pg.evaluate("() => { it.kf.lastGot = Date.now(); it.kf.waitUntil = 0; itKillPump(); }"); pg.wait_for_timeout(700)
    settle(pg); k = pg.evaluate(STATE)
    kills_only = [q for _, q in HITS[h0:]]
    check(live and len(kills_only) >= 3 and not seqs(h0) and k['blk'] == 0 and not k['strip'],
          f'live: unreadable kill files alone (normal, "not there yet") show nothing ({len(kills_only)} reads, {k["blk"]}, {k["strip"]!r})')
    for _ in range(3): skip(pg, live_seq=True)
    s = pg.evaluate(STATE)
    check(s['strip'] == "zKillboard's kill feed can't be read right now (a problem on zKillboard's side). New kills will show when it's fixed. (INTEL-06)" and len(seqs(h0)) == 3,
          f'live, then three unreadable sequence.json reads: the strip, without the blocker words (the feed was read before) ({s["strip"]!r}, {len(seqs(h0))})')
    MODE['acao'] = 'ok'; skip(pg, live_seq=True)
    check(not pg.evaluate(STRIP), 'fixed while live: the strip goes')
    # Intel off: the strip goes, nothing sent
    MODE['acao'] = 'none'
    for _ in range(3): skip(pg, live_seq=True)
    was = pg.evaluate(STRIP)
    pg.click('#intelSwLabel'); pg.wait_for_timeout(500); n0 = len(HITS); pg.wait_for_timeout(4000)
    check(bool(was) and not pg.evaluate(STRIP) and len(HITS) == n0, f'Intel off: the strip goes, no requests ({bool(was)}, {len(HITS) - n0})')
    ctx.close()

    # ---- 4. reading back when the header breaks: published kills that can't be read count ----
    MODE['acao'] = 'ok'; HITS.clear()
    ctx, pg = start(1440)
    pg.click('#intelSwLabel')
    for _ in range(40):
        if pg.evaluate("() => it.kf && it.kf.seq !== null && !it.kf.head"): break
        pg.wait_for_timeout(250)
    MODE['acao'] = 'double'; h0 = len(HITS)
    for _ in range(4):
        skip(pg)
        if pg.evaluate("() => it.kf.blk >= 3"): break
    r = pg.evaluate(STATE)
    # v2026.11.06.6 (build queue 019): an unreadable published kill is asked once more, then sequence.json is read to tell a gap from a dead
    # feed; here it can't be read either, so the pass counts as today (nothing read past)
    check(not r['head'] and r['blk'] >= 3 and bool(r['strip']), f'reading back, the published kills unreadable: counted, the strip shown ({r["head"]}, {r["blk"]}, {r["strip"]!r})')
    ctx.close()
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
SRV.shutdown()
print(f"FAILURES: {NS['NS']['fails'] if 'NS' in NS else NS.get('fails')}")   # the counter lives in intel_check's namespace (intel_kills_check's NS)
