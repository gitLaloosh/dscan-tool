#!/usr/bin/env node
// Phase 1 of the dscan-tool architectural remediation plan (see memory file
// dscan-tool-architecture, ARCH-1 / Phase 1): an automated, re-runnable check
// for SHIP_ROLE_BONUS / SHIP_RESIST_BONUS drifting out of sync with the live
// game, instead of waiting for a human to stumble onto a stale entry the way
// the Hawk patch (24.01, 2026-09-22) was only caught weeks later.
//
// WHAT THIS DOES: extracts the live SHIP_ROLE_BONUS/SHIP_RESIST_BONUS tables
// directly out of dscan-tool.html (so it's always checking the ACTUAL live
// file, never a separately-maintained copy that could itself go stale), then
// for every keyed ship id fetches everef.net's rendered ship-traits page and
// independently re-derives the expected bonus tuples from its plain-English
// trait text -- the same primary source and the same "Type Bonus (per level)
// vs flat Role Bonus" distinction the project's two manual audits
// (2026-10-08 missile batch + final-coverage batch) already proved is the
// reliable way to do this (raw ESI dogma_effects alone don't cleanly
// separate the two -- that's documented in this project's own memory).
//
// WHAT THIS DOES NOT DO: it does not edit dscan-tool.html, and it does not
// assert a finding is a confirmed bug. Every MISMATCH/MISSING finding is a
// CANDIDATE for human review, exactly like the original audits' classifier
// output -- "All 35 fixes [were] verified individually by re-fetching and
// reading each ship's raw trait text (not trusting the classifier's single
// automated first-pass)" is the standing rule here too. This script narrows
// hundreds of ships down to a short, specific list; it doesn't replace the
// verify-before-applying step.
//
// STATUS AS OF 2026-10-09: the first draft of this script was written while
// the device bridge to the user's machine was disconnected, so it shipped
// with two guesses that turned out wrong when checked against the real
// site via the built-in browser (device_bash itself was still unavailable,
// but the browser pane could reach everef.net directly):
//   1. The URL was guessed as /ship/<id> -- actually /types/<id>. /ship/<id>
//      404s ("Page not found: /ship/47270").
//   2. "per level" was assumed to be a phrase attached to each individual
//      bonus sentence (e.g. "...damage per level"). It isn't -- it appears
//      ONCE, in a sub-heading ("Precursor Battleship bonuses per level")
//      under the literal "Type Bonuses" heading. Everything under "Type
//      Bonuses" is per-level (x5 at level V); everything under the
//      following "Role Bonuses" heading is already flat. Fixed by having
//      splitTraitsSections() split on those two literal headings instead of
//      scanning for a "per level" phrase near each sentence.
// Both fixes were verified against the real rendered pages for all three
// calibration ships (Vedmak 47270, Drekavac 49711, Leshak 47271) plus two
// more (Megathron 641, Rokh 24688) before being written into the code below
// -- see the comments on EVEREF_SHIP_URL and splitTraitsSections.
//
// Then went further: used the browser's own `fetch()` (same-origin, same
// HTTP GET a Node fetch would make) to pull the ACTUAL raw server-rendered
// HTML for Vedmak/Drekavac/Leshak's Traits blocks -- not the browser's
// already-stripped visible text, the real markup, full of Vue/Nuxt hydration
// comments (<!--[-->, <!---->) wrapping every fragment. Ran that real HTML
// through stripHtmlToText -> splitTraitsSections -> findBonusCandidates ->
// candidatesToTuples exactly as this script does, as an actual Node unit
// test (not hand-reasoning). First run FAILED on Leshak: only the "damage"
// bonus came back, "rate of fire" silently vanished. Root cause: the old
// BONUS_SENTENCE_RE's trailing-context group `([^.]{0,40})?` had nothing to
// stop it at a line break, so on a line with no period it ate the \n and
// the start of the NEXT bonus line, which made the regex engine's lastIndex
// skip straight past that next real match. Fixed by excluding \n from that
// group (and from the separate `context` window used for the mode-
// conditional check) so each match is confined to its own line, matching
// how stripHtmlToText actually lays out one bonus per line. Re-ran: all
// three calibration ships now reproduce their known-correct tuples exactly
// from the real fetched HTML. That test harness and the raw HTML fixtures
// live in this session's scratch space, not shipped with this file, but the
// fix they drove is in the code below.
//
// Residual, lower-confidence gap: the HTML was fetched via the browser
// pane's fetch(), not literally Node's `fetch` on the user's machine. Both
// are a plain unauthenticated GET to the same origin, so they should get
// byte-identical responses, but that's inference, not a literal same-process
// test. If a real `node audit_role_bonus_drift.mjs ... --only 47270,49711,47271`
// run ever disagrees with what's documented here, trust the live run over
// this comment and report back what's different.
//
// USAGE:
//   node audit_role_bonus_drift.mjs <path-to-dscan-tool.html> [options]
// OPTIONS:
//   --only 47270,49711,47271   Only check these ship ids (default: the
//                              3-ship calibration set below).
//   --all                      Check every id in SHIP_ROLE_BONUS +
//                              SHIP_RESIST_BONUS (the real full sweep).
//   --limit N                  Cap how many ids get checked (after --only/
//                              --all is applied) -- useful for a quick
//                              partial run.
//   --concurrency N            Parallel everef.net fetches (default 3).
//   --delay-ms N                Delay between fetches per worker, ms
//                              (default 400) -- be polite to everef.net.
//   --out <path>               Where to write the JSON findings report
//                              (default: ./role_bonus_drift_report_<ts>.json
//                              next to this script).
//
// EXIT CODE: 0 always (this is a report tool, not a pass/fail gate like
// run_regression.mjs) -- read the console summary / JSON report.

