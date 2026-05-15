# Basic Combat Rules / 基础战斗规则 v0.1

This stage adds the first Basic Combat Rules / 基础战斗规则 on top of the deterministic battle skeleton / 确定性战斗骨架.

The goal is to prove that a battle can progress through Targeting AI / 目标选择 AI, Basic Attack / 普通攻击, Damage / 伤害, Death / 死亡, and Victory Check / 胜负判断 while preserving deterministic replay output / 确定性回放输出.

## Scope

Implemented:

- Targeting AI / 目标选择 AI.
- Basic Attack / 普通攻击.
- Damage / 伤害.
- Death / 死亡.
- Victory Check / 胜负判断.
- Combat Events / 战斗事件: `attack`, `damage`, `death`.
- Basic mode / 基础战斗模式 for `tools/run_demo_battle.py`.

Not implemented:

- Skill resolver / 技能解析器.
- Synergy application / 羁绊应用.
- Formation bonus application / 阵型加成应用.
- Battle report / 战报.
- HTML viewer / Web 回放器.
- C# host / C# 宿主.
- Godot.
- xlsx adapter / xlsx 适配器.
- Third-party dependencies / 第三方依赖.

## Runtime Model Boundary / 运行时模型边界

`UnitDef / 单位配置定义` remains read-only config data loaded from generated runtime JSON / 运行时 JSON.

`UnitState / 单位运行时状态` is now a mutable battle instance / 可变战斗实例. Basic Combat Rules / 基础战斗规则 can update:

- `hp / 血量`
- `alive / 存活状态`
- `next_action_tick / 下次行动 tick`
- `action_interval_ticks / 行动间隔 tick`

`BattleState / 战斗运行时状态` still owns one battle run / 单场战斗运行, including current tick / 当前 tick, units / 单位, and result / 结果.

## Targeting AI / 目标选择 AI

`select_target(attacker, candidates)` chooses one alive enemy / 存活敌方单位 or returns `None`.

Rules:

- It only considers enemy alive units / 敌方存活单位.
- No movement / 不移动.
- It uses exposure layer / 暴露层 based on current alive enemy rows:
  - range 1 / 攻击范围 1: front exposed layer only / 只攻击最前暴露层.
  - range 2 / 攻击范围 2: front two exposed layers / 攻击最前两层.
  - range 3+ / 攻击范围 3 及以上: all exposed layers / 攻击全部层.
- Same column bonus / 同列加分.
- Adjacent column bonus / 邻列加分.
- Low HP bonus / 低血量加分.
- Stable tie-break / 稳定决胜顺序: score / 分数, hp_ratio / 血量比例, instance_id / 实例 ID.

## Basic Attack / 普通攻击

Each alive unit / 存活单位 receives an action schedule / 行动调度:

```text
action_interval_ticks = round(attack_interval * tick_rate)
```

The value is clamped to at least 1 tick / 至少 1 tick.

When `current_tick >= next_action_tick`, the unit can perform one Basic Attack / 普通攻击 if it has a target / 目标.

After acting:

```text
next_action_tick = current_tick + action_interval_ticks
```

## Damage / 伤害

Damage / 伤害 is intentionally simple:

```text
damage = max(1, attacker.base_atk - defender.base_defense)
```

No weapon effects / 武器效果, skills / 技能, synergies / 羁绊, or formation bonuses / 阵型加成 are applied.

## Death / 死亡

`apply_damage(defender, amount)` subtracts HP / 扣除血量.

If HP / 血量 reaches 0:

```text
defender.hp = 0
defender.alive = False
```

A `death / 死亡` event is emitted when a unit dies / 单位死亡.

## Victory Check / 胜负判断

After each Basic Attack / 普通攻击 and Death / 死亡 resolution, the runner checks both sides:

- If all enemy units / 敌方单位 are dead, winner / 胜者 is `ally`.
- If all ally units / 我方单位 are dead, winner / 胜者 is `enemy`.
- If both sides are dead, winner / 胜者 is `draw`.
- If max tick / 最大 tick is reached first, winner / 胜者 is `draw`, reason / 原因 is `timeout`.

## Events / 事件

Basic mode / 基础战斗模式 emits:

- `battle_start / 战斗开始`
- `unit_spawn / 单位生成`
- `attack / 攻击`
- `damage / 伤害`
- `death / 死亡`
- `battle_end / 战斗结束`

Event ids / 事件 ID remain deterministic and sequential:

```text
evt_000001
evt_000002
...
```

## Demo Command / 演示命令

```bash
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
```

Skeleton compatibility mode / 骨架兼容模式 remains available:

```bash
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode skeleton
```

Generated artifacts / 生成产物:

- `runs/demo_001/replay.json`
- `runs/demo_001/debug_timeline.json`
- `runs/demo_001/run_summary.md`

## Verification / 验证

```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
python tools/inspect_config_models.py --config config/generated
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
python -m unittest discover -s sim-python/tests
```

The tests cover Targeting AI / 目标选择 AI, Damage / 伤害, Death / 死亡, Basic Combat / 基础战斗, deterministic event streams / 确定性事件流, and the absence of future rule events / 未产生未来规则事件 such as skill or synergy events.
