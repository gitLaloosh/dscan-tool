# dscan-tool regression suite

> Before changing a calculation, read `../LESSONS_LEARNED.md`, the catalog of mistakes made in this project and the method that works for each. Expected values for golden fits come from `../tools/independent_checks/`, never from the tool's own output.

## Why this exists

On 2026-09-10 we found that THREE previously-found, previously-validated
bugs in the EHP/resistance code (Damage Control pooled into the stacking
array instead of applied as its own independent multiplier; the 20%
Compensation-skill assumption applied unconditionally instead of gated on a
qualifying hardener; fitted-module quantity collapsed to 1 copy instead of
the real fitted count) had all silently regressed back into
`claude/dscan-tool_15.html` — bugs that earlier sessions had already found,
fixed, and validated against real killmails (see `dscan-tool.md` in memory).

The most likely mechanism: a later session (the 340-ship SHIP_ROLE_BONUS
audit) worked from an offline copy of the file made for its own tooling,
and that copy predated the resistance fixes from an earlier point in the
same long-running session. When that audit session delivered its result,
it silently overwrote the newer fixes with the stale copy's version — and
because no regression suite was ever persisted anywhere durable, nobody
caught it until a user-reported fit exposed the wrong numbers weeks later.

Later the same day, re-verifying against a real Ishtar killmail turned up
TWO MORE regressions of the same kind (RESISTANCE_BONUS_ATTR being used as
a raw fraction instead of divided by 100; the Ishtar-family sentry/combat
drone bonus split being entirely absent) — bugs the Legion fit alone could
never have caught, since it has no hardener and no drones. That's the
reason this suite deliberately spans fits with different module/weapon
mixes rather than just adding more Legion-like entries.

Then, relayed from a DIFFERENT session (not directly accessible — the user
pasted its findings and its own pyfa-verified fits into chat), a much
bigger DPS bug was found and fixed the same day: see "The turret/missile
DPS fix" below.

## The rule, going forward

**Before delivering ANY change to dscan-tool.html — to the user via
SendUserFile, to their local folder via device_commit_files, or to the
Claude Project doc via project_write — run this suite against the
candidate file and confirm ALL PASS:**

```
node run_regression.mjs                      # tests ../index.html (the live tool)
node run_regression.mjs /path/to/candidate.html
```

If a fit that used to pass now fails, that is a regression. Do not deliver
until you understand why, and either fix the real bug or (rarely) update
`golden_fits.json`'s expected values *explicitly and visibly* — never
silently.

(The tool was renamed from `dscan-tool.html` to `index.html` at the repo
root on 2026-10-12 so GitHub Pages serves it at the site root.)

**Before starting any edit**, re-read the CURRENT canonical file fresh —
either the Claude Project doc (`claude/dscan-tool_15.html`, via
`project_read`) or this local folder's copy — rather than trusting a copy
sitting in scratch/session workspace from earlier in a long session,
especially if other edits may have landed on the canonical copy since that
scratch copy was made. If you need an offline copy for some tooling
(decoding SDE data, batch-processing hundreds of entries, etc.), treat it
as **read-only reference data**, and reapply whatever changes it produced
onto a freshly-read copy of the canonical file before writing anything
back — never deliver the offline copy itself.

## The turret/missile DPS fix (2026-09-10, second half of the day)

Every fit in this suite had shown turret or missile DPS well below (or, for
one Hawk-mixed-fit case, above) real pyfa targets — Legion lasers ~28% low,
Ishtar autocannons ~28% low, Caracal missiles ~13% low. A separate session
(inaccessible directly to this one — its findings were relayed by the user
via chat, along with two of its own real pyfa-verified fits, Hawk and
Rifter) root-caused the dominant piece of this: the tool's `MAX_TURRET_*`
and `MAX_MISSILE_*` constants modeled the weapon Specialization skill
(Small/Medium/Large Turret Specialization, Rocket/Light Missile/etc.
Specialization) as a DAMAGE bonus. It's actually a RATE-OF-FIRE bonus
(+2%/level). The real, previously entirely-unmodeled damage bonus is the
weapon-SIZE-CLASS skill itself (Small/Medium/Large [X] Turret; Rockets/
Light Missiles/Heavy Missiles/Torpedoes — +5%/level damage, so +25% at V) —
a bigger single source of error than any other DPS bug found this project.
Confirmed by reconciling a real pyfa Hawk fit's rocket-only volley/DPS to
within 0.5%.

Fixed the same day, in this order:
1. `MAX_TURRET_DAMAGE_MULT`/`MAX_TURRET_ROF_MULT`/`MAX_MISSILE_DAMAGE_MULT`/
   `MAX_MISSILE_ROF_MULT` corrected to include the real weapon-size-class
   damage skill and the real, fuller RoF skill chain (Gunnery for turrets;
   Missile Launcher Operation + weapon-size-class Specialization for
   missiles, alongside the pre-existing Rapid Firing/Rapid Launch).
2. Weapon rate-of-fire rigs (`Rig Projectile Weapon`, `Rig Energy Weapon`,
   `Rig Hybrid Weapon` — the Burst Aerator family) were being silently
   ignored entirely (not in `MODULE_DAMAGE_GROUP_CATEGORY` at all). Added.
   (There's no turret *damage* rig in EVE — Locus Coordinator rigs sharing
   those same groups are range-only and carry neither relevant attribute,
   so adding the group is safe.)
3. Ship/skill damage role bonuses can be restricted to ONE damage type in
   real EVE (confirmed for the Hawk: its Assault Frigates bonus only ever
   touches kinetic damage) even though the tool grants the bonus to a whole
   weapon CATEGORY. Applying it unconditionally overstated DPS whenever the
   loaded ammo was a different type. `SHIP_ROLE_BONUS` entries now support
   an optional 4th element (a damage-type string) and the bonus is only
   applied when the loaded ammo's dominant damage type matches; Hawk's
   entry is now tagged `"kin"`. This is currently the ONLY entry tagged —
   the other ~339 ships were NOT re-audited for this (that's the same
   340-ship audit whose earlier work already regressed once; a full
   re-audit is future work, tracked below).
4. The `RECS` table (drives the "recommended ammo to exploit this weakness"
   display text only — never a DPS/EHP calculation) had two missile family
   names swapped: it said `em → Nova` and `exp → Mjolnir`, but live ESI
   ammo dogma data confirms Mjolnir is the EM-damage family and Nova is the
   Thermal-damage family (Inferno is Explosive, Scourge is Kinetic — that
   one was already correct). Corrected to `em → Mjolnir`, `therm → Nova`,
   `exp → Inferno`. Purely cosmetic; doesn't change any golden fit's
   expected values.

