// node regression_suite/dump_results.mjs [index.html] out.json [field,field...] [mode] [fitId,fitId...]
// Runs every golden fit through the real estimateHpAndDps() (same harness as run_regression.mjs)
// and writes {fitId: {field: value}} -- for the independent comparisons in tools/independent_checks.
import fs from 'fs'; import vm from 'vm'; import path from 'path'; import { fileURLToPath } from 'url';
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const [htmlPath = path.join(__dirname, '..', 'index.html'), outPath, fieldList, modeOverride, fitList] = process.argv.slice(2);
const onlyFits = fitList ? new Set(fitList.split(',')) : null;
const golden = JSON.parse(fs.readFileSync(path.join(__dirname, 'golden_fits.json'), 'utf8'));
const code = [...fs.readFileSync(htmlPath, 'utf8').matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');
const fields = fieldList ? fieldList.split(',') : null;
const out = {};
for (const [id, fit] of Object.entries(golden)) {
  if (onlyFits && !onlyFits.has(id)) continue;
  const fakeFetch = async url => { const t = url.match(/\/universe\/types\/(\d+)\//), g = url.match(/\/universe\/groups\/(\d+)\//);
    const r = t ? fit.types[t[1]] : g ? fit.groups[g[1]] : null; return r ? {ok: true, json: async () => r} : {ok: false, status: 404}; };
  const fakeEl = () => ({addEventListener(){}, get style(){return {};}, querySelectorAll(){return [];}, appendChild(){}, innerHTML: ''});
  const sb = {fetch: fakeFetch, document: {getElementById: fakeEl, createElement: fakeEl}, console: {log(){}, warn(){}, error(){}}, Promise, Map, Set, Infinity, Math, JSON, Object, Array, Number, String};
  vm.createContext(sb); vm.runInContext(code, sb);
  let tally = fit.tally, cargo = new Set([...Object.keys(fit.tally?.['Cargo'] || {}), ...Object.keys(fit.tally?.['Fleet hangar'] || {})].map(Number));
  let hs = new Map(Object.entries(fit.highSlotByFlag || {}).map(([k, v]) => [Number(k), v])), ms = new Map(Object.entries(fit.midSlotByFlag || {}).map(([k, v]) => [Number(k), v]));
  if (fit.killmail) ({tally, cargoItemIds: cargo, highSlotByFlag: hs, midSlotByFlag: ms} = sb.buildLossTally(fit.killmail));
  try {
    const r = JSON.parse(JSON.stringify(await sb.estimateHpAndDps(fit.shipTypeId, tally, cargo, hs, (modeOverride && modeOverride !== '-') ? modeOverride : (fit.tacticalMode || 'sharpshooter'), ms, fit.moduleStates || null, fit.droneStates || null, fit.fitSource ? {fitSource: fit.fitSource} : null)));
    out[id] = fields ? Object.fromEntries(fields.map(f => [f, r[f]])) : r;
  } catch (e) { out[id] = {error: String(e)}; }
}
fs.writeFileSync(outPath, JSON.stringify(out));
console.log(`${Object.keys(out).length} fits -> ${outPath}`);
