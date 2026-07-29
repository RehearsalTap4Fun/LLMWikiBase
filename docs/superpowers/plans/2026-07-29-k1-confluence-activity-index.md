# K1 Confluence Activity Index Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local, incrementally synchronized Markdown index that maps K1 activity names, aliases, child-page titles, tags, and summaries to the exact Confluence pages needed for live answers.

**Architecture:** A standard-library Python package wraps the approved Confluence CLI, crawls the complete descendant tree, computes a metadata-only state delta, and renders one Markdown page per first-level activity plus a catalog. Generated regions are refreshed transactionally while curated summaries and tags are preserved; a separate read-only CLI ranks local matches and returns the target Wiki URLs.

**Tech Stack:** Python 3.10 standard library, pytest 9, Markdown/YAML frontmatter generated in a constrained format, existing `confluence.pyz` CLI, PowerShell verification commands.

## Global Constraints

- Root Confluence page is exactly `73598402` (`K1活动`).
- Read Confluence only through `%USERPROFILE%/.skills/confluence/scripts/confluence.pyz` or an explicit `--confluence-cli` override.
- Credentials come only from process environment or Windows `HKCU/Environment`; never print or persist credential values.
- Use `PYTHONIOENCODING=utf-8` for CLI subprocesses.
- Store no Confluence full body, reward table, server range, schedule, item ID list, token, email, or authentication header in Markdown, state, logs, or fixtures.
- `sources/` is read-only.
- One Markdown page represents one first-level activity; descendants are rows inside that page.
- Activity filenames are `k1-activity-<pageId>.md` so Wiki renames do not break local links.
- Confluence `current` is a page publication status, not proof that an activity is currently open.
- Missing, historical, obsolete, inaccessible, or deleted-looking pages remain indexed with explicit status; they are not silently removed.
- Existing user changes in `wiki/index.md`, `wiki/log.md`, and all other dirty files must be preserved. Stage only task-owned files or exact task-owned hunks.
- `wiki/work/` and `.cache/k1-activity-index/` contain local/internal data and must remain uncommitted.
- Use `apply_patch` for repository edits during execution.
- No third-party runtime dependency is added; tests may use the already available pytest 9.
- The missing current-HEAD sources for `tools/search.py` and `tools/lint.py` are not restored or imported; this feature supplies its own parser, search, and validator.

## Scope Check

Synchronization, Markdown rendering, and local lookup share one state model and one generated format, so they form one testable feature rather than independent products. Initial live ingestion is the final integration task because it validates the tooling and produces the user-visible index.

## File Responsibility Map

### New runtime files

- `tools/k1_activity_index/__init__.py` — package exports only.
- `tools/k1_activity_index/models.py` — immutable records and shared exceptions.
- `tools/k1_activity_index/confluence.py` — environment resolution and JSON CLI adapter.
- `tools/k1_activity_index/crawl.py` — complete breadth-first descendant traversal.
- `tools/k1_activity_index/state.py` — metadata-only state loading, delta computation, rename/move history, and review flags.
- `tools/k1_activity_index/semantics.py` — deterministic aliases, roles, lifecycle labels, tags, and safe draft summaries.
- `tools/k1_activity_index/markdown.py` — constrained frontmatter parser, curated/generated region parser, renderer, and validator.
- `tools/k1_activity_index/transaction.py` — validated batch replacement with rollback.
- `tools/k1_activity_index/service.py` — synchronization orchestration and report creation.
- `tools/k1_activity_index/query.py` — local document loader, normalization, ranking, and ambiguity handling.
- `tools/sync_k1_activity_index.py` — thin sync/validate CLI.
- `tools/search_k1_activity.py` — thin local search CLI.

### New tests and fixtures

- `tests/test_k1_activity_confluence.py`
- `tests/test_k1_activity_crawl.py`
- `tests/test_k1_activity_state.py`
- `tests/test_k1_activity_semantics.py`
- `tests/test_k1_activity_markdown.py`
- `tests/test_k1_activity_transaction.py`
- `tests/test_k1_activity_service.py`
- `tests/test_k1_activity_query.py`
- `tests/fixtures/k1_activity_index/tree.json` — synthetic metadata tree.
- `tests/fixtures/k1_activity_index/pages.json` — short invented bodies without internal facts.

### Generated local files

- `wiki/work/k1-activity-catalog.md`
- `wiki/work/k1-activities/k1-activity-<pageId>.md`
- `.cache/k1-activity-index/state.json`
- `.cache/k1-activity-index/review-report.json`

### Existing files to modify

- `AGENTS.md:57` — add K1 activity query routing after the general Query workflow.
- `.gitignore:10` — ignore `.cache/k1-activity-index/`.
- `wiki/index.md:12` — add one catalog entry under “项目组 wiki 口径”.
- `wiki/work/k1-confluence-routing.md:9,16-30` — link the precise activity catalog and replace the obsolete “cannot access locally” route.
- `wiki/log.md:4` — prepend the completed ingest record.

---

### Task 1: Shared Models and Confluence CLI Adapter

**Files:**
- Create: `tools/k1_activity_index/__init__.py`
- Create: `tools/k1_activity_index/models.py`
- Create: `tools/k1_activity_index/confluence.py`
- Create: `tests/test_k1_activity_confluence.py`

**Interfaces:**
- Produces: `PageRecord`, `CrawlSnapshot`, `PageUnavailableError`, `ConfluenceCommandError`.
- Produces: `resolve_confluence_environment(process_env, user_reader) -> dict[str, str]`.
- Produces: `CliConfluenceClient.check() -> None`, `children(page_id, limit) -> dict`, and `page(page_id) -> dict`.
- Consumes: existing compiled `confluence.pyz` only; no direct HTTP.

- [ ] **Step 1: Write failing environment and redaction tests**

```python
# tests/test_k1_activity_confluence.py
import subprocess
from pathlib import Path

import pytest

from tools.k1_activity_index.confluence import (
    CliConfluenceClient,
    ConfluenceCommandError,
    resolve_confluence_environment,
)


def test_environment_falls_back_to_windows_user_scope():
    user_values = {
        "CONFLUENCE_URL": "https://wiki.example.test",
        "CONFLUENCE_EMAIL": "user@example.test",
        "CONFLUENCE_API_TOKEN": "secret-value",
    }
    resolved = resolve_confluence_environment({}, lambda name: user_values.get(name))
    assert resolved == user_values


def test_cli_sets_utf8_and_never_exposes_token(tmp_path: Path):
    calls = []

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(
            command, 1, stdout="", stderr="Error: request failed for secret-value"
        )

    client = CliConfluenceClient(
        cli_path=tmp_path / "confluence.pyz",
        environment={
            "CONFLUENCE_URL": "https://wiki.example.test",
            "CONFLUENCE_EMAIL": "user@example.test",
            "CONFLUENCE_API_TOKEN": "secret-value",
        },
        runner=runner,
    )
    with pytest.raises(ConfluenceCommandError) as error:
        client.check()

    assert "secret-value" not in str(error.value)
    assert calls[0][1]["env"]["PYTHONIOENCODING"] == "utf-8"
```

- [ ] **Step 2: Run the tests and verify the module is absent**

Run:

```powershell
python -m pytest tests/test_k1_activity_confluence.py -v
```

