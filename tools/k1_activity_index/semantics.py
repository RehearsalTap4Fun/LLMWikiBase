"""Deterministic, metadata-safe semantic drafts for K1 activity pages."""

from dataclasses import dataclass
import re
import unicodedata

from .models import PageRecord


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

_K1_PREFIX = re.compile(r"^k1", re.IGNORECASE)


@dataclass(frozen=True)
class SemanticDraft:
    summary: str
    aliases: tuple[str, ...]
    tags: tuple[str, ...]
    role: str
    lifecycle: str


def normalize_label(text: str) -> str:
    """Normalize an activity label without deriving any new wording."""
    normalized = unicodedata.normalize("NFKC", text).strip()
    normalized = _K1_PREFIX.sub("", normalized, count=1)
    return "".join(
        character
        for character in normalized
        if not character.isspace() and not unicodedata.category(character).startswith("P")
    )


def draft_page_semantics(page: PageRecord, body: str) -> SemanticDraft:
    """Classify a page with a closed taxonomy while retaining no body text."""
    searchable = f"{page.title}\n{body}".casefold()
    role = _first_matching_label(searchable, ROLE_RULES, fallback="其他")
    scenes = _matching_labels(searchable, SCENE_RULES)
    lifecycle = "历史/过期" if _contains_any(searchable, HISTORY_WORDS) else "当前"
    tags = ("K1", "活动", role, *scenes)
    if lifecycle == "历史/过期":
        tags += ("历史",)

    alias = normalize_label(page.title)
    aliases = (alias,) if alias else ()
    return SemanticDraft(
        summary=f"{page.title}的{role}规则入口。",
        aliases=aliases,
        tags=tags,
        role=role,
        lifecycle=lifecycle,
    )


def draft_topic_summary(topic: PageRecord, descendant_drafts) -> str:
    """Summarize a topic from its title and known child roles only."""
    title = normalize_label(topic.title)
    observed_roles = {draft.role for draft in descendant_drafts}
    roles = tuple(label for label, _ in ROLE_RULES if label in observed_roles)
    if roles:
        return f"{title}主题活动，包含{'、'.join(roles)}等子活动入口。"
    return f"{title}主题活动。"


def _first_matching_label(text: str, rules, fallback: str) -> str:
    for label, keywords in rules:
        if _contains_any(text, keywords):
            return label
    return fallback


def _matching_labels(text: str, rules) -> tuple[str, ...]:
    return tuple(label for label, keywords in rules if _contains_any(text, keywords))


def _contains_any(text: str, keywords) -> bool:
    return any(keyword.casefold() in text for keyword in keywords)
