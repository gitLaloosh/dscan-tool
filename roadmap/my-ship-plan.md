# Plan: "My ship"

Status: **PHASES 1 and 2 DONE** (phase 1 v2026.10.14.33, 2a v.41, 2b v.42, all 2026-10-23). Open: the strip's placement (backlog below).
Mockups: the "My ship — chip and panel mockup" design canvas
(claude.ai artifact WKMf8Uf3GaZWbjiFCGyzCh), pages "Chip and panel" and "Threat ⇄ my ship".
Related: `turret-application-plan.md` (its D2 = where "your" sig, speed and radius come from).

## What it is

You save your own fit once (EFT paste), and the tool can then assess every threat against it, on every tab.

## Decisions (the owner)

| # | Decision | Date |
|---|---|---|
| M1 | Set by pasting an EFT fit. It persists until a new one replaces it or the user deletes it. | 2026-10-22 |
| M2 | Easy to find on every tab, with a "Use in assessments" toggle next to it. The mockup puts both in a header chip beside the tabs, not on a fourth tab. | 2026-10-22 |
| M3 | The user can see their ship as the Fit Analyzer shows it. | 2026-10-23 |
| M4 | Changing my ship's module states updates the whole analysis, and the changes are kept as part of "my ship". A Reset returns to the pasted fit's default states. | 2026-10-23 |
| M5 | With a ship saved and the toggle on, a switch flips between the threat and my ship in the Pilot and Fit Analyzers. Every number updates. | 2026-10-23 |
| M6 | A changed number shows the change visually (amber), with no "updated" label. | 2026-10-23 |
| M7 | Module-state changes made to a threat are forgotten when a different threat is loaded. Only "my ship" keeps its states. | 2026-10-23 |

## Mockup details

the owner: "ok, work on 1" (2026-10-23), i.e. build phase 1 as drawn. Built in phase 1: the chip and switch, the
panel (paste, summary, Replace, Copy EFT, Delete), "Set as my ship", "Viewing my ship", the threat ⇄ my ship
switch with module states kept, storage, the phone layout. Not yet: the matchup strip, Weaknesses flipping its
point of view, the "vs my ship" tag and the amber changed numbers (M6), which all need numbers that compare the
two fits.


- Chip states: an outlined "+ My Ship" with the toggle disabled (the owner renamed it from "Set my ship", 2026-10-23); once set, "MY SHIP · Vexor · Brawl". Clicking
  the chip opens a panel with a paste box (empty), or a six-number summary with Open in Fit Analyzer, Replace,
  Copy EFT and Delete (set).
- A "Set as my ship" button on any Fit Analyzer fit.
- A matchup strip that stays in place in both views: their DPS on you, your DPS on them, how long you last,
  how long they last, who's faster.
- Weaknesses flips its point of view with the switch: your guns vs them, then their guns vs you.
- Colours: threat amber, my ship cyan. A "vs my ship" tag on any card that uses it.
- Storage: the EFT text, the module states, the toggle and the date it was set, kept in browser storage.
  Recomputed on load, so tool fixes and game-data patches apply.
- Phone: a larger chip plus the toggle; the panel opens as a sheet from the bottom; the switch stays at the
  top when scrolling; the matchup numbers sit in a 2×2 grid.

## Phase 1 as built (v2026.10.14.33)

- Storage: `localStorage` key `dscanMyShip`, `{v: 1, eft, shipName, fitName, shipTypeId, shipGroup, savedAt,
  use, moduleStates, moduleCopyOrder, droneStates, activeMode, asbDry}`. No numbers. The fit is recomputed from
  `eft` the first time a page load needs it (no ESI call on page load).
- "Use in assessments" is on when a ship is first saved; Replace keeps its setting.
- "Set as my ship" keeps that fit's current module states (hover text says so).
- Errors: MYSHIP-01 (storage refused: works until the page closes), MYSHIP-02 (saved fit no longer loads; the
  message carries the underlying code, the saved text is kept).
- Check: `tools/page_checks/my_ship_check.py`.

## Phase 2 (decided 2026-10-23; 2a DONE v2026.10.14.41, 2b DONE v2026.10.14.42)

