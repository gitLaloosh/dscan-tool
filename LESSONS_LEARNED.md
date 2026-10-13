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

1. List every pyfa handler that touches the stat by **running** them with
   `tools/pyfa_effects.py`. For a table that already exists, run
   `tools/audit_effect_tables.py`. Never use grep or regex for this.
   → #1, #16, #19
2. For each source, note which **effect** carries it and which **attribute of
   the carrying item** holds the value. Never take a value from memory, trait
   text or a hand-made table.
   → #2, #4, #8, #11, #18
3. Treat earlier "fully checked, nothing found" claims as unproven until you
   have re-run the search yourself.
   → #5

**Phase 2 — Derive the expected numbers (still before writing code)**

4. Write or extend a script in `tools/independent_checks/`. Use pyfa's rules
   typed by hand and SDE values only. The script alone must produce every
   expected number.
   → #3
5. Build a constructed golden fit from full SDE records, through the real EFT
   parser, with slot pairing for charges and scripts. Run the suite and
   confirm the fit **fails** on the current build.
   → #6
6. If you are comparing with a pyfa screenshot:
   - split pyfa's number into its parts first
   - get pyfa's module states
   - check pyfa's game-data version
   
   → #9, #10

**Phase 3 — Implement**

7. Gate on dogma effect IDs and read the value from the item's own
   attribute. Keep group names only as a fallback for records without effects.
   When a count depends on module state, count per **effect**, not per item.
   → #2, #17
8. Copy `stackingPenalties` and `penaltyGroup` from the recorded handler
   call. Apply one `pyfaPenalizedProduct()` per penalty group.
   → #7, #15
9. When the new effect-driven path replaces an old one, switch the old one to
   fallback-only behind a flag.
   → #14

**Phase 4 — Verify and deliver**

10. Run `node --check`, the regression suite (ALL PASS, parse tests too) and a
    Playwright render of one affected fit.
    → #12
11. Diff the full output of the old and new builds over every golden fit
    (`diffall`). Explain and pin every change with a note. Re-run any table
    generator or audit script; it must be clean.
    → #1, #6
12. Bump the version tag. After writing to the user's machine, byte-verify
    every file.
    → #13
13. Record the lesson:
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
- **Do this instead:** generate hull bonus tables from the hull's
  `dogma_effects` (#1). If a hull record has effects, don't also apply the old
  hand table, or the bonus gets counted twice. See `weaponRangeViaEffects`.

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
- **How it was caught:** a fix changed a number you'd expect to change, or
  failed to change one you'd expect to.
- **Do this instead:** build fixtures from full SDE records, through the real
  `parseEftFit()` (`run_eft.mjs`) or a real killmail. Add slot pairing
  (`midSlotByFlag`, `highSlotByFlag`) whenever charges or scripts are fitted.
  If a fit didn't change when it should have, inspect the fixture's records
  first.

## 9. Comparing different quantities with pyfa

- **What happened:**
  - **Golem:** "4.8% low" compared torpedo-only DPS to pyfa's total, which
    included two smartbombs.
  - **Rorqual capacitor:** the delta depends on which modules are active in
    pyfa.
  - **Rorqual shield rep:** the gap was the pilot's boosters (drugs), not a
    bug.
- **Do this instead:** break pyfa's number into its parts first. Ask for the
  per-module values or a screenshot of module states before calling it a bug.

## 10. Different game data versions

- **What happened:** Erik's pyfa v2.66.3 had April data (client build
  3326071): 50MN MWD II with 200 GJ cap use and +500% sig. Current SDE and ESI
  have 160 and +475%, so the Legion's MWD numbers differed for a reason that
  had nothing to do with the math.
- **Do this instead:** check pyfa's data build (Help → About, or `eve.db`)
  before diagnosing a small difference on a specific module.

# Phase 3 — Implementing

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

# Phase 4 — Verifying and delivering

## 12. `node --check` passes, the page still breaks

- **What happened:** a constant was declared after its first use
  (temporal dead zone). That's valid syntax, but it threw at runtime.
- **Do this instead:** run the regression suite and render one fit with
  Playwright.

## 13. "Delivered" wasn't delivered

- **What happened:** a commit reported success but the file never reached the
  user's disk (2026-10-08).
- **Do this instead:** after every write to the user's machine, list the file
  and compare its size and mtime with the source.
