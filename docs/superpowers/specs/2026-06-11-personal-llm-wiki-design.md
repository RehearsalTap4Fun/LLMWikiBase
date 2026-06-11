# 个人 LLM Wiki 知识库 — 设计文档

- 日期：2026-06-11
- 形态：方案 B（markdown 为核心 + 少量本地 Python 脚本）
- 运行时：Python 3.10.6（已确认本机可用）
- 搜索：BM25 纯关键词检索（不使用向量 / RAG）

## 背景与参考

本设计基于四篇参考资料的综合：

| 参考 | 角色 | 采纳的要点 |
|---|---|---|
| Karpathy LLM Wiki gist | 理念源头 | 三层架构（原始素材 / wiki / schema），LLM 作为知识"编译器"与维护者 |
| garrytan/gbrain | 重型实现 | `[[wikilinks]]` 自动构建知识图谱、search vs query 双模式、按 type 分类、定期 lint |
| Saeloun 博客（LLM Wiki + gbrain + gstack） | 落地流水线 | 隐私优先（数据留本地）、元数据三件套（来源/时间/置信度）、人工审核闸门、无证据不标"已验证" |
| Atlan《LLM Wiki vs RAG》 | 决策依据 | "规模决定架构，治理决定结果"；个人规模（<100~200 页）纯文件 + 关键词检索即足够，无需 RAG |

**核心结论**：这是个人知识库，规模几乎必然落在 5万~10万 token 阈值以下，因此采用 Karpathy 式纯 LLM Wiki，叠加方案 B 的轻量 Python 工具。明确不引入向量数据库 / RAG / MCP / 数据库 / 多用户。

## 内容范围

知识库服务三个内容方向，用顶层子目录隔离，互不污染：

- `work` — 个人工作项目记录
- `gaming` — 游戏行业研究
- `ai-llm` — AI / LLM 的持续学习

## 1. 整体架构（三层 + 脚本工具）

```
KnowledgeBase/
├── AGENTS.md            # Schema 层：维护约定与工作流（agent 每次工作前先读）
├── sources/             # 原始素材层：用户投喂的原文，agent 只读不改
│   ├── work/
│   ├── gaming/
│   └── ai-llm/
├── wiki/                # Wiki 层：agent 编译维护的知识页面
│   ├── work/            #   工作项目记录
│   ├── gaming/          #   游戏行业研究
│   ├── ai-llm/          #   AI/LLM 学习
│   ├── index.md         #   内容地图：全部页面 + 一句话摘要（查询时先读）
│   └── log.md           #   时间线：追加式操作日志（可 grep）
├── tools/               # Python 脚本（方案 B）
│   ├── search.py        #   BM25 关键词搜索
│   ├── lint.py          #   健康检查
│   └── requirements.txt
└── docs/superpowers/specs/   # 本设计文档存放处
```

`sources/` 与 `wiki/` 都按 `work` / `gaming` / `ai-llm` 三个域分区，使搜索和 lint 可按域过滤。

## 2. 知识页面结构与元数据

每个 wiki 页面是一个 markdown 文件，顶部 YAML frontmatter 采用元数据方案：

```markdown
---
title: 实体或概念名
type: project | concept | entity | source-summary | synthesis | log
domain: work | gaming | ai-llm
source: <来源 URL / 文件名 / "对话">   # 缺来源即视为"凭感觉"，应降低 confidence
date: 2026-06-11                        # 最后更新日期（ISO 格式 YYYY-MM-DD）
confidence: high | medium | low         # 证据强度
tags: [标签1, 标签2]
links: ["[[other-page]]"]               # 双向链接，构成知识图谱
---

正文：摘要、要点、与其他页面的关联……
```

### type 分类定义（精简 6 类，不照搬 gbrain 的 15 类）

- `project` — 工作项目（多见于 work 域）
- `concept` — 概念（如某算法、某商业模式、某游戏机制）
- `entity` — 实体（公司、人、产品、具体游戏、模型）
- `source-summary` — 单篇素材的摘要页
- `synthesis` — 跨素材综合产生的洞见页
- `log` — 日志条目（仅用于 log.md）

### wikilinks 约定

- 页面之间用 `[[页面名]]` 互链（页面名 = 不含扩展名的文件名 basename）。
- `lint.py` 据此发现断链（指向不存在的页）与孤立页（无人链接且不链接他人）。

