# Card and page-part names (the one list)

Status: **built in v2026.10.14.45** (2026-10-24): `CARD_NAMES` + `cardName()` in index.html, checked by
`tools/check_card_names.py` (update-check chain). This table and `CARD_NAMES` must match; the check compares them.

Names are Title Case (the owner 2026-10-23: "card names should use my structure", after "Navigation & Targeting").

the owner (2026-10-23): "i see a recurring issue with not having definitive names for each card. it results in subtext and
explanatory info referencing card titles that should be interchangeable."

## The names

Every card title, collapsed row, note, tooltip and error-code location takes its name from this list by key. Nothing
types a name by hand.

| Key | Name | Was / notes |
|---|---|---|
| `weak` | Weaknesses | |
| `ewar` | EWAR / Misc | some text said "EWAR card" |
| `fp` | Firepower | |
| `rs` | Resistance | |
| `nav` | Navigation & Targeting | was "Navigation & targeting"; the owner 2026-10-23: "please capitalize targeting"; key was `nv` (the owner: "let's change to nav") |
| `cp` | Capacitor | |
| `fit` | Fit | |
| `dmg` | Damage Application | was "Their damage on you"; the owner: "we're getting rid of 'Damage applied to you'" (that stays a phrase in the text, not the name) |
| `board` | Matchup | the scoreboard; was "switch" / "strip" in text and error codes |
| `lastkill` | Last Kill | the header line and its panel; was "last-kill box" |
| `perspective.threat` | Threat Perspective | which ship the cards describe, picked on the Matchup; key was `views` (the owner 2026-10-23: "change the 'views' key to 'perspective' and we'll adjust names/text accordingly"); was "threat view" in text. Text reads e.g. "from the Threat Perspective" |
| `perspective.mine` | My Ship Perspective | the other side of `perspective`; was "My ship view" |
| `myshippage` | Viewing My Ship | the Fit Analyzer page that shows your saved ship on its own (no Matchup); a different thing from the My Ship Perspective, so it keeps its own key |

Settled: Title Case for every name (the open capitalisation question is closed).

## Task: build the registry (DONE v2026.10.14.45; the chart labels are still open, turret-application-plan.md)

1. `CARD_NAMES` in index.html (key -> name) and a helper that every title, collapsed row and sentence uses;
   ERROR_CODES "where" fields name parts by key, resolved by `tools/gen_errors_md.py`.
2. A new update-check step that fails when a listed name appears anywhere outside the list (user-facing strings and
   ERROR_CODES), or when text names a part that isn't in it.
3. Today's stale references to fix with it: the Capacitor note's "EWAR card"; PILOT-0x "last-kill box"; MYSHIP-02
   "threat / my ship switch" (now the Matchup); WP-01 "(threat view and My ship view)" (now the two perspectives); the scoreboard and picks notes and DMG-01 naming "Their damage on you" (now "Damage Application").
4. Page checks read titles from the list instead of literal text.
5. The code's card key `nv` becomes `nav` everywhere it is used (FIT_LAYOUT stacks, cardOpen, layout_check CARD_KEYS,
   card_width_check); nothing stores card keys in the browser, so no saved state is lost.

## How to rename a card (or add a part)

1. Change the name in `CARD_NAMES` (index.html, near the top of the script) and the same row above.
2. Run `python3 -I tools/check_card_names.py` and `python3 -I tools/gen_errors_md.py --write` (ERRORS.md fills the
   `{card:key}` names in).
3. A new card or part: add a key to both, then use `cardName('key')` (titles come from `cardLabelHtml(key)` and
   `collapsedCardHtml(key, summary)`, which take no title).
4. The old name, if it was ever shown, goes into `RETIRED` in check_card_names.py so it can't creep back.
