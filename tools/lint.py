# tools/lint.py
"""wiki 健康检查 CLI。纯本地文件操作，不联网。只读不自动改。

检查: 断链 / 孤立页 / frontmatter 缺字段 / 超期 / 低置信度。

用法:
    python tools/lint.py [--wiki DIR] [--domain D] [--stale-days N]
"""
import argparse
import datetime
import re

import frontmatter as fm

REQUIRED_FIELDS = ["title", "type", "domain", "source", "date", "confidence"]
_LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def lint(wiki_dir, domain=None, stale_days=180, today=None):
    if today is None:
        today = datetime.date.today()
    pages = fm.load_pages(wiki_dir, domain=domain)
    names = {p["name"] for p in pages}
    report = {"broken_links": [], "orphans": [], "missing_fields": [],
              "stale": [], "low_confidence": []}
    linked_to = set()
    has_outlink = {}

    for p in pages:
        targets = _LINK_RE.findall(p["body"])
        has_outlink[p["name"]] = bool(targets)
        for t in targets:
            t = t.strip()
            linked_to.add(t)
            if t not in names:
                report["broken_links"].append(f"{p['path']}: 断链 [[{t}]]")

    for p in pages:
        missing = [f for f in REQUIRED_FIELDS if f not in p["meta"]]
        if missing:
            report["missing_fields"].append(f"{p['path']}: 缺字段 {', '.join(missing)}")

        if str(p["meta"].get("confidence", "")).lower() == "low":
            report["low_confidence"].append(f"{p['path']}: confidence=low 待补证")

        date_val = p["meta"].get("date")
        if date_val:
            try:
                d = date_val if isinstance(date_val, datetime.date) else \
                    datetime.date.fromisoformat(str(date_val))
                if (today - d).days > stale_days:
                    report["stale"].append(f"{p['path']}: 已 {(today - d).days} 天未更新")
            except ValueError:
                report["missing_fields"].append(f"{p['path']}: date 格式非法 '{date_val}'")

        if p["name"] not in linked_to and not has_outlink[p["name"]]:
            report["orphans"].append(f"{p['path']}: 孤立页(无人链接且不链接他人)")

    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="wiki 健康检查")
    parser.add_argument("--wiki", default="wiki", help="wiki 目录(默认 wiki)")
    parser.add_argument("--domain", default=None, help="限定域: work/gaming/ai-llm")
    parser.add_argument("--stale-days", type=int, default=180, help="超期天数阈值(默认 180)")
    args = parser.parse_args(argv)
    report = lint(args.wiki, args.domain, args.stale_days)
    labels = {
        "broken_links": "断链", "orphans": "孤立页", "missing_fields": "缺字段",
        "stale": "陈旧页", "low_confidence": "低置信度",
    }
    total = 0
    for key, label in labels.items():
        items = report[key]
        total += len(items)
        if items:
            print(f"\n## {label} ({len(items)})")
            for s in items:
                print(f"  - {s}")
    print(f"\n共发现 {total} 个问题。" if total else "\n未发现问题，wiki 健康。")


if __name__ == "__main__":
    main()
