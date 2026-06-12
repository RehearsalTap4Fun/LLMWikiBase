# gbrain —— AI agent 的知识大脑层

> **来源**：https://github.com/garrytan/gbrain
> **作者**：Garry Tan
> **获取日期**：2026-06-12
> **说明**：本文为 AI 转写的结构化摘要，基于仓库 README 与介绍页，非逐字原文。基准数字等未独立核实，以原仓库为准。

## 定位

gbrain 是一个有明确主张的、MIT 许可的"知识大脑"层，供 AI agent 使用。核心卖点："搜索给你原始页面，gbrain 给你答案。" 它在检索之上叠加了综合、知识图谱遍历和缺口分析，让编码/个人 agent 不再"对代码以外的一切失忆"。

两种查询模式定义了它的价值：
- `gbrain search` —— 原始混合排序的页面检索（无 LLM 成本）
- `gbrain think` —— 综合的、带引用的答案，外加一句诚实的"大脑目前还不知道什么"（缺口分析是其差异化特征）

支持多用户"公司大脑"模式，每人只看到登录范围内的数据。

## 与 Karpathy gist 的关系

二者是同一理念的两个极端：Karpathy 的 gist 是极简哲学（纯 markdown + 一份 schema 配置，靠 LLM 直接维护，零依赖）；gbrain 是重型工程系统（TypeScript + Postgres + pgvector + MCP server + 后台 daemon + 定时任务 + 队列），是个可部署的产品。

## 核心循环

信号 → 搜索 → 响应 → 写入 → 自动链接 → 同步。信号探测器在每条 agent 消息上运行，大脑优先查找先于外部 API 调用，自动链接在每次页面写入时触发（纯模式匹配，不调 LLM），定时任务在夜间富化（去重、修引用、找矛盾）。

## Schema Pack（知识库约定）

gbrain 拒绝单一固定布局，提供 schema pack：
- `gbrain-base-v2`（默认）—— 15 类分类法（14 个规范类型 + `note` 兜底）：person、company、media、tweet、social-digest、analysis、atom、concept、source、deal、email、slack、writing、project、note
- `gbrain-base`（旧版 24 类）、`gbrain-recommended`（增加 13 个目录），以及用户自建 pack

## LLM Wiki 模式实现

知识以 markdown 形式存于 git"大脑仓库"（事实来源），同步进 Postgres 供检索；git 删除对应 DB 软删除。自连线知识图谱从 wikilink（如 `[[wiki/people/bob]]`）提取实体引用，写入带类型的边（`attended`、`works_at`、`invested_in`、`founded`、`advises`），全程不调 LLM。支持 Obsidian 风格的裸 `[[note-name]]` 按 basename 解析。

## 架构与能力

- 混合检索：pgvector HNSW + BM25 + 倒数排名融合 + 来源层级加权 + 重排器，三种模式（conservative / balanced / tokenmax）
- Minions：Postgres 原生的持久化任务队列，崩溃安全的两阶段持久化
- 43 个精选 markdown skill，经 `skills/RESOLVER.md` 路由
- 评测框架（LongMemEval、NamedThingBench、跨模态检查）
- 两套引擎共用一个 `BrainEngine` 契约：PGLite（零配置默认，约 5 万页以内）和 Postgres+pgvector（规模化/团队）
- MCP server 暴露 30+ 工具（stdio 与 HTTP），带 OAuth 2.1、scope 门控、限流

## 借鉴要点（对本知识库）

- `[[wikilinks]]` 自动构建知识图谱
- `search`（纯检索，无 LLM 成本）vs `think`（综合 + 缺口分析）双查询模式
- 按 type 分类的 schema（我们采用精简的 6 类，而非 gbrain 的 15 类）
- 定期 lint 找矛盾/孤立页
