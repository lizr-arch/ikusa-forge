# Local Development Setup

This repository is currently in Phase 1 Data Config v0.1.3 state.

The scaffold and first config pipeline exist so later tasks can add a deterministic Python simulator, a C# subprocess host, and an HTML replay debugger without mixing responsibilities.

## Expected local tools

- Project target: Python >= 3.10.
- Recommended Python: 3.11 or newer.
- Current scripts may still run on Python 3.6 for this machine's local compatibility, but that is not a long-term project constraint.
- .NET SDK for the future C# host.
- A modern browser for the future HTML replay debugger.

No heavy dependencies are required for the current CSV-first config pipeline.

## Repository layout

```text
config/source/      Designer-editable source data and CSV sample data.
config/generated/   Runtime JSON output; generated files are ignored.
sim-python/         Future pure Python combat simulator package and tests.
host-csharp/        Future C# host that invokes Python as a subprocess.
web-viewer/         Future local HTML replay debugger.
tools/              Future export, validation, and demo-run scripts.
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

## Test config tools

Run the standard-library unittest suite:

```bash
python -m unittest discover -s sim-python/tests
```

The tests export sample data into a temporary directory and validate both valid and invalid generated config.

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

## Later command flow

The intended full Phase 1 flow is documented in `README.md`. Data export and validation are implemented; battle simulation and host commands are still future work:

```bash
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --out runs/demo_001
dotnet run --project host-csharp/IkusaForge.Host -- --battle demo_001 --seed 1001
```

Do not treat the battle or C# host commands as runnable until the corresponding Phase 1 tasks are implemented.