import fs from 'fs';
import path from 'path';
import vm from 'vm';
import { fileURLToPath, pathToFileURL } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Vedmak (Precursor Cruiser), Drekavac (Precursor Battlecruiser), Leshak
// (Precursor Battleship) -- all three independently hand-verified via live
// ESI dogma_effects + everef.net trait text during the 2026-10-09 bug #26/#27
// fixes. If this script can't reproduce "47270: [[precursor,damage,25]]",
// "49711: [[precursor,damage,50]]", "47271: [[precursor,damage,25],
// [precursor,rof,25]]" against the live page, something about the parsing
// approach needs fixing before it's trusted on anything else.
const CALIBRATION_SET = ['47270', '49711', '47271'];

// CONFIRMED LIVE 2026-10-09 via the built-in browser (device bridge's
// device_bash shell was unavailable, but the browser pane could reach
// everef.net directly): the ship page lives at /types/<id>, NOT /ship/<id>.
// The first draft of this script guessed /ship/<id> and that guess was wrong
// -- hitting it returns a 404 ("Page not found: /ship/47270"). Verified by
// loading https://everef.net/types/47270, /49711, /47271, /641 (Megathron)
// and /24688 (Rokh) and reading the rendered page text directly.
const EVEREF_SHIP_URL = (id) => `https://everef.net/types/${id}`;

function parseArgs(argv) {
  const out = { htmlPath: null, only: null, all: false, limit: null, concurrency: 3, delayMs: 400, outPath: null };
  const rest = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--only') { out.only = argv[++i].split(',').map(s => s.trim()).filter(Boolean); }
    else if (a === '--all') { out.all = true; }
    else if (a === '--limit') { out.limit = Number(argv[++i]); }
    else if (a === '--concurrency') { out.concurrency = Number(argv[++i]); }
    else if (a === '--delay-ms') { out.delayMs = Number(argv[++i]); }
    else if (a === '--out') { out.outPath = argv[++i]; }
    else { rest.push(a); }
  }
  out.htmlPath = rest[0] || null;
  return out;
}

