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
| ZKB-01 | zKillboard's API isn't answering | Pilot Analyzer status line and the Last Kill line | A zKillboard API call took over 20 s (ZKB_TIMEOUT_MS) or answered 5xx. Since 2026-10-22 zKillboard queues API requests and answers 503 'API result unavailable' when its worker doesn't answer within 60 s. Further zKillboard calls fail at once for 60 s (ZKB_COOLDOWN_MS); since v2026.10.14.81 the pause doubles with each failure in a row, up to 10 minutes (ZKB_COOLDOWN_MAX_MS, plan D4). | Open a zkillboard.com/api/... URL in a browser. If it shows 'API result unavailable', the problem is on zKillboard's side. | The page used to wait a full minute and then tell the user to check their network. | v2026.10.14.31 ([2026-10-23_zkillboard-api-outage-message.html](dscan-tool-history/2026-10-23_zkillboard-api-outage-message.html)) |
| ZKB-02 | zKillboard losses lookup failed | Pilot Analyzer status line | zKillboard's /api/losses/characterID/... gave no response or a non-5xx error status (5xx is ZKB-01). | The status in the message; the user's connection to zkillboard.com. | ARCH-4. | 2026-10-10 ([2026-10-10_esi-error-messages-phase4.html](dscan-tool-history/2026-10-10_esi-error-messages-phase4.html)) |
| ZKB-03 | zKillboard kills lookup failed | Pilot Analyzer, the Last Kill line | zKillboard's /api/kills/characterID/... answered a non-5xx error status (5xx is ZKB-01). | The status in the message. | ARCH-4. | 2026-10-10 ([2026-10-10_esi-error-messages-phase4.html](dscan-tool-history/2026-10-10_esi-error-messages-phase4.html)) |
| ZKB-04 | zKillboard limit reached in this browser | Any zKillboard lookup (Pilot Analyzer, System Analyzer, Standings) | The page asked zKillboard ZKB_BUDGET (100) times within 10 minutes in this browser (counted in localStorage across reloads; plan D4). | Wait the minutes the message gives; anything already looked up (kept for an hour) still works. | the owner (D4): keep the tool polite to zKillboard, which asks tools not to hammer its API. | v2026.10.14.81 ([2026-10-27_system-analyzer-local-and-your-side.html](dscan-tool-history/2026-10-27_system-analyzer-local-and-your-side.html)) |
| ZKB-05 | zKillboard lookup for your side failed | System Analyzer (the evidence) and Standings (suggested friendlies) | zKillboard's /api/losses/ or /api/kills/ for your alliance (or corporation) answered a non-5xx error status or something that isn't a list (5xx is ZKB-01). | The status in the message; open the same zkillboard.com/api/... URL in a browser. | The evidence and the suggestions are extras: the lists still work without them, and the message says why they're missing. | v2026.10.14.81 ([2026-10-27_system-analyzer-local-and-your-side.html](dscan-tool-history/2026-10-27_system-analyzer-local-and-your-side.html)) |

## System Analyzer: the D-Scan box

| Code | What | Where | Cause | What to check | Why it exists | Since |
|---|---|---|---|---|---|---|
| DSCAN-01 | A fit was pasted into the D-Scan box | System Analyzer, D-Scan box | The paste starts with an EFT header like [Ship, Fit name]. | Nothing to fix: the hint offers to open it in the Fit Analyzer. | Bug list (the owner, 2026-10-14): an EFT fit pasted into the D-Scan box was read as a scan. | v2026.10.14.9 ([2026-10-14_dscan-fit-paste-guard-and-panic-active-state.html](dscan-tool-history/2026-10-14_dscan-fit-paste-guard-and-panic-active-state.html)) |
| DSCAN-02 | ESI rejected the D-Scan names | System Analyzer, D-Scan box | The name lookup for the scan's types failed (wraps the ESI-01 text). Usually the paste lost its tab characters, so whole lines were sent as names. | 'Parsed rows' under the input: whether columns are split correctly. | Points at the paste rather than ESI when columns weren't split. | original (before 2026-10-08) |
| DSCAN-03 | D-Scan lines couldn't be split into columns | System Analyzer, D-Scan box, parsed rows note | Lines without the tab-separated columns a D-Scan copy has. | Copy the scan again with Ctrl+A, Ctrl+C in the client. | Explains why those lines' type lookup will fail. | original (before 2026-10-08) |

## System Analyzer: Local

