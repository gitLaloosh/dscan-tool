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
| Damage-type-limited hull bonuses, special-edition fallback only | Applies per damage attribute | For the 7 fallback hulls: applies when the ammo's *dominant* damage type matches (`hullDamageMultFor`) | Every other hull uses the generated table, applied per damage type exactly as pyfa does (v2026.10.14.3). |
| Special-edition hulls without SDE damage effects (Moros Interbus, Naglfar Justice, Phoenix Wiyrkomi, Revelation Sarum, two Punisher editions, Rorqual ORE Development) | No hull bonus (no effects to run) | The base hull's bonus from the fallback table `SHIP_ROLE_BONUS` (used only when the hull has no generated damage effect; `audit_firepower.py` checks this) | Known open item #4. Assumption, not verified: an edition hull carries its base hull's traits. The SDE has no effects for them. |
| Alliance Tournament hulls scaling with pilot security status (Sidewinder, effect 12165 ATFrigDmgBonus; an Alliance Tournament cruiser's web range bonus, ATcruiserStasisWebifierBonus) | Scales the bonus by the pilot's security status | Not applied (no bonus) | A killmail or EFT paste doesn't carry the pilot's security status. Reported by `gen_hull_damage_table.py` as skipped. |

## 2. Inputs the tool chooses (pyfa gets these from the user's fit)

| Input | Tool's choice |
|---|---|
| Skills | All V (pyfa's "All 5" character) |
| Implants and boosters | **Fit Analyzer:** exactly the EFT paste's, as pyfa imports it: a bare name with implantness / boosterness is applied, a `Name x1` line is cargo, the first item per slot wins (v2026.10.14.12; weapons, drones and drone control range since v2026.10.14.13). Expired event boosters (pyfa's database deletes them) are not applied and are named in a note (v2026.10.14.14). Booster side effects off, pyfa's default. **Pilot Analyzer:** none -- a ship killmail never lists implants (only the pod's killmail does, flag 89), boosters appear on no killmail, and the Pilot Analyzer doesn't use pod losses. `PILOT_ANALYZER_APPLY_IMPLANTS` (false) turns flag-89 implants on if pods are ever used. |
| Module states | Plan defaults: siege family **active**; cloak, MJD, MJFG, Signature Suppressor, Entosis, Capital Sensor Arrays, Cynosural Field Generators (v2026.10.14.8: a lit cyno immobilises the ship), Zero-Point Mass Entanglers (v2026.10.14.30: active, it pins the Heavy Interdictor in place; it's run only once tackled) **online**; Assault Damage Control burst online; everything else as pyfa's default. The user can change them in the module list. |
| Capacitor Booster charge | Loaded, else found in cargo or fleet hangar. If none: a killmail (Pilot Analyzer) assumes the largest compatible charge ("assumed", amber icon), since its charges may have run out in the fight; a pasted fit (Fit Analyzer) has none, so the booster injects nothing and the Weaknesses card flags "no charges" (the owner, v2026.10.14.24). pyfa uses only the charge in the fit, like the pasted-fit rule. |
| Ancillary Shield Booster | Has charges (icon toggles "out of charges"), except a pasted fit with no charge loaded or in cargo: it runs on capacitor and is flagged (v2026.10.14.24) |
| Ancillary Armor Repairer paste | v2026.10.14.61: Nanite Repair Paste loaded, else in cargo or fleet hangar. A killmail with none seen in the module assumes a full clip (its paste may have run out in the fight; the owner). A pasted fit with none anywhere repairs its plain amount, and the Weaknesses card flags "No paste for its ...". The Repairs strip's burst shows only with paste aboard (or assumed). pyfa uses only the paste in the fit. |
| Drones in space | Hardest-hitting combat drones up to bandwidth and 5 drones; changeable per type |
| Weapon with no charge loaded | v2026.10.14.67 (the owner: "Assume a charge", "Their best against you"): for Damage Application and the Matchup, a weapon type with no charge in any copy is taken as loaded with the charge aboard (loaded elsewhere or in cargo / fleet hangar, pyfa's isValidCharge) that kills the target fastest at the fight's point -- the same charge the Weaknesses picks rank first. Its numbers are pyfa's for the fit with that charge in every copy. Shown "Assumed loaded: ..." on the card and in the board's hover and "why". pyfa computes the fit as given: no charge, no damage. A type with some copies loaded and some empty counts its loaded copies only. The Firepower card keeps the range over every charge aboard. |
| Fighters | Changeable per type in the Fighter bay since v2026.10.14.66. Default (the owner 2026-10-25, "Damage first"): damage squadrons hardest-first within the tubes and class limits, then support squadrons in the tubes left, webs first. pyfa adds a squadron in space only while a tube and a slot of its class are free (`gui/fitCommands/calc/fighter/localAdd.py`), in the order they are added. An EFT line `Firbolg I x18` is read as 18 fighters in the bay, launched as 3 squadrons (the owner kept the bay count); pyfa loads it as one squadron (capped at 6). A structure fighter can't be launched from a ship (pyfa: `Fighter.fits()` is false); before v.66 the tool launched one. |
| Fighter abilities | pyfa's defaults (`Fighter.__init__`): Attack Missile + every ability before it except MWD / Evasive Maneuvers — light fighters fire Missiles too, heavy bombers' bombs stay off, a support squadron's EWAR and afterburner are on. DPS ignores rearm time, as pyfa does unless "factor in reload time" is on. (v2026.10.14.4) Since v2026.10.14.66 each can be switched in the Fighter bay: a damage ability off adds nothing, a speed ability on (MWD, afterburner, evasive maneuvers) changes the squadron's speed as pyfa's handler does. Since v2026.10.14.71 a bomber's Bomb can be switched on: pyfa's volley from the squadron's charge (damage x fighters, every Launch Bomb duration; nothing modifies it), landing without a lock at min(1, signature / the bomb's explosion radius). |
| RAH damage profile | Uniform 25% each, which is pyfa's default profile too |
| Ship mode (Tactical Destroyers incl. the Skua; the Anhinga) | Tactical Destroyers: **Sharpshooter**, switchable. pyfa's default is the hull's first mode item (Defense on every Tactical Destroyer); the tool keeps Sharpshooter because it shows the hull's damage. Anhinga: **Primary**, pyfa's default too (the owner's choice, 2026-10-14). Every mode effect is pyfa's own handler (`MODE_EFFECT_ROWS`, `gen_mode_table.py`; v2026.10.14.6). |
| Hardener scripts | Read from a mid-slot module's flag-paired charge (Capital Flex Shield Hardener). A killmail's low-slot charges aren't paired, so a Capital Flex **Armor** Hardener's script is ignored. |

## 3. Shown by the tool, not part of pyfa's fit stats

- Weaknesses, Tank Type, Break Point, recommendations (ammo, drones, turret "No answer").
- Misc flags on the EWAR / Misc card (cyno, MJD / MJFG, Interdiction Nullifier, PANIC). The PANIC's invulnerability has no pyfa handler, so, as in pyfa, it can't be set active and changes no stat; the flag quotes CCP's item description, its range and its duration as pyfa computes it at All V (6 min). (v2026.10.14.10; v.9 briefly allowed an Active state that changed nothing.)
- Missile damage application vs a target (the Weaknesses card's missile pick). Uses the standard missile application formula `min(1, S/E, ((S/E)(Ve/Vt))^drf)` (EVE University; CCP dogma attributes; pyfa's graphs use the same). Since v2026.10.14.27 your missiles get the tool's All V application skills, the only two pyfa skill handlers on them: Guided Missile Precision -25% explosion radius, Target Navigation Prediction +50% explosion velocity (`check_missile_application.py`). Your own rigs, Missile Guidance Computers and hull bonuses aren't known and aren't applied. Since v2026.10.14.69 the tile shows the best ammo for each launcher (each launcher's first entry in the ranking), with the target's prop module off and on; the prop-on state is the winning prop module's speed with its own signature: an MWD's bloom, an afterburner's base signature (before v.69 an afterburner fit had no prop-on ranking). Percentages on the tile are whole numbers rounded half up from the ranking's one decimal; the hover gives the one decimal.
- "Net cap rate": a simple average (recharge − drain + injection). The capacitor *state* comes from pyfa's simulation.
- The My Ship matchup strip's "You last" / "They last" (v2026.10.14.41, my-ship-plan.md P2). pyfa has no time to
  kill. Built from pyfa's pieces: the incoming applied DPS by damage type (pyfa's damage graph with applyProjected,
  each module's and drone's own damage types) against each layer's resonances, shield then armor then hull, minus
  that layer's local repair rate and the shield's PEAK passive regen (2.5 x HP / recharge time, as the Break Point;
  real regen is lower away from ~25% shield), with the repairs stopping when pyfa's capacitor simulation runs dry.
  An Ancillary Shield Booster on charges (v2026.10.14.57) doesn't use the capacitor (pyfa calculateSustainableTank): it
  reps for its clip (pyfa numShots = capacity / charge volume / chargeRate), reloads (reloadTime, 60 s), and so on
  while charges last (a full loaded clip plus the same charge in the hold, also if a Capacitor Booster shares them),
  then stops. pyfa itself would either ignore the reload (its default) or average it over the fight ("factor in
  reload": rate x clip time / (clip time + reload)); a time to kill needs the gap. An ASB with no charge seen on a
  killmail (assumed charged) runs until the capacitor runs dry, as before. An Ancillary Armor Repairer (v2026.10.14.61)
  with Nanite Repair Paste repairs chargedArmorDamageMultiplier (3) times its amount for a clip (pyfa numShots, 8 cycles),
  starting when the armor starts taking damage, reloads for 60 s with no repair, and so on while paste lasts (a full clip
  per copy plus the hold), then repairs its plain amount; unlike an ASB it needs the capacitor either way. pyfa would
  show the 3x rate throughout (peak) or average it with the reload ("factor in reload"). Not counted: their neuts on your capacitor, remote
  repairs, overheating, the card's MWD switch on your capacitor (it changes your speed and signature only).
  "holds" when the damage never gets through. Checked by `check_matchup.py` against an independent build of the
  same rule on pyfa's numbers.
- The Weaknesses picks with My Ship in use (v2026.10.14.42, my-ship-plan.md B1-B4). The DPS shown is pyfa's applied
  DPS of that weapon type with the charge loaded in every active copy (the fit run again through pyfa's handlers),
  or of a flight of one drone type, at the strip's fight. The ORDER is the tool's: the strip's time to kill above
  with that swap (their resists count; the rest of the fit as it is), then the time against their buffer alone,
  then the charge already loaded. Choices: only ammo and drones aboard (loaded, cargo, drone bay; pyfa's
  isValidCharge rule for what loads); a drone pick is one type at a time (as many as the bay, 5 drones and the
  bandwidth allow), not mixed flights; the fight's webs, painters and scram are the fit's current ones, whatever
  is being ranked. Fighters (v2026.10.14.72, the owner: "One tile per class", abilities "As set in the Fighter bay"): one
  pick per class (light, heavy), each damage-dealing type flown in that class's squadrons -- as many as its bay, the class
  limit and the tubes left by the other classes' squadrons in space allow -- with its abilities as set (pyfa's defaults
  otherwise); support squadrons aren't ranked (they deal no damage). Checked by `check_weakness_picks.py`.
- Keep at Range on the Damage Application card and the fight strip (v2026.10.14.53, fight setup F2; the owner 2026-10-24).
  pyfa's damage graph has no such movement; it is mapped onto the graph's own inputs. The ship keeping range moves
  straight away along the line of sight (angle 180°, so no transversal, pyfa `_calcAngularSpeed`) at the other ship's
  closing speed (its speed when it approaches; 0 when it sits still, orbits or keeps range too), capped at its own
  top speed. It isn't offered inside the other ship's scram or web range or when the other ship closes faster than
  it can fly; chosen and then no longer possible, it stays chosen, marked, with the speed capped. The chart stays a
  snapshot at one distance, as pyfa's graph. Checked by `check_matchup.py` (the inputs and the "can hold" rule, written
  again) and `fight_strip_check.py`.
- EVE's closed-form capacitor stability, on ring hover (pyfa computes it as `cap_stable_eve` but doesn't display it).
- Rounding of the tool's own values (missile application % and applied DPS in the ammo ranking, the ring's drawing geometry) stays JavaScript's `Math.round`. Every pyfa stat the tool shows is rounded with `pyRound` (Python `round()`, ties to even) since v2026.10.14.22.

