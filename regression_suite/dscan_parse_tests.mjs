#!/usr/bin/env node
// Regression coverage for parseDscan() -- backlog #13 (D-scan name-parsing
// robustness), added 2026-10-11.
//
// The fixture lines below are NOT guessed, in two rounds:
//
// ROUND 1 (the cases marked EVEPRAISAL, plus hand-constructed adversarial
// ones): taken verbatim from the evepraisal/evepaste reference parser (the
// Nothing4You/eveparser fork, tests/parsers/dscan.py), the de-facto
// authoritative sample set for this paste format used across the EVE
// 3rd-party tool ecosystem, plus cases constructed per backlog #13's own
// framing (unusual punctuation, non-Latin characters, ragged/empty
// columns) to stress-test beyond what that reference set covers.
//
// ROUND 2 (the cases marked REAL-PASTE): lines taken verbatim from an
// actual D-Scan paste the owner supplied directly, which turned out to use a
// 4-column format (a leading bare inventory-type-ID column) the round-1
// reference fixtures never showed at all -- round 1 alone would have
// missed this entirely. See the comment on parseDscan() itself for what
// this exposed and how it was fixed.
//
// ROUND 3 (REAL_PASTE_2 block below): a second, much larger (229-contact)
// real paste from the owner, run as a pure validation pass against the round-2
// fix -- zero new issues found, but kept as permanent coverage since it
// exercises things round 1/2 didn't: CJK/Cyrillic/emoji/symbol names, a
// custom ship name that is itself a bare number with no unit ("6565",
// correctly NOT mistaken for a distance), a multi-comma-grouped distance
// over 4 million km, and a "Wreck of: <pilot>" naming shape.
//
// Usage: node dscan_parse_tests.mjs [path-to-index.html]
import fs from 'fs';
import vm from 'vm';
import { fileURLToPath } from 'url';

// fileURLToPath() (not .pathname) -- a raw file:// URL's .pathname keeps a
// leading slash before a Windows drive letter ("/C:/Users/..."), which
// fs.readFileSync then fails to open; fileURLToPath() is the standard fix.
const htmlPath = process.argv[2] || fileURLToPath(new URL('../index.html', import.meta.url));
const html = fs.readFileSync(htmlPath, 'utf8');
const scriptMatch = html.match(/<script>([\s\S]*)<\/script>/);
if (!scriptMatch) {
  console.error('FAIL: could not find <script> block in', htmlPath);
  process.exit(1);
}
const code = scriptMatch[1];

function fakeEl() {
  return {
    addEventListener() {}, get style() { return {}; }, querySelectorAll() { return []; },
    appendChild() {}, get innerHTML() { return ''; }, set innerHTML(v) {},
  };
}
const sandbox = {
  fetch: async () => ({ ok: false, status: 404 }),
  document: { getElementById() { return fakeEl(); }, createElement() { return fakeEl(); } },
  console, Promise, Map, Set, Infinity, Math, JSON, Object, Array, Number, String,
};
vm.createContext(sandbox);
vm.runInContext(code, sandbox);

if (typeof sandbox.parseDscan !== 'function') {
  console.error('FAIL: parseDscan() not found in', htmlPath);
  process.exit(1);
}

