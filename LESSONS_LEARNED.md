# Lessons learned: mistakes made here and how to avoid them

This file is for any model or person changing a calculation in `index.html`.
Every entry is a mistake that actually happened in this project. Each entry
covers how it showed up, how it was caught, and the method that works.

The goal is to match pyfa (the community fitting tool) exactly. Use primary
sources only: pyfa's source (`eos/effects.py`, `eos/modifiedAttributeDict.py`,
`eos/saveddata/module.py`, `eos/saveddata/fit.py`, `eos/capSim.py`) and CCP's
SDE / live ESI. Tooling for both is in `tools/` (see `tools/README.md`).

**How to use this file**

0. Start with the **Index** below: one line per entry, grouped by task. Open only the entries that apply; you don't need to
   read the whole file for a page or Intel change.
1. For a calculation change, follow the checklist below **in order**. The order matters:
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

## Index (read this first)

One line per entry, grouped by what you are about to do. Read the group that matches your task, open the entries that apply, and
follow the checklist below for any calculation change. Entries keep their numbers wherever they sit in the file (`// LESSON #n`
comments point at them); `tools/check_lessons_index.py` (a chain step) checks every entry is listed here once.

**Calculations: finding every source (read before changing how anything is calculated)**

- #1 Finding pyfa handlers with text matching misses some of them.
- #16 Python closures in pyfa handlers (a trap for the recorder itself).
- #19 Skill handlers that filter on the skill itself (another recorder trap).
- #28 A recorder error is a handler you didn't record.
- #2 Gating on group names instead of effects.
- #4 Hand-maintained per-hull tables are incomplete.
- #11 Assuming a hull bonus from memory or trait text.
- #5 "Exhaustively checked, nothing found" was wrong.
- #8 Excluding an attribute as a "collision".
- #18 Reading part of a list, or a stand-in for the real rule.
- #20 The stat isn't only its modifiers: caps, alternate attributes, and the code that consumes it.
- #24 "The default ability" vs everything pyfa switches on.
- #26 Every carrier pyfa runs, not only hulls and modules.
- #76 Before modelling an effect, find pyfa's handler for it: it may already say how.
- #62 A generated table covers only the attributes you listed: grep pyfa for every attribute your formula reads.
- #59 A handler's source value is the source's MODIFIED attribute: a script changes it.
- #64 A state gated on one variant's attribute silently drops the other variants.
- #68 A new list of inputs exposes the engine to inputs no fit had: check every one against pyfa.
- #35 "Matches no published item" can mean your test set is missing that item.
- #31 Find where the input really comes from, and size the job by running it.
- #32 pyfa's database is not the SDE.
- #29 pyfa's gaps are not the game's rules, and a control must change something.
- #22 Auditing pyfa: missing attributes, split bonuses, unpublished hulls.
- #27 A reference that swallows errors like pyfa hides its own gaps.

**Calculations: expected values, fixtures and golden fits**

- #3 Checking the tool against itself.
- #6 Trimmed golden-fit records hid effects.
- #37 A fixture built from the code's assumption agrees with the code.
- #9 Comparing different quantities with pyfa.
- #10 Different game data versions.
- #61 A golden fit that tests an input must set it to something the default wouldn't give.
- #40 A ranking metric that leaves out what the pick is for.
- #78 A number can be exactly right and still mislead: check the assumption, not only the arithmetic.
- #108 Don't compute a precise answer from guesses stacked on guesses: show the facts it would be built from. See also #78.
- #81 Mock data must keep the real data's rules, or a check tests a case that can't happen.
- #83 A test double must replace the real thing, not fill in when it is missing.
- #71 A mock that accepts anything can't check what the feature adds.
- #65 New rows in an existing output reach every check that reads it.
- #66 A fetch every fit makes needs a shared fixture, served by every harness.
- #69 Per-copy inputs: keep each copy's place and each copy's state, on both sides.
- #70 A "skip" that a shared helper doesn't know about, and a cycle that isn't only the module's speed.
- #75 A weapon and its charge share a killmail flag: pick items by type, not by flag.
- #67 An input that is a Map reads as empty through Object.keys and JSON.
- #63 When a number is 0, show the cause the tool knows, not a guess about the fit.
- #53 An independent check's exclusions are where bugs hide.

