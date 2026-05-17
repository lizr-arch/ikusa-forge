# Combat Behavior Pack / 战斗行为包

## Goal / 目标

让每一次攻击/技能选择都能解释“为什么这么做”。
核心目标是把目标决策从“会发生”变成“可验证的行为证据”：

- 为什么选这个目标？
- 为什么对这个目标放技能？
- 哪些目标优先规则导致了当前结论？

## Targeting AI v0.2 / 目标选择 AI v0.2

`sim-python/ikusa_sim/targeting.py` 使用固定评分规则返回：

- `exposure_score / 暴露层评分`
- `column_score / 同列评分`
- `low_hp_score / 低血量评分`
- `threat_score / 威胁评分`
- `role_score / 职责偏好评分`
- `tie_break / 平分规则`

决策包含：

- `target / 目标单位`
- `reason / 目标原因`
- `score / 目标评分`
- `candidates / 候选列表（内部调试信息，非完整写入 replay）`

规则说明（固定 handler，不引入通用 AI DSL）：

- 同层优先：`_filter_by_exposure` 仍先限制攻击者可见图层
- 同列优先：`column` 与 `exposure` 的正向权重保留，`final` 是各评分之和
- 威胁加权：`threat_score = atk + range*4 + 技能/支援微量加分`
- 角色偏好：基于攻击者属性（前排/后排/侧翼等）给不同目标角色加权
- 确定性平分：`final desc -> hp_ratio asc -> instance_id asc`

## Skill Target Reason / 技能目标原因

`skill_trigger` 事件新增 `target_reason`。

当前映射：

- `current_target / 当前目标`：沿用当前攻击目标，附带 `target_score`
- `lowest_hp_enemy / 最低血量敌人`：非当前目标技能，记录原因
- `self / self`、`adjacent_allies / adjacent allies`：按技能定义原因透传

示例：

```json
{
  "type": "attack",
  "payload": {
    "attacker": "ally_003",
    "target": "enemy_004",
    "target_reason": "frontline_exposed_same_column",
    "target_score": {
      "final": 42,
      "exposure": 20,
      "column": 10,
      "low_hp": 3,
      "threat": 7,
      "role": 2,
      "tie_break": 0
    }
  }
}
```

```json
{
  "type": "skill_trigger",
  "payload": {
    "source": "ally_003",
    "skill": "iaijutsu_burst",
    "trigger": "on_attack",
    "targets": ["enemy_004"],
    "target_reason": "lowest_hp_enemy"
  }
}
```

## Replay/Report/Viewer Explainability / 回放、战报、回放器可解释性

当前实现通过以下链路展示可解释性：

- 回放事件：
  - `attack`：追加 `target_reason` + `target_score`
  - `skill_trigger`：追加 `target_reason` + optional `target_score`
- 战报：
  - `summary.target_reason_counts / 目标原因统计`
  - `summary.skill_target_reason_counts / 技能目标原因统计`
- 回放器：
  - 时间线高亮显示 `Target Reason / 目标原因` 与 `Target Score / 目标评分`
  - 战报面板显示目标原因统计摘要
  - 单位详情显示最近目标原因/评分标记

示例事件聚合（来自真实 demo）用于审查：

- `summary.target_reason_counts`：包含非空目标原因
- `summary.skill_target_reason_counts`：包含非空技能目标原因
- `target_score.final`：可在 attack / skill 中查看关键打分来源

## Not in Scope / 不在范围

- 不做移动 / 不做寻路（移动与寻路 remains out of scope）
- 不做 C# 宿主 / 不做 C# host
- 不做 Godot
- 不做 xlsx adapter / 不做 xlsx 适配器
- 不做通用 AI DSL / 不做通用 AI DSL
- 不做通用技能 DSL / 不做通用技能 DSL
- 不改浏览器端能力边界（保留 HTML demo 只读能力）

## Verification / 验证

与本阶段一致的本地命令（与 CI 对齐）：

```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
python tools/smoke_phase1_mvp.py --run runs/demo_001 --viewer web-viewer --battle demo_001 --seed 1001
python -m unittest discover -s sim-python/tests
cd web-viewer
npm install
npm run typecheck
npm run build
npm run test:e2e
```

## Demo delta / 当前阶段与前序基线差异

在同配置 `demo_001 / seed=1001` 下，当前预期变化链路已收敛（见 `tactical-depth-pack-v0.1.md` 与 `phase-1-summary.md`）：

- events / 事件数：`205`
- end_tick / 结束 tick：`240`
- total_damage / 总伤害：`1189`
- total_kills / 总击杀：`9`
- total_skill_triggers / 总技能触发：`48`
- total_modifiers / 总修正数：`16`
- formation_modifiers / 阵型修正：`8`
- synergy_modifiers / 羁绊修正：`8`