Expected: collection fails with `ModuleNotFoundError: No module named 'tools.k1_activity_index'`.

- [ ] **Step 3: Implement immutable models and the CLI adapter**

Define these exact shared records in `models.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class PageRecord:
    page_id: str
    title: str
    status: str
    space: str
    version: int
    url: str
    parent_id: str
    path: tuple[str, ...]
    topic_id: str
    wiki_updated_at: str | None = None


@dataclass(frozen=True)
class CrawlSnapshot:
    root_page_id: str
    pages: dict[str, PageRecord]
    children_by_parent: dict[str, tuple[str, ...]]


class ConfluenceCommandError(RuntimeError):
    pass


class PageUnavailableError(ConfluenceCommandError):
    def __init__(self, page_id: str, status_code: int):
        self.page_id = page_id
        self.status_code = status_code
        super().__init__(f"Confluence page {page_id} is unavailable ({status_code})")
```

Implement `confluence.py` with:

```python
REQUIRED_ENV = (
    "CONFLUENCE_URL",
    "CONFLUENCE_EMAIL",
    "CONFLUENCE_API_TOKEN",
)


def resolve_confluence_environment(process_env, user_reader):
    resolved = {}
    for name in REQUIRED_ENV:
        value = process_env.get(name) or user_reader(name)
        if not value:
            raise ConfluenceCommandError(f"Missing environment variable: {name}")
        resolved[name] = value
    return resolved
```

`CliConfluenceClient` executes `[sys.executable, cli_path, *arguments]` with `capture_output=True`, `text=True`, `encoding="utf-8"`, and a copied environment containing `PYTHONIOENCODING=utf-8`. Parse stdout with `json.loads`. Classify stderr containing HTTP 403 or 404 as `PageUnavailableError` for `page()`; all other nonzero exits raise a redacted `ConfluenceCommandError`. Redaction replaces every credential value with `***` before constructing an exception.

- [ ] **Step 4: Run the focused tests**

Run `python -m pytest tests/test_k1_activity_confluence.py -v`.

Expected: all tests pass.

- [ ] **Step 5: Commit the adapter**

```powershell
git add tools/k1_activity_index/__init__.py tools/k1_activity_index/models.py tools/k1_activity_index/confluence.py tests/test_k1_activity_confluence.py
git diff --cached --check
git commit -m "feat: add Confluence adapter for K1 activity index"
```

---

### Task 2: Complete Descendant Tree Crawler

**Files:**
- Create: `tools/k1_activity_index/crawl.py`
- Create: `tests/test_k1_activity_crawl.py`
- Create: `tests/fixtures/k1_activity_index/tree.json`

**Interfaces:**
- Consumes: any reader exposing `children(page_id: str, limit: int) -> dict`.
- Produces: `crawl_tree(reader, root_page_id, limit=1000) -> CrawlSnapshot`.
- Produces: `IncompleteTreeError` and `InvalidTreeError`.

- [ ] **Step 1: Add failing traversal and truncation tests**

```python
# tests/test_k1_activity_crawl.py
import pytest

from tools.k1_activity_index.crawl import IncompleteTreeError, crawl_tree


class FakeReader:
    def __init__(self, responses):
        self.responses = responses

    def children(self, page_id, limit):
        return self.responses[page_id]


def _page(page_id, title):
    return {
        "id": page_id,
        "title": title,
        "status": "current",
        "space": "KEFU",
        "version": 1,
        "url": f"https://wiki.example.test/pages/viewpage.action?pageId={page_id}",
    }


def test_crawl_assigns_every_descendant_to_one_first_level_topic():
    reader = FakeReader({
        "73598402": {"total": 2, "results": [_page("100", "主题A"), _page("200", "主题B")]},
        "100": {"total": 1, "results": [_page("101", "A商店")]},
        "101": {"total": 0, "results": []},
        "200": {"total": 0, "results": []},
    })

    snapshot = crawl_tree(reader, "73598402")

    assert snapshot.pages["100"].topic_id == "100"
    assert snapshot.pages["101"].topic_id == "100"
    assert snapshot.pages["101"].path == ("主题A", "A商店")
    assert snapshot.pages["200"].topic_id == "200"


def test_crawl_rejects_server_side_truncation():
    reader = FakeReader({
        "73598402": {"total": 2, "results": [_page("100", "主题A")]},
    })
    with pytest.raises(IncompleteTreeError, match="73598402"):
        crawl_tree(reader, "73598402")
```

Put the same synthetic tree in `tree.json` for later service integration tests. Use invented labels such as “主题A”; do not copy real K1 prose.

- [ ] **Step 2: Run the crawler tests and verify failure**

Run `python -m pytest tests/test_k1_activity_crawl.py -v`.

Expected: import fails because `crawl.py` does not exist.

- [ ] **Step 3: Implement breadth-first traversal**

Use `collections.deque`. For each parent:

1. Fetch `children(parent_id, limit)`.
2. Require `response["total"] == len(response["results"])`.
3. Reject a child pageId already assigned to a different parent.
4. For a child of the root, set `topic_id = child.page_id` and `path = (child.title,)`.
5. For deeper children, inherit the parent topic and append the title to the path.
6. Record children in API order so rendered tables are deterministic.

Implement this exact function body:

```python
from collections import deque


def crawl_tree(reader, root_page_id: str, limit: int = 1000) -> CrawlSnapshot:
    pages = {}
    children_by_parent = {}
    queue = deque([(root_page_id, (), None)])

    while queue:
        parent_id, parent_path, inherited_topic_id = queue.popleft()
        response = reader.children(parent_id, limit)
        results = response.get("results", [])
        if response.get("total") != len(results):
            raise IncompleteTreeError(
                f"Child listing for {parent_id} returned "
                f"{len(results)} of {response.get('total')}"
            )

        child_ids = []
        for raw in results:
            page_id = str(raw["id"])
            if page_id in pages:
                raise InvalidTreeError(f"Page {page_id} has multiple parents")
            path = parent_path + (raw["title"],)
            topic_id = page_id if parent_id == root_page_id else inherited_topic_id
            record = PageRecord(
                page_id=page_id,
                title=raw["title"],
                status=raw["status"],
                space=raw["space"],
                version=int(raw["version"]),
                url=raw["url"],
                parent_id=parent_id,
                path=path,
                topic_id=topic_id,
                wiki_updated_at=raw.get("wiki_updated_at"),
            )
            pages[page_id] = record
            child_ids.append(page_id)
            queue.append((page_id, path, topic_id))
        children_by_parent[parent_id] = tuple(child_ids)

    return CrawlSnapshot(root_page_id, pages, children_by_parent)
```

- [ ] **Step 4: Run focused tests**

Run `python -m pytest tests/test_k1_activity_crawl.py -v`.

Expected: all tests pass.

- [ ] **Step 5: Commit the crawler**

```powershell
git add tools/k1_activity_index/crawl.py tests/test_k1_activity_crawl.py tests/fixtures/k1_activity_index/tree.json
git diff --cached --check
git commit -m "feat: crawl complete K1 activity page tree"
```

---

### Task 3: Metadata-Only State and Delta Computation

**Files:**
- Create: `tools/k1_activity_index/state.py`
- Create: `tests/test_k1_activity_state.py`
- Modify: `tools/k1_activity_index/models.py`

