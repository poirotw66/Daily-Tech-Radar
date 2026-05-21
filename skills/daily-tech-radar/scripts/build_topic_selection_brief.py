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

    lines = [
        "# Daily Tech Radar Topic Selection Brief",
        "",
        f"Selected candidate: `{scores.get('selected_candidate_id')}`",
        "",
        scores.get("selection_reason", ""),
        "",
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

    lines.extend(
        [
            "## Next Step",
            "",
            "Use `prompts/research_topic.md` on the selected candidate. If the selected topic feels weak, ask the user to pick another candidate before drafting.",
        ]
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
