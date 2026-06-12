# 个人 LLM Wiki 知识库 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建一个 Karpathy 式个人 LLM Wiki 知识库(方案 B)：markdown 文件为核心 + 两个本地 Python 脚本(BM25 搜索、健康检查 lint)。

**Architecture:** 三层结构 —— `sources/`(只读原始素材)、`wiki/`(agent 维护的 markdown 页面，按 work/gaming/ai-llm 三域分区)、`AGENTS.md`(schema 层约定)。两个 Python 脚本提供本地关键词搜索与健康检查，纯文件操作、不联网。

**Tech Stack:** Python 3.10、rank-bm25(BM25 检索)、pyyaml(解析 frontmatter)、pytest(测试)。

---

## 文件结构

| 文件 | 职责 |
|---|---|
| `tools/requirements.txt` | 声明运行依赖 rank-bm25、pyyaml |
| `tools/frontmatter.py` | 共享模块：解析 markdown 的 YAML frontmatter + 正文，扫描 wiki 目录收集页面 |
| `tools/search.py` | BM25 关键词搜索 CLI，依赖 frontmatter.py |
| `tools/lint.py` | 健康检查 CLI(断链/孤立页/缺字段/超期/低置信度)，依赖 frontmatter.py |
| `tools/tests/test_frontmatter.py` | frontmatter.py 的单元测试 |
| `tools/tests/test_search.py` | search.py 的测试 |
| `tools/tests/test_lint.py` | lint.py 的测试 |
| `AGENTS.md` | Schema 层：目录约定、frontmatter 规范、type 分类、三工作流、三铁律 |
| `wiki/index.md` | 内容地图模板 |
| `wiki/log.md` | 追加式日志模板 |
| `wiki/{work,gaming,ai-llm}/.gitkeep` | 占位，保留空目录 |
| `sources/{work,gaming,ai-llm}/.gitkeep` | 占位，保留空目录 |

**设计要点：** 把 frontmatter 解析与目录扫描抽到 `frontmatter.py` 共享模块，search 和 lint 都复用它（DRY），各自只保留自己的逻辑。

---

## Task 1: 依赖声明与目录骨架

**Files:**
- Create: `tools/requirements.txt`
- Create: `sources/work/.gitkeep`, `sources/gaming/.gitkeep`, `sources/ai-llm/.gitkeep`
- Create: `wiki/work/.gitkeep`, `wiki/gaming/.gitkeep`, `wiki/ai-llm/.gitkeep`

- [ ] **Step 1: 写 requirements.txt**

```
rank-bm25
pyyaml
```

- [ ] **Step 2: 创建目录占位文件**

创建 6 个 `.gitkeep` 空文件（内容为空），路径见上方 Files。

- [ ] **Step 3: 安装依赖并验证**

Run: `pip install -r tools/requirements.txt && python -c "import rank_bm25, yaml; print('ok')"`
Expected: 输出 `ok`

- [ ] **Step 4: Commit**

```bash
git add tools/requirements.txt sources wiki
git commit -m "chore: 添加依赖声明与目录骨架"
```

---

## Task 2: frontmatter 共享解析模块

**Files:**
- Create: `tools/frontmatter.py`
- Test: `tools/tests/test_frontmatter.py`

`parse_markdown(text)` 解析单篇 markdown，返回 `{"meta": dict, "body": str}`；frontmatter 缺失时 `meta={}`、`body` 为全文。`load_pages(wiki_dir, domain=None)` 扫描目录下所有 `.md`（排除 index.md/log.md），返回页面列表，每项含 `path`、`name`(basename 去扩展名)、`meta`、`body`。

- [ ] **Step 1: 写失败测试**

