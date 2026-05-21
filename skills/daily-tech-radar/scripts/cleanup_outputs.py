#!/usr/bin/env python3
"""Clean generated Daily Tech Radar output/data files older than N days."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path


TARGET_DIRS = [
    "data/sources",
    "data/normalized",
    "output/source_briefs",
    "output/candidates",
    "output/drafts",
    "output/review_packages",
    "output/refinements",
    "output/logs",
    "output/source_health",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-dir", type=Path, required=True)
    parser.add_argument("--keep-days", type=int, default=14)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cutoff = datetime.now().timestamp() - (args.keep_days * 86400)
    removed = []
    for relative in TARGET_DIRS:
        root = args.skill_dir / relative
        if not root.exists():
            continue
        for path in sorted(root.rglob("*"), reverse=True):
            if path.is_file() and path.stat().st_mtime < cutoff:
                removed.append(str(path))
                if not args.dry_run:
                    path.unlink()
        for path in sorted(root.rglob("*"), reverse=True):
            if path.is_dir() and not any(path.iterdir()):
                if not args.dry_run:
                    path.rmdir()

    action = "Would remove" if args.dry_run else "Removed"
    print(f"{action} {len(removed)} files older than {args.keep_days} days.")
    for path in removed[:200]:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
