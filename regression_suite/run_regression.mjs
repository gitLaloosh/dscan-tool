#!/usr/bin/env node
// Regression suite for dscan-tool.html's estimateHpAndDps().
//
// WHY THIS EXISTS: on 2026-09-10 we discovered that THREE previously-found,
// previously-validated bugs (Damage Control treated as an independent
// resistance multiplier instead of pooled with hardeners; the 20% Shield/
// Armor Compensation skill assumption gated on a qualifying hardener
// actually being fitted; fitted-module quantity not collapsed to 1 copy)
// had all silently regressed back into claude/dscan-tool_15.html at some
// point between sessions, most likely because a later session edited a
// stale/cached copy of the file rather than the current canonical one, and
// then overwrote the canonical copy with that stale-based edit. There was
// no automated check to catch this.
//
// RULE GOING FORWARD: before delivering ANY change to index.html
// (via SendUserFile, device_commit_files, or project_write), run this
// script against the candidate file:
//
//   node run_regression.mjs                 (defaults to ../index.html)
//   node run_regression.mjs /path/to/candidate.html
//
// It must print ALL PASS. If a fit that used to pass now fails, that is a
// regression — do not deliver until you understand why and either fix it
// or deliberately update golden_fits.json's expected values (and say so
// explicitly, never silently).
//
// This suite currently has one entry (the Legion fit from the 2026-09-10
// session — the first one verified against live ESI + the real tool's
// reported output). Add an entry for every fit verified from now on
// (Hawk, Rifter, Caracal, Ishtar were validated in earlier sessions but
// their raw ESI dogma data was never saved anywhere durable, so they
// aren't reconstructable without re-fetching from ESI — do that once and
// add them here rather than re-deriving by hand each session).

import fs from 'fs';
import path from 'path';
import vm from 'vm';
import { fileURLToPath } from 'url';
import { checkPyfaCore } from '../tools/check_pyfa_core.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const htmlPath = process.argv[2] || path.join(__dirname, '..', 'index.html');
const goldenPath = path.join(__dirname, 'golden_fits.json');

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
const golden = JSON.parse(fs.readFileSync(goldenPath, 'utf8'));

// GUARD (added 2026-10-11, incident: a stale duplicate regression_suite\
// folder -- leftover from an earlier abandoned-duplicate-folder scrape --
// got invoked by a relative path instead of the current canonical files,
// silently running a ~1-month-old 10-fit golden_fits.json against a
// freshly-edited dscan-tool.html. The mismatched pair still produced a
// plausible-looking FAIL list (stale Hawk dpsFixed range, etc.), easy to
// mistake for a real regression. This line makes that impossible to miss:
// always prints exactly which two files (absolute paths) and how many
// fits are about to run, every single invocation.
console.log(`Testing: ${path.resolve(htmlPath)}`);
console.log(`Against: ${path.resolve(goldenPath)} (${Object.keys(golden).length} fits)\n`);

let anyFail = false;
// v2026.10.14.35 (PYFA CORE projected): every fit's application / projectedTarget, for the cross-fit pins
// "tackled@<target fitId>,distance=..,speed=<share of the target's top speed>[,lock=1][,dcr=1][,drones=1|2|3]"
// (the target's speed under this fit's webs / scram) and "painted@..." (its signature radius under this fit's
// painters), checked after every fit has run.
const projApps = {}, projTargets = {}, projPins = [];
let lastSandbox = null;
const PROJ_PIN = /^(tackled|painted)@/;

// PYFA CORE lock (2026-10-14, PYFA_CORE.md): code fenced as PYFA CORE in index.html
// must match the fingerprints in tools/pyfa_core_manifest.json. A changed section
// fails the suite until it is re-verified against pyfa and the manifest updated.
{
  const core = checkPyfaCore(html);
  if (core.ok) console.log(`PYFA CORE: ${Object.keys(core.sections).length} sections match the manifest`);
  else { console.log('*** PYFA CORE LOCK:\n  ' + core.problems.join('\n  ')); anyFail = true; }
}

