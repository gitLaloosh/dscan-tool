"""Serves the page's ESI calls from pyfa's SDE copy, for checks that load the real index.html in a browser
(Playwright). Network to ESI / the image server is not needed: types, groups and name lookups come from
tools/pyfa_sde.py (PYFA_SRC), images answer 404 (the page falls back to text).

    from esi_from_sde import route_all
    route_all(page)            # before page.goto(...)
"""
import os, sys, json, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from refresh_golden_fixtures import sde_type
from pyfa_sde import types, groups, _en, PYFA_SRC

byname = {}
for k, v in types.items(): byname.setdefault(_en(v.get('typeName') or v.get('name')), int(k))

# v2026.10.14.76: a group's types, as ESI lists them (the Charges list reads a weapon's charge groups)
_GROUP_TYPES = {}
def group_types(gid):
    if not _GROUP_TYPES:
        for k, v in types.items(): _GROUP_TYPES.setdefault(str(v.get('groupID')), []).append(int(k))
    return sorted(_GROUP_TYPES.get(str(gid), []))
def handle(route):
    url = route.request.url
    m = re.search(r'/universe/types/(\d+)/', url); g = re.search(r'/universe/groups/(\d+)/', url)
    if m: return route.fulfill(status=200, content_type='application/json', body=json.dumps(sde_type(m.group(1))))
    if g:
        gr = groups[g.group(1)]
        return route.fulfill(status=200, content_type='application/json', body=json.dumps({'group_id': int(g.group(1)), 'name': _en(gr['groupName']), 'category_id': gr['categoryID'], 'published': True, 'types': group_types(g.group(1))}))
    if '/universe/ids/' in url:
        names = json.loads(route.request.post_data)
        return route.fulfill(status=200, content_type='application/json', body=json.dumps({'inventory_types': [{'id': byname[n], 'name': n} for n in names if n in byname]}))
    return route.fulfill(status=404, body='')

def img(route): return route.fulfill(status=404, body='')
# v2026.10.14.75: the game's icons from pyfa's copy (imgs/icons/<iconID>@1x/2x.png, the type's SDE iconID), for checks that
# need an icon to load (ring_track_check.py: the icon's own turn). Renders and types without an icon stay 404.
def icon_route(route):
    m = re.search(r'/types/(\d+)/icon', route.request.url)
    if m:
        i = (types.get(m.group(1)) or {}).get('iconID')
        size = int((re.search(r'size=(\d+)', route.request.url) or [0, 64])[1])
        f = os.path.join(PYFA_SRC, 'imgs', 'icons', f'{i}@{"2x" if size > 32 else "1x"}.png')
        if i and os.path.exists(f): return route.fulfill(status=200, content_type='image/png', body=open(f, 'rb').read())
    return route.fulfill(status=404, body='')

def route_all(page):
    page.route(re.compile(r'https://esi\.evetech\.net/.*'), handle)
    page.route(re.compile(r'https://images\.evetech\.net/.*'), img)
    page.route(re.compile(r'https://fonts\..*'), img)

def run_async(page, fn, arg=None, timeout=90000):
    """Runs an async page function that builds a fit and draws it (parseEftFit / estimateHpAndDps / renderFitTabs), and
    returns its result. v2026.10.14.61 (LESSON #57): `page.evaluate` on such a function stopped now and then with
    "Execution context was destroyed", with no navigation, reload or crash. Chrome had answered the evaluate with
    "Promise was collected" (seen in the protocol log, DEBUG=pw:protocol): the promise Playwright waits on was garbage
    collected while the page drew a big fit synchronously inside it. Started from a timer, with the result kept on
    window and polled, nothing is waiting on a collectable promise."""
    page.evaluate("""([src, arg]) => { window.__runAsync = {done: false};
        setTimeout(() => { Promise.resolve().then(() => (0, eval)('(' + src + ')')(arg)).then(
          v => { window.__runAsync.value = v; window.__runAsync.done = true; },
          e => { window.__runAsync.error = String((e && e.stack) || e); window.__runAsync.done = true; }); }, 0); }""", [fn, arg])
    page.wait_for_function("() => window.__runAsync && window.__runAsync.done", timeout=timeout)
    r = page.evaluate("() => window.__runAsync")
    if r.get('error'): raise RuntimeError('page function failed: ' + r['error'])
    return r.get('value')
