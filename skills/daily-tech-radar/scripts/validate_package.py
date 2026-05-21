#!/usr/bin/env python3
"""Validate that a Daily Tech Radar review package contains required sections."""

from __future__ import annotations

import argparse
from pathlib import Path


REQUIRED_SECTIONS = [
    "## 1. 今日主題",
    "## 2. 為什麼選這題",
    "## 3. 來源清單",
    "## 4. 文章草稿",
    "## 5. 事實檢查結果",
    "## 6. 需要你特別確認的地方",
    "## 7. LinkedIn 貼文",
    "## 8. Threads 貼文",
    "## 9. Facebook 社團貼文",
    "## 10. Newsletter 摘要",
    "## 11. SEO Metadata",
    "## 12. 建議發布標籤",
    "## 13. 發布前 Checklist",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    args = parser.parse_args()

    text = args.package.read_text(encoding="utf-8")
    missing = [section for section in REQUIRED_SECTIONS if section not in text]

    if missing:
        print("Missing sections:")
        for section in missing:
            print(f"- {section}")
        return 1

    print("Review package structure looks good.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
