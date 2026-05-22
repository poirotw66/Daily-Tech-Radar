#!/usr/bin/env python3
"""Build a Traditional Chinese draft package from selected topic artifacts.

This deterministic draft is a scaffold for later LLM refinement. It keeps
professional terms in English and marks where user judgment should be added.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from draft_scaffolds import (
    application_for_angle,
    judgment_for_angle,
    resolve_angle,
    subtitle_for_angle,
    tldr_for_angle,
    why_notable_for_angle,
)


def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    return " ".join(text.split())


def load_sources(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("sources"), list):
        return data["sources"]
    raise ValueError(f"Unsupported sources JSON shape: {path}")


def primary_body_text(source: dict) -> tuple[str, str]:
    """Return (body_text, provenance_label)."""
    if source.get("page_fetch_status") == "ok" and source.get("page_text"):
        return str(source["page_text"]).strip(), "full_page"
    return clean_text(source.get("raw_summary", "")), "rss_summary"


def slugify(text: str) -> str:
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:80] or "daily-tech-radar"


def load_selected(scores: dict, candidates: list[dict]) -> dict:
    selected_id = scores.get("selected_candidate_id")
    for candidate in candidates:
        if candidate.get("candidate_id") == selected_id:
            return candidate
    return candidates[0]


def source_map(sources: list[dict]) -> dict[str, dict]:
    return {source.get("source_id"): source for source in sources}


def selected_sources(candidate: dict, sources_by_id: dict[str, dict]) -> list[dict]:
    return [sources_by_id[source_id] for source_id in candidate.get("required_sources", []) if source_id in sources_by_id]


def build_article(candidate: dict, sources: list[dict]) -> str:
    main_source = sources[0] if sources else {}
    title = candidate.get("title", "今日技術觀察")
    publisher = main_source.get("publisher", "來源")
    published_at = main_source.get("published_at") or "未標示日期"
    source_url = main_source.get("url", "")
    body_text, provenance = primary_body_text(main_source)
    angle = resolve_angle(candidate, sources)
    subtitle = subtitle_for_angle(angle)
    fetch_note = (
        "以下依每日流程擷取之官方頁面正文（已嘗試擷取 article/main，非 IDE 臨時抓取）。"
        if provenance == "full_page"
        else "以下僅依 RSS 摘要；全文擷取未成功，精修前請重跑 `run_daily_radar.sh` 並加上 `--insecure-skip-tls-verify`（macOS 常需要）。"
    )
    excerpt = body_text[:3500] + ("…" if len(body_text) > 3500 else "")
    tldr_lines = "\n".join(f"- {line}" for line in tldr_for_angle(angle, publisher, published_at, title))

    return f"""# {title}：{subtitle}

## TL;DR
{tldr_lines}

## 發生了什麼？

根據來源 [{title}]({source_url})，{fetch_note}

> {excerpt}

以下是基於上述來源內容產生的初步分析（推論段落需與事實分離閱讀）。

## 為什麼值得注意？

{why_notable_for_angle(angle)}

## 可以怎麼應用？

{application_for_angle(angle)}

## 限制與風險

- 本文 scaffold 不能取代官方文件、合約與你方法遵判定。
- 若 `page_fetch_status` 非 ok，勿對未讀段落做具體產品宣稱。
- 企業、金融或客戶資料場景：先處理 access control、audit trail、資料留存與人工審核，再擴大自動化。
- 勿把單一整合解讀為「已合規」或「可無審核上線」。

## 我的判斷

{judgment_for_angle(angle)}

需要你補充：可加入你自己的 Codex、Claude Code、Copilot 或內部流程經驗（避開機密）。

## 延伸閱讀

