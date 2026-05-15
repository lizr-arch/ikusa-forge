# Deterministic Battle Skeleton v0.1.1

This stage adds the first deterministic battle runtime skeleton / 确定性战斗运行时骨架.

It proves that the same config files / 配置文件, battle setup / 战斗配置, and seed / 随机种子 produce the same replay event stream / 回放事件流. It does not implement full combat rules / 完整战斗规则.

## Scope

Implemented:

- `UnitState / 单位运行时状态`: a single runtime unit instance created from `UnitDef / 单位配置定义` plus encounter placement / 遭遇战站位 and formation role / 阵型角色.
- `BattleState / 战斗运行时状态`: one battle run's mutable runtime state, including `battle_id`, `seed`, tick settings / tick 参数, units / 单位列表, finished flag / 结束标记, and result / 结果.
- `BattleResult / 战斗结果`: current skeleton result is always `winner="draw"` and `reason="timeout_no_combat"`.
- `BattleEvent / 战斗事件`: structured events with `tick`, deterministic `event_id`, `type`, and `payload`.
- `BattleRng / 战斗随机包装器`: battle-scoped wrapper around `random.Random(seed)`. The skeleton instantiates it but does not consume random values yet.
- `run_battle_skeleton() / 运行战斗骨架`: emits `battle_start`, `unit_spawn`, and `battle_end`.
- `tools/run_demo_battle.py`: writes replay / 回放, debug timeline / 调试时间线, and run summary / 运行摘要 artifacts.
- Module split / 模块拆分:
  - `runtime_models.py / 运行时模型`
  - `events.py / 战斗事件`
  - `rng.py / 随机包装器`
  - `battle_skeleton.py / 战斗骨架`
  - `battle.py / 兼容转发层`

Not implemented:

- Attack / 攻击.
- Damage / 伤害.
- Death / 死亡.
- Targeting AI / 目标选择 AI.
- Skill resolver / 技能解析器.
- Synergy application / 羁绊应用.
- Formation bonus application / 阵型加成应用.
- Full battle report / 战报.
- HTML viewer / Web 回放器.
- C# host / C# 宿主.
- Godot gameplay / Godot 玩法.
- xlsx adapter / xlsx 适配器.
- Third-party dependencies / 第三方依赖.

## Runtime Model Boundary

`UnitDef / 单位配置定义` is read-only config data loaded from runtime JSON. It describes reusable unit identity and base numbers such as `hp`, `atk`, `defense`, `range`, `attack_interval`, `weapon_slots`, and `skill_ids`.

`UnitState / 单位运行时状态` is a per-battle unit instance. It contains `instance_id`, `side`, `unit_def_id`, board position / 棋盘坐标, `role`, copied base attributes / 基础属性, current `hp`, and `alive`. It is the place future combat logic can mutate HP / 血量 or alive state / 存活状态.

`ConfigBundle / 只读配置集合` is the loaded collection of generated runtime config tables. It does not track a battle run.

`BattleState / 战斗运行时状态` is the state for one battle run. It references the chosen `battle_id` and seed / 随机种子, contains runtime units / 运行时单位, and records the final `BattleResult / 战斗结果`.

`BattleEvent / 战斗事件` is the replay-facing event contract. It is data-only and can be serialized into `replay.json / 回放 JSON` or `debug_timeline.json / 调试时间线 JSON`.

Runtime side enum / 运行时阵营枚举 uses `ally/enemy`.

`config.encounters[].player_units / 配置字段 player_units` remains the designer-facing config field. During runtime state creation it becomes `UnitState.side="ally" / 我方阵营`.

`config.encounters[].enemy_units / 配置字段 enemy_units` becomes `UnitState.side="enemy" / 敌方阵营`.

The dependency direction stays:

```text
config -> simulator -> replay/report -> viewer/host
```

The simulator does not import the web viewer / Web 回放器, Godot scene / Godot 场景, or C# UI / C# 界面.

## Module Boundary

`runtime_models.py / 运行时模型` owns runtime dataclasses:

- `UnitState / 单位运行时状态`
- `BattleState / 战斗运行时状态`
- `BattleResult / 战斗结果`

`events.py / 战斗事件` owns event data and grouping:

- `BattleEvent / 战斗事件`
- `event_to_dict`
- `events_to_tick_groups`

`rng.py / 随机包装器` owns:

- `BattleRng / 战斗随机包装器`

`battle_skeleton.py / 战斗骨架` owns runtime orchestration and serialization:

- `create_battle_state`
- `spawn_units_from_encounter`
- `run_battle_skeleton`
- `build_replay_document`
- `battle_state_to_dict`
- `unit_state_to_dict`
- `battle_result_to_dict`

`battle.py / 兼容转发层` is a compatibility facade. New code should prefer importing from `runtime_models.py / 运行时模型`, `events.py / 战斗事件`, `rng.py / 随机包装器`, and `battle_skeleton.py / 战斗骨架`.

## Event Stream

The skeleton emits deterministic event ids / 确定性事件编号 in run order:

```text
evt_000001
evt_000002
...
```

For `demo_001 / 演示战斗 001`:

- tick `0`: one `battle_start / 战斗开始` event.
- tick `0`: twelve `unit_spawn / 单位生成` events.
- tick `1200`: one `battle_end / 战斗结束` event.

Config `player_units / 玩家单位配置字段` are spawned first as `ally_001` through `ally_006` with runtime side / 运行时阵营 `ally / 我方`.
Config `enemy_units / 敌方单位配置字段` are spawned second as `enemy_001` through `enemy_006` with runtime side / 运行时阵营 `enemy / 敌方`.

The result / 结果 is always:

```json
{
  "winner": "draw",
  "reason": "timeout_no_combat",
  "end_tick": 1200
}
```

The `battle_end / 战斗结束` event payload / 事件载荷 uses that same top-level shape:

```json
{
  "winner": "draw",
  "reason": "timeout_no_combat",
  "end_tick": 1200
}
```

Replay metadata / 回放元数据 still keeps `metadata.result / 元数据结果` as the same result object.

## Demo Command

Export and validate config first:

```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
python tools/inspect_config_models.py --config config/generated
```

Run the deterministic battle skeleton / 确定性战斗骨架:

```bash
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001
```

Windows Python launcher form:

```bash
py -3.11 tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001
```

Generated artifacts / 生成产物:

- `runs/demo_001/replay.json`: grouped replay document / 分组回放文档 with `schema_version="battle_replay.v0.1"`.
- `runs/demo_001/debug_timeline.json`: flat event list / 扁平事件列表.
- `runs/demo_001/run_summary.md`: human-readable run summary / 人类可读运行摘要.

## Verification

Use:

```bash
python -m unittest discover -s sim-python/tests
```

The tests assert:

- `demo_001` creates twelve `UnitState / 单位运行时状态` objects.
- `ally_001` and `enemy_001` exist.
- runtime side enum / 运行时阵营枚举 is `ally/enemy`.
- every `UnitState.role / 单位运行时角色` is non-empty.
- the event stream contains one `battle_start`, twelve `unit_spawn`, and one `battle_end`.
- the final result is draw / 平局 because of timeout without combat / 无战斗超时.
- the same `ConfigBundle / 只读配置集合`, battle id / 战斗 id, and seed / 随机种子 emit identical event dictionaries.
- replay metadata / 回放元数据 records the passed seed.

## Next Step

The next phase should be `phase1/basic-combat-rules`: add minimal target selection / 目标选择, attack cadence / 攻击节奏, damage / 伤害, death / 死亡, and a first battle report / 初版战报 while preserving deterministic replay output.