Matchup strip (their DPS on you, yours on them, how long each lasts, who's faster), Weaknesses from both points
of view, "vs my ship" tags, changed numbers in amber (M6). Decisions (the owner, 2026-10-23):

| # | Decision |
|---|---|
| P1 | **Split:** 2a = the matchup strip, "vs my ship" tags and amber changed numbers (M6); 2b later = Weaknesses flipping to "your guns / their guns" (it needs picking ammo and drones from your own bays). |
| P2 | **"You last" / "They last":** by damage type, with reps -- their applied DPS split by damage type against your resists layer by layer (shield, then armor, then hull), minus your reps and passive regen while your capacitor holds; "holds" when you out-rep them. Not a pyfa number (pyfa has no time to kill): built from pyfa's pieces, recorded in DEVIATIONS.md when built. |
| P3 | **Drones:** port pyfa's drone application first (getDroneMult) -- DONE v2026.10.14.40; fighters later. |
| P4 | **Engagement:** the strip follows the "Their damage on you" card's settings (range, movement); your DPS on them uses the mirror (your speed as the attacker's, theirs as the target's). |

### 2a as built (v2026.10.14.41, `dscan-tool-history/2026-10-23_matchup-strip.html`)

- `mysMatchup(threatFit, myFit, cardState)` (block `// ==== MATCHUP STRIP`): five cells, "Their DPS on you",
  "Your DPS on them", "You last", "They last", "Faster"; rendered in the threat / my ship switch area
  (`.mys-strip`), the same in both views, following the visible Pilot losses tab; on a phone four cells, two rows,
  sticky with the switch.
- Typed applied DPS: `dmgTypedPoint` (pyfaProjectedPoint, then pyfaApplicationMult / pyfaGetDroneMult per item x
  its `typeDps`, an engine input added to application weapons and drones). Time to kill: `ttkDefense` / `ttkSeconds`
  (DEVIATIONS.md section 3).
- M6: a baseline of my ship with the pasted fit's own states (`mysEnsureBaseline`, one engine run per saved fit);
  strip cells and, in the My ship view, every card number (`mysMarkChanged`) that differ are amber with the pasted
  value on hover.
- The card's "their speed" now tops at their speed in their current states (their prop only if running).
- Checks: `tools/independent_checks/check_matchup.py` (chain), `tools/page_checks/matchup_strip_check.py`.

### 2b decisions (the owner, 2026-10-23: "proceed with 2b")

| # | Decision |
|---|---|
| B1 | **Ammo pool:** what the ship carries -- loaded charges plus compatible charges in cargo (and the drone types in its bay). Killmails list cargo too, so threats work the same way. |
| B2 | **Ranking point:** the "Their damage on you" card's settings, the strip's fight (P4), mirrored for your side. |
| B3 | **Old tiles:** replaced by the picks while a ship is saved and in use; with no ship saved (or "Viewing my ship") the card is as before. |
| B4 | **Design:** built from the existing mockup (the "your guns" / "their guns" tags and tiles). |

Found while building (recorded, LESSON #40): pyfa's damage graph ignores resists by default, so the picks are ORDERED
by the strip's time to kill against the target's resists with the rest of the fit as it is (then their buffer alone,
then the loaded charge), while the number shown stays pyfa's applied DPS.

### 2b as built (v2026.10.14.42, `dscan-tool-history/2026-10-23_weaknesses-your-guns-their-guns.html`)

- Block `// ==== WEAKNESS PICKS`: `wpCandidates(f)` (one engine run per round, cached per estimate), `wpRank`,
  `wpCardHtml`, `wpFill` (called from `mysRenderStrip`, so every strip refresh re-ranks). `mysFight` is the strip's
  fight, shared by the strip and the picks.
- The switch puts `.mys-picks-on` on the threat / My ship view; CSS swaps `.weak-generic` for `.weak-picks` and shows the
  tag. A collapsed Weaknesses card shows the picks in its summary row (`.wp-sum`).
- Error WP-01 (a candidate run failed). Checks: `tools/independent_checks/check_weakness_picks.py` (chain),
  `tools/page_checks/weakness_picks_check.py`.

## The matchup inside the loss (DONE v2026.10.14.43, `dscan-tool-history/2026-10-23_matchup-scoreboard-inside-the-loss.html`)

the owner (2026-10-23): the strip "seems out of place"; merge it into the threat / my ship toggle and put it inside the
container of the fit or loss being assessed. Then, on the v.42 page: "the UI is just too busy with all of the hulls
from their losses. the threat/my ship toggle is outside of the actual assessment window so it feels disjointed."
Options A (big tabs), B (scoreboard bar), C (inside the damage card) drawn on the My Ship canvas, page "Matchup
placement"; the owner: "ok that looks better. do it" (B, the recommended one).

- **Header line (Pilot Analyzer):** pilot name, a hull dropdown (their most-lost hulls with counts; `<details>`), the
  last kill on one line that opens to the full details (pivot button, attackers). The hull is named plainly when it
  was typed or picked from the last kill.
- **Assessment box:** the loss tabs sit on a box that holds everything about that loss. The Fit Analyzer result is the
  same box without tabs.
- **Scoreboard (the switch):** inside each loss (and the Fit Analyzer box), above the cards. Threat half: their DPS on
  you, how long they last; my-ship half: how long you last, your DPS on them; middle: the edge (who outlasts the
  other; "neither breaks" when both hold) and who is faster. Clicking a half shows that ship below. The side shown is
  shared by every loss tab. Phone: halves side by side, edge and speed under them, sticky.
- Also fixed: probe / bomb / interdiction sphere launchers no longer get a Weaknesses tile (v.42 bug, the owner's screenshot).
