"""Command-line entry point for offline K1 activity routing."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.k1_activity_index.query import search_index  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search the local K1 activity index")
    parser.add_argument("query", help="activity name, alias, child page, or mechanism")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--top", type=_positive_int, default=10, metavar="N")
    parser.add_argument(
        "--activity-dir",
        type=Path,
        default=REPOSITORY_ROOT / "wiki" / "work" / "k1-activities",
        help="directory containing managed k1-activity-<pageId>.md files",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    _configure_utf8_stdout()
    arguments = _parser().parse_args(argv)
    try:
        hits = search_index(arguments.activity_dir, arguments.query, arguments.top)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        if arguments.as_json:
            print(json.dumps({"status": "error", "message": str(error)}, ensure_ascii=False))
        else:
            print(f"Error: {error}", file=sys.stderr)
        return 1

    if arguments.as_json:
        print(json.dumps([_json_hit(hit) for hit in hits], ensure_ascii=False, sort_keys=True))
    elif hits:
        for hit in hits:
            print(_human_hit(hit))
    else:
        print("No local K1 activity matches.")
    return 0


def _positive_int(value: str) -> int:
    result = int(value)
    if result <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return result


def _json_hit(hit) -> dict[str, object]:
    payload = asdict(hit)
    payload["local_path"] = str(hit.local_path)
    return payload


def _human_hit(hit) -> str:
    child = f"\n  child: {hit.child_title}" if hit.child_title else ""
    return (
        f"[{hit.score}] {hit.match_kind}\n"
        f"  activity: {hit.topic_title}{child}\n"
        f"  local: {hit.local_path}\n"
        f"  wiki: {hit.wiki_url}"
    )


def _configure_utf8_stdout() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
