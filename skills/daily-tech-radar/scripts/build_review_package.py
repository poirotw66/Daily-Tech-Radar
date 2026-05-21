#!/usr/bin/env python3
"""Build a Markdown review package from structured Daily Tech Radar JSON."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:80] or "daily-tech-radar"


def source_lines(sources: list[dict]) -> str:
    lines = []
    for idx, source in enumerate(sources, 1):
        trust = source.get("trust_level", "medium")
        title = source.get("title", "Untitled")
        url = source.get("url", "")
        publisher = source.get("publisher", "unknown")
        lines.append(f"{idx}. [{title}]({url}) - {publisher}, trust: {trust}")
    return "\n".join(lines) if lines else "- No sources provided."


def issue_lines(issues: list[dict]) -> str:
    if not issues:
        return "- No issues reported."
    lines = []
    for issue in issues:
        severity = issue.get("severity", "unknown")
        problem = issue.get("problem") or issue.get("text") or json.dumps(issue, ensure_ascii=False)
        fix = issue.get("suggested_fix", "")
        lines.append(f"- [{severity}] {problem}" + (f" Suggested fix: {fix}" if fix else ""))
    return "\n".join(lines)


def claim_table(rows: list[dict]) -> str:
    if not rows:
        return "| Claim | Source | Status | Note |\n|---|---|---|---|\n| 未提供 | 需要補來源 | needs_review | 請人工確認 |"
    output = ["| Claim | Source | Status | Note |", "|---|---|---|---|"]
    for row in rows:
        output.append(
            "| {claim} | {source} | {status} | {note} |".format(
                claim=str(row.get("claim", "")).replace("|", "/"),
                source=str(row.get("source", "")).replace("|", "/"),
                status=str(row.get("status", "needs_review")).replace("|", "/"),
                note=str(row.get("note", "")).replace("|", "/"),
            )
        )
    return "\n".join(output)


def build_package(data: dict) -> str:
    fact_check = data.get("fact_check", {})
    distribution = data.get("distribution", {})
    seo = data.get("seo", {})
    confirmations = data.get("user_confirmation_needed") or [
        "是否加入個人使用經驗或案例？",
        "是否有任何公司、客戶或工作內容需要刪除？",
        "是否同意目前選題與發布角度？",
    ]

    return f"""# 今日技術文章審稿包

## 1. 今日主題
{data.get("topic", "未命名主題")}

## 2. 為什麼選這題
{data.get("selection_reason", "尚未提供選題理由。")}

## 3. 來源清單
{source_lines(data.get("sources", []))}

## 4. 文章草稿
{data.get("article_markdown", "尚未提供文章草稿。")}

## 5. 事實檢查結果
Status: `{fact_check.get("status", "needs_revision")}`

{issue_lines(fact_check.get("issues", []))}

### Claim-Source Table
{claim_table(fact_check.get("claim_source_table", []))}

## 6. 需要你特別確認的地方
{chr(10).join(f"- {item}" for item in confirmations)}

## 7. LinkedIn 貼文
{distribution.get("linkedin", "待生成。")}

## 8. Threads 貼文
{distribution.get("threads", "待生成。")}

## 9. Facebook 社團貼文
{distribution.get("facebook", "待生成。")}

## 10. Newsletter 摘要
{distribution.get("newsletter", "待生成。")}

## 11. SEO Metadata
- Title: {seo.get("title", data.get("topic", ""))}
- Description: {seo.get("description", "")}
- Slug: {seo.get("slug", slugify(data.get("topic", "")))}
- Tags: {", ".join(seo.get("tags", []))}

## 12. 建議發布標籤
{", ".join(seo.get("tags", [])) or "AI Engineering, DevTools"}

## 13. 發布前 Checklist
- [ ] 主要事實都有來源
- [ ] 推論與個人判斷已清楚標示
- [ ] 沒有公司內部資訊或客戶資料
- [ ] 金融/企業情境已加入資料、權限、治理或合規限制
- [ ] 已補上必要的個人觀點
- [ ] 已確認是否發布到網站與社群
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Review package JSON")
    parser.add_argument("-o", "--output", type=Path, help="Markdown output path or directory")
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    markdown = build_package(data)

    output = args.output
    if output:
        if output.suffix.lower() != ".md":
            topic_slug = slugify(data.get("seo", {}).get("slug") or data.get("topic", "daily-tech-radar"))
            output = output / f"{date.today().isoformat()}-{topic_slug}.md"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown, encoding="utf-8")
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
