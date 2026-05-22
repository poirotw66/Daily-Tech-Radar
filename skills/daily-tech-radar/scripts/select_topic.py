#!/usr/bin/env python3
"""Record the user's chosen topic candidate for a given run date."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Set selected_candidate_id in scores JSON after reviewing the daily briefs."
    )
    parser.add_argument("--scores", type=Path, required=True, help="YYYY-MM-DD-scores.json")
    parser.add_argument("--candidate-id", required=True, help="candidate_id from topic selection brief")
    parser.add_argument("--reason", default="", help="Optional note for selection_reason")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write updated scores (default: overwrite --scores)",
    )
    args = parser.parse_args()

    scores = json.loads(args.scores.read_text(encoding="utf-8-sig"))
    candidate_id = args.candidate_id.strip()
    table = scores.get("score_table") or []
    known = {str(row.get("candidate_id")) for row in table}
    if candidate_id not in known:
        print(f"Unknown candidate_id: {candidate_id}", flush=True)
        print(f"Known: {sorted(known)}", flush=True)
        return 1

    scores["selected_candidate_id"] = candidate_id
    scores["recommendation_only"] = False
    scores["user_selected"] = True
    if args.reason.strip():
        scores["selection_reason"] = args.reason.strip()
    else:
        scores["selection_reason"] = f"User selected `{candidate_id}` after reviewing daily briefs."

    out = args.output or args.scores
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(scores, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "selected_candidate_id": candidate_id, "output": str(out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
