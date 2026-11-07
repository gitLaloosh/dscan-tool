"""The page with its Content-Security-Policy ON (v2026.11.07.3, build queue 023; Project doc roadmap/sso-hardening-plan.md; LESSON #145).

    PYFA_SRC=/path/to/pyfa python3 -I tools/page_checks/csp_check.py [index.html]   -> 'FAILURES: N' (must be 0)

Every other page check opens the page with bypass_csp=True: they test behaviour, and they need eval (run_async), modified copies
and mutants, which the policy rightly refuses. This is the one check that keeps the policy on, so the policy itself is tested
here and nowhere else. The page is served over HTTP from its own folder (as GitHub Pages serves it, so 'self' and the referrer
behave as they will live); ESI, zKillboard, R2Z2 and EVE's images are the page checks' stand-ins (made-up data, no network).
  * a tour with the policy on: every tab, the Fit Analyzer with a fit, the Pilot Analyzer (zKillboard), Local, the profile and
    My Fits panels, and Intel running (its timer worker, reports read from made-up logs): 0 policy violations, no page errors;
  * an inline handler injected the way a missed escape would let it in (<img onerror>) is refused: it doesn't run, and the
    browser reports a script-src-attr violation;
  * each data-imgfail kind does what its inline handler did (hide, remove, none, next, next-block, initials), with EVE's
    images answering 404; the initials are text, never HTML;
  * the site's own icons load under the policy ('self' in img-src, v2026.11.07.4);
  * no request carries a Referer (<meta name="referrer" content="no-referrer">);
  * a copy with Windows line endings (CRLF) still runs: the browser hashes the script after HTML's newline normalization, and
    so does tools/csp_hash.py.
v2026.11.07.2 fails (no policy: the injected handler runs). A stale hash fails (nothing runs).
"""
import sys, os, re, json, threading, functools, http.server, socketserver, tempfile, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
_src = open(os.path.join(HERE, 'intel_check.py'), encoding='utf-8').read()
_src = _src[:_src.index('with sync_playwright() as p:')]
NS = {'__file__': os.path.join(HERE, 'intel_check.py'), '__name__': 'intel_check_prefix'}
exec(compile(_src, 'intel_check.py (first part)', 'exec'), NS)
globals().update({k: v for k, v in NS.items() if not k.startswith('__') and k not in ('check', 'fails')})
check = NS['check']
from playwright.sync_api import sync_playwright

PAGE = os.path.abspath(HTML)
COLLECT = """window.__csp = []; document.addEventListener('securitypolicyviolation', (e) => window.__csp.push(e.effectiveDirective + ' ' + (e.blockedURI || '') + ' ' + (e.sample || '').slice(0, 40)));"""
FIT = "[Vexor, Brawl]\nDamage Control II\nMedium Armor Repairer II\n\n10MN Afterburner II\n\nDrone Link Augmentor I\n\nHammerhead II x5\n"

class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
def serve(folder):
    srv = socketserver.ThreadingTCPServer(('127.0.0.1', 0), functools.partial(_Quiet, directory=folder))
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f'http://127.0.0.1:{srv.server_address[1]}/'

REFERERS = []
def make_ctx(b):
    ctx = b.new_context(viewport={'width': 1440, 'height': 1000})   # no bypass_csp: the policy is what's under test
    ctx.add_init_script(COLLECT); ctx.add_init_script(FS); route(ctx)
    ctx.on('request', lambda r: REFERERS.append(r.headers.get('referer')) if not r.url.startswith('http://127.0.0.1') else None)
    return ctx

