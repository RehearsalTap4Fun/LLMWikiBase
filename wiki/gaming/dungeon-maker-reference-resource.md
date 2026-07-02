---
title: Dungeon Maker 参考资源包
type: source-summary
domain: gaming
source: sources/gaming/dungeon-maker-reference/README.md
date: 2026-07-01
confidence: medium
tags: [Dungeon Maker, 地牢经营, 塔防, 配置物料, 游戏参考, resource]
links: ["[[dungeon-maker-framework-pattern]]"]
---

# Dungeon Maker 参考资源包

这是一次面向后续开发的本地 resource 整理：将 Dungeon Maker 英文 Wiki 中可结构化的系统、单位、房间、技能、遗物等内容，整理成知识库内的游戏参考资源包。

## Resource 位置

- 原始资源目录：`sources/gaming/dungeon-maker-reference/`
- 框架说明：`sources/gaming/dungeon-maker-reference/framework.md`
- 配置 Schema：`sources/gaming/dungeon-maker-reference/config_schema.json`
- 本地配置：`sources/gaming/dungeon-maker-reference/config/`
- 生成脚本：`sources/gaming/dungeon-maker-reference/tools/scrape_dungeon_maker_configs.py`

## 已整理配置

| 文件 | 条目数 | 用途 |
|---|---:|---|
| `dark_lords.json` | 10 | 黑暗领主：基础属性、技能、解锁来源 |
| `monsters.json` | 84 | 怪物：星级、属性、固有技能、结构化合成字段 |
| `heroes.json` | 84 | 英雄：星级、技能、Boss 层、拷问工具 |
| `rooms.json` | 201 | 房间：类型、星级、效果文本、结构化合成/升级字段 |
| `monster_fusion_recipes.json` | 84 | 怪物合成图谱：输入材料、输出目标、来源方向 |
| `room_recipes.json` | 580 | 房间合成/升级图谱：输入房间、输出房间、来源方向 |
| `relics.json` | 269 | 遗物：星级、锁定、可重复、来源页 |
| `fate_cards.json` | 14 | 命运卡：卡牌类型、行动入口 |
| `skills.json` | 304 | 技能配置：普通技能、怪物技能、英雄技能、说明和旧版说明 |
| `status_effects.json` | 82 | 状态效果配置：状态 code、名称、说明、备注 |
| `events.json` | 32 | 事件配置：事件描述、选择项文本、备注 |
| `rewards.json` | 8 | 奖励配置：奖励入口、说明、来源和备注 |
| `boss_battles.json` | 114 | Boss 战配置：天数、分数、Boss/英雄 ID、祝福 buff |
| `difficulty_tiers.json` | 26 | 难度与可选 Trial：经验倍率、Buff 文本、增长参数 |
| `trial_modifiers.json` | 10 | Trial Card 负面词条：点数和效果说明 |
| `books.json` | 66 | 书籍配置：章节数和章节收益说明 |
| `torture_tools.json` | 12 | 拷问工具：所需天数、解锁和说明 |
| `systems.json` | 4 | 模式、资源、卡包、运行时事件枚举 |

## 适合复用的内容

- 以 `Fate Cards` 驱动每日选择的 Run 内路径结构。
- 地牢 Grid 中 `Trap / Battle / Facility / Prison / Altar / Shrine` 的房间类型拆分。
- 单位配置中的 `Dark Lord / Monster / Hero / Corrupted Hero` 分层。
- 用统一 `EffectSpec` 管理技能、遗物、装备、房间和状态效果。
- 通过 Pack、Challenge、Story、Succession 组成局外成长与长期解锁。

## 已知缺口

- 合成关系已经拆成图结构，但还没有归一到项目正式 ID 命名和资源管线格式。
- 技能和状态效果已有说明文本，但尚未完全拆成可执行的效果 DSL、触发器、目标选择器和公式 AST。
- 事件、奖励、Boss、难度、Trial、书籍、拷问工具已有配置文件。
- 剩余未完全结构化：事件选项强类型分支、奖励权重、商店价格曲线、难度/Boss 数值公式 AST。
- Wiki 是非官方来源，且只做参考设计归纳；用于正式项目时应二次设计，避免直接复制内容。

## 关联

- [[dungeon-maker-framework-pattern]]：从该 resource 提炼出的可复用系统框架。
