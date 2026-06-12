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

def test_lint_orphan_detection(tmp_path):
    wiki = tmp_path / "wiki"
    (wiki / "work").mkdir(parents=True)
    # hub links to leaf; lonely has no links in or out
    (wiki / "work" / "hub.md").write_text(
        "---\ntitle: Hub\ntype: project\ndomain: work\nsource: chat\n"
        "date: 2026-06-11\nconfidence: high\n---\n see [[leaf]]",
        encoding="utf-8")
    (wiki / "work" / "leaf.md").write_text(
        "---\ntitle: Leaf\ntype: project\ndomain: work\nsource: chat\n"
        "date: 2026-06-11\nconfidence: high\n---\n no links here",
        encoding="utf-8")
    (wiki / "work" / "lonely.md").write_text(
        "---\ntitle: Lonely\ntype: project\ndomain: work\nsource: chat\n"
        "date: 2026-06-11\nconfidence: high\n---\n alone",
        encoding="utf-8")
    report = L.lint(str(wiki), today=datetime.date(2026, 6, 11))
    orphans_str = " ".join(report["orphans"])
    assert "lonely.md" in orphans_str       # no in-links, no out-links -> orphan
    assert "hub.md" not in orphans_str       # has an out-link -> not orphan
    assert "leaf.md" not in orphans_str      # linked-to by hub -> not orphan