After fix #1 above, the golden fits' `expected` DPS ranges were
re-finalized against the fixed tool's own output (see `golden_fits.json`);
all five fits now pass, including a brand-new `rifter_user` entry whose
`expected` block had been left as a placeholder in an earlier pass.

Net effect across this suite: Legion 494→624 (target 686, 72%→91%), Ishtar
turret-only ~31→~40 (target ~43, 72%→93%), Rifter (new) 175 (target 192,
91%) — a large improvement across every TURRET fit. Caracal (missile,
Light Missiles specifically) went 292→409 against a 335.1 target — WORSE,
now 22% high instead of 13% low. This means the weapon-size-class skill's
value is NOT uniform across missile families the way it was assumed to be
(confirmed uniform +25%/V for Rockets only, via the Hawk fit) — a concrete,
narrowed-down open item for whoever next has a pyfa-verified Light Missile
fit to reconcile against.

## Osprey Navy Issue fixes (2026-09-10, third pass the same day)

A real pyfa-verified Osprey Navy Issue fit (3x Rapid Light Missile Launcher
II/Caldari Navy Nova Light Missile, 2x Ballistic Control System II, 5x
Acolyte II) came back with the tool badly overshooting weapon DPS (603 vs
pyfa's 268 — more than 2x) and undershooting drone DPS (47 vs pyfa's 86.6).
Two real, separate bugs, both fixed:

1. **SHIP_ROLE_BONUS untagged-bonus regression, again.** Osprey Navy Issue's
   entry stored `[[missile,damage,125],[missile,damage,100]]`, both
   UNTAGGED (universal, applies to any damage type). Live ESI dogma_effects
   show the truth: a 100% bonus that really is universal (its three
   per-type effects — em/therm/exp — all share one modifying attribute,
   487) PLUS a separate, additional 125% bonus that is KINETIC-ONLY (a
   different modifying attribute, 1535, effect 6351). This ship was
   explicitly documented in `dscan-tool.md` (memory) as already fixed by an
   earlier 340-ship audit — this is the SAME regression pattern that has
   hit this project repeatedly (a stale offline copy silently overwriting a
   real fix on delivery). Tagged the 125% entry `"kin"`; left the 100%
   entry untagged. This fit's ammo is Explosive (Nova Light Missile), so
   only the universal 100% should apply — fixing this took weapon DPS from
   603 to an EXACT match with pyfa's 268.
2. **Drone DPS never applied a drone's own intrinsic damage multiplier.**
   Every combat drone carries a `damageMultiplier` attribute (64 — verified
   via ESI's own attribute metadata: "Damage Modifier... high_is_good" —
   the exact same attribute a turret's loaded charge already used in this
   tool), and the drone DPS loop never multiplied it in at all. Acolyte II
   (1.68), Berserker II (1.56), Caldari Navy Vespa (1.8) all carry a non-1
   value. Fixed by multiplying it into `dmgPerCycle`, same as turrets
   already do with their charge's multiplier. Took the Osprey's drone DPS
   from 47 to 79 against pyfa's 86.6 (91% — the same ~90% residual band
   seen on every turret/missile fit in this project, not fully resolved but
   a large, independently-verified improvement).

Also RE-corrected the RECS ammo-name table from earlier the same day: an
first attempt at fixing "Nova/Mjolnir swapped" got Nova and Inferno backwards
(assumed Nova=Thermal/Inferno=Explosive without checking). Direct ESI dogma
checks on all four Rage Rocket AND Light Missile variants confirm the real
mapping: Mjolnir=EM, Scourge=Kinetic, Nova=EXPLOSIVE, Inferno=THERMAL. Fixed
for real this time — cosmetic only, never touched DPS/EHP math.

Side effect of fix #2: this suite's `ishtar_zkb137694046` entry's `droneDps` (which
shares two of the same drone types — Acolyte II and, via its own hull's
role bonus stacking, similarly-affected types) changed from 379 to 611. The
old 379 was only ever checked against this tool's own prior output on that
killmail, never independently against pyfa — so it wasn't a real
validation, and the new 611 is believed more correct (same standard as
everywhere else: validated directly against an outside pyfa export, on the
Osprey). `expected` widened to a 590–630 range since no independent pyfa
target exists for this specific Ishtar drone bay.

## Megathron armor/EHP fixes (2026-09-10, fourth pass the same day)

A real pyfa-verified Megathron fit (7x Neutron Blaster Cannon II/Void L, 2x
1600mm Steel Plates II, Reactive Armor Hardener, 2x Multispectrum Energized
Membrane II, 3x Large Trimark Armor Pump I) came back with armorHP well
short of pyfa's target (111.5k vs pyfa's 146k, 76%) even though shield and
hull matched almost exactly. Two real, separate, previously-undiscovered
bugs, both fixed:

1. **The universal Battleship role bonus was entirely unhandled.** Live ESI
   dogma_effects show every T1/navy battleship (confirmed identical on 9
   different hulls: Megathron, Raven, Tempest, Scorpion, Apocalypse,
   Armageddon, Typhoon, Dominix, Rokh, Hyperion — effect 8377,
   "BattleshipRoleBonusArmorPlate&ShieldExtenderHP") carries a role bonus
   that boosts a fitted Armor Plate's own flat armor-HP attribute by +50%
   and a fitted Shield Extender's own flat shield-HP attribute by +100% —
   read directly off the ship's own attributes 3266/3267 (a
   `LocationGroupModifier`, so it targets those two specific module groups
   only, not the ship's base HP or any other HP source). The tool never
   applied this at all. Fixed generically (not hardcoded per-hull): read
   `attrVal(shipDogma, 3266/3267, 0)` once, apply to `ARMOR_HP_FLAT_ADD_ATTR`
   contributions from `Armor Plate` group items and `SHIELD_HP_FLAT_ADD_ATTR`
   contributions from `Shield Extender` group items respectively — so it
   correctly applies to any battleship carrying it, not just this one.
2. **Reactive Armor Hardener was modeled as a static flat 15%/15%/15%/15%
   split.** It had been folded into the same direct-multiply path Damage
   Control uses (both carry the same 267-270 attribute ids), but in real EVE
   (and in pyfa — its `eos/sim/reactive_armor_hardener.py` was fetched and
   read directly this session) it continuously shifts a fixed 6%-per-cycle
   chunk of resistance FROM whichever damage type(s) it's taking the LEAST
   of TOWARD whichever it's taking the MOST, converging to a settled (or
   short-looping) state rather than sitting flat. Ported pyfa's exact
   donor/recipient/loop-detection algorithm, assuming a uniform (25% each
   type) incoming damage profile (pyfa's own default when no custom pattern
   is set — the only reasonable assumption with no actual incoming-fire
   context). Validated directly against this fit: simulated convergence
   gives 75.1%/72.0%/71.5%/71.0% EM/Exp/Kin/Therm resistance vs pyfa's
   reported 75%/71%/71%/71% — an almost exact match.

