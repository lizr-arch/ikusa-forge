# Python Combat Models v0.1

This stage introduces the first Python combat-core boundary: generated config
JSON can be loaded into pure dataclasses and queried for formation roles.

It does not implement a battle loop.

## Scope

Implemented:

- Pure config dataclasses in `sim-python/ikusa_sim/models.py`.
- Runtime JSON loader in `sim-python/ikusa_sim/config_loader.py`.
- Validation-before-load by reusing `tools/validate_config.py`.
- Formation coordinate-to-role lookup in `sim-python/ikusa_sim/formation.py`.
- Inspection CLI in `tools/inspect_config_models.py`.

Not implemented:

- UnitState or BattleState.
- Tick loop.
- Attack, damage, death, targeting, skill, synergy, replay, or report logic.
- C# host, HTML viewer, Godot, xlsx adapter, or third-party dependencies.

## ConfigBundle

`load_config(config_dir)` reads only generated runtime JSON:

```text
config/generated/
  units.json
  weapons.json
  skills.json
  formations.json
  synergies.json
  encounters.json
  constants.json
```

It returns a `ConfigBundle` with:

- `constants`
- `units`
- `weapons`
- `skills`
- `formations`
- `synergies`
- `encounters`

Definition tables are indexed by id for safe downstream lookup. The models
mirror config data and intentionally do not track mutable combat state.

The project target remains Python >= 3.10. The current model code uses
conservative `typing` annotations so this machine's bare `python` command can
still run the validation and inspection commands during the transition.

## Formation Role Lookup

Data Config v0.1.3 guarantees every formation slot has a non-empty `role` and
that encounter unit coordinates are inside the selected formation slots.

The simulator can therefore rely on:

```text
unit coordinate -> formation slot -> role
```

`get_slot_role(formation, x, y)` returns the slot role or raises a clear
`FormationLookupError` if the coordinate is absent. This stage does not apply or
interpret `bonus_rule`.

## Inspect Config Models

After exporting and validating config, inspect loaded models with:

```bash
python tools/inspect_config_models.py --config config/generated
```

Windows Python launcher form:

```bash
py -3.11 tools/inspect_config_models.py --config config/generated
```

The command prints config table counts, constants, board size, and the role
lookup for `demo_001` player and enemy units.

## Next Stage

The next stage should be a deterministic battle skeleton:

- load `ConfigBundle`
- create explicit runtime state types
- run a minimal tick loop
- emit deterministic structural output

It should still avoid implementing the full skill system in one step.
