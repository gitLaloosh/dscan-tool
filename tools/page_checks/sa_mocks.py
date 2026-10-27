"""Made-up ESI and zKillboard data for system_analyzer_check.py (v2026.10.14.81). Every name and ID here is invented
(no real alliance or pilot). expected() works out, in plain Python and independently of the page, what the System
Analyzer should show for LOCAL with the Your Side the check sets up:
  your pilot Test Pilot (Example Corp, Example Alliance); also friendly: Blue Coalition Member, Allied Wing; hostile list:
  Crimson Tide Syndicate (an alliance) and Turncoat Corp (a corporation inside Blue Coalition Member); pilot rows 15."""
import os, re, json, hashlib, time
from esi_from_sde import handle as esi_handle, byname
from pyfa_sde import types as _TYPES, _en

ALLIANCE, CORP = 99000001, 98000001
BCM, CRTS, VOIDR, NPACT, ALLIED, THIRD, QHC = 99000002, 99000003, 99000004, 99000005, 99000006, 99000007, 99000008
TURNCOAT, ASHR = 98000009, 98000006
ORGS = {   # id: (kind, name, ticker, alliance)
    ALLIANCE: ('alliance', 'Example Alliance', 'EXA', None), CORP: ('corporation', 'Example Corp', 'EXMPL', ALLIANCE),
    98000011: ('corporation', 'Example Industries', 'EXIN', ALLIANCE),
    BCM: ('alliance', 'Blue Coalition Member', 'BCM', None), 98000002: ('corporation', 'Bluewater Fleet', 'BWF', BCM),
    TURNCOAT: ('corporation', 'Turncoat Corp', 'TURN', BCM),
    CRTS: ('alliance', 'Crimson Tide Syndicate', 'CRTS', None), 98000003: ('corporation', 'Red Ledger Holdings', 'RLH', CRTS),
    98000004: ('corporation', 'Bloodfin Corp', 'BLDF', CRTS),
    VOIDR: ('alliance', 'Void Runners', 'VOIDR', None), 98000005: ('corporation', 'Nightglass Logistics', 'NGLS', VOIDR),
    ASHR: ('corporation', 'Ashen Reach Industries', 'ASHR', None),
    NPACT: ('alliance', 'Northern Pact', 'NPACT', None), 98000007: ('corporation', 'Frostline Mining', 'FRST', NPACT),
    98000008: ('corporation', 'Pact Holding', 'NPH', NPACT),
    QHC: ('alliance', 'Quiet Harbor Collective', 'QHC', None), 98000012: ('corporation', 'Harborlight', 'HRBL', QHC),
    98000013: ('corporation', 'Lantern Bay Traders', 'LBT', None), 98000030: ('corporation', 'Three Pilots Inc', 'TPI', None),
    ALLIED: ('alliance', 'Allied Wing', 'AW', None), 98000040: ('corporation', 'Allied Wing Ops', 'AWO', ALLIED),
    THIRD: ('alliance', 'Random Third Party', 'RTP', None), 98000041: ('corporation', 'Third Party Corp', 'RTPC', THIRD),
    1000167: ('corporation', 'State War Academy', 'SWA', None), 1000044: ('corporation', 'School of Applied Knowledge', 'SAK', None),
}
SMALL = [98000020 + i for i in range(8)]
for i, c in enumerate(SMALL): ORGS[c] = ('corporation', f'Small Group {chr(65 + i)}', f'SG{chr(65 + i)}', None)
SIZES = {CORP: 12, 98000011: 18, 98000002: 12, TURNCOAT: 2, 98000003: 21, 98000004: 11, 98000005: 13, ASHR: 7, 98000007: 19,
         98000008: 14, 98000012: 17, 98000013: 9, 98000030: 3, 98000040: 4, 1000167: 3, 1000044: 2}
for c, n in zip(SMALL, [1, 2, 1, 1, 2, 1, 1, 1]): SIZES[c] = n
FIRST = ['Kael', 'Mira', 'Doran', 'Ysolde', 'Tarik', 'Vexa', 'Orrin', 'Liss', 'Brannoc', 'Ilka', 'Sorrel', 'Jask', 'Nyra', 'Hollis', 'Pell',
         'Rhoswen', 'Taavi', 'Quill', 'Eira', 'Marrek', 'Seren', 'Corvin', 'Anouk', 'Dax', 'Lio']
