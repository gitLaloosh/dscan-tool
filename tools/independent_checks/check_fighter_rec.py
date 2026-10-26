"""The Weaknesses card's generic Fighter tile (v2026.10.14.73; the owner: "yes please" to fighters with no ship saved, then
"B: names + how much lands" collapsed and "Count the bomb"): estimate.fighterRec.

    PYFA_SRC=... python3 -I tools/independent_checks/check_fighter_rec.py [index.html]   -> 'N mismatches' (must be 0)

Part 1 -- the mapping (index.html FIGHTER_REC_TYPES), written here from the SDE alone: for each damage type, the T2
(metaGroupID 2) fighter of each fighterSquadronRole -- 2 light attack, 4 heavy attack, 5 heavy bomber (1 superiority
and 3 support are not damage picks) -- whose every damage ability deals only that type, the bomber's bomb charge
(fighterAbilityLaunchBombType) included. Exactly one per role and type, and the tool's table must equal it.

Part 2 -- every golden fit's three shares, from pyfa:
  * the fighter: an oracle fit (tools/pyfa_fit_oracle.py, pyfa's handlers, skills at V) with one squadron of each
    type in space on a hull with no fighter bonus (a Rifter; an Ibis must give the same attributes, else a hull
    handler reached them); abilities pyfa's defaults (eos Fighter.__init__), plus the bomb on the bomber;
  * each ability's DPS: pyfa FighterAbility.getDps (check_application.py's _Ability, which runs pyfa's getVolley
    rule, the bomb from its charge); the tool's dps must equal it for one fighter;
  * how much lands: pyfa's getFighterAbilityMult (graphs/data/fitDamageStats/calc/application.py, unmodified) at
    distance 0 from a source of radius 0, lock range ignored, mobile mode auto, against the golden fit as a target FIT
    (its oracle ship: the fighter-missile resistance attribute each ability names), at the signature and speed of
    the missile ranking (estimate.missileApplication.inputs, checked by check_missile_application.py) with its prop
    module off and on; the share is the DPS-weighted mean over the abilities.
Tolerance 1e-6 relative. Also: rows light, heavy, bomber; names without " II"; damageType = the estimate's weakest.
"""
import sys, os, json, re, subprocess, tempfile, math
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, HERE)
import check_application as CA
from pyfa_fit_oracle import OracleFit, fighter_default_actives
from golden_oracle import oracle_for, GOLDEN
from pyfa_sde import types, td, attrs as SDE_ATTRS, _en
html = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
bad = 0
def fail(msg):
    global bad
    bad += 1; print('MISMATCH', msg)
def close(a, b): return a is not None and b is not None and abs(a - b) <= 1e-6 * max(1.0, abs(a), abs(b))
AN = {k: v['name'] for k, v in SDE_ATTRS.items()}
def A(t): return {AN.get(str(x['attributeID']), str(x['attributeID'])): x['value'] for x in (td.get(str(t)) or {}).get('dogmaAttributes', [])}
DMG = {'em': 'EM', 'therm': 'Therm', 'kin': 'Kin', 'exp': 'Exp'}
CHARGE_DMG = {'em': 'emDamage', 'therm': 'thermalDamage', 'kin': 'kineticDamage', 'exp': 'explosiveDamage'}
ROLE = {2: 'light', 4: 'heavy', 5: 'bomber'}

# Part 1: the mapping from the SDE
def damage_types(t):
    a, out = A(t), set()
    for k, v in a.items():
        m = re.fullmatch(r'fighterAbility\w+Damage(EM|Therm|Kin|Exp)', k)
        if m and v > 0: out.add(next(d for d, s in DMG.items() if s == m.group(1)))
    bomb = int(a.get('fighterAbilityLaunchBombType') or 0)
    if bomb: out |= {d for d, k in CHARGE_DMG.items() if A(bomb).get(k, 0) > 0}
    return out
want = {c: {} for c in ROLE.values()}
for t, v in types.items():
    if not v.get('published') or v.get('metaGroupID') != 2: continue
    role = A(t).get('fighterSquadronRole')
    if role is None or int(role) not in ROLE: continue
    dts = damage_types(t)
    if len(dts) != 1: fail(f'T2 {ROLE[int(role)]} fighter {_en(v.get("typeName") or v.get("name"))} deals {sorted(dts)}: not one damage type'); continue
    d = dts.pop(); c = ROLE[int(role)]
    if d in want[c]: fail(f'two T2 {c} fighters deal {d}: {want[c][d]} and {t}')
    want[c][d] = int(t)
blk = re.search(r'const FIGHTER_REC_TYPES = (\{.*?\}\})\s*;', open(html).read(), re.S).group(1)
tool_map = json.loads(re.sub(r'//[^\n]*', '', re.sub(r'(\w+):', r'"\1":', blk)))
for c in ROLE.values():
    if set(want[c]) != set(DMG): fail(f'{c}: the SDE has T2 picks for {sorted(want[c])}, not all four damage types')
