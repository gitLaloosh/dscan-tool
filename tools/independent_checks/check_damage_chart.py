"""Their damage on you (v2026.10.14.36; roadmap/turret-application-plan.md Phase 2b).

    PYFA_SRC=... python3 -I tools/independent_checks/check_damage_chart.py [index.html]   -> 'N mismatches'

The card charts one number per point: pyfa's damage graph with applyProjected on (getter.py _calculatePoint), i.e.
the attacker's webs / painters / scram on the target first (calc/projected.py), then the attacker's weapons at the
tackled speed and painted signature (calc/application.py). This check runs both of pyfa's files UNMODIFIED -- the
harnesses of check_projected.py and check_application.py, imported, not copied -- on pyfa's own attribute values
(tools/pyfa_fit_oracle.py) for both ships, and compares the card's own point function (dmgPoint on dmgTargetObj,
index.html) at every point of a grid of distance x the target's speed share and heading x the attacker's speed and
heading x the signature slider, for both of the target's prop states (variants.on / variants.off):
  * targets: the five class presets (DMG_CLASS_PRESETS, built from their EFT text by the real engine,
    eft_engine.py; pyfa side OracleFit with the MWD active / online) and golden fits with a prop module (pyfa side
    the golden oracle with the tool's states, the prop module active / online);
  * each target variant's untackled top speed and signature radius;
  * at every point: the tackled speed, the painted signature radius and the applied DPS.
The signature slider scales the target's base signature; every term after it is a multiplier, so pyfa's side is
scale x tgt.getSigRadius() x getSigRadiusMult (scale-free). Tolerance 1e-6 relative.
"""
import sys, os, re, json, subprocess, tempfile, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import check_projected as CP
import check_application as CA
from golden_oracle import oracle_for, GOLDEN
from pyfa_fit_oracle import OracleFit
from eft_engine import run_efts

NODE = r'''
const fs = require('fs'), vm = require('vm');
const [htmlPath, inPath, outPath] = process.argv.slice(2);
const code = [...fs.readFileSync(htmlPath, 'utf8').matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');
const fakeEl = () => ({addEventListener(){}, get style(){return {};}, querySelectorAll(){return [];}, appendChild(){}, innerHTML: ''});
const sb = {fetch: async () => ({ok: false, status: 404}), document: {getElementById: fakeEl, createElement: fakeEl, querySelectorAll(){return [];}},
  console: {log(){}, warn(){}, error(){}}, Promise, Map, Set, Infinity, Math, JSON, Object, Array, Number, String};
vm.createContext(sb); vm.runInContext(code + '\n;globalThis.__P = DMG_CLASS_PRESETS; globalThis.__E = DMG_EMPTY_PROJECTED;', sb);
const {apps, targets, pairs, grid} = JSON.parse(fs.readFileSync(inPath, 'utf8'));
const out = {presets: sb.__P.map(p => [p.key, p.hull, p.prop, sb.dmgPresetEft(p)]), targets: {}, points: {}};
for (const [id, pt] of Object.entries(targets)) for (const prop of [true, false]) {
  if (prop && !pt.variants.on) continue;
  const t = sb.dmgTargetObj(pt, prop, 1);
  out.targets[id + '|' + prop] = [sb.pyfaTargetValue(t, 'maxVelocity', null, false), sb.pyfaTargetValue(t, 'signatureRadius', null, false)];
}
for (const [a, t] of pairs) {
  const app0 = apps[a], app = Object.assign({}, app0, {projected: app0.projected || sb.__E}), pt = targets[t];
  for (const prop of [true, false]) {
    if (prop && !pt.variants.on) continue;
    const maxU = out.targets[t + '|' + prop][0];
    out.points[a + '|' + t + '|' + prop] = grid.map(g => {
      const r = sb.dmgPoint(app, sb.dmgTargetObj(pt, prop, g.sigScale), {d: g.distance, ySpeed: g.speedFrac * maxU, yAngle: g.tgtAngle, tSpeed: g.atkSpeed, tAngle: g.atkAngle});
      return [r.speed, r.sig, r.dps];
    });
  }
}
fs.writeFileSync(outPath, JSON.stringify(out));
'''

