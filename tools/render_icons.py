"""The site's tab and home-screen icons, rendered from the logo's SVGs (v2026.11.07.4, build queue 022; Project doc
roadmap/logo-header-plan.md). No new dependency: the pre-installed Playwright draws the SVG and saves the PNG.

    python3 -I tools/render_icons.py          -> favicon-32.png and apple-touch-icon.png at the repo root (from favicon.svg and
                                                 img/logo/threat-vector-logo.svg)
    python3 -I tools/render_icons.py --check  -> fails when a PNG is missing or isn't the size it should be

favicon.svg (the monogram without orbits: at 16 px the orbits become an X) is the tab icon, with favicon-32.png for browsers without
SVG icons. apple-touch-icon.png (180 px) is the phone home-screen icon, from the full logo; it is drawn on the tile's own colour to
its corners, since iOS rounds the corners itself and turns transparency black. These files are standalone images, so they hold the
colour tokens' hex values (--text #d7dee3, --amber #d99a3c, --cyan #4fc3d9; the tile #0d1115).
"""
import os, sys, struct
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
JOBS = [   # (source svg, out png, size, background behind the svg or None for transparent)
    ('favicon.svg', 'favicon-32.png', 32, None),
    ('img/logo/threat-vector-logo.svg', 'apple-touch-icon.png', 180, '#0d1115'),
]


def png_size(path):
    with open(path, 'rb') as f:
        head = f.read(24)
    if head[:8] != b'\x89PNG\r\n\x1a\n': return None
    return struct.unpack('>II', head[16:24])


def check():
    bad = []
    for src, out, size, _ in JOBS:
        p = os.path.join(ROOT, out)
        if not os.path.exists(os.path.join(ROOT, src)): bad.append(f'{src} is missing')
        if not os.path.exists(p): bad.append(f'{out} is missing: run python3 -I tools/render_icons.py')
        elif png_size(p) != (size, size): bad.append(f'{out} is {png_size(p)}, not {size}x{size}')
    for x in bad: print('ICONS', x)
    print(f'ICONS: {len(JOBS)} rendered icons; {len(bad)} problems')
    return 1 if bad else 0


def render():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        for src, out, size, bg in JOBS:
            svg = open(os.path.join(ROOT, src), encoding='utf-8').read()
            pg = b.new_page(viewport={'width': size, 'height': size}, device_scale_factor=1)
            pg.set_content(f'<!doctype html><html><body style="margin:0;background:{bg or "transparent"}">'
                           f'<div style="width:{size}px;height:{size}px">{svg.replace("<svg ", f"<svg width=\"{size}\" height=\"{size}\" ", 1)}</div></body></html>')
            pg.screenshot(path=os.path.join(ROOT, out), clip={'x': 0, 'y': 0, 'width': size, 'height': size}, omit_background=bg is None)
            pg.close()
            print('wrote', out, png_size(os.path.join(ROOT, out)))
        b.close()
    return check()


if __name__ == '__main__':
    sys.exit(check() if '--check' in sys.argv else render())
