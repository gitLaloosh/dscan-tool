# Charges in the Fit card (plan, 2026-10-26)

the owner: "let's work on the ammo in the fit card but i also think we should have a dropdown that gives you a list of every
usable charge for those weapons/launchers. they have it in eve workbench and it's really useful. even if we had to flag
items missing from a fit as not being available to the fit, the user might want to see what affect each ammo type has
on the numbers." Also: "i also prefer how much easier it is to see the icons in their fits." Screenshots: EVE Workbench's
fitting ring, its "Possible charges" panel, the ring with charges loaded, and its hover (launcher, charge, state).

Mockup: `charges_mockup.html` (the real page: bigger tiles, two ways to show a charge, the Charges list on desktop and
phone, the what-if state, list view). Decisions:

- **Ring charge: "A: charge icon"**: a weapon's tile shows its charge's icon (as Workbench); the hover names the
  weapon, the charge and the state.
- **Ring style: "Workbench-style track"**: tiles edge to edge along one continuous dark ring, empty slots drawn as
  outlines, the ship render filling the middle, icons as big as the card allows.
- **Loading a charge: drag and drop, as Workbench**: "dropping on a single module loads it there. dropping in middle
  of ring loads to all possible modules."

## Delivery 1: the ring as a Workbench-style track (done, v2026.10.14.75)

- Each rack (high top, mid right, low bottom, rigs + subsystems left) gets one position per slot the hull has, as pyfa
  counts them (`Fit.getNumSlots`: the ship's hiSlots / medSlots / lowSlots / rigSlots / maxSubSystems, with the
  subsystems' slotModifier handler, the only pyfa handler on those attributes). Empty slots are dim outlines.
- Tiles follow the circle (rotated with their position), sized from the spacing along the arc, so they are bigger
  than today's upright squares.
- A weapon (turret or launcher) with a charge shows the charge's icon; the hover: "Heavy Missile Launcher II · Scourge
  Heavy Missile · Active. Click to set online." Clicking a tile still sets its state, as today.
- The ship render fills the middle.
- Checks: slot counts against pyfa (oracle ship attributes, T3 subsystems included); layout_check (tiles inside the
  ring, no overlap, sizes) and a page check for the empty slots, charge icons and hovers.

## Delivery 2: the Charges list, drag and drop, "not on board" (done, v2026.10.14.76)

- A Charges button by Ring / List opens the list for each weapon type: charges aboard first (loaded, in cargo), then
  every other charge the weapon can load (pyfa isValidCharge, already in the page), marked "not on board", sorted by DPS.
  Each row: that charge's DPS for the copies it would load into and its range (the engine run once per charge, filled
  in as they finish); damage-type filter chips.
- Drag a charge onto a weapon tile: loads it there only. Drop it in the middle of the ring: loads it into every weapon
  that can take it. Pointer-based dragging, so it works with a finger too. A click or tap on a charge (and Enter for a
  keyboard) loads it into every copy, the same as a drop in the middle.
