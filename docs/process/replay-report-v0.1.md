# Replay Report / 回放与战报 v0.1

This stage adds Replay Report / 回放与战报 output on top of Minimal Skill Triggers / 最小技能触发.

The goal is to write `battle_report.json / 战报 JSON` from the existing replay event stream / 回放事件流 without changing combat behavior / 战斗行为.

## Scope / 范围

Implemented:

- `battle_report.json / 战报 JSON`.
- Report generator / 战报生成器.
- Event-derived report / 基于事件生成战报.
- `damage_done / 输出伤害`.
- `damage_taken / 承受伤害`.
- `kills / 击杀`.
- `deaths / 死亡次数`.
- `skill_triggers / 技能触发次数`.
- Combat System Pack / 战斗系统包 counters: `statuses_applied`, `cooldowns_started`, `actions_taken`, and `victory_explanation`.
- `key_moments / 关键时刻`.
- `run_summary.md / 运行摘要` report totals / 战报汇总.

Not implemented:

- HTML viewer / Web 回放器.
- C# host / C# 宿主.
- Godot.
- Synergy application / 羁绊应用.
- Formation bonus application / 阵型加成应用.
- xlsx adapter / xlsx 适配器.
- Third-party dependencies / 第三方依赖.
- New combat rules / 新战斗规则.
- New skill effects / 新技能效果.
- Targeting AI / 目标选择 AI changes.
- Damage / 伤害 formula changes.
- Victory Check / 胜负判断 changes.

## Event-Derived Report / 基于事件生成战报

`build_battle_report(replay_doc, timeline_events)` consumes:

- `replay_doc.metadata / 回放元数据`
- `debug_timeline.json / 调试时间线` style flat event list / 扁平事件列表

The report generator / 战报生成器 does not read `BattleState / 战斗运行时状态`, `UnitState / 单位运行时状态`, or other unserialized Python internal state / 未序列化 Python 内部状态.

This keeps report generation reproducible from saved artifacts / 保存产物:

```text
replay.json + debug_timeline.json -> battle_report.json
```

## battle_report.json / 战报 JSON Schema

Current schema version / 当前 schema 版本:

```json
{
  "schema_version": "battle_report.v0.1",
  "battle_id": "demo_001",
  "seed": 1001,
  "winner": "ally",
  "reason": "enemy_eliminated",
  "end_tick": 260,
  "summary": {
    "total_damage": 1234,
    "total_kills": 9,
    "total_skill_triggers": 54,
    "total_status_applied": 4,
    "total_status_expired": 0,
    "total_skill_cooldowns": 54,
    "total_actions_scheduled": 80
  },
  "victory_explanation": {
    "winner": "ally",
    "reason": "enemy_eliminated",
    "end_tick": 260,
    "winner_alive": 3,
    "loser_alive": 0,
    "winner_total_hp": 286,
    "loser_total_hp": 0,
    "summary": "ally won by enemy_eliminated at tick 260"
  },
  "units": {
    "ally_001": {
      "damage_done": 120,
      "damage_taken": 40,
      "kills": 1,
      "deaths": 0,
      "skill_triggers": {
        "katana_slash": 3
      },
      "statuses_applied": 1,
      "cooldowns_started": 3,
      "actions_taken": 5,
      "last_next_action_tick": 280
    }
  },
  "top_units": {
    "damage_done": ["ally_001", "ally_003", "enemy_002"],
    "damage_taken": ["enemy_001", "ally_004", "enemy_003"],
    "skill_triggers": ["ally_006", "enemy_006"]
  },
  "key_moments": [
    {
      "tick": 120,
      "type": "death",
      "unit": "enemy_003",
      "killer": "ally_002",
      "summary": "enemy_003 was killed by ally_002"
    }
  ]
}
```

## Stat Rules / 统计规则

`damage_done / 输出伤害`:

- Sum `damage.payload.amount / 伤害数值` by `damage.payload.source / 伤害来源`.

`damage_taken / 承受伤害`:

- Sum `damage.payload.amount / 伤害数值` by `damage.payload.target / 伤害目标`.

`skill_triggers / 技能触发次数`:

- Count `skill_trigger / 技能触发事件` by source unit / 来源单位 and skill id / 技能 ID.

`statuses_applied / 状态应用次数`:

- Count `status_apply / 状态应用` by target unit / 目标单位.

`cooldowns_started / 冷却开始次数`:

- Count `skill_cooldown / 技能冷却` by source unit / 来源单位.

`actions_taken / 行动次数`:

- Count `action_scheduled / 行动排期` by acting unit / 行动单位 and keep `last_next_action_tick / 最后下一行动 tick`.

`top_units / 最高单位`:

- Sort by descending stat value / 统计值降序.
- Stable tie-break / 稳定决胜 uses unit id / 单位 ID ascending.
- Units with zero value / 零值单位 are omitted from top lists / 最高列表.

## Kill Attribution / 击杀归因

Kill attribution / 击杀归因 uses a simple last-damage rule / 最近伤害规则:

1. Maintain `last_damage_source_by_target / 目标最近伤害来源`.
2. Every `damage / 伤害` event updates `target -> source`.
3. When a `death / 死亡` event appears, the killer / 击杀者 is `last_damage_source_by_target[dead_unit]`.
4. If there is no known source / 无已知来源, killer / 击杀者 is `null`.
5. If killer / 击杀者 is `null`, no unit receives a `kills / 击杀` count.

Death key moments / 死亡关键时刻 include the killer / 击杀者:

```json
{
  "tick": 120,
  "type": "death",
  "unit": "enemy_003",
  "killer": "ally_002",
  "summary": "enemy_003 was killed by ally_002"
}
```

## Key Moments / 关键时刻

Current `key_moments / 关键时刻` include:

- `death / 死亡`
- `battle_end / 战斗结束`

The `battle_end / 战斗结束` key moment records winner / 胜者, reason / 原因, and end_tick / 结束 tick.

## Demo Command / 演示命令

```bash
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
```

Generated artifacts / 生成产物:

- `runs/demo_001/replay.json`
- `runs/demo_001/debug_timeline.json`
- `runs/demo_001/battle_report.json`
- `runs/demo_001/run_summary.md`

Skeleton compatibility mode / 骨架兼容模式 also writes `battle_report.json / 战报 JSON` with zero combat totals / 零战斗统计:

```bash
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001_skeleton --mode skeleton
```

## Verification / 验证

```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
python tools/inspect_config_models.py --config config/generated
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001_skeleton --mode skeleton
python -m unittest discover -s sim-python/tests
git diff --check
```
