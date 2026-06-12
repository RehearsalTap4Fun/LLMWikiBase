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
