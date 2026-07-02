# Dungeon Maker 参考框架与配置物料

资料来源：Dungeon Maker 英文非官方 Wiki，采集日期 2026-06-30。本文不是逐字搬运 Wiki，而是把其系统结构反推为后续开发可用的框架、配置表和数据关系。

## 1. 游戏定位

参考游戏是“地牢经营 + 路线卡牌 + 自动战斗 + 长线解锁”的混合框架：

- 玩家选择一个 Dark Lord 作为核心角色。
- 每一天从 3 张 Fate Cards 中选择路径，决定当天行动。
- 玩家通过战斗、商店、地牢建设、事件、读书、拷问等行动强化地牢。
- 英雄按波次入侵，穿过房间并尝试击杀 Dark Lord。
- 每 20 天触发 Boss Battle，作为世界周期结算点。
- 局外通过 Abyss Shop、Pack、成就与重生等级解锁角色、房间、遗物、模式和继承能力。

## 2. 主循环框架

### 2.1 Run 内循环

1. `StartRun`
   - 选择游戏模式、难度、Dark Lord、初始继承内容、可选 Dungeon Map。
   - 初始化资源：Gold、Soul、Day、Dungeon Grid、Prison、Altar、Monster Pool、Relics。

2. `DailyFateSelection`
   - 展示 3 张 Fate Cards。
   - 玩家选择一张；选择会影响下一日可见卡组路径。

3. `ResolveCardAction`
   - Battle 类：进入自动战斗，胜利后给奖励。
   - Dungeon 类：建设、读书、拷问、设施操作等。
   - Trader 类：消费 Gold/Soul 购买、强化、变更单位或房间。
   - Event 类：触发多选项随机事件。
   - Trial 类：选择一个永久负面词条。

4. `BattleSimulation`
   - 英雄从入口路径进入房间。
   - Trap Room 在英雄进入时触发。
   - Battle Room 内怪物与英雄战斗。
   - Facility、Relic、Skill、Status Effect 持续修正战斗。
   - Dark Lord Room 是最后防线。

5. `RewardAndProgress`
   - 发放 Gold、Soul、Reward Options。
   - 更新 Day。
   - 每 20 天插入 Boss Battle。
   - 满足条件时解锁更高难度或局外奖励。

### 2.2 局外循环

- `RebirthLevel`：运行结束后累计经验，提升长期等级。
- `DevilStone`：通过成就和重生获得，用于 Abyss Shop 抽取永久解锁。
- `PackUnlock`：Original、Awakening、Advanced、Corruption、Adventure、Myth、Conqueror、Abyss 等包。
- `Succession`：允许继承部分怪物、房间或能力进入后续 Run。
- `Collection`：Dark Lord、Monster、Room、Relic、Equipment、Book、Event、Mode 等图鉴和解锁。

## 3. 核心配置对象

### 3.1 Dark Lord

Wiki 结构来源：`UnitDarklord` 模板，例如 Lilith、Elizabeth、Luca。

建议配置字段：

- `id`：如 `D1001`。
- `name`：角色名。
- `baseStats`：`life`、`atk`、`def`。
- `skills`：4 个 Boss Skill 或成长技能槽。
- `unlock`：初始可用、Pack 解锁、Challenge 解锁、Story 解锁等。
- `awakening`：觉醒版本条件和皮肤。
- `transcendence`：超越版本条件和皮肤。
- `synergyTags`：核心流派标签，例如 charm、vampire、thorn、burn。
- `relicSynergy`：专属或强相关遗物。

### 3.2 Monster / Corrupted Hero

Wiki 结构来源：`PageMonster`、`PageHero` 模板。

建议配置字段：

- `id`：数值或字符串 ID。
- `name`
- `unitType`：`monster`、`hero`、`corruptedHero`、`fusion`、`contract`、`event`。
- `rank`：星级或稀有度。
- `baseStats`：`life`、`atk`、`def`。
- `innateSkill`：唯一技能。
- `commonSkillSlots`：普通技能槽数量，参考 Dark Lord 可有 5 个、怪物常规 4 个。
- `fusionFrom`：合成材料。
- `fusionTo`：可作为哪些合成的材料。
- `orbConvertible`：能否被转化为 Orb。
- `unlock`：Pack、事件、挑战、模式、初始。
- `tortureTools`：英雄或腐化英雄关联的拷问工具。

### 3.3 Room

Wiki 结构来源：`PageRoom` 模板；分类包括 Battle Rooms、Traps、Facilities、Prisons and Altars、Shrines。

