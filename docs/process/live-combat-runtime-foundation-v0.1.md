# Live Combat Runtime Foundation / 实时战斗运行时基础 v0.1

## Goal / 目标

Live Combat Runtime Foundation / 实时战斗运行时基础 turns the existing one-shot `run_basic_combat()` loop into a step-capable BattleSession / 战斗会话.

The goal is to make the combat core portable beyond replay generation:

- Step Runtime / 单步运行时 for advancing a battle by ticks.
- Battle Snapshot / 战斗状态快照 for reading JSON-safe runtime state.
- Event Buffer / 事件缓冲 for reading new events since a known integer cursor.
- Runtime Contract / 运行时契约 that keeps replay/report/viewer behavior compatible.

This phase is a runtime shape refactor. It does not add combat rules, skills, AI, movement, HTTP serving, C# host, Godot, or HTML live mode.

## Runtime Contract / 运行时契约

The new module is:

```text
sim-python/ikusa_sim/battle_session.py
```

### BattleSession / 战斗会话

BattleSession / 战斗会话 stores the running battle:

- `config`: loaded `ConfigBundle / 配置集合`
- `state`: mutable `BattleState / 战斗状态`
- `battle_id`: encounter id
- `seed`: deterministic seed
- `initialized`: whether tick 0 setup has run
- `finished`: whether a result exists
- `current_tick`: current runtime tick
- `events`: accumulated `BattleEvent / 战斗事件`
- `event_cursor`: optional caller cursor storage
- `max_ticks`: battle max tick

### Step Runtime / 单步运行时

Public APIs:

```python
create_battle_session(config, battle_id, seed)
initialize_battle_session(session)
step_battle_session(session, ticks=1)
step_until_finished(session)
```

Flow:

1. `create_battle_session / 创建战斗会话` validates the battle id and creates empty runtime state. It does not emit events.
2. `initialize_battle_session / 初始化战斗会话` emits tick 0 setup events: `battle_start`, `unit_spawn`, `stat_modifier`, `status_apply`, and `skill_cooldown` where current demo rules produce them.
3. `step_battle_session / 单步推进` advances at most `ticks` ticks and returns only events produced during that call.
4. `step_until_finished / 推进到结束` repeatedly steps until `battle_end` exists.

If a BattleSession / 战斗会话 is already finished, `step_battle_session / 单步推进` returns an empty list and does not emit a second `battle_end`.

### Battle Snapshot / 战斗状态快照

`build_battle_snapshot(session)` returns JSON-safe data:

```json
{
  "schema_version": "battle_snapshot.v0.1",
  "battle_id": "demo_001",
  "seed": 1001,
  "tick": 20,
  "finished": false,
  "result": null,
  "units": [
    {
      "instance_id": "ally_001",
      "side": "ally",
      "unit_def_id": "ashigaru_spear",
      "name": "Ashigaru Spear",
      "x": 1,
      "y": 0,
      "role": "frontline",
      "hp": 120,
      "base_hp": 120,
      "atk": 15,
      "base_atk": 12,
      "defense": 6,
      "base_defense": 4,
      "range": 1,
      "base_range": 1,
      "alive": true,
      "next_action_tick": 40,
      "action_interval_ticks": 20,
      "guard_value": 0,
      "skill_cooldowns": {
        "spear_thrust": 40
      },
      "statuses": []
    }
  ],
  "event_count": 42
}
```

The snapshot intentionally exposes data, not Python objects. It is suitable for future HTML live mode / HTML 实时模式, C# host / C# 宿主, or Godot consumers, but those consumers are not implemented in this phase.

### Event Buffer / 事件缓冲

`get_events_since(session, event_index)` returns event dicts from an integer cursor:

```json
{
  "events": [],
  "next_event_index": 42
}
```

`event_index` is an integer list index, not an `event_id`. A caller stores `next_event_index` and passes it back on the next poll.

## Compatibility / 兼容性

`run_basic_combat(config, battle_id, seed)` remains the stable one-shot API:

```python
session = create_battle_session(config, battle_id, seed)
initialize_battle_session(session)
step_until_finished(session)
return session.state, session.events
```

The public signature does not change. Existing tools keep using it:

- `tools/run_demo_battle.py`
- `tools/generate_demo_scenarios.py`
- replay/report generation
- smoke checks
- web viewer fixture consumption

For `demo_001 / seed=1001`, the compatibility target remains:

- events: `332`
- winner: `ally`
- reason: `enemy_eliminated`
- end_tick: `240`
- total_damage: `1189`
- total_kills: `9`
- total_skill_triggers: `48`
- total_status_applied: `4`
- total_skill_cooldowns: `48`
- total_actions_scheduled: `75`

## Engine Portability / 引擎可移植性

Engine Portability / 引擎可移植性 means future hosts can consume the simulator without owning Python loop details:

- call Step Runtime / 单步运行时 to advance combat
- read Battle Snapshot / 战斗状态快照 for current board/unit state
- read Event Buffer / 事件缓冲 for replay/report/view updates

This keeps the dependency direction:

```text
config -> simulator -> snapshot/events -> viewer/host
```

The simulator still has no dependency on the web viewer, C# UI, Godot scenes, HTTP servers, or WebSocket servers.

Follow-up Live Combat API / 实时战斗 API exposes the same BattleSession / 战斗会话, Battle Snapshot / 战斗状态快照, and Event Buffer / 事件缓冲 through a Local HTTP Server / 本地 HTTP 服务 without changing combat behavior.

## Not in Scope / 不在范围

- No HTTP server / 不做 HTTP server
- No WebSocket server / 不做 WebSocket server
- No HTML live mode / 不做 HTML 实时模式
- No C# host / 不做 C# 宿主
- No Godot / 不做 Godot
- No xlsx adapter / 不做 xlsx 适配器
- No movement/pathfinding / 不做移动与寻路
- No new combat rules / 不做新战斗规则
- No new skill effects / 不做新技能效果
- No new AI logic / 不做新 AI 逻辑
- No general-purpose DSL / 不做通用 DSL
- No new frontend framework / 不引入新前端框架
- No visual regression / 不做视觉回归
- No cross-browser matrix / 不做跨浏览器矩阵

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