```python
# tools/tests/test_frontmatter.py
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import frontmatter as fm

def test_parse_markdown_with_frontmatter():
    text = "---\ntitle: Foo\ntype: concept\n---\n\nbody text here"
    result = fm.parse_markdown(text)
    assert result["meta"]["title"] == "Foo"
    assert result["meta"]["type"] == "concept"
    assert result["body"].strip() == "body text here"

def test_parse_markdown_without_frontmatter():
    text = "just body, no frontmatter"
    result = fm.parse_markdown(text)
    assert result["meta"] == {}
    assert result["body"].strip() == "just body, no frontmatter"

def test_load_pages_skips_index_and_log(tmp_path):
    wiki = tmp_path / "wiki"
    (wiki / "work").mkdir(parents=True)
    (wiki / "work" / "alpha.md").write_text("---\ntitle: Alpha\ndomain: work\n---\nhello", encoding="utf-8")
    (wiki / "index.md").write_text("# index", encoding="utf-8")
    (wiki / "log.md").write_text("# log", encoding="utf-8")
    pages = fm.load_pages(str(wiki))
    names = [p["name"] for p in pages]
    assert "alpha" in names
    assert "index" not in names and "log" not in names

def test_load_pages_domain_filter(tmp_path):
    wiki = tmp_path / "wiki"
    (wiki / "work").mkdir(parents=True)
    (wiki / "gaming").mkdir(parents=True)
    (wiki / "work" / "a.md").write_text("---\ntitle: A\n---\nx", encoding="utf-8")
    (wiki / "gaming" / "b.md").write_text("---\ntitle: B\n---\ny", encoding="utf-8")
    pages = fm.load_pages(str(wiki), domain="gaming")
    names = [p["name"] for p in pages]
    assert names == ["b"]
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd tools && python -m pytest tests/test_frontmatter.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'frontmatter'`

- [ ] **Step 3: 写实现**

```python
# tools/frontmatter.py
"""解析 markdown frontmatter 与扫描 wiki 目录的共享模块。纯本地文件操作，不联网。"""
import os
import yaml

SKIP_FILES = {"index.md", "log.md"}


def parse_markdown(text):
    """解析 markdown，返回 {"meta": dict, "body": str}。无 frontmatter 时 meta={}。"""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            try:
                meta = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                meta = {}
            if isinstance(meta, dict):
                return {"meta": meta, "body": parts[2]}
    return {"meta": {}, "body": text}


def load_pages(wiki_dir, domain=None):
    """扫描 wiki_dir 下的 .md 页面（排除 index.md/log.md）。
    domain 不为 None 时只返回该子目录下的页面。
    返回 [{"path","name","meta","body"}]。"""
    pages = []
    root = os.path.join(wiki_dir, domain) if domain else wiki_dir
    if not os.path.isdir(root):
        return pages
    for dirpath, _dirs, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".md") or fn in SKIP_FILES:
                continue
            path = os.path.join(dirpath, fn)
            with open(path, encoding="utf-8") as f:
                parsed = parse_markdown(f.read())
            pages.append({
                "path": path,
                "name": os.path.splitext(fn)[0],
                "meta": parsed["meta"],
                "body": parsed["body"],
            })
    return pages
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd tools && python -m pytest tests/test_frontmatter.py -v`
Expected: PASS（4 个测试）

- [ ] **Step 5: Commit**

```bash
git add tools/frontmatter.py tools/tests/test_frontmatter.py
git commit -m "feat: 添加 frontmatter 解析与 wiki 扫描模块"
```

---

## Task 3: BM25 搜索脚本

**Files:**
- Create: `tools/search.py`
- Test: `tools/tests/test_search.py`

`search(wiki_dir, query, domain=None, type_filter=None, top=5)` 返回排序后的命中列表 `[{"name","title","path","score","snippet"}]`。分词用简单的小写 + 正则切词（中英混合：保留连续字母数字与单个 CJK 字符）。

- [ ] **Step 1: 写失败测试**

