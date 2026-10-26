"""Bombs (v2026.10.14.78, roadmap/charges-plan.md delivery 4): a Bomb Launcher's bomb in the fit's DPS, volley and
damage application, against pyfa.

    PYFA_SRC=... python3 -I tools/independent_checks/check_bombs.py [index.html]   -> 'N mismatches' (must be 0)

pyfa (eos/saveddata/module.py): getVolleyParameters counts any Active module whose charge deals damage -- the charge's
em/thermal/kinetic/explosive damage x the launcher's damageMultiplier; getDps divides by getCycleParameters().averageTime,
which with reload off (pyfa's default) is rawCycleTime + moduleReactivationDelay. Module.maxRange of a bomb launcher is its
bomb's missileMaxRangeData. All on pyfa's own handlers (tools/pyfa_fit_oracle.py): the hull's bomb damage bonuses,
the Bomb Deployment skill's reactivation delay bonus.
Tool side: the page's engine on pasted fits (eft_engine.run_page): every published Stealth Bomber with every published
bomb launcher and every published bomb (one at a time), plus a launcher set Online (no damage, as in pyfa). Compared:
the fit's DPS and volley (exact), and the bomb's application inputs (maxRange 1e-6, explosionRange, aoeCloudSize).
The application itself (pyfa getBombMult) is compared on a pinned fit by check_application.py.
"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from eft_engine import run_page, BYNAME
from pyfa_fit_oracle import OracleFit
from pyfa_sde import types, groups, _en
from check_missile_range import pyfa_missile_range
html = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
DMG = ('emDamage', 'thermalDamage', 'kineticDamage', 'explosiveDamage')
def gname(t): return _en(groups[str(types[str(t)]['groupID'])].get('groupName') or groups[str(types[str(t)]['groupID'])].get('name'))
def tname(t): return _en(types[str(t)].get('typeName') or types[str(t)].get('name'))
pub = [int(k) for k, v in types.items() if v.get('published')]
HULLS = sorted(t for t in pub if gname(t) == 'Stealth Bomber')
LAUNCHERS = sorted(t for t in pub if gname(t) == 'Missile Launcher Bomb')
from pyfa_sde import td
def A(t): return {x['attributeID']: x['value'] for x in (td.get(str(t)) or {}).get('dogmaAttributes', [])}
CG = {int(A(l)[a]) for l in LAUNCHERS for a in (604, 605, 606, 609) if A(l).get(a)}   # the launchers' chargeGroup1-4
BOMBS = sorted(t for t in pub if types[str(t)]['groupID'] in CG)
cases = []
for h in HULLS:
    for l in LAUNCHERS:
        for bmb in BOMBS:
            cases.append({'hull': h, 'launcher': l, 'bomb': bmb, 'state': 'active'})
    cases.append({'hull': h, 'launcher': LAUNCHERS[0], 'bomb': BOMBS[0], 'state': 'online'})
def eft(c): return f"[{tname(c['hull'])}, Bomb check]\n\n\n{tname(c['launcher'])}, {tname(c['bomb'])}\n"
FN = """async (sb, cases) => { const out = [];
  for(const c of cases){
    const {f} = await sb.buildFitFromEft(c.text);
    if(c.state !== 'active'){ f.moduleStates = {[c.launcher]: {active: 0, online: 1, offline: 0}}; await sb.recomputeFitWithStates(f); }
    const e = f.estimate, ex = e.exact || {};
    const w = (e.application.weapons || []).find(x => x.kind === 'bomb') || null;
    out.push({dps: ex.smartbombDps, total: e.dpsFixed, volley: e.volleyFixed, w: w && {maxRange: w.maxRange, blastRadius: w.blastRadius, aoeCloudSize: w.aoeCloudSize, qty: w.qty}});
  }
  return out; }"""
tool = run_page(html, FN, [dict(c, text=eft(c)) for c in cases])
if isinstance(tool, dict) and 'error' in tool: raise SystemExit(tool['error'])
bad = 0; n = 0
def fail(m):
    global bad
    bad += 1; print('MISMATCH', m)
def close(a, b, rel=1e-6): return a is not None and b is not None and abs(a - b) <= rel * max(1.0, abs(a), abs(b))
for c, t in zip(cases, tool):
    o = OracleFit(c['hull'], [(c['launcher'], c['state'], c['bomb'])]).calculate()
    tag = f"{tname(c['hull'])} {tname(c['launcher'])} {tname(c['bomb'])} {c['state']}"
    if o.errors or o.oracleGaps: fail(f'{tag}: oracle errors {o.errors} gaps {o.oracleGaps}'); continue
    m = o.modules[0]
    vol = sum(m.charge.get(a) or 0 for a in DMG) * (m.get('damageMultiplier') if m.get('damageMultiplier') is not None else 1)
    cyc = (max(m.get('speed') or 0, m.get('duration') or 0) + (m.get('moduleReactivationDelay') or 0)) / 1000
    active = c['state'] == 'active' and vol > 0
    want_dps = vol / cyc if active else 0
    if not close(t['dps'] or 0, want_dps): fail(f"{tag}: DPS tool {t['dps']} pyfa {want_dps}")
    if (t['volley'] or 0) != round(vol if active else 0): fail(f"{tag}: volley tool {t['volley']} pyfa {vol if active else 0}")
    if active:
        mr = pyfa_missile_range(o, m)
        w = t['w'] or {}
        want = {'maxRange': mr[3] if mr else None, 'blastRadius': m.charge.get('explosionRange'), 'aoeCloudSize': m.charge.get('aoeCloudSize')}
        for k, v in want.items():
            if not close(w.get(k), v): fail(f"{tag}: {k} tool {w.get(k)} pyfa {v}")
    elif t['w']: fail(f"{tag}: a bomb in the application with the launcher {c['state']}")
    n += 1
print(f"{len(HULLS)} bombers x {len(LAUNCHERS)} launcher(s) x {len(BOMBS)} bombs + online cases")
print(f'{bad} mismatches ({n} cases; bombs vs pyfa getVolleyParameters / getDps / maxRange)')
sys.exit(1 if bad else 0)