srv, base = serve(os.path.dirname(PAGE))
tmp = tempfile.mkdtemp(prefix='csp_crlf_')
try:
    with sync_playwright() as p:
        b = p.chromium.launch(); errs = []
        ctx = make_ctx(b); pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
        url = base + os.path.basename(PAGE)
        pg.goto(url); pg.evaluate("(s) => { localStorage.setItem('dscanSide', JSON.stringify(s)); localStorage.removeItem('dscanIntel'); }", SIDE); pg.reload()
        try: runs = bool(pg.wait_for_function("() => typeof switchTab === 'function' && typeof escapeHtml === 'function'", timeout=15000))
        except Exception: runs = False   # a stale hash: the browser refuses the script, nothing runs
        if not runs:
            check(False, f'the page runs with its policy on: it does not (a stale script hash? tools/csp_hash.py --check) {pg.evaluate("() => window.__csp")[:2]}')
            print(f"FAILURES: {NS['fails']}"); srv.shutdown(); sys.exit(1)
        meta = pg.evaluate("() => [(document.querySelector('meta[http-equiv=\"Content-Security-Policy\"]') || {}).content || '', (document.querySelector('meta[name=referrer]') || {}).content]")
        check(runs and "script-src 'sha256-" in meta[0] and meta[1] == 'no-referrer', f'the page runs with its policy on (served over HTTP), the referrer meta present {meta[1]!r}')
        # ---- the tour ----
        for tab in ('pilot', 'fleet', 'dscan', 'fit', 'intel'):
            pg.evaluate("(t) => switchTab(t)", tab); pg.wait_for_timeout(400)
        pg.evaluate("() => switchTab('fit')"); pg.fill('#fitAnalyzerInput', FIT); pg.click('#fitAnalyzerBtn'); pg.wait_for_timeout(500)
        pg.wait_for_function("() => !document.querySelector('#fitAnalyzerResults .fit-card-busy')", timeout=60000); pg.wait_for_timeout(800)
        fitok = pg.evaluate("() => (document.querySelector('#fitAnalyzerResults') || {}).innerText.length > 200")
        pg.click('#tabBtnPilot'); pg.fill('#pilotName', 'Test Pilot'); pg.click('#fitBtn'); pg.wait_for_timeout(6000)
        pg.evaluate("() => switchTab('dscan')"); pg.wait_for_timeout(300)
        pg.fill('#localInput', '\n'.join(M.LOCAL.split('\n')[:12])); pg.click('#analyzeBtn'); pg.wait_for_timeout(5000)
        pg.evaluate("() => openProfile()"); pg.wait_for_timeout(600); pg.keyboard.press('Escape')
        pg.evaluate("() => openMyShipPanel(undefined, {})"); pg.wait_for_timeout(600); pg.keyboard.press('Escape')
        # Intel: made-up logs, its timer worker running, reports read
        pg.click('#tabBtnIntel'); setup_logs(pg); pg.click('[data-it-act="folder"]'); pg.wait_for_timeout(500)
        pg.check('[data-it-chan="region.intel"]'); pg.check(f'[data-it-me="{MAIN}"]'); pg.click('#intelSwLabel'); pg.wait_for_timeout(4000)
        intel = pg.evaluate("() => [it.on, it.ticker && it.ticker.kind, document.querySelectorAll('#intelPanel .it-fd').length]")
        v = pg.evaluate("() => window.__csp")
        check(fitok and intel[0] and intel[1] == 'worker' and intel[2] >= 1 and not v and not errs,
              f'a tour with the policy on: every tab, a fit, a pilot, Local, the profile and My Fits, Intel with its worker: no violations, no page errors {v[:4]} {errs[:2]} fit {fitok} intel {intel}')
        # ---- an injected inline handler is refused ----
        pg.evaluate("() => { const d = document.createElement('div'); d.innerHTML = '<img src=\"data:,x\" onerror=\"window.__ran = 1\">'; document.body.appendChild(d); }"); pg.wait_for_timeout(600)
        ran = pg.evaluate("() => window.__ran === 1"); v2 = pg.evaluate("() => window.__csp")
        check(not ran and any(x.startswith('script-src-attr') for x in v2), f'an injected <img onerror> is refused: it ran {ran}, the violation {v2[:2]}')
        # ---- each data-imgfail kind does what its handler did ----
        pg.evaluate("""() => { const d = document.createElement('div'); d.id = 'imgfailT'; const src = 'https://images.evetech.net/types/1/icon?size=32';
          d.innerHTML = ['hide', 'remove', 'none'].map(k => `<span class="k-${k}"><img data-imgfail="${k}" src="${src}&${k}"></span>`).join('')
            + `<span class="k-next"><img data-imgfail="next" src="${src}&n"><b style="display:none">fb</b></span>`
            + `<span class="k-nextb"><img data-imgfail="next-block" src="${src}&nb"><i style="display:none">fb</i></span>`
            + `<span class="k-ini"><img data-imgfail="initials" data-initials="${escapeHtml("O'<b>")}" src="${src}&i"></span>`;
          document.body.appendChild(d); }""")
        pg.wait_for_timeout(1500)
        k = pg.evaluate("""() => { const q = (s) => document.querySelector('#imgfailT ' + s);
          return {hide: q('.k-hide img') && q('.k-hide img').style.visibility, remove: !q('.k-remove img'), none: q('.k-none img') && q('.k-none img').style.display,
            next: [q('.k-next img').style.display, q('.k-next b').style.display], nextb: [q('.k-nextb img').style.display, q('.k-nextb i').style.display],
            ini: [!q('.k-ini img'), q('.k-ini .pf-ini') && q('.k-ini .pf-ini').textContent, !q('.k-ini b')]}; }""")
        check(k == {'hide': 'hidden', 'remove': True, 'none': 'none', 'next': ['none', ''], 'nextb': ['none', 'block'], 'ini': [True, "O'<b>", True]},
              f'each data-imgfail kind as its handler did: hide, remove, none, next, next-block, initials (as text) {k}')
        v3 = [x for x in pg.evaluate("() => window.__csp") if not x.startswith('script-src-attr')]
        check(not v3, f'... and none of them is a violation {v3[:3]}')
        # v2026.11.07.4 (build queue 022): the site's own icons load under the policy ('self' in img-src)
        ic = pg.evaluate("""async () => { const one = (h) => new Promise((ok) => { const i = new Image(); i.onload = () => ok([h, i.naturalWidth]); i.onerror = () => ok([h, 0]); i.src = h; });
          return Promise.all(['favicon.svg', 'favicon-32.png', 'apple-touch-icon.png'].map(one)); }""")
        v4 = [x for x in pg.evaluate("() => window.__csp") if x.startswith('img-src')]
        check(all(n > 0 for _, n in ic) and not v4, f'the site\'s icons (favicon.svg, favicon-32.png, apple-touch-icon.png) load under the policy {ic} {v4[:2]}')
        sent = [r for r in REFERERS if r]
        check(REFERERS and not sent, f'no request carries a Referer ({len(REFERERS)} requests, {len(sent)} with one: {sent[:2]})')
        check(not errs, f'no page errors {errs[:3]}')
        # ---- a Windows checkout (CRLF line endings) still runs ----
        raw = open(PAGE, 'rb').read().decode('utf-8').replace('\r\n', '\n').replace('\n', '\r\n')
        open(os.path.join(tmp, 'index.html'), 'wb').write(raw.encode('utf-8'))
        srv2, base2 = serve(tmp)
        pg2 = ctx.new_page(); e2 = []; pg2.on('pageerror', lambda e: e2.append(str(e)[:160])); pg2.goto(base2 + 'index.html'); pg2.wait_for_timeout(2500)
        crlf = pg2.evaluate("() => [typeof switchTab === 'function', window.__csp.filter(x => x.startsWith('script-src')).length]")
        check(crlf == [True, 0], f'a copy with CRLF line endings runs (the browser hashes after newline normalization, as csp_hash.py does) {crlf} {e2[:2]}')
        srv2.shutdown(); b.close()
finally:
    srv.shutdown(); shutil.rmtree(tmp, ignore_errors=True)
print(f"FAILURES: {NS['fails']}")
sys.exit(1 if NS['fails'] else 0)
