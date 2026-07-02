---
title: Andrej Karpathy
type: entity
domain: ai-llm
source: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
date: 2026-06-12
confidence: medium
tags: [人物, llm-wiki, 理念提出者]
links: ["[[llm-wiki-pattern]]", "[[karpathy-llm-wiki]]"]
---

# Andrej Karpathy

[[llm-wiki-pattern]]的提出者。2026 年 4 月发布 [[karpathy-llm-wiki]],描述了用 LLM 增量构建并维护个人 markdown 知识库的模式,是本知识库的设计源头。

## 与本库相关的观点

- 提出三层架构(原始素材 / wiki / schema)与三操作(ingest / query / lint)。
- 比喻:"Obsidian 是 IDE;LLM 是程序员;wiki 是代码库。"
- 把 LLM 当知识"编译器"——把原始输入综合成结构化文章,而非仅查询。
- 明确把该模式限定在**个人研究者**范围;其规模局限(约 5万–10万 token 阈值,见 [[atlan-llm-wiki-vs-rag]])是设计取舍而非缺陷。

> 注:本页仅记录与 LLM Wiki 模式相关的信息;Karpathy 的其他履历(如深度学习领域工作)本库素材未覆盖,故 confidence 标 medium。
