"""Charges in modules that aren't turrets or launchers (v2026.10.14.78, roadmap/charges-plan.md delivery 4): the Charges
list's sections for Capacitor Boosters, Ancillary Shield / Armor Repairers, scripted modules, Command Bursts, Interdiction
Sphere Launchers and Bomb Launchers, against pyfa and against the fit pasted with that charge.

    PYFA_SRC=... python3 -I tools/independent_checks/check_module_charges.py [index.html]   -> 'N mismatches' (must be 0)

Tool side: the page's own chgBuild / chgMetrics (eft_engine.run_page, ESI answered from the SDE). Checked:
  1. the list: every module that takes charges gets a section of the right kind, and its charges are pyfa's
     Module.getValidCharges (written here from eos/saveddata/module.py, as check_charge_list.py: chargeGroup1-4, the
     charge's volume within the module's capacity, chargeSize when the module has one);
  2. the numbers: each charge's two numbers (and "No charge") equal the same numbers on the fit PASTED with that charge in
     every copy of the module (with "No charge": none in the module and none of its charges in cargo -- a pasted fit with
     none anywhere is empty, v.24, which is what an unload means). So the list's input change (chgInputWithPicks and the
     engine's options.unloaded) is exactly a fit with that charge; the pasted fits' numbers are pyfa's by the other checks
     (check_capacitor, check_repairs, compare_ewar, compare_resists, check_targeting, check_bombs);
  3. pyfa directly, on small fits with the module and the charge (every module active): Sensor Booster scripts -> the
     ship's maxTargetRange and scanResolution; Tracking Computer scripts -> the turret's maxRange, falloff and
     trackingSpeed; Missile Guidance Computer scripts -> the missile's maxRange (missileMaxRangeData) and aoeCloudSize;
     Remote Sensor Dampener, Tracking and Guidance Disruptor scripts -> the module's maxTargetRangeBonus /
     scanResolutionBonus / maxRangeBonus / falloffBonus / trackingSpeedBonus / missileVelocityBonus / explosionDelayBonus /
     aoeVelocityBonus / aoeCloudSizeBonus; Flex Shield Hardener scripts -> the ship's four shield resonances. Relative 1e-6
     (missile range 1 m: the tool keeps whole metres);
  4. "No charge" overrides the cargo inference: an unloaded Capacitor Booster injects nothing with Cap Booster charges in
     cargo, an unloaded Interdiction Sphere Launcher launches nothing with probes in cargo, an unloaded Ancillary Armor
     Repairer has no burst with paste in cargo; a module that isn't a weapon keeps its state when unloaded.
"""
import sys, os, json, re
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from eft_engine import run_page, BYNAME
from pyfa_fit_oracle import OracleFit, resonances
from pyfa_sde import types, td, groups, _en
import check_application as CA
from check_missile_range import pyfa_missile_range
html = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
FITS = {
 'megathron': """[Megathron, D4]
Large Ancillary Armor Repairer, Nanite Repair Paste
Magnetic Field Stabilizer II
Damage Control II

Heavy Capacitor Booster II, Navy Cap Booster 800
Tracking Computer II, Optimal Range Script
Sensor Booster II, Targeting Range Script
100MN Afterburner II

Neutron Blaster Cannon II, Void L
Neutron Blaster Cannon II, Void L


Navy Cap Booster 800 x20
Nanite Repair Paste x100
Tracking Speed Script x1
Scan Resolution Script x1
""",
 'arazu': """[Arazu, D4]
Damage Control II

Remote Sensor Dampener II, Targeting Range Dampening Script
Tracking Disruptor II, Optimal Range Disruption Script
Tracking Disruptor II
Guidance Disruptor II, Missile Range Disruption Script

Covert Ops Cloaking Device II


Scan Resolution Dampening Script x2
Tracking Speed Disruption Script x1
""",
 'claymore': """[Claymore, D4]
Damage Control II

X-Large Ancillary Shield Booster, Navy Cap Booster 400
Heavy Capacitor Booster II, Navy Cap Booster 400

Shield Command Burst II, Shield Harmonizing Charge
Skirmish Command Burst II, Interdiction Maneuvers Charge
Heavy Assault Missile Launcher II, Scourge Heavy Assault Missile


Navy Cap Booster 400 x30
Active Shielding Charge x200
""",
 'sabre': """[Sabre, D4]
Damage Control II

Warp Disruptor II

Interdiction Sphere Launcher I, Warp Disrupt Probe
200mm AutoCannon II, Republic Fleet EMP S


Stasis Webification Probe x4
""",
 'onyx': """[Onyx, D4]
Damage Control II

Large Shield Extender II

Warp Disruption Field Generator II, Focused Warp Disruption Script
Heavy Missile Launcher II, Scourge Heavy Missile


Focused Warp Scrambling Script x1
""",
 'hound': """[Hound, D4]
Ballistic Control System II

Missile Guidance Computer II, Missile Range Script

Torpedo Launcher II, Nova Rage Torpedo
Bomb Launcher I, Shrapnel Bomb
Covert Ops Cloaking Device II


Concussion Bomb x2
Missile Precision Script x1
""",
 'myrmidon': """[Myrmidon, D4: an Ancillary Armor Repairer with no paste anywhere]
Medium Ancillary Armor Repairer
Damage Control II

10MN Afterburner II
""",
 'minokawa': """[Minokawa, D4]
Damage Control II

Capital Flex Shield Hardener II, Shield EM Resistance Script
Capital Flex Shield Hardener II


Shield Thermal Resistance Script x1
""",
}
WANT_KINDS = {'megathron': {'Neutron Blaster Cannon II': 'weapon', 'Heavy Capacitor Booster II': 'capBooster', 'Tracking Computer II': 'tc',
                            'Sensor Booster II': 'sb', 'Large Ancillary Armor Repairer': 'aar'},
              'arazu': {'Remote Sensor Dampener II': 'damp', 'Tracking Disruptor II': 'disruptor', 'Guidance Disruptor II': 'disruptor'},
              'claymore': {'X-Large Ancillary Shield Booster': 'asb', 'Heavy Capacitor Booster II': 'capBooster', 'Shield Command Burst II': 'burst',
                           'Skirmish Command Burst II': 'burst', 'Heavy Assault Missile Launcher II': 'weapon'},
              'sabre': {'Interdiction Sphere Launcher I': 'sphere', '200mm AutoCannon II': 'weapon'},
              'onyx': {'Warp Disruption Field Generator II': 'wdfg', 'Heavy Missile Launcher II': 'weapon'},
              'hound': {'Missile Guidance Computer II': 'mgc', 'Torpedo Launcher II': 'weapon', 'Bomb Launcher I': 'bomb'},
              'myrmidon': {'Medium Ancillary Armor Repairer': 'aar'},
              'minokawa': {'Capital Flex Shield Hardener II': 'flex'}}
