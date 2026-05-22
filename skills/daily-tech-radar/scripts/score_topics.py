#!/usr/bin/env python3
"""Calculate weighted Daily Tech Radar topic scores from candidate JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_WEIGHTS = {
    "relevance": 0.25,
    "timeliness": 0.15,
    "practicality": 0.20,
    "differentiation": 0.20,
    "business_value": 0.10,
    "source_quality": 0.10,
}


def load_weights(path: Path | None) -> dict[str, float]:
    if not path or not path.exists():
        return DEFAULT_WEIGHTS

    weights: dict[str, float] = {}
    in_weights = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line == "weights:":
            in_weights = True
            continue
        if in_weights and raw_line and not raw_line.startswith(" "):
            break
        if in_weights and ":" in line:
            key, value = line.split(":", 1)
            try:
                weights[key.strip()] = float(value.strip())
            except ValueError:
                pass
    return weights or DEFAULT_WEIGHTS


def score_candidate(candidate: dict, weights: dict[str, float]) -> dict:
    scores = candidate.get("scores") or {}
    weighted = 0.0
    missing = []
    for key, weight in weights.items():
        if key not in scores:
            missing.append(key)
            continue
        weighted += float(scores[key]) * weight

    memory_penalty = float(candidate.get("memory_penalty") or 0)
    adjusted = max(0.0, weighted - (memory_penalty * 0.05))

    result = dict(candidate)
    result["weighted_score"] = round(adjusted, 3)
    result["base_weighted_score"] = round(weighted, 3)
    result["missing_score_fields"] = missing
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidates", type=Path, help="JSON file containing candidate objects")
    parser.add_argument("--scoring", type=Path, help="Path to scoring.yaml")
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument(
        "--recommendation-only",
        action="store_true",
        help="Rank candidates but do not set selected_candidate_id (human picks later)",
    )
    args = parser.parse_args()

    candidates = json.loads(args.candidates.read_text(encoding="utf-8"))
    if not isinstance(candidates, list):
        candidates = candidates.get("candidates", [])

    weights = load_weights(args.scoring)
    scored = [score_candidate(candidate, weights) for candidate in candidates]
    scored.sort(key=lambda item: item.get("weighted_score", 0), reverse=True)

    top = scored[0] if scored else None
    if args.recommendation_only:
        selected_id = None
        reason = (
            "Automated ranking only. Review the topic selection brief and pick a candidate "
            "before running the article pipeline (select_topic.py / run_article_from_pick.sh)."
        )
        if top:
            reason += f" Top recommendation: `{top.get('candidate_id')}` ({top.get('title')})."
    else:
        selected_id = top["candidate_id"] if top else None
        reason = (
            f"Auto-selected highest weighted score ({top.get('weighted_score')})."
            if top
            else "No candidates to score."
        )

    payload = {
        "selected_candidate_id": selected_id,
        "recommendation_only": args.recommendation_only,
        "recommended_candidate_id": top["candidate_id"] if top else None,
        "score_table": scored,
        "selection_reason": reason,
    }

    output = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