GRID = [dict(distance=d, speedFrac=f, tgtAngle=ta, atkSpeed=asp, atkAngle=aa, sigScale=s)
        for d, f, ta, (asp, aa), s in itertools.product([0, 2000, 7500, 10000, 13400, 20000, 32000, 60000, 120000], [0, 0.5, 1], [0, 90],
                                                        [(0, 0), (400, 0), (400, 90)], [1, 0.4, 2.5])]

def close(a, b):
    if a is None or b is None: return a == b
    return abs(a - b) <= 1e-6 * max(1.0, abs(a), abs(b))

def pyfa_chart_point(src_fit, src_app, inp, tgt, g):
    """getter.py _calculatePoint: tackled speed and painted signature (projected.py), then application.py."""
    speed, sig = CP.pyfa_point(src_fit, tgt, inp, dict(distance=g['distance'], speedFrac=g['speedFrac'], ignoreLockRange=True, ignoreDCR=False, droneMode=1))
    sig *= g['sigScale']
    _, dps = CA.pyfa_point(src_app, dict(distance=g['distance'], atkSpeed=g['atkSpeed'], atkAngle=g['atkAngle'], tgtSpeed=speed,
                                         tgtAngle=g['tgtAngle'], tgtSigRadius=sig, tgtRadius=tgt.getRadius(), ignoreLockRange=True))
    return speed, sig, dps

