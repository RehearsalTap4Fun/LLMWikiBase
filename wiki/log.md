# 操作日志 (log)

> 追加式、按时间倒序。条目格式可 grep：`## [YYYY-MM-DD] 动作 — 摘要`

## [2026-06-16] ingest — 新增 3 篇素材(ai-llm hook 经验 ×2 + gaming 兼容自检 ×1)
- 来源:sources/ai-llm/hook-usage-log-pipeline、windows-python-hook-stdout-ascii;sources/gaming/高兼容性风险的修改项自检
- 新建 3 页:
  - ai-llm source-summary ×2:hook-usage-log-pipeline、windows-python-hook-stdout-ascii(两页互链,均个人亲历经验标 high)
  - gaming concept ×1:高兼容性风险修改项自检(K1 开发规范,补全「新旧版本兼容/团队规范沉淀」背景后标 high)
- 更新 index.md:ai-llm 新增「个人经验」小组(2 条)、gaming 分区从「暂无」改为 1 条
- 边界:gaming 页不硬链 work 域机密页,仅正文点明「源自 K1 实践」,避免协作者侧悬空链接
- lint(ai-llm)通过

## [2026-06-12] ingest — K1 月报补全全年趋势(2025-01 至 2026-05)
- 来源:sources/work/ 全 17 期月报
- 将 7 个 work 指标页从"仅最新两月"扩展为全年趋势:
  - revenue-arpc / edau / dac / payment-structure / retention-roi 补 17 月数据表
  - progression-lines 补科研/图鉴满进度长期曲线
  - monthly-overview 改为全年经营快照(全年大势 + 关键转折 + 近月对照)
- 更新 index.md work 分区摘要
- 核心结论:规模一年收缩 61%(EDAU 15.1万→5.9万)、流水千万→600万,靠付费深度(ARPC/超R)撑收入;2026-01 运营控制拉收致流水 -25.6%

## [2026-06-12] ingest — K1 数据月报试点(2026-04, 2026-05)
- 来源:sources/work/ 的 k1-月报-2026-04 / 2026-05(17 份已全部转 md,机密仅本地)
- 新建 7 页(均在 wiki/work/,仅本地不推送):
  - concept ×6:k1-revenue-arpc、k1-payment-structure、k1-edau、k1-dac、k1-new-player-retention-roi、k1-progression-lines
  - synthesis ×1:k1-monthly-overview
- 更新 wiki/index.md 的 work 分区(7 条目)
- 试点范围:仅最新两月;后续可补 2025-01 起的全年趋势
- 置信度 high(来自机密月报原文数字)

## [2026-06-12] ingest — AI/LLM 四篇 LLM Wiki 素材
- 来源:sources/ai-llm/ 的 karpathy / atlan / saeloun / gbrain 四篇
- 新建 8 页(均在 wiki/ai-llm/):
  - source-summary ×4:karpathy-llm-wiki、atlan-llm-wiki-vs-rag、saeloun-private-llm-wiki、gbrain
  - concept ×2:llm-wiki-pattern、rag
  - entity ×1:karpathy
  - synthesis ×1:llm-wiki-vs-rag(规模决定架构,双源支撑标 high)
- 更新 wiki/index.md 的 ai-llm 分区(8 条目)
- 置信度:gbrain/saeloun/karpathy(实体)标 medium(数字未核实或履历未覆盖),其余 high

## [2026-06-11] init — 知识库初始化
- 建立三层结构与 work/gaming/ai-llm 三域分区
- 添加 search.py / lint.py 工具
