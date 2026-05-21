#!/usr/bin/env python3
"""Build a source health report from Daily Tech Radar run logs."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--logs-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()

    log_files = sorted(args.logs_dir.glob("*-daily-run.json"), key=lambda path: path.stat().st_mtime, reverse=True)[: args.limit]
    by_step: dict[str, Counter] = defaultdict(Counter)
    rows: list[dict] = []

    for path in log_files:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        run_date = data.get("run_date", path.name)
        for step in data.get("steps", []):
            name = step.get("name", "unknown")
            status = step.get("status", "unknown")
            by_step[name][status] += 1
            rows.append({"run_date": run_date, "step": name, "status": status, "seconds": step.get("seconds")})

    lines = [
        "# Daily Tech Radar Source Health Report",
        "",
        f"Runs analyzed: {len(log_files)}",
        "",
        "## Summary",
        "",
        "| Step | Status | Count |",
        "|---|---|---:|",
    ]
    for step in sorted(by_step):
        for status, count in sorted(by_step[step].items()):
            lines.append(f"| {step} | {status} | {count} |")

    lines.extend(["", "## Recent Runs", "", "| Run date | Step | Status | Seconds |", "|---|---|---|---:|"])
    for row in rows[:100]:
        lines.append(f"| {row['run_date']} | {row['step']} | {row['status']} | {row.get('seconds') or 0} |")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(str(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
