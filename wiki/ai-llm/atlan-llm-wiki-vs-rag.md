---
title: Atlan：LLM Wiki vs RAG（素材摘要）
type: source-summary
domain: ai-llm
source: https://atlan.com/know/llm-wiki-vs-rag-knowledge-base/
date: 2026-06-12
confidence: high
tags: [llm-wiki, rag, 架构选型, 规模, 治理]
links: ["[[llm-wiki-pattern]]", "[[rag]]", "[[llm-wiki-vs-rag]]", "[[karpathy-llm-wiki]]"]
---

# Atlan：LLM Wiki vs RAG（素材摘要）

Emily Winks(Atlan,2026 年 4 月更新)的对比文章,为"个人规模该选 [[llm-wiki-pattern]] 还是 [[rag]]"提供**决策依据**。本库的架构选型(纯 wiki、零向量库)即据此判定。

## 核心区分:编译时 vs 查询时

根本差别在于知识**何时被组装**:

- **LLM wiki** — 把结构化 markdown 索引直接载入上下文,模型预先读取,无需向量库(**编译时**组装)。假设知识有界且稳定。
- **RAG** — 在查询那一刻从向量库检索语义相关片段(**查询时**组装)。假设知识庞大、动态、多领域。

强调这是规模假设的差别,不是智能的差别。

## 5万–10万 Token 阈值

这是 wiki 方案停止可靠工作的临界点。阈值以下,wiki 在简单性与 token 效率上胜出(最高省 95%);超过后索引放不进上下文,被迫引入检索层。token 效率优势在与优化后的 RAG 对比时收窄,超过单上下文窗口后消失。

## 权衡(节选)

| 维度 | LLM Wiki | RAG |
|---|---|---|
| 知识规模 | ~100–200 篇 | 百万级文档 |
| 基础设施 | 零(markdown) | 向量库 + embedding 流水线 + 检索层 |
| 搭建时间 | 数小时 | 数天到数周 |
| 失败模式 | 上下文溢出、内容过期、无访问控制 | 分块差、embedding 漂移、数据未治理 |
| 最适 | 稳定、精选、个人规模 | 动态、大规模、企业级 |

## 何时用哪个

- **从 wiki 起步**:个人研究、约 150 页内稳定语料、单人、零基础设施约束。
- **从 RAG 起步**:企业规模、动态内容、多用户、监管环境、超上下文限制。
- **混合**:wiki 作为高置信"种子"上下文 / 双层分离(确知层 vs 当前语料层)/ wiki 作为受治理元数据层。

## 关键结论

- 约 5万–10万 token 以下,wiki 在 token 效率上胜出;RAG 在企业规模胜出。
- 真正的企业问题不是 wiki vs RAG,而是源数据是否足够可信。
- 访问控制、新鲜度、并发是**治理问题**,不是检索架构问题。
- 底线:"**规模决定架构,治理决定结果。**" Karpathy 明确把 wiki 限定在个人研究者范围,其局限是设计取舍而非缺陷。

## 在本库中的角色

本项目是**个人**知识库,规模几乎必然落在阈值以下,因此采用纯 LLM Wiki(markdown + 轻脚本)是正确选择,无需向量库。跨素材的综合判断见 [[llm-wiki-vs-rag]]。