LAST = ['Varos', 'Ketter', 'Ashby', 'Morrow', 'Halden', 'Quist', 'Torvald', 'Rheme', 'Sallow', 'Indra', 'Kade', 'Brisk', 'Vantor', 'Lusk', 'Mercer', 'Feyre']
PILOTS = {}   # id: (name, corp)
PILOTS[90000001] = ('Test Pilot', CORP)
_i = 0
for corp, n in SIZES.items():
    for k in range(n - (1 if corp == CORP else 0)):
        nm = f'{FIRST[_i % len(FIRST)]} {LAST[(_i // len(FIRST)) % len(LAST)]}'
        PILOTS[91000000 + _i] = (nm, corp); _i += 1
NAME_ID = {v[0].lower(): k for k, v in PILOTS.items()}
TURNCOAT_PILOT = next(v[0] for v in PILOTS.values() if v[1] == TURNCOAT)
NOT_FOUND = ['Kaell Varos', 'Old Alt 3']
LOCAL = '\n'.join(sorted(v[0] for v in PILOTS.values() if v[1] not in (98000041,)) + NOT_FOUND)
SCAN = '\n'.join(f"{byname[t]}\tSomeone's {t}\t{t}\t{d}" for t, d in [('Ferox', '3.2 AU'), ('Ferox', '420 km'), ('Scimitar', '6.8 AU')])
FIT = '[Rifter, test]\nDamage Control I\n\n1MN Afterburner I\n\n200mm AutoCannon I, EMP S'

def aff(cid):
    corp = PILOTS[cid][1]; a = ORGS[corp][3]
    return {'character_id': cid, 'corporation_id': corp, **({'alliance_id': a} if a else {})}
def att(cid, final=False):
    return dict(aff(cid), final_blow=final, damage_done=100, ship_type_id=byname['Ferox'], security_status=0)
def pick(corp, k=0): return [i for i, v in PILOTS.items() if v[1] == corp][k]
THIRD_PILOT = 92000001; PILOTS[THIRD_PILOT] = ('Rando Thirdparty', 98000041)
NPC_ALT = pick(1000167)
# your side's losses (D2b evidence): Void Runners on 3, Ashen Reach on 1; friendlies, NPCs and NPC-corp pilots never count
LOSSES = {
    9200001: [att(pick(98000005), True), att(pick(ASHR)), {'corporation_id': 1000125, 'damage_done': 5, 'final_blow': False, 'security_status': 0}],
    9200002: [att(pick(98000005, 1), True), att(pick(98000005, 2)), att(pick(98000002))],
    9200003: [att(pick(98000005, 3), True), att(pick(98000011))],
    9200004: [{'corporation_id': 98000099, 'damage_done': 50, 'final_blow': True, 'security_status': 0}, att(NPC_ALT)],
}
# your side's kills (suggested friendlies): Allied Wing on 3, Northern Pact on 2, Random Third Party on 1
KILLS = {
    9300001: [att(pick(CORP), True), att(pick(98000040)), att(THIRD_PILOT), att(pick(98000002))],
    9300002: [att(pick(CORP), True), att(pick(98000040)), att(pick(98000040, 1)), att(pick(98000007))],
    9300003: [att(pick(98000011), True), att(pick(98000040, 2)), att(pick(98000008))],
}
def km(kid, attackers, victim_corp):
    return {'killmail_id': kid, 'killmail_time': '2026-10-26T12:00:00Z', 'solar_system_id': 30000142, 'attackers': attackers,
            'victim': {'character_id': pick(victim_corp), 'corporation_id': victim_corp, 'ship_type_id': byname['Ferox'], 'damage_taken': 100, 'items': [], 'position': {'x': 0, 'y': 0, 'z': 0}}}
KM = {k: km(k, a, CORP) for k, a in LOSSES.items()}
KM.update({k: km(k, a, 98000013) for k, a in KILLS.items()})
H = {k: hashlib.sha1(str(k).encode()).hexdigest() for k in KM}
ZKB_CALLS = []

