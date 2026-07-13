# 知识库索引 (index)

> 内容地图：每个页面一行 + 一句话摘要。查询时先读本文件定位。

## work — 工作项目记录

**综合**
- [[k1-monthly-overview]] — K1 全年经营快照(2025-01至2026-05)：规模持续收缩、靠付费深度撑收入。
- [[k1-activity-monetization-2026h1]] — 2026H1 活动与付费综合判断：节日仍有真增量，但付费价值感、L1/L2 DAC 下滑和新玩家单价才是底盘风险。
- [[k1-live-activity-patterns-2026h1]] — K1 2026H1 活动机制归纳：主题入口、通行证、商店、转盘/棋盘、排行和充值触点是近期活动复用骨架。

**项目组 wiki 口径**
- [[k1-project-knowledge-map]] — Confluence `K1 游戏知识` 页面树盘点：活动、FAQ、付费、KVK 是主干，`需删除` 和旧/过期页默认排除。
- [[k1-confluence-routing]] — 未摄取内容路由表：本地查不到时按分支去 Confluence 找，跟踪各分支摄取状态。
- [[k1-cs-faq-current]] — K1 客服 FAQ 当前口径：守卫币、领主装备、联盟跨服召集、新玩家保护等可答复边界。
- [[k1-kvk-burning-expedition]] — K1 燃烧的远征/KVK 口径：名称、联盟规则、安全区、女神系统和客服答复边界。
- [[k1-paid-products-current]] — K1 付费产品当前口径：守卫币、精英卡、成长基金、商会补给、首充等产品边界。

**素材摘要**
- [[work-weekly-2026-06-08]] — 2026-06-08 至 06-14 周报：世界杯主题活动、巨龙培育、周年庆验收与 KVK 后续目标。
- [[work-dingtalk-logs-2026-h1]] — 2026H1 钉钉日报归档：118 条日志串起联盟对决、SVS/KVK、巨龙培育、世界杯主题活动正式配置、手感调优、双操作模式与 AI 协作。
- [[work-dingtalk-logs-2026-h2]] — 2026H2 钉钉日报归档种子页：07-01 承接世界杯主体活动引导、AI 难度调整与双操作模式验收。
- [[k1-satisfaction-2026-h1]] — K1 2026H1 满意度母报告：付费体验最低，礼包性价比与付费活动是最低三级指标。
- [[k1-payment-experience-decline-2026-h1]] — 2026H1 付费体验下降归因：不满集中在“花钱不值”，俄语区、新玩家第一印象和边付边骂人群风险突出。
- [[k1-wilderness-hunting-return-analysis]] — 荒野狩猎回归分析：活动可拉 PVE 与在线，但付费率/ARPPU 无系统性抬升。
- [[k1-no-holiday-event-revenue-forecast]] — 不做节日活动流水推算：未来 6 个月净少赚约 $5.22M，但中老玩家 DAC 下滑是更长期风险。

**指标(concept)**
- [[k1-revenue-arpc]] — 月流水与 ARPC：17 月趋势，从 1051 万降至 666 万低位；补节日活动流水推算入口。
- [[k1-payment-structure]] — 付费结构：礼包大类、Rlevel 贡献、代币、退款全年趋势；补付费体验满意度风险。
- [[k1-edau]] — EDAU：从 15.1 万收缩至 5.9 万，高度依赖买量。
- [[k1-dac]] — DAC：从 6.8 万降至 3.8 万；补 open_udid 设备口径 DAC 与 L1/L2 cohort 风险。
- [[k1-new-player-retention-roi]] — 新玩家留存与回本：7日ROI 走弱，回本波动大；补新玩家付费价值感与单价下滑。
- [[k1-progression-lines]] — 投放线进度：超R 科研满进度 >90%，成长线趋饱和。

## gaming — 游戏行业研究

**项目/方案**
- [[k1-new-server-map-plan]] — K1 新服大地图重构策划案 v0.6：用 KVK 方格/堡垒/王座骨架重构新服原服地图,21 天赛季节奏对标 KVK 但省 7 天匹配。
- [[k1-new-map-payment-growth-attribution]] — D23 新地图回归付费成长系数拆解:D30~D60 最大涨幅全靠 KVK 从 D28 推迟到 D43,首周涨幅与地图机制无关(素材/内容驱动)。
- [k1-new-server-map-brief.html](../sources/gaming/k1-new-server-map/k1-new-server-map-brief.html) — 上述策划案的非开发职能速览页(单文件 HTML,含地图 SVG 示意图与 FAQ;分发版:图片已内嵌 base64,1.4MB,双击可开)。
- [k1-new-server-map-brief.template.html](../sources/gaming/k1-new-server-map/k1-new-server-map-brief.template.html) — 上一速览页的编辑模板(引用外部图片,便于修改;修改后可用 Python 一键内嵌图片再另存分发版)。

**概念/规范**
- [[dungeon-maker-framework-pattern]] — Dungeon Maker 式地牢经营框架:每日卡牌路径 + 地牢建设 + 自动战斗 + 局外解锁。
- [[高兼容性风险修改项自检]] — K1 开发规范:哪些改动有新旧版本兼容风险,提交前必查的 8 项清单。
- [[双模式难度故意不对齐]] — 多模式并行系统设计模式：偏向 + 切换零代价 = 玩家自学场景-模式映射。

**素材摘要**
- [[dungeon-maker-reference-resource]] — Dungeon Maker 参考资源包:本地 JSON 配置物料与框架说明,用于后续开发参考。

## ai-llm — AI/LLM 学习

**概念**
- [[llm-wiki-pattern]] — LLM Wiki 模式:三层架构 + 三操作,LLM 当知识"编译器"做簿记。
- [[rag]] — RAG 检索增强生成,LLM Wiki 的对照概念(查询时组装)。

**实体**
- [[karpathy]] — Andrej Karpathy,LLM Wiki 模式提出者。

**综合**
- [[llm-wiki-vs-rag]] — 规模决定架构:个人规模为何选纯 wiki 而非 RAG(5万–10万 token 阈值)。
- [[ai-claude-workflow-lessons]] — AI 工作流经验:Claude/Codex 配置工程、spec grounding、审查线程、开发资产四件套与 clean checkout 护栏。

**素材摘要**
- [[karpathy-llm-wiki]] — Karpathy gist:模式理念源头。
- [[atlan-llm-wiki-vs-rag]] — Atlan:wiki vs RAG 决策依据。
- [[saeloun-private-llm-wiki]] — Saeloun:隐私优先落地流水线 + 人工审核闸门。
- [[gbrain]] — gbrain:重型工程实现(wikilink 建图 / search+think 双模式)。

**个人经验**
- [[hook-usage-log-pipeline]] — 用 Stop hook 在对话超阈值时自动记日志 + 唤醒总结,沉淀 AI 使用经验。
- [[windows-python-hook-stdout-ascii]] — Windows 下 Python hook 输出中文须用 ASCII 转义,否则 GBK/UTF-8 错位乱码。
- [[windows-python3-store-stub-trap]] — Windows python3 命令指向 Store 空壳,与 pip 装包环境不一致,需用完整路径调用真实 Python。
- [[dingtalk-md-escape-diff]] — 钉钉文档与本地 md 双向同步的 GFM 转义差异及反转义脚本。
