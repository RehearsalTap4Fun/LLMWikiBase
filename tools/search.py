# tools/search.py
"""BM25 关键词搜索 CLI。纯本地文件操作，不联网、不发送数据。

用法:
    python tools/search.py "关键词" [--wiki DIR] [--domain D] [--type T] [--top N]
"""
import argparse
import re
import sys

from rank_bm25 import BM25Plus

import frontmatter as fm

_TOKEN_RE = re.compile(r"[a-z0-9]+|[一-鿿]")


def tokenize(text):
    """小写化后切词：连续英数为一个 token，单个 CJK 字符各为一个 token。"""
    return _TOKEN_RE.findall(text.lower())


def search(wiki_dir, query, domain=None, type_filter=None, top=5):
    pages = fm.load_pages(wiki_dir, domain=domain)
    if type_filter:
        pages = [p for p in pages if p["meta"].get("type") == type_filter]
    if not pages:
        return []
    corpus = [tokenize(p["name"] + " " + str(p["meta"].get("title", "")) + " " + p["body"])
              for p in pages]
    bm25 = BM25Plus(corpus)
    scores = bm25.get_scores(tokenize(query))
    ranked = sorted(zip(pages, scores), key=lambda x: x[1], reverse=True)
    results = []
    for page, score in ranked[:top]:
        if score <= 0:
            continue
        body = page["body"].strip().replace("\n", " ")
        results.append({
            "name": page["name"],
            "title": page["meta"].get("title", page["name"]),
            "path": page["path"],
            "score": round(float(score), 3),
            "snippet": body[:120],
        })
    return results


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows 控制台默认 GBK，避免中文乱码
    parser = argparse.ArgumentParser(description="BM25 搜索 wiki 页面")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("--wiki", default="wiki", help="wiki 目录(默认 wiki)")
    parser.add_argument("--domain", default=None, help="限定域: work/gaming/ai-llm")
    parser.add_argument("--type", dest="type_filter", default=None, help="限定 type")
    parser.add_argument("--top", type=int, default=5, help="返回条数(默认 5)")
    args = parser.parse_args(argv)
    results = search(args.wiki, args.query, args.domain, args.type_filter, args.top)
    if not results:
        print("(无匹配结果)")
        return
    for r in results:
        print(f"[{r['score']}] {r['title']}  ({r['path']})")
        print(f"      {r['snippet']}")


if __name__ == "__main__":
    main()