| Code | What | Where | Cause | What to check | Why it exists | Since |
|---|---|---|---|---|---|---|
| SYS-01 | Local lookup failed (affiliations) | System Analyzer status line, and setting your pilot in Standings | ESI's POST /characters/affiliation/ failed (no response or an error status). | The status in the message; ESI's status page. | Without each pilot's corporation and alliance nobody can be sorted into a side. | v2026.10.14.81 ([2026-10-27_system-analyzer-local-and-your-side.html](dscan-tool-history/2026-10-27_system-analyzer-local-and-your-side.html)) |
| SYS-02 | Not a Local member list | System Analyzer status line | The Local box holds D-Scan rows (tab-separated) or a ship fit (EFT). | Paste the D-Scan in the D-Scan box, a fit in the Fit Analyzer. | Names from a scan or a fit aren't pilots; looking them up would only fill the not-found list. | v2026.10.14.81 ([2026-10-27_system-analyzer-local-and-your-side.html](dscan-tool-history/2026-10-27_system-analyzer-local-and-your-side.html)) |

## Your Side

| Code | What | Where | Cause | What to check | Why it exists | Since |
|---|---|---|---|---|---|---|
| SIDE-01 | Your pilot wasn't found | Standings, your pilot | ESI's /universe/ids/ has no pilot by the name typed. | The spelling; pilot names must match exactly. | Your pilot is what sets your corporation and alliance. | v2026.10.14.81 ([2026-10-27_system-analyzer-local-and-your-side.html](dscan-tool-history/2026-10-27_system-analyzer-local-and-your-side.html)) |
| SIDE-02 | Alliance or corporation not found | Standings, the friendly and hostile lists | ESI's /universe/ids/ has no alliance or corporation by one of the names added (a ticker instead of the name, or a typo). | Use the full name, as on the alliance's or corporation's info window. | ESI looks groups up by their name, not their ticker. | v2026.10.14.81 ([2026-10-27_system-analyzer-local-and-your-side.html](dscan-tool-history/2026-10-27_system-analyzer-local-and-your-side.html)) |

## Pilot Analyzer

| Code | What | Where | Cause | What to check | Why it exists | Since |
|---|---|---|---|---|---|---|
| PILOT-01 | No pilot with that name | Pilot Analyzer | ESI doesn't know a character with exactly that name. | Spelling and capitalization. | Name lookups are exact. | original (before 2026-10-08) |
| PILOT-02 | No ship type with that name | Pilot Analyzer (optional ship box) | The typed ship name isn't an ESI type (title-case and apostrophe variants are tried too). | Spelling. |  | original (before 2026-10-08) |
| PILOT-03 | No recorded kills or losses | Pilot Analyzer | zKillboard lists no kills and no losses for the pilot (since v2026.10.14.90 kills count too). | Type a ship name to analyze that hull without a loss. |  | original (before 2026-10-08) |
| PILOT-04 | Couldn't read the losses to guess a ship | Pilot Analyzer (no ship typed) | None of the sampled loss killmails could be fetched from ESI. | ESI status; type a ship name instead. |  | original (before 2026-10-08) |
| PILOT-05 | Only capsules, shuttles, rookie ships or MTUs lost | Pilot Analyzer (no ship typed) | Every recent loss was a hull the 'most flown' guess leaves out. | Type a ship name. | Those hulls say nothing about what the pilot flies into fights (exact ESI group ids, not name matching). | 2026-10-08 ([2026-10-08_pilot-search-hull-exclusion-filter.html](dscan-tool-history/2026-10-08_pilot-search-hull-exclusion-filter.html)) |
| PILOT-06 | Couldn't read the losses of that hull | Pilot Analyzer | None of the hull's recent loss killmails could be fetched from ESI. | ESI status. |  | original (before 2026-10-08) |
| PILOT-07 | Pilot not among the attackers of their last kill | Pilot Analyzer, the Last Kill line | zKillboard's latest kill for the pilot doesn't list them as an attacker in ESI's killmail. | The killmail on zkillboard.com. |  | 2026-10-10 ([2026-10-10_last-kill-hull-pivot-button.html](dscan-tool-history/2026-10-10_last-kill-hull-pivot-button.html)) |
| PILOT-08 | Couldn't load the pilot's corporation | Pilot Analyzer, Pilot Affiliation | ESI's /characters/{id}/ didn't answer (offline, an ESI outage, or a character ESI no longer knows). | ESI status; analyze the pilot again. The rest of the Pilot Analyzer doesn't need it. |  | 2026-10-27 (v2026.10.14.87) ([2026-10-27_pilot-affiliation-and-zkillboard-stats.html](dscan-tool-history/2026-10-27_pilot-affiliation-and-zkillboard-stats.html)) |
| PILOT-09 | Couldn't read some of their older kills | Pilot Analyzer, Pilot Dossier, the kills under a row | ESI didn't return some killmails while Show 10 more read their older kills (offline, an ESI outage). | ESI status; press Try again under the list once ESI answers. The kills already shown stay. |  | 2026-10-27 (v2026.10.14.93) ([2026-10-27_dossier-kills-under-a-row.html](dscan-tool-history/2026-10-27_dossier-kills-under-a-row.html)) |

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

