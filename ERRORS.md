# Error codes

Every error EVE Threat Assessment shows ends with a code, for example "... (ZKB-01)". To report a problem,
give the code and the version tag at the top right of the page.

Generated from `ERROR_CODES` in `index.html` by `tools/gen_errors_md.py`; do not edit by hand. Rules: a code is
never reused or renumbered; a retired error keeps its row, marked retired. Prompts for an empty box ("Enter a
pilot name.", "Paste a fit first.") carry no code: they are instructions, not errors.

## The page itself

| Code | What | Where | Cause | What to check | Why it exists | Since |
|---|---|---|---|---|---|---|
| APP-01 | Unexpected error | Any status line | An error the page didn't anticipate: a bug in the tool, not a network or data problem. | Report it with the version tag and what was pasted or typed. The browser console has the full error. | Catch-all so every error shown carries a code; anything shown with APP-01 is a gap to fix. | v2026.10.14.32 ([2026-10-23_error-codes.html](dscan-tool-history/2026-10-23_error-codes.html)) |

## ESI (CCP's API)

| Code | What | Where | Cause | What to check | Why it exists | Since |
|---|---|---|---|---|---|---|
| ESI-01 | ESI name lookup failed | D-Scan, Pilot and Fit Analyzer status lines | ESI's /universe/ids/ (turns pasted names into ids) gave no answer or an error status. The message names the status: 404, 420/429 rate limit, 5xx server error, or no response. | ESI status (esi.evetech.net), the user's connection; a 420/429 clears by waiting. | Every ESI and zKillboard failure used to look identical ('type fetch failed'); ARCH-4 gave each one its context and the cause class. | 2026-10-10 ([2026-10-10_esi-error-messages-phase4.html](dscan-tool-history/2026-10-10_esi-error-messages-phase4.html)) |
| ESI-02 | ESI type fetch failed | Any analysis | ESI's /universe/types/{id}/ failed for one item. A 404 usually means an id ESI doesn't know (often a new or removed item). | The type id in the message; whether ESI has it. | ARCH-4: show which type id failed and why. | 2026-10-10 ([2026-10-10_esi-error-messages-phase4.html](dscan-tool-history/2026-10-10_esi-error-messages-phase4.html)) |
| ESI-03 | ESI group fetch failed | Any analysis | ESI's /universe/groups/{id}/ failed. | The group id in the message; ESI status. | ARCH-4. | 2026-10-10 ([2026-10-10_esi-error-messages-phase4.html](dscan-tool-history/2026-10-10_esi-error-messages-phase4.html)) |
| ESI-04 | ESI id-to-name lookup failed | Pilot Analyzer | ESI's /universe/names/ failed. | ESI status, the user's connection. | ARCH-4. | 2026-10-10 ([2026-10-10_esi-error-messages-phase4.html](dscan-tool-history/2026-10-10_esi-error-messages-phase4.html)) |
| ESI-05 | Killmail fetch failed | Pilot Analyzer (losses, last kill, a shared killmail link) | ESI's /killmails/{id}/{hash}/ failed for one killmail. | The killmail id in the message; ESI status. | ARCH-4. | 2026-10-10 ([2026-10-10_esi-error-messages-phase4.html](dscan-tool-history/2026-10-10_esi-error-messages-phase4.html)) |

## zKillboard

| Code | What | Where | Cause | What to check | Why it exists | Since |
|---|---|---|---|---|---|---|
| ZKB-01 | zKillboard's API isn't answering | Pilot Analyzer status line and the Last Kill line | A zKillboard API call took over 20 s (ZKB_TIMEOUT_MS) or answered 5xx. Since 2026-10-22 zKillboard queues API requests and answers 503 'API result unavailable' when its worker doesn't answer within 60 s. Further zKillboard calls fail at once for 60 s (ZKB_COOLDOWN_MS). | Open a zkillboard.com/api/... URL in a browser. If it shows 'API result unavailable', the problem is on zKillboard's side. | The page used to wait a full minute and then tell the user to check their network. | v2026.10.14.31 ([2026-10-23_zkillboard-api-outage-message.html](dscan-tool-history/2026-10-23_zkillboard-api-outage-message.html)) |
| ZKB-02 | zKillboard losses lookup failed | Pilot Analyzer status line | zKillboard's /api/losses/characterID/... gave no response or a non-5xx error status (5xx is ZKB-01). | The status in the message; the user's connection to zkillboard.com. | ARCH-4. | 2026-10-10 ([2026-10-10_esi-error-messages-phase4.html](dscan-tool-history/2026-10-10_esi-error-messages-phase4.html)) |
| ZKB-03 | zKillboard kills lookup failed | Pilot Analyzer, the Last Kill line | zKillboard's /api/kills/characterID/... answered a non-5xx error status (5xx is ZKB-01). | The status in the message. | ARCH-4. | 2026-10-10 ([2026-10-10_esi-error-messages-phase4.html](dscan-tool-history/2026-10-10_esi-error-messages-phase4.html)) |

## D-Scan Analyzer

| Code | What | Where | Cause | What to check | Why it exists | Since |
|---|---|---|---|---|---|---|
| DSCAN-01 | A fit was pasted into the D-Scan box | D-Scan Analyzer | The paste starts with an EFT header like [Ship, Fit name]. | Nothing to fix: the hint offers to open it in the Fit Analyzer. | Bug list (the owner, 2026-10-14): an EFT fit pasted into the D-Scan box was read as a scan. | v2026.10.14.9 ([2026-10-14_dscan-fit-paste-guard-and-panic-active-state.html](dscan-tool-history/2026-10-14_dscan-fit-paste-guard-and-panic-active-state.html)) |
| DSCAN-02 | ESI rejected the D-Scan names | D-Scan Analyzer | The name lookup for the scan's types failed (wraps the ESI-01 text). Usually the paste lost its tab characters, so whole lines were sent as names. | 'Parsed rows' under the input: whether columns are split correctly. | Points at the paste rather than ESI when columns weren't split. | original (before 2026-10-08) |
| DSCAN-03 | D-Scan lines couldn't be split into columns | D-Scan Analyzer, parsed rows note | Lines without the tab-separated columns a D-Scan copy has. | Copy the scan again with Ctrl+A, Ctrl+C in the client. | Explains why those lines' type lookup will fail. | original (before 2026-10-08) |

## Pilot Analyzer

| Code | What | Where | Cause | What to check | Why it exists | Since |
|---|---|---|---|---|---|---|
| PILOT-01 | No pilot with that name | Pilot Analyzer | ESI doesn't know a character with exactly that name. | Spelling and capitalization. | Name lookups are exact. | original (before 2026-10-08) |
| PILOT-02 | No ship type with that name | Pilot Analyzer (optional ship box) | The typed ship name isn't an ESI type (title-case and apostrophe variants are tried too). | Spelling. |  | original (before 2026-10-08) |
| PILOT-03 | No recorded losses | Pilot Analyzer | zKillboard lists no losses for the pilot. | Type a ship name to analyze that hull without a loss. |  | original (before 2026-10-08) |
| PILOT-04 | Couldn't read the losses to guess a ship | Pilot Analyzer (no ship typed) | None of the sampled loss killmails could be fetched from ESI. | ESI status; type a ship name instead. |  | original (before 2026-10-08) |
| PILOT-05 | Only capsules, shuttles, rookie ships or MTUs lost | Pilot Analyzer (no ship typed) | Every recent loss was a hull the 'most flown' guess leaves out. | Type a ship name. | Those hulls say nothing about what the pilot flies into fights (exact ESI group ids, not name matching). | 2026-10-08 ([2026-10-08_pilot-search-hull-exclusion-filter.html](dscan-tool-history/2026-10-08_pilot-search-hull-exclusion-filter.html)) |
| PILOT-06 | Couldn't read the losses of that hull | Pilot Analyzer | None of the hull's recent loss killmails could be fetched from ESI. | ESI status. |  | original (before 2026-10-08) |
| PILOT-07 | Pilot not among the attackers of their last kill | Pilot Analyzer, the Last Kill line | zKillboard's latest kill for the pilot doesn't list them as an attacker in ESI's killmail. | The killmail on zkillboard.com. |  | 2026-10-10 ([2026-10-10_last-kill-hull-pivot-button.html](dscan-tool-history/2026-10-10_last-kill-hull-pivot-button.html)) |

## Fit Analyzer

| Code | What | Where | Cause | What to check | Why it exists | Since |
|---|---|---|---|---|---|---|
| FIT-01 | The fit paste is empty | Fit Analyzer | Only blank lines were pasted. | Paste a fit copied from the EVE client or exported from pyfa. |  | original (before 2026-10-08) |
| FIT-02 | The first line isn't an EFT header | Fit Analyzer | The paste doesn't start with [Ship Name, Fit Name]. | Paste the whole fit, header included. |  | original (before 2026-10-08) |
| FIT-03 | The fit's ship isn't recognized | Fit Analyzer | The ship name in the header doesn't resolve in ESI (title-case and apostrophe variants are tried too). | Spelling of the ship name. |  | original (before 2026-10-08) |
| FIT-04 | Some fit lines weren't recognized | Fit Analyzer, note under the fit; My Ship panel, the "Viewing My Ship" page and the My Ship Perspective | Item names that don't resolve in ESI; they're left out of the fit. | Spelling, SKIN variants, renamed or removed items. | The rest of the fit is still analyzed; the note lists what was dropped. | original (before 2026-10-08) |

## My Ship

| Code | What | Where | Cause | What to check | Why it exists | Since |
|---|---|---|---|---|---|---|
| MYSHIP-01 | Browser storage unavailable | My Ship panel | The browser refused to store or read the saved ship: a private window, blocked site data, or full storage. | The browser's site-data settings for the page. My Ship still works until the page is closed. | My Ship lives only in the browser; without storage it is gone after a reload, and the user should know that before relying on it. | v2026.10.14.33 ([2026-10-23_my-ship-phase1.html](dscan-tool-history/2026-10-23_my-ship-phase1.html)) |
| MYSHIP-02 | The saved ship couldn't be loaded | My Ship panel, the Fit Analyzer's "Viewing My Ship" page, the Matchup | The saved fit is recomputed from its EFT text when first needed, and that failed (the message includes the underlying code, e.g. ESI-01), or the stored copy is damaged. | The underlying code in the message. If an item was renamed or removed from the game, Replace the fit. | Recomputing on load lets tool fixes and game patches apply to a saved ship; when it fails, the saved text is kept rather than dropped. | v2026.10.14.33 ([2026-10-23_my-ship-phase1.html](dscan-tool-history/2026-10-23_my-ship-phase1.html)) |
| MYSHIP-03 | My Ships is full | My Ship panel (+ Add a fit, the paste box), the Fit Analyzer's "Set as my ship" | Adding a fit when 20 are already saved (MY_SHIPS_MAX; the owner 2026-10-25: "limit the list of fits they can save to 20 for now"). | Delete a saved fit you no longer fly, or Replace one, then add the new fit. | A fixed limit keeps the list and the Matchup's ship menu short; the browser could hold far more. | v2026.10.14.65 ([2026-10-25_my-ships-saved-fits.html](dscan-tool-history/2026-10-25_my-ships-saved-fits.html)) |

## DMG

| Code | What | Where | Cause | What to check | Why it exists | Since |
|---|---|---|---|---|---|---|
| DMG-01 | No ship to apply their damage to | Damage Application card (Fit Analyzer and Pilot losses) | The typical-class preset fit (a hull with its MWD, built from EFT text like any pasted fit) failed to build (the message includes the underlying code, e.g. ESI-01), or your saved ship's hull has no dogma effects, so pyfa's speed and signature can't be worked out for it. | The underlying code in the message; pick another class, or set your own ship. | The chart needs a real target fit (speed, signature, what their scram switches off); it says so rather than charting against made-up numbers. | v2026.10.14.36 ([2026-10-23_their-damage-on-you-chart.html](dscan-tool-history/2026-10-23_their-damage-on-you-chart.html)) |
| DMG-02 | No chart of the damage applied to them | Damage Application card in the My Ship Perspective | Your ship's or the threat's hull record has no dogma effects (no application or no projected target), so pyfa's damage graph can't be worked out for your guns on them. | Which hull it is; the Matchup shows the same gap as dashes. | This chart is the same fight as the board's "DPS applied to them"; without both ships' pyfa inputs it says so rather than charting made-up numbers. | v2026.10.14.55 ([2026-10-24_damage-application-in-my-ship-perspective.html](dscan-tool-history/2026-10-24_damage-application-in-my-ship-perspective.html)) |

## SHARE

| Code | What | Where | Cause | What to check | Why it exists | Since |
|---|---|---|---|---|---|---|
| SHARE-01 | zKillboard has no such killmail | Pilot Analyzer status line, a zKillboard kill link pasted into the pilot box | zKillboard's /api/killID/{id}/ didn't return that killmail (no killmail with that ID, or a non-5xx error status; 5xx is ZKB-01). | The killmail ID in the link; open the link on zkillboard.com. | The hash ESI needs comes from zKillboard; without it the killmail can't be fetched. | v2026.10.14.79 ([2026-10-27_shared-killmail-links.html](dscan-tool-history/2026-10-27_shared-killmail-links.html)) |
| SHARE-02 | Incomplete shared killmail link | Pilot Analyzer status line, a page opened from a link | The address has #kill= but not a killmail ID and a 40-character hash (#kill={id}/{hash}), e.g. a link cut short when pasted. | Copy the link again with "Copy share link" in the loss's ⋮ menu. |  | v2026.10.14.79 ([2026-10-27_shared-killmail-links.html](dscan-tool-history/2026-10-27_shared-killmail-links.html)) |
| SHARE-03 | Pilot link not recognized | Pilot Analyzer status line, a page opened from the browser extension | #pilot={id} with an ID ESI doesn't know as a pilot, or #pilotname= with no name (or longer than EVE's 37 characters). | The pilot's zKillboard page; the text that was selected. |  | v2026.10.14.80 ([2026-10-27_browser-extension.html](dscan-tool-history/2026-10-27_browser-extension.html)) |

## WP

| Code | What | Where | Cause | What to check | Why it exists | Since |
|---|---|---|---|---|---|---|
| WP-01 | Weaknesses picks not worked out | Weaknesses card, with My Ship saved and "Use in assessments" on (the Threat Perspective and the My Ship Perspective) | Running the fit again with one of its carried charges or drone types failed, usually because a charge or drone type couldn't be fetched (the message includes the underlying code, e.g. ESI-01). | The underlying code in the message; pick the other side on the Matchup or move a slider to try again. | The picks are pyfa numbers for each charge and drone aboard; when one can't be worked out the card says so instead of ranking what's left. | v2026.10.14.42 ([2026-10-23_weaknesses-your-guns-their-guns.html](dscan-tool-history/2026-10-23_weaknesses-your-guns-their-guns.html)) |
