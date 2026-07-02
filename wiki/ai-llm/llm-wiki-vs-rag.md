---
title: LLM Wiki vs RAG：规模决定架构
type: synthesis
domain: ai-llm
source: 综合自 Atlan、Karpathy、gbrain、Saeloun 四篇素材
date: 2026-06-12
confidence: high
tags: [llm-wiki, rag, 架构选型, 规模, 综合]
links: ["[[llm-wiki-pattern]]", "[[rag]]", "[[atlan-llm-wiki-vs-rag]]", "[[karpathy-llm-wiki]]", "[[gbrain]]", "[[saeloun-private-llm-wiki]]"]
---

# LLM Wiki vs RAG：规模决定架构

> 跨四篇素材的综合洞见。核心结论由 [[atlan-llm-wiki-vs-rag]] 与 [[karpathy-llm-wiki]] 双源支撑,故标 high。

## 一句话

**规模决定架构,治理决定结果。** [[llm-wiki-pattern]] 与 [[rag]] 不是智能的差别,而是规模假设的差别——选哪个取决于语料能否放进上下文窗口。

## 决策轴:5万–10万 token 阈值

这是 wiki 方案停止可靠工作的临界点(见 [[atlan-llm-wiki-vs-rag]]):

- **阈值以下** — 索引能整体载入上下文,wiki 在简单性与 token 效率上胜出(最高省 95%),零基础设施。
- **阈值以上** — 索引放不进上下文,被迫引入检索层,RAG 的规模优势显现,wiki 的 token 优势消失。

| | LLM Wiki | RAG |
|---|---|---|
| 组装时机 | 编译时(素材进来即整合) | 查询时(每次提问才检索) |
| 适用规模 | ~100–200 篇 / 个人 | 百万级 / 企业 |
| 基础设施 | 零 | 向量库 + 流水线 |
| 知识累积 | 持久、复利 | 每次从零重新发现 |

## 对本知识库的判断

本项目是**个人**知识库,规模几乎必然落在阈值以下 → 采用纯 LLM Wiki(markdown + 轻量脚本 search.py/lint.py),**不引入向量库/RAG**。当规模超过约 100–200 页或需多人协作时,再评估向 [[gbrain]] 式工程或混合方案演进。

## 三个维度,各有归属

四篇素材在不同层面互补,拼出完整图景:

1. **理念**(为什么这么做)— [[karpathy-llm-wiki]]:LLM 当编译器,簿记成本趋零使 wiki 可持续。
2. **选型**(规模够不够)— [[atlan-llm-wiki-vs-rag]]:阈值以下选 wiki,以上选 RAG。
3. **纪律**(怎么不出错)— [[saeloun-private-llm-wiki]]:source/time/confidence 三件套、`--review` 人工闸门、"无产物不下论断"。
4. **演进**(将来怎么扩)— [[gbrain]]:wikilink 自动建图、search/think 双模式、定期富化,是规模化后的参照实现。

## 关键提醒

Atlan 指出:访问控制、新鲜度、并发是**治理问题**,不是检索架构问题。换言之,即便选了 wiki,内容过期与无访问控制仍是其固有失败模式——靠 [[saeloun-private-llm-wiki]] 式的元数据纪律与定期 lint 来缓解,而非靠换架构。