# v2026.10.14.82 pilot rows (L3): each SMALL_LOCAL threat pilot's zKillboard history, built from golden-fit killmails
# (their pinned numbers are pyfa-verified: Curse 177 DPS / 22,648 EHP, Vedmak 507 DPS). Times are relative to now.
GOLDEN = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'regression_suite', 'golden_fits.json')))
GF = {'Curse': 'curse_zkb139073592_ewar', 'Vedmak': 'vedmak_zkb139012125_precursor_role_bonus', 'Loki': 'loki_zkb138935092'}
PIN = {h: GOLDEN[k]['expected'] for h, k in GF.items()}
def _iso(days): return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - days * 86400))
_kid = [9400000]
def _loss(cid, hull, days):
    _kid[0] += 1; k = _kid[0]
    if hull == 'Capsule': victim = {'ship_type_id': byname['Capsule'], 'items': []}
    else: victim = json.loads(json.dumps(GOLDEN[GF[hull]]['killmail']['victim']))
    victim.update(character_id=cid, corporation_id=PILOTS[cid][1], damage_taken=1000, position={'x': 0, 'y': 0, 'z': 0})
    KM[k] = {'killmail_id': k, 'killmail_time': _iso(days), 'solar_system_id': 30000142, 'victim': victim,
             'attackers': [dict(att(pick(98000013)), final_blow=True)]}
    H[k] = hashlib.sha1(str(k).encode()).hexdigest(); return k
def _kill(cid, hull, days):
    _kid[0] += 1; k = _kid[0]
    KM[k] = {'killmail_id': k, 'killmail_time': _iso(days), 'solar_system_id': 30000142,
             'victim': {'character_id': pick(98000013), 'corporation_id': 98000013, 'ship_type_id': byname['Ferox'], 'damage_taken': 100, 'items': [], 'position': {'x': 0, 'y': 0, 'z': 0}},
             'attackers': [dict(aff(cid), final_blow=True, damage_done=100, ship_type_id=byname[hull], security_status=0)]}
    H[k] = hashlib.sha1(str(k).encode()).hexdigest(); return k
_red = [i for i, v in PILOTS.items() if v[1] == 98000003]
_frost = sorted([i for i, v in PILOTS.items() if v[1] == 98000007], key=lambda i: PILOTS[i][0])
HIST = {}   # character id -> {'kills': [...], 'losses': [...]}
def _h(cid, kills=(), losses=()): HIST[cid] = {'kills': [_kill(cid, h, d) for h, d in kills], 'losses': [_loss(cid, h, d) for h, d in losses]}
SMALL_RED = sorted(_red[:3], key=lambda i: PILOTS[i][0])
SMALL_FROST = sorted(_frost[:4], key=lambda i: PILOTS[i][0])
_h(SMALL_RED[0], losses=[('Curse', 3)])                                        # lost a Curse 3 d ago
_h(SMALL_RED[1], kills=[('Vedmak', 2 / 24)], losses=[('Vedmak', 5)])            # a kill in a Vedmak 2 h ago
_h(SMALL_RED[2], kills=[('Loki', 1)])                                          # a Loki on a kill, never lost: fit unknown
_h(SMALL_FROST[0], losses=[('Curse', 40), ('Vedmak', 45), ('Curse', 50)])       # nothing in 30 days: most lost = Curse
_h(SMALL_FROST[1])                                                             # no history
_h(SMALL_FROST[2], kills=[('Vedmak', 1 / 24)], losses=[('Curse', 2)])          # Curse on the D-Scan wins over the newer Vedmak
_h(SMALL_FROST[3], losses=[('Capsule', 1)])                                     # only a capsule
SMALL_LOCAL = [PILOTS[i][0] for i in SMALL_RED + SMALL_FROST] + [v[0] for v in PILOTS.values() if v[1] == 98000002][:2]
SCAN_ROWS = SCAN + '\n' + f"{byname['Curse']}\tSomeone's Curse\tCurse\t2.1 AU"
def expected_rows():
    """The rows, worked out here from HIST (plan D8): newest ship seen in 30 days (a ship on the scan first), else the
    hull lost most; numbers from the newest loss in it (the golden pins), else fit unknown; hostile first, then DPS."""
    scan = {'Ferox', 'Scimitar', 'Curse'}
    rows = []
    for idx, (cid, side) in enumerate([(i, 'h') for i in SMALL_RED] + [(i, 'n') for i in SMALL_FROST]):
        seen = [(KM[k]['killmail_time'], 'kill', next(a['ship_type_id'] for a in KM[k]['attackers'] if a.get('character_id') == cid)) for k in HIST[cid]['kills']]
        seen += [(KM[k]['killmail_time'], 'loss', KM[k]['victim']['ship_type_id']) for k in HIST[cid]['losses']]
        name = {v: k for k, v in byname.items()}
        seen = [(t, kd, name[s]) for t, kd, s in seen if name[s] != 'Capsule']
        seen.sort(reverse=True)
        if not seen: rows.append((idx, side, PILOTS[cid][0], None, None, -2)); continue
        recent = [x for x in seen if x[0] >= _iso(30)]
        on = [x for x in recent if x[2] in scan]
        if on: hull = on[0][2]
        elif recent: hull = recent[0][2]
        else:
            ls = [x[2] for x in seen if x[1] == 'loss']; hull = max(dict.fromkeys(ls), key=ls.count)
        has_loss = any(x[1] == 'loss' and x[2] == hull for x in seen)
        dps = PIN[hull]['dpsFixed'] if has_loss else None
        rows.append((idx, side, PILOTS[cid][0], hull, dps, dps if dps is not None else -1))
    rows.sort(key=lambda r: (0 if r[1] == 'h' else 1, -r[5], r[0]))
    return [(r[2], r[3], r[4]) for r in rows]