- [{title}]({source_url})
"""


def build_research(candidate: dict, sources: list[dict]) -> dict:
    angle = resolve_angle(candidate, sources)
    source_brief = []
    any_full_page = False
    for source in sources:
        body_text, provenance = primary_body_text(source)
        if provenance == "full_page":
            any_full_page = True
        source_brief.append(
            {
                "source_id": source.get("source_id"),
                "title": source.get("title"),
                "url": source.get("url"),
                "page_fetch_status": source.get("page_fetch_status"),
                "key_points": [
                    body_text[:1200],
                    "This source should be treated as primary evidence only for what it explicitly states.",
                ],
                "reliability": source.get("trust_level", "medium"),
            }
        )
    uncertainties = [
        "Claims about real-world impact should be reviewed against the full source before publishing.",
    ]
    if not any_full_page:
        uncertainties.insert(
            0,
            "Primary source full-page fetch failed or was skipped; draft uses RSS summary only.",
        )
    return {
        "topic": candidate.get("title"),
        "content_angle": angle,
        "core_question": candidate.get("core_question"),
        "source_brief": source_brief,
        "verified_facts": [
            f"Primary source title: {source.get('title')}" for source in sources
        ],
        "uncertainties": uncertainties,
        "possible_angles": [angle, candidate.get("content_angle")],
    }


def build_outline(candidate: dict, sources: list[dict]) -> str:
    title = candidate.get("title", "今日技術觀察")
    subtitle = subtitle_for_angle(resolve_angle(candidate, sources))
    return f"""# {title}：{subtitle}

## TL;DR
## 發生了什麼？
## 為什麼值得注意？
## 可以怎麼應用？
## 限制與風險
## 我的判斷
## 延伸閱讀
"""


def build_review_package_json(candidate: dict, sources: list[dict], article: str) -> dict:
    angle = resolve_angle(candidate, sources)
    subtitle = subtitle_for_angle(angle)
    title = candidate.get("title", "今日技術觀察")
    tags = ["Agent", "AI Engineering", "DevTools", "Automation"]
    return {
        "topic": title,
        "content_angle": angle,
        "selection_reason": f"Selected candidate `{candidate.get('candidate_id')}` because it scored highly on relevance, practicality, differentiation, business value, and source quality.",
        "sources": sources,
        "article_markdown": article,
        "fact_check": {
            "status": "needs_revision",
            "issues": [
                {
                    "severity": "medium",
                    "problem": "This is a deterministic scaffold. Review the full source before publishing.",
                    "suggested_fix": "Use prompts/research_topic.md and fact_check.md to verify concrete claims.",
                }
            ],
            "claim_source_table": [
                {
                    "claim": f"{source.get('publisher')} published {source.get('title')} on {source.get('published_at')}.",
                    "source": source.get("url"),
                    "status": "supported",
                    "note": "Based on collected source metadata.",
                }
                for source in sources
            ],
        },
        "distribution": {
            "linkedin": f"整理了「{title}」：{subtitle}。\n\n完整文章：{{URL placeholder}}",
            "threads": f"1/ 今日雷達：{title}\n2/ 角度：{subtitle}\n3/ 完整文章：{{URL placeholder}}",
            "facebook": f"這篇整理「{title}」的實務重點（{subtitle}）。\n\n完整文章：{{URL placeholder}}",
            "newsletter": f"本期觀察 {title}（{subtitle}）。",
        },
        "seo": {
            "title": f"{title}：{subtitle}",
            "description": f"依一級來源整理「{title}」的事實、應用情境、限制與判斷（{subtitle}）。",
            "slug": slugify(title),
            "tags": tags,
        },
        "user_confirmation_needed": [
            "是否要加入你自己的 Agent / Codex / Claude Code 使用經驗？",
            "是否要避免提到任何公司內部流程或客戶情境？",
            f"是否同意以「{subtitle}」為對外主軸？",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--run-date", default=date.today().isoformat())
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    candidates = json.loads(args.candidates.read_text(encoding="utf-8-sig"))
    scores = json.loads(args.scores.read_text(encoding="utf-8-sig"))
    sources = load_sources(args.sources)
    selected = load_selected(scores, candidates)
    sources_by_id = source_map(sources)
    selected_source_list = selected_sources(selected, sources_by_id)

    article = build_article(selected, selected_source_list)
    research = build_research(selected, selected_source_list)
    outline = build_outline(selected, selected_source_list)
    review_json = build_review_package_json(selected, selected_source_list, article)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{args.run_date}-{slugify(selected.get('title', 'topic'))}"

    (args.output_dir / f"{prefix}-research.json").write_text(json.dumps(research, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / f"{prefix}-outline.md").write_text(outline, encoding="utf-8")
    (args.output_dir / f"{prefix}-draft.md").write_text(article, encoding="utf-8")
    (args.output_dir / f"{prefix}-review-package.json").write_text(json.dumps(review_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"prefix": prefix, "selected_candidate_id": selected.get("candidate_id")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
