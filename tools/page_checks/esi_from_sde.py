"""Serves the page's ESI calls from pyfa's SDE copy, for checks that load the real index.html in a browser
(Playwright). Network to ESI / the image server is not needed: types, groups and name lookups come from
tools/pyfa_sde.py (PYFA_SRC), images answer 404 (the page falls back to text).

    from esi_from_sde import route_all
    route_all(page)            # before page.goto(...)
"""
import os, sys, json, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from refresh_golden_fixtures import sde_type
from pyfa_sde import types, groups, _en

byname = {}
for k, v in types.items(): byname.setdefault(_en(v.get('typeName') or v.get('name')), int(k))

def handle(route):
    url = route.request.url
    m = re.search(r'/universe/types/(\d+)/', url); g = re.search(r'/universe/groups/(\d+)/', url)
    if m: return route.fulfill(status=200, content_type='application/json', body=json.dumps(sde_type(m.group(1))))
    if g:
        gr = groups[g.group(1)]
        return route.fulfill(status=200, content_type='application/json', body=json.dumps({'group_id': int(g.group(1)), 'name': _en(gr['groupName']), 'category_id': gr['categoryID'], 'published': True, 'types': []}))
    if '/universe/ids/' in url:
        names = json.loads(route.request.post_data)
        return route.fulfill(status=200, content_type='application/json', body=json.dumps({'inventory_types': [{'id': byname[n], 'name': n} for n in names if n in byname]}))
    return route.fulfill(status=404, body='')

def img(route): return route.fulfill(status=404, body='')

def route_all(page):
    page.route(re.compile(r'https://esi\.evetech\.net/.*'), handle)
    page.route(re.compile(r'https://images\.evetech\.net/.*'), img)
    page.route(re.compile(r'https://fonts\..*'), img)
