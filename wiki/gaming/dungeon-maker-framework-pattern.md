---
title: Dungeon Maker 式地牢经营框架
type: concept
domain: gaming
source: sources/gaming/dungeon-maker-reference/framework.md
date: 2026-07-01
confidence: medium
tags: [地牢经营, 塔防, 卡牌路径, 自动战斗, 局外成长, 配置驱动]
links: ["[[dungeon-maker-reference-resource]]"]
---

# Dungeon Maker 式地牢经营框架

Dungeon Maker 的可复用价值不在单个数值，而在“每日卡牌路径 + 地牢建设 + 自动战斗 + 局外解锁”的组合框架。它适合被抽象为配置驱动的塔防/地牢经营原型。

## 主循环

1. 玩家选择模式、难度、Dark Lord 和继承内容。
2. 每天从 3 张 Fate Cards 中选择一张。
3. 卡牌触发战斗、建设、商店、事件、试炼、读书、拷问等行动。
4. 战斗中英雄沿地牢路径入侵，房间和单位按触发器结算。
5. 胜利后发放资源、房间、怪物、遗物、装备等奖励。
6. 每 20 天进入 Boss Battle，作为阶段压力和奖励节点。
7. Run 结束后进入局外成长，消耗长期货币解锁卡包、角色、房间和继承能力。

## 核心对象

- `Dark Lord`：Run 的核心角色，也是最终防线。
- `Monster / Hero / Corrupted Hero`：战斗双方与转化系统的基础单位。
- `Room`：地牢格子上的主要配置实体，分为战斗、陷阱、功能、监狱、祭坛、神殿等。
- `Fate Card`：每日行动入口，也是路径选择和节奏控制工具。
- `Skill / Status Effect`：战斗表达层，建议统一走事件触发和效果 DSL。
- `Relic / Equipment / Orb / Room Component`：局内道具和构筑强化层。

## 配置驱动要点

- 把 `onEnterRoom`、`onDeath`、`onBattleStart`、`onReward`、`onDayStart` 等事件标准化。
- 房间、技能、遗物、装备不要各自硬编码，统一转成 `EffectSpec`。
- 解锁和掉落分离：`unlock` 决定是否进入池，`sourcePool` 决定从哪里产出。
- Run 开始时生成 `RunRuleset` 快照，合并模式、难度、继承、局外解锁，战斗中只读快照。
- 对合成和升级关系单独建图，避免房间/怪物配置表承担过多关系查询职责。

## 可迁移到后续项目的模块

- `FateCardSystem`：生成每日 3 选 1 路径、Boss 节点、Trial 节点。
- `DungeonGridSystem`：管理格子、房间覆盖、路径、唯一房间。
- `RoomTriggerSystem`：处理进入、离开、相邻、全局触发。
- `AutoBattleSystem`：英雄波次、怪物站位、技能冷却、状态结算。
- `RewardSystem`：按卡牌、难度、天数、Boss 状态生成奖励池。
- `MetaProgressionSystem`：卡包、重生等级、继承、挑战解锁。

## 使用边界

该框架是从 [[dungeon-maker-reference-resource]] 的本地配置和框架文档中整理出的设计模式。置信度标为 medium：系统结构来自 Wiki 和本地抽取结果，但具体数值、技能公式、掉落权重仍需项目内二次验证。