Also uncovered (a methodology note, not a tool bug): mid-investigation, a
batched multi-item ESI fetch from this session's own browser tab returned
Damage Control II's dogma_attributes MISSING its shield-resistance attributes
(271-274, its +12.5% shield bonus) — apparently a stale/incomplete cached
response, since a solo re-fetch of the same type with `cache:'no-store'`
came back complete. Worth remembering: an unexplained gap in fetched ESI
data is worth a cache-busted re-fetch before concluding it's real.

After both fixes: armorHP 148581 vs pyfa's 146000 (102%), shieldHP 13655 vs
pyfa's 13700 (99.6%), hullHP 25653 vs pyfa's 25700 (99.8%), totalHP 187889
vs pyfa's 185000 (101.6%) — all close matches now. Weapon DPS (dpsFixed)
1086 vs pyfa's 1195 weapon-only figure (90.9%) is the SAME already-tracked
~90%-of-target turret/missile DPS residual seen on every other fit in this
project — NOT re-root-caused here, left as the existing known open item.

Ran the full regression suite (all 6 prior fits) after making these changes
— none of them fit an Armor Plate, Shield Extender, or Reactive Armor
Hardener, so ALL PASS unchanged, confirming no regression.

## Turret Specialization-skill DPS fix (2026-09-10, sixth pass, final pass the same day)

After the Megathron armor/EHP fixes above (fourth pass), the user explicitly
pushed back on leaving the Megathron's turret DPS at the already-known
~90%-of-target residual (1086 vs pyfa's 1195, "100 DPS difference is pretty
significant") rather than accepting it as an open item. Root-caused this
time, all the way, grounded in live ESI data:

**Every T2 ("...II") turret module carries a THIRD required-skill attribute
(184 = `requiredSkill3`) pointing at a per-subtype "Specialization" skill**
— e.g. Neutron Blaster Cannon II (type 3186) requires Large Blaster
Specialization (type 12212). Fetched that skill's own ESI record directly;
its description reads verbatim: *"2% Bonus per skill level to the damage of
large turrets requiring Large Blaster Specialization."* That's a DAMAGE
bonus — not a rate-of-fire bonus, which is what the earlier same-day
"turret/missile DPS fix" section above had assumed for the whole
"Specialization" skill family (it was right about missiles, wrong about
turrets — the two families are structured differently and were conflated).

Checked all 15 live turret Specialization skills that exist (Small/Medium/
Large × Blaster/Railgun/Autocannon/Artillery/Pulse Laser/Beam Laser, ids
12201-12215, plus 12212): every single one is worded identically, 2%/level,
so +10% at level V — a uniform, generic bonus, not something that needs a
per-subtype lookup table.

Confirmed this is T2-only, so it can't just be added as a flat constant:
"Neutron Blaster Cannon I" (type 573, T1) has only `requiredSkill1`/
`requiredSkill2` (182/183) and NO `requiredSkill3` at all. Missile launchers
were also checked (e.g. Heavy Missile Launcher II, type 2410) and never
carry a `requiredSkill3` either — this fitting-requirement mechanic is
turret-specific, so missile DPS is correctly untouched by this fix.

**Fix**: added `REQUIRED_SKILL_3_ATTR` (184) and `TURRET_SPECIALIZATION_MULT`
(1.10) constants; at both turret-DPS computation sites, the per-weapon
`weaponDogma` is checked for attribute 184's presence, and if present,
`MAX_TURRET_DAMAGE_MULT` is multiplied by the extra 1.10 for that weapon
only — T1 turrets (no attribute 184) are correctly left unaffected.

Two of this suite's turret-fixture captures (`legion_owner`'s Heavy Beam
Laser II, and originally the Megathron fixture before the fourth-pass fix)
had been captured with an incomplete/reduced `dogma_attributes` list missing
attribute 184 — patched both to the real, complete ESI record so the
regression suite actually exercises this fix rather than silently skipping
it.

**Results — three independent EXACT matches to real pyfa targets**:
- Megathron: 1086 → **1195** (pyfa: 1195)
- Legion: 624 → **686** (pyfa: 686)
- Rifter: 175 → **192** (pyfa: 192)

All three `golden_fits.json` entries pinned to these exact values
(`tolerancePct` 1%), replacing the old wide `_min`/`_max` ranges that had
been set specifically to tolerate this bug. Ishtar's turret component (its
125mm Gatling AutoCannon II fixture already had the full attribute set) also
picked up the fix automatically; its existing 630-670 combined range still
passes (655) with no change needed. Ran the full 7-fit suite after — ALL
PASS.