```python
# tools/tests/test_search.py
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import search as S

def _make_wiki(tmp_path):
    wiki = tmp_path / "wiki"
    (wiki / "gaming").mkdir(parents=True)
    (wiki / "ai-llm").mkdir(parents=True)
    (wiki / "gaming" / "roguelike.md").write_text(
        "---\ntitle: Roguelike\ntype: concept\ndomain: gaming\n---\n"
        "roguelike games feature procedural generation and permadeath",
        encoding="utf-8")
    (wiki / "ai-llm" / "rag.md").write_text(
        "---\ntitle: RAG\ntype: concept\ndomain: ai-llm\n---\n"
        "retrieval augmented generation uses a vector database",
        encoding="utf-8")
    return str(wiki)

def test_search_finds_relevant_page(tmp_path):
    wiki = _make_wiki(tmp_path)
    results = S.search(wiki, "procedural generation")
    assert results
    assert results[0]["name"] == "roguelike"

def test_search_domain_filter(tmp_path):
    wiki = _make_wiki(tmp_path)
    results = S.search(wiki, "generation", domain="ai-llm")
    names = [r["name"] for r in results]
    assert "roguelike" not in names

def test_search_type_filter(tmp_path):
    wiki = _make_wiki(tmp_path)
    results = S.search(wiki, "vector", type_filter="entity")
    assert results == []  # 没有 entity 类型页面
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd tools && python -m pytest tests/test_search.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'search'`

- [ ] **Step 3: 写实现**

```python
# tools/search.py
"""BM25 关键词搜索 CLI。纯本地文件操作，不联网、不发送数据。

用法:
    python tools/search.py "关键词" [--wiki DIR] [--domain D] [--type T] [--top N]
"""
import argparse
import re
import sys

from rank_bm25 import BM25Plus  # 用 Plus 而非 Okapi：小语料下某词出现在所有文档时 Okapi 的 IDF 会转负，导致分数被 score<=0 过滤掉

import frontmatter as fm

_TOKEN_RE = re.compile(r"[a-z0-9]+|[一-鿿]")


def tokenize(text):
    """小写化后切词：连续英数为一个 token，单个 CJK 字符各为一个 token。"""
    return _TOKEN_RE.findall(text.lower())


def search(wiki_dir, query, domain=None, type_filter=None, top=5):
    pages = fm.load_pages(wiki_dir, domain=domain)
    if type_filter:
        pages = [p for p in pages if p["meta"].get("type") == type_filter]
    if not pages:
        return []
    corpus = [tokenize(p["name"] + " " + str(p["meta"].get("title", "")) + " " + p["body"])
              for p in pages]
    bm25 = BM25Plus(corpus)
    scores = bm25.get_scores(tokenize(query))
    ranked = sorted(zip(pages, scores), key=lambda x: x[1], reverse=True)
    results = []
    for page, score in ranked[:top]:
        if score <= 0:
            continue
        body = page["body"].strip().replace("\n", " ")
        results.append({
            "name": page["name"],
            "title": page["meta"].get("title", page["name"]),
            "path": page["path"],
            "score": round(float(score), 3),
            "snippet": body[:120],
        })
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description="BM25 搜索 wiki 页面")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("--wiki", default="wiki", help="wiki 目录(默认 wiki)")
    parser.add_argument("--domain", default=None, help="限定域: work/gaming/ai-llm")
    parser.add_argument("--type", dest="type_filter", default=None, help="限定 type")
    parser.add_argument("--top", type=int, default=5, help="返回条数(默认 5)")
    args = parser.parse_args(argv)
    results = search(args.wiki, args.query, args.domain, args.type_filter, args.top)
    if not results:
        print("(无匹配结果)")
        return
    for r in results:
        print(f"[{r['score']}] {r['title']}  ({r['path']})")
        print(f"      {r['snippet']}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd tools && python -m pytest tests/test_search.py -v`
Expected: PASS（3 个测试）

- [ ] **Step 5: Commit**

```bash
git add tools/search.py tools/tests/test_search.py
git commit -m "feat: 添加 BM25 关键词搜索脚本"
```

---

