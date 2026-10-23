# Plan: "My ship"

Status: **DESIGN** (2026-10-23). Mockups: the "My ship — chip and panel mockup" design canvas
(claude.ai artifact WKMf8Uf3GaZWbjiFCGyzCh), pages "Chip and panel" and "Threat ⇄ my ship".
Related: `turret-application-plan.md` (its D2 = where "your" sig, speed and radius come from).

## What it is

You save your own fit once (EFT paste), and the tool can then assess every threat against it, on every tab.

## Decisions (Erik)

| # | Decision | Date |
|---|---|---|
| M1 | Set by pasting an EFT fit. It persists until a new one replaces it or the user deletes it. | 2026-10-22 |
| M2 | Easy to find on every tab, with a "Use in assessments" toggle next to it. The mockup puts both in a header chip beside the tabs, not on a fourth tab. | 2026-10-22 |
| M3 | The user can see their ship as the Fit Analyzer shows it. | 2026-10-23 |
| M4 | Changing my ship's module states updates the whole analysis, and the changes are kept as part of "my ship". A Reset returns to the pasted fit's default states. | 2026-10-23 |
| M5 | With a ship saved and the toggle on, a switch flips between the threat and my ship in the Pilot and Fit Analyzers. Every number updates. | 2026-10-23 |
| M6 | A changed number shows the change visually (amber), with no "updated" label. | 2026-10-23 |
| M7 | Module-state changes made to a threat are forgotten when a different threat is loaded. Only "my ship" keeps its states. | 2026-10-23 |

## Mockup details (not yet decided)

- Chip states: an outlined "+ My Ship" with the toggle disabled (Erik renamed it from "Set my ship", 2026-10-23); once set, "MY SHIP · Vexor · Brawl". Clicking
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