// Each case: a single D-scan line, and the exact {candidates, distance} the
// current, fixed parseDscan() is expected to produce for it.
const CASES = [
  {
    label: 'EVEPRAISAL: plain ship, "+" placeholder name col, comma-grouped distance',
    line: "+\tNoctis\t3,225 m",
    expect: { candidates: ['+', 'Noctis'], distance: '3,225 m' },
  },
  {
    label: 'EVEPRAISAL: plain ship, km unit',
    line: "+\tThrasher\t12 km",
    expect: { candidates: ['+', 'Thrasher'], distance: '12 km' },
  },
  {
    label: 'EVEPRAISAL: custom-named ship, "-" (same-grid/no-read) distance',
    line: "some dude's Stabber Fleet Issue\tStabber Fleet Issue\t-",
    expect: { candidates: ["some dude's Stabber Fleet Issue", 'Stabber Fleet Issue'], distance: '-' },
  },
  {
    label: 'EVEPRAISAL: wreck row',
    line: "Wreck\tTayra\t82 km",
    expect: { candidates: ['Wreck', 'Tayra'], distance: '82 km' },
  },
  {
    label: 'space-grouped thousands separator (locale-formatted distance, not comma)',
    line: "test\tNoctis\t3 225 m",
    expect: { candidates: ['test', 'Noctis'], distance: '3 225 m' },
  },
  {
    label: 'NBSP-grouped thousands separator (raw non-breaking space, U+00A0)',
    line: "test\tNoctis\t3 225 m",
    expect: { candidates: ['test', 'Noctis'], distance: '3 225 m' },
  },
  {
    label: 'celestial, AU distance',
    line: "Otanuomi V - Moon 11\tMoon\t10.4 AU",
    expect: { candidates: ['Otanuomi V - Moon 11', 'Moon'], distance: '10.4 AU' },
  },
  {
    label: 'wormhole celestial, ly distance',
    line: "J123456 - something\tStar\t0.02 ly",
    expect: { candidates: ['J123456 - something', 'Star'], distance: '0.02 ly' },
  },
  {
    label: 'non-Latin (Cyrillic) pilot name',
    line: "Иван Иванов\tAstrahus\t45 km",
    expect: { candidates: ['Иван Иванов', 'Astrahus'], distance: '45 km' },
  },
  {
    label: 'non-Latin structure/corp name with punctuation («»)',
    line: "ЕВЕ-Alliance's «Товарищество» Keepstar\tKeepstar\t1,234 km",
    expect: { candidates: ["ЕВЕ-Alliance's «Товарищество» Keepstar", 'Keepstar'], distance: '1,234 km' },
  },
  {
    label: 'CJK structure name',
    line: "東京タワー Keepstar\tKeepstar\t999 km",
    expect: { candidates: ['東京タワー Keepstar', 'Keepstar'], distance: '999 km' },
  },
  {
    label: 'apostrophe/possessive in both name columns',
    line: "Bob's Revenge\tLegion\t500 m",
    expect: { candidates: ["Bob's Revenge", 'Legion'], distance: '500 m' },
  },
  {
    label: 'empty name column (leading tab)',
    line: "\tRifter\t5,000 m",
    expect: { candidates: ['Rifter'], distance: '5,000 m' },
  },
  {
    label: 'empty distance column (trailing tab, nothing after)',
    line: "SomePilot\tRifter\t",
    expect: { candidates: ['SomePilot', 'Rifter'], distance: '' },
  },
  {
    label: 'ragged doubled tab between columns',
    line: "SomePilot\t\tRifter\t5,000 m",
    expect: { candidates: ['SomePilot', 'Rifter'], distance: '5,000 m' },
  },
  {
    label: 'digit-leading null-sec system/structure name is NOT mistaken for a distance',
    line: "6VDT-H - Keepstar\tKeepstar\t500 km",
    expect: { candidates: ['6VDT-H - Keepstar', 'Keepstar'], distance: '500 km' },
  },
  {
    label: 'digit-leading wormhole-style system name (no separator) is NOT mistaken for a distance',
    line: "4HWWF\tRaitaru\t30 km",
    expect: { candidates: ['4HWWF', 'Raitaru'], distance: '30 km' },
  },
  {
    label: 'single-token fallback (no tabs, no 2+-space run) keeps the whole line as one candidate',
    line: "Purifier",
    expect: { candidates: ['Purifier'], distance: '' },
  },
  {
    label: 'REAL-PASTE: 4-column format, leading type ID + comma-grouped km distance',
    line: "22464\tSH: Mccpncf Ziectw\tFlycatcher\t1,331 km",
    expect: { candidates: ['22464', 'SH: Mccpncf Ziectw', 'Flycatcher'], distance: '1,331 km' },
  },
  {
    label: 'REAL-PASTE: 4-column format, leading type ID + "-" (same-grid/no-read)',
    line: "672\t.\tCaldari Shuttle\t-",
    expect: { candidates: ['672', '.', 'Caldari Shuttle'], distance: '-' },
  },
  {
    label: 'REAL-PASTE: 4-column format, m-unit distance, apostrophe in a non-name field',
    line: "17715\tGila: gaghg qesdwzt\tGila\t3,039 m",
    expect: { candidates: ['17715', 'Gila: gaghg qesdwzt', 'Gila'], distance: '3,039 m' },
  },
  {
    label: 'REAL-PASTE: 4-column format, Korean pilot name',
    line: "12038\t퇙쪌 Tavixsbz v.2.4\tPurifier\t6,724 km",
    expect: { candidates: ['12038', '퇙쪌 Tavixsbz v.2.4', 'Purifier'], distance: '6,724 km' },
  },
  {
    label: 'REAL-PASTE: 4-column format, type ID coincidentally a known low ESI id (Velator=606)',
    line: "606\tVelator - Pexx\tVelator\t129 km",
    expect: { candidates: ['606', 'Velator - Pexx', 'Velator'], distance: '129 km' },
  },
];

// Full real D-Scan paste the owner supplied (2026-10-28: every custom ship name scrambled, letter for letter, so no player's name is in the repository; the format, types and distances are untouched), run as one block: every row's real
// distance (never the leading type-ID column) must be picked out, and
// every row's actual ship-type name must survive into `candidates` so ESI
// resolution still finds it.
const REAL_PASTE = `37604\tDvd Bane's\tApostle\t64 km
37604\tQLYA - P\tApostle\t121 km
11969\t!! WEV DKI !!\tArazu\t54 km
11969\tHqzejes Uihhvsxyb\tArazu\t48 km
672\t.\tCaldari Shuttle\t-
671\tJs Tritq\tErebus\t40 km
22464\tSH: Mccpncf Ziectw\tFlycatcher\t1,331 km
11129\t0/*\tGallente Shuttle\t27 km
11129\t0/\tGallente Shuttle\t35 km
11129\t0/*\tGallente Shuttle\t17 km
17715\tGila: gaghg qesdwzt\tGila\t3,039 m
22544\tRde Hidaz sbj\tHulk\t27 km
17738\tLnvklm\tMachariel\t33 km
37605\tWctlE\tMinokawa\t62 km
37607\tWavo\tNinazu\t1,328 km
33818\tOagkg bqwg\tOrthrus\t174 km
29340\t\\00//\tOsprey Navy Issue\t49 km
11965\tGcmx mute\tPilgrim\t44 km
11965\tProrator*\tPilgrim\t-
47466\t*Yarlhznfz Praxis Nv\tPraxis\t45 km
586\tXuio - nxuln\tProbe\t-
12038\t퇙쪌 Tavixsbz v.2.4\tPurifier\t6,724 km
29336\tQjbtl\tScythe Fleet Issue\t84 km
19744\tSigil - QFRHWJYFZFFB\tSigil\t22 km
19744\t# Dvd.g.VKXW.Acnv\tSigil\t22 km
4310\tAfqi Intksb's Ftdalnvtam\tTornado\t31 km
644\tTYPHOON\tTyphoon\t39 km
606\tVelator - Pexx\tVelator\t129 km`;

