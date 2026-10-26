#!/usr/bin/env node
// Golden-fit scaffolder (Phase 5 of the architectural remediation plan, see
// [[dscan-tool-architecture]]).
//
// WHY THIS EXISTS: every golden fit in regression_suite/golden_fits.json so
// far was built by hand -- opening browser tabs, fetching each referenced
// item's /universe/types/{id}/ and /universe/groups/{id}/ dogma from ESI one
// at a time, and hand-typing the JSON into the file. Pure transcription-error
// risk for a mechanical task. This script automates that mechanical part:
// given a real killmail, it fetches the real killmail from ESI, every type/
// group it references, and emits a ready-to-paste golden_fits.json entry in
// the exact shape the regression harness (run_regression.mjs) already
// understands -- the newer `killmail` field shape (added 2026-10-09), which
// runs the tool's REAL buildLossTally() on it, not a hand-assembled tally.
//
// WHAT THIS DOES NOT AUTOMATE, ON PURPOSE: the actual ground-truth numbers
// (dpsFixed, shieldHP, armorHP, hullHP) still need a real pyfa cross-check
// before this fit can be trusted as a regression guard -- that is the one
// step in this whole project that is NOT mechanical, it's the actual
// verification, and automating it away would violate this project's
// standing "verify against primary sources, don't guess" rule. What this
// script DOES do instead: it runs the tool's own estimateHpAndDps() against
// the freshly-built fit (same vm-sandbox technique used throughout this
// project's test scripts) and writes that as a PROVISIONAL `expected` block,
// clearly labeled as not-yet-pyfa-verified, with a wide tolerance -- so you
// aren't starting from a blank "expected" object, but you still have to
// either (a) export this fit to pyfa (use the printed EFT-ish module list as
// a cross-check, or better, hand-build the fit in pyfa from the killmail)
// and tighten the numbers to match, or (b) consciously decide the tool's own
// output is trustworthy enough as a structural regression floor for this
// particular fit (same category as e.g. the Vorton Projector/Fighter Bay
// golden fits, which pyfa doesn't support yet and were hand-derived instead).
//
// USAGE:
//   node scaffold_golden_fit.mjs <killmail_id> [killmail_hash] [options]
//
// If killmail_hash is omitted, it's resolved via zKillboard's own API
// (https://zkillboard.com/api/killID/<id>/) -- the same hash-lookup step the
// live tool's own fetchKillmail() relies on (there it comes from a loss-list
// stub's `.zkb.hash`; a single killmail has no stub, so this script asks
// zKillboard directly for just that one killmail's hash).
//
// Options:
//   --label "text"      Human label for the fit (default: auto-built from
//                        the victim ship's real name + killmail id)
//   --id slug           Key to use in golden_fits.json (default: auto-slug
//                        of the ship name + "_zkb<id>")
//   --html path          Path to dscan-tool.html to run the provisional
//                        estimateHpAndDps() pass against (default: looks for
//                        dscan-tool.html next to this script, then in the
//                        current directory)
//   --out path          Write the single-entry JSON here (default: print to
//                        stdout only)
//   --merge-into path   Read this golden_fits.json-shaped file, insert the
//                        new entry, and write it back (2-space indent,
//                        matching the existing file's style). Refuses if the
//                        id already exists unless --force is also given.
//                        Without this flag, nothing is merged automatically
//                        -- review the provisional `expected` block first.
//   --force             Allow --merge-into to overwrite an existing id.
//   --tolerance-pct N   Tolerance (%) for the provisional DPS/HP ranges
//                        (default: 5 -- wider than a real pyfa-pinned fit's
//                        usual 1%, since this hasn't been cross-checked yet)
//
// EXIT CODES: 0 success, 1 ESI/zKillboard fetch failure, 2 bad usage/args,
// 3 dscan-tool.html not found or has no <script> block (the fit JSON is
// still printed/written in this case -- only the provisional `expected`
// pre-fill is skipped, with a note saying so).

import fs from 'fs';
import path from 'path';
import vm from 'vm';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SHARED = JSON.parse(fs.readFileSync(path.join(__dirname, 'shared_types.json'), 'utf8'));

const ESI = 'https://esi.evetech.net/latest';
const ZKB = 'https://zkillboard.com/api';
// zKillboard's API usage policy asks for a descriptive User-Agent so they
// can reach you if something's wrong with your usage pattern. Personalize
// this with your own contact info if you plan to run this often -- left
// generic by default rather than baking in any personal identifying info.
const USER_AGENT = 'dscan-tool-golden-fit-scaffolder/1.0 (personal fitting-analysis script)';
const REQUEST_DELAY_MS = 150; // polite pacing between sequential ESI/zKB calls

