# Dungeon Maker 参考游戏资源包

> resource 类型：游戏设计参考 / 索引说明  
> 来源：Dungeon Maker 英文非官方 Wiki 与本地整理结果  
> 整理日期：2026-07-01  
> 原工作区：`/Users/tap4fun/Documents/TDGame`

## 内容

- `framework.md`：游戏框架、系统拆分、配置表建议。
- 配置 Schema 草案位于 `/Users/tap4fun/Documents/TDGame/data/dungeon_maker_config_schema.json`。
- Wiki 抽取的本地 JSON 配置物料位于 `/Users/tap4fun/Documents/TDGame/data/config/`。
- 配置抓取与生成脚本位于 `/Users/tap4fun/Documents/TDGame/tools/scrape_dungeon_maker_configs.py`。
- Wiki 美术资源、索引与说明位于 `/Users/tap4fun/Documents/TDGame/assets/wiki/`。
- Wiki 美术资源下载脚本位于 `/Users/tap4fun/Documents/TDGame/tools/download_dungeon_maker_assets.py`。

## 配置条目

当前项目目录 `/Users/tap4fun/Documents/TDGame/data/config/` 包含：

- `dark_lords.json`：10 条
- `monsters.json`：84 条
- `heroes.json`：84 条
- `rooms.json`：201 条
- `monster_fusion_recipes.json`：84 条
- `room_recipes.json`：580 条
- `relics.json`：269 条
- `fate_cards.json`：14 条
- `skills.json`：304 条
- `status_effects.json`：82 条
- `events.json`：32 条
- `rewards.json`：8 条
- `boss_battles.json`：114 条
- `difficulty_tiers.json`：26 条
- `trial_modifiers.json`：10 条
- `books.json`：66 条
- `torture_tools.json`：12 条
- `systems.json`：4 个系统枚举分组

## 用途

这个 resource 用作后续塔防/地牢经营类游戏开发的参考素材：

- 设计阶段：参考系统边界、主循环、局外成长、房间/单位/技能关系。
- 配置阶段：从 TDGame 项目的 `data/config/` 复用 JSON 表结构，进一步清洗为项目正式配置。
- 原型阶段：快速搭建地牢格子、命运卡、自动战斗、奖励池和解锁系统。

## 边界

- 本资源包不是 Wiki 镜像，不包含完整原始页面。
- 合成关系已拆成 `monster_fusion_recipes.json` 和 `room_recipes.json`，原始字段仍保留用于审计。
- `skills.json` 已补齐技能说明，`status_effects.json` 已补齐状态 code、名称、说明和备注。
- 事件、奖励、Boss、难度、Trial、书籍、拷问工具已生成本地配置。
- Wiki 美术资源已按模块下载到 `/Users/tap4fun/Documents/TDGame/assets/wiki/`，共 6236 个资源条目，索引见 `/Users/tap4fun/Documents/TDGame/assets/wiki/manifest.summary.json`。
- 仍需二次清洗的部分：技能/状态公式 DSL、事件选项强类型分支、奖励权重、商店价格曲线、难度/Boss 数值公式 AST。
