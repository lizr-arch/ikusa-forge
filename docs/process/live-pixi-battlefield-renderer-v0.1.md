# Live Pixi Battlefield Renderer / PixiJS 实时战场渲染器 v0.1

## Goal / 目标

把 HTML Live Mode / HTML 实时模式 的主战场从 SVG/DOM 调试展示升级为 PixiJS 渲染的 Live Battlefield / 实时战场。

本阶段的目标不是加新玩法，而是让浏览器端更适合观看实时战斗：

- Python Combat Runtime / Python 战斗运行时 仍然是唯一战斗规则来源
- Live API / 实时 API 的 Snapshot + Events / 快照 + 事件 契约不变
- DOM 继续负责控制面板、单位详情、事件日志、战报、性能面板
- PixiJS 只负责主战场绘制、单位几何、点击命中和临时视觉效果

## Why PixiJS / 为什么选择 PixiJS

PixiJS 是渲染引擎，不是完整游戏框架。

选择 PixiJS 的原因是：

- 适合把 Python Combat Runtime / Python 战斗运行时 的空间快照做成长期客户端渲染层
- 对单位、血条、行动条、视觉特效的增量渲染更自然
- 仍然保留 HTML/DOM 作为控制与信息面板，不强行接管整个应用生命周期
- 后续如果迁移到 Godot / C#，Pixi 侧可以继续只消费 Snapshot + Events / 快照 + 事件

## Why not Phaser / 为什么不选 Phaser

Phaser 更像完整游戏框架，会把场景管理、物理、循环与输入体系一起带进来。

当前项目不是普通 HTML5 游戏，而是战斗系统实验室，因此没有必要把页面生命周期交给 Phaser。

本阶段只需要一个主战场渲染器，而不是整套游戏壳。

## Why not raw Canvas / 为什么不继续 raw Canvas

raw Canvas / 原生 Canvas 2D 可以很轻，但长期维护会把渲染、命中、精灵、效果和布局逻辑重新写一遍。

PixiJS 更适合作为长期 renderer / 渲染器：

- 提供可维护的场景树
- 保留后续扩展空间
- 不把页面绑定到自制 Canvas 管线
- 避免先做一层 Canvas 再整体迁移

## Visual State Buffer / 视觉状态缓冲

live snapshot / 实时快照 到达后，浏览器不会直接把单位位置瞬间跳到下一帧。

而是通过 `visualStateBuffer.ts` 保存 previous/current state，并在渲染时做轻量插值：

- 连续坐标 / Continuous Position 使用 `position_x / position_y`
- 视觉上平滑过渡，不要求 Python runtime 产生更复杂的动画事件
- 死亡单位仍保留位置并变灰
- 事件效果继续从 `events` 中读取

这让 Snapshot + Events / 快照 + 事件 既可用于 replay / 回放，也可用于 live / 实时观看。

## Formation Roster / 阵容堆栈

右侧的 Formation Roster / 阵容堆栈 是 live battlefield 的信息补充，而不是主战场本身。

它按 Ally（友军）/ Enemy（敌军）分组展示单位，并提供：

- unit id / 单位 ID
- troop shape / 兵种形状
- HP / 生命
- Combat State / 战斗状态

点击阵容项后，Selected Unit / 选中单位 会显示更完整的细节。

## Boundary / 边界

本阶段不做：

- 不改 Python 战斗规则
- 不改 Live API response shape / 响应形状
- 不做 WebSocket
- 不做 Godot / C# host
- 不做 A* / navmesh / terrain / obstacle collision
- 不引入 React / Vue / Phaser
- 不做视觉回归截图测试

PixiJS 只负责渲染层，战斗逻辑仍由 Python runtime 决定。