function usage(msg) {
  if (msg) console.error('Error: ' + msg + '\n');
  console.error('Usage: node scaffold_golden_fit.mjs <killmail_id> [killmail_hash] [options]');
  console.error('See the comment block at the top of this file for the full option list.');
  process.exit(2);
}

function parseArgs(argv) {
  const positional = [];
  const opts = { toleranceCpt: 5 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--label') opts.label = argv[++i];
    else if (a === '--id') opts.id = argv[++i];
    else if (a === '--html') opts.html = argv[++i];
    else if (a === '--out') opts.out = argv[++i];
    else if (a === '--merge-into') opts.mergeInto = argv[++i];
    else if (a === '--force') opts.force = true;
    else if (a === '--tolerance-pct') opts.toleranceCpt = Number(argv[++i]);
    else if (a.startsWith('--')) usage(`unknown option ${a}`);
    else positional.push(a);
  }
  if (positional.length < 1) usage('killmail_id is required');
  opts.killmailId = positional[0];
  opts.hash = positional[1];
  return opts;
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function slugify(s) {
  return String(s).toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
}

// Shared fetch-with-description helper -- same spirit as the live tool's own
// describeEsiFailure() (Phase 4): distinguishes network failure / 404 / rate
// limit / other non-2xx, always naming the failing URL, with one retry on a
// 420/429/5xx after a short backoff (ESI and zKillboard both rate-limit).
async function fetchJson(url, { retries = 2 } = {}) {
  for (let attempt = 0; attempt <= retries; attempt++) {
    let res;
    try {
      res = await fetch(url, { headers: { 'User-Agent': USER_AGENT, Accept: 'application/json' } });
    } catch (e) {
      if (attempt < retries) { await sleep(500 * (attempt + 1)); continue; }
      throw new Error(`Network failure fetching ${url}: ${e.message}`);
    }
    if (res.ok) return res.json();
    if ((res.status === 420 || res.status === 429 || res.status >= 500) && attempt < retries) {
      const retryAfter = Number(res.headers.get('retry-after')) || (1 + attempt);
      await sleep(retryAfter * 1000);
      continue;
    }
    if (res.status === 404) throw new Error(`404 Not Found fetching ${url} (bad id, or this killmail/type/group doesn't exist)`);
    throw new Error(`HTTP ${res.status} fetching ${url}`);
  }
}

async function resolveHash(killmailId, givenHash) {
  if (givenHash) return givenHash;
  console.error(`Resolving killmail hash via zKillboard for killmail ${killmailId}...`);
  const data = await fetchJson(`${ZKB}/killID/${killmailId}/`);
  const entry = Array.isArray(data) ? data[0] : data;
  const hash = entry && entry.zkb && entry.zkb.hash;
  if (!hash) throw new Error(`zKillboard returned no hash for killmail ${killmailId} -- it may not exist, or zKillboard hasn't indexed it yet. Pass the hash explicitly as the 2nd argument if you have it (e.g. from the killmail's own ESI link).`);
  return hash;
}

async function fetchKillmail(killmailId, hash) {
  console.error(`Fetching killmail ${killmailId} from ESI...`);
  return fetchJson(`${ESI}/killmails/${killmailId}/${hash}/?datasource=tranquility`);
}

async function fetchType(typeId, cache) {
  if (cache.has(typeId)) return cache.get(typeId);
  await sleep(REQUEST_DELAY_MS);
  console.error(`  fetching type ${typeId}...`);
  const data = await fetchJson(`${ESI}/universe/types/${typeId}/?datasource=tranquility`);
  cache.set(typeId, data);
  return data;
}

async function fetchGroup(groupId, cache) {
  if (cache.has(groupId)) return cache.get(groupId);
  await sleep(REQUEST_DELAY_MS);
  console.error(`  fetching group ${groupId}...`);
  const data = await fetchJson(`${ESI}/universe/groups/${groupId}/?datasource=tranquility`);
  cache.set(groupId, data);
  return data;
}

function findDscanToolHtml(explicitPath) {
  const candidates = [
    explicitPath,
    path.join(__dirname, 'dscan-tool.html'),
    path.join(process.cwd(), 'dscan-tool.html'),
    path.join(__dirname, '..', 'dscan-tool.html'),
    path.join(__dirname, '..', 'index.html'),
  ].filter(Boolean);
  for (const c of candidates) {
    if (fs.existsSync(c)) return c;
  }
  return null;
}

// Runs the REAL tool's buildLossTally()/estimateHpAndDps() against the
// freshly-scaffolded fit, inside a vm sandbox fed only the types/groups we
// just fetched (same technique as run_regression.mjs and this project's
// other verification scripts) -- so the provisional `expected` block comes
// from the tool's actual current behavior, not a hand guess.
async function computeProvisionalExpected(htmlPath, killmail, typesMap, groupsMap) {
  const html = fs.readFileSync(htmlPath, 'utf8');
  const m = html.match(/<script>([\s\S]*)<\/script>/);
  if (!m) return null;
  const code = m[1];

  async function fakeFetch(url) {
    const typeMatch = url.match(/\/universe\/types\/(\d+)\//);
    const groupMatch = url.match(/\/universe\/groups\/(\d+)\//);
    if (typeMatch) {
      const id = typeMatch[1];
      // shared_types.json (v2026.10.14.73): the generic Fighter tile's types, fetched for every fit (run_regression.mjs falls back to it too)
      const r = typesMap[id] || SHARED.types[id];
      if (r) return { ok: true, json: async () => r };
      return { ok: false, status: 404 };
    }
    if (groupMatch) {
      const id = groupMatch[1];
      const r = groupsMap[id] || SHARED.groups[id];
      if (r) return { ok: true, json: async () => r };
      return { ok: false, status: 404 };
    }
    return { ok: false, status: 404 };
  }
  function fakeEl() {
    return { addEventListener() {}, get style() { return {}; }, querySelectorAll() { return []; }, appendChild() {}, get innerHTML() { return ''; }, set innerHTML(v) {} };
  }
  const fakeDocument = { getElementById() { return fakeEl(); }, createElement() { return fakeEl(); } };
  const sandbox = { fetch: fakeFetch, document: fakeDocument, console, Promise, Map, Set, Infinity, Math, JSON, Object, Array, Number, String };
  vm.createContext(sandbox);
  vm.runInContext(code, sandbox);

  const { tally, cargoItemIds, highSlotByFlag } = sandbox.buildLossTally(killmail);
  const result = await sandbox.estimateHpAndDps(killmail.victim.ship_type_id, tally, cargoItemIds, highSlotByFlag);
  return result;
}

function buildProvisionalExpected(result, toleranceCpt) {
  if (!result) {
    return {
      note: 'PROVISIONAL BLOCK NOT COMPUTED -- dscan-tool.html was not found next to this script (pass --html <path>), so no automatic expected values could be generated. Fill this in by hand: a real pyfa cross-check (preferred), or by running the tool against this fit and hand-verifying the numbers against live ESI, same bar as every other golden fit in this file.',
      tolerancePct: toleranceCpt,
    };
  }
  const exp = {
    note: `PROVISIONAL -- auto-generated ${new Date().toISOString().slice(0, 10)} by scaffold_golden_fit.mjs from the tool's OWN estimateHpAndDps() output. NOT cross-checked against pyfa yet. Before trusting this as a real regression guard: either (a) build this fit in pyfa from the killmail's own module list and tighten these numbers/tolerance to match a real pyfa export, or (b) if pyfa doesn't support something on this fit (a weapon system it doesn't model, etc.), hand-derive the expected DPS/EHP from live ESI dogma the way the Vorton Projector/Fighter Bay/Entropic Disintegrator golden fits did, and replace this note once done.`,
    confirmedWeaponCount: result.confirmedWeaponCount,
    cargoResolvedWeaponCount: result.cargoResolvedWeaponCount,
    unmatchedWeaponCount: result.unmatchedWeaponCount,
    variableWeaponCount: result.variableWeaponCount,
    droneCount: result.droneCount,
    droneBayCount: result.droneBayCount,
    tolerancePct: toleranceCpt,
  };
  if (result.fighterBayCount) {
    exp.fighterSquadronCount = result.fighterSquadronCount;
    exp.fighterBayCount = result.fighterBayCount;
  }
  if (Array.isArray(result.ammoEstimates)) {
    exp.ammoEstimatesCount = result.ammoEstimates.length;
  }
  // Numbers that actually depend on skill/damage assumptions a pyfa
  // cross-check could catch a divergence in -- these go in as a range, not
  // pinned exact, reflecting that they are NOT yet independently verified.
  const band = (v) => {
    if (v === undefined || v === null) return undefined;
    return { min: Math.round(v * (1 - toleranceCpt / 100)), max: Math.round(v * (1 + toleranceCpt / 100)) };
  };
  for (const [field, val] of [
    ['dpsFixed', result.dpsFixed],
    ['droneDps', result.droneDps],
    ['shieldHP', result.shieldHP],
    ['armorHP', result.armorHP],
    ['hullHP', result.hullHP],
    ['totalHP', result.totalHP],
  ]) {
    const b = band(val);
    if (b) {
      exp[field + '_min'] = b.min;
      exp[field + '_max'] = b.max;
    }
  }
  // Remove undefined keys (some fields won't exist on every fit, e.g. no
  // fighters/drones) so the printed JSON stays clean.
  for (const k of Object.keys(exp)) if (exp[k] === undefined) delete exp[k];
  return exp;
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));

  const hash = await resolveHash(opts.killmailId, opts.hash);
  const killmail = await fetchKillmail(opts.killmailId, hash);

  if (!killmail || !killmail.victim || !killmail.victim.ship_type_id) {
    throw new Error('Killmail fetched successfully but has no victim.ship_type_id -- unexpected shape, aborting.');
  }

  const shipTypeId = killmail.victim.ship_type_id;
  const itemTypeIds = new Set([shipTypeId]);
  for (const it of killmail.victim.items || []) itemTypeIds.add(it.item_type_id);

  console.error(`Killmail references ${itemTypeIds.size} unique type ids (ship + items). Fetching each from ESI...`);
  const typeCache = new Map();
  const typesMap = {};
  const groupIds = new Set();
  for (const typeId of itemTypeIds) {
    const t = await fetchType(typeId, typeCache);
    typesMap[String(typeId)] = t;
    if (t && t.group_id) groupIds.add(t.group_id);
  }

  console.error(`Referencing ${groupIds.size} unique group ids. Fetching each from ESI...`);
  const groupCache = new Map();
  const groupsMap = {};
  for (const groupId of groupIds) {
    const g = await fetchGroup(groupId, groupCache);
    groupsMap[String(groupId)] = g;
  }

  const shipName = (typesMap[String(shipTypeId)] && typesMap[String(shipTypeId)].name) || `type ${shipTypeId}`;
  const label = opts.label || `${shipName} (zKillboard ${opts.killmailId})`;
  const fitId = opts.id || `${slugify(shipName)}_zkb${opts.killmailId}`;

  const htmlPath = findDscanToolHtml(opts.html);
  let provisionalResult = null;
  let computeError = null;
  if (htmlPath) {
    console.error(`Running the tool's own estimateHpAndDps() against this fit (${htmlPath}) for a provisional expected block...`);
    try {
      provisionalResult = await computeProvisionalExpected(htmlPath, killmail, typesMap, groupsMap, groupsMap);
    } catch (e) {
      computeError = e;
      console.error(`  (could not compute a provisional expected block: ${e.message})`);
    }
  } else {
    console.error('dscan-tool.html not found (pass --html <path>) -- skipping the provisional expected block.');
  }

  const expected = buildProvisionalExpected(provisionalResult, opts.toleranceCpt);
  if (computeError) {
    expected.note = `PROVISIONAL BLOCK NOT COMPUTED -- the tool's own estimateHpAndDps() threw while evaluating this fit: ${computeError.message}. This likely means the fit hits a code path with a real bug, or an ESI shape this script didn't anticipate -- worth investigating before treating this as a normal golden fit. Fill in "expected" by hand once that's understood.`;
  }

  const entry = {
    label,
    shipTypeId,
    types: typesMap,
    groups: groupsMap,
    killmail,
    expected,
  };

  const printed = JSON.stringify({ [fitId]: entry }, null, 2);

  if (opts.out) {
    fs.writeFileSync(opts.out, printed, 'utf8');
    console.error(`Wrote standalone entry to ${opts.out}`);
  } else {
    console.log(printed);
  }

  if (opts.mergeInto) {
    if (!fs.existsSync(opts.mergeInto)) throw new Error(`--merge-into path does not exist: ${opts.mergeInto}`);
    const golden = JSON.parse(fs.readFileSync(opts.mergeInto, 'utf8'));
    if (golden[fitId] && !opts.force) {
      throw new Error(`"${fitId}" already exists in ${opts.mergeInto} -- pass --force to overwrite, or --id to pick a different key.`);
    }
    golden[fitId] = entry;
    fs.writeFileSync(opts.mergeInto, JSON.stringify(golden, null, 2), 'utf8');
    console.error(`Merged "${fitId}" into ${opts.mergeInto}. Re-run the regression suite before delivering anything.`);
  }

  console.error(`\nDone. Fit id: "${fitId}"`);
  console.error(computeError
    ? 'IMPORTANT: the provisional expected block could not be computed -- see the note above, investigate before using this fit.'
    : 'IMPORTANT: the expected block is PROVISIONAL (tool-computed, not pyfa-verified). Review it before merging/trusting, per the note inside it.');
}

main().catch(e => {
  console.error('\nFAILED: ' + e.message);
  process.exit(1);
});
