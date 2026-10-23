// node tools/independent_checks/application_grid.mjs index.html in.json out.json
// Helper for check_application.py (v2026.10.14.34): loads index.html's script in a Node vm (no page, no network),
// then, for each fit's estimate.application in in.json ({fits: {fitId: application}, grid: [params...]}), evaluates
// PYFA CORE application -- pyfaApplicationMult per weapon and pyfaAppliedDps -- at every grid point.
// Writes {fitId: {mults: {weaponKey: [m per point]}, total: [dps per point]}}.
import fs from 'fs'; import vm from 'vm';
const [htmlPath, inPath, outPath] = process.argv.slice(2);
const code = [...fs.readFileSync(htmlPath, 'utf8').matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');
const fakeEl = () => ({addEventListener(){}, get style(){return {};}, querySelectorAll(){return [];}, appendChild(){}, innerHTML: ''});
const sb = {fetch: async () => ({ok: false, status: 404}), document: {getElementById: fakeEl, createElement: fakeEl}, console: {log(){}, warn(){}, error(){}},
  Promise, Map, Set, Infinity, Math, JSON, Object, Array, Number, String};
vm.createContext(sb); vm.runInContext(code, sb);
const {fits, grid} = JSON.parse(fs.readFileSync(inPath, 'utf8'));
const out = {};
for (const [id, app] of Object.entries(fits)) {
  const mults = {};
  for (const w of app.weapons) mults[`${w.weaponTypeId}:${w.ammoTypeId ?? ''}`] = grid.map(p =>
    sb.pyfaApplicationMult(w, Object.assign({atkRadius: app.radius, lockRange: app.lockRange}, p)));
  out[id] = {mults, total: grid.map(p => sb.pyfaAppliedDps(app, p))};
}
fs.writeFileSync(outPath, JSON.stringify(out));