建议配置字段：

- `id`：如 `eArena`、`eArrow`、`ePrison`。
- `name`
- `roomType`：
  - `battle`：可部署怪物，提供房间战斗修正。
  - `trap`：英雄进入时触发。
  - `facility`：经济、强化、特殊功能。
  - `prison`：囚禁英雄，支撑拷问/腐化系统。
  - `altar`：产出 Soul 或特殊资源。
  - `shrine`：英雄侧强化或地图特殊房。
- `rank`
- `capacity`：怪物位、囚犯位、资源上限。
- `effect`：触发条件、目标、数值公式。
- `levelScaling`：每级增加值。
- `recipe`：合成来源。
- `materialFor`：可合成目标。
- `placementRules`：可放置区域、是否覆盖、是否唯一。
- `unlock`

### 3.4 Fate Card

Wiki 来源：Cards、Dungeon Card、Trial Card、Events、Black Market、Facility Trader、Boss Battles。

建议配置字段：

- `id`
- `name`
- `cardType`：
  - `battle`
  - `eliteBattle`
  - `bossBattle`
  - `dungeon`
  - `event`
  - `merchant`
  - `facilityTrader`
  - `equipmentTrader`
  - `blackMarket`
  - `trial`
  - `treasure`
- `weight`
- `availability`：模式、难度、天数、解锁条件。
- `actionList`：卡牌可执行服务。
- `costRules`：Gold、Soul、Day、资源倍率。
- `rewardPool`
- `nextCardInfluence`：影响后续卡牌路径或权重的标签。

### 3.5 Skill

Wiki 来源：Common Skills、Monster Skills、Hero Skills、Corrupted Hero Skills。

建议配置字段：

- `id`
- `name`
- `skillType`：`active`、`passive`、`continuous`、`boss`。
- `ownerType`：Dark Lord、Monster、Hero、Corrupted Hero、Equipment、Orb。
- `rank`
- `cooldown`
- `trigger`
- `targetSelector`
- `effects`
- `inheritance`：是否可通过合成、占卜、Orb、装备继承。
- `stackRule`：是否唯一、是否叠加、同名是否互斥。

### 3.6 Status Effect

Wiki 来源：Status Effects。

建议配置字段：

- `id`
- `name`
- `polarity`：buff、debuff、antiBuff、antiDebuff、resourceLike。
- `stackable`
- `consumeRule`
- `durationRule`
- `effectFormula`
- `counteredBy`
- `producedBy`：房间、技能、遗物、装备、书籍、事件。

### 3.7 Relic / Equipment / Orb / Room Component

建议拆成四张配置表：

- `RelicConfig`：局内获得、全局被动、可重复、锁定、星级。
- `EquipmentConfig`：单位装备，立即分配，只能持有 1 件，附加随机词条。
- `OrbConfig`：由怪物或腐化英雄献祭生成，继承其 innate skill，作为装备穿戴。
- `RoomComponentConfig`：房间装备，强化房间战斗、经济或特殊效果。

通用字段：

- `id`
- `name`
- `itemType`
- `rank`
- `effect`
- `rollRange`
- `sourcePool`
- `equipTarget`
- `replacementRule`
- `unlock`

## 4. 地牢与战斗结构

### 4.1 Dungeon Grid

- 默认从 3x3 到 6x5 扩展。
- 可选择预设 Dungeon Map，选择后房间布局不可再自由组织。
- 房间类型决定触发规则：
  - Trap：英雄进入触发。
  - Battle：英雄进入后与部署怪物战斗。
  - Facility：持续或服务型效果。
  - Prison/Altar：和囚犯、Soul 系统绑定。
  - Dark Lord Room：终点和失败条件。

### 4.2 自动战斗建议模块

- `WaveSpawner`：按 Day、Difficulty、BossTable 生成英雄波次。
- `PathResolver`：计算英雄穿越房间路径。
- `RoomTriggerSystem`：处理进入、离开、死亡、相邻、全局等触发。
- `CombatSystem`：单位属性、普攻、技能冷却、目标选择。
- `StatusSystem`：统一处理 Buff/Debuff、Anti-Buff、消耗与叠层。
- `RewardSystem`：根据卡牌类型、Boss、奖励池生成选项。

## 5. 玩法系统拆分

### 5.1 Construction

来源：Dungeon Card、Facility Trader、Rewards。