- The engine takes the charge per weapon copy (as a killmail's per-flag charges). Every card recalculates.
- A charge the fit doesn't have is flagged "not on board" (the owner: "rather than calling it a 'what if', does it still make
  sense if we just stick w/ flagging as 'not on board'?" -- yes): an amber "not on board" tag in the card head, dashed
  amber tiles, and the Loaded line "Caldari Navy Scourge Heavy Missile ×6 · not on board" with a link back to the fit's
  own charges (the reset button also restores them). A charge picked from the cargo isn't flagged: it's on board.
- List view: each weapon row shows its charge as a small dropdown that opens the same list.
- Checks: per-charge DPS and range against pyfa (oracle fit with that charge), drag / drop / tap, the "not on board" flag,
  phone sheet.

Delivery 2 as built: the list shows on board first (loaded, cargo, fleet hangar), then "not on board" by DPS, with each
charge's DPS and range worked out on opening (about a second for 30 charges). The engine now takes which copies are
active from the Fit card (a weapon's copies can hold different charges). Found on the way and fixed: Civilian missiles
got the missile damage skills and Ballistic Control Systems (pyfa filters them on the charge requiring Missile Launcher
Operation), and two launcher types sharing a charge shared one range entry. The EFT export keeps the fit's own charges;
the Weaknesses picks rank only the charges on board.

## Delivery 3: unloading, and the list inside the Fit card (done, v2026.10.14.77)

the owner, after v.76: "this brings me to the next problem. unloading charges." Screenshots of Workbench: a weapon's hover
icons (unload module, unload ammo, online), the menu at the start of each rack (Online / Activate / Overheat / Offline /
Unload Ammo / Unload Module), the right-click menu (information only). Mockup: `unload_mockup.html` (the real v.76 page;
unloading one of six launchers takes the Drake's weapon DPS 328 -> 273). Discussed one section at a time:

1. **The list stays inside the Fit card at every width** (the owner: "the charges list needs to stay inside of the fit card
   because if i reduce my window size as far as possible on the site, there is no way to put the list on the left or the
   right"). Below 600 px it opens inside the card as on a wide window (no sheet over the page); opening it scrolls the
   card's top into view; its height fits the window and it scrolls inside itself. Drag and drop as on desktop.
   Added: **weapon-type filter chips** ("similar to the existing filter chips, allow the user to filter by module type"),
   one per weapon type on the fit, shown only when the fit has more than one, beside the damage-type chips.
2. **A "No charge" row** first in each weapon's section (0 DPS, no range): click / Enter unloads every copy, a drag onto
   one weapon unloads that one, a drop in the middle of the ring unloads every weapon.
   - An unloaded copy goes **Online** (the owner: "just put it in the online state"; EVE can't activate a weapon with no
     ammo; pyfa would let it be Active, using capacitor (capUse counts capacitorNeed whenever Active) for no damage).
     Its tile shows the weapon's own icon (a loaded one shows its charge), nothing else ("not a fan of the strike
     through"). A click on it switches Online / Offline only.
   - **Subtext rule** ("less subtext taking up real estate"): the list's how-to paragraph moves into an (i) in its
     header; no line under the No charge row; the Loaded line names no empty copies. Firepower, Damage Application and the
     Matchup name an empty weapon through their existing "weapons not active" line: a short line (at most 40 characters,
     e.g. "1 launcher empty") with the full sentence in its hover / info panel. The charge rows' status tags stay.
   - A weapon a killmail shows empty keeps today's assumed charge; only an unload the user picks overrides it.
   - **No memory of earlier charges** (the owner: "having to remember prior charges for every module could result in a point
     of failure"): unload -> Online; loading a charge into an empty copy -> Active (a freshly fitted weapon in pyfa).
   - The link back is **"Use original charges"** (the owner's wording, was "use the fit's own"); reset restores charges and
     states.
3. **Hover bar on a weapon** (the owner: "worth trying"): after a short pause, under the tile: **Unload charge · Charges…**
   on a loaded copy, **Charges…** alone on an empty one (opens the list at that weapon, its weapon-type chip on). No
   Reload ("make them choose a new charge using the list"), no power button (a tile click sets the state), no unload
   module (ETA doesn't edit fits). Keyboard focus shows it; on a phone a held finger opens the same choices as a menu.
   Weapons that take charges only.
4. **A menu per rack** (High, Mid, Low; rigs and subsystems are always online): All active / All online / All offline,
   Unload all charges (the rack's weapons; only when it has some), Charges…. No overheat (backlog). **"All active" is
   literal** (the owner: "let's stick with the literal option for now"): every module in the rack is requested Active and the
   state engine applies what pyfa allows (group limits, activation blocks, EWAR lockout), saying why for the rest. Empty
   weapons stay Online. Check at 320 px that the rack buttons fit without covering a tile (else a row under the ring).

Delivery 3 as built (the owner: "proceed"): as above. Found on the way and fixed: the capacitor need bonus of a weapon's charge
(Void L +25%) was averaged over every copy of the weapon type, Online and empty ones included (a Megathron with two of
seven blasters unloaded drained 31.8 GJ/s, pyfa 32.8); the pyfa stand-in for the goldens skipped empty slots when pairing
charges with copies; a weapon type with no Active copy could still get an assumed charge; the open list kept its DPS
after a state change. LESSON #69. Checks: unload_check.py (pyfa per step), two pyfa goldens, charges_check.py updated.
