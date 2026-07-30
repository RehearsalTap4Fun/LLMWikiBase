import pytest

from tools.k1_activity_index.crawl import (
    IncompleteTreeError,
    InvalidTreeError,
    crawl_tree,
)


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
    reader = FakeReader(
        {
            "73598402": {
                "total": 2,
                "results": [_page("100", "Topic A"), _page("200", "Topic B")],
            },
            "100": {"total": 1, "results": [_page("101", "A Store")]},
            "101": {"total": 0, "results": []},
            "200": {"total": 0, "results": []},
        }
    )

    snapshot = crawl_tree(reader, "73598402")

    assert snapshot.pages["100"].topic_id == "100"
    assert snapshot.pages["101"].topic_id == "100"
    assert snapshot.pages["101"].path == ("Topic A", "A Store")
    assert snapshot.pages["200"].topic_id == "200"
    assert snapshot.children_by_parent["73598402"] == ("100", "200")


def test_crawl_rejects_server_side_truncation():
    reader = FakeReader(
        {
            "73598402": {"total": 2, "results": [_page("100", "Topic A")]},
        }
    )

    with pytest.raises(IncompleteTreeError, match="73598402"):
        crawl_tree(reader, "73598402")


def test_crawl_rejects_a_page_with_multiple_parents():
    reader = FakeReader(
        {
            "73598402": {
                "total": 2,
                "results": [_page("100", "Topic A"), _page("200", "Topic B")],
            },
            "100": {"total": 1, "results": [_page("300", "Shared page")]},
            "200": {"total": 1, "results": [_page("300", "Shared page")]},
            "300": {"total": 0, "results": []},
        }
    )

    with pytest.raises(InvalidTreeError, match="300"):
        crawl_tree(reader, "73598402")
