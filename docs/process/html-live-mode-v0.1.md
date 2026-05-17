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

This avoids replay-only playback and demonstrates that a browser client can observe a running
runtime session through polling.

## Modes / 模式

The viewer supports three modes simultaneously:

- Live Mode / 实时模式
- Scenario Mode / 场景模式（静态文件样例）
- File Replay Mode / 文件回放模式（手动上传）

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

## Not in Scope / 不在范围

- No WebSocket / 不做 WebSocket
- No C# host / 不做 C# 宿主
- No Godot / 不做 Godot
- No xlsx adapter / 不做 xlsx 适配器
- No movement/pathfinding / 不做移动与寻路
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
