#!/usr/bin/env python3
"""Build a human-readable source brief from normalized source records."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


def item_line(item: dict) -> str:
    title = item.get("title", "Untitled")
    url = item.get("url", "")
    publisher = item.get("publisher", "unknown")
    published = item.get("published_at") or "unknown date"
    source_type = item.get("source_type", "unknown")
    trust = item.get("trust_level", "medium")
    summary = (item.get("raw_summary") or "").replace("\n", " ").strip()
    if len(summary) > 260:
        summary = summary[:257].rstrip() + "..."
    return f"- [{title}]({url}) — {publisher}, {published}, `{source_type}`, trust: `{trust}`\n  {summary}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--run-date", default=date.today().isoformat())
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()

    items = json.loads(args.input.read_text(encoding="utf-8-sig"))
    type_counts = Counter(item.get("source_type", "unknown") for item in items)
    trust_counts = Counter(item.get("trust_level", "unknown") for item in items)
    by_type: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        by_type[item.get("source_type", "unknown")].append(item)

    lines = [
        f"# Daily Tech Radar Source Brief - {args.run_date}",
        "",
        "## Summary",
        f"- Total normalized sources: {len(items)}",
        f"- Source types: {', '.join(f'{k}={v}' for k, v in sorted(type_counts.items())) or 'none'}",
        f"- Trust levels: {', '.join(f'{k}={v}' for k, v in sorted(trust_counts.items())) or 'none'}",
        "",
        "## Suggested Next LLM Step",
        "Use `prompts/deduplicate_sources.md`, then `prompts/generate_candidates.md`, then `prompts/score_topics.md`.",
        "",
    ]

    for source_type in sorted(by_type):
        lines.append(f"## {source_type}")
        lines.extend(item_line(item) for item in by_type[source_type])
        lines.append("")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
