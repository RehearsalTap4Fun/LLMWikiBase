# tools/frontmatter.py
"""解析 markdown frontmatter 与扫描 wiki 目录的共享模块。纯本地文件操作，不联网。"""
import os
import yaml

SKIP_FILES = {"index.md", "log.md"}


def parse_markdown(text):
    """解析 markdown，返回 {"meta": dict, "body": str}。无 frontmatter 时 meta={}。"""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            try:
                meta = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                meta = {}
            if isinstance(meta, dict):
                return {"meta": meta, "body": parts[2]}
    return {"meta": {}, "body": text}


def load_pages(wiki_dir, domain=None):
    """扫描 wiki_dir 下的 .md 页面（排除 index.md/log.md）。
    domain 不为 None 时只返回该子目录下的页面。
    返回 [{"path","name","meta","body"}]。"""
    pages = []
    root = os.path.join(wiki_dir, domain) if domain else wiki_dir
    if not os.path.isdir(root):
        return pages
    for dirpath, _dirs, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".md") or fn in SKIP_FILES:
                continue
            path = os.path.join(dirpath, fn)
            with open(path, encoding="utf-8") as f:
                parsed = parse_markdown(f.read())
            pages.append({
                "path": path,
                "name": os.path.splitext(fn)[0],
                "meta": parsed["meta"],
                "body": parsed["body"],
            })
    return pages
