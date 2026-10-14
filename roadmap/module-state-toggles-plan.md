# Plan: module on/off states and a fit view with toggles

Status: **APPROVED** (2026-10-13). Decisions recorded in section 4.
**Phase 1 (engine) DONE in v2026.10.13.20** — see
`dscan-tool-history/2026-10-13_module-states-engine-phase1.html`.
**Phase 2 (module list UI) DONE in v2026.10.13.22** — see
`dscan-tool-history/2026-10-13_module-states-ui-phase2.html`.
**Phase 3 (special cases) DONE in v2026.10.13.26** — see
`dscan-tool-history/2026-10-13_module-states-phase3-special-cases.html`.
Next: Phase 4 is optional (D4 capacitor advice, D5 overheat, both in the backlog).
Backlog item: "Module on/off toggles for stat-transforming modules" (Medium).
This plan widens it from "siege-type modules" to every fitted module.

---

## 1. Problem

The calculation engine (`estimateHpAndDps()`, about 3,000 lines in
`index.html`) treats almost every fitted module as **active at the same time**.
Real fits often can't do that:

- **Game rules forbid it.** The SDE marks some groups with `maxGroupActive`
  (attribute 763) or blocks activation with `activationBlocked`. Examples are
  listed in section 2.
- **The capacitor can't sustain it.** Everything on at once can drain a fit
  that is stable in normal use.
- **The pilot's choice.** A cloak, an MJD or a Signature Suppressor burst are
  short or situational.

There are already a few special cases:

- MWD/AB "cruising vs boosted" pairs
- the capacitor booster toggle
- the T3D mode buttons
- several effects excluded as "while active, module-toggle item"
  (Capital Sensor Arrays, Entosis Link, MJD sig spike, Suppressor burst,
  Triage EWAR lockout)

These each work differently, so the rules aren't consistent across the tool.

The roadmap's "build a counter fit / time to kill" request (`roadmap/feature requests.txt`) also depends on this. A time-to-kill comparison is only honest if both fits run modules they could actually run together.

## 2. How pyfa does it (primary source: pyfa v2.69.2)

**States.** `eos/const.py` `FittingModuleState`: OFFLINE (−1), ONLINE (0),
ACTIVE (1), OVERHEATED (2).

**Which effects apply in which state.** `eos/saveddata/module.py`
`calculateModifiedAttributes()` (around line 930) and `canDealDamage()`:

| Handler `type` | Applies when |
|---|---|
| `'offline'` | Always, even when offline. Example: cloak scan-res multiplier, effect 854 |
| `'passive'` | Module is at least ONLINE. Example: Signature Suppressor ×0.9 (8108) |
| `'active'` | Module is at least ACTIVE. Examples: MWD 6730, Sensor Booster 2670, Tracking Computer 4559, Bastion 6658 |
| `'overheat'` | Module is OVERHEATED |

Every handler in `effects.py` declares its `type`; `tools/pyfa_effects.py`
can read it (2,131 passive, 72 active, 19 overheat, 4 offline, plus
projected/gang types that are out of scope).

**Which states are valid.** `module.py` `isValidState()` and `canHaveState()`:

- ACTIVE needs the item to have an active effect and `activationBlocked == 0`.
  - Bastion sets `activationBlocked` on MJDs (6658).
  - Networked Sensor Array blocks capital MJDs (6567).
  - Warp-scramble effects block MWDs and MJDs.
- OVERHEATED needs an overheat effect.
- **Group limits:** at most `maxGroupActive` modules of one group can be
  ACTIVE, and at most `maxGroupOnline` can be ONLINE. Groups with
  `maxGroupActive = 1` in the current SDE include:
  - Propulsion Module (one AB or MWD at a time)
  - Damage Control
  - Siege Module (Bastion, Siege, Triage, Industrial Cores)
  - Micro Jump Drive and MJFG
  - Signature Suppressor
  - Reactive Armor Hardener
  - Ancillary Armor Repairer
  - Burst Jammer
  - Command Burst
  - Cynosural Field Generator
  
  (`tools/pyfa_effects.py` lists the full set.)

## 3. Proposed behavior

### Default state: "best case", within the game's rules

Every module starts at the highest state pyfa allows: ACTIVE if it has an
active effect and nothing blocks it, otherwise ONLINE. Group limits are then
applied, with these default choices:

- **Propulsion:** the primary prop mod (highest speed factor) is ACTIVE, any
  second one is ONLINE. Today's "cruising / boosted / secondary boosted"
  display stays, now driven by state.
- **Siege family, cloak, MJD/MJFG, Signature Suppressor burst:** see
  decisions D2–D3.

For killmails and d-scan this keeps today's "assume the opponent at their
best" approach. The difference is that the results are possible in game.

### Engine (Phase 1, no UI)

- **State map.** Add a per-fitted-module state map (keyed by slot flag where
  known, otherwise by type with per-state counts) as a new optional argument
  to `estimateHpAndDps()`. Without it, the default rules above are used.
- **Effect table.** Generate an `EFFECT_ACTIVATION_TYPE` table (effect ID →
  offline / passive / active / overheat) from pyfa's handler types with a
  `tools/` script, the same way the weapon-range table is generated.
- **One gate.** Every place that currently counts a module (`qtyById`, the
  effect-table collectors, the capacitor loop, resists, reps, DPS) asks one
  helper: "how many copies of this item have this effect applied?"
- **Capacitor:** only ACTIVE modules drain. That makes "is this fit
  cap-stable with these modules on?" an exact question.
- **Validity:** a state that breaks a game rule is refused, and the reason is
  returned for the UI (e.g. "Bastion blocks MJD activation").

