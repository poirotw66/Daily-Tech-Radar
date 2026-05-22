#!/usr/bin/env python3
"""Build a Markdown topic-selection brief from scored candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("scores_json", type=Path)
    parser.add_argument("--sources", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()

    scores = json.loads(args.scores_json.read_text(encoding="utf-8-sig"))
    source_map = {}
    if args.sources and args.sources.exists():
        sources = json.loads(args.sources.read_text(encoding="utf-8-sig"))
        source_map = {source.get("source_id"): source for source in sources}

    selected = scores.get("selected_candidate_id")
    recommended = scores.get("recommended_candidate_id")
    if scores.get("recommendation_only"):
        header = (
            "## Your decision\n\n"
            "No topic is selected yet. Read the candidates below, pick one `candidate_id`, then run:\n\n"
            "```bash\n"
            "CANDIDATE_ID=<candidate_id> ./scripts/run_article_from_pick.sh\n"
            "```\n\n"
            f"System ranking suggestion (optional): `{recommended}`\n"
        )
        selected_line = "_Pending your pick_"
    else:
        header = ""
        selected_line = f"`{selected}`"

    lines = [
        "# Daily Tech Radar Topic Selection Brief",
        "",
        f"Selected candidate: {selected_line}",
        "",
        scores.get("selection_reason", ""),
        "",
        header,
        "## Candidates",
        "",
    ]

    for candidate in scores.get("score_table", []):
        lines.extend(
            [
                f"### {candidate.get('candidate_id')}: {candidate.get('title')}",
                "",
                f"- Weighted score: `{candidate.get('weighted_score')}`",
                f"- Target reader: `{candidate.get('target_reader')}`",
                f"- Angle: `{candidate.get('content_angle')}`",
                f"- Core question: {candidate.get('core_question')}",
                f"- Why now: {candidate.get('why_now')}",
                "",
                "| Dimension | Score |",
                "|---|---:|",
            ]
        )
        for key, value in (candidate.get("scores") or {}).items():
            lines.append(f"| {key} | {value} |")
        lines.extend(["", "Sources:"])
        for source_id in candidate.get("required_sources", []):
            source = source_map.get(source_id)
            if source:
                lines.append(f"- [{source.get('title')}]({source.get('url')}) — {source.get('publisher')}")
            else:
                lines.append(f"- `{source_id}`")
        lines.append("")

    if scores.get("recommendation_only"):
        next_step = (
            "## Next Step",
            "",
            "Choose one candidate, run `run_article_from_pick.sh`, then refine with `prompts/refine_review_package.md`.",
        )
    else:
        next_step = (
            "## Next Step",
            "",
            "Use `prompts/research_topic.md` on the selected candidate, or run `run_article_from_pick.sh` if you changed the pick.",
        )
    lines.extend(next_step)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
