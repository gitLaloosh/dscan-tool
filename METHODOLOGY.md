# How the numbers are worked out

This was the "How effective HP and DPS are calculated" note at the bottom of every fit, one long paragraph. the owner
(2026-10-24): "At this point it's impossible to read and comprehend in that format. perhaps it needs to be it's own
document." It moved here in v2026.10.14.51, split into sections and brought up to date. The short version of each
section is behind the matching card's ⓘ button on the page (`CARD_INFO` in index.html).

Everything follows pyfa (the verified version is in `tools/pyfa_core_manifest.json`). Where the tool deliberately
differs, it's listed in `DEVIATIONS.md`. **Treat every number as a ceiling, not a guarantee:** all skills are assumed
at level V, so a less-trained pilot with fewer damage modules hits softer and tanks less.

## Effective HP and resists (Resistance card)

- **Resist sources:** every source pyfa applies to the fit, with pyfa's own rules:
  - Damage Control, hardeners, amplifiers, membranes and resist rigs;
  - a Bastion Module and hardener scripts;
  - a Tactical Destroyer's Defense Mode;
  - the hull's own resist bonuses (special-edition hulls included);
  - Shield and Armor Compensation skills at V.
- **Stacking penalties** follow pyfa's groups:
  - hardeners, amplifiers and rigs penalize each other;
  - Damage Control, a Bastion Module and a Reactive Armor Hardener penalize each other in a separate group;
  - hull bonuses aren't penalized.
- **Reactive Armor Hardener:** simulated exactly as pyfa does by default, against an even 25% per type incoming
  profile, after every other resist source. Its real split depends on the incoming damage, which a killmail can't
  reveal.
- **Polarized weapons:** a fitted Polarized weapon sets every resist to 0%, as in the game.
- **Hit points:**
  - the hull's base HP;
  - plus plates, shield extenders, and Reinforced Bulkheads / Nanofiber Internal Structure (flat HP or a multiplier,
    whichever the module uses);
  - plus Trimark Armor Pump and Core Defense Field Extender rigs, minus other rigs' HP drawbacks;
  - plus Shield Management, Hull Upgrades and Mechanics at V.
- **Strategic Cruisers** (Tengu, Legion, Proteus, Loki): subsystems count like any other module. That includes flat
  shield and hull HP, and any hardener-style resist a Defensive subsystem carries.
- **EHP** is each layer's HP against an even mix of the four damage types.

## Repairs and Break Point (Resistance card, Repairs strip)

- **Sources:** a fitted Shield Booster, Armor Repairer or Hull Repairer, from the module's own repair amount and cycle
  time.
- **Armor and hull:** Repair Systems / Capital Repair Systems at V (25% faster cycling).
- **Shield Booster:** gets no skill bonus. Its required skill, Shield Operation, only speeds up passive shield
  regen, not the booster. This is a real asymmetry in the game, not an oversight.
- **Passive shield regen:** its peak (reached near 25% shield), 2.5 × shield HP ÷ recharge time.
- **Break Point:** the sustained DPS an attacker needs to outpace that layer's repair or regen. A dash means the layer
  has no repair module (pure buffer), not a missing number.
- **Ancillary Armor Repairer:** also shows a burst figure while its Nanite Repair Paste lasts, because its repair
  amount roughly triples then.
- **Ancillary Shield Booster:** its Cap Booster charges only change where the activation cost comes from, not the
  repair amount.

## DPS (Firepower card)

- **Turrets and launchers:** DPS is calculated per weapon.
  - First from the exact charge that weapon had loaded (the same killmail flag as the gun).
  - Only when a gun has no identifiable loaded charge, from a category-matched guess at spare ammo in cargo or the
    fleet hangar. Total and Weapon DPS then show a range, and the ammo is listed at the bottom of the card.
- **Other sources:** drones, fighters and fixed-damage weapons. Smartbombs cycle 25% faster with Energy Pulse Weapons
  at V.
- **Vorton Projector (EDENCOM):** trains on its own three-skill tree, not the turret skills, and is scored with that.
- **Drones:** only as many as the hull can have in space at once (the lower of max active drones and drone
  bandwidth), hardest-hitting first, not every drone in the bay.
