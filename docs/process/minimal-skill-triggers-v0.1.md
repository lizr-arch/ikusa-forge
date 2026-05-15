# Minimal Skill Triggers / 最小技能触发 v0.1

This stage adds Minimal Skill Triggers / 最小技能触发 on top of Basic Combat Rules / 基础战斗规则.

The goal is to prove deterministic Skill Resolver / 技能解析器 behavior for sample skills / 示例技能 without introducing a general-purpose Skill DSL / 通用技能 DSL or final balance rules / 最终平衡规则.

## Scope / 范围

Implemented:

- Skill Resolver / 技能解析器 with a fixed handler map / 固定处理器映射.
- Skill Cooldown / 技能冷却.
- `on_battle_start / 战斗开始触发`.
- `on_attack / 攻击时触发`.
- `on_attacked / 被攻击时触发`.
- `on_ally_attacked / 友军被攻击时触发`.
- `skill_trigger event / 技能触发事件`.
- Damage reason / 伤害原因 in `damage / 伤害` events.
- Minimal stat mutation / 最小属性变化 through current `atk / 攻击`, `defense / 防御`, and `guard_value / 守护值`.

Not implemented:

- Synergy application / 羁绊应用.
- Formation bonus application / 阵型加成应用.
- Battle report / 战报.
- HTML viewer / Web 回放器.
- C# host / C# 宿主.
- Godot.
- xlsx adapter / xlsx 适配器.
- Third-party dependencies / 第三方依赖.
- General-purpose Skill DSL / 通用技能 DSL.

## Runtime Model / 运行时模型

`UnitDef / 单位配置定义` remains read-only config data / 只读配置数据.

`UnitState / 单位运行时状态` is the mutable runtime instance / 可变运行时实例. Minimal Skill Triggers / 最小技能触发 add:

- `skill_cooldowns / 技能冷却`: next ready tick / 下次可用 tick by skill id / 技能 ID.
- `atk / 当前攻击`: current battle attack / 当前战斗攻击值, initialized from `base_atk / 基础攻击`.
- `defense / 当前防御`: current battle defense / 当前战斗防御值, initialized from `base_defense / 基础防御`.
- `guard_value / 守护值`: simple MVP damage mitigation / MVP 伤害减免值.

`base_atk / 基础攻击` and `base_defense / 基础防御` keep original config values / 原始配置值.

Basic Attack / 普通攻击 and Skill Damage / 技能伤害 use current `atk / 当前攻击`, `defense / 当前防御`, and `guard_value / 守护值`.

## Skill Resolver / 技能解析器

The Skill Resolver / 技能解析器 reads `SkillDef / 技能配置定义` from `ConfigBundle / 只读配置集合` and checks `UnitState.skill_cooldowns / 单位技能冷却`.

Ready check / 可用检查:

```text
skill_cooldowns[skill_id] <= current_tick
```

When a skill is used / 技能使用后:

```text
skill_cooldowns[skill_id] = current_tick + round(skill.cooldown * tick_rate)
```

Cooldown ticks / 冷却 tick are clamped to at least 1 tick / 至少 1 tick through the same conversion used by action intervals / 行动间隔.

## Handler Map / 处理器映射

This stage uses a fixed handler map / 固定处理器映射, not a Skill DSL / 技能 DSL.

Supported sample skill handlers / 支持的示例技能处理器:

