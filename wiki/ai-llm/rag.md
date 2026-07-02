---
title: RAG（检索增强生成）
type: concept
domain: ai-llm
source: 综合自 sources/ai-llm（Atlan、Karpathy）
date: 2026-06-12
confidence: high
tags: [rag, 向量检索, 知识库, 架构]
links: ["[[llm-wiki-pattern]]", "[[atlan-llm-wiki-vs-rag]]", "[[llm-wiki-vs-rag]]"]
---

# RAG（检索增强生成）

Retrieval-Augmented Generation:向量索引的文档库 + 检索层。LLM 从不载入全部语料,只在查询时检索到的证据上落地回答。在本库中作为 [[llm-wiki-pattern]]的**对照概念**存在。

## 流水线

文档库 → 分块层 → embedding 模型 → 向量数据库(Pinecone / Weaviate / pgvector)→ 检索层(取 top-K)→ LLM 落地综合。

## 与 LLM Wiki 的对比

知识**何时组装**是分水岭:RAG 在**查询时**检索片段;LLM Wiki 在**编译时**预先整合。详见 [[atlan-llm-wiki-vs-rag]] 与综合页 [[llm-wiki-vs-rag]]。

- RAG 优势:知识规模可达百万级文档,无上下文上限;为并发读设计;可近实时重索引。
- RAG 局限:输出质量完全取决于上游数据质量;默认不内建访问控制、新鲜度、血缘;分块与 embedding 策略带来工程开销(分块差、embedding 漂移是典型失败模式)。

## 何时选 RAG

企业规模、动态内容、多用户、监管环境,或语料超出单个上下文窗口(约 5万–10万 token 阈值以上)。个人规模的稳定语料则 LLM Wiki 更优——本库即属此类,故**不采用** RAG。

## 混合方案

二者不互斥:wiki 可作 RAG 之上的高置信"种子"上下文;或双层分离(wiki 持"确知层",RAG 处理"当前语料层");或 wiki 作受治理的元数据层。
