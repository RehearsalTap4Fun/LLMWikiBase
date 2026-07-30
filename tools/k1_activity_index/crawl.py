from collections import deque

from .models import CrawlSnapshot, PageRecord


class IncompleteTreeError(RuntimeError):
    pass


class InvalidTreeError(RuntimeError):
    pass


def crawl_tree(reader, root_page_id: str, limit: int = 1000) -> CrawlSnapshot:
    pages = {}
    children_by_parent = {}
    queue = deque([(root_page_id, (), None)])

    while queue:
        parent_id, parent_path, inherited_topic_id = queue.popleft()
        response = reader.children(parent_id, limit)
        results = response.get("results", [])
        if response.get("complete", response.get("total") == len(results)) is not True:
            raise IncompleteTreeError(f"Child listing for {parent_id} is not complete")
        if response.get("total") != len(results):
            raise IncompleteTreeError(
                f"Child listing for {parent_id} returned "
                f"{len(results)} of {response.get('total')}"
            )

        child_ids = []
        for raw in results:
            page_id = str(raw["id"])
            if page_id in pages:
                if page_id in {parent_id, *parent_path_ids(parent_id, pages)}:
                    raise InvalidTreeError(f"Page {page_id} forms a cycle")
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

    return CrawlSnapshot(root_page_id, pages, children_by_parent, complete=True)


def parent_path_ids(page_id: str, pages: dict[str, PageRecord]) -> tuple[str, ...]:
    ancestors: list[str] = []
    current = pages.get(page_id)
    while current is not None:
        ancestors.append(current.page_id)
        current = pages.get(current.parent_id)
    return tuple(ancestors)
