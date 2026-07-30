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
        _page("K1 绿野通行证"),
        "活动时间 UTC 2026/7/28。服务器 103-127。通行证奖励道具 3320214。",
    )

    assert draft.aliases == ("绿野通行证",)
    assert draft.role == "通行证"
    assert "通行证" in draft.tags
    assert "2026/7/28" not in draft.summary
    assert "3320214" not in draft.summary


def test_topic_summary_uses_child_roles_not_volatile_body():
    topic = _page("K1 绿野假面")

    summary = draft_topic_summary(
        topic,
        [
            draft_page_semantics(_page("K1 绿野通行证", "101"), ""),
            draft_page_semantics(_page("K1 绿野宝铺", "102"), "兑换商店"),
        ],
    )

    assert summary == "绿野假面主题活动，包含通行证、商店/兑换等子活动入口。"


def test_topic_summary_uses_taxonomy_role_order_not_descendant_order():
    topic = _page("K1 绿野假面")
    drafts = (
        draft_page_semantics(_page("K1 绿野宝铺", "102"), "兑换商店"),
        draft_page_semantics(_page("K1 绿野通行证", "101"), ""),
    )

    assert draft_topic_summary(topic, drafts) == draft_topic_summary(topic, tuple(reversed(drafts)))


def test_normalization_removes_k1_prefix_spacing_and_punctuation():
    assert normalize_label(" K1：绿野 假面 ") == "绿野假面"


def test_low_signal_page_uses_safe_fallback_without_an_empty_alias():
    draft = draft_page_semantics(_page(" K1：— "), "")

    assert draft.aliases == ()
    assert draft.role == "其他"
    assert draft.lifecycle == "当前"
    assert draft.tags == ("K1", "活动", "其他")


def test_history_and_scene_keywords_are_exposed_as_controlled_labels():
    draft = draft_page_semantics(_page("K1 旧圣诞宝铺"), "")

    assert draft.lifecycle == "历史/过期"
    assert draft.tags == ("K1", "活动", "商店/兑换", "节日", "历史")