const REAL_PASTE_EXPECTED_TYPES = [
  'Apostle', 'Apostle', 'Arazu', 'Arazu', 'Caldari Shuttle', 'Erebus', 'Flycatcher',
  'Gallente Shuttle', 'Gallente Shuttle', 'Gallente Shuttle', 'Gila', 'Hulk', 'Machariel',
  'Minokawa', 'Ninazu', 'Orthrus', 'Osprey Navy Issue', 'Pilgrim', 'Pilgrim', 'Praxis',
  'Probe', 'Purifier', 'Scythe Fleet Issue', 'Sigil', 'Sigil', 'Tornado', 'Typhoon', 'Velator',
];
const REAL_PASTE_EXPECTED_DISTANCES = [
  '64 km', '121 km', '54 km', '48 km', '-', '40 km', '1,331 km', '27 km', '35 km', '17 km',
  '3,039 m', '27 km', '33 km', '62 km', '1,328 km', '174 km', '49 km', '44 km', '-', '45 km',
  '-', '6,724 km', '84 km', '22 km', '22 km', '31 km', '39 km', '129 km',
];

let pass = 0, fail = 0;
for (const c of CASES) {
  const rows = sandbox.parseDscan(c.line);
  const row = rows[0];
  const gotCandidates = JSON.stringify(row ? row.candidates : null);
  const wantCandidates = JSON.stringify(c.expect.candidates);
  const gotDistance = row ? row.distance : undefined;
  const ok = row && gotCandidates === wantCandidates && gotDistance === c.expect.distance;
  if (ok) {
    pass++;
  } else {
    fail++;
    console.log(`FAIL: ${c.label}`);
    console.log(`  line:     ${JSON.stringify(c.line)}`);
    console.log(`  expected: candidates=${wantCandidates} distance=${JSON.stringify(c.expect.distance)}`);
    console.log(`  got:      candidates=${gotCandidates} distance=${JSON.stringify(gotDistance)}`);
  }
}

// Block check helper: run parseDscan() over a whole paste and verify,
// row by row, that the real distance was identified and the real ship-
// type name survived into candidates (never mind the leading type-ID/
// pilot-name noise alongside it -- that's expected and harmless, same
// as elsewhere).
function checkBlock(label, pasteText, expectedTypes, expectedDistances) {
  const rows = sandbox.parseDscan(pasteText);
  let blockPass = 0, blockFail = 0;
  if (rows.length !== expectedTypes.length) {
    console.log(`FAIL: ${label} -- expected ${expectedTypes.length} rows, got ${rows.length}`);
    return { pass: 0, fail: 1 };
  }
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    const wantType = expectedTypes[i];
    const wantDist = expectedDistances[i];
    const typeOk = row.candidates.includes(wantType);
    const distOk = row.distance === wantDist;
    if (typeOk && distOk) {
      blockPass++;
    } else {
      blockFail++;
      console.log(`FAIL: ${label} row ${i} (${JSON.stringify(row.raw)})`);
      if (!typeOk) console.log(`  expected type "${wantType}" in candidates, got ${JSON.stringify(row.candidates)}`);
      if (!distOk) console.log(`  expected distance ${JSON.stringify(wantDist)}, got ${JSON.stringify(row.distance)}`);
    }
  }
  return { pass: blockPass, fail: blockFail };
}

const r1 = checkBlock('REAL-PASTE (round 2, 28 contacts)', REAL_PASTE, REAL_PASTE_EXPECTED_TYPES, REAL_PASTE_EXPECTED_DISTANCES);