**Interfaces:**
- Produces: `PageState`, `IndexState`, and `ChangeSet`.
- Produces: `load_state(path, root_page_id) -> IndexState`.
- Produces: `compute_next_state(previous, snapshot, synced_at) -> tuple[IndexState, ChangeSet]`.
- Produces: `mark_unavailable(state, page_id, status_code) -> IndexState`.
- Produces: `mark_reviewed(state, page_ids) -> IndexState`.
- Produces: `dump_state(state) -> str`.

- [ ] **Step 1: Write failing delta and secret-safety tests**

```python
# tests/test_k1_activity_state.py
from tools.k1_activity_index.models import CrawlSnapshot, IndexState, PageRecord
from tools.k1_activity_index.state import compute_next_state, dump_state


def _record(page_id="100", title="主题A", version=1):
    return PageRecord(
        page_id=page_id,
        title=title,
        status="current",
        space="KEFU",
        version=version,
        url=f"https://wiki.example.test/pages/viewpage.action?pageId={page_id}",
        parent_id="73598402",
        path=(title,),
        topic_id="100",
    )


def test_rename_keeps_old_title_as_alias_and_requires_review():
    first, _ = compute_next_state(
        IndexState.empty("73598402"),
        CrawlSnapshot("73598402", {"100": _record()}, {"73598402": ("100",)}),
        "2026-07-29T10:00:00+08:00",
    )
    second, changes = compute_next_state(
        first,
        CrawlSnapshot(
            "73598402",
            {"100": _record(title="主题A新名", version=2)},
            {"73598402": ("100",)},
        ),
        "2026-07-29T11:00:00+08:00",
    )

    assert second.pages["100"].aliases == ("主题A",)
    assert second.pages["100"].review_needed is True
    assert changes.renamed_ids == ("100",)
    assert changes.content_ids == ("100",)


def test_missing_page_is_retained_without_body_or_credentials():
    first, _ = compute_next_state(
        IndexState.empty("73598402"),
        CrawlSnapshot("73598402", {"100": _record()}, {"73598402": ("100",)}),
        "2026-07-29T10:00:00+08:00",
    )
    second, _ = compute_next_state(
        first,
        CrawlSnapshot("73598402", {}, {"73598402": ()}),
        "2026-07-29T11:00:00+08:00",
    )

    payload = dump_state(second)
    assert second.pages["100"].availability == "missing-from-root"
    assert '"body"' not in payload
    assert "CONFLUENCE_API_TOKEN" not in payload
```

- [ ] **Step 2: Run state tests and verify failure**

Run `python -m pytest tests/test_k1_activity_state.py -v`.

Expected: imports fail because state records and functions are absent.

- [ ] **Step 3: Implement state schema version 1**

Add to `models.py`:

```python
@dataclass(frozen=True)
class PageState:
    page_id: str
    title: str
    status: str
    space: str
    version: int
    url: str
    parent_id: str
    path: tuple[str, ...]
    topic_id: str
    wiki_updated_at: str | None
    aliases: tuple[str, ...]
    availability: str
    review_needed: bool


@dataclass(frozen=True)
class IndexState:
    schema_version: int
    root_page_id: str
    synced_at: str | None
    pages: dict[str, PageState]

    @classmethod
    def empty(cls, root_page_id: str):
        return cls(1, root_page_id, None, {})


@dataclass(frozen=True)
class ChangeSet:
    new_ids: tuple[str, ...]
    version_changed_ids: tuple[str, ...]
    renamed_ids: tuple[str, ...]
    moved_ids: tuple[str, ...]
    missing_ids: tuple[str, ...]
    content_ids: tuple[str, ...]
```

`compute_next_state` sorts every ID tuple numerically when possible and lexically otherwise. New, renamed, moved, and version-changed pages set `review_needed=True`. A missing page retains its last metadata and aliases but changes availability to `missing-from-root`.

`dump_state` builds a `payload` dictionary and returns `json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"`. Before serialization it rejects any dictionary key case-insensitively equal to `body`, `content`, `html`, `token`, `password`, or `api_token`.

- [ ] **Step 4: Run state tests**

Run `python -m pytest tests/test_k1_activity_state.py -v`.

Expected: all tests pass.

- [ ] **Step 5: Commit state handling**

```powershell
git add tools/k1_activity_index/models.py tools/k1_activity_index/state.py tests/test_k1_activity_state.py
git diff --cached --check
git commit -m "feat: track K1 activity index state"
```

---

### Task 4: Safe Semantic Drafts

**Files:**
- Create: `tools/k1_activity_index/semantics.py`
- Create: `tests/test_k1_activity_semantics.py`
- Create: `tests/fixtures/k1_activity_index/pages.json`

**Interfaces:**
- Produces: `SemanticDraft(summary, aliases, tags, role, lifecycle)`.
- Produces: `draft_page_semantics(page, body) -> SemanticDraft`.
- Produces: `draft_topic_summary(topic, descendant_drafts) -> str`.
- Produces: `normalize_label(text) -> str`.

Define:

```python
@dataclass(frozen=True)
class SemanticDraft:
    summary: str
    aliases: tuple[str, ...]
    tags: tuple[str, ...]
    role: str
    lifecycle: str
```

- [ ] **Step 1: Write failing controlled-taxonomy tests**

```python
# tests/test_k1_activity_semantics.py
from tools.k1_activity_index.models import PageRecord
from tools.k1_activity_index.semantics import (
    draft_page_semantics,
    draft_topic_summary,
    normalize_label,
)


def _page(title, page_id="100"):
    return PageRecord(
        page_id=page_id,
        title=title,
        status="current",
        space="KEFU",
        version=1,
        url=f"https://wiki.example.test/pages/viewpage.action?pageId={page_id}",
        parent_id="73598402",
        path=(title,),
        topic_id="100",
    )


def test_draft_detects_alias_role_and_safe_tags():
    draft = draft_page_semantics(
        _page("K1 绯夜通行证"),
        "活动时间 UTC 2026/7/28。服务器 103-127。通行证奖励道具 3320214。",
    )
    assert draft.aliases == ("绯夜通行证",)
    assert draft.role == "通行证"
    assert "通行证" in draft.tags
    assert "2026/7/28" not in draft.summary
    assert "3320214" not in draft.summary


def test_topic_summary_uses_child_roles_not_volatile_body():
    topic = _page("K1 绯夜假面")
    summary = draft_topic_summary(
        topic,
        [
            draft_page_semantics(_page("K1 绯夜通行证", "101"), ""),
            draft_page_semantics(_page("K1 绯夜宝铺", "102"), "兑换商店"),
        ],
    )
    assert summary == "绯夜假面主题活动，包含通行证、商店/兑换等子活动入口。"


def test_normalization_removes_k1_prefix_spacing_and_punctuation():
    assert normalize_label(" K1：绯夜 假面 ") == "绯夜假面"
```

- [ ] **Step 2: Run semantic tests and verify failure**

Run `python -m pytest tests/test_k1_activity_semantics.py -v`.

Expected: import fails because `semantics.py` is absent.

- [ ] **Step 3: Implement the controlled taxonomy**

Use these ordered keyword groups:

```python
ROLE_RULES = (
    ("通行证", ("通行证", "BP", "battle pass")),
    ("商店/兑换", ("商店", "宝铺", "兑换")),
    ("转盘/抽奖", ("转盘", "抽奖", "幸运")),
    ("排行/冲刺", ("排行", "最强", "冲刺")),
    ("充值/礼包", ("充值", "特购", "礼包")),
    ("收集", ("收集", "秘典", "宝典")),
    ("PVP", ("战场", "争霸", "对决")),
    ("PVE", ("狩猎", "入侵", "秘境")),
    ("小游戏", ("大作战", "大富翁", "世界杯")),
)

SCENE_RULES = (
    ("节日", ("圣诞", "新年", "复活节", "周年", "节日")),
    ("新服", ("新人", "新服")),
    ("回归", ("回归",)),
    ("KVK", ("KVK", "破碎大陆", "远征")),
    ("日常", ("日常",)),
)

HISTORY_WORDS = ("旧", "过期", "废弃", "需删除")
```

Draft summaries may contain the page title and controlled role names only. Bodies are used only for keyword presence. Aliases strip leading `K1`, normalize whitespace/punctuation, and exclude empty strings.

- [ ] **Step 4: Run semantic tests**

Run `python -m pytest tests/test_k1_activity_semantics.py -v`.

Expected: all tests pass.

- [ ] **Step 5: Commit semantic drafting**

```powershell
git add tools/k1_activity_index/semantics.py tests/test_k1_activity_semantics.py tests/fixtures/k1_activity_index/pages.json
git diff --cached --check
git commit -m "feat: draft safe K1 activity semantics"
```

---

### Task 5: Markdown Parsing, Preservation, Rendering, and Validation

**Files:**
- Create: `tools/k1_activity_index/markdown.py`
- Create: `tests/test_k1_activity_markdown.py`

**Interfaces:**
- Produces: `CuratedTopic`, `ChildEntry`, `TopicDocument`, and `ParsedTopic`.
- Produces: `parse_topic_page(text) -> ParsedTopic`.
- Produces: `render_topic_page(document, existing_text=None) -> str`.
- Produces: `render_catalog(documents, synced_at, existing_text=None) -> str`.
- Produces: `validate_topic_page(text, expected_page_id) -> tuple[str, ...]`.
- Produces markers `K1-ACTIVITY-CURATED` and `K1-ACTIVITY-GENERATED`.

Define:

```python
@dataclass(frozen=True)
class CuratedTopic:
    summary: str
    aliases: tuple[str, ...]
    tags: tuple[str, ...]
    links: tuple[str, ...]
    notes: str


@dataclass(frozen=True)
class ChildEntry:
    page: PageState
    role: str
    summary: str


@dataclass(frozen=True)
class TopicDocument:
    topic: PageState
    curated: CuratedTopic
    children: tuple[ChildEntry, ...]
    synced_at: str


@dataclass(frozen=True)
class ParsedTopic:
    curated: CuratedTopic
    children: dict[str, ChildEntry]
```

- [ ] **Step 1: Write failing preservation and schema tests**

```python
# tests/test_k1_activity_markdown.py
from dataclasses import replace

import pytest

from tools.k1_activity_index.markdown import (
    ChildEntry,
    CuratedTopic,
    TopicDocument,
    parse_topic_page,
    render_catalog,
    render_topic_page,
    validate_topic_page,
)
from tools.k1_activity_index.models import PageState


def _state(page_id, title, topic_id="100", parent_id="73598402", availability="available"):
    return PageState(
        page_id=page_id,
        title=title,
        status="current",
        space="KEFU",
        version=1,
        url=f"https://wiki.example.test/pages/viewpage.action?pageId={page_id}",
        parent_id=parent_id,
        path=(title,),
        topic_id=topic_id,
        wiki_updated_at=None,
        aliases=(),
        availability=availability,
        review_needed=True,
    )


def _document(page_id="100", title="K1 主题A", availability="available"):
    topic = _state(page_id, title, topic_id=page_id, availability=availability)
    child = _state("101" + page_id, "主题A商店", topic_id=page_id, parent_id=page_id)
    return TopicDocument(
        topic=topic,
        curated=CuratedTopic(
            summary="主题A活动，包含商店入口。",
            aliases=("主题A",),
            tags=("K1", "活动", "商店/兑换"),
            links=("[[k1-activity-catalog]]", "[[k1-confluence-routing]]"),
            notes="",
        ),
        children=(ChildEntry(child, "商店/兑换", "主题A商店的商店/兑换规则入口。"),),
        synced_at="2026-07-29T12:00:00+08:00",
    )


def test_rendered_page_has_required_frontmatter_and_no_body():
    rendered = render_topic_page(_document())

    assert validate_topic_page(rendered, "100") == ()
    assert "活动涉及服务器" not in rendered
    assert "3320214" not in rendered
    assert "Wiki 更新时间 | 未知" in rendered


def test_existing_curated_region_survives_rerender():
    first = render_topic_page(_document())
    edited = first.replace("主题A活动，包含商店入口。", "人工确认后的摘要。")
    parsed = parse_topic_page(edited)
    rerendered = render_topic_page(
        replace(_document(), curated=parsed.curated),
        existing_text=edited,
    )
    assert "人工确认后的摘要。" in rerendered


def test_parser_rejects_missing_curated_end():
    broken = '---\ntitle: "x"\n---\n<!-- K1-ACTIVITY-CURATED:START -->'
    with pytest.raises(ValueError, match="curated"):
        parse_topic_page(broken)


def test_catalog_groups_historical_and_inaccessible_topics():
    current = _document("100", "K1 当前活动")
    historical = replace(
        _document("200", "K1 旧活动"),
        curated=CuratedTopic("历史活动。", ("旧活动",), ("K1", "活动", "历史"), (), ""),
    )
    inaccessible = _document("300", "K1 不可访问活动", "inaccessible")
    catalog = render_catalog(
        (current, historical, inaccessible),
        "2026-07-29T12:00:00+08:00",
    )
    assert "## 当前可用" in catalog
    assert "## 历史/过期" in catalog
    assert "## 不可访问" in catalog
```

- [ ] **Step 2: Run Markdown tests and verify failure**

Run `python -m pytest tests/test_k1_activity_markdown.py -v`.

Expected: import fails because `markdown.py` is absent.

- [ ] **Step 3: Implement the constrained Markdown format**

Define:

```python
CURATED_START = "<!-- K1-ACTIVITY-CURATED:START -->"
CURATED_END = "<!-- K1-ACTIVITY-CURATED:END -->"
GENERATED_START = "<!-- K1-ACTIVITY-GENERATED:START -->"
GENERATED_END = "<!-- K1-ACTIVITY-GENERATED:END -->"
```

Render frontmatter values using JSON string/list syntax, which remains valid YAML and is parseable with `json.loads`:

```yaml
---
title: "K1 主题A"
type: "source-summary"
domain: "work"
source: "https://wiki.example.test/pages/viewpage.action?pageId=100"
date: "2026-07-29"
confidence: "medium"
tags: ["K1", "活动", "商店/兑换"]
links: ["[[k1-activity-catalog]]", "[[k1-confluence-routing]]"]
---
```

The curated region contains `主题摘要`, `别名`, `语义标签`, and `人工备注`. The generated region contains root metadata, old titles discovered by state, the descendant table, review flags, and the回源 boundary. Escape `|` as `\|` and replace embedded newlines with spaces in table cells.