## FLEET

| Code | What | Where | Cause | What to check | Why it exists | Since |
|---|---|---|---|---|---|---|
| FLEET-01 | A fleet link that isn't complete | Fleet tab, opened from a link | A #fleet= link without a killmail ID and its 40-character hash, or with a pilot entry the page can't read (cut short when copied). | Copy the link again with Copy share link on the Fleet tab. |  | 2026-10-28 (v2026.10.14.94) ([2026-10-28_fleet-from-a-kill.html](dscan-tool-history/2026-10-28_fleet-from-a-kill.html)) |

## INTEL

| Code | What | Where | Cause | What to check | Why it exists | Since |
|---|---|---|---|---|---|---|
| INTEL-01 | This browser can't read the chat logs | Intel tab | The browser has no File System Access API (showDirectoryPicker): Firefox, Safari, or a page not served over https. | Use Chrome or Edge on the GitHub Pages address. |  | 2026-10-28 (v2026.10.14.96) ([2026-10-28_intel-feed.html](dscan-tool-history/2026-10-28_intel-feed.html)) |
| INTEL-02 | The chat logs folder can't be read | Intel tab | The browser didn't allow reading the chosen folder (Allow not pressed after a restart), or the folder was moved or deleted while watching. | Turn the slider on again and choose Allow; or choose the folder again under the gear. |  | 2026-10-28 (v2026.10.14.96) ([2026-10-28_intel-feed.html](dscan-tool-history/2026-10-28_intel-feed.html)) |
| INTEL-03 | The system names didn't load | Intel tab, turning it on | ESI's /universe/names/ failed for the stargate table's systems (asked once, then kept in the browser), or named fewer than 90% of them. | ESI status, the connection; turn the slider on again. |  | 2026-10-28 (v2026.10.14.96) ([2026-10-28_intel-feed.html](dscan-tool-history/2026-10-28_intel-feed.html)) |
| INTEL-04 | No EVE chat logs in the folder | Intel tab | The chosen folder has no file named like an EVE chat log (<Channel>_<date>_<time>_<character>.txt). | Choose Documents\EVE\logs\Chatlogs (OneDrive may have moved Documents); in EVE turn on Log Chat to File. |  | 2026-10-28 (v2026.10.14.96) ([2026-10-28_intel-feed.html](dscan-tool-history/2026-10-28_intel-feed.html)) |
| INTEL-05 | zKillboard's live kill feed isn't answering | Intel tab, kills in the Feed | R2Z2 (r2z2.zkillboard.com, zKillboard's live feed) gave an error or no answer. The page tries again after 30 seconds, then longer (up to 5 minutes); reports from your channels carry on. | zKillboard's status; the connection. zKillboard blocks an address that asks more than 15 times a second for an hour; the page then can't read any file, so this note stays for up to an hour. Since v2026.10.30.3 the page asks at most 5 times a second, hidden tab or not, and stops for an hour at a 429 (INTEL-07). |  | 2026-10-28 (v2026.10.14.99) ([2026-10-28_intel-feed-kills.html](dscan-tool-history/2026-10-28_intel-feed-kills.html)) |
| INTEL-06 | This browser can't read zKillboard's live kill feed | Intel tab, kills in the Feed | sequence.json from R2Z2 (r2z2.zkillboard.com) came back with nothing the page may read: the browser blocked the answer (zKillboard's answer lacked the header that lets other websites read it, CORS), a blocker stopped it, or there is no connection. Read at the start and after a minute with no kill. The page tries again after 30 seconds, then longer (up to 5 minutes); reports from your channels carry on. | The browser's console (F12): 'blocked by CORS policy' means zKillboard's setting changed (it happened briefly on 2026-10-29); tell zKillboard. Otherwise an ad or privacy blocker, or the connection. | On 2026-10-29 zKillboard removed the Origin from requests to fix stale copies at Cloudflare, and for a while answers came without the permission header: every browser threw them away while curl and desktop apps still read them. | 2026-10-29 (v2026.10.29.8) ([2026-10-29_kills-read-as-documented.html](dscan-tool-history/2026-10-29_kills-read-as-documented.html)) |
| INTEL-07 | zKillboard asked the page to slow down | Intel tab, kills in the Feed | R2Z2 (r2z2.zkillboard.com) answered 429, 420 or 403: too many requests from this address, or not allowed. zKillboard bans an address that asks more than 15 times a second for an hour. The page stops at the first such answer, drops every request still queued, and sends nothing to R2Z2 for an hour (kept in this browser, so a reload or another tab waits too); the note says until when. Reports from your channels carry on. | Another copy of the page with Intel on (another tab, browser or a local copy) or another tool reading R2Z2 from the same address. The page itself asks at most 5 times a second. | zKillboard's developer, 2026-06-04: the limit cut from 20 to 15 a second, the ban raised from 10 minutes to an hour, and the limit cut further if abuse continues. Asking again during a ban helps nobody. | 2026-10-30 (v2026.10.30.3) ([2026-10-30_live-feed-guard-and-plus-counts.html](dscan-tool-history/2026-10-30_live-feed-guard-and-plus-counts.html)) |
| INTEL-08 | The page stopped itself asking zKillboard's live feed | Intel tab, kills in the Feed | The page counted more requests to R2Z2 in one second than it allows itself (5). Its gate should make that impossible, so this is a fault in the page: it stops for an hour before zKillboard has to ban the address. | A bug: report it with the version. tools/page_checks/intel_guard_check.py tests this tripwire. | A second, independent guard behind the gate (the owner: testing the fix itself must not get us blocked). | 2026-10-30 (v2026.10.30.3) ([2026-10-30_live-feed-guard-and-plus-counts.html](dscan-tool-history/2026-10-30_live-feed-guard-and-plus-counts.html)) |

## SHARE

| Code | What | Where | Cause | What to check | Why it exists | Since |
|---|---|---|---|---|---|---|
| SHARE-01 | zKillboard has no such killmail | Pilot Analyzer status line, a zKillboard kill link pasted into the pilot box | zKillboard's /api/killID/{id}/ didn't return that killmail (no killmail with that ID, or a non-5xx error status; 5xx is ZKB-01), or couldn't be reached at all (a network error; since v2026.10.14.93, was APP-01). | The killmail ID in the link; open the link on zkillboard.com. | The hash ESI needs comes from zKillboard; without it the killmail can't be fetched. | v2026.10.14.79 ([2026-10-27_shared-killmail-links.html](dscan-tool-history/2026-10-27_shared-killmail-links.html)) |
| SHARE-02 | Incomplete shared killmail link | Pilot Analyzer status line, a page opened from a link | The address has #kill= but not a killmail ID and a 40-character hash (#kill={id}/{hash}), e.g. a link cut short when pasted. | Copy the link again with "Copy share link" in the loss's ⋮ menu. |  | v2026.10.14.79 ([2026-10-27_shared-killmail-links.html](dscan-tool-history/2026-10-27_shared-killmail-links.html)) |
| SHARE-03 | Pilot link not recognized | Pilot Analyzer status line, a page opened from the browser extension | #pilot={id} with an ID ESI doesn't know as a pilot, or #pilotname= with no name (or longer than EVE's 37 characters). | The pilot's zKillboard page; the text that was selected. |  | v2026.10.14.80 ([2026-10-27_browser-extension.html](dscan-tool-history/2026-10-27_browser-extension.html)) |

## WP

| Code | What | Where | Cause | What to check | Why it exists | Since |
|---|---|---|---|---|---|---|
| WP-01 | Weaknesses picks not worked out | Weaknesses card, with My Ship saved and "Use in assessments" on (the Threat Perspective and the My Ship Perspective) | Running the fit again with one of its carried charges or drone types failed, usually because a charge or drone type couldn't be fetched (the message includes the underlying code, e.g. ESI-01). | The underlying code in the message; pick the other side on the Matchup or move a slider to try again. | The picks are pyfa numbers for each charge and drone aboard; when one can't be worked out the card says so instead of ranking what's left. | v2026.10.14.42 ([2026-10-23_weaknesses-your-guns-their-guns.html](dscan-tool-history/2026-10-23_weaknesses-your-guns-their-guns.html)) |
