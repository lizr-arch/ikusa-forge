# HTML Live Mode / HTML 实时模式 v0.1

## Goal / 目标

HTML Live Mode / HTML 实时模式 lets the existing SVG Replay Viewer / SVG 回放查看器
run a battle through the local Live Combat API / 实时战斗 API, instead of loading a pre-generated
`replay.json` file.

The viewer behavior is:

- Start Live Battle / 开始实时战斗
- call `POST /api/battle/start`
- poll `POST /api/battle/step` on an interval
- consume `snapshot` and `events` to render `Battlefield / 战场`
- stop at battle end
- render Realtime Spatial Combat / 实时空间战斗 movement from Continuous Position / 连续坐标 fields

This avoids replay-only playback and demonstrates that a browser client can observe a running
runtime session through polling.

## Modes / 模式

The viewer supports three modes simultaneously:

- Live Mode / 实时模式
- Scenario Mode / 场景模式（静态文件样例）
- File Replay Mode / 文件回放模式（手动上传）

Live rendering behavior is now Battlefield-first / 战场优先:

- Battlefield（战场） is the dominant visual zone for live playback
- Timeline（事件日志） and Report（战报） remain secondary
- Replay / 场景 controls stay available and unchanged for non-live work

Mode switching keeps old workflows intact:

- Live mode disables replay timer controls.
- Replay / 场景 loading calls `stopAllPlayback()` and switches to replay mode.
- Manual file load still works through existing controls and stays available in Scenario Mode / 场景模式.

## Live API Flow / 实时 API 流程

The browser live loop follows this contract:

1. `GET /api/health`
2. `POST /api/battle/start`
3. repeatedly `POST /api/battle/step` with `ticks` (1/2/4 based on speed)
4. `build` visual state from latest `snapshot`
5. append live `events`
6. stop timer on finished session

Endpoints are consumed directly from `liveApiClient.ts`:

- `healthLiveApi`
- `startLiveBattle`
- `stepLiveBattle`
- `getLiveSnapshot`
- `getLiveEvents`
- `resetLiveBattle`

Snapshot / 状态快照 units may include Realtime Spatial Combat / 实时空间战斗 fields such as `position_x`, `position_y`, `move_speed`, `attack_range`, `engaged_target`, and `movement_intent`. The HTML viewer treats those as the authoritative Live Battlefield / 实时战场 position.

## Bilingual UI / 双语界面

This mode keeps user-visible labels bilingual (`English（中文）`) in:

- Live Mode / 实时模式 panel
- Battle field controls / 战场控制
- Scenario Selector / 场景选择器
- Playback Controls / 播放控制
- Event Highlight / 事件高亮
- Timeline / 时间线
- Unit Detail / 单位详情
- Report Panel / 战报面板
- Battle Summary / 战斗摘要
- Live Status / 实时状态
- Error readouts / 错误提示

Examples shown in UI:

- `Start Live Battle（开始实时战斗）`
- `Pause（暂停）`
- `Resume（继续）`
- `Step（单步）`
- `Reset（重置）`
- `Speed（速度）`
- `Live API unavailable（实时 API 不可用）`

## Battlefield First Layout / 战场优先布局

- Battlefield（战场） is the top-level focus in desktop layout.
- Units now show battlefield-first status overlays:
  - HP Bar / 血条
  - Action Bar / 行动条
  - status count / 状态数量
  - cooldown count / 冷却数量
  - selected / highlighted styles / 选中与高亮样式
- Live status metadata now includes:
  - Current Tick（当前 Tick）
  - Unit Alive（存活单位）
  - Latest Event（最新事件）
  - Transport（传输方式）

Live visual effects in this phase:

- Attack Line / 攻击线
- Floating Damage / 伤害跳字
- Skill Callout / 技能提示
- Status Badge / 状态标记
- Cooldown Badge / 冷却标记
- Death Marker / 死亡标记
- Victory Banner / 胜负横幅

## Not in Scope / 不在范围

- No WebSocket / 不做 WebSocket
- No C# host / 不做 C# 宿主
- No Godot / 不做 Godot
- No xlsx adapter / 不做 xlsx 适配器
- Movement / 移动 is limited to straight-line Simple Engagement / 简单接敌; no A* pathfinding / 不做 A* 寻路
- No new frontend framework / 不引入新前端框架
- No visual regression / 不做视觉回归
- No cross-browser matrix / 不做跨浏览器矩阵

## Verification / 验证

For local live-mode smoke:

```bash
python tools/run_live_api.py --config config/generated --host 127.0.0.1 --port 8765
```

and then open:

```text
http://127.0.0.1:5173
```

Then in Live Mode / 实时模式:

- set `API URL（API 地址）`
- set battle id / 种子
- click `Start Live Battle（开始实时战斗）`

Failure case should show clear message in `Live Status（实时状态）`:

- `Live API unavailable（实时 API 不可用）`

## Local CORS and hosting boundary / 本地 CORS 与托管边界

Live mode uses local browser polling against `liveApi` on `127.0.0.1`:

1. Start API locally:
   - `python tools/run_live_api.py --config config/generated --host 127.0.0.1 --port 8765`
2. Run viewer:
   - `cd web-viewer && npm run dev`
3. Click in UI:
   - `Start Live Battle（开始实时战斗）`

The API returns local dev CORS headers so calls from `http://127.0.0.1:5173` and `http://localhost:5173` succeed:

- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET, POST, OPTIONS`
- `Access-Control-Allow-Headers: Content-Type`

Local boundary notes:

- 默认只应绑定本机地址（`--host 127.0.0.1`）;
- 当前 `*` 来源策略为 local dev convenience，不应对不可信网络开放;
- 若要对外提供服务，需要补充认证、严格 CORS policy 与 `config` 参数校验。