if tool_map != want: fail(f'FIGHTER_REC_TYPES {tool_map} != the SDE {want}')
for c, m in want.items():
    print(f'{c:6}: ' + ', '.join(f'{d} {_en(types[str(t)].get("typeName") or types[str(t)].get("name"))}' for d, t in m.items()))

# Part 2: pyfa's fighters (skills at V, a hull with no fighter bonus)
def host(ship):
    sq = []
    for c, m in want.items():
        for d, t in m.items():
            eff = [e['effectID'] for e in td[str(t)].get('dogmaEffects', [])]
            act = sorted(set(fighter_default_actives(eff)) | ({6485} if c == 'bomber' else set()))
            sq.append((t, int(A(t)['fighterSquadronMaxSize']), act))
    o = OracleFit(ship, [], fighters=sq).calculate()
    if o.errors or o.oracleGaps: raise SystemExit(f'ORACLE host {ship}: errors {o.errors} gaps {o.oracleGaps}')
    return o
rifter, ibis = host(587), host(596)
for fr, fi in zip(rifter.fighters, ibis.fighters):
    if any(fr.attrs.get(k) != fi.attrs.get(k) for k in set(fr.attrs) | set(fi.attrs)): fail(f'fighter {fr.item.ID}: a hull handler reached it (Rifter and Ibis differ)')
PF = {int(f.item.ID): CA._FighterApp(f) for f in rifter.fighters}
class _Src0:   # "at the target": a source of radius 0 (the tool's {lockRange: Infinity, radius: 0})
    def getRadius(s): return 0
CA.SETTINGS['ignoreLockRange'] = True; CA.SETTINGS['mobileDroneMode'] = CA.DroneMode(1)   # auto
GFM = CA.APP['getFighterAbilityMult']
def pyfa_row(tid, tgt, st):
    f = PF[tid]; parts = [(a, a.getDps()) for a in f.abilities if a.active and a.getDps() > 0]
    tot = sum(w for _, w in parts)
    share = None if st is None or not tot else sum(w * GFM(f, a, _Src0(), tgt, 0, st['speed'], st['sig']) for a, w in parts) / tot
    return tot / f.amount, share, [a.attrPrefix for a, _ in parts]

G = json.load(open(GOLDEN))
tmp = tempfile.mkdtemp(); dump = os.path.join(tmp, 'd.json')
subprocess.run(['node', os.path.join(ROOT, 'regression_suite', 'dump_results.mjs'), html, dump, 'fighterRec,missileApplication,weakest,moduleStates,droneStates'],
               check=True, stdout=subprocess.DEVNULL)
D = json.load(open(dump))
n = shares = 0
for k in G:
    t = D.get(k) or {}; r = t.get('fighterRec')
    if not r: fail(f'{k}: no fighterRec'); continue
    n += 1
    if r['damageType'] != t.get('weakest'): fail(f"{k}: damageType {r['damageType']} != weakest {t.get('weakest')}")
    if [x['cls'] for x in r['rows']] != ['light', 'heavy', 'bomber']: fail(f"{k}: rows {[x['cls'] for x in r['rows']]}"); continue
    inp = (t.get('missileApplication') or {}).get('inputs') or {}
    states, dr = CA.tool_states(t)
    tgt = CA._TgtFit(oracle_for(k, states=states, drones=dr, group_limits=False), 0)
    for x in r['rows']:
        tid = want[x['cls']][r['damageType']]
        if x['typeId'] != tid: fail(f"{k} {x['cls']}: type {x['typeId']} != {tid}"); continue
        nm = _en(types[str(tid)].get('typeName') or types[str(tid)].get('name'))
        if x['name'] + ' II' != nm: fail(f"{k} {x['cls']}: name {x['name']!r} for {nm}")
        dps, off, ab = pyfa_row(tid, tgt, inp.get('cruising'))
        _, on, _ = pyfa_row(tid, tgt, inp.get('boosted'))
        if not close(x['dps'], dps): fail(f"{k} {nm}: dps tool {x['dps']} pyfa {dps}")
        if x['abilities'] != ab: fail(f"{k} {nm}: abilities tool {x['abilities']} pyfa {ab}")
        for lab, tv, pv in (('off', x['cruising'], off), ('on', x['boosted'], on)):
            if (tv is None) != (pv is None) or (tv is not None and not close(tv, pv)): fail(f'{k} {nm} prop {lab}: tool {tv} pyfa {pv}')
            elif tv is not None: shares += 1
print(f'{bad} mismatches ({n} fits, {shares} shares; the Fighter tile vs the SDE mapping and pyfa getFighterAbilityMult)')
sys.exit(1 if bad else 0)
