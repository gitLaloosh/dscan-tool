# Plan: a card layout people can arrange themselves

Status: **STEP 1 DONE** (v2026.10.14.37, 2026-10-23; `dscan-tool-history/2026-10-23_damage-card-on-top-and-layout-table.html`).
**STEP 2 DONE** (v2026.10.14.38, 2026-10-23; `dscan-tool-history/2026-10-23_cards-sized-by-their-own-width.html`).
Step 3 is backlog (the owner: steps separately, step 2 first; My Ship phase 2 next). the owner 2026-10-23 asked whether the cards should be "so modular that the user can move the
cards around and define how many columns they span", then "ok, let's go with your suggestion" for this staged plan.

## Why staged

- What matters most differs by player (a solo PvPer wants "Their damage on you" and EWAR first; someone checking a
  doctrine wants Firepower and Resistance), and the cards are already self-contained units in one CSS grid, so a
  saved arrangement is mostly data.
- But: most cards are tuned to their column with screen-width breakpoints, not to their own width; the sticky Fit
  column covers anything placed below it in the same grid (LESSON #38); on a phone everything is one column;
  every arrangement multiplies the page checks; a layout saved in the browser has to survive new cards.

## Step 1 — the layout table (done, v2026.10.14.37)

- `FIT_LAYOUT` in `index.html` (block `// ==== FIT LAYOUT TABLE`):
  - `stacks`: the cards stacked in each column, top to bottom (beat: TD mode, Weaknesses, EWAR; fit: Fit;
    stats: Firepower, Resistance, Navigation & targeting, Capacitor);
  - `bands`: cards in their own grid area that may span columns (`dmg`, "Their damage on you");
  - `grid`: per minimum width (0 / 900 / 1280 px) the column sizes, row sizes and rows of areas.
- `fitSummaryParts()` returns each card separately (`cards`), `fitLayoutHtml()` stacks them from the table, and
  `fitLayoutGridCss()` writes the grid stylesheet (`<style id="fitLayoutGrid">`) from the table at load. It
  throws if a row has the wrong number of areas or if anything sits below the last row with `fit` from 900 px up.
- Default (the owner's option B): phone `dmg / beat / fit / stats`; 900 px `dmg dmg / fit beat / fit stats`;
  1280 px `beat dmg dmg / beat fit stats`.

## Step 2 — every card sized by its own width (done, v2026.10.14.38)

- Every column and band of `.fit-layout` is a size container (`.fit-layout > div{container-type:inline-size}`).
- A width lab (`tools/page_checks/card_width_check.py`) copies every card into containers of 300, 340, 460,
  520, 700, 1000 and 1358 px. Found on v.37: Firepower's four tiles went 3 + 1 at 520 px; Navigation's speed
  "1,691 m/s" broke across two lines at 340 px; the Tactical Destroyer mode row's info link reached 6 px outside
  the card at 300 px; Capacitor's net-rate tile became a tall narrow column at 340-520 px. Resistance, the
  Weaknesses tiles, EWAR, the Fit card and "Their damage on you" were already fine at every width.
- Fixes, all presentation: tile rows (`.estimate-box`) are a grid with 1 column, 2 from 300 px, a row of 3 from
  520 px and of 4 from 640 px, an odd last tile spanning the row; the Capacitor row has its own rule (one per row
  under 440 px, the state tile across the row until 700 px, then 2 : 1 : 1); tile values wrap the badge, not the
  number; the mode row wraps; the Weaknesses rule for narrow columns keys on the card's width (< 400 px), not on
  `.fl-beat` at 1280 px.
- The Fit card's default Ring / List view is still chosen by screen width (< 600 px: list). With the Fit card
  fixed in its own column (step 3 decision below) it is never narrower than ~430 px from 600 px up, so that stays
  right; no change needed.

## Step 3 — "Edit layout" (backlog, only if still wanted after step 2)

**Decision (the owner 2026-10-23):** "only allow [the Fit card] to be placed in the center column ... given the
complexity of the layout with the module ring, probably the easiest way to avoid quirky behavior." So:
- The Fit card is not movable and never spans: it keeps its own column at every width (the center column at
  1280 px and up, the left column at 900-1279 px, where there are only two). That column holds only the Fit card,
  so its sticky behaviour and ring sizing stay as they are.
- Bands (e.g. "Their damage on you") may still sit above it and span across it; nothing may sit below it
  (LESSON #38, already enforced).
- The other cards move between the remaining columns and bands. On a phone (one column, nothing sticky) the
  Fit card could still move in the order; to decide when step 3 is designed.

- An "Edit layout" mode: on each card, move up / down, "move to column" and "span 1 / 2 / 3"; a Reset button.
  Buttons, not drag-and-drop (more reliable on touch; drag could come later).
- Saved in the browser (`localStorage`, wrapped in try/catch) as an override of `FIT_LAYOUT`; cards the saved
  layout doesn't name (added in a later version) fall back to their default place.
- The LESSON #38 rule is enforced by `fitLayoutGridCss()`: a span below the sticky Fit column is refused. The
  editor offers no move / span controls on the Fit card, and refuses a saved layout that moves it.
- Phone: order only.
- Page checks over a set of arrangements, Reset, and an old saved layout meeting a new card.
