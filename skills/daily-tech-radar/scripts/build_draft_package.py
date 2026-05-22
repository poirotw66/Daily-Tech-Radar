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
from datetime import date
from pathlib import Path


EN_TERMS = {
    "Agent",
    "runtime",
    "orchestration",
    "access control",
    "workflow",
    "developer productivity",
    "enterprise automation",
    "LLM",
    "API",
    "MCP",
    "DevTools",
}


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
    fetch_note = (
        "以下依每日流程擷取之官方頁面全文整理（非 IDE 臨時抓取）。"
        if provenance == "full_page"
        else "以下僅依 RSS 摘要；全文擷取未成功，精修前請重跑 `enrich_primary_sources` 或檢查 TLS 設定。"
    )
    excerpt = body_text[:3500] + ("…" if len(body_text) > 3500 else "")
    core_question = candidate.get("core_question", "")

    return f"""# {title}：Agent workflow 進入 runtime 與治理階段

## TL;DR
- {publisher} 在 {published_at} 發布了與 `{title}` 相關的更新。
- 這個題目的重點不只是新功能，而是 Agent workflow 開始碰到 runtime、access control、tooling 與 enterprise automation 的落地問題。
- 我的初步判斷是：值得追蹤，但正式導入前要先確認資料權限、執行邊界、audit trail 與 human review。

## 發生了什麼？

根據來源 [{title}]({source_url})，{fetch_note}

> {excerpt}

以下是基於上述來源內容產生的初步分析（推論段落需與事實分離閱讀）。

用比較務實的角度看，它指向一個趨勢：Agent 不再只是 prompt 或單次任務，而是逐漸變成需要 runtime、orchestration、access control 與 observability 支撐的 workflow。

## 為什麼值得注意？

真正值得注意的不是「又多了一個 Agent 產品」，而是 Agent 開始被放進更接近 production 的環境。當 Agent 可以呼叫工具、存取私有 backend、執行 code delivery 或協助工程支援時，問題就不只是模型回答得好不好，而是整個流程能不能被控管。

這對工程團隊、PM 和自動化需求者都有意義：

- 對工程師來說，重點會從 prompt design 延伸到 runtime design。
- 對 PM 來說，Agent 能不能落地取決於流程邊界和責任分工。
- 對企業或金融場景來說，access control、log、review、data governance 會比 demo 效果更重要。

## 對工程流程的影響

如果這類 Agent workflow 成熟，開發流程可能會多一層「由 Agent 執行、由人類審核」的中介層。常見場景包括：

- 讓 Agent 先做 issue triage、log investigation 或初步 root cause analysis。
- 讓 Agent 產生 code change proposal，但由工程師做 final review。
- 讓 Agent 在受限 sandbox 或 runtime 裡執行工具，而不是直接接觸 production system。

這裡的關鍵不是完全自動化，而是把低價值、重複性的探索工作交給 Agent，同時保留 human-in-the-loop。

## 可以怎麼應用？

對小團隊來說，可以先從低風險 workflow 開始：

1. 文件整理：讓 Agent 根據 issue、PR、release note 產生摘要。
2. 工程支援：讓 Agent 協助查詢 log、整理可能原因，但不直接改 production。
3. 自動化顧問場景：把內部 SOP 拆成 Agent 可執行的小步驟，再加上人工批准點。

如果放到企業場景，第一個問題會是：Agent 能看到什麼資料、能呼叫哪些 tools、每一步有沒有可追蹤紀錄。

## 限制與風險

這類技術不適合一開始就接上高風險流程。幾個限制需要先講清楚：

- Access control：Agent 的權限必須比人更嚴格，而不是更寬。
- Auditability：每次 tool call、資料讀取、輸出建議都要能追蹤。
- Data governance：不能把客戶資料、內部機密或受監管資料丟進未確認的 runtime。
- Over-automation：如果沒有 review gate，很容易把錯誤自動化放大。

## 我的判斷

我會把這件事看成 Agent 從「可展示的 demo」走向「可治理的 workflow」的一個訊號。短期內，它最適合用在工程支援、開發輔助、文件整理和內部自動化；但如果要進企業或金融場景，真正的門檻會在權限、紀錄、審核和責任歸屬。

需要你補充：這裡可以加入你自己的使用經驗，例如目前用 Codex、Claude Code、GitHub Copilot 或內部自動化流程時，哪些步驟最適合交給 Agent，哪些仍然必須人工決策。

## 延伸閱讀

- [{title}]({source_url})
"""


def build_research(candidate: dict, sources: list[dict]) -> dict:
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
        "core_question": candidate.get("core_question"),
        "source_brief": source_brief,
        "verified_facts": [
            f"Primary source title: {source.get('title')}" for source in sources
        ],
        "uncertainties": uncertainties,
        "possible_angles": [
            "Agent workflow governance",
            "Runtime and access control",
            "Enterprise automation with human review",
        ],
    }


def build_outline(candidate: dict) -> str:
    title = candidate.get("title", "今日技術觀察")
    return f"""# {title}：Agent workflow 進入 runtime 與治理階段

## TL;DR
## 發生了什麼？
## 為什麼值得注意？
## 對工程流程的影響
## 可以怎麼應用？
## 限制與風險
## 我的判斷
## 延伸閱讀
"""


def build_review_package_json(candidate: dict, sources: list[dict], article: str) -> dict:
    tags = ["Agent", "AI Engineering", "DevTools", "Automation"]
    return {
        "topic": candidate.get("title"),
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
            "linkedin": f"Agent workflow 的重點正在從 demo 走向 runtime、access control 與 human review。\n\n我整理了 {candidate.get('title')} 對工程與企業自動化的意義。\n\n完整文章：{{URL placeholder}}",
            "threads": f"1/ 今天看到一個值得注意的 Agent workflow 更新：{candidate.get('title')}\n2/ 真正重要的不是 Agent 多會寫，而是 runtime、權限和 review gate 能不能管得住。\n3/ 完整文章：{{URL placeholder}}",
            "facebook": f"最近很多人在討論 Agent，我覺得可以從比較實務的角度看：runtime、權限、審核、紀錄。\n\n這篇整理 {candidate.get('title')} 可能帶來的啟發。\n\n完整文章：{{URL placeholder}}",
            "newsletter": f"本期觀察 {candidate.get('title')}，重點放在 Agent workflow、runtime、access control 與 enterprise automation。",
        },
        "seo": {
            "title": f"{candidate.get('title')}：Agent workflow 進入 runtime 與治理階段",
            "description": "從工程流程與企業自動化角度，分析 Agent workflow 為什麼開始需要 runtime、access control、auditability 與 human review。",
            "slug": slugify(candidate.get("title", "")),
            "tags": tags,
        },
        "user_confirmation_needed": [
            "是否要加入你自己的 Agent / Codex / Claude Code 使用經驗？",
            "是否要避免提到任何公司內部流程或客戶情境？",
            "是否同意把文章角度放在 runtime、權限與治理，而不是產品功能介紹？",
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
    outline = build_outline(selected)
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