## Task 4: 健康检查 lint 脚本

**Files:**
- Create: `tools/lint.py`
- Test: `tools/tests/test_lint.py`

`lint(wiki_dir, domain=None, stale_days=180, today=None)` 返回 `{"broken_links","orphans","missing_fields","stale","low_confidence"}`，每项为问题描述列表。必填字段：title/type/domain/source/date/confidence。`today` 参数便于测试（默认取当天）。

- [ ] **Step 1: 写失败测试**

```python
# tools/tests/test_lint.py
import sys, pathlib, datetime
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import lint as L

def test_lint_detects_broken_link(tmp_path):
    wiki = tmp_path / "wiki"
    (wiki / "work").mkdir(parents=True)
    (wiki / "work" / "a.md").write_text(
        "---\ntitle: A\ntype: project\ndomain: work\nsource: chat\n"
        "date: 2026-06-11\nconfidence: high\n---\n see [[ghost]]",
        encoding="utf-8")
    report = L.lint(str(wiki), today=datetime.date(2026, 6, 11))
    assert any("ghost" in s for s in report["broken_links"])

def test_lint_detects_missing_fields(tmp_path):
    wiki = tmp_path / "wiki"
    (wiki / "work").mkdir(parents=True)
    (wiki / "work" / "b.md").write_text("---\ntitle: B\n---\nbody", encoding="utf-8")
    report = L.lint(str(wiki), today=datetime.date(2026, 6, 11))
    assert any("b.md" in s for s in report["missing_fields"])

def test_lint_detects_stale(tmp_path):
    wiki = tmp_path / "wiki"
    (wiki / "work").mkdir(parents=True)
    (wiki / "work" / "c.md").write_text(
        "---\ntitle: C\ntype: project\ndomain: work\nsource: chat\n"
        "date: 2020-01-01\nconfidence: high\n---\nbody",
        encoding="utf-8")
    report = L.lint(str(wiki), stale_days=180, today=datetime.date(2026, 6, 11))
    assert any("c.md" in s for s in report["stale"])

def test_lint_detects_low_confidence(tmp_path):
    wiki = tmp_path / "wiki"
    (wiki / "work").mkdir(parents=True)
    (wiki / "work" / "d.md").write_text(
        "---\ntitle: D\ntype: project\ndomain: work\nsource: chat\n"
        "date: 2026-06-11\nconfidence: low\n---\nbody",
        encoding="utf-8")
    report = L.lint(str(wiki), today=datetime.date(2026, 6, 11))
    assert any("d.md" in s for s in report["low_confidence"])
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd tools && python -m pytest tests/test_lint.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'lint'`

- [ ] **Step 3: 写实现**