## 4. Not modeled (gaps, not choices)

Each is in a backlog:

- overheating
- bomb launchers (ship-fitted) and the Disruptive Lance; heavy fighters' Launch Bomb is off by default as in pyfa (switch it on in the Fighter bay, v2026.10.14.71)
- drone hit points
- effect beacons (wormhole and incursion system effects)
- projected effects (remote reps on the target; command bursts received from a fleet booster -- the booster's OWN bursts are listed on its EWAR / Misc card since v2026.10.14.26, they don't change its own stats, as in pyfa)
- damage application, partly (v2026.10.14.34 added the engine, PYFA CORE `application`; the page shows it in
  the "Their damage on you" card since v2026.10.14.36, turret-application-plan.md Phase 2b): pyfa's damage graph is ported for turrets, missile
  launchers, Vorton Projectors and smartbombs with pyfa's graph defaults (lock range ignored unless asked,
  target resists ignored). Drones since v2026.10.14.40 (getDroneMult; the owner "port drone application first").
  Fighters since v2026.10.14.64 (getFighterAbilityMult per damage ability; the owner 2026-10-25, the fighters' MWD
  ability off as pyfa's default). Not yet: drones and fighters on a hull record without dogma effects (fallback path,
  their DPS stays raw, `application.unapplied`, named under the chart), bombs, doomsdays and breacher pods. Effect
  beacons that change fighters (a Metaliminal Plasma Firestorm's explosion radius, pyfa Effect8114) aren't modelled,
  like every system effect. Since v2026.10.14.35 (Phase 2a, PYFA CORE `projected`) the engine also
  has pyfa's `applyProjected` (on by default in pyfa's graph): the attacker's own webs, target painters, web /
  painter drones, burst projectors and warp scramblers (a scrammed target's MWD, MJD and MJFG are ignored)
  slowing and growing the target fit or profile. Since v2026.10.14.70 that includes **support fighters' webs** (Dromi,
  pyfa `getProjFighterData`: one mobile web per squadron in space with its web on). Support fighters' neutralizers, ECM and
  warp disruption (Cenobite, Scarab, Siren) are shown on the EWAR / Misc card with pyfa's modified numbers but not applied,
  as pyfa's damage graph doesn't apply them either (and module neutralizers aren't applied to the times)
- mode effects on stats the tool doesn't show: remote repair and remote shield boost amounts (Confessor / Svipul Defense; their capacitor need *is* applied), weapon-disruption and sensor-dampener resistance (every Sharpshooter mode)

**Hand-built tables not yet replaced by pyfa-derived ones:** none. Firepower was replaced in v2026.10.14.3 (P1); fighter
abilities and Fighter Support Units followed in v2026.10.14.4, resistances (P2)
in v2026.10.14.5, ship modes (every hull with modes, every mode stat) in
v2026.10.14.6, missile flight range (pyfa's `Module.missileMaxRangeData`) in v2026.10.14.7, speed / agility / mass / align time (P3) in v2026.10.14.8, and every EWAR module value (P4: range, falloff, strength, neutralizer / nosferatu amount, with skills, hull, subsystems, rigs and loaded scripts) in v2026.10.14.11.

**Resistances** (P2) moved to pyfa's handlers in v2026.10.14.5: hull, module, script,
Compensation-skill and mode effects are generated (`gen_resist_table.py`), and the Reactive
Armor Hardener is pyfa's own algorithm. The tool no longer clamps a resonance at 3%: pyfa
only caps it at the max-resonance attributes.
