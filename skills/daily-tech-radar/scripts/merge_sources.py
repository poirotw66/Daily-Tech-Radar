#!/usr/bin/env python3
"""Merge multiple source JSON arrays into one source item array."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()

    merged: list[dict] = []
    seen: set[str] = set()
    for path in args.inputs:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data, dict):
            data = [data]
        for item in data:
            url = str(item.get("url", "")).strip()
            title = str(item.get("title", "")).strip()
            key = url or title.lower()
            if not key or key in seen:
                continue
            seen.add(key)
            merged.append(item)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