# v2026.10.14.83 fleet view (L4): Crimson Tide's kills (Curse 6, Vedmak 3, Loki 1 and a capsule) and losses by hull
# (Curse: 3 of the golden fit + 2 with a 50MN MWD for the afterburner; Vedmak: 1; Loki: none); Void Runners' kills
# (4 in Lokis) and Loki losses (3 of the golden fit, the newest with Scourge). Variant 2 of the Curse also flies
# Hammerhead II for the Infiltrator II (a drone type: part of the fit's key, not of "what differs"). Other groups: no kills.
def _gkill(attackers, days):
    _kid[0] += 1; k = _kid[0]
    KM[k] = {'killmail_id': k, 'killmail_time': _iso(days), 'solar_system_id': 30000142,
             'victim': {'character_id': pick(98000013), 'corporation_id': 98000013, 'ship_type_id': byname['Ferox'], 'damage_taken': 100, 'items': [], 'position': {'x': 0, 'y': 0, 'z': 0}},
             'attackers': [dict(aff(c), final_blow=i == 0, damage_done=100, ship_type_id=byname[h], security_status=0) for i, (c, h) in enumerate(attackers)]}
    H[k] = hashlib.sha1(str(k).encode()).hexdigest(); return k
def _gloss(cid, hull, days, *swaps):
    k = _loss(cid, hull, days)
    for a, b in swaps:
        for it in KM[k]['victim']['items']:
            if it['item_type_id'] == a: it['item_type_id'] = b
    return k
_crts = [i for i, v in PILOTS.items() if v[1] in (98000003, 98000004)]
_void = [i for i, v in PILOTS.items() if v[1] == 98000005]
_npact = pick(98000007)
FLEET_KILLS = {CRTS: [_gkill([(_crts[i], 'Curse'), (_npact, 'Ferox')], 1 + i) for i in range(6)]
                     + [_gkill([(_crts[6 + i], 'Vedmak')], 2 + i) for i in range(3)]
                     + [_gkill([(_crts[9], 'Loki'), (_crts[10], 'Capsule')], 3)],
               VOIDR: [_gkill([(_void[i], 'Loki')], 1 + i) for i in range(4)]}
AB, MWD = byname['Federation Navy 100MN Afterburner'], byname['50MN Y-T8 Compact Microwarpdrive']
FLEET_LOSSES = {(CRTS, 'Curse'): [_gloss(_crts[i], 'Curse', 2 + i) for i in range(3)] + [_gloss(_crts[3 + i], 'Curse', 6 + i, (AB, MWD), (byname['Infiltrator II'], byname['Hammerhead II'])) for i in range(2)],
                (CRTS, 'Vedmak'): [_gloss(_crts[7], 'Vedmak', 4)], (CRTS, 'Loki'): [],
                # the newest Loki loss had Scourge in its launchers: the variant's most common charge (Mjolnir Rage) is put back
                # (made last: the page orders losses by killmail ID, as zKillboard numbers them in time)
                (VOIDR, 'Loki'): [_gloss(_void[i], 'Loki', 3 + i) for i in range(2)]
                                 + [_gloss(_void[2], 'Loki', 2, (byname['Mjolnir Rage Heavy Assault Missile'], byname['Caldari Navy Scourge Heavy Assault Missile']))]}
