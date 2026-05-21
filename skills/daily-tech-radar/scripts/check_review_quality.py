#!/usr/bin/env python3
"""Check a refined Daily Tech Radar review package for basic quality gates."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_PATTERNS = {
    "我的判斷": r"我的判斷",
    "限制與風險": r"限制與風險",
    "需要人工確認": r"需要人工確認",
    "fact-check table": r"\|\s*Claim\s*\|\s*Source\s*\|\s*Status\s*\|\s*Note\s*\|",
    "review checklist": r"發布前 Checklist",
}

FORBIDDEN_TERMS = [
    "革命性",
    "顛覆",
    "史詩級",
    "保證",
    "必然",
    "完全取代",
    "無痛導入",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    args = parser.parse_args()

    text = args.package.read_text(encoding="utf-8-sig")
    issues: list[str] = []

    for label, pattern in REQUIRED_PATTERNS.items():
        if not re.search(pattern, text, flags=re.IGNORECASE):
            issues.append(f"Missing required quality marker: {label}")

    for term in FORBIDDEN_TERMS:
        if term in text:
            issues.append(f"Forbidden or risky term found: {term}")

    if "http" not in text:
        issues.append("No source URL found.")

    if issues:
        print("Quality check failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Review package quality gates look good.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