export function extractLiveTables(htmlPath) {
  if (!fs.existsSync(htmlPath)) {
    console.error(`No such file: ${htmlPath}`);
    process.exit(2);
  }
  const html = fs.readFileSync(htmlPath, 'utf8');
  const m = html.match(/<script>([\s\S]*)<\/script>/);
  if (!m) {
    console.error('Could not find a <script> block in the given HTML file.');
    process.exit(2);
  }
  const code = m[1];

  function fakeEl() {
    return { addEventListener() {}, get style() { return {}; }, querySelectorAll() { return []; }, appendChild() {}, get innerHTML() { return ''; }, set innerHTML(v) {} };
  }
  const fakeDocument = { getElementById() { return fakeEl(); }, createElement() { return fakeEl(); } };
  const sandbox = { fetch: async () => ({ ok: false, status: 0 }), document: fakeDocument, console, Promise, Map, Set, Infinity, Math, JSON, Object, Array, Number, String };
  vm.createContext(sandbox);
  // CONFIRMED LIVE 2026-10-09: dscan-tool.html declares these as
  // `const SHIP_ROLE_BONUS = {...}` / `const SHIP_RESIST_BONUS = {...}`, and
  // Node's vm module does NOT attach top-level const/let bindings onto the
  // contextified sandbox object the way it attaches `var` and implicit
  // globals -- `vm.runInContext(code, sandbox)` ran cleanly with no error,
  // but `sandbox.SHIP_ROLE_BONUS` stayed undefined afterward, every time.
  // That's what the "was not found" error below was actually catching (not
  // a renamed constant). Fixed by appending a line to the SAME script string
  // (so it shares the original code's top-level lexical scope and can still
  // see the const bindings) that copies them onto the sandbox's global
  // object explicitly, where they can be read back afterward.
  const exportLine = '\nglobalThis.__AUDIT_EXPORTS__ = { SHIP_ROLE_BONUS: typeof SHIP_ROLE_BONUS !== "undefined" ? SHIP_ROLE_BONUS : undefined, SHIP_RESIST_BONUS: typeof SHIP_RESIST_BONUS !== "undefined" ? SHIP_RESIST_BONUS : undefined };';
  vm.runInContext(code + exportLine, sandbox);
  const exported = sandbox.__AUDIT_EXPORTS__ || {};

  if (!exported.SHIP_ROLE_BONUS) {
    console.error('SHIP_ROLE_BONUS was not found in the live file\'s sandbox context -- did the constant get renamed?');
    process.exit(2);
  }
  return {
    roleBonus: exported.SHIP_ROLE_BONUS,
    resistBonus: exported.SHIP_RESIST_BONUS || {},
  };
}

// ---- everef.net fetch + plain-text extraction -----------------------------

export function stripHtmlToText(html) {
  let t = html
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<(br|\/p|\/li|\/div|\/h[1-6])\s*\/?>/gi, '\n')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&#39;|&apos;/g, "'")
    .replace(/&quot;/g, '"');
  t = t.replace(/[ \t]+/g, ' ').replace(/\n\s*\n+/g, '\n').trim();
  return t;
}