def expected_fleet():
    """The fleet view worked out here: shares from the kills (each attacker of the group counts its hull; capsules
    don't), ≈ = share × the group's count in local, the variants by exact module set, and the summary from the golden
    pins (Curse 177, Vedmak 507, Loki 801 DPS)."""
    n_local = {CRTS: 32, VOIDR: 13}
    out = {}
    for g, kills in FLEET_KILLS.items():
        cnt = {}
        for k in kills:
            for a in KM[k]['attackers']:
                if a.get('alliance_id') != g: continue
                h = {v: kk for kk, v in byname.items()}[a['ship_type_id']]
                if h == 'Capsule': continue
                cnt[h] = cnt.get(h, 0) + 1
        tot = sum(cnt.values())
        out[g] = [(h, round(100 * c / tot), round(c / tot * n_local[g])) for h, c in sorted(cnt.items(), key=lambda x: (-x[1], byname[x[0]]))]
    dps = {'Curse': PIN['Curse']['dpsFixed'], 'Vedmak': PIN['Vedmak']['dpsFixed'], 'Loki': PIN['Loki']['dpsFixed']}
    counted = [(h, est) for g in out for h, pct, est in out[g] if FLEET_LOSSES.get((g, h))]
    return {'rows': out, 'dps': dps, 'sum_dps': sum(est * dps[h] for h, est in counted), 'ships': sum(est for _, est in counted)}

def expected():
    """What the page should show, worked out here. Side rules (plan D2, D2b): corporation entries first (yours, the
    friendly list, the hostile list), then alliance entries, then the evidence, else neutral."""
    fA, fC = {ALLIANCE, BCM, ALLIED}, {CORP}
    hA, hC = {CRTS}, {TURNCOAT}
    ev = {}
    for kid, atts in LOSSES.items():
        keys = {a.get('alliance_id') or a['corporation_id'] for a in atts if a.get('character_id') and not (1000000 <= a['corporation_id'] < 2000000)}
        for k in keys: ev[k] = ev.get(k, 0) + 1
    def side(corp):
        a = ORGS[corp][3]
        if corp in fC: return ('f', None, None)
        if corp in hC: return ('h', 'list', 'corp')
        if a in fA: return ('f', None, None)
        if a in hA: return ('h', 'list', None)
        k = a or corp
        if not (1000000 <= corp < 2000000) and k in ev: return ('h', 'zkb', ev[k])
        return ('n', None, None)
    found = [v for k, v in PILOTS.items() if k != THIRD_PILOT]
    groups = {'h': {}, 'n': {}, 'f': {}}
    for name, corp in found:
        s, why, x = side(corp); a = ORGS[corp][3]
        npc = s == 'n' and 1000000 <= corp < 2000000
        key = 'npc' if npc else (f'c{corp}' if (x == 'corp' or not a) else f'a{a}')
        nm = 'NPC corporations' if npc else ORGS[corp][1] if key.startswith('c') else ORGS[a][1]
        g = groups[s].setdefault(key, {'name': nm, 'n': 0, 'why': why, 'ev': x if why == 'zkb' else None, 'npc': npc})
        g['n'] += 1
        if why == 'list': g['why'] = 'list'
    order = lambda gs: sorted(gs, key=lambda g: (-g['n'], g['name']))
    def why_text(g):
        return 'Your hostile list' if g['why'] == 'list' else f"Killed {g['ev']} of yours in 7 days" if g['why'] == 'zkb' else ''
    hostile = [(g['name'], g['n'], why_text(g)) for g in order(groups['h'].values())]
    ng = order(groups['n'].values())
    small = [g for g in ng if not g['npc'] and g['n'] <= 2] if len(ng) > 6 else []
    neutral = [(g['name'], g['n']) for g in ng if g not in small] + ([(f'{len(small)} smaller groups', sum(g['n'] for g in small))] if len(small) > 1 else [])
    friendly = [g['name'] for g in order(groups['f'].values())]
    n = {k: sum(g['n'] for g in v.values()) for k, v in groups.items()}
    red = sorted(v[0] for v in PILOTS.values() if v[1] == 98000003)
    # suggestions: co-attackers on your kills, not friendly or listed (Allied Wing was off the lists when asked)
    fA2 = {ALLIANCE, BCM}; cnt = {}
    for kid, atts in KILLS.items():
        seen = set()
        for a in atts:
            if not a.get('character_id') or 1000000 <= a['corporation_id'] < 2000000: continue
            al = a.get('alliance_id')
            if a['corporation_id'] in fC or a['corporation_id'] in hC or al in fA2 or al in hA: continue
            k = al or a['corporation_id']
            if k in seen: continue
            seen.add(k); cnt[k] = cnt.get(k, 0) + 1
    sug = [[ORGS[k][1], f'on {c} of your last {len(KILLS)} kills'] for k, c in sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0])) if c >= 2]
    small_threat = sum(1 for nm in SMALL_LOCAL if side(PILOTS[NAME_ID[nm.lower()]][1])[0] != 'f')
    return {'found': len(found), 'n': n, 'hostile': hostile, 'neutral': neutral, 'friendly': friendly,
            'crts_corps': [('Red Ledger Holdings [RLH]', SIZES[98000003]), ('Bloodfin Corp [BLDF]', SIZES[98000004])],
            'crts_first6': red[:6], 'crts_more': len(red) - 6, 'suggest': sug, 'small_threat': small_threat}

