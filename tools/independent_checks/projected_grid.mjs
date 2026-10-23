// node tools/independent_checks/projected_grid.mjs index.html in.json out.json
// Helper for check_projected.py (v2026.10.14.35): loads index.html's script in a Node vm (no page, no network),
// then for each (attacker, target) pair evaluates PYFA CORE projected -- pyfaProjectedPoint, the target's speed
// under the attacker's webs / scram and its signature radius under the painters -- at every grid point.
// in.json: {apps: {fitId: estimate.application}, targets: {fitId: estimate.projectedTarget}, pairs: [[att, tgt]],
//           grid: [{distance, speedFrac, ignoreLockRange, ignoreDCR, droneMode}]}
// out.json: {targets: {fitId: [maxVelocity, signatureRadius]}, points: {"att|tgt": [[speed, sig] per point]}}
import fs from 'fs'; import vm from 'vm';
const [htmlPath, inPath, outPath] = process.argv.slice(2);
const code = [...fs.readFileSync(htmlPath, 'utf8').matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');
const fakeEl = () => ({addEventListener(){}, get style(){return {};}, querySelectorAll(){return [];}, appendChild(){}, innerHTML: ''});
const sb = {fetch: async () => ({ok: false, status: 404}), document: {getElementById: fakeEl, createElement: fakeEl}, console: {log(){}, warn(){}, error(){}},
  Promise, Map, Set, Infinity, Math, JSON, Object, Array, Number, String};
vm.createContext(sb); vm.runInContext(code, sb);
const {apps, targets, pairs, grid} = JSON.parse(fs.readFileSync(inPath, 'utf8'));
const out = {targets: {}, points: {}};
for(const [id, t] of Object.entries(targets)) out.targets[id] = [sb.pyfaTargetValue(t, 'maxVelocity', null, false), sb.pyfaTargetValue(t, 'signatureRadius', null, false)];
for(const [a, t] of pairs){
  const app = apps[a], tgt = targets[t];
  const maxU = sb.pyfaTargetValue(tgt, 'maxVelocity', null, false);
  out.points[a + '|' + t] = grid.map(p => {
    const r = sb.pyfaProjectedPoint(app, tgt, {distance: p.distance, tgtSpeed: p.speedFrac * maxU, ignoreLockRange: p.ignoreLockRange, ignoreDCR: p.ignoreDCR, droneMode: p.droneMode});
    return [r.tgtSpeed, r.tgtSigRadius];
  });
}
fs.writeFileSync(outPath, JSON.stringify(out));