- **Fighters** (carriers, supercarriers, FAXes): only as many squadrons as the hull's launch tubes and per-class
  (light / support / heavy) limits allow, hardest-hitting first, then support squadrons in the tubes left (webs
  first). Since v2026.10.14.66 you choose them in the Fighter bay: one square per squadron, and each type's
  abilities (the game's icons) on or off. A damage ability switched off adds nothing; a speed ability switched on
  makes the squadron faster in the fight, as pyfa's handler does. Support squadrons' EWAR isn't in the numbers yet.
- **Skills, all at V:**
  - Turrets and missiles: damage and rate-of-fire skills (Surgical Strike / Rapid Firing, or Warhead Upgrades /
    Rapid Launch), plus the weapon-size and T2 Specialization skills.
  - Drones: damage-only skills (Drone Interfacing, the size skill or Sentry Drone Interfacing, racial Drone
    Specialization on T2 drones).
  - Fighters: damage-only skills (Fighters, Drone Interfacing's fighter bonus, Heavy Fighters, racial Fighter
    Specialization on T2 light squadrons).
  - Drones and fighters have no rate-of-fire skill.
- **Damage modules and rigs:** Gyrostabilizer, Magnetic Field Stabilizer, Heat Sink, Ballistic Control System, Drone
  Damage Amplifier, the rate-of-fire rigs, Bay Loading Accelerator and Warhead Calefaction Catalyst rigs, and Sentry
  Damage Augmentor rigs on sentries. Each is stacking-penalized against its own kind.
- **Hull bonuses:** the hull's role and skill bonuses at V (a Vexor's hybrid damage, a Drake's kinetic missiles). On a
  Strategic Cruiser the bonus comes from the fitted Offensive subsystem instead.
- **Siege-type modules:**
  - **Bastion Module** (Marauders): doubles turret and launcher rate of fire while running.
  - **Siege Module** (Dreadnoughts): a much larger flat damage bonus. Turrets get damage only; launchers get damage
    and rate of fire.
  - **Industrial Core** (Rorqual / Orca / Porpoise): doesn't affect turrets or launchers. While running it adds a
    large stacking-penalized drone damage bonus (+100% on a Capital Industrial Core II), boosts and speeds up local
    shield boosters, and multiplies scan resolution.
  - **Triage Module** (Carriers): no effect on weapon damage or rate of fire.
  - All four run by default and immobilize the ship while running, so a fitted one shows 0 m/s. Siege, Triage and
    Industrial Core also multiply mass by 10, which shows in align time.
- **Volley:** one shot from every weapon, drone and fighter at once, exactly as pyfa's Volley. It's the instant alpha,
  not a sustained rate, so it ignores different cycle times.

## Weapon range (Firepower card's weapon rows)

- **Turrets:** optimal + falloff with the loaded ammo, Sharpshooter / Trajectory Analysis at V. A Vorton Projector
  uses Vorton Arc Extension instead.
- **Missiles:** the flight range as pyfa computes it: flight time plus the ship-radius bonus, flown in whole seconds,
  with acceleration, measured from the ship's surface, capped for auto-targeting missiles. Hover it for the two
  possible distances. Missile Projection / Missile Bombardment at V.
- **Bonuses included:** the hull's or subsystem's range bonuses, Tracking Enhancers and Computers (with a loaded
  Optimal Range or Tracking Speed script), Missile Guidance Enhancers and Computers (with their scripts), range rigs,
  a Bastion Module, and a Tactical Destroyer's Sharpshooter Mode. All stacking-penalized as pyfa does.
- **What range is not:** this is how far a weapon reaches. How much of its damage *lands* at a distance depends on
  the target's signature and speed; that is on the Damage Application card (pyfa's damage graph).
- **Not shown:** weapons only resolved through the cargo-ammo guess, and drones, whose engagement range is up to
  their pilot.

## Module states (Fit card)

- **When bonuses apply:** as in pyfa, only in the state that turns them on. A hardener, repairer, weapon or
  propulsion module needs to be running; most other modules only need to be online. Only running modules use
  capacitor.
- **Default states:** a killmail doesn't say what was running, so every module starts running if the game allows
  it, with these limits:
  - one propulsion module at a time (the fastest);
  - only as many Command Bursts or similar as the hull permits;
  - cloaks, Micro Jump Drives and Field Generators, a Signature Suppressor's burst, Entosis Links, Capital Sensor
    Arrays and an Assault Damage Control's burst start online, not running.
- **Changing states:** switch any module off, online or active on the Fit card and every number recalculates. The
  game's rules still apply: one propulsion module running at a time, Bastion blocks the Micro Jump Drive, and so on.

## The fight (Damage Application card, Matchup and its strip)