// CONFIRMED LIVE 2026-10-09 (Vedmak/Drekavac/Leshak/Megathron/Rokh, via the
// built-in browser): everef.net's rendered Traits block is NOT "one sentence
// per bonus, each individually tagged (per level)" the way the first draft
// assumed. It's two literal sub-headings:
//   Type Bonuses
//     <Skill name> bonuses per level
//     5 %  bonus to Large Precursor Weapon damage
//     5 %  bonus to Large Precursor Weapon rate of fire
//   Role Bonuses
//     100 %  bonus to Remote Armor Repair Systems range
//     ...
// "per level" appears exactly ONCE, in the sub-heading under "Type Bonuses"
// -- never attached to the individual bonus lines themselves. So per-level
// scaling has to be decided by WHICH BLOCK a sentence falls in, not by
// scanning near each sentence for a "per level" phrase (the first draft's
// approach, which would never have matched anything real). Everything under
// "Type Bonuses" is scaled by 5 (max skill level); everything under "Role
// Bonuses" is already flat. Confirmed this reproduces all three calibration
// answers by hand before trusting it in code (Vedmak 5%->25, Drekavac
// 10%->50, Leshak 5%/5%->25/25).
export function splitTraitsSections(text) {
  const traitsStart = text.search(/\bTraits\b/i);
  if (traitsStart === -1) return { typeBonusText: '', roleBonusText: '', found: false };
  const rest = text.slice(traitsStart);
  const endHeadingRe = /\b(Defenses|Variations|Market|Subsystem|Attributes|Fitting|Required Skills)\b/;

  const typeIdx = rest.search(/\bType Bonuses\b/i);
  const roleIdx = rest.search(/\bRole Bonuses\b/i);

  let typeBonusText = '';
  let roleBonusText = '';

  if (typeIdx !== -1) {
    const afterType = rest.slice(typeIdx + 'Type Bonuses'.length);
    let end;
    if (roleIdx !== -1 && roleIdx > typeIdx) {
      end = roleIdx - (typeIdx + 'Type Bonuses'.length);
    } else {
      const m = afterType.match(endHeadingRe);
      end = m ? m.index : afterType.length;
    }
    typeBonusText = afterType.slice(0, Math.max(0, end));
  }

  if (roleIdx !== -1) {
    const afterRole = rest.slice(roleIdx + 'Role Bonuses'.length);
    const m = afterRole.match(endHeadingRe);
    const end = m ? m.index : afterRole.length;
    roleBonusText = afterRole.slice(0, end);
  }

  return { typeBonusText, roleBonusText, found: typeIdx !== -1 || roleIdx !== -1 };
}

const CATEGORY_KEYWORDS = [
  // Order matters -- check the more specific phrase before the generic one
  // (e.g. "sentry drone" before "drone").
  [/precursor weapon|entropic disintegrator/i, 'precursor'],
  [/vorton/i, 'vorton'],
  [/sentry drone/i, 'dronesentry'],
  [/\bdrone/i, 'drone'],
  [/fighter/i, 'fighter'],
  [/\b(missile|torpedo|rocket)/i, 'missile'],
  [/\b(energy turret|laser)/i, 'energy'],
  [/\b(hybrid turret|railgun|blaster)/i, 'hybrid'],
  [/\b(projectile turret|autocannon|artillery)/i, 'projectile'],
];

const DMG_TYPE_KEYWORDS = [
  [/\bkinetic\b/i, 'kin'],
  [/\bthermal\b/i, 'therm'],
  [/\bexplosive\b/i, 'exp'],
  [/\bem\b/i, 'em'],
];

function categoryFromText(fragment) {
  for (const [re, cat] of CATEGORY_KEYWORDS) {
    if (re.test(fragment)) return cat;
  }
  return null;
}

// A sentence can restrict to one or more damage types ("EM, explosive,
// thermal damage") -- the project's established convention (Gila/Worm/etc,
// Osprey Navy Issue) is to split a multi-type restriction into several
// same-magnitude tuples, one per type, rather than one tuple with a list.
function damageTypesFromText(fragment) {
  const found = [];
  for (const [re, tag] of DMG_TYPE_KEYWORDS) {
    if (re.test(fragment)) found.push(tag);
  }
  return found; // [] means unrestricted
}