### Fit view with toggles (Phase 2)

- **Slot rack.** A compact list grouped high / mid / low / rig / subsystem /
  drones, one row per fitted module with its name, icon and state control.
  Icons come from CCP's public image server, `images.evetech.net/types/{id}/icon`.
- **Click to change state.** A click cycles OFFLINE → ONLINE → ACTIVE.
  Invalid states are skipped, and hovering shows why.
- **Live recalculation.** Every stat card re-renders on each change, using
  the existing pattern from the T3D mode and capacitor-booster toggles.
  "Reset to best case" restores the defaults.
- **Where it appears:** the Fit Analyzer (EFT paste) always. On the Pilot
  Analyzer, behind a "Fit" expander on each loss (decision D1).
- **Capacitor link:** the capacitor card shows which modules are counted, and
  the existing booster toggle becomes one row in the same list.

### Fold in the special cases (Phase 3)

These become ordinary module states:

- the backlog "module-toggle" items (Bastion/Siege/Triage/Industrial Core,
  Signature Suppressor burst, Capital Sensor Arrays, Entosis Link, MJD spike)
- the Triage EWAR lockout
- the capacitor booster toggle

Remove the scattered flags (`hasMWD` assumptions, "assumed active whenever
fitted" branches) once each one is driven by state.

**Done (v.26).**

- The siege family was already state-driven since Phase 1. v.26 pinned it
  (Siege Module online = no-siege numbers) and fixed Triage drone damage (×0).
- Now modeled when set active:
  - MJD/MJFG and Signature Suppressor signature bursts
  - Entosis Link sensor strength
  - Networked and Integrated Sensor Array sensors, scan resolution and
    targeting range, plus capital rep cycle and cap need
- Triage / Networked Sensor Array EWAR lockout: the affected modules are
  blocked while it runs. They default online, and a request to activate them
  is refused with the reason.
- The capacitor booster: whether it runs is its row in the module list (only
  an active booster injects).
  - v.26 kept the ring toggle as a "charges" toggle.
  - **v.27 (the owner) removed it.** The capacitor figures are the best case of the
    running modules: active Capacitor Boosters inject, and active ASBs have
    charges.
  - Each boost counted shows its in-game icon next to the ring. The ASB icon
    is clickable for "out of charges".
- MWD/AB: the speed card keeps its cruising and boosted figures side by side,
  with an online prop mod shown as the "if switched on" figure (v.20).
- Found along the way and fixed:
  - Targeting range is now capped at maximumRangeCap.
  - Module cycle time now follows pyfa's `rawCycleTime`, so Nullifiers,
    Suppressors and Burst Projectors now use capacitor (LESSONS #20).

### Optional (Phase 4)

- **Overheated state (backlog, D5):** pyfa's 19 `overheat` handlers. Show heat
  bonuses only, with no heat-damage simulation.
- **Capacitor advice (backlog, D4):** when the chosen states aren't
  cap-stable, suggest which modules to switch off. Revisit after Phases 1–3.
- **Visual fitting-window layout:** circular slot rings like the in-game
  window. Mostly appearance, so lowest priority.

## 4. Decisions (the owner, 2026-10-13)

| # | Question | Decision |
|---|---|---|
| D1 | Show the module list on Pilot Analyzer losses, or only in the Fit Analyzer? | **Both.** Collapsed by default on losses. |
| D2 | Default for the siege family (Bastion, Siege, Triage, Industrial Core): active or online? | **Active**, as today. A Marauder threat assessment assumes Bastion. |
| D3 | Default for cloak, MJD/MJFG, Signature Suppressor burst, Entosis Link: active or online? | **Online.** They're short or situational; "active" would make the other numbers impossible. |
| D4 | Fit Analyzer: when every module can't run because of capacitor, should the tool suggest which to switch off? | **Later**, once we've learned enough from Phases 1–3 to make a recommendation. In the backlog. |
| D5 | Overheat (Phase 4): in or out? | **Not now.** In the backlog. |

## 5. Risks and how they're handled

- **Wide refactor.** The "active" assumption is spread through about 3,000
  lines. Mitigation: Phase 1 changes no output under the default states, and
  the full `diffall` over all 123 golden fits must come back empty (except for
  the group-limit corrections, each explained and pinned).
- **Killmail path has no states.** A killmail says what was fitted, not what
  was running. Defaults stay "best case within rules", and the UI says the
  states are assumed.
- **Multi-loss averaged view.** Quantities there can be fractional. States
  apply per type with counts, which handles that.

## 6. Verification plan (per `LESSONS_LEARNED.md`, in order)

1. Run `tools/pyfa_effects.py` to list every effect's activation type and
   every `maxGroupActive` / `maxGroupOnline` / `activationBlocked` source.
2. Write `tools/independent_checks/check_module_states.py`, with expected
   values for:
   - a Vargur with Bastion online vs active
   - a dual-prop fit with each prop active
   - a cap-unstable fit becoming stable with one module offline
   - a Bastion fit trying to activate an MJD (refused)
3. Build constructed golden fits that carry explicit states. The regression
   harness gets an optional `moduleStates` field, the same way `tacticalMode`
   works today.
4. Phase 1 delivery: output diff with default states is empty, apart from
   the listed group-limit corrections.
5. Phase 2 delivery: Playwright renders of the module list in each state,
   and click tests that confirm recalculation.

## 7. Rough size

| Phase | Size |
|---|---|
| 1 — engine | Large, the bulk of the work. Probably split into two deliveries: the state model plus capacitor first, then resists, reps and the rest. |
| 2 — module list UI | Medium |
| 3 — fold in special cases | Medium |
| 4 — optional | Small to medium each |
