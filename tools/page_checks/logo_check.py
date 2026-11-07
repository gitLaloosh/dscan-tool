"""The Threat Vector logo in the header, and the site's icons (v2026.11.07.4, build queue 022; Project doc roadmap/logo-header-plan.md;
mockup Claude outputs/logo_header_mockup.html).

    python3 -I tools/page_checks/logo_check.py [index.html]   -> 'FAILURES: N' (must be 0)

The owner, 2026-11-06: "R37 is the one", "Left of the title", "align the top of the T in Threat Vector with the top of the T in the
logo please"; 2026-11-07: "No tile". Checks, at 1440, 390 and 320 px:
  * the logo is an inline SVG inside .hero-title-row, before the h1, aria-hidden and not focusable (decoration: the h1 carries the name);
  * its colours are the page's tokens (cyan orbits, amber V and dot, the text colour's T), no tile;
  * the top of the logo's T and the top of the title's T are within 1 px (inked rows of a 4x screenshot, the mockup's pxcheck.py);
  * the title row doesn't overflow, the title stays on one line, the page has no sideways scroll;
  * the icon links (favicon.svg, favicon-32.png, apple-touch-icon.png) point at files that exist, and the PNGs are 32 and 180 px.
"""
import sys, os, re, io, pathlib, struct
HERE = os.path.dirname(os.path.abspath(__file__))
from playwright.sync_api import sync_playwright
HTML = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', '..', 'index.html'))
fails = 0
def check(ok, msg):
    global fails
    print(('OK   ' if ok else 'FAIL ') + msg)
    if not ok: fails += 1

def ink_top(png, x0, x1):
    """The first row (from the top) with a light pixel (all channels over 185) between x0 and x1, in that image's pixels."""
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert('RGB'); px = im.load()
    for y in range(im.height):
        for x in range(max(0, x0), min(im.width, x1)):
            r, g, b = px[x, y]
            if min(r, g, b) > 185: return y
    return None

with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    for w in (1440, 390, 320):
        pg = b.new_page(bypass_csp=True, viewport={'width': w, 'height': 400}, device_scale_factor=4); pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
        pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('file:') else r.abort())
        pg.goto(pathlib.Path(HTML).as_uri()); pg.wait_for_timeout(600)
        st = pg.evaluate("""() => { const l = document.querySelector('.hero-logo'), h = document.querySelector('.hero-title-row h1'), row = document.querySelector('.hero-title-row');
          const fill = (s) => { const e = l && l.querySelector(s); return e ? getComputedStyle(e).fill : null; };
          const root = getComputedStyle(document.documentElement), tok = (n) => root.getPropertyValue(n).trim();
          return {inRow: !!(l && l.closest('.hero-title-row')), before: !!(l && h && (l.compareDocumentPosition(h) & Node.DOCUMENT_POSITION_FOLLOWING)),
            hidden: l && l.getAttribute('aria-hidden'), focusable: l && l.getAttribute('focusable'), tile: l ? l.querySelectorAll('rect').length : -1,
            orbit: l && getComputedStyle(l.querySelector('.lg-orbit')).stroke, v: fill('.lg-v'), t: fill('.lg-t'), dot: fill('.lg-dot'),
            tok: [tok('--cyan'), tok('--amber'), tok('--text')],
            rowOver: row.scrollWidth - row.clientWidth, oneLine: h.getBoundingClientRect().height < parseFloat(getComputedStyle(h).fontSize) * 1.6,
            pageOver: document.documentElement.scrollWidth - innerWidth,
            lb: l.getBoundingClientRect().toJSON(), hb: h.getBoundingClientRect().toJSON(), rowH: row.getBoundingClientRect().height}; }""")
        hexrgb = lambda h: 'rgb(%d, %d, %d)' % tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) if h.startswith('#') and len(h) == 7 else h
        tk = [hexrgb(x) for x in st['tok']]
        if w == 1440:
            check(st['inRow'] and st['before'] and st['hidden'] == 'true' and st['focusable'] == 'false',
                  f'the logo: inline in the title row, before the h1, aria-hidden, not focusable {[st["inRow"], st["before"], st["hidden"], st["focusable"]]}')
            check(st['tile'] == 0 and [st['orbit'], st['v'], st['t'], st['dot']] == [tk[0], tk[1], tk[2], tk[1]],
                  f'its colours are the tokens (orbits --cyan, V and dot --amber, T --text) and no tile (the owner: "No tile") {[st["orbit"], st["v"], st["t"], st["dot"]]} {tk}')
        lb, hb = st['lb'], st['hb']
        y0 = int(min(lb['y'], hb['y']) - 6); y1 = int(max(lb['y'] + lb['height'], hb['y'] + hb['height']) + 4)
        x0 = int(lb['x'] - 4); x1 = int(hb['x'] + 120)
        png = pg.screenshot(clip={'x': x0, 'y': y0, 'width': x1 - x0, 'height': y1 - y0})
        lx = int((lb['x'] - x0) * 4); lw = int(lb['width'] * 4); hx = int((hb['x'] - x0) * 4)
        lt = ink_top(png, lx, lx + lw); tt = ink_top(png, hx, (x1 - x0) * 4)
        diff = None if lt is None or tt is None else abs(tt - lt) / 4
        check(diff is not None and diff <= 1, f'{w} px: the top of the logo\'s T and the title\'s T within 1 px ({diff} px; logo {lb["width"]:.0f} px wide)')
        check(st['rowOver'] <= 0 and st['oneLine'] and st['pageOver'] <= 0, f'{w} px: the title row fits, the title on one line, no sideways scroll (row height {st["rowH"]:.0f} px) {[st["rowOver"], st["oneLine"], st["pageOver"]]}')
        pg.close()
    # the icon links point at files that exist; the PNGs are the right size
    src = open(HTML, encoding='utf-8').read()
    links = re.findall(r'<link rel="(icon|apple-touch-icon)" href="([^"]+)"', src)
    folder = os.path.dirname(HTML)
    def size(f):
        with open(f, 'rb') as fh: h = fh.read(24)
        return struct.unpack('>II', h[16:24]) if h[:8] == b'\x89PNG\r\n\x1a\n' else None
    have = {h: os.path.exists(os.path.join(folder, h)) for _, h in links}
    sizes = {h: size(os.path.join(folder, h)) for h in have if h.endswith('.png') and have[h]}
    check(sorted(h for _, h in links) == ['apple-touch-icon.png', 'favicon-32.png', 'favicon.svg'] and all(have.values()) and sizes == {'favicon-32.png': (32, 32), 'apple-touch-icon.png': (180, 180)},
          f'the icon links point at files that exist, the PNGs 32 and 180 px {have} {sizes}')
    check(not errs, f'no page errors {errs[:3]}')
    b.close()
print(f'FAILURES: {fails}')
sys.exit(1 if fails else 0)