`parse_topic_page` rejects missing or duplicated markers and malformed frontmatter. It parses existing child rows by pageId so their summaries survive unchanged versions. `render_topic_page` preserves parsed curated content from `existing_text`; only a new page uses a draft `CuratedTopic`.

- [ ] **Step 4: Implement validation**

`validate_topic_page` returns explicit error strings for:

- missing frontmatter keys `title`, `type`, `domain`, `source`, `date`, `confidence`, `tags`, or `links`;
- source URL pageId not equal to the filename/topic pageId;
- missing or duplicated curated/generated markers;
- duplicate descendant pageIds;
- a descendant row whose topic ID differs from the root;
- forbidden keys or copied-body markers.

`render_catalog` emits the same required frontmatter, preserves its curated intro region, and groups topics into current, historical/expired, and inaccessible/missing sections.

Render `confidence: "low"` when the title/lifecycle marks a page historical, expired, obsolete, or deleted; otherwise render `confidence: "medium"`. Never render `high` from this single-source index.

- [ ] **Step 5: Run Markdown tests**

Run `python -m pytest tests/test_k1_activity_markdown.py -v`.

Expected: all tests pass.

- [ ] **Step 6: Commit the renderer**

```powershell
git add tools/k1_activity_index/markdown.py tests/test_k1_activity_markdown.py
git diff --cached --check
git commit -m "feat: render K1 activity index pages"
```

---

### Task 6: Transactional Batch Output

**Files:**
- Create: `tools/k1_activity_index/transaction.py`
- Create: `tests/test_k1_activity_transaction.py`

**Interfaces:**
- Produces: `write_batch_atomic(outputs: dict[Path, str], replace=os.replace) -> None`.
- Consumes: already rendered and validated UTF-8 text.

- [ ] **Step 1: Write failing success and rollback tests**

```python
# tests/test_k1_activity_transaction.py
from pathlib import Path

import pytest

from tools.k1_activity_index.transaction import write_batch_atomic


def test_batch_replaces_every_target(tmp_path: Path):
    first = tmp_path / "first.md"
    second = tmp_path / "second.json"
    first.write_text("old", encoding="utf-8")

    write_batch_atomic({first: "new", second: '{"ok": true}\n'})

    assert first.read_text(encoding="utf-8") == "new"
    assert second.read_text(encoding="utf-8") == '{"ok": true}\n'


def test_batch_rolls_back_after_replace_failure(tmp_path: Path):
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    first.write_text("old-first", encoding="utf-8")
    second.write_text("old-second", encoding="utf-8")
    calls = 0

    def failing_replace(source, target):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("synthetic replace failure")
        Path(source).replace(target)

    with pytest.raises(OSError, match="synthetic"):
        write_batch_atomic(
            {first: "new-first", second: "new-second"},
            replace=failing_replace,
        )

    assert first.read_text(encoding="utf-8") == "old-first"
    assert second.read_text(encoding="utf-8") == "old-second"
```

- [ ] **Step 2: Run transaction tests and verify failure**

Run `python -m pytest tests/test_k1_activity_transaction.py -v`.

Expected: import fails because `transaction.py` is absent.

- [ ] **Step 3: Implement staged writes with rollback**

For each target:

1. Create the parent directory.
2. Write UTF-8 text to a unique temporary file in the same directory.
3. Copy an existing target to a unique backup.
4. Replace targets in the insertion order supplied by the caller.
5. If a replace fails, restore every already-replaced target from backup and remove targets that did not exist before.
6. Delete all temporary and backup files in `finally`.

The caller inserts state last, so Markdown is installed before state records the sync as complete.

- [ ] **Step 4: Run transaction tests**

Run `python -m pytest tests/test_k1_activity_transaction.py -v`.

Expected: all tests pass and no temporary or backup files remain under the pytest directory.

- [ ] **Step 5: Commit transaction support**

```powershell
git add tools/k1_activity_index/transaction.py tests/test_k1_activity_transaction.py
git diff --cached --check
git commit -m "feat: write K1 activity index atomically"
```

---

### Task 7: Synchronization Service and CLI

**Files:**
- Create: `tools/k1_activity_index/service.py`
- Create: `tools/sync_k1_activity_index.py`
- Create: `tests/test_k1_activity_service.py`
- Modify: `tools/k1_activity_index/state.py`
- Modify: `tools/k1_activity_index/markdown.py`

**Interfaces:**
- Produces: `SyncConfig` and `SyncReport`.
- Produces: `sync_index(config, client, now) -> SyncReport`.
- Produces: `load_existing_topic_documents(wiki_work_dir) -> dict[str, ParsedTopic]`.
- Produces: `build_topic_documents(state, existing_topics, bodies, synced_at) -> tuple[TopicDocument, ...]`.
- Produces: `render_and_validate_outputs(config, documents, state) -> dict[Path, str]`.
- Produces: `validate_existing_index(config) -> SyncReport`.
- Produces CLI modes `--dry-run`, `--validate-only`, and repeatable `--mark-reviewed PAGE_ID`.
- Consumes all interfaces from Tasks 1–6.

- [ ] **Step 1: Write a failing first-sync integration test**

```python
# tests/test_k1_activity_service.py
import json
from pathlib import Path

from tools.k1_activity_index.service import SyncConfig, sync_index


def _child(page_id, title, version=1):
    return {
        "id": page_id,
        "title": title,
        "status": "current",
        "space": "KEFU",
        "version": version,
        "url": f"https://wiki.example.test/pages/viewpage.action?pageId={page_id}",
    }


class FakeClient:
    def __init__(self, responses=None, pages=None):
        self.responses = responses or {
            "73598402": {"total": 1, "results": [_child("100", "K1 主题A")]},
            "100": {"total": 1, "results": [_child("101", "主题A商店")]},
            "101": {"total": 0, "results": []},
        }
        self.pages = pages or {
            "100": {"id": "100", "title": "K1 主题A", "body": "合成活动说明。"},
            "101": {"id": "101", "title": "主题A商店", "body": "合成商店规则。"},
        }
        self.page_calls = []

    def check(self):
        return None

    def children(self, page_id, limit):
        return self.responses[page_id]

    def page(self, page_id):
        self.page_calls.append(page_id)
        value = self.pages[page_id]
        if isinstance(value, Exception):
            raise value
        return value


def _config(tmp_path, dry_run=False, validate_only=False, mark_reviewed=()):
    return SyncConfig(
        root_page_id="73598402",
        wiki_work_dir=tmp_path / "wiki" / "work",
        state_path=tmp_path / ".cache" / "k1-activity-index" / "state.json",
        review_report_path=tmp_path / ".cache" / "k1-activity-index" / "review-report.json",
        child_limit=1000,
        dry_run=dry_run,
        validate_only=validate_only,
        mark_reviewed=mark_reviewed,
    )


def test_first_sync_writes_catalog_topic_state_and_review_report(tmp_path: Path):
    config = _config(tmp_path)
    report = sync_index(
        config,
        FakeClient(),
        lambda: "2026-07-29T12:00:00+08:00",
    )

    assert report.topic_count == 1
    assert report.page_count == 2
    assert (config.wiki_work_dir / "k1-activity-catalog.md").exists()
    assert (config.wiki_work_dir / "k1-activities" / "k1-activity-100.md").exists()
    state_text = config.state_path.read_text(encoding="utf-8")
    assert "合成活动说明" not in state_text
    report_data = json.loads(config.review_report_path.read_text(encoding="utf-8"))
    assert report_data["review_needed"] == ["100", "101"]
```

