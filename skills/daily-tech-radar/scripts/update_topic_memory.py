#!/usr/bin/env python3
"""Maintain recent topic memory to reduce repeated daily topic selection."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def prune(entries: list[dict], days: int) -> list[dict]:
    cutoff = date.today() - timedelta(days=days)
    kept = []
    for entry in entries:
        try:
            entry_date = datetime.fromisoformat(entry.get("date", "")[:10]).date()
        except ValueError:
            continue
        if entry_date >= cutoff:
            kept.append(entry)
    return kept


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("--memory", type=Path, required=True)
    parser.add_argument("--run-date", default=date.today().isoformat())
    parser.add_argument("--keep-days", type=int, default=14)
    args = parser.parse_args()

    scores = load_json(args.scores, {})
    selected_id = scores.get("selected_candidate_id")
    selected = None
    for candidate in scores.get("score_table", []):
        if candidate.get("candidate_id") == selected_id:
            selected = candidate
            break

    memory = load_json(args.memory, {"topics": []})
    topics = prune(memory.get("topics", []), args.keep_days)

    if selected:
        topics = [topic for topic in topics if not (topic.get("date") == args.run_date and topic.get("candidate_id") == selected_id)]
        topics.append(
            {
                "date": args.run_date,
                "candidate_id": selected_id,
                "title": selected.get("title"),
                "content_angle": selected.get("content_angle"),
                "target_reader": selected.get("target_reader"),
                "weighted_score": selected.get("weighted_score"),
                "required_sources": selected.get("required_sources", []),
            }
        )

    args.memory.parent.mkdir(parents=True, exist_ok=True)
    args.memory.write_text(json.dumps({"topics": topics}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"memory": str(args.memory), "topics": len(topics)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
