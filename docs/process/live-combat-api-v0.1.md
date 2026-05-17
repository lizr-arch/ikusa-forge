# Live Combat API / 实时战斗 API v0.1

## Goal / 目标

Live Combat API / 实时战斗 API exposes the existing BattleSession / 战斗会话 runtime through a Local HTTP Server / 本地 HTTP 服务.

The goal is to let external clients create and step live battles without importing Python modules directly:

- Battle Session Manager / 战斗会话管理器 owns in-memory sessions.
- Start Battle / 开始战斗 creates and initializes a session.
- Step Battle / 推进战斗 advances the session by ticks.
- Snapshot / 状态快照 returns JSON-safe battle state.
- Event Buffer / 事件缓冲 returns incremental replay events from an integer cursor.

This phase is an API Contract / API 契约 layer over existing combat behavior. It does not add WebSocket, HTML live mode, C# host, Godot, new combat rules, movement/pathfinding, new AI, or a frontend framework.

## API Contract / API 契约

The server module is:

```text
sim-python/ikusa_sim/live_api.py
```

The server uses Python standard library modules only:

- `http.server`
- `json`
- `urllib.parse`
- `threading`
- `uuid`

### Health / 健康检查

```http
GET /api/health
```

Response:

```json
{
  "ok": true,
  "service": "ikusa-live-api"
}
```

### Start Battle / 开始战斗

```http
POST /api/battle/start
```

Request:

```json
{
  "battle_id": "demo_001",
  "seed": 1001,
  "config": "config/generated"
}
```

`config` is optional. If omitted, the server uses the config directory provided at startup.

Response:

```json
{
  "ok": true,
  "session_id": "uuid",
  "snapshot": {
    "schema_version": "battle_snapshot.v0.1"
  },
  "events": [],
  "next_event_index": 29
}
```

Start Battle / 开始战斗 creates a BattleSession / 战斗会话 and runs initialization, so the response includes tick 0 events such as `battle_start`, `unit_spawn`, `stat_modifier`, `status_apply`, and `skill_cooldown` when the demo rules produce them.

### Step Battle / 推进战斗

```http
POST /api/battle/step
```

Request:

```json
{
  "session_id": "uuid",
  "ticks": 1
}
```

Response:

```json
{
  "ok": true,
  "snapshot": {
    "schema_version": "battle_snapshot.v0.1"
  },
  "events": [],
  "next_event_index": 42
}
```

Step Battle / 推进战斗 returns only the events emitted during that step call.

### Snapshot / 状态快照

```http
GET /api/battle/snapshot?session_id=uuid
```

Response:

```json
{
  "ok": true,
  "snapshot": {
    "schema_version": "battle_snapshot.v0.1"
  }
}
```

### Event Buffer / 事件缓冲

```http
GET /api/battle/events?session_id=uuid&since=0
```

Response:

```json
{
  "ok": true,
  "events": [],
  "next_event_index": 42
}
```

`since` is an integer list cursor, not an `event_id`. Store `next_event_index` and pass it back on the next call.

### Reset / 重置会话

```http
POST /api/battle/reset
```

Request:

```json
{
  "session_id": "uuid"
}
```

Response:

```json
{
  "ok": true
}
```

Reset / 重置会话 removes the in-memory session. No session data is persisted to disk.

## Session Lifecycle / 会话生命周期

Recommended client flow:

1. `GET /api/health`
2. `POST /api/battle/start`
3. Repeatedly call `POST /api/battle/step`
4. Poll `GET /api/battle/snapshot` and `GET /api/battle/events`
5. Call `POST /api/battle/reset` when done

Multiple sessions can coexist in one Battle Session Manager / 战斗会话管理器. Each session has an independent BattleSession / 战斗会话, Snapshot / 状态快照, and Event Buffer / 事件缓冲.

## Error Handling / 错误处理

The API always returns JSON, including errors:

```json
{
  "ok": false,
  "error": "unknown session_id: ..."
}
```

Status codes:

- `200` for success
- `400` for bad request, bad JSON, missing fields, invalid ticks, invalid battle id, or config load/validation errors
- `404` for unknown session ids or unsupported routes
- `500` for unexpected internal errors

## Smoke / 冒烟

Run the server:

```bash
python tools/run_live_api.py --config config/generated --host 127.0.0.1 --port 8765
```

In another terminal, run the smoke:

```bash
python tools/smoke_live_api.py --host 127.0.0.1 --port 8765 --battle demo_001 --seed 1001
```

CI uses the managed smoke wrapper so the server is always stopped:

```bash
python tools/run_live_api_smoke.py --config config/generated --battle demo_001 --seed 1001
```

The smoke checks:

- Health / 健康检查
- Start Battle / 开始战斗
- Snapshot / 状态快照 schema `battle_snapshot.v0.1`
- tick 0 events from initialization
- repeated Step Battle / 推进战斗 until finished
- final winner/reason/end_tick
- Event Buffer / 事件缓冲 from `since=0`
- Snapshot / 状态快照 endpoint
- Reset / 重置会话

## Not in Scope / 不在范围

- No WebSocket / 不做 WebSocket
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
