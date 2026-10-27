# EVE Threat Assessment for zKillboard (Chrome extension)

Right-click on zKillboard to open a kill or a pilot in EVE Threat Assessment (ETA). Version 1.0.0, made with the tool's
v2026.10.14.80.

## What it adds to the right-click menu

| Where you right-click | Item | What the tool opens |
|---|---|---|
| A link to a kill (`zkillboard.com/kill/…`) | Open kill in EVE Threat Assessment | That loss, as a shared killmail (the Pilot Analyzer on that one loss) |
| A kill's own page | Open this kill in EVE Threat Assessment | The same |
| A link to a pilot (`zkillboard.com/character/…`) | Analyze pilot in EVE Threat Assessment | The Pilot Analyzer for that pilot (their most-flown hull, as typing the name) |
| A pilot's own page | Analyze this pilot in EVE Threat Assessment | The same |
| Selected text on any page | Analyze "&lt;text&gt;" in EVE Threat Assessment | The Pilot Analyzer for that name (a selected zKillboard kill or pilot link opens that instead) |

Each opens a new tab. Chrome puts the items under "EVE Threat Assessment for zKillboard" when more than one applies.

## Install (Chrome, Edge, Brave and other Chromium browsers)

1. Open `chrome://extensions` (Edge: `edge://extensions`).
2. Turn on **Developer mode** (top right).
3. Click **Load unpacked** and pick this `browser-extension` folder.
4. Optional: pin it, or open its **Details → Extension options** to change the tool's address.

After pulling a new version from the repo, press the reload icon on the extension's card in `chrome://extensions`.

## The tool's address

The default is `https://gitlaloosh.github.io/dscan-tool/`. Change it in the options page, for example to test a local copy
(`file:///…/index.html`).

## Permissions and privacy

- `contextMenus`: the right-click items.
- `storage`: the tool's address, if you change it (synced with your browser profile).

It reads nothing from the pages you visit and makes no network requests itself: it opens the tool with the kill ID, pilot
ID or name in the address (`#zkill=…`, `#pilot=…`, `#pilotname=…`). The tool then fetches the data from zKillboard and ESI
as it always does.

## How it's checked

`tools/page_checks/extension_check.py` loads this folder into Chromium and checks every menu item, the link each click
opens, the tool page that link shows, and the options page.