- 房间购买、强化、合成、特殊升级。
- 基础房间可覆盖，部分房间唯一。
- 合成需要 2 到 3 个材料房间。

### 5.2 Prison / Torture / Corruption

来源：Prisons and Altars、Torture、Black Market。

- 战斗奖励可捕获英雄，前提是存在 Prison。
- 拷问工具对不同英雄的 Mental Strength 削减不同。
- 怪物类型通常不影响拷问效率，技能可加成。
- 英雄准备完成后可在 Black Market 腐化为可用单位。

### 5.3 Books

来源：Books。

- Dungeon Card 行动之一。
- 读章节，每章完成立即提供持续到本 Run 结束的收益。
- 书籍可来自奖励、事件或初始解锁。

### 5.4 Trials

来源：Trial Card、Normal Mode。

- 高难度中出现。
- 按特定天数强制出现。
- 玩家从 3 个永久负面修正中选 1 个，持续整局。

### 5.5 Modes

- `Normal Mode`：标准体验，14 个难度等级、9 个大阶层。
- `Challenge Mode`：特殊条件挑战，可解锁角色超越等。
- `Rogue-like Mode`：DLC 模式，偏卡组构筑和回合制。
- `Story Mode`：Luca 主线，有限资源、入侵/防守、结局分支。
- `Total War`：主页面列为额外玩法，适合作为后续扩展模式。

## 6. 推荐配置表清单

- `dark_lords.json`
- `units_monsters.json`
- `units_heroes.json`
- `rooms.json`
- `room_recipes.json`
- `fate_cards.json`
- `card_actions.json`
- `skills.json`
- `status_effects.json`
- `relics.json`
- `equipment.json`
- `orbs.json`
- `room_components.json`
- `books.json`
- `events.json`
- `trials.json`
- `boss_waves.json`
- `difficulty_tiers.json`
- `reward_pools.json`
- `unlock_packs.json`
- `game_modes.json`

## 7. 实现建议

- 配置优先：房间、技能、遗物、状态都走统一 effect DSL，避免每个道具写硬编码。
- 触发统一：把 `onEnterRoom`、`onDeath`、`onBattleStart`、`onDayStart`、`onReward` 等设计为事件总线。
- 数值公式结构化：例如 `base + perLevel * level`、`base + growth * floor(world / 5)`。
- 解锁和掉落分离：`unlock` 控制是否进入池，`sourcePool` 控制从哪里获得。
- 运行时快照：Run 开始时把长期解锁、难度、模式合成一份 `RunRuleset`，减少战斗中反复查局外状态。

## 8. 主要来源页面

- [Dungeon Maker Wiki](https://duma-eng.fandom.com/wiki/Dungeon_Maker_Wiki)
- [Cards](https://duma-eng.fandom.com/wiki/Cards)
- [Dungeon Card](https://duma-eng.fandom.com/wiki/Dungeon_Card)
- [Trial Card](https://duma-eng.fandom.com/wiki/Trial_Card)
- [Battle Rooms](https://duma-eng.fandom.com/wiki/Battle_Rooms)
- [Traps](https://duma-eng.fandom.com/wiki/Traps)
- [Room Components](https://duma-eng.fandom.com/wiki/Room_Components)
- [Common Skills](https://duma-eng.fandom.com/wiki/Common_Skills)
- [Monster Skills](https://duma-eng.fandom.com/wiki/Monster_Skills)
- [Hero Skills](https://duma-eng.fandom.com/wiki/Hero_Skills)
- [Status Effects](https://duma-eng.fandom.com/wiki/Status_Effects)
- [Normal Mode](https://duma-eng.fandom.com/wiki/Normal_Mode)
- [Rogue-like Mode](https://duma-eng.fandom.com/wiki/Rogue-like_Mode)
- [Story Mode](https://duma-eng.fandom.com/wiki/Story_Mode)
- [Challenge Mode](https://duma-eng.fandom.com/wiki/Challenge_Mode)
- [Abyss Shop](https://duma-eng.fandom.com/wiki/Abyss_Shop)
- [Events](https://duma-eng.fandom.com/wiki/Events)
- [Books](https://duma-eng.fandom.com/wiki/Books)
- [Equipment](https://duma-eng.fandom.com/wiki/Equipment)
- [Orbs](https://duma-eng.fandom.com/wiki/Orbs)
- [Torture](https://duma-eng.fandom.com/wiki/Torture)
- [Prisons and Altars](https://duma-eng.fandom.com/wiki/Prisons_and_Altars)
