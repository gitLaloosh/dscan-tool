# Plan: "My ship"

Status: **PHASE 1 DONE** (v2026.10.14.33, 2026-10-23; `dscan-tool-history/2026-10-23_my-ship-phase1.html`).
Phase 2 (comparing the two fits) waits for the turret-application decisions. Mockups: the "My ship — chip and panel mockup" design canvas
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

## Phase 2 (not started)

Needs turret-application D1-D6. Matchup strip (their DPS on you, yours on them, how long each lasts, who's
faster), Weaknesses from both points of view, "vs my ship" tags, changed numbers in amber (M6).
