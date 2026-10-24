# Plan: subtext, site-wide (one rule for every card)

Status: **BUILT 2026-10-24 (S1–S3, v2026.10.14.48–.50); DECIDED 2026-10-24** (the owner: "works as written. info icon opens a panel over the page. the 40 character limit is fine."). Mockup: layout canvas page "Subtext rule". Build phases in section 5.

the owner (2026-10-24): "the subtext in the tool is a little overwhelming and distracts from important values ... come up
with a solution that will address it across the entire tool, not just one card here and there. we need to address it
as a site wide design choice." And: "when making changes to the damage application slider, numbers change on multiple
cards which causes the content to shuffle and move elements on the page in some cases (long subtext that contains
dynamic data). this redesign should also address that."

## 1. What's there today (measured on the real page, v2026.10.14.47)

Fit Analyzer, Hecate threat vs a saved Vexor, every card open, 1440 px. "Subtext" = visible text in the dim/faint
colours that isn't a heading, value or uppercase label.

- Threat Perspective: 68 pieces, **2,819 characters**. 12 pieces over 40 characters hold **2,128** of them (75%).
- My Ship Perspective: 55 pieces, 2,127 characters; 11 over 40 characters hold 1,638.

The long ones (threat side):

| Card | Chars | Lines | Text starts |
|---|---|---|---|
| Resistance | 456 | 6 | "Break Point = DPS sustained to outpace repair/regen ..." |
| Damage Application | 327 | 4 | "As pyfa's damage graph: their webs, target painters ..." |
| Capacitor | 266 | 9 | "8.3 GJ/s peak recharge − 8.6 GJ/s active drain — the average behind ..." |
| Weaknesses (picks) | 219 | 4 | "Applied DPS at 4.4 km, you orbiting, as set on ..." |
| Fit | 209 | 3 | "Click a module to switch it off, online or active ..." |
| Matchup note | 155 | 1 | "At 4.4 km, you orbiting, as set on "Damage Application". Time to kill ..." |
| Weaknesses (cap) | 124 | 3 | "even at best case assuming its fitted Capacitor Booster ..." |
| Firepower (volley) | 97 | 4 | "one-shot damage from every confirmed weapon ..." |
| Navigation (sig) | 83 | 3 | "402 m with MWD active (assumed) — bloated by ..." |
| Capacitor (state) | 76 | 2 | "Best case of the running modules: Medium Ancillary ..." |
| Navigation (drones) | 65 | 2 | "20 km base + 40 km skills (Drone Avionics/Adv. ..." |

Most of it explains *how* a number is worked out. It's the same text every time, and a player reads it once.

