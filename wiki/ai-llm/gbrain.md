---
title: gbrain（素材摘要）
type: source-summary
domain: ai-llm
source: https://github.com/garrytan/gbrain
date: 2026-06-12
confidence: medium
tags: [llm-wiki, 知识库, 工程实现, 知识图谱, mcp]
links: ["[[llm-wiki-pattern]]", "[[karpathy-llm-wiki]]", "[[rag]]"]
---

# gbrain（素材摘要）

Garry Tan 的 MIT 许可"知识大脑"层(供 AI agent 使用)。是 [[llm-wiki-pattern]]的**重型工程实现**一端，与 [[karpathy-llm-wiki]]的极简哲学构成同一理念的两个极端。

> 基准数字等未独立核实，以原仓库为准——故本页 confidence 标 medium。

## 定位与双模式

卖点："搜索给你原始页面，gbrain 给你答案。" 在检索之上叠加综合、知识图谱遍历、缺口分析。两种查询模式定义其价值：

- `gbrain search` — 原始混合排序检索(无 LLM 成本)
- `gbrain think` — 综合的带引用答案 + 一句诚实的"大脑目前还不知道什么"(缺口分析是差异化特征)

## 核心循环

信号 → 搜索 → 响应 → 写入 → 自动链接 → 同步。信号探测器在每条 agent 消息上运行，大脑优先查找先于外部 API；自动链接在每次写入时触发(纯模式匹配，不调 LLM)；定时任务夜间富化(去重、修引用、找矛盾)。

## 与本库相关的实现细节

- 知识以 markdown 存于 git"大脑仓库"(事实来源)，同步进 Postgres 供检索；git 删除对应 DB 软删除。
- 自连线知识图谱从 wikilink(形如 `wiki/people/bob` 的双方括号链接)提取实体引用，写入带类型的边(`works_at`、`founded`、`invested_in` 等)，全程不调 LLM;支持 Obsidian 风格裸 `note-name` 双方括号链接按 basename 解析。
- Schema pack：默认 `gbrain-base-v2` 为 15 类分类法(person/company/concept/source/project/note 等)。
- 混合检索:pgvector HNSW + BM25 + 倒数排名融合 + 重排器。
- 技术栈:TypeScript + Postgres + pgvector + MCP server(30+ 工具) + 后台 daemon + 任务队列。

## 借鉴要点

- wikilink 双方括号链接自动建图 → 本库采用同样的双方括号互链约定。
- search(纯检索) vs think(综合 + 缺口分析)双模式 → 对应本库 Query 工作流。
- 按 type 分类的 schema → 本库采用精简 6 类而非 gbrain 的 15 类。
- 定期 lint 找矛盾/孤立页 → 本库 `tools/lint.py`。

本库刻意走 [[karpathy-llm-wiki]] 极简路线(纯 markdown + 轻脚本)，gbrain 代表规模化后可演进的方向。
