# tools/ — verification tooling for D-Scan Analyzer calculations

Everything here reads **primary sources only**: pyfa's real source code
(`eos/effects.py`) and CCP's SDE, which pyfa ships under `staticdata/fsd_built/`.
Nothing here reads `index.html`'s tables, except where a script compares
against them on purpose (`gen_weapon_range_table.py`).

Read `../LESSONS_LEARNED.md` first. It explains why these tools exist.

## Setup (no pip installs needed)

```
git clone https://github.com/pyfa-org/Pyfa  /some/path/Pyfa   # verified with v2.69.2, SDE build 3579973
export PYFA_SRC=/some/path/Pyfa
python3 -I tools/gen_weapon_range_table.py index.html
```

`-I` (isolated mode) is deliberate. The scripts set their own import paths.

## Files

| File | What it does |
|---|---|
| `pyfa_sde.py` | Loads the SDE from pyfa's dump. `A('Rokh')` returns an attribute dict by name; `reqs(typeId)` returns the direct required skills (what pyfa's `requiresSkill` checks). |
| `pyfa_effects.py` | **Runs pyfa's real effect handlers** against a recording mock fit. It tells you exactly which attribute a handler changes, from which source attribute, with which skill scaling, and whether it is stacking-penalized and in which penalty group. `filter_hits()` evaluates the handler's filter against real SDE items. For skill effects pass `carrier=skillTypeId` (LESSON #19). Use this instead of regex-reading `effects.py`. |
| `audit_effect_tables.py` (+ `dump_effect_tables.mjs`) | Runs every pyfa handler and compares with `index.html`'s capacitor, HP, sensor, repair, shield-recharge and signature tables. Prints MISSING / EXTRA / ROW MISSING / FILTER, PENALTY or LEVEL DIFF, plus skill rows. Deliberate exclusions live in its `KNOWN` list with reasons. Run: `node tools/dump_effect_tables.mjs index.html > /tmp/t.json && python3 -I tools/audit_effect_tables.py /tmp/t.json`. A clean run prints no MISSING/EXTRA/DIFF lines. |
| `gen_module_state_tables.py` | Regenerates `EFFECT_STATE_TYPE` (which effects are active/offline/overheat), `GROUP_LIMIT_MOD_EFFECTS` (maxGroupActive/Online modifiers) and `ACTIVATION_BLOCK_EFFECTS` from pyfa's handler types and recorded calls, and diffs them with `index.html`. Re-run after a pyfa/SDE update. |
| `gen_weapon_range_table.py` | Worked example: regenerates `WEAPON_RANGE_MOD_EFFECTS` and diffs it against `index.html`. Copy it as the template for any "every handler that changes attribute X" table. Re-run it after a pyfa/SDE update to see what changed. |
| `independent_checks/` | Hand-typed pyfa rules with SDE values. These produce the **expected** numbers for golden fits. Each script prints `label (pinned value) computed value`. |

## independent_checks

| Script | Batch | Golden fits it produced |
|---|---|---|
| `check_capacitor.py` | v.11 capacitor | executioner/tengu constructed; `check_capacitor.py <golden_id>` for any fit's module drain |
| `check_targeting.py` | v.13 targeting | caracal/crow/tengu constructed |
| `check_hp.py` | v.14 HP pools | megathron/guardian constructed |
| `check_repairs.py` | v.15 repairs | hyperion/maelstrom constructed |
| `check_signature.py` | v.16 signature | vagabond/hyena/svipul/legion constructed + pins |
| `check_weapon_range.py` | v.17 weapon range | rokh/raven/hecate/jackdaw constructed + pins |
| `check_recorder_audit.py` | v.19 table audit | apostle (triage), valravn, exequror constructed; Bastion sensor pins |
| `check_module_states.py` | v.20 module states | vargur (Bastion/MJD states), rifter (dual prop, rep offline, ADC/hardener states), prophecy/damnation (Command Burst limits) constructed; Ishtar/Ishkur pins |
| `check_required_skills.py` | v.21 required skills 4–6 | revelation (capital T2 Gunnery slot 4; capital T1 no Specialization), abaddon (Aralez two racial specs) constructed |
| `check_drone_states.py` | v.23 drones in space | abaddon drone-state constructed fits (default, mixed, bandwidth refused, 5-drone refused) |

Python's `round()` rounds .5 to even and JavaScript's `Math.round` rounds .5 up.
So 70,312.5 prints as 70312 here and 70313 in the tool. That's expected.

**When you add a batch, add its check script here.** The script alone must
reproduce every pinned number. If you need a manual adjustment that lives only
in a golden-fit note, the script is incomplete. That happened once:
`check_capacitor.py` was missing the Executioner's scram role bonus, which the
note applied by hand.
