# 知识库索引 (index)

> 内容地图：每个页面一行 + 一句话摘要。查询时先读本文件定位。

## work — 工作项目记录

**综合**
- [[k1-monthly-overview]] — K1 全年经营快照(2025-01至2026-05)：规模持续收缩、靠付费深度撑收入。

**指标(concept)**
- [[k1-revenue-arpc]] — 月流水与 ARPC：17 月趋势，从 1051 万降至 666 万低位。
- [[k1-payment-structure]] — 付费结构：礼包大类、Rlevel 贡献、代币、退款全年趋势。
- [[k1-edau]] — EDAU：从 15.1 万收缩至 5.9 万，高度依赖买量。
- [[k1-dac]] — DAC：从 6.8 万降至 3.8 万；1000刀+超R 稳定在 ~600 人。
- [[k1-new-player-retention-roi]] — 新玩家留存与回本：7日ROI 走弱，回本波动大。
- [[k1-progression-lines]] — 投放线进度：超R 科研满进度 >90%，成长线趋饱和。

## gaming — 游戏行业研究

**概念/规范**
- [[dungeon-maker-framework-pattern]] — Dungeon Maker 式地牢经营框架:每日卡牌路径 + 地牢建设 + 自动战斗 + 局外解锁。
- [[高兼容性风险修改项自检]] — K1 开发规范:哪些改动有新旧版本兼容风险,提交前必查的 8 项清单。

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

**素材摘要**
- [[karpathy-llm-wiki]] — Karpathy gist:模式理念源头。
- [[atlan-llm-wiki-vs-rag]] — Atlan:wiki vs RAG 决策依据。
- [[saeloun-private-llm-wiki]] — Saeloun:隐私优先落地流水线 + 人工审核闸门。
- [[gbrain]] — gbrain:重型工程实现(wikilink 建图 / search+think 双模式)。

**个人经验**
- [[hook-usage-log-pipeline]] — 用 Stop hook 在对话超阈值时自动记日志 + 唤醒总结,沉淀 AI 使用经验。
- [[windows-python-hook-stdout-ascii]] — Windows 下 Python hook 输出中文须用 ASCII 转义,否则 GBK/UTF-8 错位乱码。
