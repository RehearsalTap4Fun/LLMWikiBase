---
title: Karpathy LLM Wiki gist（素材摘要）
type: source-summary
domain: ai-llm
source: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
date: 2026-06-12
confidence: high
tags: [llm-wiki, 知识库, 架构, 理念]
links: ["[[llm-wiki-pattern]]", "[[karpathy]]", "[[rag]]", "[[llm-wiki-vs-rag]]"]
---

# Karpathy LLM Wiki gist（素材摘要）

[[karpathy]] 于 2026 年 4 月发布的 gist，是 [[llm-wiki-pattern]]的理念源头。刻意保持抽象——它是一份"理念文件"，意在复制粘贴给 LLM agent，由 agent 与用户协作搭出具体实现。本知识库即据此搭建。

## 核心论断

与标准 [[rag]] 的关键区别：RAG 在查询时检索原始片段，"LLM 在每个问题上都从零重新发现知识"，没有累积；而本模式让 LLM **增量构建并维护一个持久 wiki**——介于用户与原始素材之间的结构化、互链 markdown 文件。

> "wiki 是一个持久的、不断累积的产物。" 交叉引用已经存在，矛盾已被标记，综合反映了读过的一切。

作者比喻："Obsidian 是 IDE；LLM 是程序员；wiki 是代码库。" 分工：用户负责取材、探索、提问；LLM 负责摘要、交叉引用、归档、簿记。

## 三层架构

- **原始素材(Raw sources)** — 精选源文档，不可变，"LLM 只读不改"，是事实来源。
- **Wiki** — LLM 生成的 markdown 文件目录，"LLM 完全拥有这一层"。
- **Schema** — 定义结构/约定/工作流的配置文档(如 AGENTS.md)，"让 LLM 成为有纪律的 wiki 维护者而非通用聊天机器人"。

## 三个操作

- **Ingest** — 投一篇素材：阅读 → 讨论要点 → 写摘要页 → 更新 index → 更新实体/概念页 → 追加 log。"单篇素材可能触及 10-15 个 wiki 页面。"
- **Query** — 找相关页并综合出带引用的回答。关键洞见："好的回答可以作为新页面归档回 wiki"。
- **Lint** — 定期巡检：矛盾、过期论断、孤立页、缺失概念页、缺失交叉引用、可由搜索补全的缺口。

## 索引与日志

- **index.md** — 面向内容的目录，回答查询时先读它；在约 100 篇素材/数百页的中等规模下工作良好，"避免了基于 embedding 的 RAG 基础设施"。
- **log.md** — 按时间倒序、追加式；统一前缀使其可被 unix 工具解析。

## 其他

- 可选 CLI 工具：推荐 qmd(本地 BM25/向量混合搜索)，或自写简单脚本。
- 为何有效：繁琐的不是阅读或思考而是**簿记**；人类放弃 wiki 因维护负担超过价值，而 LLM"不会厌倦、不会忘记更新交叉引用、能一次触及 15 个文件"。
- 渊源：Vannevar Bush 的 Memex(1945)——私有、主动策划、文档间连接与文档本身同等重要；"他没能解决的是谁来维护，LLM 解决了。"

## 在本库中的角色

四篇参考之首，提供整体架构。落地细节由 [[saeloun-private-llm-wiki]] 补充，规模边界由 [[atlan-llm-wiki-vs-rag]] 界定，重型工程对照见 [[gbrain]]。
