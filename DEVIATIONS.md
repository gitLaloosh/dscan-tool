# Deliberate differences from pyfa

The tool's goal is pyfa's numbers (`PYFA_CORE.md`). Everything below differs on
purpose, or is a known gap waiting for a fix. **A difference that isn't listed
here is a bug.** Add an entry, with its reason, in the same change that
introduces a difference.

## 1. Calculation differences

| What | pyfa | Tool | Why / status |
|---|---|---|---|
| Triage Module / Networked Sensor Array EWAR lockout | Leaves EWAR, webs, scrams and disruptors active with +900,000,000% / +9,999,900% cap need, so the capacitor empties at once | Treats them as blocked (can't be set active; reason on hover) | In game they can't run. Showing an instantly empty capacitor would hide the real cap state. (v2026.10.13.26) |
| `capSim` injector choice | `max()` over an empty list in one branch (would crash) | Max over the awaiting injectors | The evident intent; that branch never ran in 1,683 comparisons. (v2026.10.14.1) |
| Rounded stacking table: `applyStacking` / `applyStackingBonus` | Exact `exp(-i²/7.1289)`: 0.86912, 0.57058, 0.28296, ... | `STACKING_PENALTY` rounded to 3 decimals: 0.869, 0.571, 0.283, ... | Historical. A fraction of a percent on turret/missile damage modules, shield-boost amps and sensors. To be replaced by `pyfaPenalizedProduct` (already in the core) as each area moves into the core. Exact already for drone and fighter damage modules (v2026.10.14.4), every resistance (v2026.10.14.5), speed / agility / mass (v2026.10.14.8) and every EWAR module value (v2026.10.14.11). |
| Damage-type-limited hull bonuses, special-edition fallback only | Applies per damage attribute | For the 7 fallback hulls: applies when the ammo's *dominant* damage type matches (`hullDamageMultFor`) | Every other hull uses the generated table, applied per damage type exactly as pyfa does (v2026.10.14.3). |
| Special-edition hulls without SDE damage effects (Moros Interbus, Naglfar Justice, Phoenix Wiyrkomi, Revelation Sarum, two Punisher editions, Rorqual ORE Development) | No hull bonus (no effects to run) | The base hull's bonus from the fallback table `SHIP_ROLE_BONUS` (used only when the hull has no generated damage effect; `audit_firepower.py` checks this) | Known open item #4. Assumption, not verified: an edition hull carries its base hull's traits. The SDE has no effects for them. |
| Alliance Tournament hulls scaling with pilot security status (Sidewinder, effect 12165 ATFrigDmgBonus; an Alliance Tournament cruiser's web range bonus, ATcruiserStasisWebifierBonus) | Scales the bonus by the pilot's security status | Not applied (no bonus) | A killmail or EFT paste doesn't carry the pilot's security status. Reported by `gen_hull_damage_table.py` as skipped. |

## 2. Inputs the tool chooses (pyfa gets these from the user's fit)

| Input | Tool's choice |
|---|---|
| Skills | All V (pyfa's "All 5" character) |
| Implants and boosters | **Fit Analyzer:** exactly the EFT paste's, as pyfa imports it: a bare name with implantness / boosterness is applied, a `Name x1` line is cargo, the first item per slot wins (v2026.10.14.12; weapons, drones and drone control range since v2026.10.14.13). Expired event boosters (pyfa's database deletes them) are not applied and are named in a note (v2026.10.14.14). Booster side effects off, pyfa's default. **Pilot Analyzer:** none -- a ship killmail never lists implants (only the pod's killmail does, flag 89), boosters appear on no killmail, and the Pilot Analyzer doesn't use pod losses. `PILOT_ANALYZER_APPLY_IMPLANTS` (false) turns flag-89 implants on if pods are ever used. |
| Module states | Plan defaults: siege family **active**; cloak, MJD, MJFG, Signature Suppressor, Entosis, Capital Sensor Arrays, Cynosural Field Generators (v2026.10.14.8: a lit cyno immobilises the ship) **online**; Assault Damage Control burst online; everything else as pyfa's default. The user can change them in the module list. |
| Capacitor Booster charge | Loaded, else found in cargo or fleet hangar, else the largest compatible charge ("assumed", amber icon) |
| Ancillary Shield Booster | Has charges (icon toggles "out of charges") |
| Drones in space | Hardest-hitting combat drones up to bandwidth and 5 drones; changeable per type |
| Fighters | Automatic by tubes and class limits (backlog: selectable). An EFT line `Firbolg I x18` is read as 18 fighters in the bay, launched as 3 squadrons; pyfa loads it as one squadron (capped at 6). |
| Fighter abilities | pyfa's defaults (`Fighter.__init__`): Attack Missile + every ability before it except MWD / Evasive Maneuvers — light fighters fire Missiles too, heavy bombers' bombs stay off. DPS ignores rearm time, as pyfa does unless "factor in reload time" is on. (v2026.10.14.4) |
| RAH damage profile | Uniform 25% each, which is pyfa's default profile too |
| Ship mode (Tactical Destroyers incl. the Skua; the Anhinga) | Tactical Destroyers: **Sharpshooter**, switchable. pyfa's default is the hull's first mode item (Defense on every Tactical Destroyer); the tool keeps Sharpshooter because it shows the hull's damage. Anhinga: **Primary**, pyfa's default too (Erik's choice, 2026-10-14). Every mode effect is pyfa's own handler (`MODE_EFFECT_ROWS`, `gen_mode_table.py`; v2026.10.14.6). |
| Hardener scripts | Read from a mid-slot module's flag-paired charge (Capital Flex Shield Hardener). A killmail's low-slot charges aren't paired, so a Capital Flex **Armor** Hardener's script is ignored. |

## 3. Shown by the tool, not part of pyfa's fit stats

- Weaknesses, Tank Type, Break Point, recommendations (ammo, drones, turret "No answer").
- Misc flags on the EWAR / Misc card (cyno, MJD / MJFG, Interdiction Nullifier, PANIC). The PANIC's invulnerability has no pyfa handler, so, as in pyfa, it can't be set active and changes no stat; the flag quotes CCP's item description, its range and its duration as pyfa computes it at All V (6 min). (v2026.10.14.10; v.9 briefly allowed an Active state that changed nothing.)
- Missile damage application vs a target. Uses the standard missile application formula `min(1, S/E, ((S/E)(Ve/Vt))^drf)` (EVE University; CCP dogma attributes) on raw charge stats. Hull, skill and module application bonuses aren't applied (hand-tables P5).
- "Net cap rate": a simple average (recharge − drain + injection). The capacitor *state* comes from pyfa's simulation.
- EVE's closed-form capacitor stability, on ring hover (pyfa computes it as `cap_stable_eve` but doesn't display it).

## 4. Not modeled (gaps, not choices)

Each is in a backlog:

- overheating
- bombs (heavy fighters' Launch Bomb, off by default in pyfa too; bomb launchers) and the Disruptive Lance
- drone hit points
- effect beacons (wormhole and incursion system effects)
- projected effects (remote reps on the target, command bursts)
- turret tracking application
- mode effects on stats the tool doesn't show: turret tracking (Svipul Sharpshooter), remote repair and remote shield boost amounts (Confessor / Svipul Defense; their capacitor need *is* applied), weapon-disruption and sensor-dampener resistance (every Sharpshooter mode)

**Hand-built tables not yet replaced by pyfa-derived ones:** none. Firepower was replaced in v2026.10.14.3 (P1); fighter
abilities and Fighter Support Units followed in v2026.10.14.4, resistances (P2)
in v2026.10.14.5, ship modes (every hull with modes, every mode stat) in
v2026.10.14.6, missile flight range (pyfa's `Module.missileMaxRangeData`) in v2026.10.14.7, speed / agility / mass / align time (P3) in v2026.10.14.8, and every EWAR module value (P4: range, falloff, strength, neutralizer / nosferatu amount, with skills, hull, subsystems, rigs and loaded scripts) in v2026.10.14.11.

**Resistances** (P2) moved to pyfa's handlers in v2026.10.14.5: hull, module, script,
Compensation-skill and mode effects are generated (`gen_resist_table.py`), and the Reactive
Armor Hardener is pyfa's own algorithm. The tool no longer clamps a resonance at 3%: pyfa
only caps it at the max-resonance attributes.