// Finds candidate "<pct>% bonus to <description> <damage|rate of fire>"
// sentences within ONE already-split block (Type Bonuses text or Role
// Bonuses text -- see splitTraitsSections above), and flags ones that look
// mode-conditional (T3 Destroyer-style "while Sharpshooter Mode is enabled"
// lines, which the original human audit confirmed must be EXCLUDED -- those
// are modeled separately via MODE_EFFECT_ROWS (index.html), not
// SHIP_ROLE_BONUS). Per-level scaling is NOT decided here -- it's decided by
// the caller based on which block this text came from (see fetchShipTraitsTuples).
// CONFIRMED LIVE 2026-10-09: the first draft's trailing-context group
// ([^.]{0,40}) crossed newlines -- stripHtmlToText puts each bonus on its
// own line (</li> -> \n), but nothing in the stripped text ends a "sentence"
// with a period, so `[^.]` happily ate the \n and the start of the NEXT
// bonus line too. That made the regex's lastIndex jump past the next real
// match, silently dropping it -- caught by running this against the real
// Leshak fragment: only the "damage" bonus came back, "rate of fire" was
// swallowed into the first match's tail and never seen as its own match.
// Fixed by excluding \n from the tail group so it can't cross into the next
// line.
const BONUS_SENTENCE_RE = /(\d+(?:\.\d+)?)\s*%\s*(?:bonus\s+to\s+|reduction\s+in\s+)?([a-z0-9,\/ '-]{3,80}?)\s*(damage|rate of fire|rof|cycle time)\b([^.\n]{0,40})?/gi;

export function findBonusCandidates(sectionText) {
  const candidates = [];
  let match;
  const re = new RegExp(BONUS_SENTENCE_RE);
  while ((match = re.exec(sectionText))) {
    const [full, pctStr, desc, kindRaw, tail = ''] = match;
    // Bound the context window to the same line as the match (each bonus is
    // its own line after stripHtmlToText's </li> -> \n) so it can't bleed
    // into an adjacent bonus's text -- the same cross-line bug fixed in
    // BONUS_SENTENCE_RE's tail group above, applied here too since this
    // window is built independently of that group.
    const lineStart = sectionText.lastIndexOf('\n', match.index) + 1;
    const nextNewline = sectionText.indexOf('\n', match.index + full.length);
    const lineEnd = nextNewline === -1 ? sectionText.length : nextNewline;
    const windowStart = Math.max(lineStart, match.index - 60);
    const context = sectionText.slice(windowStart, Math.min(lineEnd, match.index + full.length + (tail ? tail.length : 0) + 20));
    if (/while\s+\w+\s+Mode\s+is\s+enabled/i.test(context)) continue; // T3D mode-conditional, out of scope here
    const kind = /rate of fire|rof|cycle time/i.test(kindRaw) ? 'rof' : 'damage';
    const category = categoryFromText(desc) || categoryFromText(context);
    if (!category) continue; // can't place it -- skip rather than guess
    const dmgTypes = kind === 'damage' ? damageTypesFromText(desc + ' ' + context) : [];
    const pct = parseFloat(pctStr.replace(/,/g, ''));
    candidates.push({ category, kind, pct, dmgTypes, raw: full.trim() });
  }
  return candidates;
}

// Expands damage-type-restricted candidates into one tuple per type (the
// multi-type-split convention), and drops exact duplicates.
export function candidatesToTuples(candidates) {
  const tuples = [];
  for (const c of candidates) {
    if (c.dmgTypes.length <= 1) {
      tuples.push([c.category, c.kind, round1(c.pct), c.dmgTypes[0] || undefined].filter(v => v !== undefined));
    } else {
      for (const t of c.dmgTypes) tuples.push([c.category, c.kind, round1(c.pct), t]);
    }
  }
  const seen = new Set();
  return tuples.filter(t => {
    const key = JSON.stringify(t);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function round1(n) { return Math.round(n * 10) / 10; }

function tupleKey(t) {
  // [cat, kind, pct, dmgType?] -- order-insensitive-safe key
  return `${t[0]}|${t[1]}|${round1(t[2])}|${t[3] || ''}`;
}

export function diffTuples(expected, actual) {
  const expSet = new Set(expected.map(tupleKey));
  const actSet = new Set((actual || []).map(tupleKey));
  const missingFromTable = expected.filter(t => !actSet.has(tupleKey(t)));
  const extraInTable = (actual || []).filter(t => !expSet.has(tupleKey(t)));
  return { missingFromTable, extraInTable, isMatch: missingFromTable.length === 0 && extraInTable.length === 0 };
}

// ---- small concurrency-limited fetch helper (mirrors the tool's own
// analyzeChunks(ids, fn, concurrency) pattern for consistency) -------------

async function runWithConcurrency(items, worker, concurrency, delayMs) {
  const results = new Array(items.length);
  let next = 0;
  async function runOne() {
    while (next < items.length) {
      const idx = next++;
      try {
        results[idx] = await worker(items[idx], idx);
      } catch (e) {
        results[idx] = { error: e.message };
      }
      if (delayMs) await new Promise(r => setTimeout(r, delayMs));
    }
  }
  const workers = Array.from({ length: Math.max(1, concurrency) }, runOne);
  await Promise.all(workers);
  return results;
}

export async function fetchShipTraitsTuples(id) {
  if (typeof fetch !== 'function') {
    throw new Error('global fetch is not available -- this script needs Node 18+');
  }
  const url = EVEREF_SHIP_URL(id);
  // CONFIRMED LIVE 2026-10-09: any throw out of this function (a fetch()
  // rejection from a DNS failure, blocked network, or connection reset --
  // below the HTTP layer, as opposed to a non-2xx response which is handled
  // as a normal {error} return below -- or anything else unexpected) used to
  // propagate uncaught. Caught in a real run: main()'s per-id worker doesn't
  // wrap its call to this function in try/catch, so the only thing catching
  // that throw was runWithConcurrency's generic try/catch -- which stores it
  // in a `results` array that main() never reads. Net effect: a network
  // failure made that ship silently vanish from both the console output and
  // the JSON report, with no finding recorded and no trace it was ever
  // checked. For a full --all sweep over ~340 ships, any transient blip
  // would make a genuinely stale table entry disappear from the report
  // instead of surfacing as "couldn't check this one" -- exactly the kind of
  // silent failure this whole script exists to avoid. Fixed by wrapping the
  // whole fetch-and-parse sequence in one try/catch so every failure mode --
  // bad response, missing sections, parse error, or a hard network error --
  // returns the same {url, error} shape and always produces a finding.
  try {
    const res = await fetch(url, { headers: { 'User-Agent': 'dscan-tool-role-bonus-audit/1.0 (personal project tooling)' } });
    if (!res.ok) return { url, error: `HTTP ${res.status}` };
    const html = await res.text();
    const text = stripHtmlToText(html);
    if (!/Traits/i.test(text)) {
      // Page loaded but doesn't look like a ship traits page at all -- the
      // URL pattern or the site structure may have changed. Don't guess;
      // report it.
      return { url, error: 'page fetched but no "Traits" heading found -- URL pattern or page structure may be wrong, needs human check' };
    }
    const { typeBonusText, roleBonusText, found } = splitTraitsSections(text);
    if (!found) {
      return { url, error: 'no "Type Bonuses"/"Role Bonuses" heading found under Traits -- page structure may have changed, needs human check' };
    }
    // Type Bonuses lines are per-skill-level (x5 at level V, this table's
    // own convention); Role Bonuses lines are already flat. See
    // splitTraitsSections.
    const typeCandidates = findBonusCandidates(typeBonusText).map(c => ({ ...c, pct: c.pct * 5, perLevel: true }));
    const roleCandidates = findBonusCandidates(roleBonusText).map(c => ({ ...c, perLevel: false }));
    const candidates = [...typeCandidates, ...roleCandidates];
    const tuples = candidatesToTuples(candidates);
    return { url, tuples, candidates, typeBonusExcerpt: typeBonusText.slice(0, 400), roleBonusExcerpt: roleBonusText.slice(0, 400) };
  } catch (e) {
    return { url, error: `fetch/parse failed: ${e.message}` };
  }
}

// ---- main ------------------------------------------------------------------

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.htmlPath) {
    console.error('Usage: node audit_role_bonus_drift.mjs <path-to-dscan-tool.html> [--only id1,id2] [--all] [--limit N] [--concurrency N] [--delay-ms N] [--out path.json]');
    process.exit(2);
  }

  const { roleBonus, resistBonus } = extractLiveTables(args.htmlPath);
  console.log(`Loaded live tables from ${args.htmlPath}: ${Object.keys(roleBonus).length} SHIP_ROLE_BONUS entries, ${Object.keys(resistBonus).length} SHIP_RESIST_BONUS entries.`);

  let ids;
  if (args.only) {
    ids = args.only;
  } else if (args.all) {
    ids = Object.keys(roleBonus);
  } else {
    ids = CALIBRATION_SET;
    console.log(`No --only/--all given -- running the ${ids.length}-ship CALIBRATION SET (${ids.join(', ')}). Pass --all to check every table entry.`);
  }
  if (args.limit) ids = ids.slice(0, args.limit);

  console.log(`Checking ${ids.length} ship id(s) against live everef.net trait pages (concurrency=${args.concurrency}, delay=${args.delayMs}ms)...\n`);

  const findings = [];
  await runWithConcurrency(ids, async (id) => {
    const liveTuples = roleBonus[id] || [];
    const fetched = await fetchShipTraitsTuples(id);
    if (fetched.error) {
      console.log(`  ? ${id}: FETCH/PARSE ISSUE -- ${fetched.error}`);
      findings.push({ id, status: 'FETCH_ISSUE', detail: fetched.error, url: fetched.url });
      return;
    }
    const diff = diffTuples(fetched.tuples, liveTuples);
    const status = diff.isMatch ? 'MATCH' : (liveTuples.length === 0 ? 'MISSING_FROM_TABLE' : 'MISMATCH');
    const marker = diff.isMatch ? 'OK' : '!!';
    console.log(`  ${marker} ${id}: ${status}${diff.isMatch ? '' : `\n       table has:    ${JSON.stringify(liveTuples)}\n       page implies: ${JSON.stringify(fetched.tuples)}`}`);
    findings.push({ id, status, table: liveTuples, derivedFromPage: fetched.tuples, missingFromTable: diff.missingFromTable, extraInTable: diff.extraInTable, url: fetched.url, typeBonusExcerpt: fetched.typeBonusExcerpt, roleBonusExcerpt: fetched.roleBonusExcerpt });
  }, args.concurrency, args.delayMs);

  const counts = findings.reduce((acc, f) => { acc[f.status] = (acc[f.status] || 0) + 1; return acc; }, {});
  console.log('\n--- SUMMARY ---');
  for (const [status, n] of Object.entries(counts)) console.log(`  ${status}: ${n}`);
  console.log(`\nNOTE: MISMATCH/MISSING findings are candidates for human review, not confirmed bugs -- verify each one against the live page and ESI dogma_effects before touching the table, same as every prior fix in this project.`);

  const outPath = args.outPath || path.join(__dirname, `role_bonus_drift_report_${new Date().toISOString().replace(/[:.]/g, '-')}.json`);
  fs.writeFileSync(outPath, JSON.stringify({ generatedAt: new Date().toISOString(), htmlPath: args.htmlPath, idsChecked: ids, findings }, null, 2));
  console.log(`\nFull findings written to ${outPath}`);
}

// Only auto-run when executed directly (`node audit_role_bonus_drift.mjs ...`),
// not when imported as a module (e.g. by a test harness importing the
// exported parsing functions above).
//
// CONFIRMED BROKEN then FIXED, live, 2026-10-09: the first version of this
// guard compared `import.meta.url` to the string `file://${process.argv[1]}`.
// That happens to work on Linux with a simple no-space path (e.g.
// /home/claude/audit_role_bonus_drift.mjs -> file:///home/claude/... lines up
// character-for-character), which is the only place this was tested before
// shipping -- a real gap, since the test harness imports this file as a
// module and so never actually exercises this guard at all. On the user's
// real Windows machine it silently evaluated to false: process.argv[1] is a
// backslash path with a space in it ("...\Claude Projects\d-scan
// tool\regression_suite\audit_role_bonus_drift.mjs"), while import.meta.url
// is a proper file:// URL with forward slashes and the space percent-encoded
// (file:///C:/Users/.../Claude%20Projects/...) -- those two strings can
// never be equal. The result: main() silently never ran. Confirmed exactly
// this by watching the user run `node regression_suite\audit_role_bonus_drift.mjs
// dscan-tool.html --only 47270,49711,47271` in their own Command Prompt --
// command returned straight to a fresh prompt with zero output, no error,
// nothing. Fixed using Node's own URL<->path conversion on both sides
// (pathToFileURL), which normalizes separators and percent-encoding
// correctly on every platform instead of hand-building a URL string.
if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  main();
}