The short context lines also use `--text-faint` (#4d5960) in several places (`.estimate-sub`). That is below 4.5:1
contrast on the card background, so they are hard to read *and* still take space.

## 2. What moves when the Damage Application range slider is dragged (measured)

Dragging 0 → max at 1440, 1100 and 375 px:

- **The whole page below the Damage Application card jumps 16 px** (42 px on a phone). The "Reset to my ship" button
  appears as soon as a setting leaves its default, and its row is taller than the title row without it.
- **The Weaknesses card grows 26 px** (24 on a phone) past ~12 km. A pick goes from "Out of reach" to a DPS line plus
  "they last ..." text that wraps to a second line, so the EWAR card under it moves too.
- The Matchup note and the picks note rewrite their sentence with the new distance. At narrow widths that changes the
  line count.

## 3. The rule (proposed)

1. **Under a value: at most one line of context, ≤ 40 characters, never wraps.** The line is always there (an empty
   slot keeps its height). If it's ever too long it's cut with "…", and the full text is on hover/tap. Only context
   that changes how you read *this* number stays (e.g. "225 m/s without MWD", "Magnetometric", "they last 25 s").
2. **How it's worked out goes behind one ⓘ per card**, in the card's title row. It opens a panel over the page, the
   same floating panel as Last Kill (a bottom sheet on a phone). Assumptions, pyfa notes, what a dash means and how
   to use the controls all move there. Per-value detail stays in that value's hover, as today.
3. **Warnings are warning rows, not grey paragraphs**: the warning colour/badge, one short bold line, and at most one
   context line ("Capacitor drains" · "even with its booster charged").
4. **Nothing moves unless you open or close something.**
   - Dynamic text lives in fixed-height, single-line slots.
   - Controls that come and go keep their space: Reset becomes an icon button that is always there, disabled at
     the defaults.
   - Numbers use tabular figures.
   - A card's height changes only when you open or close something.
   - **Numbers that change get a set width** (the owner 2026-10-24: "make sure you're considering if you should have a
     set length for the numbers so things are not moving around as values change"). Each live number sits in a box
     as wide as the widest value it can take, right-aligned, so the words after it never slide:
     - headline DPS ("0" → "1,195"): width of the fit's raw DPS, which no applied value can exceed;
     - Matchup cells: DPS as above; times as the widest form ("10 min 59 s"; "holds" fits inside it);
     - slider readouts ("4.4 km" / "125 km", "1,691 m/s · 100%"): the slider's maximum, formatted;
     - Weaknesses picks and stat tiles: same rule, widest value the slot can show.
   - **Charts keep their frame.**
     - The plot's left edge is set from the widest label the y axis can show (its top value), not from the labels
       shown right now, so the coloured DPS label never pushes the plot sideways.
     - The x axis labels (tackle distances, your range) sit in their own row under the plot. They move along the
       axis as values change, but never resize the chart.
     - While a slider is being dragged the y scale holds still. It rescales once, when you let go, so the curve
       doesn't jump under your cursor.
5. **The Matchup and picks notes go away.** The Option C strip under the Matchup (fight setup plan) already shows the
   range and movement, so neither card needs to repeat "At 4.4 km, you orbiting, as set on ...".
6. **Context lines use `--text-dim`, not `--text-faint`** (readable contrast).

Mockup (layout canvas, page "Subtext rule"): each board puts today's real card (screenshot) next to the same card
under the rule.
- Board 1: Damage Application, with the ⓘ panel shown beside it.
- Board 2: the Weaknesses column.
- Board 3: Resistance and Capacitor.
- Board 4: Navigation & Targeting and Firepower.

Same numbers, much less grey text. Heights at 1440 px, today → proposed (the mockup's cards measured):

| Card | Today | Proposed |
|---|---|---|
| Damage Application | 576 | 477 |
| Weaknesses | ~505 | 328 |
| Resistance | 472 | 345 |
| Capacitor | 370 | 236 |
| Navigation | 468 | 392 |
| Firepower | 378 | 303 |

## 4. Keeping it that way (checks)

- `CARD_INFO` registry (like `CARD_NAMES`): the ⓘ text for each card by key, written once. A card's long
  explanations can only come from there.
- New lint step: no visible context string over 40 characters outside `CARD_INFO` and hover titles. It also fails
  when `--text-faint` is used for text.
- New page check "nothing moves":
  - drag every Damage Application slider, press every movement button, toggle "Use in assessments" and switch a
    module state;
  - record every card's top and height at 1440, 1100 and 375 px;
  - fail if anything moves more than 1 px without being opened or closed.

## 5. Build phases (each its own version, regression + chain + every page check, history doc)

Subtext rule first, then the fight setup on top of it (turret-application-plan.md "Fight setup"):

| Phase | What |
|---|---|
| S1 **DONE v2026.10.14.48** | Shared pieces: single-line context slot (`ctxHtml`, ≤ 40 chars, full text on hover), ⓘ button + info panel (reuse the Last Kill panel and its Escape / outside-press closer, bottom sheet on a phone), `CARD_INFO` registry, set-width number boxes, Reset as a reserved icon. Checks: `check_subtext.py` lint (chain step) and the "nothing moves" page check, report-only at first. Also the "Adjust with no sliders" fix (hidden loss tab). |
| S2 **DONE v2026.10.14.49** | Damage Application headline (the number, "DPS applied at 4.4 km", one context line "290 if you sit still · 755 raw"; the movement is in the legend), Weaknesses (one context line per value, warning rows, picks as three single lines per tile, one per row; ranking note → ⓘ), EWAR / Misc (one-line chips, short Misc lines, ⓘ), Mode (its "How this is handled" panel → ⓘ, name "Mode" in `CARD_NAMES`), Fit (legend and implant note → ⓘ / one line; drone rows one line). `CARD_INFO` keys may be `<card key>#<variant>` and name cards as `{card:key}`. The info panel is placed against its card, not its button (LESSON #46). "Nothing moves" is a hard fail for all of these at 1440, 1100 and 375 px; nothing else moves either (no notes left). |
| S3 **DONE v2026.10.14.50** | Firepower (one line under each tile; weapon rows = charge + "weapon · 2.8 + 1.6 km"; ⓘ), Resistance (Repairs note → ⓘ), Navigation & Targeting (one line per tile: "225 m/s without MWD", "8.7 s with MWD on", "20 base + 40 skills", "402 m with MWD on", "Magnetometric"; ⓘ), Capacitor (caption "best case · ASB on charges", "8.3 recharge − 8.6 drain"; ⓘ). Every text colour `--text-faint` → `--text-dim` except 3 disabled controls; `check_subtext.py` fails on it. "Nothing moves" is a hard fail for every card. The rule now covers the whole Fit Analyzer page. |
| F1 **DONE v2026.10.14.51** | Option C strip under the Matchup (`mysFightStripHtml`; menus edit the threat card's settings, `dmgSyncControls` keeps Adjust in step), in-game names Stopped / Approach / Orbit for both ships (their new Stopped state, `theirMode: 'still'`, is the default), one shared fight; the Matchup note removed (errors only), its method text in the board's ⓘ (`CARD_INFO.board`). Also the "How effective HP and DPS are calculated" note → `METHODOLOGY.md`. |
| F2 **DONE v2026.10.14.53** | Keep at Range for both ships (`FIGHT_ANGLE` keep = 180°, `dmgYourSpeed` / `dmgTheirSpeed` = the other's closing speed capped at own top, `fightKeepState` = can it hold); offered only where it holds, chosen-and-no-longer-possible marked amber with the reason; `check_matchup.py` writes the inputs and the rule again. |
| F3 **DONE v2026.10.14.54** | Chart markers 5c (`dmgRangeMarks`, `dmgChartSvg`, `dmgChartKeyHtml`; the y scale held while a slider is dragged, `dmgHoldY`): tackle shaded with the EWAR card's letters, tackle distances and your range on the x axis, DPS at your range on the y axis, range pins + key; chart frame fixed. |
| F4 | Damage Application card in the My Ship Perspective (DPS applied to them, your tackle and ranges, two columns at 1280+). |

## 6. Decisions (made 2026-10-24)

- The rule as written: yes.
- ⓘ opens a panel over the page (like Last Kill; a bottom sheet on a phone).
- Context line limit: 40 characters.