**Calculations: implementing (pyfa's math, stacking, rounding, states)**

- #23 pyfa math and tool choices mixed together.
- #25 A locked "port" that wasn't, and pooling that lost three rules.
- #7 Wrong stacking penalties.
- #14 Counting the same bonus twice.
- #15 pyfa rules that are easy to get wrong.
- #17 One module, two kinds of effect (module states).
- #30 A name that resolves is an item, not necessarily the right kind of item.
- #34 JavaScript rounds a tie up; pyfa rounds it to even.

**The page: layout, controls and what people see**

- #33 Check a layout at a real phone width, with mobile emulation. See also #103.
- #103 A mockup shows the look, not the room: measure the real container before building to its numbers. See also #33, #46.
- #38 A new grid row under a sticky column gets covered when you scroll.
- #39 An override inside `:has()` lost to the general rule it was overriding.
- #44 A control that appears when a value changes moves the page.
- #45 Measuring a hidden element gives 0.
- #46 A pop-up checked in one place can open off the screen in another. See also #103.
- #55 Flex items are centred, not set on a baseline.
- #73 What's inside a closed <details> still has a box.
- #96 A scroll area inside the page must not trap the wheel; test scrolling with the mouse over it.
- #41 A mockup on a page the canvas doesn't open on.
- #87 Read a mockup's numbers, not only its layout.
- #42 A card's name typed in many places drifts apart.
- #43 A collapsed card that only updates while it's open.
- #48 Moving text into a hover hides it from checks that read the page.
- #49 Two controls for one setting: one owner, both redraw from it.
- #50 A choice that can become impossible: keep it, mark it, say why.
- #52 An input's value attribute is where it started, not where it is.
- #56 A rename changes what people see, not where their data lives.
- #60 A marker the checks wait on is a contract: new text in that element must not contain it.
- #79 Removing an element removes everything it did, not only what it showed.
- #84 One state, one control: a switch shown on every tab needs no twin on the page it controls.
- #86 A partial redraw must cover everything that can change while it is the only redraw.
- #95 Put a control where people look for it, and don't let a number say something it doesn't.
- #97 A limit the user can't see reads as a bug: name it where they set things.
- #101 A component's border shorthand quietly cancels the site's focus rule: measure each state, then write the rule down and check it.
- #104 escapeHtml() doesn't escape quotes: a value in an attribute needs `&quot;`.
- #107 One meaning drawn twice drifts: draw it once and use it everywhere. See also #42.
- #109 A `1fr` column beside fixed and `auto` ones can shrink to nothing: sweep every width the layout spans. See also #103.
- #110 Don't make people pick from a list that is still moving: freeze what they choose from, in a place that holds still.
- #111 A lookup that ignores capitals turns ordinary words into people: match what the person typed, not just the letters.

**Checks and test machinery**

- #12 `node --check` passes, the page still breaks.
- #21 A renamed result field silently turned its pins into no-ops.
- #36 Code that runs at page load also runs inside the regression suites.
- #47 One wrong anchor stops a whole patch.
- #51 A collision rule passes trivially when nothing collides.
- #54 "Never" is a time too: give Infinity its own branch.
- #57 "Execution context was destroyed" wasn't a navigation: read the protocol log.
- #58 A pipe write is asynchronous: don't exit right after it.
- #72 A tab a browser extension opens isn't routed on its first load.
- #74 A request log shared by several pages counts the other pages' work too.
- #77 A failure case leaves state behind: the next case in the same page inherits it.
- #80 A check that still passes after a change may never reach the change.
- #82 A lint's pattern can run for minutes on a long data string.
- #94 Guard a whole class of failure with a check on the code, not only a test of today's case.

**Intel and live data (chat logs, zKillboard's feed)**

- #85 A list kept in arrival order isn't in time order.
- #88 In free text, a word that is also a character's name is not a pilot until the domain says so.
- #92 Before fixing what a screenshot shows, read the line that produced it.
- #89 Check a live service's edges from where the page runs before writing its test double. (Its 404-without-header case is gone since 2026-10-29; the advice stands.)
- #93 A hidden tab's timers fire late and together: pace a rate-limited service by the clock, in a worker. (The "holes" part was removed in v2026.10.29.8; the pacing advice stands.)
- #98 A reader that waits for data must notice when it has waited too long; and a hard bug may need a recording, not a probe. **Superseded by #102** (the gaps were a cache, not missing numbers; read ahead no more).
- #99 A look-ahead at fixed spots can miss every time: to cross a gap of unknown shape, read through it. **Superseded by #102** (same).
- #102 When a client that works reads the same source, find what differs before tuning your workaround again.
- #100 A warning that fires on a routine event teaches people to ignore it: check the thing itself, out of their sight.
- #105 A reader that decides a word's kind before its lookups can't use what they say: decide after. See also #88.
- #106 A rate guard must stop at the first refusal, stay stopped, and count what it granted. See also #93, #94.

**Delivery, privacy and the repository**

- #13 "Delivered" wasn't delivered.
- #90 A public repository keeps everything you save in it: check every saved file for personal data, pictures included.
- #91 Before handing over a history rewrite, run its replacement list on the cleaned tree first.

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
- **How it was caught:** the owner's pyfa screenshot of a constructed Thanatos fit:
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
    would have built a Pilot Analyzer path with no data behind it; the owner decided to keep it off
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
  reads the SDE directly, so it had the booster too; only the owner's real pyfa showed the gap.
- **Do this instead:**
  - Treat `db_update.py` as part of pyfa: it filters, renames and patches the SDE (also the T3C subsystem
    slot count, forced publish flags in `service/market.py`). `pyfa_sde.pyfa_removed_types()` mirrors the
    removals; the generator, the oracle and the tool all use it (`PYFA_REMOVED_IMPLANT_IDS`).
  - A count in pyfa's UI that differs from the paste (Boosters (2) for three lines) is a finding, even when
    every stat on screen looks plausible.

## 33. Check a layout at a real phone width, with mobile emulation

- **What happened (v2026.10.14.15):** the owner reported the tool was "difficult to see and read on mobile". Every
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
  - Test with the longest real strings (v.17, the owner: "test how large strings will affect layout"): the
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
  for it, so ACTIVE changed no number on any card, and the owner pointed out that a user who sets it
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
  - The `ishtar_zkb137694046` fixture had no **group** record for its X-Large
    Shield Booster, so the engine dropped the module entirely. For months
    the pin said capacitor stable 96.9% while the real page and the owner's pyfa
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
  The canvas opens on its first page, so the owner saw the old phase-1 boards and asked whether he had the wrong file.
- **Do this instead:** when you add boards to an existing canvas, either set its `launch` to the new page or name
  the page in your message ("open the page list, pick X"). Before saying what a mockup shows, render the board
  files yourself (strip the canvas markup, Playwright screenshot) and send the images too; the user then has the
  options even when the canvas view goes wrong.

## 42. A card's name typed in many places drifts apart

- **What happened (fixed v2026.10.14.45):** each card's title was a string passed by hand at every call
  (`cardLabelHtml('dmg', 'Their damage on you')`), and notes, tooltips and ERROR_CODES typed the names again. Over a
  few builds they disagreed: "Navigation & targeting" vs the agreed "Navigation & Targeting", a Capacitor note
  pointing at an "EWAR card" whose title is "EWAR / Misc", error codes naming a "last-kill box" and a "threat / my
  ship switch" that no longer existed. The owner: "subtext and explanatory info referencing card titles that should be
  interchangeable."
- **Do this instead:** name each card or page part once, in `CARD_NAMES` (roadmap/card-names.md has the same
  table), and refer to it by key: `cardName('dmg')` in text, `cardLabelHtml(key)` / `collapsedCardHtml(key, summary)`
  for titles (they take no title), `{card:dmg}` in ERROR_CODES. `tools/check_card_names.py` (update-check chain)
  reads every string the page can show and fails on a name typed by hand, a "<Name> card" that isn't a listed name,
  an old name, or a key that doesn't exist. When you rename something, add the old name to its `RETIRED` list.
- **A trap found on the way:** `${cardName('fit')}` inside a `'...'` string is printed literally, and in a `'...'`
  string that also contains `'fit'` it is a syntax error that stops the whole script (the regression suite caught
  it). Use backticks for any string with `${...}`; the check flags `${cardName(` inside quotes.
- **Again (v2026.10.14.95), a rename:** "Your Side" became "Standings" with one line of `CARD_NAMES`. Retiring the old name
  lower-cased would have flagged ordinary prose ("your side's losses"), so `check_card_names.py` gained `RETIRED_EXACT`,
  matched as written. Retire a name whose words are also plain English by its exact spelling.

## 43. A collapsed card that only updates while it's open

- **What happened (fixed v2026.10.14.47, found by the owner):** the Damage Application card's collapsed row showed a
  headline cached from the last time the card was drawn open. The refresh after a change ("Use in assessments" off,
  a new saved ship, a preset) only redrew cards that were open, so a collapsed card kept its old numbers ("still
  shows old text (out of sync w/ user's change)"). On a phone, where the card starts collapsed, the row never had
  numbers until it was opened once.
- **Do this instead:** anything a collapsed card shows is computed from the same inputs as the open card, and the
  refresh path covers both states (`dmgFillCollapsed`, `dmgRefreshAll` refills every card). When you add a refresh
  hook, ask what else on the page displays that value: a collapsed row, the Firepower link, the Matchup. A page
  check that changes an input while the card is collapsed catches it; one that only tests the open card doesn't.

## 44. A control that appears when a value changes moves the page

- **What happened (fixed v2026.10.14.48, found by the owner):** the Damage Application card showed a "Reset to my
  ship" button only once a setting left its default. The button's row was taller than the title row without it, so
  the first touch of any slider made the card 16 px taller (42 px on a phone) and pushed every card below it down.
  The owner: "numbers change on multiple cards which causes the content to shuffle and move elements on the page".
- **Do this instead:** anything that can appear while the user is working keeps its space from the start. Show
  the control disabled rather than hidden, and give live numbers a box as wide as their widest possible value
  (`numBoxStyle`). Then measure it: `tools/page_checks/no_shift_check.py` uses every control and fails if a covered
  card moves more than 1 px. A screenshot can't show this; only a before/after measurement can.

## 45. Measuring a hidden element gives 0

- **What happened (fixed v2026.10.14.48, from the owner's screenshot):** the Damage Application card decides whether its
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
- **Again in v2026.10.14.52 (the owner's screenshot: "info panel clipping bottom edge of the matchup bar"):** the same
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

## 51. A collision rule passes trivially when nothing collides

- **What happened (v2026.10.14.54, chart markers):** the chart drops a round tick number that would touch a marked
  value (your range, their scram). The first "no axis numbers touch" check passed, and still passed with the
  dropping switched off: at the default settings no marked value sat near a tick, so there was nothing to drop.
- **Do this instead:** put the case that collides into the test on purpose (here: your range set to exactly 20 km,
  a round tick, and to their scram distance), then switch the rule off in a copy of the page and see the check fail
  (`damage_chart_check.py`, `markers_at`). The same goes for any "nudge apart", "merge equal labels" or "clamp
  inside" rule: test it where it has to act, and prove the check bites with a mutation.
- **Mutate the whole behaviour, not one branch (v2026.10.14.55):** turning off only the strip's fast path to your
  card left its fallback (a full refill) in place, which was also right, so the check still passed. That pass
  says nothing about the check. Remove everything that delivers the behaviour, then see the check fail.

## 52. An input's value attribute is where it started, not where it is

- **What happened (v2026.10.14.55):** a check read a range slider with `get_attribute('value')` after the page had
  moved it, got the value it was drawn with (4400) instead of the current one (5000), and failed a correct page.
- **Do this instead:** read the live value as a property (`el.value` in `evaluate`, or `input_value()`), and the
  same for `checked`. The attribute only says what the HTML said when it was written.
- **Also (v2026.10.14.56):** a range slider's `step` rounds whatever is written into it: with 500 m steps the default
  4.4 km silently showed 4.5 km. Keep the step as fine as the values the page writes (here 100 m), and derive a shared
  value's limits once (`dmgFightRangeMax`) instead of in each view; three copies had drifted.

## 53. An independent check's exclusions are where bugs hide

- **What happened (v2026.10.14.57):** `check_matchup.py` compared the Matchup's "you last" / "they last" against an
  independent build of the rule, and passed for weeks, but it left out every fit with an Ancillary Shield Booster
  ("an ancillary booster's rate isn't a plain amount / duration"). The owner's first real ASB matchup showed the rule was
  wrong for them: it stopped the ASB when the capacitor ran dry (an ASB on charges needs none) and never reloaded it.
- **Do this instead:** when a check skips a case because it isn't simple, write down what it skips (in the check's
  output, not only a comment) and close it next, or check that case another way before trusting the number there.
  A user's own fits are the best test cases: keep them in the repo (`tools/independent_checks/fits/`) and check them.

## 54. "Never" is a time too: give Infinity its own branch

- **What happened (v2026.10.14.58, caught before delivery):** the "why" panel asks what each repairer was doing when a
  layer broke, by comparing the break time with the capacitor's empty time. For a layer that holds, the break time is
  `Infinity`, so every capacitor-run repairer looked switched off, and the words read "Your capacitor runs dry at
  Infinity:NaN:NaN" and "Nothing gets through your armor's resists", for a ship that holds because its repairers run
  for ever.
- **How it was caught, twice:** a hand-worked case for every kind of sentence in the regression suite ("holds with a
  repairer"), and `check_matchup.py` scanning 94,208 explanations for "NaN" and checking each printed time against
  its own layer ends (16 pairs failed).
- **Do this instead:** when a rule built for a moment (`t < capSec`) is reused at the end of something that may never
  end, write the never-ending case on its own line (holding: only what runs for ever counts). Test it by name, and
  scan generated text for `NaN`, `undefined` and `Infinity`.
- **Also:** CSS margin isn't a space. "Threat" in its own span next to "Weaknesses" looked right, but the text read
  "ThreatWeaknesses" (what a screen reader names the button). Put a real space between words in separate spans.

## 55. Flex items are centred, not set on a baseline

- **What happened (v2026.10.14.58, the owner's screenshot "alignment issue"):** the open Weaknesses card's toggle is an
  `inline-flex` button with `align-items: center`. "Threat" / "Your" (small capitals) and "Weaknesses" (13 px) became
  two flex items, each centred on its own, so the small word sat 1.5 px above the name's baseline. The collapsed row
  looked right because there the words were inline in one span. No check measured it.
- **Do this instead:** words meant to read as one line go in one inline box (here `.cc-name`) so they share a line
  and a baseline. To check alignment, compare baselines, not boxes: a text's Range rect bottom less its font's
  descent (canvas `measureText(...).fontBoundingBoxDescent`). A 0x0 probe placed after the text gives the baseline
  only in an inline context; next to a flex item it becomes a flex item itself and reports the centre.

## 56. A rename changes what people see, not where their data lives

- **What happened (v2026.10.14.60, the rename to EVE Threat Assessment):** the old name is also in the browser
  storage keys (`dscanMyShip`, `dscanDmgPreset`, `dscanFitView`), the item cache database (`dscan-tool-cache`), the
  repo (and so the GitHub Pages address) and many file names. Renaming those would have wiped every user's saved
  ship and cache and broken links, for no visible gain.
- **Do this instead:** rename the visible text only, say in a comment where the old name stays and why, and check
  that data saved before the rename is still read after it (`header_check.py` saves a ship, reloads, finds it).
- **Also:** to check that two things don't overlap, measure what's drawn. The header's `h1` box spans the whole
  width, so it always "overlapped" the version tag; the text's own Range rects are what can collide.

## 57. "Execution context was destroyed" wasn't a navigation: read the protocol log

- **What happened (v.51 to v.60, fixed v2026.10.14.61):** page checks stopped now and then with Playwright's
  "Execution context was destroyed, most likely because of a navigation", always on a `page.evaluate` that built a fit
  and drew it as Pilot losses (parseEftFit, estimateHpAndDps, renderFitTabs). It was written off as a browser hiccup
  for ten versions: reruns passed, and logging navigations, loads and crashes showed nothing.
- **How it was found:** a new check reproduced it every time. Running with `DEBUG=pw:protocol` showed what Chrome
  had actually answered: `{"error": {"message": "Promise was collected"}}`. The promise the evaluate waited on was
  garbage collected while the page drew a big fit synchronously inside it; nothing navigated (the page's own state was
  intact afterwards). Starting the same function from a timer and polling for its result never failed.
- **Do this instead:** `esi_from_sde.run_async(page, fn, arg)` for page functions that build and draw a fit. More
  generally: when a tool's error message guesses at the cause ("most likely because of a navigation"), get the raw
  answer underneath (the protocol log, the HTTP response, the exception's original message) before calling it a
  flake. A flake that only ever happens at one kind of call is not random.

## 58. A pipe write is asynchronous: don't exit right after it

- **What happened (v2026.10.14.61):** `eft_engine.py`'s Node side wrote its whole result as one line, then called
  `process.exit(0)`. With more fits the line passed 64 KB and was cut off: Python failed with JSONDecodeError
  "Unterminated string". It had worked for months because the output had always been small.
- **Do this instead:** exit in the write's callback (`process.stdout.write(text, () => process.exit(0))`), or let the
  process end on its own.

## 59. A handler's source value is the source's MODIFIED attribute: a script changes it

- **What happened (found v2026.10.14.64, there since v2026.10.14.40):** the drone (and new fighter) handler rows read
  the carrying module's RAW attribute (`m.attr`). pyfa reads `src.getModifiedItemAttr(...)`, and a script loaded in
  the module changes exactly those attributes: an Omnidirectional Tracking Link with an Optimal Range Script doubles
  its drone range / falloff bonus and zeroes its tracking and explosion bonuses. So a scripted link gave drones its
  UNSCRIPTED bonuses. Nothing caught it: every golden drone fit had an unscripted link.
- **How it was caught:** the new fighter fits were built to reach every handler on the generated list, scripts
  included (LESSON #53); the scripted link failed `check_application.py` at once. A drone twin
  (`vexor_constructed_scripted_omni_link_drones`) then failed the old page too.
- **Do this instead:** when a generated row says "value from the carrier's attribute X", feed it the carrier's
  attribute after its own charge / script and self effects (here `ewarAttrsFor(m, script)`), per copy, scripted
  copies first. When building golden fits for a handler table, give every module that takes a script one scripted
  copy.

## 111. A lookup that ignores capitals turns ordinary words into people: match what the person typed, not just the letters

- **What happened (v2026.10.31.4):** Intel looked up every word left over in a report as a pilot's name, and ESI's name lookup
  ignores capitals. EVE has characters named after almost any word, often alts in starter corporations. The owner's reports showed
  the result: "Kill: <pilot> ..." made "Kill" a pilot; "Gate Drag Bubbled Cormorrant Navy Fleet +9 Gate is hot" and "proc tackled in
  the medium ark by the <group> rats" sent "DRAG", "Navy", "HOT", "Proc", "MediuM" and "Rats" to the System Analyzer; "linked to ess
  223m" made "Linked" a pilot ("linked" should not have been resolved as a pilot name"). Each wrong pilot also raised the row's count.
- **Do this instead:** a single word typed by hand is a pilot only in the name's own capitals; words a report is made of (kill,
  linked, drag, hot, tackled, rats, navy ...) are never a pilot unless dragged in from chat ('*'); an amount ("223m") is not a name;
  a ship name one letter off is still that ship, so its words aren't left over to become people. Test with made-up characters named
  like those words (`intel_words_check.py`). Players also shorten a corporation or alliance to a word everyone knows; when a character
  has that name in the same capitals it is still read as that pilot, until Intel learns those shorthands (backlog).

## 110. Don't make people pick from a list that is still moving: freeze what they choose from, in a place that holds still

- **What happened (v2026.10.30.4 → v2026.10.31.2):** a Near You badge for several kills opened that row on Intel to list them, each
  with its own Fleet ▸. Intel redraws as reports and kills arrive, Near You re-sorts by distance and the Feed scrolls beside it. The
  owner: "this is not very intuitive or easy to read with a constantly changing list on both sides of the page"; "move the 'which
  kill to analyze' decision to the fleet tab".
- **Do this instead:** when a choice is offered from live data, take a snapshot when the person asks and show it where nothing else
  moves (here `fk.picks`, listed in the Fleet tab's header, "as they were when you opened this"); open the likeliest one at once (the
  newest) so a pick is only needed to change it. One control per action: the kill's label is the button; a second button doing the
  same was dropped (#84).

## 109. A `1fr` column beside fixed and `auto` ones can shrink to nothing: sweep every width the layout spans

- **What happened (v2026.10.31.1, the owner: "text wrapping issue ... it's pretty annoying", a window about 1290 px wide):** Near
  You's row is one grid line: the jump count (62 px), the system (as wide as the widest system name), the word (`minmax(0,1fr)`), the
  time and the kill badges (`auto`, the badges with a 118 px slot so times line up), the toggle and Assess. The word got what was
  left. With the page's real system names and the Intel card split in two (about 900-1400 px) that was nothing, and "2 neutral" stood
  one letter a line. `intel_layout_check.py` measured the layout at 1440 px and 390 px only, with a made-up table whose widest name is
  far shorter than the real one's.
- **Do this instead:** a column that takes what's left needs a floor, or the layout needs a second shape for when there's no room.
  Decide by measuring the real content in the real container, not by a window width (here `itNearFit`: the word kept on one line;
  wider than its column, the row stacks). Check every width the layout spans, with content as wide as the real data can be (here
  905-1700 px with a 160 px system column), not two widths and a short test table.

- **The same for a column's content (v2026.10.31.3):** a mockup of the Pilot Dossier's kills widened the gang column until "21
  pilots ›" fitted; the owner: "some killmails could have hundreds of pilots on the kill" ("1,248 pilots ›" is 119 px). Size a
  column for the largest value the data can hold, not the sample's; here the count alone under "Fleet size".

## 108. Don't compute a precise answer from guesses stacked on guesses: show the facts it would be built from

- **What happened (v2026.10.30.4 → v2026.10.31.1):** the Fleet tab's Against This Fleet worked out how long the victim, then your
  ship, would last against the fleet on a kill, and how long you'd need for each of them. Every pilot's fit was a guess (their latest
  loss in that hull, or their alliance's common fit), and the whole fleet was put at one range. The owner, testing it: "it's not as
  intuitive as i'd like"; "each ship in that fleet is going to be trying to be at their optimal range so i just dont know how
  realistic this is"; "given the fluidity of ranges in fleet battles, we probably should not be giving a time to kill numbers." The
  numbers were exactly what the engine gives for those inputs (#78), and the inputs were the problem.
- **Do this instead:** before building a number, count the guesses under it (here: the fit, the range, each ship's movement, all
  times every ship). When the answer depends on choices the players make in the fight, show what each guess rests on instead (here
  each fit's DPS, damage mix, weapon range and what its tackle reaches) and leave the conclusion to the reader. A one-on-one with a
  fit read from its own killmail is different: there the Matchup keeps its numbers.

## 107. One meaning drawn twice drifts: draw it once and use it everywhere

- **What happened (v2026.10.30.4, the owner: "i really want to see the standings icons ... implemented with this delivery. right now,
  hostile and friendly look ok but neutral is just wrong"):** standing had two drawings. The System Analyzer's `SIDE_MARK` (v.81: a red
  square with −, a blue one with +, an empty circle for neutral) and Intel's EVE-style icons (v.100: a star for your corporation and
  alliance, +, =, −). Each was right where it was made; side by side on the new Fleet tab they disagreed, and neutral read as "nothing".
- **Do this instead:** when a second place needs a meaning the page already draws, call the first drawing (here `standIcon` /
  `standMark`), don't draw it again. When two drawings exist, merge them into one before adding a third use, and keep the classes the
  checks read (`sa-mark h / n / f`). Same family as #42 (a card's name typed in many places).
- **And check what the shared drawing carries:** Intel's icon carried a `<title>` (its only label, beside a pilot's name). Put beside
  the word "Hostile" in the System Analyzer, that title became text: the key read "HostileHostile 54" (`system_analyzer_check.py`,
  unchanged, caught it). A drawing reused where its meaning is already written goes in as decoration (`standIcon(k, true)`,
  `SIDE_MARK_BY_WORD`: no title, `aria-hidden`).

## 106. A rate guard must stop at the first refusal, stay stopped, and count what it granted

- **What happened (v2026.10.30.3, the owner: "what happens if someone opens multiple browser tabs ... and turn intel on"; then a
  screenshot of zKillboard's developer: R2Z2's limit cut to 15 a second, an automatic 1-hour ban, and the limit cut further if
  abuse continues):** the live-feed reader paced itself (10 a second) but had no idea what to do once refused. A read-back queued
  28 requests at once; when one failed, the other 27 still went out. After an error it tried again in 30 s, 1, 2, 4 and 5 minutes,
  all inside an hour-long ban. Nothing coordinated two copies of the page. The first tripwire written for the fix counted when the
  code after the gate ran, not when the gate let a request through: on a busy page two turns ran close together, it counted 6 in
  a second and stopped a healthy reader within seconds. `intel_kills_check.py`, run unchanged, caught it.
- **Do this instead:** send every request to a rate-limited service through one function that (1) waits its turn, (2) checks a stop
  that is kept where every copy of the page sees it (here localStorage), (3) counts the start the gate granted and stops itself
  before the service has to, and (4) on the first "too many" answer stops for the service's full ban and drops what is queued.
  Treat an answer you can't read in the middle of a burst as a reason to stop the burst. Keep the pace well under the published
  limit (here a third), from one constant. Test all of it against a stand-in that answers 429 on cue; never provoke the real one.

- **The same for zKillboard's API (v2026.10.31.2):** its pause after a failure (`zkbUnavailableUntil`) lived in memory, so a reload,
  the thing the error's "try again in a few minutes" invited, started asking again at once. The pause is now kept in localStorage
  (`dscanZkbPause`), the text says reloading won't help, and every Retry for a zKillboard failure is `zkbRetryHtml`: disabled with
  a countdown until the pause and the budget allow a request (the owner: "we need a refresh / retry icon ... even if we need to
  add a timer").

## 105. A reader that decides a word's kind before its lookups can't use what they say: decide after

- **What happened (v2026.10.30.2, the owner's screenshot):** an intel line was three pilots and a system, and the first pilot's
  name is also a real system's. The reader found systems first and took any Title Case word that matched one; a word taken as a
  system was never looked up as a pilot, so the row was headed by a system 26 jumps away and the real one (13) became a second
  chip. The owner added that some players name their pilots this way on purpose, to slip past intel tools; the same trick works
  on every word list the reader keeps (a pilot named "Clear" would mark a system clear). The lookup that would have told the
  two apart ran after the decision.
- **Do this instead:** when a word could be two things, keep both readings until the lookups are back, then decide with
  everything known (here `itForce` then `itPlace`, after `itResolve`: what the words around it say, the ring, whether it's a
  pilot's name, then distance). Bias the tie-break toward the reading that warns; never toward the one that hides. In a check,
  make the mock answer for the ambiguous word (here made-up pilots named "Jita" and "Clear"), so a reader that decides early fails.

## 104. escapeHtml() doesn't escape quotes: a value in an attribute needs `&quot;`

- **What happened (v2026.10.30.1):** Near You's 3-line cap keeps each row's pilots and ships in a `data-it-cap` attribute as JSON,
  written with `escapeHtml(JSON.stringify(...))`. `escapeHtml` (a text node's innerHTML) escapes `&`, `<` and `>`, not `"`, so the
  first quote in the JSON ended the attribute: the page read `{` and the cap silently did nothing. The screenshots looked right
  because no test row had enough names to need the cap; the new layout check's 300-pilot gang caught it.
- **Do this instead:** for an attribute, escape the quotes too (`.replace(/"/g, '&quot;')`), or set it from script
  (`el.dataset.x = ...`). Test the case a feature exists for (here: more names than fit), not only the everyday one.

## 103. A mockup shows the look, not the room: measure the real container before building to its numbers

- **What happened (v2026.10.30.1):** the Near You and Feed layout was settled in a mockup 760 px wide. On the page at 1440 px,
  Near You's column is about 580 px, so the pilot and ship list (the column left after the jump count, the system name, the time,
  the badges, the toggle and Assess) was barely 100 px and wrapped into a tower. On a phone the Feed's header (jumps, system,
  time, label, toggle on one line) left the system name about 40 px and cut it to "Y…". Both were found by screenshots of the
  real page with made-up data, then fixed: the names run under the time and badges, and on a phone the time and label move to a
  second line and the lines below run the full width.
- **Do this instead:** before building a mockup's layout, read the real container's width at each breakpoint (the page's own
  columns, not the viewport) and check the mockup's fixed columns against it. Mock up at that width, and screenshot the built page
  at desktop and phone widths before handing it over.

## 102. When a client that works reads the same source, find what differs before tuning your workaround again

- **What happened (v2026.10.29.4-29.8):** Intel's kills went missing for a day. Three deliveries tuned a read-ahead past
  "missing" numbers (LESSON #98, #99), and each failed live, while RIFT read the same feed without trouble. The numbers were
  never missing: Cloudflare, in front of R2Z2, kept a separate copy per website (per `Origin`). Our site got a day-old
  `sequence.json` and, for about an hour, a remembered 404 for any number it asked for before it was published. Reading ahead
  of a live feed created exactly those 404s, so each fix made it worse. A controlled test settled it: one number asked for
  early from our site stayed unreadable there after publication, while the next one, not asked early, read fine. zKillboard's
  developer then fixed it at Cloudflare. The first attempt removed the `Origin`, which also dropped the permission header (CORS)
  every browser needs, so every web page went blind while curl and desktop apps still read fine.
- **Do this instead:** when another client reads the same source correctly, list what differs between its requests and
  yours (headers such as `Origin`, cookies, timing, path) and test the source with only that one thing changed, before
  adding more logic. A "missing" answer can be a cache's memory, and asking too early can create it. Read a feed the way its
  docs and a working client do. Test a header change at the source from a browser on your own site: curl skips CORS. Give
  "the browser may read nothing" its own error code (INTEL-06), so it can't pass for a quiet night.

's border shorthand quietly cancels the site's focus rule: measure each state, then write the rule down and check it

- **What happened (v2026.10.29.7, the owner: "would you mind taking a look at how text input boxes are being treated
  differently as well (differing border colors)"):** reading the CSS suggested one text-field style. Measuring the computed
  style of every field at rest and focused, in the page, found three: the main fields turned amber-dim on focus, the Intel
  search showed the browser's own ring, and Intel's selects showed no focus at all. Their rules (`.it-fbar select`,
  `.it-box select`) set `border:` as a shorthand, and being as specific as the global `select:focus` and later in the
  file, they reset its border colour. The tags, switches and sliders had drifted the same way (two copies of one switch,
  four corner radii, the browser's own slider).
- **Do this instead:** inventory a control by its computed style in every state (rest, hover, focus, disabled), not by
  reading the CSS. Write the state rules once, after the component rules, and name the components' own selectors in
  them. Once the owner settles a look, write it down (CLAUDE.md "UI rules") and check it both ways: statically
  (`tools/check_ui_rules.py`, in the chain) and in the real page (`tools/page_checks/ui_rules_check.py`). A value only
  code sets (a slider's fill, `--p`) needs a hook wherever the value changes: input events, new elements (a
  MutationObserver), and code that sets `.value` itself.

## 101. A component's border shorthand quietly cancels the site's focus rule: measure each state, then write the rule down and check it

- **What happened (v2026.10.29.7, the owner: "would you mind taking a look at how text input boxes are being treated
  differently as well (differing border colors)"):** reading the CSS suggested one text-field style. Measuring the computed
  style of every field at rest and focused, in the page, found three: the main fields turned amber-dim on focus, the Intel
  search showed the browser's own ring, and Intel's selects showed no focus at all. Their rules (`.it-fbar select`,
  `.it-box select`) set `border:` as a shorthand, and being as specific as the global `select:focus` and later in the
  file, they reset its border colour. The tags, switches and sliders had drifted the same way (two copies of one switch,
  four corner radii, the browser's own slider).
- **Do this instead:** inventory a control by its computed style in every state (rest, hover, focus, disabled), not by
  reading the CSS. Write the state rules once, after the component rules, and name the components' own selectors in
  them. Once the owner settles a look, write it down (CLAUDE.md "UI rules") and check it both ways: statically
  (`tools/check_ui_rules.py`, in the chain) and in the real page (`tools/page_checks/ui_rules_check.py`). A value only
  code sets (a slider's fill, `--p`) needs a hook wherever the value changes: input events, new elements (a
  MutationObserver), and code that sets `.value` itself.

## 100. A warning that fires on a routine event teaches people to ignore it: check the thing itself, out of their sight

- **What happened (v2026.10.29.5, the owner: "Eve deploys patches very often. is there a way to automate the update so the
  user never has to see it?"):** since v.96 the Intel card showed an amber "EVE is on build N; the jump table was checked on
  M: a gate EVE added since may be missing" after every EVE patch, because it compared build numbers. Patches seldom touch
  stargates; checked that day, the new build's 13,978 gates made exactly the page's 6,989 connections.
- **Do this instead:** compare what matters (here the gate connections), not a proxy that changes for other reasons (the
  build). When the check needs data the page can't cheaply get, run it on a schedule where the data is (a GitHub Action
  reading CCP's published static data twice a day) and hand the owner a pull request only when something really changed.
  Test the automation on made-up copies of the real file layout when the real source can't be reached from where you work.

## 99. A look-ahead at fixed spots can miss every time: to cross a gap of unknown shape, read through it

> **Superseded by #102.** Reading through gaps was a workaround for a cache problem at zKillboard's CDN, fixed there on 2026-10-29.

- **What happened (v2026.10.29.5, the owner, the same afternoon: "it looks like that last kill feed fix didn't work"):**
  v.29.4, after a minute with no kill, looked at fixed numbers ahead (4-8, 12, 16, 24, 32, 48, 64, 128 ...). From 12:30 UTC
  zKillboard's numbers were patchy: 19 missing after where the page was, then missing ones between kills, and every fixed
  spot happened to be a missing one. The page sat 24 minutes with "no kill read". The cause came from the page's own state,
  which the owner read in his browser's console with a one-line snippet (seq, head, busy, reqs, holes, waits), plus the
  numbers probed by hand: no guessing.
- **Do this instead:** past a gap of unknown size and pattern, read every number in turn until a run of misses long enough
  to mean "the end" (here 32), then probe further with windows (8 in a row), not single spots. Back off when nothing is
  found anywhere, so a quiet source isn't hammered. Test with the pattern that broke it, including a check that the old
  build fails. When a user says a fix didn't work, ask for the program's own state first (a console line is enough).
- **And again (v2026.10.29.6), the same day:** v.29.5 read through 32; the owner's feed then had 40 missing in a row, and v.29.5's
  first window further on fell inside the gap. It had also backed off to a look every 4 minutes. Sizes taken from the gaps
  seen so far were outgrown within hours. Size limits from measurements of the live source over a longer stretch (here about
  4 in 10 numbers missing, runs up to 40), leave a wide margin (128), and keep the back-off short enough that a missed kill
  is still news (1 minute).

## 98. A reader that waits for data must notice when it has waited too long; and a hard bug may need a recording, not a probe

> **Superseded by #102.** The "missing" numbers were Cloudflare remembering early 404s; reading further ahead made it worse. Keep the first point (notice when you have waited too long), not the fix.

- **What happened (v2026.10.29.4, the owner: "i still have not seen a single killmail show up in the feed"):** v.103 read
  zKillboard's live kills by number and treated a missing number as a hole only when one of the next 3 answered. On
  2026-10-29 at 10:05 UTC four numbers in a row (100274284-287) were missing for good, with kills after them. The page read
  "nothing new yet", waited 6 s and asked the same four again, for 40 minutes, with no note. Its "far behind" check only
  ran after a kill was read, so it never ran. Gaps of 2 had been seen before, so v.103 fixed the gap it had seen, not the
  next one. Probes from a fresh start couldn't show it: a restart finds the newest kill again and works until the next gap.
- **How it was found:** the owner asked for a test over time. The page's own reader ran unchanged in the browser pane for
  40 minutes, slowed to at most 3 requests a second, logging every request and every kill and why it was kept or dropped.
  A kill he saw in RIFT was then missing from the log, and the log showed the reader asking the same 4 numbers since 10:05.
- **Do this instead:**
  - Don't size a look-ahead from the gaps you've seen. Give the reader a time limit instead: no kill read for a minute,
    look much further ahead (4 to 2048 past), and read forward from there.
  - Show the reader's health where the user looks: "last kill read N s ago", amber after 5 minutes. A stuck reader must
    not look like a quiet night.
  - Any recovery path must run whether or not data arrived; one that only runs after a success never runs when stuck.
  - When a bug comes and goes, record the real thing over time (paced well under the service's limit) rather than
    probing once from a fresh start.

## 97. A limit the user can't see reads as a bug: name it where they set things

- **What happened (v2026.10.29.3, the owner: "the kills in this RIFT feed are not showing up in the tool's Feed. Should it
  have?"):** since v.99 the page kept kills only within the alert range (or the Feed's Distance if wider), while chat reports
  showed at any distance. The rule was in the code and the info panel, but not where the alert range is set, so a kill 9
  jumps away was missing from a Feed that showed reports about the same system. The owner: "i didn't understand that kills
  were limited only to the Alert range."
- **Do this instead:** when a setting also narrows what is collected, give that limit its own control, named for what it
  does, beside the related settings. Here the gear has "Feed: kills within N jumps" next to "Alert: within N jumps". Before
  answering "should it have shown?", check the input against every rule that drops data; here that was the jump count from
  the page's own table. Don't stop at the rule you remember.

## 96. A scroll area inside the page must not trap the wheel; test scrolling with the mouse over it

- **What happened (v2026.10.29.2, users: "you can't scroll the page if your mouse is over any part of that card"):**
  v2026.10.14.15 made the Fit column sticky and, so a tall card could still be read, gave it `max-height: 100vh`,
  `overflow-y: auto` and `overscroll-behavior: contain`. A Fit card taller than the window then had its own scroll area:
  the wheel over it scrolled the card to its end and stopped (contain: no hand-off to the page). `layout_check.py`
  tested the column staying put through a state change, at a window tall enough for the test fit, and never turned the
  wheel over the card.
- **Do this instead:** avoid a scroll area inside the page unless it is a list meant to scroll on its own (a popup list).
  Pin a column only while it fits the window (here `.fl-pin`, set from its height by a ResizeObserver and on resize),
  and let a taller one scroll with the page. Test with the mouse wheel over the element at a short window and a tall
  one, and check that the page moved.

## 95. Put a control where people look for it, and don't let a number say something it doesn't

- **What happened (v2026.10.29.1, the owner, from other users):** v.97 moved Intel's on/off switch from the Intel card to the
  page header, so one switch worked from every tab. Other users opened the Intel tab and "didn't see how to turn intel
  on". Separately, every version from 2026-10-14 on was `v2026.10.14.N`: users took the date for the build's date and
  thought they had an old build.
- **Do this instead:** a control belongs where someone looks when they want it, which is usually where the thing it
  controls is shown. Show a status from anywhere if that helps (here, the "N near" pill), but don't move the control
  there. Anything shaped like a date is read as a date, so a version number carries the delivery's real date or none.

## 94. Guard a whole class of failure with a check on the code, not only a test of today's case

- **What happened (v2026.10.14.104, the owner: "if the tool were widely used and we deployed code that got the user's IP
  banned for any period of time, this would be bad"):** v.103 fixed the burst in the live kill feed, and its test
  covers that feed. A new request added anywhere else (another tab, a new lookup) could still bypass the pacing, and no
  test would notice, because each test only drives the code paths that exist when it is written.
- **Do this instead:** when a mistake would hurt the user beyond the page (an address blocked, data sent where it
  shouldn't go), add a check over the whole code that makes every new instance a decision. Here
  `tools/check_request_gates.py` lists every `fetch()` with the host it reaches and fails on an unlisted one, on a
  zKillboard request outside its two gates, and on timers staggered next to one; `request_gates_check.py` tests both
  gates with a hidden tab's bunched timers. Then break the gates on purpose (a new fetch, a bypass, a shorter spacing)
  and see the check fail.

## 93. A hidden tab's timers fire late and together: pace a rate-limited service by the clock, in a worker

- **What happened (v2026.10.14.103, the owner: "the intel feed is still not showing any kills"):** v.100 read back
  zKillboard's live feed in batches, starting 28 requests with timers 80 ms apart. In a hidden tab (the owner plays with
  the page behind the game) the browser runs timers late and together, so the 28 went out at once. zKillboard blocks an
  address that asks more than 15 times a second, for an hour, and then every file fails. Its feed also has numbers
  missing between kills: v.100 waited on a missing one for ever, and finding the newest could stop at one (an hour
  behind). The test double had neither: no holes, and timers that ran on time. Probing the live feed from the owner's
  browser to find this got his address blocked too, by the same burst.
- **Do this instead:** send requests to a rate-limited service through one gate that starts them one at a time, spaced
  by the clock (`Date.now()`), and time the waits in a worker, whose timers a hidden tab doesn't slow or bunch. Test with
  the page's timers made to fire every 2 s together, and count the requests in every second. Model the service's
  irregular data in the double (here, missing numbers) and never let one missing item stop a reader for good: look
  ahead, skip it, and ask again later. When probing a live service from the owner's machine, pace the probes too; they
  count against his address.

## 92. Before fixing what a screenshot shows, read the line that produced it

- **What happened (v2026.10.14.102, the owner's bug report: a screenshot of the Feed):** two rows had no system, and a
  report showed a pilot with a "Probe" ship chip. From the picture alone, "Probe" looked like the scanning-probes word
  read as the Probe frigate, and a fix was being planned for it. The intel line itself, read in the owner's log for its
  shape only, was `<system> <pilot> probe`, then `<system> clr` three seconds later: a pilot passing through in a Probe,
  read correctly. The rows with no system were `78 status?` and its bare answer `clr`.
- **Do this instead:** a screenshot shows the page's output, not its input. Find the input (the log line, the paste,
  the killmail) and decide from it what the page should have shown before changing the parser; a fix built on a
  guess about the input can break a reading that was right. Read real logs for their shape only and never save them.

## 91. Before handing over a history rewrite, run its replacement list on the cleaned tree first

- **What happened (v2026.10.14.101, after the owner rewrote the git history):** the replacement list for
  `git-filter-repo --replace-text` held every original D-Scan ship name from the two real pastes, mapped to its
  scrambled form. Some were short and generic: a cut-off hull name (its last word cut to one letter) got a new last letter. Literal rules match
  anywhere, with no word boundary, so the rewrite also turned `Prophecy Navy Issue` into `Prophecy Wavy Issue` in
  `index.html` (the Intel ship-name table and a comment) and in `regression_suite/dscan_parse_tests.mjs`, in every commit
  including the newest, and GitHub Pages served it. Found by comparing the owner's fresh clone with the delivered
  files after he finished; fixed by restoring the two files and dropping the rule.
- **Do this instead:** before giving anyone a replacement list, apply it the way git-filter-repo does (literals in
  order, then regexes, no word boundaries) to the already-cleaned files. The cleaned tree holds no personal data, so
  every match there is damage: drop or lengthen that rule until the run changes nothing. List only strings that are
  personal (names, paths, handles), not every string that once sat next to them. After the rewrite, compare a fresh
  clone with the delivered files (ignoring line endings) before calling it done.

## 90. A public repository keeps everything you save in it: check every saved file for personal data, pictures included

- **What happened (v2026.10.14.100, the owner: "that comment with my personal file location makes it pretty clear that
  we need to make that our first priority"):** the public repository held a comment with the owner's Windows user path,
  his first name about 1,600 times (quotes in comments, docs and test notes), his character names in test-fit IDs and
  labels, his alliance named from a screenshot, other players named from killmails and from his screenshots, and two
  real D-Scan pastes (186 custom ship names, many with pilot names: raw intel). Each was saved for a good reason (a
  quote of a decision, a fixture label, a real paste to test the parser), and nothing checked what was saved. The
  repository is served on GitHub Pages and the git history keeps every old version.
- **Do this instead:** before saving anything to the repository, ask whether it names or points at a person. Refer to
  the owner as "the owner"; label fixtures by hull and killmail ID, not by pilot; make test data up; read real logs,
  pastes and screenshots for their format only and never save them. A screenshot never goes in; a mockup shows the real
  page with made-up data, and each embedded picture is looked at before it is listed in
  `tools/pii_reviewed_images.json`. `tools/check_pii.py` refuses home paths with a user name, e-mail addresses, keys and
  tokens, image files outside the icon folders, unreviewed embedded pictures, and the personal names kept in the
  git-ignored `tools/pii_terms.local.txt` (a list of names must not itself be public). It runs in the chain and as the
  git pre-commit hook (`git config core.hooksPath tools/git-hooks`). Cleaning the files is not enough: the old
  versions stay in the git history until it is rewritten (git-filter-repo) and force-pushed. When replacing a list of
  names in bulk, replace only the full, distinctive strings: replacing every word of a pasted ship name rewrote
  `cargo` and `tackle` in the code before the diff was read.

## 89. Check a live service's edges from where the page runs before writing its test double

- **What happened (v2026.10.14.99, the owner: "are we actually capturing kills right now?"):** v.99 followed zKillboard's live
  feed (R2Z2) as its docs describe: read `sequence.json`, then each numbered file until a 404. Read from the GitHub Pages
  address on 2026-10-28, the real feed did two things the docs don't say: `sequence.json` was three hours stale (kills
  were already 3,000+ numbers past it), and a file not there yet answers 404 without the CORS header, so the browser
  reports a network error and the page never sees the 404. v.99 started three hours back, took ~10 minutes to reach
  live, then took every "nothing new yet" for the feed being down (INTEL-05, waits of up to 5 minutes). The check's
  mock answered `sequence.json` with the true newest number, and its header-less 404 reached the page as a plain 404:
  Playwright's `route.fulfill()` skips the browser's CORS check, so the double could never show the real failure (a
  mutant that treats a network error as "down" passed until the double aborted the request instead). The v.99 test of
  R2Z2 from the live origin had only read files that existed.
- **Do this instead:** before writing a double for a live service, probe its edges from the page's real origin: the
  missing item, the end of the list, an index or pointer it publishes, the headers on an error. Build the double from
  what came back (here: a stale `sequence.json`, a header-less 404). Know what the double itself skips: a fulfilled
  route is never CORS-checked, so a response the browser would block must be an aborted request in the double. In the
  happy path, check that the error note is absent; a check that only bounds a delay passes when the page is failing
  slowly. Then run a mutant that breaks the handling and see the check fail.

## 88. In free text, a word that is also a character's name is not a pilot until the domain says so

- **What happened (v2026.10.14.98, the owner's live use):** an intel line "<system> inside ess loki and curse <pilot> (Curse)
  <pilot> (Loki)" showed "Inside" and "ESS" as pilots. Every word the parser couldn't place went to ESI's name lookup,
  and EVE has real characters named "Inside" and "ESS". The made-up check lines never used such words, so nothing
  failed. The same line also counted Loki and Curse twice (named on their own and again in brackets).
- **Do this instead:** before a lookup that matches anything with a name, take out the domain's own vocabulary (places
  in a system: ESS, gate, station, structure names; intel shorthand; plain English filler). In a check, make the mock
  answer for those words (here "Inside" and "ESS" are mock characters), so a word list that misses one fails.

## 87. Read a mockup's numbers, not only its layout

- **What happened (v2026.10.14.98 mockup):** the Intel delivery 2 mockup was drawn from the real v.97 page with made-up
  lines. Its Near You row for 8WA-Z6 said "1 neutral, Vesna Dossier · Vedmak" one line after "5 hostile": Near You kept
  only a system's latest report, so a short follow-up line erased everyone reported a minute earlier. Nobody had
  noticed in v.96/v.97; the mockup's numbers showed it, and it became a question for the owner ("Everyone until clear").
- **Do this instead:** when a mockup runs on the real page, read every number and name in its frames as output to
  check, as a page check would. A frame that looks wrong is a finding, even when the frame is about something else.

## 86. A partial redraw must cover everything that can change while it is the only redraw

- **What happened (v2026.10.14.99):** so a focused search box keeps its caret, Intel redraws only its two lists while the
  Feed's filter bar has the focus. The notes above them (zKillboard not answering, INTEL-05) were left out of that
  path, so with focus in the bar the error never showed. `intel_kills_check.py` failed R2Z2 right after using the
  filters and caught it.
- **Do this instead:** when a full redraw gets a lighter path, list what the full one draws that can change on its own
  (lists, notes, badges, status) and give each a box the light path refreshes. Test the light path by leaving focus
  where it applies before the change.

## 85. A list kept in arrival order isn't in time order

- **What happened (v2026.10.14.98):** to keep Intel's Feed to the last 15 minutes, the first try dropped lines from the
  end of the list while the last one was too old. The list is in the order lines were read, not by their time (several
  channel logs, a log read from the start when Intel is turned on), so an old line in the middle stayed for good.
  `intel_assess_check.py` aged a line in the middle and caught it.
- **Do this instead:** to drop by time, filter by time; don't assume a list's order unless the code sorts it. In a
  check, age an entry that isn't at either end.

## 84. One state, one control: a switch shown on every tab needs no twin on the page it controls

- **What happened (v2026.10.14.96):** Intel got an "Intel" slider beside Standings (on every tab) and a "Watching" slider
  on the Intel card, wired as one switch. On the Intel tab both showed at once under two names, and the owner asked why there
  were two. The mockup had them both; nobody asked what each one was for that the other wasn't.
- **Do this instead:** when a mockup puts a control somewhere global, check every page it's already visible on before
  adding a local copy; one state gets one control (a second place may show the state, not switch it). v.97 kept the
  Intel slider and removed the card's.
- **Same delivery:** the "N near" pill sat inside the slider's `<label>`, and a press anywhere in a label presses its
  control: the owner turned Intel off thinking the pill was a button. Anything inside a switch's label is part of the switch;
  a badge that looks pressable gets its own element and its own action (here: open the Intel tab).

## 83. A test double must replace the real thing, not fill in when it is missing

- **What happened (v2026.10.14.96):** `intel_check.py` stubbed the File System Access API with
  `if(!window.__noFsApi) window.showDirectoryPicker = ...`, meaning "leave it out to test INTEL-01". But Chromium has its
  own `showDirectoryPicker`; leaving the stub out left the real one, so the "no API" case never happened and the check
  timed out waiting for an error the page was right not to show.
- **Do this instead:** when a check stands in for a browser API, assign it in every case (`= stub` or `= undefined`),
  never only when absent; and confirm the case the check means to test is the one that ran (here: `it.supported`).

## 82. A lint's pattern can run for minutes on a long data string

- **What happened (v2026.10.14.96):** `check_card_names.py` hung once the page carried `INTEL_JUMPS`, a 50 KB base64
  string. Its "<Name> card" pattern, `((?:[A-Z][\w&/]*\s?)+?) card`, backtracks without end on capital letters and `/`
  with no spaces, which is what base64 is. The lint was fine for prose and never meant to read data.
- **Do this instead:** generated data in the page is not text a person reads; lints that scan the page's strings skip
  long strings with no whitespace (`len > 400`, no `\s`). When a lint suddenly takes minutes, look for a new long
  string before suspecting the machine.

## 81. Mock data must keep the real data's rules, or a check tests a case that can't happen

- **What happened (v2026.10.14.94):** `fleet_kill_check.py` opened a fleet member (Rando, flying a Loki on the mocked
  kill) in the Pilot Analyzer and expected his dossier on the Loki. It came up empty: the mock gave him no kills at all,
  although he is an attacker on that very kill, and on zKillboard every attacker's kill list includes it. The page was
  right; the mock broke a rule the real data always keeps.
- **Do this instead:** when a mock adds a killmail, give it to everyone it involves (each attacker's kills, the victim's
  losses), or say in the mock why not. Before calling a failure a page bug, ask whether the mock could exist for real.

## 80. A check that still passes after a change may never reach the change

- **What happened (v2026.10.14.92):** the System Analyzer's pilot rows started picking the possible ship for a gang
  size. `pilot_rows_check.py`, `system_analyzer_check.py` and `vs_check.py` all passed at once, unchanged. Not because
  the new pick agreed with them: their mock pilots' kills each have one attacker (solo), and Auto put those pilots in a
  small gang (3 of their alliance in Local), so every row fell through to the old rule. The new path ran in none of them.
- **Do this instead:** when old checks pass untouched after a behaviour change, find out which branch their data takes
  before counting them as evidence; write a check whose data reaches the new path (here `sa_size_check.py`, from the
  dossier mock with kills in every size), and note in the old check which path it now covers. Same family as #77.

## 79. Removing an element removes everything it did, not only what it showed

- **What happened (v2026.10.14.90):** the Pilot Dossier's rows replaced the Pilot Analyzer's hull dropdown. The dropdown
  had also named the hull on the pilot line, with its class, *before* the fit was built. The replacement label was first
  written after `renderFitTabs`, so when the fit failed (ESI couldn't return the Loki's group: ESI-03) the pilot line stayed
  empty, and `renderFitTabs` overwrote the classed label with a class-less one besides. `ship_class_check.py`'s
  "no group from ESI" case caught it (a timeout, not a FAIL: it waited for the label).
- **Do this instead:** before removing an element, list its side effects (labels, focus, state other code reads) and
  where each will live now; put a label for "what was asked" before the step that can fail, and check the failure path,
  not only the happy one. Mutation `m6` (the label back after the fit) is caught by that case.
- **Again (v2026.10.14.91), the other direction: a new path into an old renderer.** The dossier's "no loss of theirs"
  fallback handed `buildLossFits` only `{km}`; the fit tabs also read `killmail_id` and `hash` (the loss row's "view on
  zKillboard" link, the share link), so the tab linked to `zkillboard.com/kill/undefined/`. The owner found it in use;
  `dossier_check.py` had checked the note, the DPS and the tab count, not the links. When a new path feeds an existing
  renderer, grep every field the renderer reads off its input and check each one on the new path.

## 78. A number can be exactly right and still mislead: check the assumption, not only the arithmetic

- **What happened (v2026.10.14.85, hidden in v.88):** "Against Your Ship" added up, for every pilot in Local, a guessed
  hull (from killmail history) with a guessed fit (from losses) into one verdict. `vs_check.py` proved every per-ship
  number matched the Matchup; the owner found it "inaccurate and even misleading" in use: "a lot of pilots simply fly a wide
  variety of hulls and/or do not get killed very often". The guesses compounded.
- **Do this instead:** before turning estimates into a verdict, ask how wrong each input can be and what one wrong input
  does to the answer; show how much of the answer rests on what's known (a ship on D-Scan) versus guessed, and don't give
  a verdict when that share is low. Checks of the arithmetic don't cover this; say so in the mockup.
- **Again (v2026.10.14.89):** the fleet view (v.83) read Local as a fleet: everyone in Local counted, the largest groups'
  hulls and fits added up. The owner, from a high-sec trade hub with 1499 in Local: "most of those pilots are docked up and
  likely not even flying a combat ship of any kind." Local says who is in the system, not who is undocked, in a ship, or
  in the fight; the summary covered 78 of 1468 pilots and still read as "their fleet". Switched off. Ask what the source
  really proves (here: presence, nothing more) before building a picture on it.

## 77. A failure case leaves state behind: the next case in the same page inherits it

- **What happened (v2026.10.14.87):** `affiliation_check.py` made zKillboard's stats answer 500 for one pilot, then
  gave a second pilot a wrong answer (`[]`) to see ZKB-05. The second case showed ZKB-01 instead: after the 500 the
  page's zKillboard queue waits before asking again (the D4 back-off), so the second request never went out. The page
  was right; the check's order was wrong. Worse, a later "zKillboard's stats aren't asked" check in the same page passed
  vacuously: the queue answered from its back-off without a request, so a mutant that did ask survived until that case got
  a page of its own.
- **Do this instead:** run each failure case in its own browser context, or put the ones that leave state behind
  (back-off, budget, caches) last, and say why in the check. Same family as #74 (a shared request log).

## 76. Before modelling an effect, find pyfa's handler for it: it may already say how

- **What happened (v2026.10.14.85):** "Against Your Ship" adds their neutralizers to your capacitor simulation. The
  first draft counted a neut only inside its optimal, at full strength: a rule made up for the card. pyfa already does this: its
  projected Energy Neutralizer / Nosferatu effects (Effect6187 / 6197) call `Fit.addDrain`, which feeds the capacitor
  simulation an incoming drain of amount × `calculateRangeFactor(optimal, falloff, distance)` (× the target's Energy
  Warfare Resistance and, for capital neuts, × min(1, signature / signature resolution)), cycle = duration, staggered.
  At 30 km the mock's Curse neut sits in its falloff: the made-up rule would have counted it at full strength.
- **Do this instead:** grep pyfa's `eos/effects.py` and `eos/saveddata/fit.py` for the attribute before writing a rule;
  port what's there (the engine already has `pyfaCalculateRangeFactor`), and put only what isn't ported in
  DEVIATIONS.md. The check writes the pyfa rule again on its own and tests a range where the falloff matters, so a
  mutant with the optimal-only rule fails.

## 75. A weapon and its charge share a killmail flag: pick items by type, not by flag

- **What happened (v2026.10.14.83, caught in review before the first run):** the fleet view rebuilds a common fit from
  the newest loss, giving each weapon the variant's most common charge. The first draft removed every high-slot item
  whose flag held a charge, to put the new charge in, which removed the weapons too: on a killmail the module and the
  charge loaded in it are two items with the same `flag` (see buildLossTally's highSlotByFlag note).
- **Do this instead:** remove or replace the charge by its type (the charge's `item_type_id` in that flag), never by
  the flag alone; and keep the original item (its quantity too) when it's already the right charge. The check builds a
  Loki loss with a different charge in its launchers so the swap really happens, and a mutant that drops the whole
  flag fails it (the pinned 801 DPS).

## 74. A request log shared by several pages counts the other pages' work too

- **What happened (v2026.10.14.82):** `pilot_rows_check.py` counts zKillboard requests to prove each pilot costs 2 and a
  batch stops at 30. The mock's log (`sa_mocks.ZKB_CALLS`) is one list for every page in the run. The check had just
  clicked a pilot row on the first page, which started the Pilot Analyzer there; its queued zKillboard request landed
  in the log after the check cleared it for the second page, and the count came out 31 instead of 30.
- **Do this instead:** when a check counts requests, count only the ones that belong to what it's testing (here: the
  `/kills/` and `/losses/characterID/` URLs of the pilots in that paste), or give each page its own browser context and
  log. Clearing a shared log doesn't stop work another page already has in flight (the zKillboard queue delays requests
  by design).

## 73. What's inside a closed <details> still has a box

- **What happened (v2026.10.14.81):** `system_analyzer_check.py` looks at 390 px for anything running off the page. It
  flagged the close buttons of three info panels (ⓘ) that were all closed. Chromium lays out the content of a closed
  `<details>` with `content-visibility: hidden`: nothing is drawn, but `getBoundingClientRect()` still returns a box, here
  the phone sheet's close button sitting past the right edge.
- **Do this instead:** in a check about what someone sees, skip what isn't shown with `el.checkVisibility()` (false
  inside a closed `<details>`, `display:none` or `content-visibility: hidden`), not just a zero width. The same goes for
  text read with `innerText` from an element that isn't rendered: it gives the raw text (the chip's phone-only ticker
  showed up in the desktop text until the check filtered with `checkVisibility()`).

## 72. A tab a browser extension opens isn't routed on its first load

- **What happened (v2026.10.14.80):** `extension_check.py` loads the extension into Chromium and lets it open the tool in a
  new tab, with the tool's address pointed at a made-up host that Playwright was told to answer. The tab showed Chrome's
  error page: a page the extension creates (chrome.tabs.create) starts loading before Playwright attaches, so its first
  navigation never reaches the route. The ESI and zKillboard calls the page makes afterwards are routed as usual.
- **Do this instead:** serve the page the extension opens from a real local web server (the check starts one on
  127.0.0.1 and sets that address in the extension's options), and keep routing only the page's own requests. Extensions
  also need Chromium's new headless mode (`--headless=new`, with headless=False in Playwright): the old one doesn't load them.

## 71. A mock that accepts anything can't check what the feature adds

- **What happened (v2026.10.14.79):** a shared killmail link carries the killmail ID and its hash, because ESI's
  /killmails/{id}/{hash}/ needs both. The page checks' ESI mock (from `last_kill_check.py`) answered any hash with the
  killmail, and its zKillboard stubs used made-up hashes ("h9100001"). A link with a wrong or cut-short hash would have
  passed every check.
- **Do this instead:** when a feature depends on part of an API's contract, make the mock enforce that part: here the
  mock answers 422 to a wrong hash, as ESI does, and the stubs carry real-looking 40-character hashes. Then check the
  failure on purpose (`shared_kill_check.py`: a wrong hash shows ESI-05, a cut-short link SHARE-02), and run a mutant
  that sends a slightly wrong hash to prove the check notices.

## 70. A "skip" that a shared helper doesn't know about, and a cycle that isn't only the module's speed

- **What happened (v2026.10.14.78):** bombs had been left out of the DPS since 2026-10-11 (counted as missiles they had
  got missile skills and no reactivation delay, >6x too high). Putting them back as pyfa counts them showed two traps:
  - the shared `is_weapon` helper of the independent checks matched bomb launchers too ("Missile Launcher Bomb"), so the
    pyfa side counted them while the tool skipped them, and the weapon loop in the engine still consumed the bomb
    launcher's copy count (it classes as a variable weapon), so the new bomb block saw nothing until the main loop
    skipped it explicitly;
  - pyfa's getDps divides by `getCycleParameters().averageTime`, which with reload off is the cycle PLUS
    moduleReactivationDelay: a Bomb Launcher's 10 s cycle is really 90 s at Bomb Deployment V (a first estimate that
    left it out was 725 DPS for a Hound's Shrapnel Bomb; pyfa's is 80.56).
- **Do this instead:** when an exclusion is lifted, grep every check for the helper that decided it (`is_weapon`,
  `weaponCategoryFromGroup`) and every loop that consumes the same copies; take a module's DPS cycle from pyfa's
  averageTime, reactivation delay included, never from its speed attribute alone.

## 69. Per-copy inputs: keep each copy's place and each copy's state, on both sides

- **What happened (v2026.10.14.77):** unloading a weapon makes copies of one weapon type differ (some empty and Online,
  some loaded and Active). The first pyfa pin for it, a Megathron with its first two blasters unloaded, showed two bugs:
  - in the pyfa stand-in (`golden_oracle.py`): an empty slot was skipped when pairing charges with copies, so pyfa got
    Void L in copies 1-5 and empty copies 6-7 -- a different fit from the tool's. v.76's Drake pin passed only because its
    empty slot happened to be the last one;
  - in the engine: a charge's capacitor need bonus (Void L +25%) was averaged over every copy of the weapon type, Online
    and empty ones included, so the five Active blasters drained 31.8 GJ/s instead of pyfa's 32.8 (Module.capUse is per
    module, and only an Active module uses any).
- **Do this instead:** when an input can differ copy by copy, line both sides up copy by copy -- every slot keeps its
  place (an empty one included), and every per-type sum or average counts only the copies in the state that matters,
  chosen the same way as the damage loop chooses them. Put the empty or inactive copy FIRST in a constructed golden: last
  is where a skipped one hides.

## 68. A new list of inputs exposes the engine to inputs no fit had: check every one against pyfa

- **What happened (v2026.10.14.76):** the Charges list offers every charge pyfa's getValidCharges allows, and its first
  check against pyfa (`check_charge_list.py`, 279 charges) found two engine bugs that 265 golden fits never reached:
  - a Civilian missile (it requires no skill) got Warhead Upgrades, the size skill and Ballistic Control Systems,
    1.51x pyfa: pyfa filters all of those on the CHARGE requiring Missile Launcher Operation;
  - two launcher types loading the same charge shared one range entry (it was keyed by charge alone).
  A third was in the state engine: a state request didn't say which copy, so a launcher set online by the user was
  not the one that stopped when the copies held different charges.
- **Do this instead:** when a feature lets the user pick from a list the fits never contained, run the WHOLE list
  through pyfa once (here every valid charge of seven weapon families), not a sample. Write the fixes' goldens from pyfa
  (`caracal_constructed_civilian_light_missiles`, `drake_constructed_mixed_charges_copy_states`). When pinning a value
  from the oracle, add only what pyfa counts: `module_dps` doesn't look at a module's state, so sum the active ones only
  (the first pin here summed an online launcher too).

## 67. An input that is a Map reads as empty through Object.keys and JSON

- **What happened (v2026.10.14.75):** the ring looked up each weapon's charge in `f.input.highSlotByFlag` with
  `Object.keys(...)`. The engine's builders make it a `Map`, so the lookup found no slots, and no weapon showed a charge;
  nothing threw. Dumping it with `JSON.stringify` for a look printed `{}`, which looked like "a paste has no flags".
  (Only the golden fixtures hold it as a plain object.)
- **Do this instead:** before reading an engine structure, check its type where it is built (`new Map()`), and accept
  both shapes when a value can come from either (`x instanceof Map ? [...x.entries()] : Object.entries(x)`). To look at a
  Map in a dump, convert it first. A page check that compares what is drawn with the input (`ring_track_check.py`: each
  launcher's charge in its own slot) catches the empty lookup; a check that only asks "is there a ring" doesn't.

## 66. A fetch every fit makes needs a shared fixture, served by every harness

- **What happened (v2026.10.14.73):** the generic Fighter tile fetches the same 12 fighters and 4 bombs for EVERY fit,
  whatever it flies. Each golden fit answers type fetches only from its own `types`, so all 263 fits would have failed
  with a 404, and copying 16 records into each fit would have added megabytes. (The missile catalog was copied into
  every fit in v.27; that was 14 small records.)
- **Do this instead:** put types the page fetches regardless of the fit in `regression_suite/shared_types.json`
  (written by `refresh_golden_fixtures.py --write` from the table in index.html, so it can't drift), and make every
  harness that answers fetches from a fixture fall back to it: grep `tools/` and `regression_suite/` for
  `universe\/types` (the escaped regex, which a plain grep for `universe/types` misses). A fit's own record still wins.
  Pin the new output on a few fits (here `fighterRec:<class>:<state>`), so a fixture that silently lost the shared
  records fails the suite.

## 65. New rows in an existing output reach every check that reads it

- **What happened (v2026.10.14.70):** support fighters' EWAR went into `estimate.ewarModules`, the list the EWAR card draws.
  The new checks for it passed, but the update chain's `compare_ewar.py` (which reads that same list) looked each entry up
  among the oracle's MODULES and failed 5 entries: "Dromi II not in the oracle fit". The check was right to fail; it just
  didn't know fighters.
- **Do this instead:** before the chain, grep `tools/` for the output field you added rows to (`ewarModules`,
  `application.projected`, ...) and run each check that reads it. Teach it the new kind of row with its own pyfa rule
  (here: the oracle launches the tool's squadrons; pyfa's ability handler x the squadron's fighters) rather than skipping
  the rows, then break the new code once to see that check fail.
- **Same rule for words (v2026.10.14.72):** `fighter_application_check.py` asserted the placeholder "Fighters aren't
  ranked yet."; when the picks learned fighters it timed out waiting for it. When a feature replaces a placeholder
  ("a coming update", "not ranked yet"), grep `tools/` for the placeholder text and change those checks in the same
  delivery.

## 64. A state gated on one variant's attribute silently drops the other variants

- **What happened (v2026.10.14.69):** the missile ranking's "prop module on" state was computed only when
  `boostedSignatureRadius` existed, and that value exists only for an MWD (its signature bloom). An afterburner fit has
  a boosted speed but no bloom, so it got no prop-on ranking at all, from v.27 to v.68. Nothing failed: no golden fit
  pinned a prop-on missile ranking on an afterburner fit, and the independent check skips a state the tool reports as
  absent. It surfaced only when the new Missile tile needed an "AB on" column.
- **Do this instead:** gate a state on what defines it (here: a prop module is fitted, `boostedSpeed`), and give each
  variant its own value (an MWD's bloomed signature, an afterburner's base signature). When a check skips a state the
  tool leaves out, also check that the tool should leave it out (`check_missile_application.py` now checks the prop-on
  signature per prop kind), and add a golden fit for each variant
  (`caracal_constructed_afterburner_missile_picks`).

## 63. When a number is 0, show the cause the tool knows, not a guess about the fit

- **What happened (v2026.10.14.68):** the owner's saved Nergal had its only gun set to Online. Firepower said "drones and fixed
  weapons only", Damage Application said "Your ship has no turrets...", and the Matchup showed a bare 0. All three were
  written for fits with no guns, and the reason the gun didn't count (its state) appeared nowhere.
- **Do this instead:** before writing a fallback sentence, list every way the number can reach that branch (no weapon,
  weapon not Active, no charge, out of range) and give each one its own words. The engine now lists
  `estimate.inactiveWeapons`, and each card names them.

## 62. A generated table covers only the attributes you listed: grep pyfa for every attribute your formula reads

- **What happened (v2026.10.14.67):** the hull damage table (`gen_hull_damage_table.py`) recorded handlers on a weapon's
  `damageMultiplier` and `speed`, but the Entropic Disintegrator formula also reads `damageMultiplierBonusMax` (its
  maximum spool-up). Three hulls double it (Nergal, Ikitursa, Babaroga), so the tool showed them at about 60% of
  pyfa's DPS since the disintegrators were added. No golden fit used those hulls, so nothing failed. It surfaced only
  because the check for a new feature (assumed charges) used the owner's pasted Nergal.
- **Do this instead:** for every attribute a DPS (or any) formula reads, grep pyfa's `eos/effects.py` for handlers that
  modify it, and make the generator record each one (or assert there are none). When a weapon system has hull-specific
  bonuses, add a golden fit on each of those hulls.

## 61. A golden fit that tests an input must set it to something the default wouldn't give

- **What happened (v2026.10.14.66):** the first Fighter bay golden fit asked for 2 Einherji squadrons, 1 Gram, 1 Dromi
  and no Siren. The default launch (damage first, then support) gives exactly that for this bay. A deliberate break that
  ignored the requested squadron counts passed every pin.
- **Do this instead:** for every input a fit pins (a state, a launch, a toggle), check that the default would differ,
  then break the code that reads it and see a pin fail. Here the fit asks for 1 Einherji squadron (the default puts 2
  out) and a Siren; the same break now fails 6 pins.
- **The same miss, one level down:** `dump_results.mjs` (which feeds the independent checks) didn't pass the new
  `fighterStates`, so `check_application.py` compared tool and pyfa both at the defaults and passed a break that
  dropped the MWD handler. A new input must reach every harness that runs the engine: grep for `estimateHpAndDps(`
  in `regression_suite/` and `tools/`.

## 60. A marker the checks wait on is a contract: new text in that element must not contain it

- **What happened (v2026.10.14.65):** the board's new ship menu ended in "Manage My Ships…". Five page checks wait for the
  Matchup's numbers with `!/…/.test(board.textContent)` (the board shows "…" while it works them out), so with the menu
  inside the board they waited forever. Hiding the half's own name with `visibility:hidden` also took it out of the
  button's accessible name and out of `inner_text`, and a `.x{color:transparent}` rule written earlier in the file lost to
  `.mys-sw-v{color:...}` written later (same specificity), so on a phone both names showed.
- **Do this instead:** before adding text to an element the checks read, grep the checks for the patterns they test
  (`…`, "holds", NaN). To hide text that must keep its size and its name, use `color:transparent` with a selector more
  specific than the rule that colours it, and measure that the overlay sits exactly on it (`my_ships_check.py` ALIGN).
- **Again (v2026.10.14.74):** the ship class added inside that hidden name is a span with its own colour, and
  `color:transparent` on a parent doesn't reach a child that sets `color` itself: the class showed twice on the board.
  Anything new placed inside a hidden twin needs its own transparent rule (`.mys-pick-ghost .hull-cls`); check its
  computed colour (`ship_class_check.py`).

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

- **What happened:** the owner's pyfa v2.66.3 had April data (client build
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
    280.3 s, which is the owner's pyfa number. The check was wrong, not the tool.
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
  matched the owner's pyfa screenshots and differed from the tool on 18 fits.
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
- **How it was caught:** comparing the owner's pyfa screenshots (262 vs 263,
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
  - The other way round (v2026.10.14.93): a page check that works out a value the page shows with `toFixed` (zKillboard's
    ISK, not a pyfa stat, so `paIsk`'s `toFixed` is right) must round the JavaScript way. `dossier_kills_check.py`
    formatted 51.25m with Python's `f'{x:.1f}'` (ties to even: "51.2") against the page's "51.3"; it now uses
    `Decimal(...).quantize(..., ROUND_HALF_UP)` on the exact value. A mismatch on a tie is the check's rounding first.
    Pin the reference unrounded and let `tolerancePct` do the comparing.
  - Again (v2026.10.14.96), and only on some days: `sa_size_check.py` worked out "N d ago" with Python's `round` against
    the page's `Math.round`. When the hours came to exactly 36.5 days (the mock's ages are offsets from the moment the
    check starts), Python said 36 and the page 37. Use `math.floor(x + 0.5)` for a value the page rounds with
    `Math.round`; a check that fails on one run and passes the next may be hitting a tie.

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

