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
