"""The Fit card's Charges list (v2026.10.14.76, roadmap/charges-plan.md delivery 2): which charges it offers each weapon,
and each charge's DPS and range, against pyfa.

    PYFA_SRC=... python3 -I tools/independent_checks/check_charge_list.py [index.html]   -> 'N mismatches' (must be 0)

Tool side: the page's own chgBuild (the code the list draws from) on pasted fits, in Node, ESI answered from the SDE
(eft_engine.run_page). pyfa side, for every weapon type and every charge:
  * the list = pyfa Module.getValidCharges, written here from eos/saveddata/module.py: every published type in the
    weapon's chargeGroup1-4 (pyfa's loop reads chargeGroup0..4) that isValidCharge accepts (the charge's volume within
    the weapon's capacity; the weapon's chargeSize, when it has one, equal to the charge's);
  * the DPS = pyfa's handlers (tools/pyfa_fit_oracle.py) on the fit with that charge in every copy of that weapon, the
    copies' getDps summed (check_application.module_dps, spool at max); weapons active, the rest online;
  * the range = pyfa Module.maxRange and falloff for a turret, the missile's displayed maxRange (missileMaxRangeData) for
    a launcher.
Fits: missiles (Drake), hybrids (Megathron), lasers with crystals (Apocalypse), projectiles (Hurricane, Tornado), two
launcher types sharing charges (Caracal), an Entropic Disintegrator (Vedmak). DPS 1e-6 relative; range 1 m (the tool
keeps whole metres).
"""
import sys, os, json, math
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from eft_engine import run_page, BYNAME
from pyfa_fit_oracle import OracleFit
from pyfa_sde import types, td, _en
import check_application as CA
from check_missile_range import pyfa_missile_range
html = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
FITS = {
 'drake': """[Drake, Missiles]
Ballistic Control System II
Ballistic Control System II

Large Shield Extender II
10MN Afterburner II

Heavy Missile Launcher II, Scourge Heavy Missile
Heavy Missile Launcher II, Scourge Heavy Missile
Heavy Missile Launcher II, Scourge Heavy Missile

Medium Core Defense Field Extender I
""",
 'megathron': """[Megathron, Hybrids]
Magnetic Field Stabilizer II
Magnetic Field Stabilizer II

500MN Microwarpdrive II

Neutron Blaster Cannon II, Void L
Neutron Blaster Cannon II, Void L
Neutron Blaster Cannon II, Void L

Large Hybrid Burst Aerator I
""",
 'apocalypse': """[Apocalypse, Lasers]
Heat Sink II
Heat Sink II

500MN Microwarpdrive II

Mega Pulse Laser II, Scorch L
Mega Pulse Laser II, Scorch L
""",
 'hurricane': """[Hurricane, Autocannons]
Gyrostabilizer II

10MN Afterburner II

220mm Vulcan AutoCannon II, Hail M
220mm Vulcan AutoCannon II, Hail M
""",
 'tornado': """[Tornado, Artillery]
Gyrostabilizer II

1400mm Howitzer Artillery II, Tremor L
1400mm Howitzer Artillery II, Tremor L
""",
 'caracal': """[Caracal, Two launcher types]
Ballistic Control System II

10MN Afterburner II

Rapid Light Missile Launcher II, Scourge Light Missile
Light Missile Launcher II, Scourge Light Missile
""",
 'vedmak': """[Vedmak, Disintegrator]
Entropic Radiation Sink II

Heavy Entropic Disintegrator II, Baryon Exotic Plasma M
""",
}
FN = """async (sb, fits) => { const out = {};
  for(const [k, t] of Object.entries(fits)){
    const {f} = await sb.buildFitFromEft(t);
    out[k] = (await sb.chgBuild(f)).map(w => ({weaponTypeId: w.weaponTypeId, name: w.name, copies: w.copies.length,
      options: w.options.map(o => ({id: o.id, name: o.name, dps: o.dps, range: o.range}))}));
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
def parse(t):
    lines = t.strip().split('\n'); ship = BYNAME[lines[0][1:].split(',')[0].strip()]
    mods = []
    for l in lines[1:]:
        l = l.strip()
        if not l: continue
        n, _, c = l.partition(',')
        mods.append((BYNAME[n.strip()], BYNAME[c.strip()] if c.strip() else None))
    return ship, mods

tool = run_page(html, FN, FITS)
if 'error' in tool: raise SystemExit(tool['error'])
for k, eft in FITS.items():
    ship, mods = parse(eft)
    ws = tool.get(k) or []
    weapon_ids = {m for m, c in mods if c is not None}
    if {w['weaponTypeId'] for w in ws} != weapon_ids: fail(f'{k}: weapons {[w["name"] for w in ws]} vs {sorted(weapon_ids)}')
    for w in ws:
        wid = w['weaponTypeId']
        want = valid_charges(wid)
        got = {o['id'] for o in w['options']}
        if got != want: fail(f"{k} {w['name']}: list {len(got)} vs pyfa {len(want)}; only tool {sorted(got - want)[:5]}, only pyfa {sorted(want - got)[:5]}")
        for o in w['options']:
            ml = [(m, 'active' if c is not None else 'online', o['id'] if m == wid else c) for m, c in mods]
            orc = OracleFit(ship, ml).calculate()
            if orc.errors or orc.oracleGaps: fail(f"{k} {o['name']}: oracle errors {orc.errors} gaps {orc.oracleGaps}"); continue
            wm = [m for m in orc.modules if int(m.item.ID) == wid]
            pd = sum(CA.module_dps(m) for m in wm)
            if not close(o['dps'], pd): fail(f"{k} {w['name']} {o['name']}: DPS tool {o['dps']} pyfa {pd}")
            m0 = wm[0]
            r = o['range'] or {}
            if 'flight' in r:
                mr = pyfa_missile_range(orc, m0)
                if mr is None or abs(r['flight'] - mr[3]) > 1: fail(f"{k} {o['name']}: missile range tool {r.get('flight')} pyfa {mr and mr[3]}")
            else:
                sm = CA._Mod(orc, m0, pd)
                if abs((r.get('optimal') or 0) - (sm.maxRange or 0)) > 1 or abs((r.get('falloff') or 0) - (sm.falloff or 0)) > 1:
                    fail(f"{k} {o['name']}: turret range tool {r} pyfa {sm.maxRange}/{sm.falloff}")
            nums += 1
    print(k + ': ' + ', '.join(f"{w['name']} {len(w['options'])} charges" for w in ws))
print(f'{bad} mismatches ({nums} charges on {len(FITS)} fits; the Charges list vs pyfa getValidCharges, getDps, maxRange / falloff)')
sys.exit(1 if bad else 0)
