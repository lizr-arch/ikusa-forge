# Local Development Setup

This repository is currently in Phase 1 deterministic battle skeleton v0.1 state.

The config pipeline, first pure Python model boundary, and minimal deterministic replay event stream exist so later tasks can add combat rules, a C# subprocess host, and an HTML replay debugger without mixing responsibilities.

## Expected local tools

- Project target: Python >= 3.10.
- Recommended Python: 3.11 or newer.
- Python 3.6 is no longer supported for the Python combat model layer because it uses standard-library dataclasses and modern typing expectations.
- On Windows, prefer `py -3.11` for all simulator/model commands.
- .NET SDK for the future C# host.
- A modern browser for the future HTML replay debugger.

No heavy dependencies are required for the current CSV-first config pipeline.

## Repository layout

```text
config/source/      Designer-editable source data and CSV sample data.
config/generated/   Runtime JSON output; generated files are ignored.
sim-python/         Pure Python combat simulator package and tests.
host-csharp/        Future C# host that invokes Python as a subprocess.
web-viewer/         Future local HTML replay debugger.
tools/              Export, validation, inspection, and demo-run scripts.
runs/               Generated battle run output; generated files are ignored.
docs/schema/        JSON schema drafts for runtime config.
```

## Export config

The v0.1 exporter keeps the stable command name planned for xlsx support:

```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
```

On Windows, prefer the Python launcher when Python 3.11 is installed:

```bash
py -3.11 tools/export_xlsx_to_json.py --input config/source --output config/generated
```

The bare `python` command is kept as a compatibility example for simple local shells.

Current behavior:

- v0.1/v0.1.3 reads CSV sample data from `config/source/sample_data/*.csv`.
- Writes formatted runtime JSON to `config/generated/*.json`.
- Converts configured comma-separated fields into JSON arrays.
- Parses configured JSON cells such as formation patterns and encounter unit lists.
- Writes `constants.json` as a runtime-friendly object, not a row list.

Expected generated constants shape:

```json
{
  "tick_rate": 20,
  "max_ticks": 1200,
  "board_rows": 3,
  "board_cols": 4,
  "default_seed": 1001
}
```

## Validate config

Validate generated runtime JSON with:

```bash
python tools/validate_config.py --input config/generated
```

Windows Python launcher form:

```bash
py -3.11 tools/validate_config.py --input config/generated
```

The validator currently checks:

- duplicate ids, or duplicate constant keys
- missing required fields
- missing skill, weapon type, unit, and formation references
- negative `hp`, `atk`, `defense`, `range`, `cooldown`, and `attack_interval`
- basic 4x3 formation and encounter coordinate validity
- non-empty `role` values for every formation `pattern.slots` entry
- encounter unit coordinates against the selected formation's `pattern.slots`
- required constants: `tick_rate`, `max_ticks`, `board_rows`, `board_cols`, `default_seed`
- negative numeric constants such as `max_ticks`

With v0.1.3 validation, simulator work can safely rely on `unit coordinate -> formation slot -> role` lookup before applying formation bonuses.

## Load config models

The first Python combat-core layer can load generated JSON into pure config
models without running a battle:

```bash
python tools/inspect_config_models.py --config config/generated
```

Windows Python launcher form:

```bash
py -3.11 tools/inspect_config_models.py --config config/generated
```

Current behavior:

- Reads only `config/generated/*.json`.
- Calls the config validator before loading models.
- Builds a `ConfigBundle` of pure config dataclasses.
- Prints the `demo_001` player and enemy formation coordinate-to-role lookup.
- Acts as the current smoke/debug CLI for the config model layer.

See `docs/process/python-combat-models-v0.1.md` for the model boundary.

`UnitDef` is a reusable config definition loaded from runtime JSON. `UnitState` is a per-battle runtime instance created from `UnitDef`, encounter placement, and formation role. `ConfigBundle` is the read-only config collection. `BattleState` is one battle run's runtime state.

## Run deterministic battle skeleton

After export and validation, run the Phase 1 skeleton with:

```bash
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001
```

Windows Python launcher form:

```bash
py -3.11 tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001
```

Current behavior:

- Loads a `ConfigBundle` from generated runtime JSON.
- Creates `BattleState` and twelve `UnitState` objects for `demo_001`.
- Spawns player units first as `ally_001..ally_006`, then enemy units as `enemy_001..enemy_006`.
- Emits deterministic `BattleEvent` ids such as `evt_000001`.
- Writes `runs/demo_001/replay.json` with `schema_version="battle_replay.v0.1"` and tick groups for tick `0` and tick `1200`.
- Writes `runs/demo_001/debug_timeline.json` as a flat event list.
- Writes `runs/demo_001/run_summary.md` with battle id, seed, unit count, event counts, and result.
- Ends with `winner="draw"` and `reason="timeout_no_combat"`.

Current limitations:

- No attack, damage, death, targeting AI, skill resolver, synergy application, formation bonus application, full battle report, HTML viewer, C# host, Godot gameplay, xlsx adapter, or third-party dependencies.

See `docs/process/deterministic-battle-skeleton-v0.1.md` for the runtime skeleton boundary.

## Test config tools

Run the standard-library unittest suite:

```bash
python -m unittest discover -s sim-python/tests
```

The tests export sample data into a temporary directory and validate both valid and invalid generated config.
They also verify deterministic battle skeleton unit creation, event counts, result payloads, tick grouping, and same-seed event stability.

## CSV-first note

Designer source format is still intended to be xlsx, and runtime format is still JSON.

Data Config v0.1/v0.1.3 uses CSV sample data first because it gives a dependency-free closed loop for schema, exporter, validator, and tests. This keeps Phase 1 moving without adding an xlsx parser before the data shape is stable.

TODO: add an xlsx adapter behind the same `tools/export_xlsx_to_json.py` command after the schema and validator stabilize.

## Structural verification

Use:

```bash
git status --short
```

Confirm that only intended source files are untracked or changed. Generated files under `config/generated/` are ignored except `.gitkeep`.

## Command flow

The current implemented local flow is:

```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
python tools/inspect_config_models.py --config config/generated
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001
```

C# host, HTML replay viewer, and full battle report commands are still future work.
