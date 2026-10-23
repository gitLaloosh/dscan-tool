# PYFA CORE: the code that replicates pyfa

The tool's numbers must match **pyfa** exactly. The code that does that is
fenced in `index.html` and locked:

```
// ==== PYFA CORE BEGIN <id> ==== mirrors pyfa; change only to match pyfa (...)
...
// ==== PYFA CORE END <id> ====
```

## The rule

**The tool may change what goes into the pyfa calculation, or how the result
is shown. It never changes how the calculation works.**

- **Inputs (tool decisions, outside the fences):** which modules are active,
  which charges are assumed, which drones are out, refusing EWAR during
  triage, assumed skills (all V), killmail and EFT parsing.
- **Presentation (outside the fences):** Weaknesses, Break Point, the ring,
  recommendations, rounding for display.
- **Calculation (inside the fences):** stacking penalties, cycle times, the
  capacitor simulation, the RAH, and every table generated from or audited
  against pyfa's handlers.

Every deliberate difference from pyfa is listed in `DEVIATIONS.md`, with the
reason. A difference that isn't listed is a bug.

## The lock

`tools/pyfa_core_manifest.json` records, for every section:

- the SHA-256 of its lines
- the pyfa code it mirrors
- its kind:
  - **port:** pyfa code translated by hand
  - **generated:** a table written by a tools/ script
  - **audited:** a table checked by running every pyfa handler
- the commands that re-verify it

The manifest also records the pyfa version, commit and SDE client build the
sections were last verified against.

`node regression_suite/run_regression.mjs` runs `tools/check_pyfa_core.mjs`
first. A section that changed **fails the suite**. The lock can't prevent an
edit; it makes every core edit deliberate.

### Changing a core section

Only do this to match pyfa, or to move more pyfa logic into the core.

1. Make the change, following `LESSONS_LEARNED.md`'s checklist: derive the
   expected values first, and add a golden fit that fails on the old build.
2. Run the section's `verify` commands from the manifest. All must pass.
3. Run `node tools/check_pyfa_core.mjs index.html --update`, then rerun the
   suite.
4. Say in the history doc which sections changed and how they were
   verified.

### Adding a section

Add the BEGIN/END markers, then a manifest entry with `kind`, `mirrors` and
`verify` (written by hand), then run `--update`. New pyfa-derived code (for
example the generated firepower table) goes inside a new section.

## Start of work: is pyfa still the version we verified?

```
PYFA_SRC=/path/to/Pyfa python3 -I tools/pyfa_update_check.py        # versions only
PYFA_SRC=/path/to/Pyfa python3 -I tools/pyfa_update_check.py --run  # + full chain
```

This compares the manifest, the local pyfa checkout, and GitHub (latest
release and master). `--run` runs the whole chain:

- the core lock
- the golden-fit data refresh report
- the weapon-range and module-state generators
- the effect-table audit
- pyfa's capacitor simulator comparison
- the regression suite

Two things change independently:

- **CCP game data** (patches). The live page reads ESI, so it sees new values
  immediately. But generated and hand tables go stale: new hulls and new
  effects are missing until they're regenerated. Example: the Akoman,
  Thunderchild and Hydra are absent from `SHIP_ROLE_BONUS`. pyfa's staticdata
  client build tracks this.
- **pyfa's code** (handlers, capSim, attribute rules). Only a pyfa update
  shows these changes.

When pyfa or its data moves:

1. Update `PYFA_SRC`.
2. Run `--run`.
3. Explain every change, fix what needs fixing, and re-pin with notes.
4. Update the manifest's `pyfa` block and fingerprints.
5. Record it all in a history doc.

