---
title: LLM Wiki 模式
type: concept
domain: ai-llm
source: 综合自 sources/ai-llm 四篇素材
date: 2026-06-12
confidence: high
tags: [llm-wiki, 知识库, 架构, 理念]
links: ["[[karpathy-llm-wiki]]", "[[gbrain]]", "[[saeloun-private-llm-wiki]]", "[[atlan-llm-wiki-vs-rag]]", "[[rag]]", "[[karpathy]]", "[[llm-wiki-vs-rag]]"]
---

# LLM Wiki 模式

由 [[karpathy]] 于 2026 年 4 月提出的个人知识库模式:让 LLM **增量构建并维护一个持久的、互链的 markdown wiki**,介于用户与原始素材之间。本知识库本身就是该模式的一个实例。

## 与 RAG 的本质区别

核心是知识**何时被组装**(详见 [[atlan-llm-wiki-vs-rag]]):

- LLM Wiki = **编译时**组装。素材进来时就读取、提炼、整合进 wiki,知识被"编译一次并保持更新"。
- [[rag]] = **查询时**组装。每次提问才检索片段,"LLM 在每个问题上都从零重新发现知识",没有累积。

> "wiki 是一个持久的、不断累积的产物"——交叉引用已存在,矛盾已标记,综合反映读过的一切。

## 三层架构

| 层 | 内容 | 可变性 |
|---|---|---|
| 原始素材 | 精选源文档(本库 `sources/`) | 不可变,只读 |
| Wiki | LLM 生成的 markdown 页(本库 `wiki/`) | LLM 完全拥有 |
| Schema | 结构/约定/工作流配置(本库 `AGENTS.md`) | 与用户共同演进 |

Schema 是"让 LLM 成为有纪律的维护者而非通用聊天机器人"的关键配置。

## 三个操作

- **Ingest** — 读素材 → 讨论要点 → 写摘要页 → 更新 index/实体/概念页 → 追加 log。单篇可触及 10-15 页。
- **Query** — 找相关页、综合带引用的回答;好回答可归档回 wiki 成新页。
- **Lint** — 巡检矛盾、过期、孤立页、缺失概念页与交叉引用。

## 导航设施

- **index.md**:面向内容的目录,查询时先读,中等规模(~数百页)下替代了 embedding RAG 基础设施。
- **log.md**:按时间倒序、可被 grep 的追加式记录。

## 为何有效

繁琐的不是阅读或思考,而是**簿记**——更新交叉引用、保持摘要当前、跨页一致。人类放弃 wiki 因维护负担超过价值;LLM 不厌倦、不漏更新、能一次触及多文件,使维护成本趋近于零。

## 落地纪律(本库铁律来源)

[[saeloun-private-llm-wiki]] 强调:没有 source/time/confidence,"记忆就只是 vibes";用 `--review` 人工闸门防止"模型偷偷改写记忆";"无产物,不下论断"。

## 实现谱系

同一理念有两个极端:[[karpathy-llm-wiki]] 的极简哲学(纯 markdown + schema)与 [[gbrain]] 的重型工程(TS + Postgres + pgvector + MCP)。本库走极简路线。