if __name__ == '__main__':
    ROOT = os.path.join(HERE, '..', '..')
    html = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(ROOT, 'index.html'))
    G = json.load(open(GOLDEN))
    tmp = tempfile.mkdtemp(); dump = os.path.join(tmp, 'd.json')
    subprocess.run(['node', os.path.join(ROOT, 'regression_suite', 'dump_results.mjs'), html, dump, 'application,projectedTarget,moduleStates,droneStates', '-', ','.join(G)],
                   check=True, stdout=subprocess.DEVNULL)
    tool = json.load(open(dump))
    bad, notes = 0, []
    # the presets, through the real engine (their EFT text is the card's own dmgPresetEft)
    src_html = open(html, encoding='utf-8').read()
    presets = re.findall(r"\{key: '(\w+)', label: '([^']+)', hull: '([^']+)', prop: '([^']+)'\}", src_html.split('const DMG_CLASS_PRESETS = [', 1)[1].split('];', 1)[0])
    peft = {f'preset:{k}': f'[{h}, Typical {l.lower()}]\n\n{p}\n' for k, l, h, p in presets}
    pres = run_efts(html, peft, fields=['projectedTarget'])
    targets, pyfa_tgt = {}, {}
    for (k, l, h, p) in presets:
        key = f'preset:{k}'
        pt = pres[key].get('projectedTarget')
        if not pt: bad += 1; notes.append(f'{key}: no projectedTarget from the engine ({pres[key]})'); continue
        targets[key] = pt
        pyfa_tgt[key + '|true'] = CP._Fit(OracleFit(h, [(p, 'active')]).calculate())
        pyfa_tgt[key + '|false'] = CP._Fit(OracleFit(h, [(p, 'online')]).calculate())
        if pt['variants']['propKind'] != 'mwd' or pt['variants']['running'] is not True: bad += 1; notes.append(f"{key}: variants {pt['variants']['propKind']} running {pt['variants']['running']} (expected the MWD, running)")
    # golden fits with a prop module as targets: the tool's own states, the prop module switched by hand on pyfa's side
    gt = [k for k in G if (tool[k].get('projectedTarget') or {}).get('variants', {}).get('propTypeId')]
    gt = gt[::max(1, len(gt) // 8)][:8]
    for k in gt:
        pt = tool[k]['projectedTarget']; v = pt['variants']; tid = str(v['propTypeId'])
        states, drones = CP.tool_states(tool[k])
        st = states.get(tid) or {'active': 0, 'online': 1, 'offline': 0}
        n = st['active'] + st['online'] + st['offline']
        on = dict(states); on[tid] = st if v['running'] else {'active': 1, 'online': n - 1, 'offline': 0}
        off = dict(states); off[tid] = {'active': 0, 'online': n - st['offline'], 'offline': st['offline']}
        targets[k] = pt
        pyfa_tgt[k + '|true'] = CP._Fit(oracle_for(k, states=on, drones=drones, group_limits=False))
        pyfa_tgt[k + '|false'] = CP._Fit(oracle_for(k, states=off, drones=drones, group_limits=False))
    # attackers: golden fits with weapons, every one with tackle and a few without
    withw = [k for k in G if ((tool[k].get('application') or {}).get('weapons'))]
    tackle = [k for k in withw if any(((tool[k]['application'].get('projected') or {}).get(x)) for x in ('webMods', 'tpMods', 'webDrones', 'tpDrones'))
              or (tool[k]['application'].get('projected') or {}).get('scramRange') is not None]
    plain = [k for k in withw if k not in tackle]
    attackers = tackle[:10] + plain[::max(1, len(plain) // 4)][:4]
    # v2026.10.14.40 (drones applied): drone ships among the attackers, every one with damage drones in space
    withd = [k for k in G if (tool[k].get('application') or {}).get('drones') and k not in attackers]
    attackers += withd[::max(1, len(withd) // 4)][:4]
    src_fit, src_app, inputs = {}, {}, {}
    for a in attackers:
        states, drones = CP.tool_states(tool[a])
        o = oracle_for(a, states=states, drones=drones, group_limits=False)
        if o.errors or o.oracleGaps: bad += 1; notes.append(f'{a}: ORACLE errors {o.errors} gaps {o.oracleGaps}'); continue
        src_fit[a] = CP._Fit(o); src_app[a] = CA._Src(o); inputs[a] = CP.pyfa_inputs(src_fit[a])
    pairs = [(a, t) for a in src_fit for t in targets]
    gin, gout, js = os.path.join(tmp, 'in.json'), os.path.join(tmp, 'out.json'), os.path.join(tmp, 'run.js')
    open(js, 'w').write(NODE)
    json.dump({'apps': {a: tool[a]['application'] for a in src_fit}, 'targets': targets, 'pairs': pairs, 'grid': GRID}, open(gin, 'w'))
    subprocess.run(['node', js, html, gin, gout], check=True)
    out = json.load(open(gout))
    for key, (tv, ts) in out['targets'].items():
        f = pyfa_tgt[key]
        if not (close(tv, f.getMaxVelocity()) and close(ts, f.getSigRadius())):
            bad += 1; notes.append(f'{key} (target): maxVelocity tool {tv} pyfa {f.getMaxVelocity()}; signatureRadius tool {ts} pyfa {f.getSigRadius()}')
    points = exact = applied_lt_raw = 0
    for a, t in pairs:
        for prop in ('true', 'false'):
            k = f'{a}|{t}|{prop}'
            if k not in out['points']: continue
            tgt = pyfa_tgt[f'{t}|{prop}']; diffs = []
            for i, g in enumerate(GRID):
                ps, pg, pd = pyfa_chart_point(src_fit[a], src_app[a], inputs[a], tgt, g); points += 1
                ts, tg, td = out['points'][k][i]
                if not (close(ts, ps) and close(tg, pg) and close(td, pd)):
                    if len(diffs) < 3: diffs.append(f'{g} tool ({ts}, {tg}, {td}) pyfa ({ps}, {pg}, {pd})')
                elif td == pd: exact += 1
            if diffs: bad += 1; notes.append(f'{k}: ' + '; '.join(diffs))
    for n in notes[:40]: print(n)
    print(f'{len(src_fit)} attackers x {len(targets)} targets ({len(presets)} class presets) x prop on / off, {points} points, {exact} DPS values bit-identical')
    print(f'{bad} mismatches (card points vs pyfa calc/projected.py + calc/application.py, grid of {len(GRID)})')