for (const [fitId, fit] of Object.entries(golden)) {
  const TYPES = fit.types;
  const GROUPS = fit.groups;

  async function fakeFetch(url) {
    const typeMatch = url.match(/\/universe\/types\/(\d+)\//);
    const groupMatch = url.match(/\/universe\/groups\/(\d+)\//);
    if (typeMatch) {
      const id = typeMatch[1];
      if (TYPES[id]) return { ok: true, json: async () => TYPES[id] };
      return { ok: false, status: 404 };
    }
    if (groupMatch) {
      const id = groupMatch[1];
      if (GROUPS[id]) return { ok: true, json: async () => GROUPS[id] };
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

  // FIXED 2026-10-09: this used to be hardcoded to an always-empty Set,
  // meaning this harness NEVER exercised estimateHpAndDps()'s cargo-ammo-
  // fallback-guess code path (where unresolved/empty turrets or launchers
  // get matched against spare ammo sitting in Cargo or Fleet Hangar) --
  // discovered while adding bugs #24 (T2 hybrid/energy ammo group names)
  // and #25 (Fleet Hangar flag 155), both of which live entirely inside
  // that path. Fixed to derive cargoItemIds the same way the real tool's
  // own buildLossTally() does: every item id sitting in the fit's own
  // 'Cargo' and/or 'Fleet hangar' tally buckets. Verified harmless for
  // every pre-existing golden fit (many already have real Cargo items in
  // their tally, e.g. loki_zkb138990669/vargur_zkb138983121_bastion/etc.)
  // by diffing the full estimateHpAndDps() result object with this fix
  // applied vs the old always-empty behavior across all 24 fits: zero
  // differences in any field, on any fit -- because none of them happen to
  // have an UNRESOLVED weapon (every turret/launcher already has a loaded
  // charge confirmed from its own killmail flag), so cargoItemIds being
  // populated or not never mattered for those. See the two
  // *_cargo_fallback/*_fleet_hangar golden fits below for the first
  // entries that actually exercise this path.
  // FIXED 2026-10-09 (second gap, found while adding bug #25's own golden
  // fit): everything above derives cargoItemIds/highSlotByFlag from a golden
  // fit's PRE-BUILT `tally`/`highSlotByFlag` JSON -- which every existing fit
  // supplies pre-shaped, as if buildLossTally() had already run correctly.
  // That means this harness has NEVER actually called buildLossTally() or
  // slotGroupFor() itself, for ANY fit, ever -- so it could not have caught
  // bug #25 (SLOT_GROUPS missing a Fleet Hangar/flag-155 entry entirely,
  // causing buildLossTally() to silently DISCARD those items via its
  // `if(!group) continue`) even with cargoItemIds fixed above, because the
  // bug lives upstream of where this harness starts. A golden fit can now
  // supply a raw `killmail` (shape: {victim:{ship_type_id, items:[...]}},
  // same as a real ESI killmail response) INSTEAD of pre-built tally/
  // highSlotByFlag; when present, this harness calls the real tool's own
  // buildLossTally() on it, exactly like the live tool does, so a future
  // regression in SLOT_GROUPS/slotGroupFor()/buildLossTally() itself is
  // actually caught. See azariel_constructed_fleethangar_fallback below for
  // the first (only) fit using this path. Every pre-existing fit keeps using
  // pre-built tally/highSlotByFlag (backward compatible, zero behavior
  // change for them).
  let tally, cargoItemIds, highSlotByFlag, midSlotByFlag;
  if (fit.killmail) {
    ({ tally, cargoItemIds, highSlotByFlag, midSlotByFlag } = sandbox.buildLossTally(fit.killmail));
  } else {
    tally = fit.tally;
    cargoItemIds = new Set([
      ...Object.keys(fit.tally['Cargo'] || {}),
      ...Object.keys(fit.tally['Fleet hangar'] || {})
    ].map(Number));
    highSlotByFlag = new Map();
    for (const [flag, items] of Object.entries(fit.highSlotByFlag || {})) {
      highSlotByFlag.set(Number(flag), items);
    }
    // Capacitor Booster follow-up (2026-10-12) -- same backward-compatible
    // shape as highSlotByFlag above: a pre-built "constructed" golden fit
    // can optionally supply its own midSlotByFlag JSON; every fit that
    // doesn't (all of them, as of this change) just gets an empty Map, same
    // as if no Capacitor Booster were fitted -- zero behavior change.
    midSlotByFlag = new Map();
    for (const [flag, items] of Object.entries(fit.midSlotByFlag || {})) {
      midSlotByFlag.set(Number(flag), items);
    }
  }

  // Tactical Destroyer Mode (bug #17b): a golden fit can pin an optional
  // "tacticalMode" field ('sharpshooter'/'defense'/'propulsion') to lock in
  // one of the 3 mode-specific variants instead of the default. Harmless
  // no-op (estimateHpAndDps's own default param applies) for every fit that
  // doesn't set it.
  let result, error;
  try {
    // Module states (v2026.10.13.20, module-state plan Phase 1): a golden
    // fit can pin an optional "moduleStates" object ({typeId: 'offline' |
    // 'online' | 'active'} or {typeId: {active, online, offline}}), the same
    // way tacticalMode works. Fits without it run at the default states.
    result = await sandbox.estimateHpAndDps(fit.shipTypeId, tally, cargoItemIds, highSlotByFlag, fit.tacticalMode || 'sharpshooter', midSlotByFlag, fit.moduleStates || null, fit.droneStates || null, fit.fitSource ? {fitSource: fit.fitSource} : null);
  } catch (e) {
    error = e;
  }

  // EFT-export regression coverage ("export fit to clipboard" context-menu
  // backlog item, 2026-10-12): fitToEftText() takes the exact same
  // tally/highSlotByFlag shape already built above for estimateHpAndDps(),
  // plus an idToName map -- built straight from this fit's own `types`
  // dump (every golden fit already carries real ESI type names there),
  // not a live /universe/ids/ name-resolution call, which this harness has
  // never needed to fake before and fitToEftText() doesn't call either (it
  // only reads names back out of the map it's given). A golden fit opts in
  // by setting `expected.eftExportText` to the exact full string; harmless
  // no-op for every other fit (the generic exact-match checker below skips
  // any `expected` key whose result field doesn't exist, and this adds the
  // field to every successful fit regardless). Only attempted when
  // estimateHpAndDps() itself didn't already throw (`result` set).
  if (result) {
    try {
      const idToName = new Map(Object.entries(TYPES).map(([id, t]) => [Number(id), t.name]));
      const shipName = TYPES[String(fit.shipTypeId)] ? TYPES[String(fit.shipTypeId)].name : fit.label;
      result.eftExportText = await sandbox.fitToEftText(shipName, 'regression-fit', tally, idToName, highSlotByFlag);
    } catch (e) {
      // Leave eftExportText unset -- a fit with no expectation on it is
      // unaffected either way, same as every other derived-scalar block.
    }
  }

  // Derived scalar for golden fits that need to pin the SHAPE of
  // ammoEstimates (added 2026-10-09 alongside the first fit exercising the
  // cargo-ammo-fallback-guess path, see cargoItemIds fix above): the raw
  // `ammoEstimates` array can't go through the generic exact/range checker
  // below (it's an array of {name, dps} objects, not a number), so expose
  // its length as its own field. This is what actually catches bug #24
  // (T2 hybrid/energy ammo group names unrecognized) regressing -- verified
  // by diffing a deliberately-reverted copy of ammoCategoryFromGroup against
  // the abaddon_zkb138966900_cargo_fallback fit below: cargoResolvedWeaponCount/
  // unmatchedWeaponCount/dpsFixed all stay IDENTICAL whether the bug is
  // present or not (every candidate ammo's weapon category still resolves via
  // the one pre-existing group name), only ammoEstimates.length changes
  // (3 -> 1, losing Scorch L and Conflagration L). Harmless no-op for every
  // other existing fit (none of them exercise this path at all, so
  // result.ammoEstimates is always []).
  if (result && Array.isArray(result.ammoEstimates)) {
    result.ammoEstimatesCount = result.ammoEstimates.length;
  }

  // Derived scalars for F3 backlog item ("test the repair calculations",
  // added 2026-10-10): `tankStyle.{shield,armor,hull}` is a nested object
  // (or null) per layer, which can't go through the generic exact/range
  // checker below either -- same shape problem ammoEstimates had above, same
  // fix (flatten to named scalar fields a golden fit's `expected` can pin).
  // `has*RepFlag` is ALWAYS set (0 or 1), specifically so a fit can assert
  // ABSENCE of a self-rep (the generic checker used to skip any key whose
  // result is undefined -- since v.27 it FAILS instead -- so there has to be a real 0/1 to assert against) --
  // this is what actually catches a REMOTE Armor/Shield/Hull Repairer ever
  // being miscounted as a self-rep (groupName.includes('remote') exclusion
  // regressing): see leshak_zkb139013625_precursor_battleship_role_bonus
  // below, a real loss with a Large Remote Armor Repairer II fitted that
  // must NOT register as armorRepSustainedDps. The *SustainedDps/*BurstDps
  // fields are only set when the corresponding layer is non-null (nothing
  // to pin otherwise).
  if (result && result.tankStyle) {
    // Passive shield recharge fix (2026-10-12): tankStyle.shield is now
    // non-null whenever the hull has ANY shield HP at all (every ship
    // regens passively, module or not -- see estimateHpAndDps()'s own
    // comment on this), so hasShieldRepFlag/shieldRepSustainedDps below
    // are kept pinned to their ORIGINAL meaning -- an ACTIVE Shield
    // Booster specifically (tankStyle.shield.activeDps) -- rather than
    // "shield entry exists at all", so every pre-existing golden fit's
    // pinned 0/1 and exact DPS values (e.g. curse_zkb139073592_ewar's
    // hasShieldRepFlag:0, hawk_user's shieldRepSustainedDps:97) keep
    // meaning exactly what they always did. hasShieldPassiveRegenFlag/
    // shieldPassiveRegenDps/shieldBreakPointDps are the new fields this
    // fix actually exercises.
    result.hasShieldRepFlag = result.tankStyle.shield && result.tankStyle.shield.activeDps ? 1 : 0;
    result.hasArmorRepFlag = result.tankStyle.armor ? 1 : 0;
    result.hasHullRepFlag = result.tankStyle.hull ? 1 : 0;
    if (result.tankStyle.shield && result.tankStyle.shield.activeDps) result.shieldRepSustainedDps = result.tankStyle.shield.activeDps;
    result.hasShieldPassiveRegenFlag = result.tankStyle.shield ? 1 : 0;
    if (result.tankStyle.shield) {
      result.shieldPassiveRegenDps = result.tankStyle.shield.passiveDps;
      result.shieldBreakPointDps = result.tankStyle.shield.breakPointDps;
    }
    if (result.tankStyle.armor) {
      result.armorRepSustainedDps = result.tankStyle.armor.sustainedDps;
      if (result.tankStyle.armor.burstDps) result.armorRepBurstDps = result.tankStyle.armor.burstDps;
    }
    if (result.tankStyle.hull) result.hullRepSustainedDps = result.tankStyle.hull.sustainedDps;
  }
  // Drone Control Range (F2 half, Phase 5, added 2026-10-11) -- same
  // flattening reason as tankStyle above: the generic checker can't assert
  // on a nested object, so pin the total (and the module/ship-bonus
  // components, when a golden fit specifically needs to catch one of those
  // paths regressing) as flat scalar fields.
  // Resist profiles (added 2026-10-13, full-EFT Rorqual pyfa check) -- same
  // flattening reason: pin each layer's per-damage-type resist % as flat
  // scalars (shieldResEm, armorResExp, hullResKin, ...).
  if (result) {
    for (const layer of ['shield', 'armor', 'hull']) {
      const r = result[layer + 'ResPct'];
      if (!r) continue;
      for (const [k, cap] of [['em', 'Em'], ['therm', 'Therm'], ['kin', 'Kin'], ['exp', 'Exp']]) {
        if (typeof r[k] === 'number') result[layer + 'Res' + cap] = r[k];
      }
    }
  }
  // Module states (v2026.10.13.20): totals of copies per state and the
  // number of refused requests, flattened for pinning.
  if (result && result.moduleStates) {
    const ms = result.moduleStates;
    result.moduleStatesRefusedCount = ms.refused.length;
    result.moduleStatesActiveCount = ms.items.reduce((s, x) => s + x.active, 0);
    result.moduleStatesOnlineCount = ms.items.reduce((s, x) => s + x.online, 0);
    result.moduleStatesOfflineCount = ms.items.reduce((s, x) => s + x.offline, 0);
  }
  // Drone states (v2026.10.13.23): drones in space, bandwidth used and
  // refused requests, flattened for pinning. A fit may carry "droneStates"
  // ({typeId: count in space}) as the engine's 8th argument.
  if (result && result.droneStates) {
    result.droneStatesActiveCount = result.droneStates.activeCount;
    result.droneStatesBandwidthUsed = result.droneStates.bandwidthUsed;
    result.droneStatesRefusedCount = result.droneStates.refused.length;
  }
  if (result && result.droneControlRange) {
    result.droneControlRangeTotal = result.droneControlRange.total;
    result.droneControlRangeModuleBonus = result.droneControlRange.moduleBonus;
    result.droneControlRangeShipBonus = result.droneControlRange.shipBonus;
  }
  // Dual-prop-mod fix (2026-10-11) -- same flattening reason as above:
  // hasSecondaryPropMod lets a golden fit assert ABSENCE (0) on a
  // single/no-prop-mod fit, same purpose as hasShieldRepFlag etc.
  if (result && result.speed) {
    result.hasSecondaryPropMod = result.speed.secondaryBoosted !== null ? 1 : 0;
    if (result.speed.secondaryBoosted !== null) result.speedSecondaryBoosted = result.speed.secondaryBoosted;
  }
  if (result && result.alignTime && result.alignTime.secondaryBoosted !== null) {
    result.alignTimeSecondaryBoosted = result.alignTime.secondaryBoosted;
  }
  // Tactical Destroyer Propulsion Mode fix (2026-10-11) -- same flattening
  // reason as above: the PRIMARY speed/alignTime/capacitor fields were never
  // flattened before now because no prior golden fit needed to assert on
  // them directly (only the *Secondary ones, dual-prop-mod-specific). Needed
  // now to pin that Propulsion Mode actually changes these numbers (it
  // silently didn't, pre-fix) without breaking anything that already reads
  // the nested result.speed/alignTime/capacitor objects elsewhere.
  if (result && result.speed) {
    result.speedCruising = result.speed.cruising;
    if (result.speed.boosted !== null) result.speedBoosted = result.speed.boosted;
  }
  if (result && result.alignTime) {
    result.alignTimeBase = result.alignTime.base;
    if (result.alignTime.boosted !== null) result.alignTimeBoosted = result.alignTime.boosted;
  }
  // v2026.10.14.25: drone recommendation as shown ("Name (size)"; alt 'none' when there is no second pick)
  if (result && result.drones && result.drones.primary) {
    result.droneRecPrimary = `${result.drones.primary.name} (${result.drones.primary.size})`;
    result.droneRecAlt = result.drones.alt ? `${result.drones.alt.name} (${result.drones.alt.size})` : 'none';
  }
  if (result && result.capacitor) {
    result.capacitorActiveDrainPerSec = result.capacitor.activeDrainPerSec;
    // Backlog #16 fix (2026-10-11): capacitor.capacity had no flattened
    // assertion field at all before now -- needed to pin the new T3 Core
    // subsystem flat capacitor-capacity-self-add fix (and to catch it
    // regressing for every other hull's un-boosted capacity too).
    result.capacitorCapacity = result.capacitor.capacity;
    // KNOWN OPEN ITEM #1 fix (2026-10-12 follow-up): peakRechargeRate/
    // netRate had no flattened assertion fields before now -- needed to
    // pin the Power Diagnostic System/Shield Power Relay fix (both affect
    // peakRechargeRate without necessarily changing capacity or the
    // other already-pinned fields above).
    result.capacitorPeakRechargeRate = result.capacitor.peakRechargeRate;
    result.capacitorNetRate = result.capacitor.netRate;
    // Capacitor stability fix (backlog #2, 2026-10-12) -- stable/stablePct/
    // timeToEmptySec/weak had no flattened assertion fields before now.
    // Booleans flattened as 0/1 ints, same convention as hasEwar/
    // hasCynoFitted above.
    result.capacitorStable = result.capacitor.stable ? 1 : 0;
    if (result.capacitor.stablePct !== null) result.capacitorStablePct = result.capacitor.stablePct;
    if (result.capacitor.timeToEmptySec !== null) result.capacitorTimeToEmptySec = result.capacitor.timeToEmptySec;
    result.capacitorWeak = result.capacitor.weak ? 1 : 0;
    // v2026.10.13.12: net rate of the confident boosted tier (loaded/inferred
    // cap booster + ASB charges), the figure comparable to pyfa's capDelta.
    // v2026.10.13.27: the primary capacitor fields ARE the best case of the
    // running modules now (no ring toggle). The old combinedConfident tier is
    // gone; its pins moved to capacitorNetRate. withoutBoosts (no Capacitor
    // Booster injection, ASBs on capacitor) and asbDry (ASBs out of charges)
    // are flattened for pinning, only when present.
    if (typeof result.capacitor.injectionPerSec === 'number') result.capacitorInjectionPerSec = result.capacitor.injectionPerSec;
    for (const [obj, pre] of [[result.capacitor.withoutBoosts, 'capacitorNoBoost'], [result.capacitor.asbDry, 'capacitorAsbDry']]) {
      if (!obj) continue;
      result[pre + 'ActiveDrainPerSec'] = obj.activeDrainPerSec;
      result[pre + 'NetRate'] = obj.netRate;
      result[pre + 'Stable'] = obj.stable ? 1 : 0;
      if (obj.stablePct !== null) result[pre + 'StablePct'] = obj.stablePct;
      if (obj.timeToEmptySec !== null) result[pre + 'TimeToEmptySec'] = obj.timeToEmptySec;
    }
    // v2026.10.13.10: the Weaknesses-card ring's own time (best-case tier), so a
    // golden fit can pin it to the boosted figure the caption describes.
    if (result.capacitor.weakTimeToEmptySec !== undefined && result.capacitor.weakTimeToEmptySec !== null) result.capacitorWeakTimeToEmptySec = result.capacitor.weakTimeToEmptySec;
    // KNOWN OPEN ITEM #4 fix (2026-10-12 follow-up): warfareResistPct had
    // no flattened assertion field before now -- only present (non-null)
    // when a Capacitor Battery is fitted, same "only when not null"
    // convention as boosted/range below.
    if (result.capacitor.warfareResistPct !== null) result.capacitorWarfareResistPct = result.capacitor.warfareResistPct;
    // Capacitor Booster gain modeling (2026-10-12, the owner-approved follow-up to
    // the capacitor-stability fix above): hasCapBooster/chargeUnidentified
    // had no flattened assertion fields before now. boosted.* only flattened
    // when a charge was actually identified (mirrors the speed/alignTime
    // "only when boosted !== null" convention above) -- a fit with no
    // Capacitor Booster at all, or one with an unidentified charge, is
    // pinned purely by hasCapBooster/chargeUnidentified being 0/1 as
    // expected, with no boosted* fields present (same as how a fit with no
    // prop mod has no speedBoosted field).
    result.capacitorHasCapBooster = result.capacitor.hasCapBooster ? 1 : 0;
    result.capacitorChargeUnidentified = result.capacitor.chargeUnidentified ? 1 : 0;
    // v2026.10.14.24: pasted-fit boosters with no charges anywhere (Weaknesses card flag), and each boost's source
    result.capacitorChargesMissing = (result.capacitor.chargesMissing || []).length;
    for (const b of result.capacitor.boosts || []) result[`capacitorBoostSource_${b.kind}`] = b.source;
    if (result.capacitor.boosted) {
      result.capacitorBoostedGainPerSec = result.capacitor.boosted.gainPerSec;
      result.capacitorBoostedStable = result.capacitor.boosted.stable ? 1 : 0;
      if (result.capacitor.boosted.stablePct !== null) result.capacitorBoostedStablePct = result.capacitor.boosted.stablePct;
      if (result.capacitor.boosted.timeToEmptySec !== null) result.capacitorBoostedTimeToEmptySec = result.capacitor.boosted.timeToEmptySec;
      // Cargo-inference fallback (2026-10-12, the owner follow-up): fromCargo
      // flattened as 0/1 same convention as every other boolean here --
      // distinguishes a flag-paired-confirmed boosted figure from one
      // inferred off spare charges sitting in cargo.
      result.capacitorBoostedFromCargo = result.capacitor.boosted.fromCargo ? 1 : 0;
    }
    // Bounded-range fallback (2026-10-12, the owner follow-up): only present when
    // a Capacitor Booster is fitted with NO identified charge anywhere
    // (neither flag-paired nor cargo-inferred) -- see CAP_BOOSTER_CHARGE_
    // CATALOG comment in dscan-tool.html for the grounding. min/max flattened
    // the same "only when not null" convention as boosted.* above.
    if (result.capacitor.range) {
      result.capacitorRangeMinGainPerSec = result.capacitor.range.minGainPerSec;
      result.capacitorRangeMaxGainPerSec = result.capacitor.range.maxGainPerSec;
      result.capacitorRangeMinStable = result.capacitor.range.min.stable ? 1 : 0;
      result.capacitorRangeMaxStable = result.capacitor.range.max.stable ? 1 : 0;
      if (result.capacitor.range.min.stablePct !== null) result.capacitorRangeMinStablePct = result.capacitor.range.min.stablePct;
      if (result.capacitor.range.max.stablePct !== null) result.capacitorRangeMaxStablePct = result.capacitor.range.max.stablePct;
    }
  }
  // Rig drawback routing fix (independent review finding #1, 2026-10-11) --
  // signature radius had NO regression coverage at all before now (part of
  // why the sig-radius/agility rig-drawback cross-contamination bug went
  // undetected). Flattened for the first time here.
  if (result && result.signatureRadius) {
    result.signatureRadiusBase = result.signatureRadius.base;
    // Backlog #10 fix (2026-10-11): the MWD-active boosted figure had no
    // flattened assertion field either -- needed now to pin the Interceptor
    // sig-bloom-reduction fix (and to catch it regressing for every other
    // hull's un-reduced boosted figure too).
    if (result.signatureRadius.boosted !== null) result.signatureRadiusBoosted = result.signatureRadius.boosted;
  }
  // EWAR capabilities card (F3, added 2026-10-11) -- same flattening reason
  // as tankStyle/droneControlRange above: result.ewarModules is an array of
  // {name, category, kind, rangeM, qty, ...} objects, which can't go through
  // the generic exact/range checker below. hasEwar is ALWAYS set (0 or 1),
  // specifically so a fit can assert ABSENCE of any EWAR module (mirrors
  // has*RepFlag's reasoning) -- this is what would catch a false-positive
  // EWAR_GROUP_INFO match (e.g. a module whose ESI group name happens to
  // collide with one of the 7 tracked groups) ever regressing on a fit that
  // should show zero. ewarModuleCount sums quantities (a stack of 2x Tracking
  // Disruptor II counts as 2); ewarTypeCount counts distinct module names.
  if (result && result.ewarModules) {
    result.ewarModuleCount = result.ewarModules.reduce((sum, m) => sum + m.qty, 0);
    result.ewarTypeCount = new Set(result.ewarModules.map(m => m.name)).size;
    result.hasEwar = result.ewarModules.length > 0 ? 1 : 0;
    result.ewarLongestRangeM = result.ewarModules.length > 0 ? Math.max(...result.ewarModules.map(m => m.rangeM)) : 0;
    // v2026.10.14.11 (hand-tables P4): every entry's numbers, keyed by module name and loaded script
    // ('-' when none), e.g. "ewar:Tracking Disruptor II:Optimal Range Disruption Script:opticalBonusPct" --
    // copies of one type with different scripts are separate entries since v.11.
    for (const m of result.ewarModules) {
      for (const [f, v] of Object.entries(m)) if (typeof v === 'number') result[`ewar:${m.name}:${m.script || '-'}:${f}`] = v;
      // v2026.10.14.26: Command Burst buffs, e.g. "ewar:Shield Command Burst II:Shield Harmonizing Charge:buff10"
      for (const b of m.buffs || []) result[`ewar:${m.name}:${m.script || '-'}:buff${b.id}`] = b.value;
    }
    // EWAR effectiveness bonuses (skills/hull/subsystem/rig, added
    // 2026-10-11) -- flattened per-kind so a golden fit can pin the EXACT
    // boosted magnitude of whichever EWAR kind(s) it carries (every golden
    // fit in this set has at most one module of any given kind on its
    // defensive slots, so "first match per kind" is unambiguous) without
    // the generic checker below needing to reach into the ewarModules
    // array itself. Only set when that kind is actually present, same
    // "assert absence separately via hasEwar" convention as above.
    const byKind = (k) => result.ewarModules.find(m => m.kind === k);
    const ecmM = byKind('ecm'), webM = byKind('web'), scramM = byKind('scram'), paintM = byKind('paint'), dampM = byKind('damp'), tdM = byKind('trackingDisruptor'), gdM = byKind('guidanceDisruptor'), neutM = byKind('neut'), nosM = byKind('nos');
    if (ecmM) { result.ewarEcmJamStrength = ecmM.jamStrength; result.ewarEcmRangeM = ecmM.rangeM; result.ewarEcmFalloffM = ecmM.falloffM; }
    if (webM) { result.ewarWebRangeM = webM.rangeM; result.ewarWebSpeedBonusPct = webM.speedBonusPct; }
    if (scramM) { result.ewarScramRangeM = scramM.rangeM; result.ewarScramStrength = scramM.scramStrength; }
    if (paintM) { result.ewarPaintRangeM = paintM.rangeM; result.ewarPaintFalloffM = paintM.falloffM; result.ewarPaintSigRadiusBonusPct = paintM.sigRadiusBonusPct; }
    if (dampM) { result.ewarDampRangeM = dampM.rangeM; result.ewarDampFalloffM = dampM.falloffM; result.ewarDampTargetingRangeBonusPct = dampM.targetingRangeBonusPct; result.ewarDampScanResolutionBonusPct = dampM.scanResolutionBonusPct; }
    if (tdM) { result.ewarTdRangeM = tdM.rangeM; result.ewarTdFalloffM = tdM.falloffM; result.ewarTdOpticalBonusPct = tdM.opticalBonusPct; result.ewarTdFalloffBonusPct = tdM.falloffBonusPct; result.ewarTdTrackingSpeedBonusPct = tdM.trackingSpeedBonusPct; }
    if (gdM) { result.ewarGdRangeM = gdM.rangeM; result.ewarGdFalloffM = gdM.falloffM; result.ewarGdMissileVelocityBonusPct = gdM.missileVelocityBonusPct; result.ewarGdFlightTimeBonusPct = gdM.flightTimeBonusPct; result.ewarGdExplosionVelocityBonusPct = gdM.explosionVelocityBonusPct; result.ewarGdExplosionRadiusBonusPct = gdM.explosionRadiusBonusPct; }
    // Energy neut/nos (backlog overnight follow-up, 2026-10-12) -- same
    // byKind flattening convention as the EWAR kinds just above.
    if (neutM) { result.ewarNeutRangeM = neutM.rangeM; result.ewarNeutFalloffM = neutM.falloffM; result.ewarNeutCapPerCycle = neutM.capPerCycle; result.ewarNeutCapPerSec = neutM.capPerSec; }
    if (nosM) { result.ewarNosRangeM = nosM.rangeM; result.ewarNosFalloffM = nosM.falloffM; result.ewarNosCapPerCycle = nosM.capPerCycle; result.ewarNosCapPerSec = nosM.capPerSec; }
  }
  // Misc fit-trait flags ("EWAR / Misc" rename, 2026-10-12) -- same
  // flattening reason/convention as ewarModules just above. hasCynoFitted
  // is ALWAYS set (0 or 1) so a fit can assert ABSENCE too (catches a
  // false-positive MISC_TRAIT_GROUP_INFO group-name collision regressing
  // on a fit that should show zero, same reasoning as hasEwar).
  if (result && result.miscTraits) {
    result.miscTraitCount = result.miscTraits.reduce((sum, m) => sum + m.qty, 0);
    result.hasCynoFitted = result.miscTraits.some(m => m.name.toLowerCase().includes('cynosural')) ? 1 : 0;
    // MJD/MJFG/Interdiction Nullifier misc flags (architecture backlog,
    // 2026-10-12 -- the owner: "Micro Jump Drives and interdiction nullifiers
    // can be flagged in the Misc category") -- same hasCynoFitted
    // convention (always 0/1, so absence is assertable too). The note-text
    // fields pin the EXACT resolved string, which is what actually exercises
    // the new logic for MJD/MJFG: their note is a function(dogma) that reads
    // the fitted item's own real attr973/attr73/attr2066/attr2067 live
    // (varies by variant, e.g. the Xarasier MJD's 120% vs the mainline
    // 150% -- see the MISC_TRAIT_GROUP_INFO comment in index.html), not a
    // hardcoded string like cyno's -- a wrong attrVal read or a broken
    // function-vs-string resolution at the push site would silently change
    // this string without tripping any other assertion.
    const mjdTrait = result.miscTraits.find(m => m.name.toLowerCase().includes('micro jump drive'));
    result.hasMjdFitted = mjdTrait ? 1 : 0;
    if (mjdTrait) result.mjdNoteText = mjdTrait.note;
    const mjfgTrait = result.miscTraits.find(m => m.name.toLowerCase().includes('micro jump field generator'));
    result.hasMjfgFitted = mjfgTrait ? 1 : 0;
    if (mjfgTrait) result.mjfgNoteText = mjfgTrait.note;
    const intNullTrait = result.miscTraits.find(m => m.name.toLowerCase().includes('interdiction nullifier'));
    result.hasInterdictionNullifierFitted = intNullTrait ? 1 : 0;
    if (intNullTrait) result.interdictionNullifierNoteText = intNullTrait.note;
    // PANIC (bug list #2, v2026.10.14.9): flag keyed by effect 6719, note
    // wording depends on the module's state (emergency button vs RUNNING).
    const panicTrait = result.miscTraits.find(m => m.name === 'Pulse Activated Nexus Invulnerability Core');
    result.hasPanicFitted = panicTrait ? 1 : 0;
    if (panicTrait) result.panicNoteText = panicTrait.note;
  }
  // Tank Type classification -- NEVER flattened/asserted before now (the
  // TANK_TYPE_THRESHOLD lowering 60%->55%, 2026-10-12, is the first change
  // to this mechanism that needed a pinned assertion). result.tankType is
  // a {type, shieldPct, armorPct, hullPct} object, same "can't go through
  // the generic exact/range checker directly" reason as ewarModules/
  // miscTraits above. tankTypeKind is a string ('shield'/'armor'/'hull'/
  // 'mixed') -- closeEnough() above already handles string fields via
  // exact equality (added for the missile-ammo-name fields, 2026-10-11).
  if (result && result.tankType) {
    result.tankTypeKind = result.tankType.type;
    result.shieldSharePct = result.tankType.shieldPct;
    result.armorSharePct = result.tankType.armorPct;
    result.hullSharePct = result.tankType.hullPct;
  }
  // Weapon Range/Falloff (F3 feature, 2026-10-10) had NO regression coverage
  // at all until the P1-C Sharpshooter/Trajectory Analysis skill fix
  // (2026-10-11) needed to pin exact optimalM/falloffM numbers. Widened for
  // P1-D (Missile Projection/Bombardment, same day) to flatten by KIND
  // (first turret-kind entry, first missile-kind entry) rather than just
  // "first entry overall" -- a mixed turret+missile fit (e.g. hawk_user:
  // AutoCannon + Rocket Launcher both fitted) would otherwise only ever
  // expose whichever weapon's flag happens to be enumerated first, silently
  // hiding the other kind's numbers from any assertion.
  if (result && result.rangeEstimates && result.rangeEstimates.length > 0) {
    const rTurret = result.rangeEstimates.find(r => r.kind === 'turret');
    const rMissile = result.rangeEstimates.find(r => r.kind === 'missile');
    if (rTurret) { result.rangeOptimalM = rTurret.optimalM; result.rangeFalloffM = rTurret.falloffM; }
    if (rMissile) { result.rangeTravelDistanceM = rMissile.travelDistanceM; result.rangeTravelLowerM = rMissile.travelLowerM; result.rangeTravelHigherM = rMissile.travelHigherM; result.rangeTravelHigherChancePct = rMissile.travelHigherChancePct; } // v2026.10.14.7: pyfa's two whole-second outcomes (missile-range core)
  }
  // Sensor strength (F3) -- never flattened/asserted before now; added
  // 2026-10-11 when the Loki sensor-strength "open gap" (pyfa 20.4 vs. this
  // tool's 17) was re-investigated and resolved as "different Core
  // subsystem fitted, not a bug" (see the SCAN_STRENGTH_ATTRS comment in
  // dscan-tool.html). Pinning the confirmed-correct value here so a future
  // change can't silently regress it with no test ever having covered this
  // card at all.
  if (result && result.sensorStrength) {
    result.sensorStrengthValue = result.sensorStrength.value;
    result.sensorStrengthType = result.sensorStrength.type;
  }
  // Missile damage-application-efficiency (missile-side only; backlog item
  // scoped this way per explicit user direction 2026-10-11, turret-side
  // deferred). T2 tiers + applied-DPS metric correction 2026-10-12 (the owner's
  // own fix: ranking by application % alone conflates "lands more often"
  // with "deals more damage" -- a tighter-explosion ammo like Precision
  // trades damage for application, so the ranking is now by appliedDps
  // by default, see MISSILE_REC_METRIC in dscan-tool.html for the revert
  // switch). Field renamed label->name (now carries the tier, e.g.
  // "Precision Light Missile", not just the class) -- same flattening
  // reason as rangeEstimates/sensorStrength above: result.missileApplication
  // .cruising/.boosted are arrays ranked best-to-worst, so a golden fit
  // can't assert on the array directly -- flatten the top entry of each
  // state (name/applicationPct/appliedDps), plus the recommended damage-
  // type ammo name (pre-existing weighted-resist "weakest" logic, not new
  // to this fix).
  if (result && result.missileApplication) {
    result.missileAmmoName = result.missileApplication.ammoName;
    if (result.missileApplication.cruising && result.missileApplication.cruising.length > 0) {
      result.missileBestCruising = result.missileApplication.cruising[0].name;
      result.missileBestCruisingPct = result.missileApplication.cruising[0].applicationPct;
      result.missileBestCruisingAppliedDps = result.missileApplication.cruising[0].appliedDps;
    }
    if (result.missileApplication.boosted && result.missileApplication.boosted.length > 0) {
      result.missileBestBoosted = result.missileApplication.boosted[0].name;
      result.missileBestBoostedPct = result.missileApplication.boosted[0].applicationPct;
      result.missileBestBoostedAppliedDps = result.missileApplication.boosted[0].appliedDps;
    }
  }
  // Turret "No answer" tiles fall back to the 2nd-weakest damage type
  // (backlog item, 2026-10-12, the owner: "utilize the next weakest resist type
  // to pick an ammo type ... flagging that it cannot take advantage of the
  // primary weakness"). turretRecs.{laser,hybrid,projectile} was already
  // part of the result object before this fix but NEVER flattened/asserted
  // (same situation sensorStrength was in before 2026-10-11) -- a golden
  // fit can't assert on a nested object/null directly. turretXName is the
  // literal string '(no answer)' rather than null so closeEnough()'s
  // string-exact-match branch (see its own comment above) engages cleanly
  // either way, same reasoning as the missile fields being strings.
  // turretXFallback is 1 only when that system's answer came from the
  // fit's SECOND-weakest damage type rather than a direct hit on its real
  // weakest -- see buildTurretRecs() in dscan-tool.html.
  // v2026.10.14.34 damage application (PYFA CORE application, turret-application-plan.md Phase 1): every
  // weapon's inputs as "app:<weapon>:<charge or ->:<field>" (missileMaxRangeData as lower / higher /
  // higherChance), and applied DPS at the points a fit pins as "applied@distance=...,tgtSpeed=...,..." (unset
  // parameters: 0, sig 40 m, target radius 50 m, lock range ignored = pyfa's graph defaults; lock=1 respects it).
  if (result && result.application) {
    for (const w of result.application.weapons) {
      const base = `app:${w.name}:${w.ammoName || '-'}:`;
      for (const [f, v] of Object.entries(w)) if (typeof v === 'number') result[base + f] = v;
      if (w.missileMaxRangeData) ['lower', 'higher', 'higherChance'].forEach((f, i) => { result[base + f] = w.missileMaxRangeData[i]; });
    }
    result.appLockRange = result.application.lockRange;
    for (const key of Object.keys(fit.expected || {})) {
      if (!key.startsWith('applied@')) continue;
      const q = {distance: 0, atkSpeed: 0, atkAngle: 0, tgtSpeed: 0, tgtAngle: 0, tgtSigRadius: 40, tgtRadius: 50, ignoreLockRange: true};
      for (const kv of key.slice(8).split(',')) {
        const [k, v] = kv.split('=');
        if (k === 'lock') q.ignoreLockRange = v !== '1'; else q[k] = Number(v);
      }
      result[key] = sandbox.pyfaAppliedDps(result.application, q);
    }
  }
  // v2026.10.14.35 projected inputs: "proj:<list>:<i>:<field>" (each list sorted by boost, optimal), counts, scram range
  // (-1 = none), drone control range; the fit as a target: "projTarget:*" (top speed and signature radius, the same
  // with its scrammed modules ignored, web / painter resistance, disallowOffensive).
  if (result && result.application && result.application.projected) {
    const pr = result.application.projected;
    result['proj:scramRange'] = pr.scramRange === null ? -1 : pr.scramRange;
    result['proj:droneControlRange'] = pr.droneControlRange;
    for (const name of ['webMods', 'tpMods', 'webDrones', 'tpDrones', 'webFighters']) {
      const list = pr[name].slice().sort((a, b) => (a.boost - b.boost) || (a.optimal - b.optimal));
      result[`proj:${name}`] = list.length;
      list.forEach((x, i) => { for (const f of ['boost', 'optimal', 'falloff', 'resAttrID', 'speed', 'radius']) if (typeof x[f] === 'number') result[`proj:${name}:${i}:${f}`] = x[f]; });
    }
    projApps[fitId] = JSON.parse(JSON.stringify(result.application));
  }
  if (result && result.projectedTarget) {
    const t = result.projectedTarget;
    result['projTarget:maxVelocity'] = sandbox.pyfaTargetValue(t, 'maxVelocity', null, false);
    result['projTarget:signatureRadius'] = sandbox.pyfaTargetValue(t, 'signatureRadius', null, false);
    result['projTarget:scrammedMaxVelocity'] = sandbox.pyfaTargetValue(t, 'maxVelocity', null, true);
    result['projTarget:scrammedSignatureRadius'] = sandbox.pyfaTargetValue(t, 'signatureRadius', null, true);
    result['projTarget:webResistance'] = t.resist[2115];
    result['projTarget:painterResistance'] = t.resist[2114];
    result['projTarget:disallowOffensive'] = t.disallowOffensiveModifiers ? 1 : 0;
    projTargets[fitId] = JSON.parse(JSON.stringify(t));
  }
  lastSandbox = sandbox;
  for (const key of Object.keys(fit.expected || {})) if (PROJ_PIN.test(key)) projPins.push([fitId, key, fit.expected[key], (fit.expected.tolerancePct || 1) / 100]);
  if (result && result.turretRecs) {
    for (const sys of ['Laser', 'Hybrid', 'Projectile']) {
      const rec = result.turretRecs[sys.toLowerCase()];
      result[`turret${sys}Name`] = rec ? rec.name : '(no answer)';
      result[`turret${sys}Fallback`] = (rec && rec.fallbackTo) ? 1 : 0;
    }
  }

  console.log(`\n=== ${fitId} — ${fit.label || ''} ===`);
  if (error) {
    console.log(`  FAIL: threw ${error.message}`);
    anyFail = true;
    continue;
  }

  const exp = fit.expected || {};
  const checks = [];
  const tol = (exp.tolerancePct || 1) / 100;
  // 2026-10-14 (LESSONS #6): every FITTED item (and drone/fighter) needs its
  // type record AND its group record in the fixture. A missing group made the
  // engine drop ishtar_zkb137694046's X-Large Shield Booster silently for months
  // (cap pinned 96.9% while the real page and pyfa both give 40.5%). Cargo and
  // fleet hangar are exempt: missing cargo records only hide unused cargo.
  for (const [slotGroup, items] of Object.entries(tally || {})) {
    if (slotGroup === 'Cargo' || slotGroup === 'Fleet hangar') continue;
    for (const id of Object.keys(items)) {
      const t = TYPES[id];
      const why = !t ? 'no type record' : (!GROUPS[String(t.group_id)] ? `no group record ${t.group_id}` : null);
      if (why) checks.push([`fixture: ${slotGroup} ${t ? t.name : id} (${why})`, undefined, undefined, false]);
    }
  }
  // Latent bug fixed 2026-10-11: this was `expected * tol` (unsigned), which
  // is always FALSE for a negative `expected` (e.g. a debuff percentage
  // like -23.63625) since a non-negative absolute difference can never be
  // <= a negative number -- every exact-match assertion on a negative
  // value was silently unpassable before this fix. Tolerance is a
  // magnitude, so it must be computed off |expected| regardless of sign.
  // Missile damage-application-efficiency fix (2026-10-11) is the first
  // flattened field that's ever a STRING (missileBestClassCruising/
  // missileAmmoName, e.g. "Rocket"/"Mjolnir") rather than a number --
  // numeric closeEnough() on a string produces NaN arithmetic, which is
  // always falsy, so every string assertion would silently FAIL. Exact
  // string equality when either side is a string; numeric tolerance
  // comparison unchanged otherwise.
  const closeEnough = (actual, expected) => {
    if (typeof expected === 'string' || typeof actual === 'string') return actual === expected;
    return Math.abs(actual - expected) <= Math.abs(expected) * tol;
  };

  // Exact-match fields (within tolerancePct): any key in `expected` that
  // isn't a reserved word and doesn't end in _min/_max is treated as an
  // exact expected value for the same-named field on the result.
  const reserved = new Set(['note', 'tolerancePct']);
  for (const key of Object.keys(exp)) {
    if (reserved.has(key) || key.endsWith('_min') || key.endsWith('_max')) continue;
    if (PROJ_PIN.test(key)) continue;   // cross-fit pins: checked after every fit (below)
    if (key.endsWith('_approx')) continue; // informational only (legion_owner's old resist notes), never checked
    // v2026.10.13.27: a pinned field missing from the result FAILS. It used to
    // be skipped silently, so a renamed/removed field (e.g. the old
    // capacitorCombinedConfidentNetRate) would have turned its pins into no-ops.
    if (result[key] === undefined) { checks.push([key + ' (not in result)', undefined, exp[key], false]); continue; }
    checks.push([key, result[key], exp[key], closeEnough(result[key], exp[key])]);
  }
  // Range fields: <field>_min / <field>_max, either or both.
  const fields = new Set();
  for (const key of Object.keys(exp)) {
    if (key.endsWith('_min')) fields.add(key.slice(0, -4));
    if (key.endsWith('_max')) fields.add(key.slice(0, -4));
  }
  for (const field of fields) {
    if (result[field] === undefined) { checks.push([field + ' (not in result)', undefined, undefined, false]); continue; }
    const min = exp[field + '_min'], max = exp[field + '_max'];
    let pass = true, label = field;
    if (min !== undefined) { pass = pass && result[field] >= min; label += ` >= ${min}`; }
    if (max !== undefined) { pass = pass && result[field] <= max; label += (min !== undefined ? ' && ' : '') + `<= ${max}`; }
    checks.push([label, result[field], undefined, pass]);
  }

  for (const [name, actual, expected, pass] of checks) {
    console.log(`  ${pass ? 'PASS' : 'FAIL'}  ${name}: got ${actual}${expected !== undefined ? `, expected ${expected}` : ''}`);
    if (!pass) anyFail = true;
  }
}

// v2026.10.14.35: cross-fit projected pins (an attacker's webs / painters / scram on another golden fit)
if (projPins.length) {
  console.log('\n=== cross-fit projected pins (PYFA CORE projected: attacker -> target) ===');
  for (const [fitId, key, expected, tol] of projPins) {
    const [kind, rest] = key.split('@');
    const parts = rest.split(','), tgtId = parts[0];
    const p = {distance: 0, speedFrac: 1, ignoreLockRange: true, ignoreDCR: false, droneMode: 1};
    for (const kv of parts.slice(1)) {
      const [k, v] = kv.split('=');
      if (k === 'lock') p.ignoreLockRange = v !== '1'; else if (k === 'dcr') p.ignoreDCR = v === '1';
      else if (k === 'drones') p.droneMode = Number(v); else if (k === 'speed') p.speedFrac = Number(v); else p[k] = Number(v);
    }
    let actual;
    if (projApps[fitId] && projTargets[tgtId] && lastSandbox) {
      const t = projTargets[tgtId];
      const r = lastSandbox.pyfaProjectedPoint(projApps[fitId], t, {distance: p.distance, tgtSpeed: p.speedFrac * lastSandbox.pyfaTargetValue(t, 'maxVelocity', null, false),
        ignoreLockRange: p.ignoreLockRange, ignoreDCR: p.ignoreDCR, droneMode: p.droneMode});
      actual = kind === 'tackled' ? r.tgtSpeed : r.tgtSigRadius;
    }
    const pass = actual !== undefined && Math.abs(actual - expected) <= Math.abs(expected) * tol;
    console.log(`  ${pass ? 'PASS' : 'FAIL'}  ${fitId} ${key}: got ${actual}, expected ${expected}`);
    if (!pass) anyFail = true;
  }
}
console.log(anyFail ? '\n*** REGRESSION SUITE: FAIL — do not deliver this file until understood/fixed ***' : '\nREGRESSION SUITE: ALL PASS');
process.exit(anyFail ? 1 : 0);