BUILD = """async (sb, fits) => { const out = {};
  for(const [k, t] of Object.entries(fits)){
    const {f} = await sb.buildFitFromEft(t);
    out[k] = (await sb.chgBuild(f)).map(w => ({typeId: w.typeId || w.weaponTypeId, kind: w.kind, sub: w.sub, name: w.name, copies: w.copies, cols: w.cols,
      none: w.none && {a: w.none.a, b: w.none.b}, options: w.options.map(o => ({id: o.id, name: o.name, a: o.a, b: o.b}))}));
  }
  return out; }"""
# one paste per (fit, module, charge): the engine's numbers on it through the same chgMetrics
PASTED = """async (sb, cases) => { const out = [];
  for(const c of cases){
    const {f} = await sb.buildFitFromEft(c.text);
    const mod = (await sb.chgModules(f.input)).find(m => m.typeId === c.typeId);
    const e = f.estimate, m = mod ? sb.chgMetrics(mod, e, c.charge) : null;
    const aw = (e.application.weapons || []), ew = (e.ewarModules || []).filter(x => mod && x.name === mod.name);
    out.push({a: m && m.a, b: m && m.b, raw: {tgt: e.exact.targetingRange, scan: e.exact.scanResolution, res: e.resonance.shield,
      turret: aw.filter(w => w.kind === 'turret').map(w => [w.optimal, w.falloff, w.tracking])[0] || null,
      missile: aw.filter(w => w.kind === 'missile').map(w => [w.weaponTypeId, w.aoeCloudSize])[0] || null,
      missileRange: (e.rangeEstimates || []).filter(r => r.kind === 'missile').map(r => r.travelDistanceM)[0] || null, ewar: ew[0] || null}});
  }
  return out; }"""
