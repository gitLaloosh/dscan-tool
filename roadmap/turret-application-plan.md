# Plan: how much of their damage actually lands (turret application)

Status: **PHASE 1 DONE** (v2026.10.14.34, 2026-10-23; `dscan-tool-history/2026-10-23_damage-application-engine.html`).
**PHASE 2a DONE** (v2026.10.14.35, 2026-10-23; `dscan-tool-history/2026-10-23_projected-webs-painters-scram.html`).
All six decisions in section 4 made. the owner 2026-10-23: Phase 2 split into 2a (pyfa's `applyProjected`, engine only)
and 2b (the "Their damage on you" chart with sliders). Next: Phase 2b.
Backlog: "Turret damage application" (DEVIATIONS.md: "turret tracking application"; architecture memory:
"turret-side damage application, needs attacker tracking + assumed range").

---

## 1. Problem

The Firepower card shows a target's raw DPS, and its turrets' optimal and falloff. It doesn't show how much
of that DPS reaches a smaller or faster ship, or one fighting outside their optimal. For the tool's purpose
("how do I beat this ship?") that is often the deciding question:

- Can I get under their guns? (Close orbit, high transversal: big turrets miss.)
- Can I kite them? (Outside optimal + falloff, their hit chance collapses.)
- Will my sig tank their guns? (A frigate against Large turrets.)

Missiles already account for application. Since v2026.10.14.27 the missile pick uses the target's
signature and speed with All V skills. Turrets and drones don't.

## 2. How pyfa does it (primary source: pyfa v2.69.3)

pyfa doesn't put one "applied DPS" number on a fit. Application lives in its **Damage graph**
(`graphs/data/fitDamageStats/calc/application.py`). The user sets the distance, the target's speed, sig
and angle, and the attacker's speed and angle. The default target is the "ideal target": no signature limit,
not moving.

The formulas, per weapon (`getApplicationPerKey`):

| Weapon | pyfa function | Inputs |
|---|---|---|
| Turrets | `_calcTurretChanceToHit` x `_calcTurretMult` | range factor `0.5 ** ((max(0, d - optimal) / falloff) ** 2)` (`eos/calc.py calculateRangeFactor`); tracking factor `0.5 ** ((angular x optimalSigRadius / (trackingSpeed x tgtSig)) ** 2)`; angular = transversal / (atkRadius + d + tgtRadius); damage multiplier with 1% wrecking hits (x3) and a (0.01 + cth) / 2 + 0.49 average |
| Missiles | `getLauncherMult` | full damage inside the shorter flight distance, pyfa's chance between the two flight distances, 0 beyond; then `min(1, S/E, (S/E x Ve/Vt) ** drf)` (the tool already has this) |
| Vorton | `getVortonMult` | range factor x the missile factor |
| Smartbombs | `getSmartbombMult` | inside the blast radius or not |
| Drones | `getDroneMult` | out of drone control range or lock range = 0. If the drone is faster than the target, it is assumed to always hit (pyfa's "auto" mode). Otherwise turret maths from the drone's own tracking, optimal, falloff and speed |
| Fighters | `getFighterAbilityMult` | per ability |

Everything beyond the attacker's **lock range** is 0, except FoF missiles and bombs.

What the tool already has: turret optimal and falloff (generated weapon-range table), missile application,
ship radius (attr 162), lock range, drone control range.

What's missing:

- **Turret tracking speed.** pyfa has 78 handlers on `trackingSpeed`. They're carried by ammo (184 charges,
  e.g. Scorch, Barrage), tracking computers and enhancers with scripts, 81 hulls, implants and boosters,
  T3 subsystems and the Motion Prediction skill. The handler recorder and `gen_weapon_range_table.py`
  already capture exactly this shape of row (optimal and falloff), so tracking would be one more target.
- `optimalSigRadius` (attr 620). No handler modifies it, so it's read as is.
- **Drone speed, tracking, optimal and falloff** after skills and modules. Today the drone pick uses fixed
  travel speeds per drone size.

## 3. Proposed behaviour

### Engine (Phase 1, no visible change)

- Generate turret tracking from pyfa's handlers: the same generator, rows, verification and PYFA CORE lock as
  weapon range.
- A new PYFA CORE section `application`: a line-for-line port of the functions above. It's verified by
  lifting pyfa's own functions unmodified (via `ast`, as `check_missile_range.py` does) and comparing every
  golden fit over a grid of distance x target speed x sig x angle.
- Result field per weapon: `application(profile, distance)`. Applied DPS = sum of each weapon's DPS x its
  multiplier, the same way pyfa sums them.

### Display (Phase 2)

On the Firepower card, under the raw DPS: **"Their damage on you"**. A small DPS-vs-distance chart from 0
to their reach, with two lines (see D3), plus one headline number at the distance you pick. It has hover,
like pyfa's graph.

**Sliders** (the owner, 2026-10-23: "would those calculations allow us to create our own graphing with sliders we
can use to adjust things like engagement range, speeds, etc.?" -> "yes please"). The chart opens on the two
D3 lines; sliders under it change the assumptions and the chart redraws while you drag:

- engagement range (where the headline number is read);
- your speed and heading (still / straight at them / orbiting), their speed and heading;
- your signature radius (e.g. a Target Painter or MWD bloom), prop module on or off;
- what the horizontal axis shows: distance, your speed or your sig (pyfa offers the same choice).

Your sig, speed and radius start at My Ship's numbers (D2). A reset button returns to them and the two
default lines. Moving a slider never re-runs the fit engine: the weapon and ship stats are computed once,
and each chart point is a few lines of the ported application maths per weapon (a full redraw of a few
hundred points is well under a millisecond). Only a fit change (a module state, the prop toggle) recomputes,
as today. On a phone the sliders sit in a collapsible panel under the chart.

### Optional (Phase 3)

The reverse direction, **your guns vs them**: turret ammo picks that account for range and tracking, like
the missile pick does today. This is also the groundwork for the "counter-fit" roadmap idea (time to kill =
your applied DPS vs their tank, and theirs vs yours).

## 4. Decisions needed (the owner)

| # | Question | Options | Recommendation |
|---|---|---|---|
| D1 | Which direction first? | (a) **their guns vs you** (threat); (b) your guns vs them; (c) both together | **Decided 2026-10-23: (a)**, their guns vs you first; (b) later as Phase 3. Why: (a) answers the threat question with nothing assumed about your weapons. |
| D2 | Where do "your" sig, speed and radius come from? | (a) **a fit you've analyzed, saved as "my ship"** (one click in the Fit Analyzer, remembered in your browser); (b) class presets (frigate / cruiser / battleship); (c) typed in by hand | **Decided 2026-10-23: (a)**, My Ship (built in v2026.10.14.33), with (b) class presets until a ship is saved. Why: the numbers come from the tool's own pyfa-exact stats, MWD or AB included. |
| D3 | What movement do we assume? | (a) two lines: you sitting still and you orbiting at full speed (90°, the worst case for them); (b) orbiting only; (c) a speed slider | **Decided 2026-10-23: (a) as the default view, plus sliders** for range, both ships' speed and heading, your sig, prop on/off and the horizontal axis (section 3, Display). Still = their range-only damage, orbiting = with tracking; the gap between the lines is what speed tanking buys you. |
| D4 | Prop module for "you" | (a) **your fit's prop active** (AB or MWD, with the MWD's sig bloom); (b) cruising | **Decided 2026-10-23: (a)**, your fit's prop active, MWD sig bloom included (a slider can switch it off). Why: Real orbits run the prop, and the MWD's sig bloom is exactly the trade-off the chart should show. |
| D5 | Their drones and fighters | (a) **include now** (needs drone speed and tracking: more engine work); (b) turrets, missiles, Vorton and smartbombs first, drones in a follow-up | **Decided 2026-10-23: (b)**, turrets, missiles, Vorton and smartbombs first; drones and fighters in a follow-up, raw drone DPS labelled as raw until then. |
| D6 | Pilot Analyzer as well as Fit Analyzer? | (a) **both**; (b) Fit Analyzer only | **Decided 2026-10-23: (a)**, both the Pilot and Fit Analyzers. Why: Same engine; killmail fits get the same card. |

## 5. Risks and how they're handled

- **Assumptions in the numbers.** Application depends on inputs nobody can know (your exact movement). The
  card names its assumptions on the chart: profile, still or orbiting, prop on. Raw DPS stays visible.
- **Lock range.** Beyond their lock range pyfa counts 0. The chart shows it as a cliff, with the reason on
  hover.
- **Sig from a saved fit goes stale** if you change that fit later. The profile stores the numbers and the
  fit name, and the card says which fit it used.

## 6. Verification plan (`LESSONS_LEARNED.md` order)

1. Recorder survey of every `trackingSpeed` handler. The generated table must reproduce the handler set
   exactly (`gen_weapon_range_table.py` reports "up to date").
2. `tools/independent_checks/check_application.py`: pyfa's own application functions, lifted unmodified,
   vs the tool, over every golden fit x a grid (distance 0 to 2x reach, target speed 0 to 3,000 m/s, sig
   20 to 5,000 m, angle 0 / 45 / 90°). Must print 0 mismatches. It goes in the update-check chain.
3. `compare_fit_stats.py` gains tracking speed per turret, compared with the oracle at 1e-6.
4. Constructed golden fits that fail on the old build:
   - a Megathron with 425mm Rails vs a frigate profile at 5 / 20 / 40 km;
   - a Rifter with autocannons and a Tracking Enhancer + Barrage;
   - a lock-range cliff case.
5. A pyfa screenshot check from you: the Damage graph for one test fit with a set target profile. We read
   two points off it.
6. Page checks: the chart at 1440 / 375 px, profile save and reload, no sideways scroll; every slider redraws
   the chart and its headline number equals `check_application.py`'s value for that input; reset returns to
   My Ship's numbers; dragging doesn't re-run the fit engine.

## 7. Rough size

| Phase | Size |
|---|---|
| 1 — tracking table + application core + checks | Medium to large (one or two deliveries) |
| 2 — "Their damage on you" chart + sliders (My Ship profile already built, v2026.10.14.33) | Medium |
| 3 — your guns vs them (optional) | Medium |
| Drones / fighters follow-up (if D5 = b) | Medium |

## Phase 1 as built (v2026.10.14.34)

- `WEAPON_RANGE_MOD_EFFECTS` (generator `gen_weapon_range_table.py`) gained the targets `tracking`,
  `missileExplosionRadius`, `missileExplosionVelocity`, `vortonExplosionRadius`, `vortonExplosionVelocity`
  (234 effects, 249 rows); skills as All V constants (Motion Prediction x1.25, Vorton Arc Guidance, the existing
  Guided Missile Precision / Target Navigation Prediction); the ammo's own tracking multiplier (Effect600) and an
  Advanced Condenser Pack's explosion velocity (Effect8062); Tracking Speed and Missile Precision scripts.
- `estimate.application` = {radius, lockRange, weapons: [{kind turret | missile | vorton | smartbomb, name,
  ammoName, weaponTypeId, ammoTypeId, qty, dps, and pyfa's modified inputs}], unapplied: {droneDps, fighterDps,
  otherFixedDps, cargoGuessWeapons}}.
- PYFA CORE `application`: `pyfaApplicationMult(w, p)` and `pyfaAppliedDps(app, p)`, p = {distance, atkSpeed,
  atkAngle, tgtSpeed, tgtAngle, tgtSigRadius, tgtRadius, ignoreLockRange}; pyfa's graph defaults (lock range
  ignored, resists ignored).
- Checks: `check_application.py` (pyfa's getApplicationPerKey unmodified, 6,000-point grid, 0 mismatches),
  `compare_fit_stats.py` (inputs vs pyfa's handlers, 0 mismatches), 4 constructed golden fits + smartbomb pins.

**Found while building, for Phase 2:** pyfa's damage graph has `applyProjected` ON by default: the attacker's own
webs and target painters slow the target and grow its signature before application (`calc/projected.py`
getTackledSpeed / getSigRadiusMult, recomputing the TARGET fit's speed and signature with those multipliers,
its scrammed MWD off). For "their damage on you" that is your speed and signature under their tackle, from My
Ship's fit. Phase 2 has to port it (or show it as a separate line) to match pyfa's default graph.
the owner 2026-10-23 ("yes please"): port it first, as Phase 2a, before the chart.

## Phase 2a as built (v2026.10.14.35)

- PYFA CORE `projected`: `pyfaGetTackledSpeed`, `pyfaGetSigRadiusMult`, `pyfaTargetValue` (getMaxVelocity /
  getSigRadius with getExtended), `pyfaCalculateMultiplier` (target profiles), `pyfaProjectedPoint(app, tgt, p)`
  (tackled speed, then painted signature) and `pyfaAppliedDpsProjected(app, tgt, p)` = what pyfa's default
  graph shows. p = {distance, tgtSpeed (the target's own speed before tackle), ignoreLockRange (default true),
  ignoreDCR (default false), droneMode (1 auto)}.
- Attacker inputs: `estimate.application.projected` = {scramRange, webMods, tpMods, webDrones, tpDrones,
  webFighters (always empty: no support fighters), tpFighters, droneControlRange}; one entry per active copy /
  drone in space, pyfa's modified attributes (EWAR tables for modules, new drone table for drones).
- Target inputs: `estimate.projectedTarget` = {isFit, radius, disallowOffensiveModifiers, resist {2115, 2114},
  maxVelocity / signatureRadius: {base, pool (pyfa's stacking groups), scrammed (what the running MWD, an active
  MJD / MJFG put in)}}. The fit's current state: with its active prop module (D4 decides the default in 2b).
  A target profile for 2b: {isFit: false, maxVelocity, signatureRadius, radius}.
- Checks: `check_projected.py` (pyfa's calc/projected.py and cache/projected.py unmodified, every attacker x every
  golden fit, 156-point grid, 0 mismatches of 932,256 points), 8 constructed golden fits, cross-fit pins in
  `run_regression.mjs` (`tackled@<target>` / `painted@<target>`).
- Found and fixed on the way: a scripted Warp Disrupt Field Generator (high slot) got the bubble's signature bloom
  and none of the script's cycle / capacitor change (LESSON #37).
