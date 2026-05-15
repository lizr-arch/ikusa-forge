# Data Config Design v0.1

## Principle

xlsx is for designers.
JSON is for runtime.

The simulator, C# host, HTML viewer, and future Godot client should read JSON, not xlsx.

## Source tables

```text
config/source/
  units.xlsx
  weapons.xlsx
  skills.xlsx
  formations.xlsx
  synergies.xlsx
  encounters.xlsx
  constants.xlsx
```

## Generated runtime files

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

## units.xlsx

| Field | Type | Example |
|---|---|---|
| id | string | ashigaru_spear |
| name | string | 足轻枪兵 |
| tags | csv string | ashigaru,spear,frontline |
| hp | int | 120 |
| atk | int | 14 |
| defense | int | 5 |
| range | int | 1 |
| attack_interval | float | 1.2 |
| weapon_slots | csv string | spear |
| skill_ids | csv string | brace_counter |

## weapons.xlsx

| Field | Type | Example |
|---|---|---|
| id | string | spear_basic |
| name | string | 竹枪 |
| type | enum | spear |
| damage_type | enum | pierce |
| range | int | 2 |
| cooldown | float | 1.4 |
| skill_ids | csv string | spear_thrust |

## skills.xlsx

| Field | Type | Example |
|---|---|---|
| id | string | brace_counter |
| name | string | 枪阵反击 |
| trigger | enum | on_attacked |
| target_rule | enum | attacker |
| cooldown | float | 3.0 |
| effect_type | enum | damage |
| effect_value | int | 20 |
| tags | csv string | spear,counter |

## formations.xlsx

| Field | Type | Example |
|---|---|---|
| id | string | fish_scale |
| name | string | 鱼鳞 |
| pattern | string/json | center_front |
| bonus_rule | string | center_units_atk_plus_10 |

### Formation slot semantics

In Data Config v0.1.3, `formation.pattern.slots` defines the legal positions and role regions for that formation.

- Each slot coordinate uses the side-local 4x3 board: `x` is `0..3`, and `y` is `0..2`.
- Each slot must include a non-empty string `role` value so later simulator logic can map a unit coordinate to a formation role.
- When an encounter uses a formation, every unit coordinate on that side must be inside that formation's `pattern.slots`.
- Later simulator work can safely look up the unit coordinate in the selected formation, read the slot role, and apply formation bonuses from `bonus_rule`.

## synergies.xlsx

| Field | Type | Example |
|---|---|---|
| id | string | spear_wall |
| name | string | 枪阵 |
| required_tags | csv string | spear |
| thresholds | json | {"2":{"defense":3},"4":{"defense":8}} |
| scope | enum | matching_units |

## encounters.xlsx

| Field | Type | Example |
|---|---|---|
| id | string | demo_001 |
| enemy_units | json | [...] |
| enemy_formation | string | fish_scale |
| reward_pool | csv string | basic_rewards |

## constants.xlsx

| Field | Type | Example |
|---|---|---|
| key | string | tick_rate |
| value | number/string | 20 |
| description | string | simulation ticks per second |

## Validator rules

The validator must catch:

- duplicate ids
- missing referenced ids
- negative hp / cooldown / range
- unknown tags where strict tag list is enabled
- invalid formation coordinates
- missing or empty formation slot roles
- encounter unit coordinates not present in the selected formation slots
- invalid JSON cells
- empty required fields
