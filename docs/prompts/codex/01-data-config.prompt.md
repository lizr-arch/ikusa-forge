# Codex Prompt: Data Config v0.1

You are working in the `ikusa-forge` repository.

Goal: implement the first data config pipeline.

Read:

- `AGENTS.md`
- `docs/design/05-data-config-design.md`
- `docs/design/02-mvp-scope-v0.1.md`
- `docs/process/01-phase-1-task-board.md`

Implement:

```text
tools/export_xlsx_to_json.py
tools/validate_config.py
config/source/sample_data/*.csv or generated sample xlsx if practical
config/generated/.gitkeep
docs/schema/units.schema.json
docs/schema/weapons.schema.json
docs/schema/skills.schema.json
docs/schema/formations.schema.json
docs/schema/synergies.schema.json
docs/schema/encounters.schema.json
docs/schema/constants.schema.json
```

Important:

- If xlsx dependency is too much for the first pass, support CSV first and document the xlsx follow-up.
- Runtime output must be JSON.
- Validator must catch duplicate ids, missing references, and invalid numeric values.
- Keep error messages readable.

Commands should be documented in `docs/process/local-dev-setup.md`.

Expected commands:

```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
```

Add tests if practical:

```text
sim-python/tests/test_config_validation.py
```

Completion report must include:

- changed files
- command output
- sample generated JSON paths
- validator behavior
- known limitations