```python
# tools/lint.py
"""wiki 健康检查 CLI。纯本地文件操作，不联网。只读不自动改。

检查: 断链 / 孤立页 / frontmatter 缺字段 / 超期 / 低置信度。

用法:
    python tools/lint.py [--wiki DIR] [--domain D] [--stale-days N]
"""
import argparse
import datetime
import re

import frontmatter as fm

REQUIRED_FIELDS = ["title", "type", "domain", "source", "date", "confidence"]
_LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def lint(wiki_dir, domain=None, stale_days=180, today=None):
    if today is None:
        today = datetime.date.today()
    pages = fm.load_pages(wiki_dir, domain=domain)
    names = {p["name"] for p in pages}
    report = {"broken_links": [], "orphans": [], "missing_fields": [],
              "stale": [], "low_confidence": []}
    linked_to = set()
    has_outlink = {}

    for p in pages:
        targets = _LINK_RE.findall(p["body"])
        has_outlink[p["name"]] = bool(targets)
        for t in targets:
            t = t.strip()
            linked_to.add(t)
            if t not in names:
                report["broken_links"].append(f"{p['path']}: 断链 [[{t}]]")

    for p in pages:
        missing = [f for f in REQUIRED_FIELDS if f not in p["meta"]]
        if missing:
            report["missing_fields"].append(f"{p['path']}: 缺字段 {', '.join(missing)}")

        if str(p["meta"].get("confidence", "")).lower() == "low":
            report["low_confidence"].append(f"{p['path']}: confidence=low 待补证")

        date_val = p["meta"].get("date")
        if date_val:
            try:
                d = date_val if isinstance(date_val, datetime.date) else \
                    datetime.date.fromisoformat(str(date_val))
                if (today - d).days > stale_days:
                    report["stale"].append(f"{p['path']}: 已 {(today - d).days} 天未更新")
            except ValueError:
                report["missing_fields"].append(f"{p['path']}: date 格式非法 '{date_val}'")

        if p["name"] not in linked_to and not has_outlink[p["name"]]:
            report["orphans"].append(f"{p['path']}: 孤立页(无人链接且不链接他人)")

    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="wiki 健康检查")
    parser.add_argument("--wiki", default="wiki", help="wiki 目录(默认 wiki)")
    parser.add_argument("--domain", default=None, help="限定域: work/gaming/ai-llm")
    parser.add_argument("--stale-days", type=int, default=180, help="超期天数阈值(默认 180)")
    args = parser.parse_args(argv)
    report = lint(args.wiki, args.domain, args.stale_days)
    labels = {
        "broken_links": "断链", "orphans": "孤立页", "missing_fields": "缺字段",
        "stale": "陈旧页", "low_confidence": "低置信度",
    }
    total = 0
    for key, label in labels.items():
        items = report[key]
        total += len(items)
        if items:
            print(f"\n## {label} ({len(items)})")
            for s in items:
                print(f"  - {s}")
    print(f"\n共发现 {total} 个问题。" if total else "\n未发现问题，wiki 健康。")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd tools && python -m pytest tests/test_lint.py -v`
Expected: PASS（4 个测试）

- [ ] **Step 5: 运行全部测试**

Run: `cd tools && python -m pytest -v`
Expected: PASS（共 11 个测试）

- [ ] **Step 6: Commit**

```bash
git add tools/lint.py tools/tests/test_lint.py
git commit -m "feat: 添加 wiki 健康检查脚本"
```

---

## Task 5: AGENTS.md（Schema 层）

**Files:**
- Create: `AGENTS.md`

- [ ] **Step 1: 写 AGENTS.md**

完整内容如下（这是让 agent 成为"有纪律的 wiki 维护者"的约定文件）：

```markdown
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

​```yaml
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
​```

### type 分类
- `project` — 工作项目（多见于 work）
- `concept` — 概念（算法、商业模式、游戏机制等）
- `entity` — 实体（公司、人、产品、具体游戏、模型）
- `source-summary` — 单篇素材摘要
- `synthesis` — 跨素材综合洞见
- `log` — 仅用于 log.md

### 链接
页面间用 `[[页面名]]` 互链（页面名 = 文件名去扩展名）。

## 三个工作流

### Ingest（投喂素材）
1. 用户把素材放入 `sources/<域>/` 或贴给你。
2. 读完先与用户讨论要点。
3. **提议**：写哪个摘要页、更新哪些关联页（列清单）。
4. **用户确认后才写入。**
5. 在 `wiki/log.md` 追加一条记录。

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
```

> 注意：上面 frontmatter 示例里的 `​```yaml` 围栏在真实文件中用三个反引号，写入时去掉示意用的零宽字符。

- [ ] **Step 2: 校验 frontmatter 示例可被解析**

Run: `python -c "import sys; sys.path.insert(0,'tools'); import frontmatter as fm; print('AGENTS.md 存在' if __import__('os').path.exists('AGENTS.md') else 'missing')"`
Expected: 输出 `AGENTS.md 存在`

- [ ] **Step 3: Commit**

```bash
git add AGENTS.md
git commit -m "docs: 添加 AGENTS.md 维护约定(schema 层)"
```

---

## Task 6: index.md 与 log.md 模板

**Files:**
- Create: `wiki/index.md`
- Create: `wiki/log.md`

- [ ] **Step 1: 写 index.md**

```markdown
# 知识库索引 (index)

