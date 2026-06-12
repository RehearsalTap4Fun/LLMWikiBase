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
