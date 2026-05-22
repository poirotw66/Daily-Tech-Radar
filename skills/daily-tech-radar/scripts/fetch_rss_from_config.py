#!/usr/bin/env python3
"""Fetch enabled RSS feeds from config/rss_sources.yaml with per-feed metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_rss
from rss_config_io import load_rss_sources


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--insecure-skip-tls-verify", action="store_true")
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()

    all_items: list[dict] = []
    errors: list[dict] = []

    for source in load_rss_sources(args.config):
        if not source.get("enabled", True):
            continue
        url = source.get("url")
        if not url:
            continue
        try:
            root = fetch_rss.fetch_xml(url, args.timeout, args.insecure_skip_tls_verify)
            items = fetch_rss.parse_feed(root, url, args.limit, source.get("categories", []))
            for item in items:
                item["publisher"] = source.get("name") or item.get("publisher")
                item["source_config_priority"] = source.get("priority", "medium")
            all_items.extend(items)
        except Exception as exc:
            errors.append({"name": source.get("name"), "url": url, "error": str(exc)})

    if errors:
        print(json.dumps({"rss_errors": errors}, ensure_ascii=False), file=sys.stderr)
    if not all_items and errors:
        raise RuntimeError("All configured RSS feeds failed.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(all_items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"fetch_rss_from_config.py failed: {exc}", file=sys.stderr)
        raise