- [ ] **Step 2: Add concrete incremental and failure-safety tests**

Append:

```python
from tools.k1_activity_index.crawl import IncompleteTreeError
from tools.k1_activity_index.models import ConfluenceCommandError, PageUnavailableError


def test_second_sync_skips_bodies_when_versions_are_unchanged(tmp_path: Path):
    config = _config(tmp_path)
    sync_index(config, FakeClient(), lambda: "2026-07-29T12:00:00+08:00")
    second_client = FakeClient()

    sync_index(config, second_client, lambda: "2026-07-29T13:00:00+08:00")

    assert second_client.page_calls == []


def test_dry_run_checks_tree_without_fetching_body_or_writing(tmp_path: Path):
    config = _config(tmp_path, dry_run=True)
    client = FakeClient()

    report = sync_index(config, client, lambda: "2026-07-29T12:00:00+08:00")

    assert report.dry_run is True
    assert client.page_calls == []
    assert not config.state_path.exists()


def test_version_change_fetches_only_changed_page_and_preserves_curated_summary(tmp_path: Path):
    config = _config(tmp_path)
    sync_index(config, FakeClient(), lambda: "2026-07-29T12:00:00+08:00")
    topic_path = config.wiki_work_dir / "k1-activities" / "k1-activity-100.md"
    edited = topic_path.read_text(encoding="utf-8").replace(
        "主题A活动，包含商店/兑换等子活动入口。",
        "人工确认后的主题摘要。",
    )
    topic_path.write_text(edited, encoding="utf-8")
    changed_responses = {
        "73598402": {"total": 1, "results": [_child("100", "K1 主题A")]},
        "100": {"total": 1, "results": [_child("101", "主题A商店", version=2)]},
        "101": {"total": 0, "results": []},
    }
    changed_client = FakeClient(responses=changed_responses)

    sync_index(config, changed_client, lambda: "2026-07-29T13:00:00+08:00")

    assert changed_client.page_calls == ["101"]
    assert "人工确认后的主题摘要。" in topic_path.read_text(encoding="utf-8")


def test_incomplete_tree_leaves_existing_outputs_unchanged(tmp_path: Path):
    config = _config(tmp_path)
    sync_index(config, FakeClient(), lambda: "2026-07-29T12:00:00+08:00")
    catalog = config.wiki_work_dir / "k1-activity-catalog.md"
    original_catalog = catalog.read_text(encoding="utf-8")
    original_state = config.state_path.read_text(encoding="utf-8")
    broken = FakeClient(responses={
        "73598402": {"total": 2, "results": [_child("100", "K1 主题A")]},
    })

    with pytest.raises(IncompleteTreeError):
        sync_index(config, broken, lambda: "2026-07-29T13:00:00+08:00")

    assert catalog.read_text(encoding="utf-8") == original_catalog
    assert config.state_path.read_text(encoding="utf-8") == original_state


def test_403_is_recorded_but_transient_error_aborts(tmp_path: Path):
    config = _config(tmp_path)
    unavailable = FakeClient(pages={
        "100": {"id": "100", "title": "K1 主题A", "body": "合成活动说明。"},
        "101": PageUnavailableError("101", 403),
    })
    sync_index(config, unavailable, lambda: "2026-07-29T12:00:00+08:00")
    assert '"availability": "inaccessible"' in config.state_path.read_text(encoding="utf-8")

    second_root = tmp_path / "transient"
    transient_config = _config(second_root)
    transient = FakeClient(pages={
        "100": {"id": "100", "title": "K1 主题A", "body": "合成活动说明。"},
        "101": ConfluenceCommandError("synthetic network failure"),
    })
    with pytest.raises(ConfluenceCommandError, match="synthetic"):
        sync_index(
            transient_config,
            transient,
            lambda: "2026-07-29T12:00:00+08:00",
        )
    assert not transient_config.state_path.exists()
```

Add `import pytest` at the top of the test module.

- [ ] **Step 3: Run service tests and verify failure**

Run `python -m pytest tests/test_k1_activity_service.py -v`.

Expected: import fails because `service.py` is absent.

- [ ] **Step 4: Implement service records and orchestration**

Define the service records exactly:

```python
@dataclass(frozen=True)
class SyncConfig:
    root_page_id: str
    wiki_work_dir: Path
    state_path: Path
    review_report_path: Path
    child_limit: int
    dry_run: bool
    validate_only: bool
    mark_reviewed: tuple[str, ...]


@dataclass(frozen=True)
class SyncReport:
    root_page_id: str
    topic_count: int
    page_count: int
    new_count: int
    changed_count: int
    missing_count: int
    inaccessible_count: int
    review_needed: tuple[str, ...]
    truncated: bool
    dry_run: bool
```

Implement `sync_index` in this order:

1. If `validate_only`, parse and validate the existing catalog/topic pages and state without constructing a Confluence client.
2. Load previous state and existing topic documents.
3. Check the client connection and crawl the complete tree.
4. Compute the next state and content IDs.
5. For a non-dry run, fetch bodies for content IDs only. Convert explicit 403/404 into `inaccessible` state; re-raise other errors before rendering or writing. A dry run validates the full tree and delta without fetching bodies.
6. Apply `mark_reviewed` before constructing documents.
7. Build topic documents, reusing existing curated fields and unchanged child summaries.
8. Render and validate all Markdown, state JSON, and review report.
9. Produce the report.
10. If `dry_run` is false, pass outputs to `write_batch_atomic` with state inserted last.
11. Remove every body reference before returning.

All topic and child ordering is by normalized title, then numeric pageId.

Use this orchestration body:

```python
def sync_index(config: SyncConfig, client, now) -> SyncReport:
    if config.validate_only:
        return validate_existing_index(config)

    synced_at = now()
    previous = load_state(config.state_path, config.root_page_id)
    existing_topics = load_existing_topic_documents(config.wiki_work_dir)
    client.check()
    snapshot = crawl_tree(client, config.root_page_id, config.child_limit)
    next_state, changes = compute_next_state(previous, snapshot, synced_at)

    bodies = {}
    if not config.dry_run:
        for page_id in changes.content_ids:
            try:
                bodies[page_id] = client.page(page_id).get("body", "")
            except PageUnavailableError as error:
                next_state = mark_unavailable(
                    next_state,
                    page_id,
                    error.status_code,
                )

    next_state = mark_reviewed(next_state, config.mark_reviewed)
    documents = build_topic_documents(
        next_state,
        existing_topics,
        bodies,
        synced_at,
    )
    outputs = render_and_validate_outputs(config, documents, next_state)
    report = build_sync_report(next_state, changes, documents, config.dry_run)
    bodies.clear()

    if not config.dry_run:
        write_batch_atomic(outputs)
    return report
```

- [ ] **Step 5: Implement the CLI entry point**

`tools/sync_k1_activity_index.py`:

- resolves the repository root from `Path(__file__).resolve().parents[1]`;
- defaults Wiki output to `wiki/work`;
- defaults state/report to `.cache/k1-activity-index/`;
- defaults root pageId to `73598402` and child limit to 1000;
- resolves the CLI from `--confluence-cli` or `%USERPROFILE%/.skills/confluence/scripts/confluence.pyz`;
- reads process/User environment without displaying values;
- prints a UTF-8 JSON summary containing only counts, IDs, statuses, and paths;
- exits 0 on success and 1 on validation, connection, or sync failure.

Supported commands:

```powershell
python tools/sync_k1_activity_index.py --root-page-id 73598402
python tools/sync_k1_activity_index.py --root-page-id 73598402 --dry-run
python tools/sync_k1_activity_index.py --validate-only
python tools/sync_k1_activity_index.py --root-page-id 73598402 --mark-reviewed 100 --mark-reviewed 101
```

- [ ] **Step 6: Run focused and full tests**

```powershell
python -m pytest tests/test_k1_activity_service.py -v
python -m pytest tests -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit the sync command**

```powershell
git add tools/k1_activity_index/service.py tools/k1_activity_index/state.py tools/k1_activity_index/markdown.py tools/sync_k1_activity_index.py tests/test_k1_activity_service.py
git diff --cached --check
git commit -m "feat: add K1 activity sync command"
```

---

### Task 8: Local Search and Intent Routing

**Files:**
- Create: `tools/k1_activity_index/query.py`
- Create: `tools/search_k1_activity.py`
- Create: `tests/test_k1_activity_query.py`

**Interfaces:**
- Produces: `SearchDocument` and `SearchHit`.
- Produces: `load_search_documents(activity_dir) -> tuple[SearchDocument, ...]`.
- Produces: `search_index(activity_dir, query, limit=10) -> tuple[SearchHit, ...]`.
- CLI prints human-readable hits by default and machine-readable output with `--json`.

Define:

```python
@dataclass(frozen=True)
class SearchChild:
    page_id: str
    title: str
    role: str
    summary: str
    wiki_url: str


@dataclass(frozen=True)
class SearchDocument:
    page_id: str
    topic_title: str
    aliases: tuple[str, ...]
    tags: tuple[str, ...]
    summary: str
    local_path: Path
    wiki_url: str
    children: tuple[SearchChild, ...]


@dataclass(frozen=True)
class SearchHit:
    score: int
    match_kind: str
    topic_page_id: str
    topic_title: str
    child_page_id: str | None
    child_title: str | None
    local_path: Path
    wiki_url: str
```

- [ ] **Step 1: Write failing ranking tests and a complete local fixture**

```python
# tests/test_k1_activity_query.py
from pathlib import Path

import pytest

from tools.k1_activity_index.markdown import (
    ChildEntry,
    CuratedTopic,
    TopicDocument,
    render_topic_page,
)
from tools.k1_activity_index.models import PageState
from tools.k1_activity_index.query import search_index


def _state(page_id, title, topic_id, parent_id):
    return PageState(
        page_id=page_id,
        title=title,
        status="current",
        space="KEFU",
        version=1,
        url=f"https://wiki.example.test/pages/viewpage.action?pageId={page_id}",
        parent_id=parent_id,
        path=(title,),
        topic_id=topic_id,
        wiki_updated_at=None,
        aliases=(),
        availability="available",
        review_needed=False,
    )


def _write_topic(directory, topic_id, title, aliases, children):
    topic = _state(topic_id, title, topic_id, "73598402")
    document = TopicDocument(
        topic=topic,
        curated=CuratedTopic(
            summary=f"{title}主题活动。",
            aliases=aliases,
            tags=("K1", "活动", "通行证", "商店/兑换"),
            links=("[[k1-activity-catalog]]",),
            notes="",
        ),
        children=tuple(
            ChildEntry(
                _state(page_id, child_title, topic_id, topic_id),
                role,
                f"{child_title}的{role}规则入口。",
            )
            for page_id, child_title, role in children
        ),
        synced_at="2026-07-29T12:00:00+08:00",
    )
    path = directory / f"k1-activity-{topic_id}.md"
    path.write_text(render_topic_page(document), encoding="utf-8")


@pytest.fixture
def activity_index(tmp_path: Path):
    directory = tmp_path / "k1-activities"
    directory.mkdir()
    _write_topic(
        directory,
        "248877776",
        "K1 绯夜假面",
        ("绯夜假面", "假面节"),
        (
            ("248877789", "K1 绯夜通行证", "通行证"),
            ("248877804", "K1绯夜宝铺", "商店/兑换"),
        ),
    )
    _write_topic(
        directory,
        "233086310",
        "K1 冬雪新年",
        ("冬雪新年",),
        (("300000001", "K1 冬雪通行证", "通行证"),),
    )
    return directory


def test_exact_topic_then_alias_then_child_title_ranking(activity_index: Path):
    assert search_index(activity_index, "绯夜假面")[0].match_kind == "topic-exact"
    assert search_index(activity_index, "假面节")[0].match_kind == "alias-exact"
    child_hit = search_index(activity_index, "绯夜通行证")[0]
    assert child_hit.match_kind == "child-exact"
    assert child_hit.wiki_url.endswith("pageId=248877789")


def test_theme_plus_role_routes_to_relevant_child(activity_index: Path):
    hit = search_index(activity_index, "绯夜 + 商店")[0]
    assert hit.topic_title == "K1 绯夜假面"
    assert hit.child_title == "K1绯夜宝铺"
    assert hit.wiki_url.endswith("pageId=248877804")


def test_equal_scores_return_all_ambiguous_candidates(activity_index: Path):
    hits = search_index(activity_index, "通行证", limit=10)
    top_score = hits[0].score
    assert len([hit for hit in hits if hit.score == top_score]) == 2
```

- [ ] **Step 2: Run query tests and verify failure**

Run `python -m pytest tests/test_k1_activity_query.py -v`.

Expected: import fails because `query.py` is absent.

- [ ] **Step 3: Implement deterministic scoring**

Normalize full-width punctuation, whitespace, English case, and leading `K1`. Split combinations on whitespace, `+`, `＋`, comma, and Chinese comma.

Use these base scores:

```python
SCORES = {
    "topic-exact": 100,
    "alias-exact": 95,
    "child-exact": 90,
    "topic-child-combination": 88,
    "title-partial": 80,
    "all-tags": 70,
    "summary": 50,
}
```

Return the most specific Wiki URL: topic matches return the topic root URL; child and topic/role combination matches return the child URL. Sort by descending score, then normalized topic title, child title, and pageId. Keep all tied candidates.

- [ ] **Step 4: Implement the thin search CLI**

Support:

```powershell
python tools/search_k1_activity.py "绯夜 + 商店"
python tools/search_k1_activity.py "绯夜通行证" --json --top 5
```

Human output includes score, match kind, activity title, optional child title, local Markdown path, and Wiki URL. JSON output uses `ensure_ascii=False` and contains no page body.

- [ ] **Step 5: Run query and full tests**

```powershell
python -m pytest tests/test_k1_activity_query.py -v
python -m pytest tests -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit local search**

```powershell
git add tools/k1_activity_index/query.py tools/search_k1_activity.py tests/test_k1_activity_query.py
git diff --cached --check
git commit -m "feat: add K1 activity local search"
```

---

### Task 9: Initial Live Sync, Semantic Review, Persistent Routing, and Final Verification