// Round 3: a second, independent, much larger (229-contact) real paste
// from the owner -- pure validation of the round-2 fix, zero new code changes.
// Lines stored one-JSON-string-per-element (not a template literal) so
// arbitrary pasted content -- backslashes, CJK, emoji, quotes -- can never
// collide with JS string-escaping rules.
const REAL_PASTE_2_LINES = [
  "11134\tAmarr Shuttle - Avkuh Fatkgpzpq\tAmarr Shuttle\t-",
  "11134\t鯯炉嶅螁樺 - ATMSGNONI\tAmarr Shuttle\t-",
  "11134\tAmarr Shuttle* — Nvlmcif Qy\tAmarr Shuttle\t69 km",
  "11202\tAres - dihtjl ymsbny\tAres\t13 km",
  "11202\tW5-X\tAres\t1,155 km",
  "608\tAtron - Yyvc Ppnst\tAtron\t14 km",
  "608\tИхщэжэццф Atron\tAtron\t19 km",
  "608\tAtron - Brseyrooe WxyGkbh\tAtron\t128 km",
  "648\tc\tBadger\t49 km",
  "648\tTccmmw 18\tBadger\t13 km",
  "648\t2136-Qylof\tBadger\t14 km",
  "1944\tBestower - Cfvrx Znjcw\tBestower\t48 km",
  "12731\tBustard - Nckbvh Imjyhthp\tBustard\t26 km",
  "11192\t*PIO Ohoti Buzzard\tBuzzard\t3,019 m",
  "11192\tIQPIH\tBuzzard\t2,215 km",
  "672\t♥ Mbfnhka Cgfk ❤\tCaldari Shuttle\t34 km",
  "672\t..\tCaldari Shuttle\t355 km",
  "670\tCapsule — Bcqka Wlsree\tCapsule\t30 km",
  "670\tCapsule - Lylslw Iltyqbi\tCapsule\t-",
  "670\tCapsule - Onenhe Rvjykeahy\tCapsule\t127 km",
  "670\tCapsule - Ottjhw Edufzaq\tCapsule\t-",
  "670\tCapsule - Kcvfl Ekqfla\tCapsule\t5,984 m",
  "670\tCapsule - Uxnps Xbcujtwr\tCapsule\t125 km",
  "670\tCapsule - Fxiod Cohgiajylmt\tCapsule\t125 km",
  "670\tCapsule - zoewoknkz\tCapsule\t16 km",
  "621\tZdayu Wvhj Jgia Fleet...\tCaracal\t60 km",
  "621\tSz Wwy Qe Cvawtcs C Iutmybu\tCaracal\t50 km",
  "621\trWAMRYMH\tCaracal\t11 km",
  "621\tSR Caracal\tCaracal\t49 km",
  "621\tts sesw\tCaracal\t58 km",
  "621\tCaracal - SR QxhwYvpk\tCaracal\t28 km",
  "621\t♪♫♪ Trru's ♪♫♪™\tCaracal\t16 km",
  "621\tHTBKM\tCaracal\t26 km",
  "621\tCaracal\tCaracal\t32 km",
  "621\tSR Caracal\tCaracal\t49 km",
  "621\tts caracal\tCaracal\t48 km",
  "621\t-0-\tCaracal\t64 km",
  "621\tSR Caracal\tCaracal\t53 km",
  "621\tSlgl\tCaracal\t28 km",
  "621\tpxd jha gsufgvr ts\tCaracal\t25 km",
  "621\tCaracal - Dmtyow Azex\tCaracal\t5,040 m",
  "621\tCaracal - yHbenxk Njgck\tCaracal\t50 km",
  "621\tSR Caracal\tCaracal\t16 km",
  "621\tSR ♠[ῲ™©\tCaracal\t51 km",
  "621\tCaracal* - Gkwgzn Vnddkml\tCaracal\t40 km",
  "621\tMvmkksxip\tCaracal\t37 km",
  "621\tI|X LqzKh DAB\tCaracal\t22 km",
  "621\tSR-W\tCaracal\t14 km",
  "621\tCaracal - Qlhdrdnj Uujmci\tCaracal\t59 km",
  "17634\tQgul\tCaracal Navy Issue\t-",
  "11196\t*Fyyxu.\tClaw\t15 km",
  "16236\t/\tCoercer\t13 km",
  "583\tSR- Dvd g rytistq\tCondor\t13 km",
  "91857\tCorax Navy Issue\tCorax Navy Issue\t17 km",
  "16238\tCormorant - Erdzig\tCormorant\t24 km",
  "16238\t✪JQM Belakj✪\tCormorant\t47 km",
  "11176\tSR zyztfb!\tCrow\t3,275 m",
  "11176\tSR zyztfb!\tCrow\t12 km",
  "11184\tSR\tCrusader\t17 km",
  "11184\tCxqdhi Oota\tCrusader\t-",
  "22474\t**Damnation\tDamnation\t50 km",
  "32874\tRde Rmec\tDragoon\t432 km",
  "24698\tVdqtx\tDrake\t31 km",
  "22442\tAWVK Agh.\tEos\t18 km",
  "589\tsnppdz\tExecutioner\t23 km",
  "29344\tExequror-orv\tExequror Navy Issue\t-",
  "16227\tSR IDO 3.36 (Ferox, \tFerox\t63 km",
  "16227\tisa-++++\tFerox\t13 km",
  "16227\t\"AO\" Absolute Execution\tFerox\t51 km",
  "16227\tX\tFerox\t29 km",
  "16227\tFerox - Qofwo Iytmk\tFerox\t50 km",
  "16227\tSR IDO 3.36 (Ferox, \tFerox\t48 km",
  "16227\tFerox - Tspph Hzop\tFerox\t39 km",
  "16227\tFerox\tFerox\t41 km",
  "22464\tFlycatcher* - Akvhvygt JPQDBY\tFlycatcher\t23 km",
  "17715\tLrtu\tGila\t-",
  "3756\tGjwif Nkmo\tGnosis\t104 km",
  "11381\t. RJ\tHarpy\t12 km",
  "11379\tUxwdpg\tHawk\t27 km",
  "35683\t1\tHecate\t23 km",
  "35683\t.\tHecate\t-",
  "11172\tSO\tHelios\t156 km",
  "605\tZntl Gaukhb DAB\tHeron\t254 km",
  "605\tHeron* — Cwjjjh\tHeron\t48 km",
  "605\tHeron - Lorqj\tHeron\t29 km",
  "605\tHeron: ESCYSVP02\tHeron\t-",
  "605\tEl.I3O-0W\tHeron\t40 km",
  "601\t傓仌撐熋 - GHO-NIP\tIbis\t-",
  "601\tIbis: Pzbnd55\tIbis\t-",
  "601\tIbis - Oua jp Jazmfbh\tIbis\t-",
  "601\tIbis - lumzcjov4747\tIbis\t15 km",
  "601\tIbis - Opuicgc Uwlekxs\tIbis\t-",
  "601\t傓仌撐熋 - HPJ-I1\tIbis\t-",
  "12753\t╦\tImpel\t39 km",
  "657\tIteron Mark V - I8B3O Zqsptr Ydmavqls\tIteron Mark V\t-",
  "657\tC\tIteron Mark V\t26 km",
  "657\tJwsqe Qitixhh\tIteron Mark V\t-",
  "657\tc\tIteron Mark V\t40 km",
  "657\tIteron Mark V\tIteron Mark V\t-",
  "11174\tTbifrmbnzvbjapfveo\tKeres\t18 km",
  "602\t☪\tKestrel\t-",
  "17738\twnvdu\tMachariel\t22 km",
  "11186\tIyjc\tMalediction\t29 km",
  "44996\tマーシャル* - Pmvaq Zynlnhie\tMarshal\t13 km",
  "609\tmslzwpbbtc\tMaulus\t24 km",
  "609\tафнюзужжлг/leefzp kfwfs\tMaulus\t25 km",
  "603\tMerlin - VCPOPA LUNTKGBEQ\tMerlin\t-",
  "77114\tOxpoo zu: Ymypr RpwR\tMetamorphosis\t23 km",
  "45534\tYkkb\tMonitor\t50 km",
  "4306\tWowjw Zxmdy\tNaga\t63 km",
  "4306\tHjovh Naga2\tNaga\t39 km",
  "4306\tHjovh Naga2 \tNaga\t63 km",
  "4306\tHjovh Naga2\tNaga\t46 km",
  "4306\tHjovh Naga2\tNaga\t66 km",
  "4306\tSR Wolf suv\tNaga\t65 km",
  "4306\tSjsx3\tNaga\t63 km",
  "4306\tqxsfs\tNaga\t61 km",
  "4306\tIaqj\tNaga\t57 km",
  "4306\tu-knvgk\tNaga\t57 km",
  "4306\tHjovh Naga2\tNaga\t47 km",
  "4306\tNaga - nmaskkgn01\tNaga\t61 km",
  "4306\tttub oxp\tNaga\t56 km",
  "4306\tNaga - Sqxxp Khbzv\tNaga\t64 km",
  "4306\t櫜\tNaga\t47 km",
  "4306\tnaga\tNaga\t51 km",
  "4306\t(---) \\u/\tNaga\t65 km",
  "4306\tDwpatwvn\tNaga\t56 km",
  "4306\tSR Naga\tNaga\t50 km",
  "4306\tNaga - lqnlrzdc\tNaga\t4,992 m",
  "4306\tNaga\tNaga\t341 km",
  "4306\tNaga - Lqaiuxsr\tNaga\t48 km",
  "4306\tWcon Yzqopx\tNaga\t60 km",
  "4306\tNaga - Vmcim Eazm\tNaga\t53 km",
  "4306\tDlfnkef Mksog\tNaga\t60 km",
  "4306\tHjovh Naga2\tNaga\t65 km",
  "4306\tHjovh Naga2\tNaga\t50 km",
  "4306\tHjovh C\tNaga\t61 km",
  "4306\tHjovh Naga2\tNaga\t60 km",
  "4306\tZvrbtau Sff\tNaga\t44 km",
  "4306\tAPRRE X*BWUW\tNaga\t52 km",
  "4306\t*Hjovh Naga2\tNaga\t63 km",
  "4306\tSR-18 Jdhr Ppis Pc.EK\tNaga\t67 km",
  "4306\t.W\tNaga\t66 km",
  "4306\tNaga - pwvsjkwcrn\tNaga\t51 km",
  "650\tVhvl\tNereus\t-",
  "33472\tWVFQ AJ WEV\tNestor\t49 km",
  "33472\t333\tNestor\t50 km",
  "33472\t222\tNestor\t51 km",
  "12745\tBAX 555 yizys\tOccator\t15 km",
  "28606\tagnoz\tOrca\t26 km",
  "12021\t**phobos2\tPhobos\t-",
  "42244\tWisbk C\tPorpoise\t24 km",
  "47466\tPraxis - vNESAe\tPraxis\t10 km",
  "47466\t-1-\tPraxis\t29 km",
  "72872\tProphecy W\tProphecy Wavy Issue\t24 km",
  "12735\ttfvwm nqyg\tProwler\t14 km",
  "588\tNaigffn Wczsr's Reaper\tReaper\t1,103 km",
  "588\tReaper - Vdibx Grabak\tReaper\t134 km",
  "11393\tRetribution* - Rczjiy\tRetribution\t-",
  "587\tRifter - Mlek\tRifter\t-",
  "11978\t:3\tScimitar\t11 km",
  "11978\tXcpnshz\tScimitar\t33 km",
  "32309\tScorpion Navy Issue - DEPBTG JZWBHOV\tScorpion Navy Issue\t27 km",
  "30486\tScanner Probe\tSisters Combat Scanner Probe\t-",
  "30486\tScanner Probe\tSisters Combat Scanner Probe\t-",
  "30486\tScanner Probe\tSisters Combat Scanner Probe\t-",
  "30486\tScanner Probe\tSisters Combat Scanner Probe\t-",
  "30486\tScanner Probe\tSisters Combat Scanner Probe\t-",
  "30486\tScanner Probe\tSisters Combat Scanner Probe\t-",
  "30486\tScanner Probe\tSisters Combat Scanner Probe\t-",
  "30486\tScanner Probe\tSisters Combat Scanner Probe\t-",
  "30486\tScanner Probe\tSisters Combat Scanner Probe\t-",
  "30486\tScanner Probe\tSisters Combat Scanner Probe\t787 km",
  "30486\tScanner Probe\tSisters Combat Scanner Probe\t-",
  "30486\tScanner Probe\tSisters Combat Scanner Probe\t-",
  "30486\tScanner Probe\tSisters Combat Scanner Probe\t-",
  "30486\tScanner Probe\tSisters Combat Scanner Probe\t-",
  "30486\tScanner Probe\tSisters Combat Scanner Probe\t-",
  "30486\tScanner Probe\tSisters Combat Scanner Probe\t-",
  "585\t*Slasher\tSlasher\t8,233 m",
  "585\tLcstmj NE\tSlasher\t-",
  "585\tET9 Tjyss\tSlasher\t86 km",
  "81008\tc\tSquall\t41 km",
  "37482\tSR Stork\tStork\t28 km",
  "649\ts\tTayra\t126 km",
  "649\tTayra\tTayra\t515 km",
  "16242\tMinmatar Uqoejbq 277713047s Pwtp\tThrasher\t22 km",
  "4310\tDfebahfi\tTornado\t50 km",
  "4310\ta.rhrsw\tTornado\t47 km",
  "4310\tTornado Ehhb\tTornado\t53 km",
  "4310\thert\tTornado\t1,230 km",
  "4310\tVe Yfkziv Joel\tTornado\t47 km",
  "4310\tSR H\tTornado\t52 km",
  "4310\tDDPP\tTornado\t61 km",
  "4310\tVubd\tTornado\t1,231 km",
  "4310\tWycma Vspzamttd\tTornado\t53 km",
  "4310\tTornado - Dpd Pwgdft\tTornado\t53 km",
  "4310\tTornado\tTornado\t52 km",
  "4310\tVubd\tTornado\t1,229 km",
  "4310\tDGAK SVRBA\tTornado\t64 km",
  "4310\tSR Fwlelkv\tTornado\t51 km",
  "4310\tTornado Ehhb-\tTornado\t61 km",
  "4310\tIDO\tTornado\t53 km",
  "4310\tBeywdiBakjdd\tTornado\t44 km",
  "4310\tS-\"Gk-.Jita44?if.WBT\tTornado\t104 km",
  "4310\tvfp\tTornado\t58 km",
  "4310\thert\tTornado\t1,229 km",
  "4310\thert\tTornado\t1,232 km",
  "4310\thert\tTornado\t1,229 km",
  "4310\thert\tTornado\t1,230 km",
  "4310\thert\tTornado\t1,230 km",
  "4310\thert\tTornado\t1,231 km",
  "4310\thert\tTornado\t1,231 km",
  "4310\t,\tTornado\t51 km",
  "4310\tVubd\tTornado\t54 km",
  "81047\tNbpcgneohg\tTorrent\t12 km",
  "593\tgxnlcty vuepq\tTristan\t4,675 m",
  "28665\tabdd\tVargur\t51 km",
  "28665\twyhkd\tVargur\t52 km",
  "28665\tRysp\tVargur\t49 km",
  "606\tVelator - Qmsuaviuprw73\tVelator\t18 km",
  "32880\tVenture - Mldfiqol Fjraq\tVenture\t8,161 m",
  "32880\tФжы Хьжшугвчцтфу\tVenture\t13 km",
  "32880\tHbbRN\tVenture\t26 km",
  "32880\tkhw\tVenture\t-",
  "17843\tVexor Navy Issue - Ghnck Eaxn\tVexor Navy Issue\t-",
  "12743\t6565\tViator\t4,344,227 km",
  "3766\tMubswt_Rtwnqqiupl\tVigil\t66 km",
  "653\tZ XTYD 1\tWreathe\t32 km",
];
const REAL_PASTE_2 = REAL_PASTE_2_LINES.join('\n');
const REAL_PASTE_2_EXPECTED_TYPES = [
  "Amarr Shuttle",
  "Amarr Shuttle",
  "Amarr Shuttle",
  "Ares",
  "Ares",
  "Atron",
  "Atron",
  "Atron",
  "Badger",
  "Badger",
  "Badger",
  "Bestower",
  "Bustard",
  "Buzzard",
  "Buzzard",
  "Caldari Shuttle",
  "Caldari Shuttle",
  "Capsule",
  "Capsule",
  "Capsule",
  "Capsule",
  "Capsule",
  "Capsule",
  "Capsule",
  "Capsule",
  "Caracal",
  "Caracal",
  "Caracal",
  "Caracal",
  "Caracal",
  "Caracal",
  "Caracal",
  "Caracal",
  "Caracal",
  "Caracal",
  "Caracal",
  "Caracal",
  "Caracal",
  "Caracal",
  "Caracal",
  "Caracal",
  "Caracal",
  "Caracal",
  "Caracal",
  "Caracal",
  "Caracal",
  "Caracal",
  "Caracal",
  "Caracal",
  "Caracal Navy Issue",
  "Claw",
  "Coercer",
  "Condor",
  "Corax Navy Issue",
  "Cormorant",
  "Cormorant",
  "Crow",
  "Crow",
  "Crusader",
  "Crusader",
  "Damnation",
  "Dragoon",
  "Drake",
  "Eos",
  "Executioner",
  "Exequror Navy Issue",
  "Ferox",
  "Ferox",
  "Ferox",
  "Ferox",
  "Ferox",
  "Ferox",
  "Ferox",
  "Ferox",
  "Flycatcher",
  "Gila",
  "Gnosis",
  "Harpy",
  "Hawk",
  "Hecate",
  "Hecate",
  "Helios",
  "Heron",
  "Heron",
  "Heron",
  "Heron",
  "Heron",
  "Ibis",
  "Ibis",
  "Ibis",
  "Ibis",
  "Ibis",
  "Ibis",
  "Impel",
  "Iteron Mark V",
  "Iteron Mark V",
  "Iteron Mark V",
  "Iteron Mark V",
  "Iteron Mark V",
  "Keres",
  "Kestrel",
  "Machariel",
  "Malediction",
  "Marshal",
  "Maulus",
  "Maulus",
  "Merlin",
  "Metamorphosis",
  "Monitor",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Naga",
  "Nereus",
  "Nestor",
  "Nestor",
  "Nestor",
  "Occator",
  "Orca",
  "Phobos",
  "Porpoise",
  "Praxis",
  "Praxis",
  "Prophecy Wavy Issue",
  "Prowler",
  "Reaper",
  "Reaper",
  "Retribution",
  "Rifter",
  "Scimitar",
  "Scimitar",
  "Scorpion Navy Issue",
  "Sisters Combat Scanner Probe",
  "Sisters Combat Scanner Probe",
  "Sisters Combat Scanner Probe",
  "Sisters Combat Scanner Probe",
  "Sisters Combat Scanner Probe",
  "Sisters Combat Scanner Probe",
  "Sisters Combat Scanner Probe",
  "Sisters Combat Scanner Probe",
  "Sisters Combat Scanner Probe",
  "Sisters Combat Scanner Probe",
  "Sisters Combat Scanner Probe",
  "Sisters Combat Scanner Probe",
  "Sisters Combat Scanner Probe",
  "Sisters Combat Scanner Probe",
  "Sisters Combat Scanner Probe",
  "Sisters Combat Scanner Probe",
  "Slasher",
  "Slasher",
  "Slasher",
  "Squall",
  "Stork",
  "Tayra",
  "Tayra",
  "Thrasher",
  "Tornado",
  "Tornado",
  "Tornado",
  "Tornado",
  "Tornado",
  "Tornado",
  "Tornado",
  "Tornado",
  "Tornado",
  "Tornado",
  "Tornado",
  "Tornado",
  "Tornado",
  "Tornado",
  "Tornado",
  "Tornado",
  "Tornado",
  "Tornado",
  "Tornado",
  "Tornado",
  "Tornado",
  "Tornado",
  "Tornado",
  "Tornado",
  "Tornado",
  "Tornado",
  "Tornado",
  "Tornado",
  "Torrent",
  "Tristan",
  "Vargur",
  "Vargur",
  "Vargur",
  "Velator",
  "Venture",
  "Venture",
  "Venture",
  "Venture",
  "Vexor Navy Issue",
  "Viator",
  "Vigil",
  "Wreathe",
];
const REAL_PASTE_2_EXPECTED_DISTANCES = [
  "-",
  "-",
  "69 km",
  "13 km",
  "1,155 km",
  "14 km",
  "19 km",
  "128 km",
  "49 km",
  "13 km",
  "14 km",
  "48 km",
  "26 km",
  "3,019 m",
  "2,215 km",
  "34 km",
  "355 km",
  "30 km",
  "-",
  "127 km",
  "-",
  "5,984 m",
  "125 km",
  "125 km",
  "16 km",
  "60 km",
  "50 km",
  "11 km",
  "49 km",
  "58 km",
  "28 km",
  "16 km",
  "26 km",
  "32 km",
  "49 km",
  "48 km",
  "64 km",
  "53 km",
  "28 km",
  "25 km",
  "5,040 m",
  "50 km",
  "16 km",
  "51 km",
  "40 km",
  "37 km",
  "22 km",
  "14 km",
  "59 km",
  "-",
  "15 km",
  "13 km",
  "13 km",
  "17 km",
  "24 km",
  "47 km",
  "3,275 m",
  "12 km",
  "17 km",
  "-",
  "50 km",
  "432 km",
  "31 km",
  "18 km",
  "23 km",
  "-",
  "63 km",
  "13 km",
  "51 km",
  "29 km",
  "50 km",
  "48 km",
  "39 km",
  "41 km",
  "23 km",
  "-",
  "104 km",
  "12 km",
  "27 km",
  "23 km",
  "-",
  "156 km",
  "254 km",
  "48 km",
  "29 km",
  "-",
  "40 km",
  "-",
  "-",
  "-",
  "15 km",
  "-",
  "-",
  "39 km",
  "-",
  "26 km",
  "-",
  "40 km",
  "-",
  "18 km",
  "-",
  "22 km",
  "29 km",
  "13 km",
  "24 km",
  "25 km",
  "-",
  "23 km",
  "50 km",
  "63 km",
  "39 km",
  "63 km",
  "46 km",
  "66 km",
  "65 km",
  "63 km",
  "61 km",
  "57 km",
  "57 km",
  "47 km",
  "61 km",
  "56 km",
  "64 km",
  "47 km",
  "51 km",
  "65 km",
  "56 km",
  "50 km",
  "4,992 m",
  "341 km",
  "48 km",
  "60 km",
  "53 km",
  "60 km",
  "65 km",
  "50 km",
  "61 km",
  "60 km",
  "44 km",
  "52 km",
  "63 km",
  "67 km",
  "66 km",
  "51 km",
  "-",
  "49 km",
  "50 km",
  "51 km",
  "15 km",
  "26 km",
  "-",
  "24 km",
  "10 km",
  "29 km",
  "24 km",
  "14 km",
  "1,103 km",
  "134 km",
  "-",
  "-",
  "11 km",
  "33 km",
  "27 km",
  "-",
  "-",
  "-",
  "-",
  "-",
  "-",
  "-",
  "-",
  "-",
  "787 km",
  "-",
  "-",
  "-",
  "-",
  "-",
  "-",
  "8,233 m",
  "-",
  "86 km",
  "41 km",
  "28 km",
  "126 km",
  "515 km",
  "22 km",
  "50 km",
  "47 km",
  "53 km",
  "1,230 km",
  "47 km",
  "52 km",
  "61 km",
  "1,231 km",
  "53 km",
  "53 km",
  "52 km",
  "1,229 km",
  "64 km",
  "51 km",
  "61 km",
  "53 km",
  "44 km",
  "104 km",
  "58 km",
  "1,229 km",
  "1,232 km",
  "1,229 km",
  "1,230 km",
  "1,230 km",
  "1,231 km",
  "1,231 km",
  "51 km",
  "54 km",
  "12 km",
  "4,675 m",
  "51 km",
  "52 km",
  "49 km",
  "18 km",
  "8,161 m",
  "13 km",
  "26 km",
  "-",
  "-",
  "4,344,227 km",
  "66 km",
  "32 km",
];