ORG_BY_NAME = {v[1].lower(): (k, v[0]) for k, v in ORGS.items()}
def esi(route):
    url, body = route.request.url, route.request.post_data or ''
    j = lambda o, st=200: route.fulfill(status=st, content_type='application/json', body=json.dumps(o))
    if '/universe/ids/' in url:
        names = json.loads(body)
        out = {}
        for n in names:
            k = n.lower()
            if k in NAME_ID: out.setdefault('characters', []).append({'id': NAME_ID[k], 'name': PILOTS[NAME_ID[k]][0]})
            elif k in ORG_BY_NAME:
                oid, kind = ORG_BY_NAME[k]
                out.setdefault('alliances' if kind == 'alliance' else 'corporations', []).append({'id': oid, 'name': ORGS[oid][1]})
        if out or not any(n in byname for n in names): return j(out)
        return esi_handle(route)
    if '/characters/affiliation/' in url:
        ids = json.loads(body)
        if any(i not in PILOTS for i in ids): return j({'error': 'Invalid character ID'}, 400)
        return j([aff(i) for i in ids])
    if '/universe/names/' in url:
        ids = json.loads(body)
        out = []
        for i in ids:
            if i in ORGS: out.append({'id': i, 'name': ORGS[i][1], 'category': ORGS[i][0]})
            elif i in PILOTS: out.append({'id': i, 'name': PILOTS[i][0], 'category': 'character'})
            elif str(i) in _TYPES: out.append({'id': i, 'name': _en(_TYPES[str(i)].get('typeName') or _TYPES[str(i)].get('name')), 'category': 'inventory_type'})   # v.83: module names
            else: return j({'error': 'Ensure all IDs are valid before resolving.'}, 404)
        return j(out)
    m = re.search(r'/(alliances|corporations)/(\d+)/\?', url)
    if m:
        i = int(m.group(2))
        if i not in ORGS: return j({'error': 'not found'}, 404)
        return j({'name': ORGS[i][1], 'ticker': ORGS[i][2]})
    m = re.search(r'/killmails/(\d+)/([^/]+)/', url)
    if m:
        kid = int(m.group(1))
        if kid not in KM or H[kid] != m.group(2): return j({'error': 'Invalid killmail_id and/or killmail_hash'}, 422)
        return j(KM[kid])
    return esi_handle(route)
def zkb(route):
    url = route.request.url
    ZKB_CALLS.append((url, time.time()))
    cors = {'access-control-allow-origin': '*'}
    stubs = lambda ids: route.fulfill(status=200, content_type='application/json', headers=cors, body=json.dumps([{'killmail_id': k, 'zkb': {'hash': H[k]}} for k in sorted(ids, reverse=True)]))
    if f'/losses/allianceID/{ALLIANCE}/' in url: return stubs(LOSSES)
    if f'/kills/allianceID/{ALLIANCE}/' in url: return stubs(KILLS)
    m = re.search(r'/losses/allianceID/(\d+)/shipTypeID/(\d+)/', url)
    if m:
        name = {v: k for k, v in byname.items()}.get(int(m.group(2)))
        return stubs(FLEET_LOSSES.get((int(m.group(1)), name), []))
    m = re.search(r'/kills/allianceID/(\d+)/$', url)
    if m and int(m.group(1)) in FLEET_KILLS: return stubs(FLEET_KILLS[int(m.group(1))])
    m = re.search(r'/(kills|losses)/characterID/(\d+)/', url)
    if m and int(m.group(2)) in HIST: return stubs(HIST[int(m.group(2))][m.group(1)])
    return route.fulfill(status=200, content_type='application/json', headers=cors, body='[]')
def route(ctx):
    ctx.route(re.compile(r'https://esi\.evetech\.net/.*'), esi)
    ctx.route(re.compile(r'https://zkillboard\.com/.*'), zkb)
    ctx.route(re.compile(r'https://(images\.evetech\.net|fonts\.).*'), lambda r: r.fulfill(status=404, body=''))