When comparing with one of Erik's pyfa screenshots, ask for Help → About:
his pyfa must be the same version and data build (LESSON #10).

## Sections (2026-10-14; re-verified 2026-10-21 against pyfa v2.69.3, data 3624425; 13 sections)

| Section | Kind | Mirrors |
|---|---|---|
| `stacking-penalty` | port | `modifiedAttributeDict.__calculateValue` stacking penalty |
| `cap-sim` | port | `eos/capSim.py`, run as `Fit.__runCapSim` |
| `resist-calc` | generated + port | every resistance handler (hulls, modules, scripts, Compensation skills, Polarized weapons, ship modes; `gen_resist_table.py`), `modifiedAttributeDict.py` value calculation for those attributes, and `effects.py` Effect4928 (Reactive Armor Hardener). Since v2026.10.14.5; replaced `rah-sim`, which was locked as a "port" but was not pyfa's algorithm (LESSON #25) |
| `modes` | generated | every effect of every ship mode item (`Ship.__getModeItems`: Tactical Destroyers incl. the Skua, and the Anhinga) as pyfa's handlers apply it (`gen_mode_table.py`), the default mode (`Ship.validateModeItem`) and each handler's module/charge filter. Since v2026.10.14.6; replaced five hand tables. Resonance rows stay in `resist-calc` |
| `speed-calc` | generated + port | every handler on ship maxVelocity / agility / mass and on the module attributes they read (`gen_speed_table.py`), pyfa's MWD / AB effects 6730 / 6731 (`pyfaPropBoost`), `Fit.maxSpeed` / `Fit.alignTime`. Since v2026.10.14.8 (hand-tables P3) |
| `ewar-calc` | generated | every handler on an EWAR module's own attributes the EWAR / Misc card shows: skills, hulls, modules, rigs, subsystems and loaded scripts (`gen_ewar_table.py`); since v2026.10.14.26 also Warp Disrupt Field Generators and Command Bursts, with their charges' own attributes (`EWAR_CHARGE_ATTRS`: burst charge multipliers after the Command Specialist skills); since v2026.10.14.29 also the ECM Burst (Burst Jammer) and the Supercarriers' Burst Projectors (field radius, lifetime, warning, how long targets stay affected); verified by `compare_ewar.py` against `pyfa_fit_oracle.py` |
| `implant-calc` | generated + port | implants and boosters from a pasted EFT fit, as pyfa runs them (`implant.py` / `booster.py`, each effect in its carrier's own context, set bonuses first, booster side effects off): `IMPLANT_EFFECTS` by `gen_implant_table.py`; `pyfaImplantSetup` hands the rows to the stat code (v2026.10.14.12; weapon / charge / drone rows join the hull damage rows and the weapon range sources since v2026.10.14.13). `PYFA_REMOVED_IMPLANT_IDS`: the implants / boosters pyfa's database doesn't have (`pyfa_sde.pyfa_removed_types`, v2026.10.14.14). Verified by `compare_implants.py` (HP, capacitor, recharge, signature, targeting, sensors, repairs, cap use, weapon / smartbomb / drone DPS, weapon ranges, drone control range) and by `compare_speed.py` / `compare_resists.py` / `compare_ewar.py` on the same fits |
| `missile-range` | port | `Module.missileMaxRangeData` + the missile branch of `Module.maxRange`, and `eos/utils/float.py` floatUnerr. Since v2026.10.14.7; verified by running pyfa's own function (`check_missile_range.py`). Since v2026.10.14.34 floatUnerr rounds with `pyfaRound` (Python `round()` exactly, ties to even) |
| `application` | port | pyfa's damage graph: `graphs/data/fitDamageStats/calc/application.py` (getApplicationPerKey; turret, launcher, Vorton and smartbomb multipliers), `eos/calc.py` calculateRangeFactor, `getter.py` applyDamage. Since v2026.10.14.34 (turret-application-plan.md Phase 1); verified by running pyfa's own getApplicationPerKey unmodified on oracle attributes over a 6,000-point grid (`check_application.py`); its inputs (tracking, explosion radius / velocity, flight ranges) by `compare_fit_stats.py` |
| `cycle-time` | port | `Module.rawCycleTime` / `reactivationDelay` / `getCycleParameters` |
| `weapon-range-table` | generated | weapon range handlers (`gen_weapon_range_table.py`); since v2026.10.14.34 also turret tracking and missile / Vorton explosion radius and velocity |
| `hull-damage` | generated | hull and subsystem damage / rate-of-fire handlers + the helpers applying them per weapon, charge, drone and fighter ability (`gen_hull_damage_table.py`, since v2026.10.14.3); `FIGHTER_ABILITY_EFFECTS` + `pyfaDefaultFighterAbilities` = pyfa's default fighter abilities (`Fighter.__init__`, since v2026.10.14.4) |
| `module-state-tables` | generated | effect types, group limits, activation blocks (`gen_module_state_tables.py`) |
| `sig-effect-tables`, `cap-rep-effect-tables`, `sensor-effect-table`, `sensor-strength-effect-ids`, `hp-effect-table` | audited | `audit_effect_tables.py` |
| `cycle-time-tables` | audited | reactivation-delay and burst-duration modifiers |

**Not in the core yet:**

- nothing from the hand-tables plan: firepower moved into `hull-damage` (v2026.10.14.3), resistances into
  `resist-calc` (v.5), speed into `speed-calc` (v.8) and EWAR into `ewar-calc` (v.11); the old hand tables
  remain only as the fallback for a hull record without dogma effects
- `applyStacking` / `applyStackingBonus` are thin wrappers over the core's `pyfaPenalizedProduct`
  since v2026.10.14.23 (they used a rounded 3-decimal table before)

They move into the core as each is replaced with pyfa-derived code.
