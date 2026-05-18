# Live Battle Visual Polish / 实时战斗视觉打磨 v0.1

## Goal / 目标

This phase turns HTML Live Mode / HTML 实时模式 from a debug-first replay inspector into a battle-first presentation.

核心目标是保持当前战斗行为不变的前提下，优先把观战焦点从事件列表切回可见化战场：

- Battlefield First Layout / 战场优先布局
- unit-state rendering / 单位状态渲染加强
- transient Visual Effects / 临时视觉效果
- clearer victory output / 更清晰的胜负显示

## Battlefield First Layout / 战场优先布局

The page now gives precedence to the live battlefield:

- Battlefield（战场）区域放在主列，使用更大空间与更高优先级布局
- Timeline（时间线）和 Report（战报）保持为辅助区域
- Control / 控制和 Live Status（实时状态）与状态元数据仍可见，但从视觉上不抢占主战场
- Required panel labels are bilingual:
  - Battle Control（战斗控制）
  - Selected Unit（选中单位）
  - Event Log（事件日志）
  - Report（战报）

## Visual Effects / 视觉效果

Live board rendering (`web-viewer/src/boardView.ts`) now adds lightweight transient marks for recent events:

- Attack Line / 攻击线：`attack` events render a visible line between source and target
- Floating Damage / 伤害跳字：`damage` amount is rendered near target
- Skill Callout / 技能提示：`skill_trigger` source label and ring
- Status Badge Flash / 状态闪烁：`status_apply` / `status_expire` marker near target
- Cooldown Badge / 冷却标记：`skill_cooldown` marker + remaining ticks
- Death Marker / 死亡标记：单位死亡时 `unit-dead` 及十字阴影显著变化
- Victory Banner / 胜负横幅：battle end 时在战场顶部显示 `Victory（胜负）`

Units now also show action/metric overlays:

- HP Bar（血条）
- Action Bar / 行动条
- Status count（状态数量）
- Cooldown count（冷却数量）
- ally/enemy side tint（阵营着色）
- selected/highlight border（选中与事件高亮）

## Bilingual UI / 双语界面

Live-related visible labels remain bilingual `English（中文）`, including:

- Battlefield（战场）
- Start Live Battle（开始实时战斗）
- Pause（暂停）
- Step（单步）
- Reset（重置）
- Live Status（实时状态）
- Session ID（会话 ID）
- Event Cursor（事件游标）
- Current Tick（当前 Tick）
- Unit Alive（存活单位）
- Latest Event（最新事件）
- Transport（传输方式）

This phase keeps earlier bilingual anchors like Scenario Selector（场景选择器）, Report Panel（战报面板）, and Timeline（事件日志）alive.

## Not in Scope / 不在范围

本阶段只做视觉打磨与显示层增强，不改战斗逻辑。

- no new combat rules / 不新增战斗规则
- no movement/pathfinding / 不做移动与寻路
- no WebSocket / 不做 WebSocket
- no C# host / 不做 C# 宿主
- no Godot / 不做 Godot
- no new frontend framework / 不引入新前端框架
- no visual regression / 不做视觉回归
