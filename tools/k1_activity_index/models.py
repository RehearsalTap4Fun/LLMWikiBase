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
    complete: bool = True


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
    complete: bool = False

    @classmethod
    def empty(cls, root_page_id: str):
        return cls(1, root_page_id, None, {}, False)


@dataclass(frozen=True)
class ChangeSet:
    new_ids: tuple[str, ...]
    version_changed_ids: tuple[str, ...]
    renamed_ids: tuple[str, ...]
    moved_ids: tuple[str, ...]
    missing_ids: tuple[str, ...]
    content_ids: tuple[str, ...]


class ConfluenceCommandError(RuntimeError):
    def __init__(self, message: str = "Confluence command failed", *, code: str = "confluence-command-failed"):
        self.code = code
        super().__init__(message)


class PageUnavailableError(ConfluenceCommandError):
    def __init__(self, page_id: str, status_code: int):
        self.page_id = page_id
        self.status_code = status_code
        super().__init__(f"Confluence page {page_id} is unavailable ({status_code})")