## 3. 三个核心工作流（写入 AGENTS.md）

### ① Ingest（投喂素材）
1. 用户把素材放入 `sources/<域>/` 或直接贴给 agent。
2. agent 读完，先与用户讨论要点。
3. agent **提议**：写哪个摘要页、更新哪些关联页（列出清单）。
4. **用户确认后** agent 才写入。
5. 追加一条 `log.md` 记录。

### ② Query（提问）
1. agent 先读 `index.md` 定位相关页。
2. 读取这些页面。
3. 给出**带引用**的回答（标明依据哪些页）。
4. 若本次综合产生新洞见，提议是否存为 `synthesis` 页（使探索可累积）。

### ③ Lint（健康检查）
1. 运行 `tools/lint.py` 或 agent 手动巡检。
2. 报告：断链、孤立页、缺 frontmatter 字段、`confidence: low` 待补证清单、超期未更新的陈旧页、潜在矛盾。
3. 只读不自动改，问题交由用户与 agent 决定如何处理。

### 贯穿三条铁律（来自 Saeloun）
- 无证据不标 `confidence: high`；仅单条信息支撑的结论标 `low`。
- 修改 / 写入记忆前先列清单给用户确认，不"偷偷改写"。
- 回答带引用，指明来源页。

## 4. Python 工具（方案 B）

两个脚本均为**本地纯文件操作，不联网、不发送任何数据**，符合"私有语料留在本地"原则。

### tools/search.py — BM25 全文关键词搜索
- 依赖：`rank-bm25`、`pyyaml`
- 行为：扫描 `wiki/**/*.md`，解析 frontmatter + 正文，构建 BM25 索引。
- 用法：`python tools/search.py "关键词" [--domain gaming] [--type concept] [--top 5]`
- 输出：匹配页面路径 + 标题 + 命中片段，按相关度排序。
- 索引策略：每次运行时即时构建（个人规模下无需持久化索引；如后续页面数增多可再优化）。

### tools/lint.py — 健康检查
- 依赖：仅 Python 标准库 + `pyyaml`（复用 search 的依赖；frontmatter 解析需要）。
- 检查项：
  - 断链：`[[x]]` 指向不存在的页
  - 孤立页：无人链接且不链接他人
  - frontmatter 缺字段（title/type/domain/source/date/confidence 必填）
  - `date` 超期（默认阈值可配置，如 180 天）
  - `confidence: low` 清单（待补证）
- 用法：`python tools/lint.py [--domain work]`
- 输出：分类问题报告，只读不自动改。

### tools/requirements.txt
```
rank-bm25
pyyaml
```

## 5. AGENTS.md（Schema 层）的作用

让 agent 成为"有纪律的 wiki 维护者"而非通用聊天机器人。内容包含：
- 目录约定
- frontmatter 规范
- type 分类定义
- 三个工作流（ingest / query / lint）的步骤
- 三条铁律
- 何时建新页 vs 更新旧页
- 如何写 `[[links]]`

**约定：agent 每次开始知识库工作前先读 AGENTS.md。**

## 6. 演进路径（YAGNI，现在不做）

明确**现在不做**、留作未来触发的能力：
- 语义 / 向量检索（embedding）
- MCP server
- 数据库（SQLite / Postgres）
- 多用户 / 访问控制
- 自动化定时 enrich 任务

触发条件：当知识库规模超过约 100~200 页、或需要多人协作时再评估演进。Atlan 的结论支持此判断：个人规模下纯文件 + 关键词检索已足够。

## 验证方式

- `search.py`：建几个示例页面后，按关键词检索能命中预期页面，`--domain` / `--type` 过滤生效。
- `lint.py`：故意制造一个断链页和一个缺字段页，确认能被报告出来。
- 运行 `pip install -r tools/requirements.txt` 能成功安装依赖。

## 初始交付物清单

1. 目录骨架（sources/、wiki/ 及各域子目录、tools/）
2. `AGENTS.md`
3. `wiki/index.md`（空模板）与 `wiki/log.md`（空模板）
4. `tools/search.py`、`tools/lint.py`、`tools/requirements.txt`
5. 每个域可放一个示例页面用于验证工具（可选）
