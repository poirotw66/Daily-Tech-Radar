#!/usr/bin/env python3
"""Fetch enabled RSS feeds from config/rss_sources.yaml with per-feed metadata."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_rss


def parse_inline_list(value: str) -> list[str]:
    value = value.strip()
    if not (value.startswith("[") and value.endswith("]")):
        return []
    body = value[1:-1].strip()
    if not body:
        return []
    return [part.strip().strip("'\"") for part in body.split(",") if part.strip()]


def parse_rss_config(path: Path) -> list[dict]:
    sources: list[dict] = []
    current: dict | None = None
    in_sources = False

    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "rss_sources:":
            in_sources = True
            continue
        if stripped == "policy:":
            break
        if not in_sources:
            continue

        if re.match(r"^\s*-\s+name:\s*", line):
            if current:
                sources.append(current)
            current = {"enabled": True, "categories": []}
            current["name"] = stripped.split("name:", 1)[1].strip()
            continue
        if current is None or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key == "enabled":
            current[key] = value.lower() != "false"
        elif key == "categories":
            current[key] = parse_inline_list(value)
        else:
            current[key] = value

    if current:
        sources.append(current)
    return sources


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

    for source in parse_rss_config(args.config):
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
