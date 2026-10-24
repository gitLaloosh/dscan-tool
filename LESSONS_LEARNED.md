# Lessons learned: calculation mistakes and how to avoid them

This file is for any model or person changing a calculation in `index.html`.
Every entry is a mistake that actually happened in this project. Each entry
covers how it showed up, how it was caught, and the method that works.

The goal is to match pyfa (the community fitting tool) exactly. Use primary
sources only: pyfa's source (`eos/effects.py`, `eos/modifiedAttributeDict.py`,
`eos/saveddata/module.py`, `eos/saveddata/fit.py`, `eos/capSim.py`) and CCP's
SDE / live ESI. Tooling for both is in `tools/` (see `tools/README.md`).

**How to use this file**

1. Follow the checklist below **in order**. The order matters:
   - Expected values are derived **before** any code is written. Otherwise you
     tend to derive what your code already does (#3).
   - A new test fit must fail on the current build before you start
     implementing.
2. Each checklist step names the entries it guards against. Read those
   entries when you reach the step.
3. The entries are grouped by the phase where the mistake happens. Their
   numbers are **permanent IDs**: `// LESSON #n` comments in `index.html`
   and the history docs refer to them. Never renumber. A new entry gets the
   next unused number and goes under the phase where it belongs.

---

## Checklist (in this order)

**Phase 1 — Find every source (before writing any code)**

0. Run `tools/pyfa_update_check.py` (pyfa version, data build, full chain with
   `--run`). Decide whether the change belongs inside a `PYFA CORE` section
   (calculation) or outside it (inputs/presentation) — `PYFA_CORE.md`.
   → #10, #23
1. List every pyfa handler that touches the stat by **running** them with
   `tools/pyfa_effects.py`. For a table that already exists, run
   `tools/audit_effect_tables.py`. Never use grep or regex for this.
   Firepower: `tools/audit_firepower.py`. Read every handler error the
   recorder reports (#28).
   → #1, #16, #19, #22, #28
2. For each source, note which **effect** carries it and which **attribute of
   the carrying item** holds the value. Never take a value from memory, trait
   text or a hand-made table. Then read the stat's SDE attribute record
   (max/min attribute, default) and follow the value through pyfa to the code
   that **consumes** it (e.g. `Module.rawCycleTime` → `getCycleParameters()`
   → `capUse` / `Fit.__generateDrain`; for fighters `Fighter.__init__` →
   `getDpsPerEffect`), not just to where it is modified.
   → #2, #4, #8, #11, #18, #20, #24, #26, #29, #31, #32
3. Treat earlier "fully checked, nothing found" claims as unproven until you
   have re-run the search yourself.
   → #5

**Phase 2 — Derive the expected numbers (still before writing code)**

4. Write or extend a script in `tools/independent_checks/`. Use pyfa's rules
   typed by hand and SDE values only. The script alone must produce every
   expected number. When a pyfa piece runs on its own (`eos/capSim.py`),
   import it unmodified as the reference instead of re-deriving it.
   `tools/pyfa_fit_oracle.py` runs pyfa's own handlers on a whole fit; check it
   has no `oracleGaps` for your fits.
   → #3, #27
5. Build a constructed golden fit from full SDE records, through the real EFT
   parser, with slot pairing for charges and scripts, every item in the slot a
   real fit puts it. Run the suite and confirm the fit **fails** on the current
   build. A mutation the check doesn't catch means the grid has a hole: add a
   point where the mutated rule changes the result.
   → #6, #37
6. If you are comparing with a pyfa screenshot:
   - split pyfa's number into its parts first
   - get pyfa's module states
   - check pyfa's game-data version
   
   → #9, #10

**Phase 3 — Implement**

7. Gate on dogma effect IDs and read the value from the item's own
   attribute. Keep group names only as a fallback for records without effects.
   When a count depends on module state, count per **effect**, not per item.
   Round a displayed pyfa stat with `pyRound()` / `kmText()` from its unrounded value.
   → #2, #17, #30, #34
8. Copy `stackingPenalties` and `penaltyGroup` from the recorded handler
   call. Apply one `pyfaPenalizedProduct()` per penalty group.
   → #7, #15
9. When the new effect-driven path replaces an old one, switch the old one to
   fallback-only behind a flag.
   → #14

**Phase 4 — Verify and deliver**

10. Run `node --check`, the regression suite (ALL PASS, parse tests too) and a
    Playwright render of one affected fit. A layout change: also
    `tools/page_checks/layout_check.py` (desktop, tablet and a real phone width).
    New code that runs at page load: the suites load the script with a stub DOM.
    → #12, #33, #36
11. Diff the full output of the old and new builds over every golden fit
    (`diffall`). Explain and pin every change with a note. Re-run any table
    generator or audit script; it must be clean. Renamed or removed a result
    field? Move its pins (the checker fails a missing pinned field).
    → #1, #6, #21
12. A changed PYFA CORE section: run its `verify` commands
    (`tools/pyfa_core_manifest.json`), then `check_pyfa_core.mjs --update`. A new
    difference from pyfa: add it to `DEVIATIONS.md`.
    → #23, #25
13. Bump the version tag. After writing to the user's machine, byte-verify
    every file.
    → #13
14. Record the lesson:
    - Add an entry here if the mistake is a new kind.
    - Add a "Lesson for future models" section to the history doc.
    - Add a `// LESSON #n` comment at the code site.

---

# Phase 1 — Finding the sources

## 1. Finding pyfa handlers with text matching misses some of them

- **What happened:** the capacitor, HP, targeting and repairs batches found
  pyfa handlers by regex over `eos/effects.py`. In the weapon-range batch, the
  same regex approach missed dozens of relevant handlers that running the
  handlers found. Examples:
  - Raven 891 picks `skill` and `penalties` through variables based on `context`.
  - Tracking Computer 4559 runs `for attr in ('maxRange', 'falloff', 'trackingSpeed')`.
  - Myrmidon Navy Issue 11061 loops the same way.
- **How it was caught:** a second search for every handler mentioning range
  attributes that the first pass had NOT matched. It returned dozens.
- **Do this instead:** run the handlers with `tools/pyfa_effects.py`. It calls
  each real handler with a recording fake fit and records:
  - the target attribute
  - the source attribute, including any `* level`
  - the `skill=` scaling
  - `stackingPenalties` and `penaltyGroup`
  
  `filter_hits()` then evaluates the handler's own filter against every real
  SDE item. Template: `tools/gen_weapon_range_table.py`.
- **Audit of the older tables (v2026.10.13.19):** `tools/audit_effect_tables.py`
  ran every handler against the text-matched tables for capacitor, HP,
  sensors, repairs, shield recharge and signature. It found rows the text
  matching had missed:
  - the Triage Module's whole remote-repair half (a FAX in triage drains 4×
    the cap)
  - Valravn / Naglfar Fleet Issue capital rep bonuses
  - the small Remote Hull Repair Systems skill
  - Bastion's +100% sensor strength
  - 14 remote-repair hull bonuses
  
  Re-run the audit after every pyfa/SDE update. Its `KNOWN` list records each
  deliberate exclusion with its reason.
- **Not yet covered by the audit:** speed/agility/mass (still group-gated
  code, not a table), damage/rate of fire (`SHIP_ROLE_BONUS`, hand-made), and
  drones/EWAR.

## 16. Python closures in pyfa handlers (a trap for the recorder itself)

- **What happened:** pyfa builds filter lambdas inside loops:
  `for skill, attr in (...): fit.modules.filteredItemBoost(lambda mod:
  mod.item.requiresSkill(skill), ...)`. The first version of the recorder
  evaluated each lambda **after** the handler returned. By then every lambda
  saw the loop's last `skill`, so Triage's remote-repair rows were attributed
  to the wrong skill.
- **How it was caught:** the audit listed a filter ("Capital Repair Systems"
  on a remote-repair duration row) that didn't match the handler source when
  read by hand.
- **Do this instead:** evaluate filters **at call time**. Pass
  `run(eid, ctx, evaluator)`; the evaluator runs inside the recorded call
  while the loop variables are current (see `tools/pyfa_effects.py`). When a
  tool's output looks odd, read the handler source once to confirm.

## 19. Skill handlers that filter on the skill itself (another recorder trap)

- **What happened (v.21):** some skill handlers filter with
  `requiresSkill(skill)`, where `skill` is the skill running the handler.
  Effect1730 (drone damage per Drone Operation / racial Specialization skill)
  and Effect1851 (launcher RoF per missile Specialization) are examples. The
  recorder's source object isn't a skill name, so `filter_hits()` returned no
  hits at all, with no error. A table built from it would silently miss the
  effect.
- **How it was caught:** checking why no racial Drone Specialization effect
  showed up for the Aralez, which requires two of them.
- **Do this instead:** for skill effects, pass the carrying skill:
  `run(eid, 'skill', evaluator, carrier=skillTypeId)`. Without it the recorder
  now records `('skill?', ...)` instead of failing silently, and
  `audit_effect_tables.py` prints `UNEVALUATED self-skill filter` lines.
  (None of the audited tables were affected: grep shows these handlers only
  touch charge damage, drone damage, launcher RoF and consumption.)

## 2. Gating on group names instead of effects

- **What happened:**
  - Signature radius counted rig sig penalties only for `Rig Shield`, but 16
    `Rig Navigation` rigs (Hyperspatial Velocity Optimizer, Warp Core
    Optimizer) carry the same effect 2716 `drawbackSigRad`. That was the
    Legion's missing +5% sig.
  - Attribute 1138 (`drawback`) is a generic container that different rig
    families route to sig, armor HP, shield HP, agility, CPU or PG.
  - The agility drawback was gated on the whole Rig Armor group, so Auxiliary
    Nano Pumps got an agility penalty they don't have.
- **How it was caught:** comparing with pyfa numbers for real fits, then
  listing every SDE type that carries the effect (it took one query).
- **Do this instead:** gate on the effect ID in the item's `dogma_effects` and
  read the value from the item's own attribute. Keep the group gate only as a
  fallback for records without effects (old trimmed fixtures). Examples:
  `SIG_DRAWBACK_EFFECT_ID`, `weaponRangeViaEffects`.

## 4. Hand-maintained per-hull tables are incomplete

- **What happened:**
  - **Weapon range:** the hand table had range bonuses for 5 hulls. pyfa has
    them on 120+.
  - **MWD signature bloom:** only Interceptors had their bloom reduction. All
    27 Assault Frigates, Heavy Assault Cruisers and Command Destroyers carry a
    flat −50% (effect 4902), so HAC MWD sig showed about 2× real.
  - **Earlier:** 12 hulls wrongly thought to lack role bonuses; missing
    Precursor hulls; resist bonuses on 90 hulls that were absent.
  - **Firepower (`SHIP_ROLE_BONUS`, ~340 hulls), replaced v2026.10.14.3:**
    - the Leviathan, Komodo and Vigil Fleet Issue got both of their
      damage-type bonuses on every type (2-3.5x DPS)
    - the Anhinga got three rate-of-fire bonuses it doesn't have (~3.6x)
    - the Akoman, Thunderchild and Hydra were missing
    - no entry knew weapon size or missile family scope

    The generated `SHIP_DAMAGE_MOD_EFFECTS` replaced it; the hand table is
    now only the fallback for 7 special editions with no SDE effects.
  - **A universal constant is a hand table with one row (v2026.10.14.22):**
    `MAX_MISSILE_DAMAGE_MULT = 1.10 * 1.25` assumed every missile needs one
    skill with the missile damage effects (660/661/662/668, 5%/level). pyfa
    applies every such skill the charge requires, and Auto-Targeting (FoF)
    missiles need their size skill **and** Auto-Targeting Missiles (3322):
    1.25 × 1.25. The Raven FoF test fit showed 45 DPS against pyfa's 56.5.
    Found only when `compare_fit_stats.py` compared every golden fit.
- **Do this instead:** generate hull bonus tables from the hull's
  `dogma_effects` (#1). For a "max skills" constant, list every item it
  covers and check which skills each one actually requires (`requiredSkill1-6`). If a hull record has effects, don't also apply the old
  hand table, or the bonus gets counted twice. See `weaponRangeViaEffects`
  and `hullHasDamageEffects`.

## 11. Assuming a hull bonus from memory or trait text

- **What happened:** wrong magnitudes:
  - Cerberus 25% vs the real 12.5%.
  - The Eagle's HAC skill per-level value.
  - Orca drone bonuses.
  - The Hawk's bonus shape changed in a game patch.
- **Do this instead:** read the hull's own attribute value through its effect
  (#1). Per-level hull bonuses are ×5 at the standing all-V convention.

## 5. "Exhaustively checked, nothing found" was wrong

- **What happened:** two memory notes claimed scan resolution and sensor
  strength had been fully checked. Both missed the Signature Analysis and
  Sensor Compensation skills, which are in the very skill group the notes
  said was covered.
- **Do this instead:** treat "nothing found" as unproven. Re-run the search
  against the data (e.g. every skill in group 1213 × its effects) before
  relying on it.
- **The reverse happens too (v2026.10.14.29):** the backlog said the Zero-Point Mass Entangler's speed and
  mass effects were "not modelled". A constructed Onyx compared with pyfa's handlers showed they had been
  exact since the v2026.10.14.8 speed phase (`SPEED_EFFECTS` 7142). A "not done" note goes stale the same
  way a "nothing found" note does. Test it against pyfa before building anything.

## 8. Excluding an attribute as a "collision"

- **What happened:** an MWD's attribute 147 was excluded as an unrelated
  collision. It's real (`capacitorCapacityMultiply`, effect 58, ×0.8 on a 5MN
  MWD II).
- **Do this instead:** before excluding an attribute on an unexpected item,
  look up which effect on that item consumes it.

## 18. Reading part of a list, or a stand-in for the real rule

- **What happened (fixed v.21):**
  - `REQUIRED_SKILL_ATTRS` held requiredSkill1–3 (attrs 182–184). pyfa's
    `requiresSkill()` uses all direct required skills (SDE
    `requiredskillsfortypes`, identical to requiredSkill1–6: 182, 183, 184,
    1285, 1289, 1290). Capital T2 turrets keep Gunnery in slot 4, so they lost
    Sharpshooter, Trajectory Analysis, Controlled Bursts and Tracking
    Enhancer/Computer bonuses; the Aralez lost its second racial Drone
    Specialization.
  - The turret Specialization bonus was gated on "has a requiredSkill3" as a
    stand-in for "is T2". The 19 T1/meta/faction capital short-range turrets
    also have a slot 3 (Gunnery or Motion Prediction), so they got +10% DPS
    they don't have.
- **How it was caught:** a backlog note from v.20 ("requiredSkill 4–6"), then
  comparing the attribute list with pyfa's own source table for every
  published type (zero mismatches for 1–6), and checking the stand-in against
  the real rule for every published turret.
- **Do this instead:** when code tests "does the item require skill X", use
  all six slots (`REQUIRED_SKILL_ATTRS`, `requiredSkillMatchCount()`). Never
  use the presence of an attribute as a stand-in for a category (T2, size,
  race). Gate on the real skill IDs, and check the gate against the SDE for
  every published item it could touch.

## 20. The stat isn't only its modifiers: caps, alternate attributes, and the code that consumes it

- **What happened (fixed v.26):**
  - Targeting range was never capped. pyfa caps an attribute at the value of
    its `maxAttributeID` (`modifiedAttributeDict.__calculateValue`);
    maxTargetRange's is maximumRangeCap (797), default 300,000 m. A Rokh with
    three scripted Sensor Boosters showed 441 km, titans 312.5 km.
  - Capacitor drain read a module's cycle from `speed` or `duration` only.
    pyfa's `Module.rawCycleTime` is the largest of seven attributes
    (durationHighisGood, four Burst Projector durations). Interdiction
    Nullifiers (active by default), Signature Suppressor bursts and Burst
    Projectors used no capacitor.
- **How it was caught:** modelling the Integrated Sensor Array, whose handler
  *forces* maximumRangeCap. Following that attribute into pyfa's code led to
  the cap; asking "what cycle time does pyfa use" for the Suppressor led to
  `rawCycleTime`.
- **Do this instead:** for every stat, also read the SDE attribute record
  (`minAttributeID` / `maxAttributeID`, `defaultValue`) and the pyfa property
  that reads it (`Module.rawCycleTime`, `Fit.maxSpeed`, ...), not only the
  effects that modify it.
- **It happened again one day later (fixed v2026.10.14.1):** the v.26 cycle-time
  fix read `rawCycleTime` but not the next property pyfa uses,
  `getCycleParameters()`. Its average cycle is active time + `moduleReactivationDelay`
  (attr 669), so MJDs, Signature Suppressors, Nullifiers, Assault Damage
  Controls, Warp Core Stabilizers and Defender Launchers drew roughly 11-25x
  their real average (2x for an Interceptor's Nullifier, whose role bonus cuts
  the delay). Four hand derivations in the independent checks had the same gap,
  so they agreed with the bug (`check_module_states.py`: MJD, ADC;
  `check_phase3.py`: Suppressor, Nullifier; corrected 2026-10-14). Follow the value all the way to where pyfa CONSUMES it
  (`capUse`, `Fit.__generateDrain`), not just to where it is computed. Also
  see #3: pyfa's capacitor simulator is now run directly as the reference.
- **A third time (fixed v2026.10.14.7): missile range.** The v.17 weapon-range batch
  followed every handler on missile `maxVelocity` and `explosionDelay`, but not the
  property that turns them into a range. pyfa's `Module.missileMaxRangeData`:
  - adds the ship's radius to the flight time
  - flies whole seconds (two outcomes and the chance of the longer)
  - counts acceleration at half speed and measures from the ship's surface
  - caps auto-targeting missiles at `maxFOFTargetRange`
  The tool used velocity x flight time: up to 580 m long on XL torpedoes, and
  22 km long on an auto-targeting cruise missile. The reference is now pyfa's
  own function, lifted unmodified from `module.py` by
  `tools/independent_checks/check_missile_range.py`. When a pyfa property is
  self-contained like this, run it instead of re-deriving it (#3).

## 24. "The default ability" vs everything pyfa switches on

- **What happened (fixed v2026.10.14.4):** fighter DPS read one ability, the
  one ESI marks `is_default` (Attack Missile, pyfa's "Turret Attack"). pyfa's
  `Fighter.__init__` switches on Attack Missile **and every implemented ability
  before it** except MWD / Evasive Maneuvers, and `getDpsPerEffect` sums them.
  Light fighters fire a rocket salvo ("Missile Attack") as well: the tool
  showed ~40% too little for them, 0 for superiority fighters (Missiles only)
  and half for long-range heavies. Fighter Support Units weren't applied at all.
- **How it was caught:** Erik's pyfa screenshot of a constructed Thanatos fit:
  831 DPS vs the tool's 502. The difference was exactly the Missiles ability
  (329.7), reproduced to the decimal from pyfa's source.
- **Why it lasted:** three older fighter goldens (2026-10-08 / 10-11) said
  "pyfa has no fighter-DPS support at all" and were pinned to hand derivations
  of the same one-ability model. Nobody opened `eos/saveddata/fighter.py`. A
  claim about what pyfa does or doesn't do is a source claim (#5): check it in
  the source.
- **Do this instead:** for any item with several abilities or effects, read the
  pyfa class that decides which ones are on (`Fighter.__init__`,
  `Module` default states) and the method that aggregates them
  (`getDpsPerEffect`, `getVolley`). The generator now asserts that every
  damaging ability pyfa switches on by default is modeled.

## 26. Every carrier pyfa runs, not only hulls and modules

- **What happened (found v2026.10.14.5):** the firepower audit (P1) ran pyfa's
  handlers for hulls and subsystems and concluded "the Anhinga has no rate-of-fire
  bonus". pyfa also runs the ship's **mode** item (`Fit.mode`, `Ship.__getModeItems`):
  Tactical Destroyers and the Anhinga always have one, pyfa defaults to the first,
  and the Anhinga's Primary Mode cuts cruise / torpedo / rapid heavy launcher cycle
  time to 0.75. The resist audit found it because mode items carry resistance
  effects too.
- **Do this instead:** list the carriers pyfa's `Fit.calculateModifiedAttributes`
  runs (character skills, ship, drones, fighters, boosters, implants, modules with
  their charges, then the mode) and decide for each one whether it's modelled.
  `tools/pyfa_fit_oracle.py` runs them all.
- **Again in v2026.10.14.11 (EWAR, P4):** scripts are carriers too. A Tracking
  Disruptor's or Sensor Dampener's script modifies its own module (`'self'` rows
  in `gen_ewar_table.py`): it doubles one strength and zeroes the others. The
  hand EWAR tables ignored them.

## 28. A recorder error is a handler you didn't record

- **What happened (v2026.10.14.8, speed phase):** the first speed survey ran every pyfa handler
  through `tools/pyfa_effects.py` and listed 18 "unrelated handler errors". Several of them were not
  unrelated:
  - all three cloak effects (`fit.extraAttributes['cloaked'] = True` failed on the stand-in), so
    the cloak speed penalty was missing
  - the Helios / Cheetah cloaked-only velocity bonuses (they read `extraAttributes['cloaked']`)
  - the Triage Module: its EWAR filter couldn't be expressed, and the assertion aborted the whole
    handler, its speed and mass rows too
  - Advanced Spaceship Command on capitals and the Capital Ships skill, which read
    `fit.character.getSkill(...)` and `fit.ship.item.requiresSkill(...)`

  A second bug in the same run: filters are tested on one representative module per
  (skills, group) signature, but the "does this row reach a module we read" check compared
  type ids, so it silently dropped every rigging-skill drawback reduction.
- **Do this instead:**
  - After any recorder run, read every handler error and decide for each one whether it touches
    your stat. An error is a dropped handler, not noise.
  - `run(..., rich=True)` records `fit.character.getSkill`, `fit.ship.item.requiresSkill` and
    `fit.extraAttributes` reads/writes as values and conditions. Use it, or extend it, instead of
    letting the handler throw.
  - Never let one failing filter abort a handler: record the failure and raise only if a row you
    keep depends on it.
  - A filter can also fail *silently*: `ProbeItem` had no `getAttribute`, so a filter like
    Effect2982's `requiresSkill(...) and mod.item.getAttribute('duration')` was always false and
    looked like "no hits". Since v2026.10.14.11 it returns the item's real base value and records
    `('hasattr', name)`; `gen_ewar_table.py` fails if such a test matters for the modules it reads.
  - Compare filter hits by signature when the pool is one type per signature.
  - One type per signature is only safe while the filter tests skills and group. Effect2982 (Burst Projector
    Operation) also tests whether the module *has* an attribute (`getAttribute('durationECMJammerBurstProjector')`).
    The seven Burst Projectors share one signature but each has a different duration attribute, so with one
    representative, four of the effect's five rows matched nothing and were silently skipped (v2026.10.14.29).
    `gen_ewar_table.py` now evaluates filters on every EWAR module as well.
  - The carrier itself can gate a handler silently too (v2026.10.14.12): Effect2298 (Halcyon B /
    Federation Electronics boosters, high-grade Talon / Grail / Jackal / Spur sets) boosts each scan
    strength only `if sensorBoost in implant.item.attributes`. The recorder's source item was a plain
    `Any()`, so `in` was always False and the handler recorded nothing -- no error, just no rows.
    `compare_implants.py` caught it (a Drake with Halcyon B-4: tool 22.8, pyfa 24.6). `Src.item.attributes`
    now answers True and records `('cond', 'srcHas', name)`; the generator then requires the gated
    value's SDE default to be neutral (a carrier without the attribute changes nothing, as in pyfa).

## 35. "Matches no published item" can mean your test set is missing that item

- **What happened (v2026.10.14.28):** `gen_implant_table.py` skipped 20 mindlink rows with "filter matches
  no published item". The rows were pyfa's `filteredChargeBoost` on a Command Burst charge's
  `warfareBuffNMultiplier`. The generator tests charge filters on (charge, module) pairs, and its pair list
  held only weapons and their ammo. No Command Burst was in it, so nothing could match. A pasted fit's
  mindlink lengthened its bursts (the module row was kept) but never made them stronger.
- **How it was caught:** DEVIATIONS.md listed it as a gap. Reading the generator's skip list found the cause.
- **Do this instead:**
  - Treat every "matches nothing" skip as a question: does pyfa apply this to a real item? If yes, the test
    set is wrong, not the row.
  - Pairs come from what a module can actually load (its `chargeGroup1-5`). The generator now fails if no
    Command Burst pair exists.
  - The constructed check (a burst fit with a mindlink) must fail on the old build: v.27 failed 6 pins.

## 31. Find where the input really comes from, and size the job by running it

- **What happened (v2026.10.14.12, implants and boosters):** the backlog item said "Moderate" scope
  and "killmails carry implants too (zKill flag 89)". Neither was checked when it was written.
  - Real killmails (zKillboard API in the built-in browser, 2026-10-14) showed a SHIP loss never
    lists implants: a shuttle loss at 08:07:44 had none, the same pilot's pod 9 s later listed 10, all
    at flag 89. Boosters appeared on none of ~1,000 pod losses. Designing "apply killmail implants"
    would have built a Pilot Analyzer path with no data behind it; Erik decided to keep it off
    (`PILOT_ANALYZER_APPLY_IMPLANTS`).
  - Running every implant and booster effect through the recorder found ~350 handlers touching nearly
    every stat (HP, resists, capacitor, speed, sig, sensors, reps, cap use, weapons, drones, warp...).
    That is a Broad item; it shipped in phases, with the Fit card saying which stats include them.
- **Do this instead:**
  - Before designing around an input, look at real data from the source the tool will read (a real
    killmail, a real paste) and confirm the field is there.
  - Before sizing a mechanic, run the recorder over every carrier of it and count the stats it reaches.
  - When a feature ships in phases, say on the page which numbers include it (`IMPLANT_SCOPE_NOTE`),
    and list the rest in `DEVIATIONS.md`.

## 32. pyfa's database is not the SDE

- **What happened (v2026.10.14.13 → .14):** a Rupture check fit pasted into pyfa showed Boosters (2) for three
  booster lines, and 284 DPS / 14.4 km falloff where the tool and the oracle said 301 / 15.2 km. pyfa had
  silently dropped Strokar Booster VI: `db_update.py`, which builds pyfa's database from the SDE, DELETES
  every booster whose `boosterLastInjectionDatetime` is before the data dump (expired event boosters; 130 of
  them), and unpublishes items named like abyssal / mutated / _PLACEHOLDER. pyfa's EFT import
  (`service/port/shared.py fetchItem`) then finds nothing and skips the line without a message. The oracle
  reads the SDE directly, so it had the booster too; only Erik's real pyfa showed the gap.
- **Do this instead:**
  - Treat `db_update.py` as part of pyfa: it filters, renames and patches the SDE (also the T3C subsystem
    slot count, forced publish flags in `service/market.py`). `pyfa_sde.pyfa_removed_types()` mirrors the
    removals; the generator, the oracle and the tool all use it (`PYFA_REMOVED_IMPLANT_IDS`).
  - A count in pyfa's UI that differs from the paste (Boosters (2) for three lines) is a finding, even when
    every stat on screen looks plausible.

## 33. Check a layout at a real phone width, with mobile emulation

- **What happened (v2026.10.14.15):** Erik reported the tool was "difficult to see and read on mobile". Every
  earlier page check was a desktop screenshot, so nobody had seen that `index.html` had **no viewport meta tag**:
  a phone drew it as a ~980 px desktop page shrunk to fit, with the browser's text inflation enlarging some text
  and not other text. Adding `<meta name="viewport" content="width=device-width, initial-scale=1">` alone made
  it readable; the only real overflow left was a drone row's numbers (`.ds-meta{flex:none}`).
- **How it was caught:** loading the page in Chromium at 375 px with `is_mobile=True` (Playwright) and
  listing every element whose right edge passes the viewport.
- **Do this instead:**
  - Any change to page layout runs `tools/page_checks/layout_check.py` (1440 / 1100 / 375 px, mobile
    emulation at 375): no sideways scrolling, the expected columns, every control still wired.
  - A plain narrow desktop window is not a phone: without `is_mobile` the viewport tag, text inflation
    and touch sizes are never exercised.
  - When markup moves, every control that re-renders it moves too. v.15 put the summary cards and the Fit
    card in one container, so each control (mode, ASB charges, module states, drones) now rebuilds that
    container and re-wires all of them; the check clicks each one at each width.
  - Anything placed by formula is checked at its worst case. v.16's ring first spaced eight tiles per
    arc by their distance along the arc (8.4% apart, tiles 7.6%), but upright square tiles near the
    diagonals overlap unless they are a tile apart on the worse AXIS: a full 8/8/8 fit had 10 overlapping
    pairs. The check now builds a full-rack fit and tests every pair of tile rectangles.
  - Test with the longest real strings (v.17, Erik: "test how large strings will affect layout"): the
    longest SDE names per category, a long fit name with and without spaces, an unrecognized line, a
    37-character pilot name. Two things only that showed: (1) **one long word** doesn't grow its element's
    box, it runs out of it, so an element-bounds check passes while the text spills -- check the text runs
    (`Range.getClientRects()`); on a phone that one word made the browser zoom the whole page out to ~980px.
    (2) a **flex or grid item** keeps its min-content width, so `overflow-wrap:break-word` doesn't help it:
    it needs `min-width:0` and `overflow-wrap:anywhere`; and a fixed-width side column (the 130px range
    column) squeezes the name next to it to a few letters per line, which no overflow check catches --
    look at the screenshot.
  - An ellipsis is hidden information, not a fix (v.18): the collapsed cards' one-line summaries were
    first cut with `text-overflow:ellipsis`; on a phone the Navigation summary lost its last numbers.
    The text-run check flags clipped text too; summaries now wrap.
  - Swapping one view for another (v.33, the threat <-> my ship switch): if the new view is drawn after a
    tick ("Loading…"), the page is briefly short and the browser clamps the scroll to the top. Keep the old
    height (`min-height`) until the new view is drawn, and check `scrollY` before and after the switch.

## 29. pyfa's gaps are not the game's rules, and a control must change something

- **What happened (v2026.10.14.9 → .10, bug list #2):** the PANIC on a Rorqual offered only offline
  and online. That matched pyfa exactly: pyfa has no `Effect6719` handler class, so
  `Item.isType('active')` is false and `Module.isValidState` refuses ACTIVE. CCP's data does make
  it an activated module, so v.9 allowed ACTIVE as an input deviation. But pyfa computes nothing
  for it, so ACTIVE changed no number on any card, and Erik pointed out that a user who sets it
  and sees nothing change will think the tool is broken. v.10 took the option back out and kept
  the description on the EWAR / Misc card. The same flag also quoted the base 4-minute duration;
  pyfa applies the Invulnerability Core Operation skill (Effect6807, +10%/level), so at All V it
  is 6 minutes.
- **Do this instead:**
  - When a player says something exists in game and pyfa disagrees, check CCP's data (the SDE
    effect's category and duration attribute, the item description).
  - If pyfa doesn't model it, don't add a control that changes nothing. Describe the mechanic in
    words where it matters (a Misc flag) and say the stats don't include it. Ask before adding an
    input whose only effect is a label.
  - Any number a flag quotes goes through pyfa's handlers at All V like every other stat
    (`tools/pyfa_fit_oracle.py`), not straight from the item's base attribute (#20).
  - Keep the scan (`check_panic.py`) in the update check so a pyfa handler appearing, or a new
    module like this, is caught.

# Phase 2 — Deriving the expected values

## 3. Checking the tool against itself

- **What happened:** early "verified" numbers were computed by re-running the
  same tables the tool uses, so a wrong table entry agreed with itself.
- **Do this instead:** type pyfa's rules by hand in Python, read every value
  from the SDE, and pin the result. See `tools/independent_checks/`.
  - Do it **before** writing the code. If you derive the expected value after
    implementing, you tend to re-derive your own implementation, including
    its mistakes.
  - Read skill values from the skill item: `SK('Shield Operation', 'rechargeratebonus')`.
    Never type them as literals. A hand-typed 0.8 for Shield Operation
    (really 0.75) turned up in a scratch script.
  - The script must reproduce the pinned value **by itself**. A manual
    adjustment in a golden-fit note (the Executioner scram role bonus) means
    the script is incomplete.
  - When a piece of pyfa runs without the rest of pyfa, run it instead of
    re-deriving it. `eos/capSim.py` is pure Python: `tools/cap_sim_oracle.py`
    imports it unmodified, and `regression_suite/compare_cap_sim.mjs` checks
    the JS port against it on every golden fit (v2026.10.14.1). Compare after
    rounding pyfa's raw values the JS way; Python's `round()` rounds halves
    to even.

## 6. Trimmed golden-fit records hid effects

- **What happened:**
  - The Legion fixture's rigs were empty stubs, which hid the Polycarbon armor
    drawback (bug #2's real cause).
  - A Small Hull Repairer II stub had no `capacitorNeed`.
  - Paladin, Kronos and Muninn fixtures had mid-slot scripts but no
    `midSlotByFlag`, so scripts could never pair with their Tracking or
    Guidance Computer.
  - The Vargur fixture's ship record had no scan-strength attributes, so the
    Bastion sensor fix showed 0 → 0 there. That was also true of 4 others
    (Legion, two Curses, Skybreaker).
  - The `ishtar_alyra` fixture had no **group** record for its X-Large
    Shield Booster, so the engine dropped the module entirely. For months
    the pin said capacitor stable 96.9% while the real page and Erik's pyfa
    screenshot both said 40.5%. The gap was blamed on the capacitor model
    (a closed form, then a simulator) until v2026.10.14.1 made the
    simulator match pyfa exactly, which left the inputs as the only
    remaining cause (fixed 2026-10-14).
- **How it was caught:** a fix changed a number you'd expect to change, or
  failed to change one you'd expect to. The Ishtar was caught by running the
  same fit as an EFT paste (full SDE records) and comparing it with the
  fixture.
- **Guard:** `run_regression.mjs` now fails any fitted item, drone or
  fighter whose type or group record is missing from its fixture (cargo and
  fleet hangar are exempt).
  `tools/refresh_golden_fixtures.py` refreshes every record from the SDE;
  in report mode it must print `0 of N fits change` (all 161 refreshed
  2026-10-14).
- **Do this instead:** build fixtures from full SDE records, through the real
  `parseEftFit()` (`run_eft.mjs`) or a real killmail. Add slot pairing
  (`midSlotByFlag`, `highSlotByFlag`) whenever charges or scripts are fitted.
  If a fit didn't change when it should have, inspect the fixture's records
  first.

## 37. A fixture built from the code's assumption agrees with the code

- **What happened (v2026.10.14.35):**
  - Since v2026.10.14.26 the engine paired a Warp Disrupt Field Generator's script from **mid-slot** flags
    only. A WDFG is a **high-slot** module, so on a real killmail or EFT paste its script sits in a high-slot
    flag.
  - The two constructed Heavy Interdictor goldens written for that version listed the WDFG as a mid slot. Code
    and fixture shared the same wrong assumption, so they agreed, and `compare_fit_stats.py` agreed with both.
  - The result on real HIC fits: a scripted WDFG still got the bubble's +50% signature bloom (pyfa Effect3380
    skips it when a charge is loaded) and none of the script's cycle / capacitor change (Focused script:
    6 s and 45 GJ, not 30 s and 112.5 GJ).
- **How it was caught:** a new golden for Phase 2a put the WDFG in a high slot, the way a real fit has it, and
  `check_projected.py` found the target's signature 225 m against pyfa's 150 m.
- **Do this instead:** put every item in a constructed fit where a real fit puts it: the slot its module
  occupies in the game, its charge in that slot's flag. If unsure, build the fit through `parseEftFit()` from
  an EFT paste (it assigns slots from the item itself), or copy the layout of a real killmail. When code pairs
  charges by slot, check the slot against the module's own slot attribute, not against the fixture.

## 38. A new grid row under a sticky column gets covered when you scroll

- **What happened (v2026.10.14.36, caught before delivery):** the "Their damage on you" card was first added as
  a fourth grid area of `.fit-layout` ("dmg dmg dmg" under "beat fit stats"). The Fit column is
  `position: sticky` from 900 px up. A sticky grid item is held inside the whole grid container, not inside
  its own row, so when the page scrolled down to the card the Fit column slid down with it and covered the chart.
- **How it was caught:** a screenshot of the card. The page check passed: it measured the boxes with the page
  scrolled to the top, where nothing overlaps.
- **Do this instead:** never put a grid area below the last row that holds the sticky column. Since
  v2026.10.14.37 the grid is written from `FIT_LAYOUT` and `fitLayoutGridCss()` throws on such a row; content
  that must come after the columns goes outside the grid. When a check measures layout next to anything sticky,
  scroll through the whole layout and measure at each step (`damage_chart_check.py` `no_overlap`; a layout with
  the card below the columns fails it). Look at a screenshot of every new card at 1440, 1100 and 375 px.

## 39. An override inside `:has()` lost to the general rule it was overriding

- **What happened (v2026.10.14.38, caught before delivery):** the tile rows got a general rule, "exactly three
  tiles: three columns" (`.estimate-box:has(> .estimate-stat:nth-child(3):last-child)`), and the Capacitor row
  an override, "two columns" (`.estimate-box:has(> .estimate-stat > .cap-ring-row)`), written later in the file.
  At 520 px the Capacitor still showed three columns. `:has()` counts the specificity of its most specific
  argument: the general rule's argument has three classes, the override's two, so the general rule won no
  matter where it stood.
- **How it was caught:** the card width lab's screenshot (`card_width_check.py --shots`).
- **Do this instead:** when one rule must not apply to some elements, exclude them in that rule
  (`:not(:has(> .estimate-stat > .cap-ring-row))`) rather than relying on a later override; do not count on
  source order between rules with `:has()`, `:is()` or `:not()`. Look at the lab screenshots for every width
  after a CSS change.

## 40. A ranking metric that leaves out what the pick is for

- **What happened (v2026.10.14.42, caught before delivery):** the first build of the Weaknesses picks ranked each
  charge by its applied DPS, the number pyfa's damage graph shows. That graph ignores the target's resists by
  default (`ignoreResists: True`). A card called "Weaknesses" then recommended the charge with the most raw DPS even
  when the target resists its damage type: 204 of the checked fights had a different, better pick once resists
  counted (Scourge vs Inferno missiles, Void vs Null, the drone race).
- **How it was caught:** asking what pyfa's graph does with resists before writing the check (`graphs/data/
  fitDamageStats/getter.py applyDamage`, `service/settings.py`), not after.
- **Do this instead:** before you rank anything, write down what the ranking is FOR and check that the number you
  sort by contains every input that decides it. Show pyfa's number, but sort by the quantity that answers the
  question (here: how long they last, the strip's time to kill against their resists, with the rest of the fit as
  it is). Add a mutation to the independent check that sorts by the naive number (`raw_dps_order`) and confirm it
  fails.

## 41. A mockup on a page the canvas doesn't open on

- **What happened (2026-10-23):** the three matchup options went onto a NEW page of the existing My Ship canvas.
  The canvas opens on its first page, so Erik saw the old phase-1 boards and asked whether he had the wrong file.
- **Do this instead:** when you add boards to an existing canvas, either set its `launch` to the new page or name
  the page in your message ("open the page list, pick X"). Before saying what a mockup shows, render the board
  files yourself (strip the canvas markup, Playwright screenshot) and send the images too; the user then has the
  options even when the canvas view goes wrong.

## 42. A card's name typed in many places drifts apart

- **What happened (fixed v2026.10.14.45):** each card's title was a string passed by hand at every call
  (`cardLabelHtml('dmg', 'Their damage on you')`), and notes, tooltips and ERROR_CODES typed the names again. Over a
  few builds they disagreed: "Navigation & targeting" vs the agreed "Navigation & Targeting", a Capacitor note
  pointing at an "EWAR card" whose title is "EWAR / Misc", error codes naming a "last-kill box" and a "threat / my
  ship switch" that no longer existed. Erik: "subtext and explanatory info referencing card titles that should be
  interchangeable."
- **Do this instead:** name each card or page part once, in `CARD_NAMES` (roadmap/card-names.md has the same
  table), and refer to it by key: `cardName('dmg')` in text, `cardLabelHtml(key)` / `collapsedCardHtml(key, summary)`
  for titles (they take no title), `{card:dmg}` in ERROR_CODES. `tools/check_card_names.py` (update-check chain)
  reads every string the page can show and fails on a name typed by hand, a "<Name> card" that isn't a listed name,
  an old name, or a key that doesn't exist. When you rename something, add the old name to its `RETIRED` list.
- **A trap found on the way:** `${cardName('fit')}` inside a `'...'` string is printed literally, and in a `'...'`
  string that also contains `'fit'` it is a syntax error that stops the whole script (the regression suite caught
  it). Use backticks for any string with `${...}`; the check flags `${cardName(` inside quotes.

## 43. A collapsed card that only updates while it's open

- **What happened (fixed v2026.10.14.47, found by Erik):** the Damage Application card's collapsed row showed a
  headline cached from the last time the card was drawn open. The refresh after a change ("Use in assessments" off,
  a new saved ship, a preset) only redrew cards that were open, so a collapsed card kept its old numbers ("still
  shows old text (out of sync w/ user's change)"). On a phone, where the card starts collapsed, the row never had
  numbers until it was opened once.
- **Do this instead:** anything a collapsed card shows is computed from the same inputs as the open card, and the
  refresh path covers both states (`dmgFillCollapsed`, `dmgRefreshAll` refills every card). When you add a refresh
  hook, ask what else on the page displays that value: a collapsed row, the Firepower link, the Matchup. A page
  check that changes an input while the card is collapsed catches it; one that only tests the open card doesn't.

## 44. A control that appears when a value changes moves the page

- **What happened (fixed v2026.10.14.48, found by Erik):** the Damage Application card showed a "Reset to my
  ship" button only once a setting left its default. The button's row was taller than the title row without it, so
  the first touch of any slider made the card 16 px taller (42 px on a phone) and pushed every card below it down.
  Erik: "numbers change on multiple cards which causes the content to shuffle and move elements on the page".
- **Do this instead:** anything that can appear while the user is working keeps its space from the start. Show
  the control disabled rather than hidden, and give live numbers a box as wide as their widest possible value
  (`numBoxStyle`). Then measure it: `tools/page_checks/no_shift_check.py` uses every control and fails if a covered
  card moves more than 1 px. A screenshot can't show this; only a before/after measurement can.

## 45. Measuring a hidden element gives 0

- **What happened (fixed v2026.10.14.48, from Erik's screenshot):** the Damage Application card decides whether its
  "Adjust" panel starts open from the card's width (`clientWidth < 720` = phone). A Pilot loss tab that isn't shown
  is drawn while hidden, so its width is 0. The panel started closed, and on the wide layout the closed panel looked
  like an "Adjust" heading with nothing under it.
- **Do this instead:** before using a measured size, ask whether the element can be hidden at that moment
  (`display: none` ancestors, tabs, collapsed cards). If it can, fall back to something that is laid out (here the
  window width), or decide in CSS. The page check opens the second loss tab and checks Adjust is open there.

## 46. A pop-up checked in one place can open off the screen in another

- **What happened (caught before delivery, v2026.10.14.49):** the info panel was built for the Damage Application
  card, which sits on the right, and its check opened only that panel. Placed against its button's right edge, it
  was fine there. Phase S2 put the same button on the Weaknesses and EWAR / Misc cards in the narrow left column at
  1440 px: the 380 px panel would have opened 1 px past the screen's left edge, across the column's edge.
- **Do this instead:** when a shared piece (a panel, a menu, a tooltip) goes onto more cards, check every place it
  appears, at every layout width, not the first one. Place it against something that can't be narrower than it (here
  the card, as wide as 380 px or its column allows). `layout_check.py` now opens every info panel at 1440, 1100 and
  375 px and fails if one leaves the screen or its column; on v.48's placement it fails on Weaknesses and EWAR.
- **Again in v2026.10.14.52 (Erik's screenshot: "info panel clipping bottom edge of the matchup bar"):** the same
  panel, put on the Matchup in v.51, was never opened by any check. Two things around it broke it:
  - the board has `overflow: hidden`, and the panel's positioned parent was inside the board, so the panel was cut
    off at the board's bottom edge;
  - below 900 px a `transform` on the button's wrapper made that wrapper the frame for the phone sheet
    (`position: fixed`), so the sheet was 34 px wide.
  Being "on screen" isn't enough. Check that the panel is actually *seen*: `document.elementFromPoint` at its corners
  must return the panel itself. `layout_check.py` (every card) and `fight_strip_check.py` (the Matchup) now do that;
  `fight_strip_check.py` fails on v.51 at all three widths. Watch for `overflow: hidden` and `transform` on any ancestor of a pop-up.

## 47. One wrong anchor stops a whole patch

- **What happened (S2 start):** one large replace script asserted each piece of old text before writing. Its first
  anchor was typed from memory ("  \"myshippage\"..." with two spaces; the file has one), so the assert stopped the
  script and none of the changes were written. Nothing broke, but all of it had to be redone.
- **Do this instead:** read the exact text of every anchor from the file before writing the replacement (copy it,
  don't retype it), and split a big change into small patches by card, each checking its own anchors and saving on
  its own. A mismatch then costs one small patch, and it says exactly which text didn't match.

## 48. Moving text into a hover hides it from checks that read the page

- **What happened (caught by the page checks, v2026.10.14.50):** the Capacitor card's caption ("Small Capacitor
  Booster II has no charges in the fit, not injecting") became a short line ("best case · booster has no charges"),
  with the sentence moved to its hover. `missing_charges_check.py` read the card with `inner_text`, which doesn't
  include hover text, so three checks failed although the page was right.
- **Do this instead:** before shortening a line, search the checks for its words (`grep -rn "<a few words>" tools/`).
  Point each one at the new short line *and* at the hover (`title`), so the check still proves the same fact. Don't
  delete the check or loosen it to "something is there".

## 49. Two controls for one setting: one owner, both redraw from it

- **What happened (designed in, v2026.10.14.51):** the fight strip under the Matchup and the Damage Application
  card's Adjust panel both set the range and how each ship moves. If each kept its own copy, a change in one would
  leave the other showing a stale value (the same class as LESSON #43, the stale collapsed row).
- **Do this instead:** keep the value in one place (here the threat fit's `f.dmg`). Every control writes there and
  then redraws from there: the strip calls `dmgSyncControls` + `dmgDraw` on the card, and the card's redraw calls
  `mysRenderStrip`, which reads the same settings. Test both directions (`fight_strip_check.py`: strip → card and
  card → strip), and from the other perspective too.

## 50. A choice that can become impossible: keep it, mark it, say why

- **What happened (designed in, v2026.10.14.53):** Keep at Range only works outside the other ship's tackle and
  when the other ship isn't faster. Moving the range slider or the other ship's speed can make an earlier choice
  impossible. Switching it to something else behind the user's back would change the fight without telling them.
- **Do this instead:** offer the choice only where it's possible, with the reason where it isn't. If it becomes
  impossible later, keep it chosen, mark it (amber), say why on hover, and compute the nearest honest thing (here
  the speed capped at the ship's top). Test all three cases: possible, not offered, chosen but impossible
  (`fight_strip_check.py`).

## 9. Comparing different quantities with pyfa

- **What happened:**
  - **Golem:** "4.8% low" compared torpedo-only DPS to pyfa's total, which
    included two smartbombs.
  - **Rorqual capacitor:** the delta depends on which modules are active in
    pyfa.
  - **Rorqual shield rep:** the gap was the pilot's boosters (drugs), not a
    bug.
  - **Curse disruptors (found v2026.10.14.11):** the 2026-10-11 pyfa check
    (-29.5% on all three Tracking Disruptor values) was made on a fit with no
    scripts. The golden fit is the killmail, whose disruptors carry Optimal
    Range Disruption Scripts: pyfa gives -59.1% / -59.1% / 0% for it. The pin
    said "pyfa-verified" for a fit pyfa never saw.
- **Do this instead:** break pyfa's number into its parts first. A pyfa number
  verifies only the exact fit pyfa was given (modules, charges, scripts,
  states); write that fit next to the pin. Ask for the
  per-module values or a screenshot of module states before calling it a bug.

## 10. Different game data versions

- **What happened:** Erik's pyfa v2.66.3 had April data (client build
  3326071): 50MN MWD II with 200 GJ cap use and +500% sig. Current SDE and ESI
  have 160 and +475%, so the Legion's MWD numbers differed for a reason that
  had nothing to do with the math.
- **Do this instead:** check pyfa's data build (Help → About, or `eve.db`)
  before diagnosing a small difference on a specific module.

## 22. Auditing pyfa: missing attributes, split bonuses, unpublished hulls

- **What happened (firepower audit, 2026-10-14):** the first runs of
  `tools/audit_firepower.py` reported about 160 mismatching hulls. Most were
  the audit's own mistakes:
  - **A missing attribute was read as 0.** pyfa's `getModifiedItemAttr`
    returns the attribute's **default** when an item lacks it.
    `fighterLightDamageMultiplier` defaults to 1, so reading 0 invented a −100%
    light-fighter penalty on every carrier.
  - **One bonus, many effects.** pyfa splits one bonus by damage type (Kestrel:
    four effects, one per type) or by launcher family (Raven: cruise, torpedo,
    rapid heavy). Counting rows one by one made matching bonuses look like
    duplicates.
  - **Charge filters that test the launcher.** Some missile bonuses check the
    fitted launcher, not the charge. Test charges against every launcher group.
  - **Damage-type boosts on drones.** The Griffin Navy Issue's −70% drone
    malus is applied to em/thermal/kinetic/explosive damage, not
    `damageMultiplier`.
  - **Unpublished hulls.** Special-edition hulls are unpublished but still
    fly and appear on killmails. Audit every hull, not only published ones.
- **Do this instead:** before trusting an audit's mismatch list, open three
  or four mismatches by hand (pyfa source + SDE values). If they share a
  cause, fix the audit first. Read absent attributes as their SDE
  `defaultValue`.

- **Both directions (v2026.10.14.13):** the tool read a Precursor or Vorton weapon's missing `falloff` as 0;
  pyfa reads the SDE default 1 (shown as 1 m, 1.25 after Trajectory Analysis). And the reverse trap, in a
  check: `damageMultiplierBonusMax` defaults to 0.5 on EVERY item, so a DPS check that multiplied by
  `1 + damageMultiplierBonusMax` gave every turret +50% (the Rifter came out 288 against pyfa's verified 192).
  pyfa's `calculateSpoolup` returns 0 unless the per-cycle value is set too. Read the defaults, then read
  the code that consumes the value: pyfa often guards a defaulted attribute there.

## 27. A reference that swallows errors like pyfa hides its own gaps

- **What happened (v2026.10.14.6):** the new mode comparison found every laser
  cap need 25% higher in the tool than in `pyfa_fit_oracle.py` (2.081 vs 1.665 GJ
  for Small Focused Pulse Laser II with Conflagration). The **oracle** was wrong.
  pyfa's crystal effect (`ammoInfluenceCapNeed`) calls `module.item.getAttribute`,
  which the oracle's stand-in item didn't have. The `AttributeError` was swallowed,
  as pyfa swallows them in effect handlers, so the handler silently did nothing.
  The same check found two more oracle gaps:
  - ships had no `mass` (pyfa's `db_update.py` copies mass / capacity / volume /
    radius from the type row into the attributes), so align time came out 0 and
    propulsion speed huge
  - a slot listing its charge before its module lost the pairing, so two of four
    lasers had no crystal and the charges ran as modules
  `compare_resists.py` had passed on all 183 fits, because none of these touch a
  resistance.
- **Do this instead:**
  - When the tool and the reference disagree, debug **both** sides. A reference
    is code too.
  - The oracle records every `AttributeError` that names one of its own
    stand-in classes in `fit.oracleGaps`. Over every golden fit there must be
    none. Scan for `_Any` fallbacks too (`Item` / `OracleFit.__getattr__`), and
    implement any that a handler really uses.
  - Compare on more stats than the one being changed. The capacitor drains in
    `compare_modes.py` caught the crystal gap, which had nothing to do with modes.
  - A stand-in can also *hang* (v2026.10.14.12): Effect2589 tests `attr in booster.itemModifiedAttributes`.
    The oracle's `Attrs` had `__getitem__` but no `__contains__`, so Python fell back to calling
    `__getitem__(0)`, `(1)`, ... forever. pyfa's `ModifiedAttributeDict` defines `__contains__` /
    `__iter__`; the stand-in now does too. A check that never finishes is a stand-in gap.
  - A check that **re-builds** the reference fit must carry every input of the original.
    `compare_speed.py` and `compare_modes.py` rebuilt `OracleFit` from `oracle_for()`'s modules and
    dropped its implants: the Rorqual's align came out 294.8 s in the "reference" against the tool's
    280.3 s, which is Erik's pyfa number. The check was wrong, not the tool.
  - A whole-fit comparison must feed the reference the tool's **resolved inputs**, not the
    reference's own defaults (v2026.10.14.22, `compare_fit_stats.py`): the oracle picked its own
    propulsion module and applied group limits again, so fits "differed" on choices, not on maths.
    Pass the tool's `moduleStates` / `droneStates` and `group_limits=False`.
  - `x or 1` turns a real 0 into 1: the Triage Module's drone `damageMultiplier` 0 became 1 in the
    reference, so the tool's (correct) 0 drone DPS looked wrong. Test for "absent", not "falsy".
  - A reference that rounds must round like pyfa: `floor(x + 0.5)` in `compare_implants.py` disagreed
    with pyfa on every exact tie once the tool rounded like pyfa (#34).

# Phase 3 — Implementing

## 23. pyfa math and tool choices mixed together

- **What happened:** the engine was one 3,300-line function in which pyfa
  formulas sat next to the tool's own choices (assumed charges, drone
  selection, EWAR lockout). Hand tables drifted from pyfa unnoticed (Leviathan,
  Anhinga), the stacking helpers used a rounded penalty table, and nothing
  told a later edit "this line is pyfa — don't adapt it for the tool".
- **Do this instead (2026-10-14):** pyfa-replicating code lives inside
  fingerprint-locked `PYFA CORE` sections (`PYFA_CORE.md`); the suite fails
  if one changes without re-verification. Tool behaviour changes the inputs
  or the presentation, never the core. Deliberate differences go in
  `DEVIATIONS.md`. Start every session with `tools/pyfa_update_check.py`.

## 25. A locked "port" that wasn't, and pooling that lost three rules

- **What happened (fixed v2026.10.14.5):** the resistance code pooled modules its
  own way: hardeners in one penalized list, Damage Control, Bastion and the Reactive
  Armor Hardener each as a separate unpenalized layer, Compensation skills at 20%.
  pyfa (and the game) put Damage Control, Bastion and the RAH in one `preMul`
  stacking group, and the Compensation skills give 5%/level. The RAH simulation was
  fenced as a PYFA CORE "port", but it wasn't pyfa's Effect4928: no 50-cycle limit,
  no 1e-6 loop tolerance, no 3-decimal rounding, run before other modifiers. The
  lock only proves a section hasn't changed since someone said it was right.
- **How it was caught:** `tools/pyfa_fit_oracle.py` runs pyfa's own handlers on a
  whole fit with a hand port of `__calculateValue`. Run over every golden fit, it
  matched Erik's pyfa screenshots and differed from the tool on 18 fits.
- **Do this instead:** don't reimplement pyfa's attribute bookkeeping per module
  type. Generate the handler rows (target, operation, source attribute, stacking
  group) and compute the attribute the way `modifiedAttributeDict` does: forced >
  base x unpenalized x each penalty group on its own, capped. Before locking a
  "port", compare it line by line with the pyfa function, and run it against the
  oracle on every golden fit (`compare_resists.py`).

## 7. Wrong stacking penalties

- **What happened:**
  - **Penalized when pyfa doesn't:** cap and shield capacity/recharge
    multipliers (PDS, Flux Coils, Power Relays). pyfa passes no
    `stackingPenalties`.
  - **Not penalized when pyfa does:** Auxiliary Nano Pump rigs and Signal
    Distortion Amplifiers.
  - **Separate penalty groups:** Signature Suppressor (`postMul`), T3D modes
    (`postDiv`), WCS/cloak scan-res (`PostMul`).
  - **Skill effects carried by rigs** (Hydraulic Bay Thrusters, Rocket Fuel
    Cache) run at level 1 and are penalized.
  - **A rounded penalty table (fixed v2026.10.14.23):** `applyStacking` used
    0.869 / 0.571 / 0.283 / ... and 0 from the 9th source on. It was off by up
    to 0.007% (Paladin volley 5,714 vs pyfa 5,713), small enough that the
    all-fit check had a 3e-4 tolerance just for it. A tolerance that exists
    for one known gap hides every other gap of that size; remove the gap,
    then the tolerance.
- **Do this instead:** copy `stackingPenalties` and `penaltyGroup` straight
  from the recorded handler call. Use `pyfaPenalizedProduct()` once per
  penalty group. It keeps >1 and <1 chains separate, largest first,
  `1+(m−1)·exp(−i²/7.1289)`.

## 14. Counting the same bonus twice

- **What happened:**
  - The Compensation skill was applied both as its own pool entry and inside
    the module's value.
  - Ishtar-type hulls got both of two mutually exclusive drone bonuses.
- **Do this instead:** when you move a mechanic to the effect-driven path,
  switch the old path to fallback-only behind a clear flag
  (`weaponRangeViaEffects`, `hpFallback`, `siegeScanResViaEffects`).

## 15. pyfa rules that are easy to get wrong

- `requiresSkill(X)` checks the item's **direct** `requiredSkill1–6` only, not
  prerequisite chains.
- Handlers passing `skill='Some Hull Skill'` scale by skill level (×5 at V).
  Role bonuses without `skill=` are flat.
- `increaseItemAttr` adds before multipliers: `(base + adds) × multipliers`.
- pyfa's capacitor sim always factors in **cap booster reloads**, even with
  reload factoring off.
- Scripts (Tracking/Guidance Computer, Sensor Booster) modify their **own
  module's** bonus attributes, so they pair per instance by slot flag.

## 17. One module, two kinds of effect (module states)

- **What happened (found while designing v.20, before any code was
  written):** the obvious module-state gate counts each module once: "ACTIVE
  copies if the module can be activated, otherwise ONLINE copies". Several
  modules carry both a passive effect and an active one:
  - Assault Damage Control: passive Damage Control resists (2302) + active
    burst (7012)
  - Signature Suppressor: passive −10% signature (8108) + active burst (8109)
  - Interdiction Nullifier / Warp Core Stabilizer: passive targeting
    penalties (2645, 2646, 8123) + active effect
  - MWD: passive capacitor-capacity penalty (58) + active speed/bloom (6730)
  - Entosis Link: passive speed penalties + active effect
  
  With a per-item count, a Signature Suppressor left ONLINE (its default)
  would lose its passive −10% too, and an online MWD its capacity penalty.
- **How it was caught:** listing every published module whose effects mix
  `active` and `passive`/`offline` handler types (a few lines with
  `tools/pyfa_effects.py`: `EFFECTS[id].type`), then checking each one against
  the code path that reads it. The constructed golden
  `rifter_constructed_states_ab_active_mwd_online` pins the online MWD's
  capacity penalty.
- **Do this instead:** count with `effQty(dt, effectId)` wherever the code is
  keyed by effect. Use the per-item `itemQty(dt)` only for code keyed by
  group/attribute, and check that list of mixed modules for each such branch.

## 30. A name that resolves is an item, not necessarily the right kind of item

- **What happened (v2026.10.14.9, bug list #1):** an EFT fit pasted into the D-Scan box was
  "analyzed": every module line resolved to a real type id through ESI, so modules were listed
  as contacts. Resolution only proves the name exists.
- **Do this instead:**
  - Check the input's shape first (an EFT header is never a D-Scan row) and say plainly what
    it is and where it belongs.
  - After resolving, check the category is one that can actually appear there (no module,
    skill, implant or subsystem is ever an object in space).
  - Test a new input check against every real paste in the parse tests, starting at every row,
    so it can't misread a real scan.

## 34. JavaScript rounds a tie up; pyfa rounds it to even

- **What happened (fixed v2026.10.14.22):** pyfa formats every number with
  Python's `round()` (`gui/utils/numberFormatter.py` → `roundToPrec`), which
  rounds the exact binary value and sends an exact tie to the even digit.
  `Math.round`, `toFixed` and `toLocaleString` send it up. So a speed of
  exactly 262.5 m/s showed 262 in pyfa and 263 here, and 81,250 m targeting
  81.2 km vs 81.3 km. Exact ties are common in EVE (HP 562.5, capacitor
  312.5, resists 12.5%): 148 golden fits moved.
  - **Double rounding:** a range rounded to whole metres and then to 0.1 km
    can differ from pyfa, which rounds the raw value once (81,350.3 m → pyfa
    81.4 km, tool 81,350 → 81.3).
  - **Truncation, not rounding:** pyfa shows time to empty with `"%ds"` /
    `"%dm%ds" % divmod(t, 60)`, which truncates (40.8 s → "40s"). The tool
    rounded, so about a quarter of the unstable fits showed one second more.
- **How it was caught:** comparing Erik's pyfa screenshots (262 vs 263,
  81.2 vs 81.3), then fuzzing.
- **Do this instead:**
  - Round a pyfa stat with `pyRound(x, nd)` (or `kmText(m)` for km), never
    `Math.round` / `toFixed` alone. `tools/check_py_round.mjs` fuzzes it
    against Python `round()` and `formatDurationShort` against pyfa's format.
  - Format from the **unrounded** value (`exact.*`, `rangeEstimates[].exactM`,
    `timeToEmptyExactSec`), so the value is rounded once, as in pyfa.
  - Read how pyfa *formats* a stat (its `gui/` view), not only how it computes it.
  - Values that are only the tool's own (missile application ranking, ring
    geometry) can keep `Math.round`; say so in `DEVIATIONS.md`.
  - Rounding *inside* a calculation too (v2026.10.14.34): pyfa's `floatUnerr`
    keeps 7 significant digits with `round()`. The port used `toFixed`, fine
    for flight times, but damage-application multipliers can be exact binary
    ties (0.5 ** 11 = 0.00048828125). `pyfaRound(x, n)` is Python's `round()`
    exactly (BigInt, ties to even); use it wherever pyfa calls `round()`.
  - Don't round a reference value when you pin it: an applied DPS of 2e-19
    rounded to 9 decimals became 0, and the pin failed against the exact tool.
    Pin the reference unrounded and let `tolerancePct` do the comparing.

## 36. Code that runs at page load also runs inside the regression suites

- **What happened (v2026.10.14.33, caught before delivery):** My Ship's start-up code reads the browser's
  storage and draws the header chip when the script loads. The regression suite, the parse tests and the
  output diff load the same `<script>` in a Node `vm` with a stub DOM: `getElementById()` returns an object
  with only `addEventListener`, `style`, `innerHTML`; there is no `classList`, no `localStorage`, no
  `document.addEventListener`. Code that touches those at load throws, and the whole suite stops before a
  single fit is checked.
- **Do this instead:**
  - Anything that runs at load (not on a click) either uses only what the stub has, or returns early when
    an element looks like the stub: `if(!chip || !chip.classList) return;` (`myShipInit`, `// LESSON #36`).
  - Wrap every storage access in try/catch (a private window throws too).
  - After adding start-up code, run `run_regression.mjs`, `dscan_parse_tests.mjs` and the output diff, not
    only the page checks: the page checks use a real browser and can't see this.
  - Pick a new class-name prefix with a grep first: `ms-` already meant "module state" here, so My Ship
    uses `mys-`. A shared prefix makes a `querySelectorAll('button.ms-...')` in one feature pick up the
    other's buttons.

# Phase 4 — Verifying and delivering

## 12. `node --check` passes, the page still breaks

- **What happened:** a constant was declared after its first use
  (temporal dead zone). That's valid syntax, but it threw at runtime.
- **Do this instead:** run the regression suite and render one fit with
  Playwright.

## 13. "Delivered" wasn't delivered

- **What happened:** a commit reported success but the file never reached the
  user's disk (2026-10-08).
  It happened again on 2026-10-14: CLAUDE.md was edited and committed from the
  same `stagedPath` used for an earlier commit; the bridge wrote the EARLIER
  content (new mtime, old size), and a listing glance didn't catch it.
- **Do this instead:** after every write to the user's machine, stage the file
  back and byte-compare it (`cmp`) with the source; at minimum compare the
  size, not just the mtime. Commit each revision from a fresh path (or a new
  SendUserFile `file_uuid`), never re-use a `stagedPath` already committed.

## 21. A renamed result field silently turned its pins into no-ops

- **What happened (fixed v.27):** the regression checker skipped any pinned
  field missing from the result. Removing the capacitor's `combinedConfident`
  tier would have turned the Rorqual's pyfa capDelta pin into a no-op, with
  the suite still printing ALL PASS. Moving a "time to empty" pin from a
  newly stable fit would have done the same.
- **How it was caught:** re-pinning by hand after the change, and noticing that
  v.26 failed only 10 checks against the new goldens because the new fields
  didn't exist there.
- **Do this instead:** the checker now FAILS a pinned field that isn't in the
  result. When you rename or remove a result field, grep `golden_fits.json`
  for its flattened name and move every pin.

