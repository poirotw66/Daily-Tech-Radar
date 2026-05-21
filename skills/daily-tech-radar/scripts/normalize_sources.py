#!/usr/bin/env python3
"""Normalize raw source items into stable Daily Tech Radar source records."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


TRUST_BY_TYPE = {
    "official_blog": "high",
    "docs": "high",
    "github": "high",
    "paper": "medium",
    "launch": "medium",
    "news": "medium",
    "discussion": "low",
}


def stable_id(title: str, url: str) -> str:
    parsed = urlparse(url)
    seed = f"{parsed.netloc.lower()}|{parsed.path.lower()}|{title.strip().lower()}"
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]


def normalize_item(item: dict) -> dict:
    title = str(item.get("title", "")).strip()
    url = str(item.get("url", "")).strip()
    source_type = str(item.get("source_type") or item.get("type") or "news").strip()
    publisher = str(item.get("publisher") or urlparse(url).netloc or "unknown").strip()
    fetched_at = item.get("fetched_at") or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    tags = item.get("tags") or []

    if not title:
        raise ValueError(f"source item missing title: {item}")
    if not url:
        raise ValueError(f"source item missing url: {item}")
    if not isinstance(tags, list):
        tags = [str(tags)]

    normalized = {
        "source_id": item.get("source_id") or stable_id(title, url),
        "title": title,
        "url": url,
        "source_type": source_type,
        "publisher": publisher,
        "published_at": item.get("published_at"),
        "fetched_at": fetched_at,
        "raw_summary": str(item.get("raw_summary") or item.get("summary") or "").strip(),
        "tags": [str(tag).strip() for tag in tags if str(tag).strip()],
        "language": item.get("language") or "en",
        "trust_level": item.get("trust_level") or TRUST_BY_TYPE.get(source_type, "medium"),
    }
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="JSON file containing a source object or array")
    parser.add_argument("-o", "--output", type=Path, help="Output JSON path")
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8-sig"))
    items = data if isinstance(data, list) else [data]
    normalized = [normalize_item(item) for item in items]

    output = json.dumps(normalized, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