- **Damage applied:** pyfa's damage graph, at one distance and one movement for each ship, with the attacker's own
  webs, target painters and scram applied (pyfa's default). Resists aren't counted there; lock range is ignored.
- **A weapon with no charge loaded** (v2026.10.14.67): charted with the charge aboard that kills you fastest at this
  fight (the one the Weaknesses picks name first), marked "Assumed loaded" on the card and in the Matchup's hover.
  The Firepower card shows every charge aboard as a range.
- **Fighters** (v2026.10.14.64): each damage ability of each squadron in space (Attack and Missiles; bombs stay off,
  as in pyfa), pyfa's `getFighterAbilityMult`:
  - a squadron at least as fast as you follows you and has its full range; a slower one is put at the carrier's
    centre and hits only within its ability's range of it (Attack: optimal + falloff; Missiles: a hard limit). Its
    speed is pyfa's, with its MWD ability off (pyfa's default; the owner 2026-10-25), after skills (Light Fighters,
    Drone Navigation), hull bonuses, Drone Navigation Computers, Fighter Support Units and rigs; switched on in the
    Fighter bay (v2026.10.14.66), the MWD, afterburner or evasive maneuvers adds its own speed bonus, stacking-
    penalized with the computers as in pyfa;
  - then the explosion maths of missiles against your signature and speed;
  - superiority fighters' missiles deal 5% to a ship, heavy fighters' torpedoes 10% to anything that isn't a
    capital or freighter (the target ship's anti-fighter / anti-capital missile resistance; a hull without it has the
    attribute's default). The raw DPS on the Firepower card is pyfa's raw number (full damage); its hover says so.
- **Movements** (in-game names, for both ships):
  - **Stopped:** speed 0.
  - **Approach:** straight at the other ship (no transversal), at the chosen share of top speed.
  - **Orbit:** at 90° to the line of sight, at the chosen share of top speed.
  - **Keep at Range:** straight away from the other ship at the other's closing speed (its speed when it
    approaches, 0 otherwise), up to its own top speed, so the distance holds. Not offered inside the other ship's
    scram or web range, or when the other ship closes faster than it can fly.
- **What the chart marks** (v2026.10.14.54): their EWAR that reaches you, shaded from 0 out to its range with the
  EWAR / Misc card's letters and colours: **T** their warp scrambler and furthest web (the same inputs pyfa's graph
  applies), **D** their furthest target painter, **C** their furthest running neutralizer and nosferatu (each module's
  optimal range). Darker where two reach. Numbered pins mark their lock range and drone control range. The x axis
  prints their tackle distances and your range, the y axis the DPS there. Markers are presentation only; the lines
  are pyfa's.
- **Your card** (v2026.10.14.55, My Ship Perspective): the same chart for your guns on them: your ship as the attacker,
  the threat as the target with its fit's own speed and signature (its prop module as it runs), your webs, painters
  and scram applied, the same fight. Its number is the board's "DPS applied to them".
- **The range** (v2026.10.14.56) runs to whichever ship reaches farther (weapons, drone control range, a fighter
  ability's range from the carrier's centre (v2026.10.14.64), or 1.25 × its default range), on both cards and the
  strip; with no ship saved, to the threat's reach.
- **One fight:** the strip under the Matchup and the card's Adjust panel set the same values, and both perspectives
  use them. The chart is a snapshot at that distance, as pyfa's graph: it doesn't play the fight out over time.
- **They last / you last** (not a pyfa number): damage by type against each layer's resists, shield then armor then
  hull, minus that layer's local repairs and the shield's peak passive regen, with the repairs stopping when pyfa's
  capacitor simulation runs dry. An Ancillary Shield Booster on charges (v2026.10.14.57) doesn't need the capacitor:
  it reps for a clip (an X-Large with Navy Cap Booster 400s: 9 cycles, 45 s), reloads for 60 s, and repeats while
  charges last (loaded plus hold), then stops. An Ancillary Armor Repairer with Nanite Repair Paste (v2026.10.14.61)
  repairs 3x for its clip (8 cycles; a Medium with Repair Systems V: 72 s) from when the armor starts taking damage,
  reloads for 60 s with no repair, repeats while paste lasts, then repairs its plain amount; it needs the capacitor
  either way. A killmail with no paste seen assumes a full clip. "holds" means the damage never gets through.
  - Not used, kept here so it can be brought back: pyfa's "factor in reload" average for an ASB, its rate x
    (clip x cycle) / (clip x cycle + reload) for the whole fight (84 HP/s instead of 196 for an X-Large with
    Navy Cap Booster 400s). It hides the reload gap, which is where a ship running an ASB usually breaks.
  - **Why** (v2026.10.14.58): hover a time on the board (tap it on a phone) for a sentence or two from the same
    steps: layers with no repairer together ("With no armor or hull repairer, the rest goes in 21 s."), and for a
    layer with one, what its repairers were doing when it broke: an ASB reloading ("21 s into your X-Large Ancillary
    Shield Booster's first reload"), out of charges ("then has nothing left to load"), the capacitor run dry, or still
    repairing ("even with ..."). Clock times (1:06) count from the start of the fight.