bad = 0; nums = 0
def fail(m):
    global bad
    bad += 1; print('MISMATCH', m)
def close(a, b, rel=1e-6): return a is not None and b is not None and abs(a - b) <= rel * max(1.0, abs(a), abs(b))
def A(t): return {x['attributeID']: x['value'] for x in (td.get(str(t)) or {}).get('dogmaAttributes', [])}
GROUP_TYPES = {}
for k, v in types.items(): GROUP_TYPES.setdefault(v.get('groupID'), []).append(int(k))
def valid_charges(w):   # pyfa Module.getValidCharges / isValidCharge
    a, cap = A(w), types[str(w)].get('capacity')
    out = set()
    for g in [int(a[x]) for x in (604, 605, 606, 609) if a.get(x)]:
        for t in GROUP_TYPES.get(g, []):
            v = types[str(t)]
            if not v.get('published'): continue
            if v.get('volume') is not None and cap is not None and v['volume'] > cap: continue
            if (a.get(128) or 0) > 0 and A(t).get(128) != a.get(128): continue
            out.add(t)
    return out
def tname(t): return _en(types[str(t)].get('typeName') or types[str(t)].get('name'))
def paste_with(text, modname, charge, drop_cargo):
    """the fit with `charge` (a name, or None) on every line of module `modname`; drop_cargo: cargo lines of these names go"""
    out = []
    for l in text.split('\n'):
        n = l.split(',')[0].strip()
        if n == modname: out.append(f'{modname}, {charge}' if charge else modname); continue
        q = re.match(r'^(.+?)\s+x\d+$', l.strip())
        if q and q.group(1) in drop_cargo: continue
        out.append(l)
    return '\n'.join(out)

tool = run_page(html, BUILD, FITS)
if 'error' in tool: raise SystemExit(tool['error'])
cases, meta = [], []
for k, eft in FITS.items():
    secs = tool.get(k) or []
    got = {s['name']: s.get('kind') for s in secs}
    if got != WANT_KINDS[k]: fail(f'{k}: sections {got} vs {WANT_KINDS[k]}')
    for s in secs:
        want = valid_charges(s['typeId'])
        ids = {o['id'] for o in s['options']}
        if ids != want: fail(f"{k} {s['name']}: list {len(ids)} vs pyfa {len(want)}; only tool {sorted(ids - want)[:5]}, only pyfa {sorted(want - ids)[:5]}")
        if s.get('kind') in ('weapon', None): continue   # weapons: check_charge_list.py
        names = {tname(t) for t in want}
        for o in [{'id': 0, 'name': None, 'a': s['none']['a'], 'b': s['none']['b']}] + s['options']:
            # Ancillary Armor Repairer paste: the line has no slot of its own; the EFT ", Nanite Repair Paste" is its loaded paste
            cases.append({'text': paste_with(eft, s['name'], o['name'], names if o['id'] == 0 else set()), 'typeId': s['typeId'], 'charge': o['id']})
            meta.append((k, s, o))