- `katana_slash / 刀击`: `on_attack / 攻击时触发`, damages current target / 对当前目标造成伤害.
- `iaijutsu_burst / 居合爆发`: `on_attack / 攻击时触发`, damages lowest HP enemy / 对最低血量敌人造成伤害.
- `spear_thrust / 枪刺`: `on_attack / 攻击时触发`, damages current target / 对当前目标造成伤害.
- `brace_counter / 枪阵反击`: `on_attacked / 被攻击时触发`, damages attacker / 对攻击者造成反击伤害.
- `bow_shot / 弓射`: `on_attack / 攻击时触发`, damages current target / 对当前目标造成伤害.
- `focus_fire / 集火`: `on_attack / 攻击时触发`, damages lowest HP enemy / 对最低血量敌人造成伤害.
- `shield_guard / 盾卫`: `on_battle_start / 战斗开始触发`, adds `guard_value / 守护值` to self / 自身.
- `intercept / 拦截`: `on_ally_attacked / 友军被攻击时触发`, damages attacker / 对攻击者造成伤害.
- `smoke_strike / 烟幕打击`: `on_attack / 攻击时触发`, damages current target / 对当前目标造成伤害.
- `banner_rally / 战旗鼓舞`: `on_battle_start / 战斗开始触发`, buffs adjacent allies' `atk / 当前攻击` / 增加相邻友军攻击.

These effects are MVP effects / MVP 效果 and do not represent final balance / 最终平衡.

## Trigger Order / 触发顺序

At tick 0 / 第 0 tick:

1. `battle_start / 战斗开始`.
2. `unit_spawn / 单位生成`.
3. `on_battle_start / 战斗开始触发` skills.

During an action / 行动:

1. The runner selects a target with Targeting AI / 目标选择 AI.
2. It tries one ready `on_attack / 攻击时触发` skill in unit skill order / 单位技能顺序.
3. If a skill action / 技能行动 is used, it emits `skill_trigger event / 技能触发事件` and `damage / 伤害`; it does not emit `attack / 攻击`.
4. If no skill is ready / 没有可用技能, it falls back to Basic Attack / 普通攻击 and emits `attack / 攻击`.
5. Damage / 伤害 may emit `damage / 伤害` and `death / 死亡`.
6. Main action damage / 主动行动伤害 can trigger `on_attacked / 被攻击时触发` and `on_ally_attacked / 友军被攻击时触发`.
7. Victory Check / 胜负判断 runs after the action / 行动结束后.

Reaction skills do not chain / 反应技能不递归触发. Counter damage / 反击伤害 and intercept damage / 拦截伤害 do not trigger another `on_attacked / 被攻击时触发` or `on_ally_attacked / 友军被攻击时触发` pass.

## Events / 事件

`attack event / 攻击事件` only represents Basic Attack / 普通攻击. A skill action / 技能行动 uses `skill_trigger event / 技能触发事件` and does not emit an extra `attack / 攻击` event.

For Basic Attack / 普通攻击, `attack.payload.target / 攻击事件目标` must match the following `damage.payload.target / 伤害事件目标` with `reason="basic_attack"`.

`skill_trigger event / 技能触发事件` payload / 事件载荷:

```json
{
  "source": "ally_001",
  "skill": "katana_slash",
  "trigger": "on_attack",
  "targets": ["enemy_001"]
}
```

`damage / 伤害` event payload / 事件载荷 includes `reason / 伤害原因`:

```json
{
  "source": "ally_001",
  "target": "enemy_001",
  "amount": 12,
  "target_hp_after": 34,
  "reason": "skill:katana_slash"
}
```

Basic Attack / 普通攻击 uses:

```text
reason = "basic_attack"
```

Skill Damage / 技能伤害 uses:

```text
reason = "skill:<skill_id>"
```

`battle_end / 战斗结束` payload / 事件载荷 still uses the top-level result contract / 顶层结果契约:

```json
{
  "winner": "ally",
  "reason": "enemy_eliminated",
  "end_tick": 300
}
```

Replay metadata / 回放元数据 still keeps `metadata.result / 元数据结果`.

## Demo Command / 演示命令

```bash
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
```

Skeleton compatibility mode / 骨架兼容模式 remains available and does not run skills / 不运行技能:

```bash
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001_skeleton --mode skeleton
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
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001_skeleton --mode skeleton
python -m unittest discover -s sim-python/tests
git diff --check
```