This resolves the "unconfirmed weapon-race-specific skill level" residual
that the earlier turret/missile DPS fix section (and several "Known open
items" below) had flagged as the suspected cause of the ~90%-of-target
turret DPS band seen across Legion/Ishtar/Rifter/Megathron. It was this
missing Specialization-skill damage bonus all along.

## Dominix Navy Issue validation (2026-09-10, seventh pass — confirms the turret Specialization fix generalizes)

Immediately after the turret Specialization-skill fix above, the user supplied
a second real pyfa-verified battleship fit to stress-test it further: a
"buffer" Dominix Navy Issue (6x Electron Blaster Cannon II/Void L — note:
Electron Blaster Cannon is a *different* large-blaster tier than the
Megathron's Neutron Blaster Cannon — plus 3x 1600mm Steel Plates II, DC II,
2x Multispectrum Energized Membrane II, Reactive Armor Hardener, 3x Large
Trimark Armor Pump II, drone bay 5x Berserker II + 5x Ogre II).

Results: weapon-only DPS (the Void L breakdown) is **629 — an EXACT match**
to pyfa's reported 629, on a different hull and a different blaster tier
than the Megathron fit that found the bug. shieldHP (20591 vs 20.6k) and
hullHP (37624 vs 37.6k) are exact/near-exact matches; armorHP (263995 vs
260k, 101.5%) and totalHP (322210 vs pyfa's 318k EHP figure, 101.3%) land in
the same known ~101-102% RAH-simulation-approximation band already seen on
the Megathron (same module, same convergence behavior).

**One real, non-bug discrepancy surfaced and is worth flagging explicitly**:
this tool's own `dpsFixed` field (1061) combines weapon + drone DPS and
always credits the full drone bay (Berserker II x5 + Ogre II x5 = 432
droneDps here) as active. pyfa's own readout for this fit showed `Drone: 0`
— the fit as captured in pyfa had no drones actually assigned/launched in
its simulator. This tool intentionally assumes a full drone bay as a
threat the pilot COULD deploy (appropriate for a threat-assessment tool),
so `dpsFixed` is pinned to the tool's own combined 1061, not pyfa's
weapon-only 629 — this is a deliberate modeling difference, not a bug, but
worth keeping in mind when comparing this tool's totals directly against a
pyfa fit that has drones sitting unlaunched.

Added as an 8th golden fit (`dominix_navyissue_buffer`) per the standing
policy of golden-listing every fit confirmed accurate. All 8 fits ALL PASS.

## Caracal Light Missile DPS — resolved as NOT a bug (2026-09-18)

The open item below ("Caracal (missile DPS, Light Missiles): now 22% HIGH
against a 335.1 target") was investigated end-to-end this session. Every
multiplier in the chain was re-verified against a primary source, none of
them relying on the 335.1 figure itself:

- **Caracal (type 621) hull traits** — fetched fresh from everef.net (an
  SDE-backed reference site, not ESI, since ESI's `/dogma/effects/` endpoint
  doesn't expose the group filter for this effect): confirmed the Caldari
  Cruiser skill grants exactly "5% bonus to Rapid Light Missiles, Heavy
  Missiles and Heavy Assault Missiles Launcher rate of fire" and nothing
  else — RoF only, no damage bonus, 25% at level V. This matches
  `SHIP_ROLE_BONUS["621"] = [["missile","rof",25.0]]` exactly.
- **Ballistic Control System II (type 22291)** — re-fetched fresh from ESI:
  attribute 213 (missile damage bonus) = 1.1, attribute 204 (speed/RoF
  multiplier) = 0.895. Matches the tool's existing constants unchanged.
- **Rapid Light Missile Launcher II (type 1877) and Mjolnir Fury Light
  Missile (type 2613) required-skill chains** (fetched earlier the same
  session): confirm the same Missile Launcher Operation + Rapid Launch +
  Light Missile Specialization (RoF-only skills) and "Light Missiles"
  (damage skill, 5%/level) structure that `MAX_MISSILE_DAMAGE_MULT`/
  `MAX_MISSILE_ROF_MULT` already assume — the same skill structure already
  proven exact for Rockets via the Hawk fit.
- **Independent third-party corroboration**: a published fit guide (Fit
  Kitchen: Caracal, ashy.vargur.dev) describes a near-identical fit — 5x
  Rapid Light Missile Launcher II, 3x Ballistic Control System II, Mjolnir
  Fury Light Missile on a Caracal — and states it does "about 400 DPS",
  matching this tool's 409 and contradicting the 335.1 figure.

The `caracal_zkb136427798` fixture's own note had already flagged 335.1 as a
"pyfa/memory" value — i.e. never a confirmed fresh pyfa export, unlike
every other golden fit in this suite (which all quote a literal
user-supplied pyfa screenshot/export). With every input to the calculation
now independently verified and a third-party fit guide corroborating ~400
DPS, the conclusion is that **335.1 was a stale or misremembered reference
value, and the tool's 409 was correct all along** — no code change was
needed. `caracal_zkb136427798.expected.dpsFixed` is now pinned to the exact value
409 (previously a 395–425 range explicitly marked as not-a-claim-of-
correctness).

If a fresh, screenshotted pyfa export of this exact fit ever turns up and
disagrees with 409, that would immediately reopen this — but absent that,
this is now closed with the same evidentiary bar as the other pinned fits.

## What's in this folder

- `golden_fits.json` — validated real fits with their expected output
  (from the tool's own real reported stats or a user-supplied pyfa export,
  cross-checked against live ESI data and, where possible, pyfa's actual
  eos/effects.py source). Five entries:
  - `legion_owner` — T3 Strategic Cruiser, 6x Heavy Beam Laser II, DC II
    hull/armor/shield tank, no shield/armor hardener. Catches the DC
    independent-multiplier bug, the Compensation-skill gating bug, and the
    module-quantity-dedup bug.
  - `ishtar_zkb137694046` — drone/gun hybrid (2x autocannon + 3x Drone Damage
    Amplifier + 2 shield hardeners + non-sentry drone bay). Catches the
    RESISTANCE_BONUS_ATTR x100 bug and the sentry/combat drone bonus
    double-counting bug.
  - `caracal_zkb136427798` — missile boat (5x Rapid Light Missile Launcher II,
    3x Ballistic Control System II, IFFA Compact DC, 2x Large Shield
    Extender, 3x rig). Catches the module-quantity-dedup bug on a fit with
    THREE/TWO identical duplicate modules; also the fit that resolved the
    Light Missile DPS question (see the dedicated section above) —
    dpsFixed is pinned exact at 409.
  - `hawk_user` (new) — real pyfa-verified fit supplied directly by the
    user: 1x 150mm Light AutoCannon II + 4x Rocket Launcher II (mixed
    turret+missile on one hull), 2x Medium Ancillary Shield Booster,
    2x Small EM Shield Reinforcer I rigs. EHP is an exact match; this is
    also the fit that pinned down the turret/missile DPS fix above.
  - `rifter_user` (new) — real pyfa-verified fit supplied directly by the
    user: 3x 200mm AutoCannon II, 2x Gyrostabilizer II, a weapon RoF rig
    (Small Projectile Burst Aerator II — previously silently ignored, see
    fix #2 above). EHP is an exact match. NOTE: the user's fit text named
    the shield rig "Small Anti-EM Screen Reinforcer I", which doesn't exist
    in the SDE — substituted "Small EM Shield Reinforcer I" (the real item
    matching this tool's established naming convention); the exact EHP
    match is strong evidence this substitution was right, but it was an
    assumption, not a given — flagged to the user.
  - `osprey_navyissue_user` (new) — real pyfa-verified fit supplied
    directly by the user: 3x Rapid Light Missile Launcher II (Explosive
    ammo), 2x Ballistic Control System II, 5x Acolyte II drones. Weapon DPS
    is an EXACT match to pyfa (268) after the SHIP_ROLE_BONUS kinetic-tag
    fix above; hullHP is an exact match. This is the fit that caught both
    Osprey fixes above.
  - `megathron_owner` (new) — real pyfa-verified fit supplied directly by
    the user: 7x Neutron Blaster Cannon II/Void L, 2x 1600mm Steel Plates
    II, Reactive Armor Hardener, 2x Multispectrum Energized Membrane II,
    3x Large Trimark Armor Pump I, no drones. Catches the universal
    Battleship Armor Plate/Shield Extender role-bonus bug (only battleship
    fit in this suite), the Reactive Armor Hardener static-vs-simulated
    resistance bug (only RAH-fitted fit in this suite), and the turret
    Specialization-skill damage bonus bug (see sixth-pass section above).
    shieldHP/hullHP/dpsFixed are exact matches (dpsFixed pinned at 1195);
    armorHP/totalHP are ranges (small residual from the RAH-convergence
    approximation).
- `run_regression.mjs` — loads a dscan-tool.html, runs its own
  `estimateHpAndDps()` in a Node vm sandbox against each golden fit's real
  captured ESI data, and reports PASS/FAIL per fit. Supports both exact-
  match fields (any `expected` key with a same-named result field, checked
  within `tolerancePct`) and `<field>_min`/`<field>_max` range checks.

## Known open items (not bugs in this suite, tracked here so they aren't lost)

- **Legion / Ishtar / Rifter / Megathron (turret DPS) — RESOLVED** by the
  turret Specialization-skill fix above (sixth pass): Legion, Rifter, and
  Megathron are now EXACT matches to real pyfa targets (686, 192, 1195);
  Ishtar's combined dpsFixed (turret+drone) also improved and passes its
  existing range. The "unconfirmed weapon-race-specific skill level"
  residual suspected here was this missing Specialization-skill damage
  bonus.
- **Caracal (missile DPS, Light Missiles) — RESOLVED, not a bug**: see the
  dedicated section above. 409 is correct; the 335.1 target it was being
  compared against was an unconfirmed memory value. Pinned exact.
- **Hawk (mixed fit)**: the Rocket portion alone is an exact match to a
  real pyfa rocket-only reconciliation (137 vs 137). The full fit
  (rockets + 1 autocannon) computes 151 vs pyfa's reported 137 for the
  whole fit — a ~10% overshoot now attributable specifically to that one
  autocannon, not yet explained (a single T1 tracking-ammo autocannon has
  unusually low raw damage; why pyfa's total appears to already equal the
  rocket-only figure hasn't been root-caused).
- **SHIP_ROLE_BONUS damage-type tagging**: only Hawk (11379) and Osprey
  Navy Issue (29340) are currently tagged with a damage-type restriction.
  The ~338 other ships in this constant were NOT re-audited this session —
  the same 340-ship audit that originally covered this ground (per
  `dscan-tool.md` in memory) had its own results silently regressed at
  least twice now (Osprey Navy Issue itself was previously fixed and lost
  once already), and re-doing it properly — plus finding a way to make the
  fix actually stick this time — is real, separate future work.
- **Drone DPS residual**: after adding the drone's own damageMultiplier
  attribute, Osprey's Acolyte II drones land at 91% of pyfa's target — the
  same ~90% band as every turret/missile fit in this project. Not yet
  root-caused further (candidates: same unconfirmed skill-level residual
  suspected on the turret side).
- **Legion fit**: `armorHP`/`totalHP` still have a small residual gap
  versus the real tool's reported numbers (armorHP ~5% high, totalHP ~2%
  high) unrelated to DPS, traced to the raw pre-resistance HP pool —
  unresolved, low priority.
- **Reactive Armor Hardener simulation is an approximation, not exact**:
  it assumes a uniform (25% each type) incoming damage profile always,
  since the tool has no actual incoming-fire context to simulate against —
  pyfa lets the user set a specific damage pattern, which would converge to
  a different (sometimes very different) result. Also, pyfa's own
  simulation can land in different points of its repeating loop depending
  on exact tick timing; this tool's port averages over the same detected
  loop, which is very close but not bit-for-bit guaranteed identical (the
  Megathron fit landed 102% of pyfa's armor EHP, not exactly 100%). Good
  enough to catch the bug returning; not a promise of an exact match on
  every RAH fit.
- **Battleship Armor Plate/Shield Extender role bonus**: confirmed on 9
  different T1/navy battleship hulls this session, applied generically (not
  hardcoded per-ship) by reading the ship's own attributes 3266/3267 — so it
  should already cover every battleship, and any other hull CCP has since
  granted the same effect to, without needing a table entry. Not
  independently re-verified against a pyfa export for any hull other than
  the Megathron above.

Don't mistake any of these checks passing for "fully correct" — see
`dscan-tool.md` in memory for the full picture of what's still open.


## Module states (v2026.10.13.20)

A golden fit can carry an optional `moduleStates` object, passed to
`estimateHpAndDps()` as its 7th argument, the same way `tacticalMode` works:
`{"<typeId>": "offline" | "online" | "active"}` for all copies of a type, or
`{"<typeId>": {"active": n, "online": n, "offline": n}}` for copy counts.
Fits without it run at the default states (see `resolveModuleStates()` in
`index.html`). The runner flattens `moduleStatesRefusedCount` and
`moduleStatesActiveCount` / `OnlineCount` / `OfflineCount` for pinning.

A fit can also carry `droneStates` (`{"<typeId>": count in space}`), the
engine's 8th argument (v2026.10.13.23). The runner flattens
`droneStatesActiveCount`, `droneStatesBandwidthUsed` and
`droneStatesRefusedCount`.

## Capacitor best case and missing-field checks (v2026.10.13.27)

- The capacitor ring toggle is gone. `capacitorActiveDrainPerSec`, `capacitorNetRate`,
  `capacitorStable`, `capacitorStablePct` and `capacitorTimeToEmptySec` are now the
  **best case of the running modules**: active Capacitor Boosters inject, and active
  Ancillary Shield Boosters have charges, so they use no capacitor (pyfa's "use"
  column).
- New flattened fields:
  - `capacitorInjectionPerSec`
  - `capacitorNoBoost*` (no injection, ASBs on capacitor; the old primary)
  - `capacitorAsbDry*` (ASBs out of charges, the clickable ASB icon)
  - each of `capacitorNoBoost*` / `capacitorAsbDry*` covers `ActiveDrainPerSec`,
    `NetRate`, `Stable`, `StablePct` and `TimeToEmptySec`
- `capacitorCombinedConfidentNetRate` was removed; its pin moved to
  `capacitorNetRate`.
- **A pinned field that is missing from the result now FAILS** (`<field> (not in
  result)`). It used to be skipped silently, which would have turned the removed
  field's pins into no-ops. Keys ending in `_approx` are informational and never
  checked.

## pyfa capacitor simulation (v2026.10.14.1)

- **Simulation:** capacitor stability and time to empty come from `capSimPyfa()`,
  a port of pyfa's `eos/capSim.py`.
- **Comparison:** `PYFA_SRC=/path/to/Pyfa node regression_suite/compare_cap_sim.mjs index.html`
  runs every golden fit's three simulations (best case, ASB out of charges,
  without boosts) through pyfa's own simulator (`tools/cap_sim_oracle.py`).
  It must report 0 mismatches. Run it alongside `run_regression.mjs` whenever
  capacitor code changes.
- **Reactivation delay:** cap drain now averages over the active cycle plus
  `moduleReactivationDelay`, as pyfa does.


## Fixture completeness check (2026-10-14)

The checker now fails any fitted item, drone or fighter whose **type or
group record** is missing from its fixture:

    FAIL  fixture: Mid slots X-Large C5-L Compact Shield Booster (no group record 40)

Cargo and fleet hangar items are exempt, since a missing cargo record only
hides unused cargo.

The first catch was `ishtar_zkb137694046`. Its fixture lacked the Shield Booster
group, so the engine dropped the booster. The capacitor was pinned at stable
96.9% for months while the real page and the owner's pyfa both gave 40.5%. With
the group added, it matches pyfa exactly: stable 40.5%, net +7.1 GJ/s,
drain 77.2 GJ/s. It also gains a 119 HP/s shield repair. See
`LESSONS_LEARNED.md` #6 and
`tools/independent_checks/check_cap_sim.py` (Ishtar case).

## Fixture refresh from the SDE (2026-10-14)

Every golden fit's type and group records were refreshed from CCP's SDE as
pyfa ships it (client build 3579973, the same data as the owner's pyfa v2.69.2) with
`tools/refresh_golden_fixtures.py --write`. The merge kept 282 attributes that
only the live-ESI captures had, plus one effect. Totals:

- 1,925 attributes filled on 194 trimmed records
- 33 missing types added
- 2,470 group records added
- 19 effects added (all on cargo items)
- 1 value changed: the Hawk's pre-patch `shipBonusCF` 10 → 7.5

15 fits' outputs moved; only `legion_owner`'s capacitor pin failed (300 →
2,100). After the refresh, that killmail copy gives exactly the numbers of its
pyfa-verified twin `legion_owner_eft_pyfa_verified` on every moved field.
New pins with notes, all failing on the old trimmed data:

- Legion: 11 fields
- Rifter armor layering: raw armor 6,563
- Vedmak: neut 15 GJ/s
- Vargur: capacitor 5,813

The other moved outputs were not pinned. They are listed in
`dscan-tool-history/2026-10-14_golden-fit-data-refresh.html` and get
re-derived as each stat's hand-table phase reaches them.

Before adding a golden fit, run `refresh_golden_fixtures.py` in report mode. It
must print `0 of N fits change`.

## Time-to-kill "why" words (v2026.10.14.58)

After the fits, `run_regression.mjs` runs `ttkWhy` on hand-built defenses (`ttkTrace` on layers with made-up hit
points, repairers and incoming damage) and compares the title and every sentence with text worked out by hand: an
Ancillary Shield Booster's one clip then spent, breaking in a reload (also the third reload of two copies), clips
spent then regen, the capacitor running dry during or before a layer, "even with", a middle layer with no repairer,
holding on a repairer or on regen, no damage at all, all buffer, and a repairer with no name (an estimate without
`localReps`). Also `ttkText` at whole minutes ("1 min", not "1 min 0 s"). The times themselves are checked against
pyfa's inputs by `tools/independent_checks/check_matchup.py`.

## PYFA CORE lock (2026-10-14)

`run_regression.mjs` runs `tools/check_pyfa_core.mjs` before any fit. If a
`PYFA CORE` section of `index.html` changed since it was verified against
pyfa, the suite fails with the section name and its re-verify commands. See
`PYFA_CORE.md`.

## Firepower from pyfa's handlers (v2026.10.14.3)

Ten constructed fits, each expected value derived first by
`tools/independent_checks/check_firepower.py`. All ten failed on
v2026.10.14.2 by exactly the predicted error, and all pass now:

- `leviathan_constructed_xl_torpedo_kinetic` and `_em`
- `anhinga_constructed_cruise_no_rof_bonus`
- `akoman_constructed_large_pulse_role_bonus`
- `thunderchild_constructed_vorton_hull_bonus`
- `nemesis_constructed_em_torpedo_no_thermal_bonus`
- `gnosis_constructed_medium_pulse_role_bonus`
- `caracal_constructed_light_launcher_out_of_scope`
- `dominix_constructed_neophyte_heat_sink_drones`
- `thanatos_constructed_dda_fighters`

Re-pinned for Vorton Power Amplification:

- Stormbringer 263 → 302
- Skybreaker 51 → 58

`audit_role_bonus_drift.mjs` is obsolete: `SHIP_ROLE_BONUS` is now only the
special-edition fallback. Use `tools/gen_hull_damage_table.py`.

## Fighter abilities (v2026.10.14.4)

pyfa sums every fighter ability it switches on by default (LESSON #24). Expected
values from `tools/independent_checks/check_firepower.py`; the first is the owner's
pyfa screenshot (831 DPS, volley 7,125, tolerance 0.1%). Six new constructed
fits, five failing on v2026.10.14.3 and one guard:

- `thanatos_constructed_one_squadron_firbolg_pyfa` (pyfa-verified)
- `thanatos_constructed_fsu_firbolg` (Fighter Support Unit II x2)
- `thanatos_constructed_satyr_superiority` and `_satyr2_specialization` (Missiles only; were 0)
- `nyx_constructed_cyclops_heavy` (Missiles + Attack Missile)
- `nyx_constructed_ametat_bomber` (guard: bombs stay off, unchanged)

Re-pinned, Attack Missile only before: `thanatos_constructed_dda_fighters`
1,505 → 2,494; `thanatos_zkb138975919_fighter_bay` 274 → 453.5 (its 2 Fighter
Support Units aren't in the fixture; 499 with them);
`nyx_constructed_heavy_fighter_specialization_bonus` 1,544 → 3,087;
`thanatos_constructed_t2_light_fighter_specialization_bonus` 334 → 551. Their
labels' claim that pyfa has no fighter DPS was wrong; each note says so.

## Resistances from pyfa's handlers (v2026.10.14.5)

Expected values from `tools/independent_checks/check_resists.py` (pyfa's own
handlers via `tools/pyfa_fit_oracle.py`). All six failed on v2026.10.14.4:

- `moa_constructed_shield_compensation_dc` (Compensation skills 25%, not 20%)
- `paladin_constructed_bastion_dc_membranes` (Bastion + Damage Control share the 'preMul' stacking group)
- `megathron_constructed_rah_dc_membranes` (pyfa's Reactive Armor Hardener algorithm)
- `rifter_constructed_polarized_weapon` (0% resists)
- `punisher_kador_edition_constructed_resist` (special-edition hull bonus)
- `phoenix_constructed_flex_script` (hardener script)

`dominix_navyissue_buffer` is now pinned to the user's pyfa screenshot (armor
75/71/71/71, Armor 260k, EHP 318k); `nighthawk_zkb138992462_rolebonus_audit`
shield EHP re-derived. `dump_results.mjs` runs every fit and writes chosen result
fields to JSON (used by `tools/independent_checks/compare_resists.py`).

## Ship modes from pyfa's handlers (v2026.10.14.6)

Expected values from `tools/independent_checks/compare_modes.py` (pyfa's own
handlers via `tools/pyfa_fit_oracle.py`, with the mode item pyfa uses). All seven
failed on v2026.10.14.5:

- `anhinga_constructed_secondary_mode` (launcher rate of fire x0.5: 65 DPS)
- `anhinga_constructed_tertiary_mode_mjd` (x0.75 rate of fire, agility, MJD reactivation x0.1; MJD pinned active)
- `skua_constructed_sharpshooter_rockets` (rocket damage x1.333, velocity x3.5, targeting / gravimetric x2)
- `skua_constructed_defense_shield` (signature, shield recharge, resistances)
- `skua_constructed_propulsion_ab` (afterburner speed factor, agility)
- `hecate_constructed_defense_armor_repairer` (repair cycle x1/1.5)
- `confessor_constructed_defense_remote_armor_repairer` (remote repairer cap need x1/1.5)

Re-pinned: `anhinga_constructed_cruise_no_rof_bonus` 33 → 43 DPS (pyfa's default
Primary Mode); `hecate_constructed_propulsion_mode_bonus` boosted speed 837 → 592
and cap drain 0.2 → 0.7 (pyfa's Hecate Propulsion Mode boosts microwarpdrives only,
not this afterburner). `dump_results.mjs` takes `[mode] [fitIds]` to run one mode.

PYFA-VERIFIED after delivery (the owner's pyfa v2.69.2): `anhinga_constructed_cruise_no_rof_bonus`
(Primary: 43.4 DPS, 1086 km, 300 km, EHP 19.5k) and `skua_constructed_sharpshooter_rockets`
(41.7 DPS, 35.4 km, 138 km, EHP 4.38k) gained full pins. New `skua_pyfa_rockets_defense_mode` = the same
EFT in Defense Mode, pyfa's default for the Skua (31.3 DPS, sig 46.7, EHP 5.33k). Layer-EHP pins cover
pyfa's whole 3-significant-figure bin plus the rounding edge (pyfa 1.91k → tool 1905-1915).

## Missile range from pyfa (v2026.10.14.7)

Expected values from `tools/independent_checks/check_missile_range.py` (pyfa's own
`Module.missileMaxRangeData`). `run_regression.mjs` now also flattens `rangeTravelLowerM`,
`rangeTravelHigherM` and `rangeTravelHigherChancePct` (pyfa's range tooltip). New
`raven_constructed_fof_cruise_range_cap` (auto-targeting cruise missile capped at 200 km minus the
Raven's 250 m radius: 199,750 m; v.6 showed 222,075 m). Re-pinned exactly: hawk_user, golem bastion,
sacrilege, muninn, both Skua mode fits (a few metres to 66 m). Split pins added on the three Anhinga
fits, both Skua fits, Golem, Nighthawk and Leviathan XL torpedo (58,725 → 58,145 m: acceleration).

## Speed / agility / mass from pyfa (v2026.10.14.8, hand-tables P3)

Expected values from `tools/independent_checks/compare_speed.py` (pyfa's own handlers). New
constructed fits, both failing on v2026.10.14.7: `helios_constructed_cloaked_velocity` (cloak active:
cloaked-only velocity bonus, 413 → 516 m/s) and `rifter_constructed_cyno_active` (cyno active:
0 m/s). Cyno now defaults online (input choice, DEVIATIONS.md); `rifter_constructed_cyno_fitted`
pins 456 m/s. Re-pinned with causes in their notes: Loki (Wake Limiter AB bonus, 1217 → 1709), Charon
(freighter velocity bonus, 75 → 94), both Monitors (agility bonus, align 9.0 → 6.7), Tengu
(Interdiction Nullifier +0.1 agility, 7.0 → 8.4), Rifter plate (Advanced Armor Layering, 10.5 → 10.8),
Leshak, both Curses, Guardian (exact stacking / plate mass).


## D-Scan fit paste and PANIC state (v2026.10.14.9, bug list #1 and #2)

`dscan_parse_tests.mjs` gained fit-paste detection: 11 cases (EFT headers from the client and
pyfa, with and without a fit name, Windows line endings; single ship names, `[Empty High slot]`,
module-only lines and tabbed rows that must NOT count as a fit) plus both real pastes tested from
every one of their 257 starting rows, and a check of the "never in space" categories. 293 cases;
v2026.10.14.8 fails them. New constructed fits from `tools/independent_checks/check_panic.py`, both
failing on v2026.10.14.8: `rorqual_constructed_panic_default_online` (PANIC defaults online, Misc
flag) and `rorqual_constructed_panic_requested_active` (ACTIVE accepted, flag says RUNNING, every
other output field identical to the online twin). `run_regression.mjs` flattens `hasPanicFitted`
and `panicNoteText`.

**Update v2026.10.14.10:** the PANIC follows pyfa again (online at most; the owner: an Active state that
changes nothing looks broken). `rorqual_constructed_panic_requested_active` now pins the refusal
(refused 1, online 1), and both PANIC fits pin the flag's 6-minute duration (pyfa's buffDuration at
All V after the Invulnerability Core Operation skill; v.9 said 4). Both fail on v.9 and v.8.

## EWAR from pyfa (v2026.10.14.11, hand-tables P4)

Expected values from `tools/independent_checks/compare_ewar.py` (pyfa's own handlers on the whole
fit, loaded scripts included). `run_regression.mjs` now also flattens every EWAR entry as
`ewar:<module name>:<script or ->:<field>` (copies of one type with different scripts are separate
entries since v.11). New constructed fits, all failing on v2026.10.14.10:
`lachesis_constructed_damp_scripts_per_copy` (two dampener scripts), `arbitrator_constructed_td_scripts_gd_neut`
(two disruptor scripts, unscripted guidance disruptor, neutralizer), `rook_constructed_ecm_signal_amps_stacking`
(exact stacking of two Signal Distortion Amplifiers, tolerance 1e-6) and `bhaalgorn_constructed_neuts_nos_webs`
(hull neutralizer / nosferatu amount and web range bonuses). Re-pinned with causes in their notes: both
Curse fits (scripts; Recon neutralizer bonuses), the Monitor painter (-99%, not -99.9%), the Crucifier
disruptor (its range bonus is on the module's range, not the disruption strength), both Lokis (web
subsystem).

## Implants and boosters (v2026.10.14.12)

A fit's tally may carry `Implants` and `Boosters` groups (a pasted EFT fit). The engine applies them
through PYFA CORE `implant-calc`. A killmail fixture's flag-89 items are applied only when
`PILOT_ANALYZER_APPLY_IMPLANTS` is on (it is off). Expected values come from
`tools/independent_checks/compare_implants.py` (pyfa's handlers with the implants, unrounded,
1e-6), `compare_speed.py` and `compare_resists.py`; every pin was computed before the tool's numbers
were read, rounded the JavaScript way (half up; Python's `round` is half-even and gave 562 for
562.5 at first). The nine fits with applied implants fail on v2026.10.14.11; the last one guards the
Pilot Analyzer switch and passes on both:

- `rorqual_eft_full_quadfeed_implants_boosters_pyfa` and `rorqual_eft_pyfa_active_state_implants_boosters`:
  the owner's Rorqual with its Genolution CA-1..4 set and two boosters, pinned to his pyfa screenshot
  (EHP 1.78M, capacitor 102k, align 280 s, shield repair 17,030 HP/s raw, capacitor delta -5.98 GJ/s).
- `abaddon_constructed_armor_implants_boosters` (Amulet set, repair / hull / structure hardwirings,
  Exile and Halcyon Y boosters), `drake_constructed_shield_implants_boosters` (Crystal set, shield
  hardwirings, capacitor hardwiring, Blue Pill and Halcyon B), `rifter_constructed_nav_implants_boosters`
  (Snake set, acceleration control, evasive maneuvering, long range targeting, X-Instinct),
  `rifter_constructed_halo_set_signature`, `merlin_constructed_talon_set_sensor_strength` (the only
  implants that ADD to a ship attribute), `merlin_constructed_high_grade_talon_set` (Effect2298, gated on
  the implant having the attribute), `punisher_constructed_cap_use_implants` (repairer and smartbomb
  cycle, afterburner cap need).
- `rifter_constructed_killmail_implants_switch_off`: a killmail listing a Snake set at flag 89; the
  pins are the implant-free numbers, so turning `PILOT_ANALYZER_APPLY_IMPLANTS` on fails it on
  purpose.

**Phase 2 (v2026.10.14.13): weapons, drones.** Expected values from the extended `compare_implants.py`
(weapon / smartbomb / drone DPS, ranges, drone control range), all failing on v2026.10.14.12:
`rupture_constructed_projectile_implants_boosters` (turret damage, rate of fire, falloff hardwirings;
Pyrolancea, Frentix, Strokar boosters), `caracal_constructed_missile_implants_boosters` (light missile
damage, rapid launch, projection; Halcyon B-5, Pyrolancea), `vexor_constructed_drone_implants_boosters`
(drone tuner, Hardpoint booster, Halcyon Y-5 +20 km drone control range), `vedmak_constructed_mimesis_set_spool`
(Mimesis set on the maximum spool-up). Re-pinned: `punisher_constructed_cap_use_implants` (smartbomb DPS
9 -> 10 with Energy Pulse Weapons EP-706), `abaddon_constructed_armor_implants_boosters` (drone control
range 60 -> 76 km, Halcyon Y-4), and `rangeFalloffM` 0 -> 1 on six Precursor / Vorton fits (a missing
falloff attribute is its SDE default, 1 m, as in pyfa; LESSON #22).

**v2026.10.14.14: expired boosters.** `rupture_constructed_projectile_implants_boosters` is PYFA-VERIFIED from
the owner's screenshot (284 DPS, 1,048 volley, 1.8 + 14.4 km, EHP 8.72k, speed 262, align 5.71 s, sig 125,
targeting 62.5 km, scan res 362 mm, sensor 18, capacitor 1.59k GJ). pyfa dropped its Strokar Booster VI (an
event booster whose last injection date is before pyfa's data dump; `db_update.py` deletes those). The fixture
keeps the booster in its tally, so the pins also guard the engine's skip of `PYFA_REMOVED_IMPLANT_IDS`;
`compare_implants.py` and the oracle drop the same boosters (`pyfa_sde.pyfa_removed_types`).

## Fighter damage application (v2026.10.14.64, turret-application-plan.md D5)

pyfa's getFighterAbilityMult per damage ability. Expected values from pyfa's side (check_application.py's harness:
pyfa's handlers on the oracle fit with the tool's launched squadrons, FighterAbility.getDps, getApplicationPerKey run
unmodified), written before the tool's numbers were pinned. Each fighter ability's inputs are pinned as
`app:fighter:<name>:<ability prefix>:<field>` (dps, speed, optimal, falloff, explosion radius / velocity); an
`applied@...` point may name a target fit, `tgt=subcap` or `tgt=capital` (the fighter missile resistances). Drone
inputs are now emitted the same way (`app:drone:<name>:<field>`).

- `hel_constructed_fighter_application` (hull velocity, Fighter Support Units, Drone Navigation Computer, Omnidirectional
  Tracking Link with an Optimal Range Script, Omnidirectional Tracking Enhancers, capital drone rigs, Valdimar implants;
  Einherji II + Mantis II)
- `revenant_constructed_fighter_application` (hull explosion bonuses, a Tracking Speed Script; Locust II superiority +
  Cyclops II heavy)
- `nidhoggur_constructed_fighter_velocity` (hull velocity; Gram II + Firbolg II)
- `vexor_constructed_scripted_omni_link_drones`: a scripted Omnidirectional Tracking Link on drones (LESSON #59). v.63
  gave the drones the link's unscripted bonuses.

v2026.10.14.63 fails every applied@ pin of the three carriers (no fighters in the application) and the Vexor's.

## Fighter bay states (v2026.10.14.66, roadmap/fighter-gaps-plan.md delivery 1)

A golden fit may carry `fighterStates` (`{typeId: {n: squadrons in space, ab: {effectId: on}}}`, the Fighter bay's
request), passed to `estimateHpAndDps` as `options.fighterStates`. Expected values from pyfa's side, as above, with those
squadrons in space and those abilities active (pyfa_fit_oracle.py runs an active speed ability's handler as eos
`Fighter.calculateModifiedAttributes` does).

- `nidhoggur_constructed_fighter_bay_states`: 1 Einherji II squadron (the default launch puts 2 out) with Missiles off
  and MWD on (its boost stacks with 2 Drone Navigation Computers in 'default'), 1 Gram II with Evasive Maneuvers on,
  1 Dromi II and 1 Siren II.
- `hel_constructed_fighter_bay_abilities`: the Hel fit above with 3 Einherji II on MWD (with Fighter Support Units'
  postMul) and 2 Mantis II with Attack off.

v2026.10.14.65 ignores `fighterStates` and fails 21 pins; a break that ignores the requested squadron counts fails 6, one
that drops the speed ability's handler 4, one that leaves its boost unpenalized 4, one that ignores the toggles 14.

## Maximum spool-up hull bonuses (v2026.10.14.67)

`nergal_constructed_max_spool_hull_bonus`, `ikitursa_constructed_max_spool_hull_bonus` and `babaroga_constructed_max_spool_hull_bonus`:
each hull with an Entropic Radiation Sink II and its size of Entropic Disintegrator II loaded with Occult. pyfa's hull
effects 7216 / 7211 / 12288 double the disintegrator's damageMultiplierBonusMax (2.125 -> 4.25). Expected DPS from
pyfa's side (pyfa_fit_oracle, getDps at max spool): 641.5 / 1,300.4 / 1,793.0. v2026.10.14.66 gave 382 / 774 / 1,067
and fails all 6 pins (LESSON #62).
