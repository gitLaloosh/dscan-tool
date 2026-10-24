# Plan: how much of their damage actually lands (turret application)

Status: **PHASE 1 DONE** (v2026.10.14.34, 2026-10-23; `dscan-tool-history/2026-10-23_damage-application-engine.html`).
**PHASE 2a DONE** (v2026.10.14.35, 2026-10-23; `dscan-tool-history/2026-10-23_projected-webs-painters-scram.html`).
**PHASE 2b DONE** (v2026.10.14.36, 2026-10-23; `dscan-tool-history/2026-10-23_their-damage-on-you-chart.html`).
All six decisions in section 4 made. the owner 2026-10-23: Phase 2 split into 2a (pyfa's `applyProjected`, engine only)
and 2b (the "Their damage on you" chart with sliders). Next: Phase 3 (your guns vs them, optional) or the drones /
fighters follow-up (D5; drones done v2026.10.14.40, `dscan-tool-history/2026-10-23_drone-damage-application.html`); My Ship
phase 2 (matchup strip) can now read the chart's headline.
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
| D5 | Their drones and fighters | (a) **include now** (needs drone speed and tracking: more engine work); (b) turrets, missiles, Vorton and smartbombs first, drones in a follow-up | **Decided 2026-10-23: (b)**, turrets, missiles, Vorton and smartbombs first; drones and fighters in a follow-up, raw drone DPS labelled as raw until then. **Drones DONE v2026.10.14.40** (the owner, for My Ship phase 2: "port drone application first"): getDroneMult in PYFA CORE application. Fighters still open. |
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

## Phase 2b decisions (2026-10-23, after the mockup)

Mockup canvas "Their damage on you — chart mockup" (Megathron vs Caracal from the golden fits; its interactive
prototype runs the engine's maths, checked against the engine on 864 points).

- **Layout: Option B** ([stated] "let's go with B"): its own full-width card under the three columns, chart left,
  sliders right; the Firepower card keeps a one-line link ("785 on you at 10 km"). On a phone the sliders fold
  into an "Adjust" panel.
- **Signature slider: scales your fit's own signature** ([stated] "scaling is fine"), so the MWD bloom and the
  scram rule still apply.
- **Default engagement range: their optimal + falloff** ([stated]). For a fit whose biggest raw DPS isn't turrets,
  the same idea per weapon: missiles their flight range (pyfa Module.maxRange), Vorton maxRange, smartbombs the
  blast radius (my reading; the weapon group with the most raw DPS decides).
- **Class presets until a ship is saved** ([stated] "yes" to the criteria, "keep it" to the Navitas): treated as
  FITS, not target profiles, so their scram switches the preset's MWD off as it would yours. Rule: published T1
  hulls of the four empire races (covert exploration frigates left out), each with its class's T2 MWD active and
  nothing else, pyfa's handlers at All V; the real hull nearest the class median of MWD speed and MWD signature
  (log distance). Picks (pyfa v2.69.3, data 3624425):

  | Class | Pick | MWD speed | MWD signature | Radius | MWD off |
  |---|---|---|---|---|---|
  | Frigate (20 hulls) | Navitas + 5MN Microwarpdrive II | 3,026 m/s | 207 m | 35 m | 512 m/s, 36 m |
  | Destroyer (8) | Cormorant + 5MN Microwarpdrive II | 1,671 m/s | 374 m | 112 m | 312 m/s, 65 m |
  | Cruiser (16) | Caracal + 50MN Microwarpdrive II | 1,913 m/s | 719 m | 202 m | 288 m/s, 125 m |
  | Battlecruiser (8) | Harbinger + 50MN Microwarpdrive II | 1,239 m/s | 1,552 m | 199 m | 219 m/s, 270 m |
  | Battleship (12) | Raven + 500MN Microwarpdrive II | 1,046 m/s | 2,358 m | 250 m | 141 m/s, 410 m |

  The selection is a script (re-run after a game-data update; a pick can change only when CCP rebalances hulls).

## Phase 2b as built (v2026.10.14.36)

- The card ("Their damage on you", collapsible key `dmg`, closed by default on a phone) is in the Fit Analyzer
  and in every Pilot losses tab; not in the "My ship" view. v.36 put it under the `.fit-layout` grid (LESSON #38);
  since v2026.10.14.37 (the owner: "place the new card ... at the top", option B) it is a band at the top of the grid,
  across the Fit and stats columns from 1280 px, full width below that (`FIT_LAYOUT`, roadmap/card-layout-plan.md).
  Its inner layout follows its own width (container query, 720 px). The Firepower card gets the one-line link (`.dmg-fp-slot`).
- Target: My Ship when saved and "Use in assessments" is on, else the class preset (stored in
  `localStorage['dscanDmgPreset']`, default cruiser). A preset is built from EFT text (`[Caracal, Typical
  cruiser]` + its MWD) by the same `buildFitFromEft` as a paste; DMG-01 if it can't be.
- Engine input added: `estimate.projectedTarget.variants` = {propTypeId, propKind, running, on, off}: the target
  with its prop module running (the running one, else the fastest of the prop kind the fit has) and with every
  prop module off. The switch picks one; D4 = on.
- Every point: `pyfaProjectedPoint` (their tackle) then `pyfaAppliedDps` at the tackled speed and painted
  signature, both PYFA CORE, unchanged. 121 samples per line; a control redraws the card only (no fit-engine run).
- Lines: "you still" (solid, #c2832e) and "you moving" (dashed, #2f9fb5), validated together. Chart across
  distance (two lines, markers: scram, web, their lock range), your speed or your signature (one line).
  "Show values" table, hover / tap tooltip with your webbed speed and painted signature.
- Checks: `tools/independent_checks/check_damage_chart.py` (pyfa's projected.py + application.py unmodified on
  oracle fits, presets and golden targets, prop on / off, 486-point grid), `tools/select_class_presets.py
  --check`, both in the update-check chain; `tools/page_checks/damage_chart_check.py`.

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

## Open: clearer chart labels (the owner, 2026-10-23, task)

the owner: "have the graph be more clear about some of the labeling (like drone range). the vertical dotted lines on either
side of the text are confusing." His screenshot (the owner, Osprey Navy Issue vs his Legion, distance axis to 80 km) has
two dotted lines near the right edge with one label, "their drone range", printed BETWEEN them.

Cause, from the code (`dmgChartSvg`, marker loop): every marker (scram, web, their lock range, their drone range) is the
same grey dotted line with a label on the top edge. A label goes right of its line, or left of it when it would run
off the chart; a label that would overlap the previous one is DROPPED. There, "their lock range" (~63 km) lost its
label, and "their drone range" (~75 km) was pushed to the left of its own line, so it sits between the two lines.

To do (design first, then build):
- every line keeps a visible label: stack colliding labels on two rows, or label at the line with a short leader,
  never drop one;
- tell the line kinds apart (e.g. tackle lines vs range limits), and say what each limit means in the hover;
- check at the card's narrow widths and on a phone; add the case (two markers close together near the right edge)
  to `tools/page_checks/damage_chart_check.py`.
Also in the same screenshot: the card's "Adjust" column shows only its heading, no sliders -- reproduce and fix with it.

## Fight setup mockup (2026-10-24): tabs, Keep at Range, your damage card, chart markers

the owner asked for these together (2026-10-24): fight settings as tabs under the Matchup ("Orbit", "Approach"; "things that
can tie directly into the damage application card's settings"), a "Keep at range" movement ("if one ship is faster than
the other, and is outside of the target's scram/web range, it's possible for them to maintain a specified distance"),
a Damage Application card in the My Ship Perspective, plus the chart labels above. Mockup: chart canvas page
"Fight setup" (boards 1-5), all numbers from the engine (Hecate threat vs saved Vexor, as in matchup_strip_check.py).

Proposed:
- **Tabs under the Matchup (board 1):** "Hecate: Stopped", "Range: 4.4 km", "You: Orbit · 1,691 m/s"; each opens a
  short menu. Option B (board 2): one strip under the board with a Change button. Option C (board 2b, added at the owner's
  request): one strip joined to the board, three parts under the board's own three columns (threat / middle / my
  ship), each opening the same menu. **DECIDED 2026-10-24: Option C** (the owner: "option C is my preference. i like that
  quite a bit actually."). Phone: the three parts in a row under the board, each opening a sheet (board 3's pattern).
- **DECIDED 2026-10-24 (the owner, after option C):** in-game names for both ships, and one shared fight for both
  perspectives. Chart markers: the owner asked for A and B combined ("the shading really makes it clear when you're inside
  of tackle range"; later maybe "different colors for different types of EWAR"; key uses "the same letter codes
  that you use in the EWAR tab") -> board 5b: EWAR ranges shaded from 0 in the EWAR card's badge colour with its
  badge letter on the line (T tackle #b9812f, D disrupt #1f9ab3, C cap drain #a66bd9, B burst cyan), darker where two
  overlap; ranges that aren't EWAR (drone range, lock range) as numbered pins; one key under the chart. **5b chosen** (the owner: "5b is the one"), **then 5c on top** (board 5c, the owner: "i like it"):
  - the tackle distances are printed in the x axis numbers, in the tackle colour; round ticks that would overlap
    are dropped, and close labels are nudged apart;
  - your engagement range is printed on the x axis, in white;
  - the DPS at that range is printed on the y axis in each line's colour, with a dashed guide to the dot (one white
    label when both lines give the same number).
  - Numbers keep a set width and the chart keeps its frame while values change (subtext-plan.md rule 4).
  All fight-setup decisions are made; build in phases next (subtext-plan.md section 5). **F1 DONE v2026.10.14.51**:
  the strip, in-game names (their new Stopped state is the default) and the shared fight. **F2 DONE v2026.10.14.53**:
  Keep at Range as mapped below, for both ships; the example below is checked on the page (`fight_strip_check.py`).
- **In-game names everywhere:** You and the threat each get Stopped / Approach / Orbit / Keep at Range (today: You
  Still / Straight at them / Orbiting; them They fly at you / They orbit you).
- **One fight for both perspectives:** the Adjust panel edits the same settings on both cards.
- **Your card (board 4):** "DPS applied to them", your scram/web/drone/lock markers, cyan edge.
- **Chart markers (board 5):** A = numbered pins over each line + a key under the chart (recommended; two close
  pins shift sideways, never dropped); B = your/their tackle shaded, ranges as lines + key.

**Keep at Range in pyfa's inputs** (pyfa `_calcAngularSpeed`, graphs/data/fitDamageStats/calc/application.py:396:
transversal = |atkSpeed·sin(atkAngle) − tgtSpeed·sin(tgtAngle)|; missiles and drones read the target's speed):
the ship keeping range moves along the line of sight (angle 180°, adds no transversal) at the speed that holds the
distance = the other ship's closing speed (its speed × cos of its angle), capped at its own top speed. If the other
ship closes faster than that, range can't be held: the option is unavailable with the reason. It is also unavailable
inside the other ship's web/scram range (they're slowed). Example from the engine: Hecate approaching at 1,613 m/s,
Vexor top 1,691 m/s, Keep at Range at 15 km → 0 DPS applied to you (holds), 291 DPS applied to them, they last 26 s.
Note the chart stays a snapshot at one distance (as pyfa's graph): Approach / Keep at Range describe how each ship
moves at that distance, not a fight played out over time.

**"Adjust" with no sliders: reproduced and found.** `dmgFill` opens Adjust only when `host.clientWidth >= 720` at
fill time. A Pilot loss tab that is hidden when the card is drawn has clientWidth 0, so Adjust starts closed; on the
wide layout its summary then reads like an empty column heading. Repro: two loss tabs, open the second at 1440 px.
Fix: decide from the viewport when the card isn't laid out yet, or keep Adjust open on the wide layout regardless.

## DONE v2026.10.14.45: "damage applied" wording (the owner, 2026-10-23, task)

Built as mapped below, with the card names registry (roadmap/card-names.md); the chart labels (section above) are
still open.

the owner first asked to rename "Their damage on you" to "Damage Application"; after the wording boards (canvas
"Their damage on you -- chart mockup", page "Damage application wording") he settled the convention: "changing phrases
like 'Their damage on you' and 'Your damage on them' to 'Damage applied to you' and 'Damage applied to them' ... We're
trying to communicate damage application so let's use the term." Do it with the chart-labels task (same card).

Phrase map (proposed on the boards; the owner may still edit them there):
| Where | Today | New |
|---|---|---|
| Card title (open and collapsed) | Their damage on you | Damage Application (the owner: "we're getting rid of 'Damage applied to you'"; the name comes from roadmap/card-names.md) |
| Tag beside the title | vs your Legion · Jun 18, 2026 | applied to your Legion · Jun 18, 2026 (says whose damage, since the title no longer does) |
| Tag, no ship saved | vs a typical cruiser | applied to a typical cruiser |
| Headline | 230 DPS at 42.2 km, you orbiting ... | 230 DPS applied at 42.2 km, you orbiting ... |
| Collapsed summary | 230 DPS on you at 42.2 km, orbiting ... | 230 DPS applied to you at 42.2 km, orbiting ... |
| Collapsed, before numbers | their applied DPS on your ship, by distance | damage applied to you, by distance |
| Scoreboard labels | DPS on you / DPS on them | DPS applied to you / DPS applied to them |
| Scoreboard and picks notes | as set on "Their damage on you" | as set on "Damage Application" |
| Weaknesses picks | 614 DPS on them / 474 DPS on you | 614 DPS applied to them / 474 DPS applied to you |
| Firepower link | 230 DPS on you at 42.2 km ↑ | 230 DPS applied to you at 42.2 km ↑ |
| DMG-01 title / where | No ship to chart their damage against / "Their damage on you" card | No ship to apply their damage to / "Damage Application" card |
| "Show values" table column, chart's screen-reader label | Their DPS on you | DPS applied to you |
| Firepower link / summary, no ship saved | 230 DPS on a typical cruiser ... | 230 DPS applied to a typical cruiser ... |
A later chart of your weapons on them would be "Damage applied to them". Checks that test the old text
(damage_chart_check, weakness_picks_check, matchup_strip_check docstrings) change with it; history docs keep the old name.
