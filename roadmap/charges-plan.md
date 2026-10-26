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

## Delivery 1: the ring as a Workbench-style track

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

## Delivery 2: the Charges list, drag and drop, "not on board"

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
