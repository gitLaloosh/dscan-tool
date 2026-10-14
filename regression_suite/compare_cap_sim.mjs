// Compare index.html's capSimPyfa() with pyfa's own eos/capSim.py on every golden fit.
//   node regression_suite/compare_cap_sim.mjs index.html            (needs PYFA_SRC, python3)
// For each fit the engine's capacitor.simInputs (best case, ASB out of charges,
// without boosts) go to tools/cap_sim_oracle.py; the JS results must match exactly
// (stable flag; stable %, time to empty and EVE value after rounding pyfa's raw values to 0.1).
import fs from 'fs'; import vm from 'vm'; import path from 'path'; import os from 'os';
import { execFileSync } from 'child_process';
import { fileURLToPath } from 'url';
const here = path.dirname(fileURLToPath(import.meta.url));
const htmlPath = process.argv[2] || path.join(here, '..', 'index.html');
const golden = JSON.parse(fs.readFileSync(path.join(here, 'golden_fits.json'), 'utf8'));
const code = fs.readFileSync(htmlPath, 'utf8').match(/<script>([\s\S]*)<\/script>/)[1];
const cases = [], jsResults = {};
for (const [fid, fit] of Object.entries(golden)) {
  const fakeFetch = async (url) => { const tm = url.match(/\/universe\/types\/(\d+)\//), gm = url.match(/\/universe\/groups\/(\d+)\//);
    if (tm && fit.types[tm[1]]) return { ok: true, json: async () => fit.types[tm[1]] };
    if (gm && fit.groups[gm[1]]) return { ok: true, json: async () => fit.groups[gm[1]] };
    return { ok: false, status: 404 }; };
  const fakeEl = () => ({ addEventListener() {}, get style() { return {}; }, querySelectorAll() { return []; }, appendChild() {}, get innerHTML() { return ''; }, set innerHTML(v) {} });
  const sb = { fetch: fakeFetch, document: { getElementById() { return fakeEl(); }, createElement() { return fakeEl(); } }, console, Promise, Map, Set, Infinity, Math, JSON, Object, Array, Number, String };
  vm.createContext(sb); vm.runInContext(code, sb);
  let tally, cargo, hs, ms;
  if (fit.killmail) ({ tally, cargoItemIds: cargo, highSlotByFlag: hs, midSlotByFlag: ms } = sb.buildLossTally(fit.killmail));
  else { tally = fit.tally; cargo = new Set(Object.keys(tally['Cargo'] || {}).map(Number)); hs = new Map(Object.entries(fit.highSlotByFlag || {}).map(([k, v]) => [Number(k), v])); ms = new Map(Object.entries(fit.midSlotByFlag || {}).map(([k, v]) => [Number(k), v])); }
  const r = await sb.estimateHpAndDps(fit.shipTypeId, tally, cargo, hs, fit.tacticalMode || 'sharpshooter', ms, fit.moduleStates || null, fit.droneStates || null);
  const si = r.capacitor && r.capacitor.simInputs;
  if (!si) continue;
  for (const v of ['best', 'asbDry', 'withoutBoosts']) {
    const id = `${fid}:${v}`;
    cases.push({ id, capacity: si.capacity, rechargeMs: si.rechargeMs, drains: si[v] });
    jsResults[id] = sb.capSimPyfa(si.capacity, si.rechargeMs, si[v]);
  }
}
const tmp = path.join(os.tmpdir(), 'cap_sim_cases.json');
fs.writeFileSync(tmp, JSON.stringify(cases));
const oracle = JSON.parse(execFileSync('python3', ['-I', path.join(here, '..', 'tools', 'cap_sim_oracle.py'), tmp], { maxBuffer: 1 << 26 }).toString());
let mismatches = 0, errors = 0, unstable = 0;
for (const o of oracle) {
  const j = jsResults[o.id];
  if (o.skipped) continue;
  if (o.error) { errors++; console.log('  PYFA ERROR', o.id, o.error, '| JS', JSON.stringify(j)); continue; }
  if (!o.stable) unstable++;
  const r1 = v => (v === null || v === undefined) ? null : Math.round(v * 10) / 10; // the oracle returns unrounded values
  const same = j.stable === o.stable && j.stablePct === r1(o.stablePct) && j.timeToEmptySec === r1(o.timeToEmptySec) && j.eveStablePct === r1(o.eveStablePct);
  if (!same) { mismatches++; console.log('  MISMATCH', o.id, 'JS', JSON.stringify(j), 'pyfa', JSON.stringify(o)); }
}
console.log(`${oracle.length} simulations (${unstable} unstable), ${mismatches} mismatches, ${errors} pyfa errors`);
process.exit(mismatches ? 1 : 0);