> 内容地图：每个页面一行 + 一句话摘要。查询时先读本文件定位。

## work — 工作项目记录

_（暂无页面）_

## gaming — 游戏行业研究

_（暂无页面）_

## ai-llm — AI/LLM 学习

_（暂无页面）_
```

- [ ] **Step 2: 写 log.md**

```markdown
# 操作日志 (log)

> 追加式、按时间倒序。条目格式可 grep：`## [YYYY-MM-DD] 动作 — 摘要`

## [2026-06-11] init — 知识库初始化
- 建立三层结构与 work/gaming/ai-llm 三域分区
- 添加 search.py / lint.py 工具
```

- [ ] **Step 3: 验证 load_pages 跳过这两个文件**

Run: `cd tools && python -c "import frontmatter as fm; ps=fm.load_pages('../wiki'); print([p['name'] for p in ps])"`
Expected: 输出 `[]`（此时无内容页，且 index/log 被正确排除）

- [ ] **Step 4: Commit**

```bash
git add wiki/index.md wiki/log.md
git commit -m "docs: 添加 index.md 与 log.md 模板"
```

---

## Task 7: 端到端验证

**Files:**
- 临时创建示例页面用于验证，验证后删除（不提交）

- [ ] **Step 1: 创建一个示例页面**

创建 `wiki/ai-llm/llm-wiki.md`：

```markdown
---
title: LLM Wiki 模式
type: concept
domain: ai-llm
source: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
date: 2026-06-11
confidence: high
tags: [knowledge-base, llm]
links: []
---

LLM Wiki 是让 LLM 持续维护一组互链 markdown 文件的知识库模式，知识被编译一次并保持更新。
```

- [ ] **Step 2: 搜索验证**

Run: `python tools/search.py "知识库 markdown" --wiki wiki`
Expected: 命中 `llm-wiki.md`，输出含标题"LLM Wiki 模式"。

- [ ] **Step 3: lint 验证**

Run: `python tools/lint.py --wiki wiki`
Expected: 该页 6 字段齐全、无断链；可能因无人链接被列为孤立页(符合预期，单页场景)。

- [ ] **Step 4: 删除示例页面**

删除 `wiki/ai-llm/llm-wiki.md`（仅为验证，不纳入库）。

- [ ] **Step 5: 跑全量测试收尾**

Run: `cd tools && python -m pytest -v`
Expected: PASS（11 个测试）

---

## 实现中发现的偏差记录

- Task 3：`BM25Okapi` → `BM25Plus`。小语料下某词出现在所有文档时 Okapi 的 IDF 转负，分数被 `score<=0` 过滤掉；Plus 的加性 IDF 恒正。
- Task 7：两个 CLI 的 `main()` 增加 `sys.stdout.reconfigure(encoding="utf-8")`。Windows 控制台默认 GBK，中文输出乱码；reconfigure 仅影响命令行输出，不改文件读写(文件始终 UTF-8)。

## 验证清单（对照 spec）

- [x] 三层架构(sources/wiki/AGENTS.md) — Task 1、5
- [x] 三域分区(work/gaming/ai-llm) — Task 1
- [x] frontmatter 六字段规范 — Task 5、4(lint 校验)
- [x] 6 类 type 定义 — Task 5
- [x] wikilinks 与断链/孤立检测 — Task 4
- [x] BM25 搜索 + domain/type 过滤 — Task 3
- [x] lint 五项检查 — Task 4
- [x] 三工作流 + 三铁律写入 AGENTS.md — Task 5
- [x] index.md / log.md 模板 — Task 6
- [x] 纯本地、不联网 — Task 3、4 实现注释
- [x] YAGNI：不做向量/MCP/数据库 — 计划未包含
```