res = run_page(html, PASTED, cases)
if isinstance(res, dict) and 'error' in res: raise SystemExit(res['error'])
pyfa_n = 0
for (k, s, o), c, r in zip(meta, cases, res):
    tag = f"{k} {s['name']} {o['name'] or 'No charge'}"
    if s['kind'] == 'bomb' and not o['id']:   # a bomb launcher's No charge isn't run (it goes Online): 0 DPS, no range
        if o['a'] != '0' or r['a'] != '0': fail(f"{tag}: list {o['a']!r}, the pasted fit {r['a']!r} (want 0 DPS)")
    elif (o['a'], o['b']) != (r['a'], r['b']): fail(f"{tag}: list {o['a']!r} / {o['b']!r}, the pasted fit {r['a']!r} / {r['b']!r}")
    nums += 1
    if not o['id'] and s['kind'] not in ('sb', 'tc', 'mgc', 'damp', 'disruptor', 'flex'): continue
    # 3. pyfa: the module (every copy) with that charge, alone on the hull with the weapon it works on
    raw = r['raw']; kind = s['kind']
    ship = BYNAME[c['text'].split('\n')[0][1:].split(',')[0].strip()]
    n = len(s['copies']); ch = o['id'] or None
    mods = [(s['typeId'], 'active', ch)] * n
    if kind in ('sb', 'tc', 'mgc', 'flex', 'damp', 'disruptor'):
        # the fit's own other modules matter (the tool's numbers are the whole fit's): rebuild it, every module as pasted
        lines = [l.strip() for l in c['text'].split('\n')[1:] if l.strip() and not re.search(r'\sx\d+$', l.strip())]
        mods = []
        for l in lines:
            mn, _, cn = l.partition(',')
            mid = BYNAME[mn.strip()]; cid = BYNAME[cn.strip()] if cn.strip() else None
            g = _en(groups[str(types[str(mid)]['groupID'])].get('groupName') or groups[str(types[str(mid)]['groupID'])].get('name'))
            st = 'online' if g == 'Cloaking Device' else 'active'   # as the tool starts them (a cloak online, the rest running)
            mods.append((mid, st, cid))
    orc = OracleFit(ship, mods).calculate()
    if orc.errors or orc.oracleGaps: fail(f'{tag}: oracle errors {orc.errors} gaps {orc.oracleGaps}'); continue
    om = [m for m in orc.modules if int(m.item.ID) == s['typeId']]
    if kind == 'sb':
        for key, want in (('tgt', orc.ship.get('maxTargetRange')), ('scan', orc.ship.get('scanResolution'))):
            if not close(raw[key], want): fail(f'{tag}: {key} tool {raw[key]} pyfa {want}')
        pyfa_n += 1
    elif kind == 'tc':
        t0 = [m for m in orc.modules if m.item.group.name == 'Hybrid Weapon'][0]; sm = CA._Mod(orc, t0, 0)
        want = (sm.maxRange, sm.falloff, t0.get('trackingSpeed'))
        if not raw['turret'] or not all(close(x, y) for x, y in zip(raw['turret'], want)): fail(f"{tag}: turret tool {raw['turret']} pyfa {want}")
        pyfa_n += 1
    elif kind == 'mgc':
        mm = [m for m in orc.modules if m.item.group.name == 'Missile Launcher Torpedo'][0]
        mr = pyfa_missile_range(orc, mm)
        if not raw['missile'] or not close(raw['missile'][1], mm.charge.get('aoeCloudSize')) or abs((raw['missileRange'] or 0) - mr[3]) > 1:   # the tool keeps whole metres
            fail(f"{tag}: missile tool {raw['missile']} / {raw['missileRange']} pyfa {mm.charge.get('aoeCloudSize')} / {mr[3]}")
        pyfa_n += 1
    elif kind in ('damp', 'disruptor'):
        ew = raw['ewar'] or {}
        fields = {'damp': (('targetingRangeBonusPct', 'maxTargetRangeBonus'), ('scanResolutionBonusPct', 'scanResolutionBonus')),
                  'td': (('opticalBonusPct', 'maxRangeBonus'), ('falloffBonusPct', 'falloffBonus'), ('trackingSpeedBonusPct', 'trackingSpeedBonus')),
                  'gd': (('missileVelocityBonusPct', 'missileVelocityBonus'), ('flightTimeBonusPct', 'explosionDelayBonus'),
                         ('explosionVelocityBonusPct', 'aoeVelocityBonus'), ('explosionRadiusBonusPct', 'aoeCloudSizeBonus'))}[kind if kind == 'damp' else s['sub']]
        for f_, a in fields:
            if not close(ew.get(f_), om[0].get(a) or 0.0): fail(f'{tag}: {f_} tool {ew.get(f_)} pyfa {om[0].get(a)}')
        pyfa_n += 1
    elif kind == 'flex':
        want = resonances(orc)['shield']
        for d, tk in (('em', 'em'), ('thermal', 'therm'), ('kinetic', 'kin'), ('explosive', 'exp')):
            wv = want.get(d, want.get(tk))
            if not close(raw['res'][tk], wv): fail(f"{tag}: shield {tk} resonance tool {raw['res'][tk]} pyfa {wv}")
        pyfa_n += 1

