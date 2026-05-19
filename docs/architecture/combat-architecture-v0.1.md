# Combat Architecture Formalization / 战斗架构正式化 v0.1

## Goal / 目标

Ikusa Forge 的战斗系统目标不是只做一条 replay / 回放链路，而是形成一个正式的 Python Combat Runtime / Python 战斗运行时。

这个运行时必须可以通过 Event/Snapshot Contract / 事件与快照契约 迁移到 Godot / C# / 其他引擎，而不是把规则绑定在 HTML viewer / HTML 查看器 或某个特定 host / 宿主 上。

核心原则是：

- Combat behavior / 战斗行为 在 Python runtime / Python 运行时 中保持确定性和可测试性
- Snapshot / 状态快照 与 Events / 事件流 对外稳定
- Engine Portability / 引擎可移植性 依赖数据契约，而不是复制规则实现

## Architecture / 架构

当前分层是：

### BattleSession / 战斗会话

- 负责 session lifecycle / 会话生命周期
- 负责 tick 调度、初始化、暂停/继续/单步、快照导出
- 不直接承载规则细节

### Systems / 战斗系统

- Spatial system / 空间系统
- Targeting / 寻敌与目标选择
- Damage / 伤害
- Skills / 技能触发
- Reporting / 报表统计

### AI Decision / AI 决策

- Intent Decision / 意图决策
- Movement Decision / 移动决策
- Skill Decision / 技能决策
- Action Decision / 行动决策

这些对象用于表达“为什么要做这件事”，而不是把规则写死在调用处。

### Unit FSM / 单位状态机

单位状态机负责轻量、明确、可迁移的状态表达：

- idle / 空闲
- moving_to_formation / 移向阵型
- moving_to_engage / 移向接敌
- engaged / 已接敌
- attacking / 攻击中
- casting / 施法中
- recovering / 恢复中
- dead / 死亡

### Action Pipeline / 行动管线

Action Pipeline / 行动管线 负责：

- build / 构造行动
- validate / 校验行动
- resolve / 结算行动

当前阶段只放入骨架，不强制把所有 combat logic / 战斗逻辑 一次性迁移进去。

### Event/Snapshot Contract / 事件与快照契约

这是可迁移的核心边界：

- Snapshot / 快照 提供权威当前状态
- Events / 事件 提供增量变化与解释
- HTML viewer / HTML 查看器、Godot、C# host / C# 宿主 都应消费这两个契约，而不是复刻规则

## Why not pure Behavior Tree / 为什么不是纯行为树

Behavior Tree / 行为树 很适合复杂角色行为与高层策略，但当前战斗 runtime 需要的是：

- deterministic / 确定性
- testable / 可测试
- portable / 可移植
- stable event ordering / 稳定事件顺序

纯行为树会让底层战斗机制过早依赖更重的节点体系，增加测试成本，也不利于把 runtime 迁移到不同引擎。

## Why not pure FSM / 为什么不是纯状态机

FSM / 状态机 适合表达单位状态，但它并不擅长单独承担：

- target selection / 目标选择
- skill selection / 技能选择
- score-based heuristics / 评分式启发

因此本阶段不把所有问题压成状态跳转，而是把 FSM / 状态机 与 Utility AI / 评分式 AI 分开。

## Chosen Model / 选型

本阶段选型是：

**FSM + Utility AI + Action Pipeline**

含义是：

- FSM / 状态机 管单位状态
- Utility AI / 评分式 AI 管意图、移动、目标、技能决策
- Action Pipeline / 行动管线 管验证与结算

## Godot Portability / Godot 可移植性

未来的 Godot client / Godot 客户端 不应复制战斗规则。

它应该只消费：

- Snapshot / 状态快照
- Events / 事件流

这样 Python runtime / Python 运行时 可以继续作为权威模拟器，而 Godot 只负责渲染与交互壳。

## Migration path / 迁移路线

Phase 2 迁移路线：

- `phase2/formation-and-engagement-system` — Formation and Engagement System / 编队与接敌系统 ✅ 已完成
