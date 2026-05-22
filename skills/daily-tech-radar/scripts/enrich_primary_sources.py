#!/usr/bin/env python3
"""Fetch full page text for the selected topic's primary source URLs.

RSS summaries are often too short for fact-checking and refinement. This step
downloads HTML for required sources on the winning candidate, extracts plain
text, and writes an enriched normalized source list for draft/refinement.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from http_fetch import fetch_bytes


ENRICH_TYPES = {"official_blog", "docs", "news", "launch"}
STRIP_TAGS = re.compile(r"<(script|style|noscript|svg)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def html_to_text(raw_html: str, max_chars: int) -> str:
    text = STRIP_TAGS.sub(" ", raw_html)
    text = TAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = WS_RE.sub(" ", text).strip()
    if len(text) > max_chars:
        return text[:max_chars] + "\n\n[truncated]"
    return text


def load_selected_source_ids(scores: dict, candidates: list[dict]) -> list[str]:
    selected_id = scores.get("selected_candidate_id")
    for candidate in candidates:
        if candidate.get("candidate_id") == selected_id:
            return list(candidate.get("required_sources") or [])
    if candidates:
        return list(candidates[0].get("required_sources") or [])
    return []


def should_enrich(source: dict) -> bool:
    source_type = str(source.get("source_type", "")).strip()
    if source_type not in ENRICH_TYPES:
        return False
    url = str(source.get("url", "")).strip()
    if not url.startswith(("http://", "https://")):
        return False
    return True


def enrich_source(
    source: dict,
    *,
    timeout: int,
    insecure_skip_tls_verify: bool,
    max_chars: int,
    max_retries: int,
) -> dict:
    enriched = dict(source)
    if not should_enrich(source):
        enriched["page_fetch_status"] = "skipped"
        enriched["page_text"] = ""
        enriched["page_fetch_error"] = ""
        return enriched

    url = source["url"]
    body, error = fetch_bytes(
        url,
        timeout=timeout,
        insecure_skip_tls_verify=insecure_skip_tls_verify,
        max_retries=max_retries,
    )
    enriched["page_fetched_at"] = now_utc()
    if body is None:
        enriched["page_fetch_status"] = "failed"
        enriched["page_text"] = ""
        enriched["page_fetch_error"] = error or "unknown error"
        return enriched

    try:
        html_doc = body.decode("utf-8", errors="replace")
    except Exception as exc:
        enriched["page_fetch_status"] = "failed"
        enriched["page_text"] = ""
        enriched["page_fetch_error"] = str(exc)
        return enriched

    enriched["page_fetch_status"] = "ok"
    enriched["page_text"] = html_to_text(html_doc, max_chars)
    enriched["page_fetch_error"] = ""
    return enriched


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--normalized", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--max-chars", type=int, default=20000)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--insecure-skip-tls-verify", action="store_true")
    args = parser.parse_args()

    sources: list[dict] = json.loads(args.normalized.read_text(encoding="utf-8-sig"))
    candidates: list[dict] = json.loads(args.candidates.read_text(encoding="utf-8-sig"))
    scores: dict = json.loads(args.scores.read_text(encoding="utf-8-sig"))

    selected_ids = set(load_selected_source_ids(scores, candidates))
    enriched_sources: list[dict] = []
    stats = {"ok": 0, "failed": 0, "skipped": 0}

    for source in sources:
        if source.get("source_id") in selected_ids:
            item = enrich_source(
                source,
                timeout=args.timeout,
                insecure_skip_tls_verify=args.insecure_skip_tls_verify,
                max_chars=args.max_chars,
                max_retries=args.max_retries,
            )
        else:
            item = dict(source)
            item.setdefault("page_fetch_status", "not_selected")
            item.setdefault("page_text", "")
            item.setdefault("page_fetch_error", "")
        status = item.get("page_fetch_status", "")
        if status in stats:
            stats[status] += 1
        enriched_sources.append(item)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "enriched_at": now_utc(),
        "selected_source_ids": sorted(selected_ids),
        "page_fetch_stats": stats,
        "sources": enriched_sources,
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "page_fetch_stats": stats}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