**Files:**
- Modify: `.gitignore:10`
- Modify: `AGENTS.md:57`
- Modify: `wiki/index.md:12`
- Modify: `wiki/work/k1-confluence-routing.md:9,16-30`
- Modify: `wiki/log.md:4`
- Generate locally: `wiki/work/k1-activity-catalog.md`
- Generate locally: `wiki/work/k1-activities/k1-activity-*.md`
- Generate locally: `.cache/k1-activity-index/state.json`
- Generate locally: `.cache/k1-activity-index/review-report.json`

**Interfaces:**
- Consumes: the completed sync and query CLIs.
- Produces: the user-visible local index and permanent query routing instructions.
- Produces: no committed internal activity body or generated `wiki/work` page.

- [ ] **Step 1: Add the cache ignore rule and perform preflight checks**

Use `apply_patch` to add:

```gitignore
.cache/k1-activity-index/
```

Before a live call, read `%USERPROFILE%/.skills/confluence/SKILL.md` completely. Then run:

```powershell
git status --short
python -m pytest tests -v
python "$env:USERPROFILE/.skills/confluence/scripts/confluence.pyz" check
```

If the process does not inherit credentials, load the three values from Windows User scope into that command process without printing them. Expected connection result contains `"connection": "OK"`.

- [ ] **Step 2: Run a live dry-run and verify completeness**

```powershell
python tools/sync_k1_activity_index.py --root-page-id 73598402 --dry-run
```

Expected JSON conditions:

- `root_page_id` is `73598402`.
- `topic_count` is 62 for the verified 2026-07-29 snapshot. If the live count changed, compare it with the root `page children` result and use the verified live count.
- `page_count >= topic_count`.
- `truncated` is false.
- No credential value or body field appears.

- [ ] **Step 3: Run the initial local sync**

```powershell
python tools/sync_k1_activity_index.py --root-page-id 73598402
python tools/sync_k1_activity_index.py --validate-only
```

Expected: catalog, one file per first-level topic, state, and review report exist; validation exits 0.

- [ ] **Step 4: Review every generated topic in batches of at most 10**

Read `.cache/k1-activity-index/review-report.json`. For every first-level topic:

1. For each exact `pageId` in the report, bind it to PowerShell variable `$pageId` and run `python "$env:USERPROFILE/.skills/confluence/scripts/confluence.pyz" page get $pageId --format plain` with UTF-8 output.
2. Edit only the curated region using `apply_patch`.
3. Replace the draft theme summary with one factual sentence describing stable mechanics, not time, server, reward, or item values.
4. Add aliases supported by titles or page text.
5. Keep tags inside the approved taxonomy and include the activity name.
6. Check historical/obsolete labels against titles and page status.
7. Preserve generated pageId, version, path, URL, and review markers.
8. Run `python tools/sync_k1_activity_index.py --validate-only` after each batch.

After all entries in the report have been reviewed, clear exactly those flags:

```powershell
$reviewData = Get-Content -Raw -Encoding UTF8 '.cache/k1-activity-index/review-report.json' | ConvertFrom-Json
$reviewArguments = foreach ($pageId in $reviewData.review_needed) { '--mark-reviewed'; [string]$pageId }
python tools/sync_k1_activity_index.py --root-page-id 73598402 @reviewArguments
```

If Windows command length is exceeded, split `$reviewData.review_needed` into slices of 100 IDs and run the same command per slice. Completion condition: `review-report.json` contains an empty `review_needed` array.

- [ ] **Step 5: Add permanent query routing and knowledge-base links**

Add under the Query workflow in `AGENTS.md`:

```markdown
### K1 活动查询
1. 用户提到 K1 活动名、别名、子活动或机制时，先把用户问题原文作为参数运行 `python tools/search_k1_activity.py "用户问题原文" --json`。
2. 读取命中的 `wiki/work/k1-activities/` 主题页，再按问题意图读取命中的 Confluence 根页或子页。
3. 时间、服务器范围、奖励、道具 ID 等易变信息必须实时回源；本地摘要只用于路由。
4. 多个结果同分或接近时列出候选，不凭印象选择。
5. 回答同时引用本地主题页与实际读取的 Confluence URL。
6. 本地无命中时使用 Confluence 搜索，并把确认的新页面纳入下一次同步。
```

Apply these approved knowledge-base changes:

- Add `[[k1-activity-catalog]] — K1 活动主题、别名、机制标签与具体 Confluence 子页的本地路由目录。` to `wiki/index.md` under “项目组 wiki 口径”.
- Add `[[k1-activity-catalog]]` to the routing page frontmatter links and update the `K1活动` row with pageId `73598402` plus the new local catalog.
- Prepend a 2026-07-29 ingest entry to `wiki/log.md` listing the catalog, live topic/page counts, sync tools, query route, and confirmation that full bodies were not stored.

- [ ] **Step 6: Run representative query acceptance checks**

```powershell
python tools/search_k1_activity.py "绯夜假面" --json
python tools/search_k1_activity.py "绯夜通行证" --json
python tools/search_k1_activity.py "绯夜 + 商店" --json
python tools/search_k1_activity.py "通行证" --json --top 10
```

Expected:

- `绯夜假面` returns topic pageId `248877776` as `topic-exact`.
- `绯夜通行证` returns Wiki pageId `248877789` as `child-exact`.
- `绯夜 + 商店` returns `K1绯夜宝铺` pageId `248877804`.
- Generic `通行证` returns multiple candidates rather than choosing one silently.

- [ ] **Step 7: Run security, structure, and regression verification**

```powershell
python tools/sync_k1_activity_index.py --validate-only
python -m pytest tests -v
git diff --check -- AGENTS.md .gitignore wiki/index.md wiki/log.md
git status --short
```

Inspect state and generated pages:

```powershell
rg -n -i '"body"|"content"|"html"|CONFLUENCE_API_TOKEN|活动涉及服务器' .cache/k1-activity-index wiki/work/k1-activities
```

Expected: no matches. Verify topic count equals the number of `k1-activity-*.md` files and every descendant pageId appears under exactly one topic.

- [ ] **Step 8: Commit only clean task-owned tracked files**

The worktree already contains unrelated edits in `wiki/index.md` and `wiki/log.md`, including additions adjacent to the new log location. Do not stage either shared file. Commit only the clean task-owned files and inspect the staged diff:

```powershell
git add AGENTS.md .gitignore
git diff --cached --name-only
git diff --cached
```

The staged diff contains only:

- the K1 activity query section in `AGENTS.md`;
- the cache ignore rule.

The catalog row and ingest entry stay in the existing unstaged `wiki/index.md` and `wiki/log.md` changes. `wiki/work/k1-confluence-routing.md` and generated activity pages remain ignored/local. Commit:

```powershell
git commit -m "docs: route K1 activity queries through local index"
```

- [ ] **Step 9: Record final handoff evidence**

Report:

- commit hashes from Tasks 1–9;
- pytest pass count;
- live topic/page counts;
- zero remaining review flags;
- the four representative query results;
- confirmation that unrelated pre-existing worktree changes remain unstaged;
- confirmation that the new `wiki/index.md` and `wiki/log.md` hunks also remain unstaged to avoid mixing ownership;
- links to `wiki/work/k1-activity-catalog.md` and the design document.
