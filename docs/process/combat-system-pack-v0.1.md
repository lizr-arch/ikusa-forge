# Combat System Pack / 战斗系统包 v0.1

## Goal / 目标

Combat System Pack / 战斗系统包 v0.1 extends the existing deterministic combat lab with explainability events and report/viewer visibility. It does not change damage formulas, targeting rules, skill success rules, config schema, or the web framework.

The goal is to make these runtime mechanics visible from saved artifacts:

- Status Effect Lifecycle / 状态效果生命周期
- Skill Cooldown Explainability / 技能冷却可解释性
- Action Timeline / 行动时间线
- Victory Explanation / 胜负解释

## Status Effect Lifecycle / 状态效果生命周期

Runtime model:

- `StatusEffect / 状态效果`: stored on `UnitState.statuses`
- Fields: `id`, `source`, `source_type`, `target`, `stat`, `amount`, `start_tick`, `expire_tick`, `reason`

Replay event:

- `status_apply / 状态应用`
- `status_expire / 状态过期` is part of the contract, but current permanent sample statuses do not force an expire event.

Current sample skills:

- `shield_guard`: keeps its existing `guard_value` behavior and emits `status_apply` with `stat=guard_value`, `reason=skill:shield_guard`, `target_reason=self`.
- `banner_rally`: keeps its existing adjacent ally `atk` bonus behavior and emits one `status_apply` per affected target with `stat=atk`, `reason=skill:banner_rally`, `target_reason=adjacent_allies`.

No general-purpose Skill DSL / 通用技能 DSL is introduced.

## Skill Cooldown Explainability / 技能冷却可解释性

Every successful skill use that enters cooldown emits:

```json
{
  "type": "skill_cooldown",
  "payload": {
    "source": "ally_003",
    "skill": "katana_slash",
    "start_tick": 20,
    "ready_tick": 40,
    "cooldown_ticks": 20
  }
}
```

This event is emitted after the skill's existing effects resolve. It explains cooldown timing but does not change cooldown behavior.

## Action Timeline / 行动时间线

After a unit actually acts and receives its next action tick, the simulator emits:

```json
{
  "type": "action_scheduled",
  "payload": {
    "unit": "ally_003",
    "current_tick": 20,
    "next_action_tick": 40,
    "action_interval_ticks": 20,
    "reason": "after_action"
  }
}
```

This is intentionally not a new `action_ready` event. The minimum explainability contract is "after this action, when will the unit act again?"

## Victory Explanation / 胜负解释

`battle_end` keeps the stable Phase 1 fields:

- `winner`
- `reason`
- `end_tick`

It now also includes:

- `winner_alive`
- `loser_alive`
- `winner_total_hp`
- `loser_total_hp`
- `summary`

The report derives `victory_explanation / 胜负解释` from the saved `battle_end` event. The report generator still reads events only; it does not inspect live runtime state.

## Replay/Report/Viewer Contract / 回放、战报、回放器契约

Replay contract additions:

- `status_apply`
- `status_expire`
- `skill_cooldown`
- `action_scheduled`
- extended `battle_end` payload

Report summary additions:

- `total_status_applied`
- `total_status_expired`
- `total_skill_cooldowns`
- `total_actions_scheduled`

Report unit additions:

- `statuses_applied`
- `statuses_expired`
- `cooldowns_started`
- `actions_taken`
- `last_next_action_tick`

Viewer additions:

- timeline filters for `status_apply`, `skill_cooldown`, and `action_scheduled`
- event highlight rows for status/cooldown/action schedule payloads
- unit detail rows for active statuses, next action tick, last cooldown, and last action schedule
- report rows for new summary counters and `victory_explanation`

Demo One-Click and Scenarios / 一键 Demo 与多场景 consumes the same contract through committed Curated Fixtures / 固化样例数据 under `web-viewer/public/samples`. Scenario Manifest / 场景清单 points the viewer at replay/report pairs, and Scenario Selector / 场景选择器 loads them without changing simulator behavior.

Live Combat Runtime Foundation / 实时战斗运行时基础 keeps the same event contract while moving the basic loop behind BattleSession / 战斗会话, Step Runtime / 单步运行时, Battle Snapshot / 战斗状态快照, and Event Buffer / 事件缓冲 APIs. `run_basic_combat` remains the one-shot compatibility entry for replay/report/viewer generation.

## Determinism / 确定性

All new events use the existing sequential `event_id` allocator. With the same config files, battle setup, and seed, the replay and report remain deterministic.

Current `demo_001 / seed=1001` expected key totals:

- events: `332`
- winner: `ally`
- reason: `enemy_eliminated`
- end_tick: `240`
- total_damage: `1189`
- total_kills: `9`
- total_skill_triggers: `48`
- total_modifiers: `16`
- total_status_applied: `4`
- total_status_expired: `0`
- total_skill_cooldowns: `48`
- total_actions_scheduled: `75`
- winner_alive: `3`
- loser_alive: `0`
- winner_total_hp: `286`
- loser_total_hp: `0`

## Not in Scope / 不在范围

- No full Godot gameplay / 不做完整 Godot 玩法
- No C# embedding of Python / 不嵌入 Python.NET
- No networked PvP / 不做联网 PvP
- No save system / 不做存档
- No large content production / 不做大规模内容生产
- No xlsx runtime reads / 模拟器运行时不直接读 xlsx
- No combat formula changes / 不改伤害公式
- No targeting behavior changes / 不改目标选择行为
- No general Skill DSL / 不做通用技能 DSL
- No HTTP server / 不做 HTTP server
- No HTML live mode / 不做 HTML 实时模式

## Verification / 验证

Run the full local chain:

```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
python tools/smoke_phase1_mvp.py --run runs/demo_001 --viewer web-viewer --battle demo_001 --seed 1001
python tools/generate_demo_scenarios.py --source config/source --out web-viewer/public/samples --battle demo_001 --seeds 1001 1002 1003
python tools/smoke_demo_scenarios.py --samples web-viewer/public/samples
python -m unittest discover -s sim-python/tests

cd web-viewer
npm install
npm run typecheck
npm run build
npm run test:e2e
```