const r2 = checkBlock('REAL-PASTE-2 (round 3, 229 contacts)', REAL_PASTE_2, REAL_PASTE_2_EXPECTED_TYPES, REAL_PASTE_2_EXPECTED_DISTANCES);

pass += r1.pass + r2.pass;
fail += r1.fail + r2.fail;

// Bug list #1 (2026-10-14, v2026.10.14.9): an EFT fit pasted into the D-Scan
// box must be recognized as a fit and refused; no real scan may trip the
// check. The real pastes are tested whole AND starting at every one of their
// rows (any row can end up first after a partial copy). Expected values
// written before the code: EFT header -> {format:'EFT', shipName, fitName};
// everything else -> null. NOT_IN_SPACE_CATEGORY_IDS from the SDE
// categories file: fitted/character/hangar-only categories in, every
// category that can be a D-Scan contact out (ship 6, drone 18, charge 8 --
// probes/bombs, deployable 22, celestial 2, structure 65, fighter 87,
// starbase 23, sovereignty 40, orbitals 46, asteroid 25).
const FIT_CASES = [
  { label: 'EFT: client copy', text: '[Rifter, the owner test]\nDamage Control II\n\n5MN Microwarpdrive II\n', expect: { format: 'EFT', shipName: 'Rifter', fitName: 'the owner test' } },
  { label: 'EFT: pyfa export with leading blank lines/spaces', text: '\n  \n  [Legion, *Simulated Legion Fit]\nMedium Armor Repairer II\n', expect: { format: 'EFT', shipName: 'Legion', fitName: '*Simulated Legion Fit' } },
  { label: 'EFT: header without a fit name', text: '[Purifier]\nDamage Control II', expect: { format: 'EFT', shipName: 'Purifier', fitName: '' } },
  { label: 'EFT: Windows line endings', text: '[Svipul, pvp]\r\nDamage Control II\r\n', expect: { format: 'EFT', shipName: 'Svipul', fitName: 'pvp' } },
  { label: 'not a fit: single ship name', text: 'Purifier', expect: null },
  { label: 'not a fit: lowercase ship name', text: 'svipul', expect: null },
  { label: 'not a fit: "[Empty High slot]" placeholder first', text: '[Empty High slot]\nDamage Control II', expect: null },
  { label: 'not a fit: modules only, no header', text: 'Damage Control II\n400mm Steel Plates II', expect: null },
  { label: 'not a fit: empty', text: '   \n', expect: null },
  { label: 'not a fit: tabbed row whose name is bracketed', text: '587\t[OXF] Rifter\tRifter\t10 km', expect: null },
  { label: 'not a fit: tabbed row that is entirely bracketed', text: '[x, y]\tRifter\t10 km', expect: null },
];
if (typeof sandbox.detectFitPaste !== 'function' || typeof sandbox.isNotInSpaceCategory !== 'function') {
  console.log('FAIL: detectFitPaste() / isNotInSpaceCategory() not found'); fail++;
} else {
  for (const c of FIT_CASES) {
    const got = sandbox.detectFitPaste(c.text);
    const ok = JSON.stringify(got) === JSON.stringify(c.expect);
    if (ok) pass++; else { fail++; console.log(`FAIL: ${c.label} -- expected ${JSON.stringify(c.expect)}, got ${JSON.stringify(got)}`); }
  }
  let realOk = 0, realBad = 0;
  for (const [name, text] of [['REAL_PASTE', REAL_PASTE], ['REAL_PASTE_2', REAL_PASTE_2]]) {
    const lines = text.split('\n');
    for (let i = 0; i < lines.length; i++) {
      const got = sandbox.detectFitPaste(lines.slice(i).join('\n'));
      if (got === null) realOk++; else { realBad++; console.log(`FAIL: ${name} from row ${i} detected as a fit: ${JSON.stringify(got)}`); }
    }
  }
  if (realBad) fail++; else pass++;
  console.log(`detectFitPaste: ${FIT_CASES.length} cases + ${realOk + realBad} real-paste starting rows (${realBad} misread)`);
  const NOT_IN_SPACE = [7, 9, 16, 20, 30, 32, 66, 91, 2100];
  const IN_SPACE = [2, 6, 8, 18, 22, 23, 25, 40, 46, 65, 87];
  const catBad = NOT_IN_SPACE.filter(c => !sandbox.isNotInSpaceCategory(c)).concat(IN_SPACE.filter(c => sandbox.isNotInSpaceCategory(c)));
  if (catBad.length) { fail++; console.log(`FAIL: isNotInSpaceCategory wrong for categories ${catBad}`); } else pass++;
}
const totalCases = CASES.length + REAL_PASTE_EXPECTED_TYPES.length + REAL_PASTE_2_EXPECTED_TYPES.length + FIT_CASES.length + 2;

console.log(`\n${pass}/${totalCases} PASS` + (fail ? `, ${fail} FAIL` : ''));
process.exit(fail ? 1 : 0);

