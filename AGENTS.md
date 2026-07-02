# AGENTS.md — 知识库维护约定

> 每次开始知识库相关工作前，先读本文件。

## 这是什么

个人 LLM Wiki 知识库。三层结构：
- `sources/` — 原始素材，**只读不改**。
- `wiki/` — 你维护的 markdown 知识页面，按域分区：`work`(工作项目) / `gaming`(游戏行业研究) / `ai-llm`(AI/LLM 学习)。
- `AGENTS.md`(本文件) — 维护约定。

辅助工具(本地、不联网)：
- `python tools/search.py "关键词" [--domain D] [--type T] [--top N]` — BM25 搜索。
- `python tools/lint.py [--domain D]` — 健康检查。

## 页面 frontmatter 规范

每个 wiki 页面顶部必须有 YAML frontmatter，六个字段必填：

```yaml
---
title: 实体或概念名
type: project | concept | entity | source-summary | synthesis | log
domain: work | gaming | ai-llm
source: <来源 URL / 文件名 / "对话">
date: 2026-06-11
confidence: high | medium | low
tags: [标签1, 标签2]
links: ["[[other-page]]"]
---
```

### type 分类
- `project` — 工作项目（多见于 work）
- `concept` — 概念（算法、商业模式、游戏机制等）
- `entity` — 实体（公司、人、产品、具体游戏、模型）
- `source-summary` — 单篇素材摘要
- `synthesis` — 跨素材综合洞见
- `log` — 仅用于 log.md

### 链接
页面间用 `[[页面名]]` 互链（页面名 = 文件名去扩展名）。**文件名应全库唯一**，避免不同域下同名页面在链接解析时冲突。 链接可写在正文中，也可写在 frontmatter 的 `links` 字段（如 `links: ["[[页面名]]"]`），两者 lint 均会识别。

## 三个工作流

### Ingest（投喂素材）
1. 用户把素材放入 `sources/<域>/` 或贴给你。若 `git status` 出现未跟踪的 `wiki/` 文件,先跑 `git log --oneline -- <file>` 判定来历——历史遗留未提交产物不属 Ingest 范围,避免与新素材混淆。
2. 读完先与用户讨论要点。
3. **提议**：写哪个摘要页、更新哪些关联页（列清单）。
4. **写入前反向找链**：grep 同域已有页面的 `tags`，与新页 tags 有重叠就**主动提议**在 `links` 里互挂(双向)，由用户裁决；硬造链不可取，宁缺勿滥。目的是避免同域孤立页随时间累积。
5. **用户确认后才写入。**
6. 在 `wiki/log.md` 追加一条记录。

### Query（提问）
1. 先读 `wiki/index.md` 定位相关页（或用 search.py）。
2. 读取相关页面。
3. 给出**带引用**的回答（指明依据哪些页）。
4. 若产生新洞见，提议是否存为 `synthesis` 页。

### Lint（健康检查）
1. 运行 `tools/lint.py` 或手动巡检。
2. 报告断链/孤立页/缺字段/超期/低置信度。
3. 只读不自动改，交用户决定如何处理。

## 三条铁律

1. **无证据不标 high。** 仅单条信息支撑的结论标 `low`。
2. **不偷偷改写记忆。** 写入/修改前先列清单给用户确认。
3. **回答带引用。** 指明来源页。

## 何时建新页 vs 更新旧页

- 已有对应实体/概念页 → 更新该页，刷新 `date`。
- 全新主题 → 建新页，并在相关页的 `links` 中互相挂上。
- 跨多页的综合结论 → 建 `synthesis` 页。
- 每次写入后同步更新 `wiki/index.md` 的条目。
