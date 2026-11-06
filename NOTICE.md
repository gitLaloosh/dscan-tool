# Threat Vector: license, credits and notices

Threat Vector (`index.html`, the browser extension and the tools in this repository)
Copyright (C) 2026 the Threat Vector contributors

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program (the file `LICENSE`). If not,
see <https://www.gnu.org/licenses/>.

## Why GPL v3

The page's fitting calculations (the `PYFA CORE` sections of `index.html`, listed in `PYFA_CORE.md`, and the tables the
`tools/gen_*.py` scripts generate) port or mirror code from pyfa. pyfa is released under the GNU GPL v3 ("either version 3
of the License, or (at your option) any later version", in its `service/` files); its `eos/` engine files are under the GNU
LGPL ("version 2 of the License, or (at your option) any later version"). Both allow this use under GPL v3 or later, which
is why this project uses it.

## Credits

- **pyfa** (<https://github.com/pyfa-org/Pyfa>), the EVE fitting tool, by its authors: the fitting, damage, capacitor,
  resistance and stacking calculations follow its source (the verified commit is in `tools/pyfa_core_manifest.json`).
- **CCP hf.**: EVE Online's game data (ESI, the Static Data Export and the client's static data files), its images
  (images.evetech.net), and the names of ships, items, systems and pilots.
- **zKillboard** (<https://zkillboard.com/>): killmail statistics and its live kill feed (R2Z2).

## CCP's notice

As the EVE Developer License Agreement (section 7.1) words it:

© CCP hf. All rights reserved. "EVE", "EVE Online", "CCP", and all related logos and images are trademarks or registered
trademarks of CCP hf.

Threat Vector is not made, endorsed or supported by CCP hf. It is offered for free and for non-commercial use.
The same notice and the license are shown in the page's footer.
