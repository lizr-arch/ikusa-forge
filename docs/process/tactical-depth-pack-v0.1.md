# Tactical Depth Pack / 战术深度包

## Goal / 目标

让阵型加成与羁绊应用真正参与模拟，并在输出链路中保持可解释性。  
Tactical Depth Pack / 战术深度包 让 `formation bonus / 阵型加成` 与 `synergy application / 羁绊应用` 变成可观察的战斗行为差异，同时把变化写进 replay / 战报合同。

## Formation Bonus / 阵型加成

通过 `formation_id` 分组单位并在 tick 0 统一应用基础加成。  
Handler map currently includes:

- `fish_scale / 鱼鳞` → vanguard / flank-center 攻击加成（`atk + 3`）
- `crane_wing / 鹤翼` → 左右翼 flank 攻击加成（`atk + 2`）与支援位轻加成（`atk + 1`）
- `goose_line / 雁行` → 后排防御加成（`defense + 2`）

每次加成会产出 `stat_modifier / 属性修正事件`，并按实例顺序写入事件流。

## Synergy Application / 羁绊应用

按 side 分开统计标签命中后，若满足阈值就触发修正并写入事件：

- `spear_wall / 枪墙` → spear 单位攻击加成
- `arrow_volley / 箭雨` → bow 单位攻击加成
- `blade_dance / 刀舞`（兼容 `duelist_honor`） → katana 单位攻击加成
- `shadow_pair / 影双` → ninja/ninja_tool 单位加成
- `banner_core / 战旗核心` → 全体与旗手相关条件加成
- `mixed_arms / 兵种混编` → 全体防御加成

### Combat Modifier / 战斗修正

修正事件统一落到统一事件类型：

- `type: stat_modifier`
- `source_type: formation|synergy`
- `stat / 属性`: `atk` / `defense` / `range`
- `amount / 数值`
- `reason / 来源原因`

## Triggered Modifier Event / 修正触发事件

最小统一载荷示例：

```json
{
  "type": "stat_modifier",
  "payload": {
    "source": "formation:fish_scale",
    "source_type": "formation",
    "target": "ally_002",
    "stat": "atk",
    "amount": 3,
    "reason": "fish_scale:vanguard_center_atk_plus_3"
  }
}
```

或

```json
{
  "type": "stat_modifier",
  "payload": {
    "source": "synergy:spear_wall",
    "source_type": "synergy",
    "target": "ally_001",
    "stat": "atk",
    "amount": 2,
    "reason": "spear_wall:threshold_2"
  }
}
```

## Report/Viewer Explainability / 报表与回放器可解释性

`battle_report.json / 战报` 会统计：

- `summary.total_modifiers / 总修正数`
- `summary.formation_modifiers / 阵型修正数`
- `summary.synergy_modifiers / 群体修正数`
- 每个单位 `stat_bonuses / 属性加成` 与 `modifiers_received / 修正命中次数`

`SVG Replay Viewer / SVG 回放调试器` 会渲染：

- `stat_modifier / 属性修正` 时间线过滤
- 当前事件的 `source/target/stat/amount/reason` 高亮与文本
- 战报页总计与 per-unit 修正汇总
- 战报点击单位联动到棋盘
- 关键时刻可导航到触发时刻

## Not in Scope / 不在范围

- No C# host / 不做 C# 宿主（仅留现有契约兼容）
- No Godot shell / 不做 Godot 外壳
- No xlsx adapter / 不做 xlsx adapter
- No general-purpose DSL / 不做通用战斗修正 DSL
- No complex animation system / 不做复杂动画系统
- No visual regression suite / 不做视觉回归矩阵

## Demo Verification / 演示验证

- `python tools/export_xlsx_to_json.py --input config/source --output config/generated`
- `python tools/validate_config.py --input config/generated`
- `python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic`
- `python tools/smoke_phase1_mvp.py --run runs/demo_001 --viewer web-viewer --battle demo_001 --seed 1001`
- `python -m unittest discover -s sim-python/tests`
- `cd web-viewer && npm install && npm run typecheck && npm run build && npm run test:e2e`

预期关键变化（`demo_001 / seed 1001`）：

- `events / 事件数`: `184`
- `end_tick / 结束 tick`: `216`
- `total_modifiers / 总修正`: `8`
- `formation_modifiers / 阵型修正`: `4`
- `synergy_modifiers / 群体修正`: `4`
- `total_damage / 总伤害`: `1088`
- `total_kills / 总击杀`: `8`
- `total_skill_triggers / 总技能触发`: `44`

## Known Limits / 已知限制

- 离散 tick/event 播放，不是平滑动画
- 无视觉回归 / 无 visual regression
- 无跨浏览器浏览器矩阵 / no cross-browser matrix
- 无 C# host / 无 C# 宿主
- 无 Godot