# 4. "No charge" overrides the cargo inference; a module that isn't a weapon keeps its state
UNLOAD = """async (sb, a) => { const out = {};
  const run = async (text, typeId) => { const {f} = await sb.buildFitFromEft(text); const before = JSON.stringify(f.estimate.moduleStates.items.map(i => [i.typeId, i.active, i.online]));
    await sb.chgLoad(f, typeId, 0, null); await sb.recomputeFitWithStates(f);
    return {e: f.estimate, same: before === JSON.stringify(f.estimate.moduleStates.items.map(i => [i.typeId, i.active, i.online]))}; };
  let r = await run(a.mega, a.cap);
  out.cap = {boosts: r.e.capacitor.boosts.filter(b => b.kind === 'capBooster').length, same: r.same};
  r = await run(a.mega, a.aar);
  out.aar = {burst: r.e.tankStyle.armor.burstDps, same: r.same};
  r = await run(a.sabre, a.sphere);
  out.sphere = {probe: (r.e.ewarModules.find(m => m.kind === 'sphere') || {}).probe || null, same: r.same};
  r = await run(a.mega, a.tc);
  out.tc = {same: r.same};
  return out; }"""
u = run_page(html, UNLOAD, {'mega': FITS['megathron'], 'sabre': FITS['sabre'], 'cap': BYNAME['Heavy Capacitor Booster II'],
                           'aar': BYNAME['Large Ancillary Armor Repairer'], 'sphere': BYNAME['Interdiction Sphere Launcher I'], 'tc': BYNAME['Tracking Computer II']})
if 'error' in u: raise SystemExit(u['error'])
if u['cap']['boosts'] or not u['cap']['same']: fail(f"unloaded Capacitor Booster with Cap Booster charges in cargo: {u['cap']} (want no injection, states kept)")
if u['aar']['burst'] or not u['aar']['same']: fail(f"unloaded Ancillary Armor Repairer with paste in cargo: {u['aar']} (want no burst, states kept)")
if u['sphere']['probe'] or not u['sphere']['same']: fail(f"unloaded Interdiction Sphere Launcher with probes in cargo: {u['sphere']} (want no probe, states kept)")
if not u['tc']['same']: fail(f"unloaded Tracking Computer: states changed {u['tc']}")
print(f"{len(FITS)} fits: " + ', '.join(f"{k} {len(v)} sections" for k, v in tool.items()))
print(f'{bad} mismatches ({nums} charges + No charge rows against the pasted fit, {pyfa_n} against pyfa, 4 unload rules; module charges vs pyfa getValidCharges)')
sys.exit(1 if bad else 0)
