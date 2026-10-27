"""zKillboard and ESI answered for the page checks of killmail links (v2026.10.14.80, from shared_kill_check.py v.79):
the killmails of last_kill_check.py with real-looking 40-character hashes. ESI answers 422 to a wrong killmail hash and 404
to an unknown ID in /universe/names, as it does (LESSON #71); /universe/names gives each ID its category."""
import os, re, json, hashlib
from esi_from_sde import handle as esi_handle
from pyfa_sde import types, _en
HERE = os.path.dirname(os.path.abspath(__file__))
GOLDEN = json.load(open(os.path.join(HERE, '..', '..', 'regression_suite', 'golden_fits.json')))
LOSSES = [('loki_zkb138935092', 9100001), ('curse_zkb139073592_ewar', 9100002), ('vedmak_zkb139012125_precursor_role_bonus', 9100003),
          ('leshak_zkb139013625_precursor_battleship_role_bonus', 9100004)]
KM = {}
for i, (k, kid) in enumerate(LOSSES):
    km = json.loads(json.dumps(GOLDEN[k]['killmail'])); km['killmail_id'] = kid; km['killmail_time'] = f'2026-10-0{i + 1}T12:00:00Z'
    km['solar_system_id'] = 30000142; km['victim']['character_id'] = 90000001
    KM[kid] = km
KM[9100005] = dict(KM[9100001], killmail_id=9100005, killmail_time='2026-10-05T12:00:00Z')
H = {kid: hashlib.sha1(str(kid).encode()).hexdigest() for kid in KM}
STUBS = [{'killmail_id': kid, 'zkb': {'hash': H[kid]}} for kid in (9100001, 9100002, 9100003, 9100004, 9100005)]
_ved = KM[9100003]['victim']['ship_type_id']
KM[9100100] = {'killmail_id': 9100100, 'killmail_time': '2026-09-01T18:18:03Z', 'solar_system_id': 30000142, 'victim': dict(KM[9100002]['victim'], items=[]),
               'attackers': [{'character_id': 90000001, 'ship_type_id': _ved, 'weapon_type_id': _ved, 'final_blow': True, 'damage_done': 900, 'security_status': 0}]}
H[9100100] = hashlib.sha1(b'9100100').hexdigest()
NAME = {int(k): _en(v.get('typeName') or v.get('name')) for k, v in types.items()}
NAME.update({90000001: 'Test Pilot', 30000142: 'Jita'})
ZKB_CALLS = []

CHARACTERS = {90000001}
SYSTEMS = {30000142}
def category(i): return 'character' if i in CHARACTERS else 'solar_system' if i in SYSTEMS else 'inventory_type'
def esi(route):
    url, body = route.request.url, route.request.post_data or ''
    if '/universe/ids/' in url and 'Test Pilot' in body:
        return route.fulfill(status=200, content_type='application/json', body=json.dumps({'characters': [{'id': 90000001, 'name': 'Test Pilot'}]}))
    m = re.search(r'/killmails/(\d+)/([^/]+)/', url)
    if m:
        kid = int(m.group(1))
        if kid not in KM or H[kid] != m.group(2): return route.fulfill(status=422, content_type='application/json', body='{"error":"Invalid killmail_id and/or killmail_hash"}')
        return route.fulfill(status=200, content_type='application/json', body=json.dumps(KM[kid]))
    if '/universe/names/' in url:
        ids = json.loads(body)
        if any(i not in NAME for i in ids): return route.fulfill(status=404, content_type='application/json', body='{"error":"Ensure all IDs are valid before resolving."}')
        return route.fulfill(status=200, content_type='application/json', body=json.dumps([{'id': i, 'name': NAME[i], 'category': category(i)} for i in ids]))
    return esi_handle(route)
def zkb(route):
    cors = {'access-control-allow-origin': '*'}
    url = route.request.url
    ZKB_CALLS.append(url)
    if '/kills/' in url: return route.fulfill(status=200, content_type='application/json', headers=cors, body=json.dumps([{'killmail_id': 9100100, 'zkb': {'hash': H[9100100]}}]))
    m = re.search(r'/killID/(\d+)/', url)
    if m:
        kid = int(m.group(1))
        return route.fulfill(status=200, content_type='application/json', headers=cors, body=json.dumps([s for s in STUBS if s['killmail_id'] == kid]))
    m = re.search(r'/shipTypeID/(\d+)/', url)
    stubs = [s for s in STUBS if not m or KM[s['killmail_id']]['victim']['ship_type_id'] == int(m.group(1))]
    return route.fulfill(status=200, content_type='application/json', headers=cors, body=json.dumps(stubs))

