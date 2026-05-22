#!/usr/bin/env python3
"""Check configured web pages for content changes (no RSS required)."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from html_extract import html_to_text
from http_fetch import fetch_bytes
from page_watch_io import load_page_watch


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def content_fingerprint(html: bytes, max_chars: int) -> tuple[str, str]:
    text = html_to_text(html.decode("utf-8", errors="replace"), max_chars)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return digest, text


def load_state(path: Path) -> dict:
    if not path.exists():
        return {"pages": {}}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def page_key(name: str) -> str:
    return hashlib.sha1(name.strip().lower().encode("utf-8")).hexdigest()[:12]


def build_source_item(page: dict, run_date: str, excerpt: str, signal: str) -> dict:
    summary = excerpt[:500] + ("…" if len(excerpt) > 500 else "")
    if signal == "content_changed":
        lead = f"Page content fingerprint changed since last check. Excerpt: {summary}"
    else:
        lead = f"First baseline stored for this page. Excerpt: {summary}"
    return {
        "title": f"{page['name']} — page update detected",
        "url": page["url"],
        "source_type": "official_blog",
        "publisher": page["name"],
        "published_at": run_date,
        "fetched_at": now_utc(),
        "raw_summary": lead,
        "tags": page.get("categories") or [],
        "language": "en",
        "trust_level": "high",
        "watch_signal": signal,
    }


def write_brief(path: Path, run_date: str, results: list[dict]) -> None:
    lines = [
        f"# Page Watch Brief — {run_date}",
        "",
        "## Summary",
        f"- Pages checked: {len(results)}",
        f"- Changes detected: {sum(1 for r in results if r.get('changed'))}",
        "",
    ]
    for row in results:
        status = "CHANGED" if row.get("changed") else ("BASELINE" if row.get("first_seen") else "unchanged")
        lines.append(f"## {row['name']} — {status}")
        lines.append(f"- URL: {row['url']}")
        lines.append(f"- Checked at: {row.get('checked_at', '')}")
        if row.get("error"):
            lines.append(f"- Error: {row['error']}")
        elif row.get("changed"):
            lines.append(f"- Previous hash: `{row.get('previous_hash', '')[:12]}…`")
            lines.append(f"- Current hash: `{row.get('content_hash', '')[:12]}…`")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path(__file__).resolve().parent.parent / "config" / "page_watch.yaml")
    parser.add_argument("--state", type=Path, default=Path(__file__).resolve().parent.parent / "memory" / "page_watch_state.json")
    parser.add_argument("--run-date", default=today_iso())
    parser.add_argument("--output-items", type=Path, help="JSON array of synthetic source items when changed")
    parser.add_argument("--output-brief", type=Path)
    parser.add_argument("--max-chars", type=int, default=12000)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--insecure-skip-tls-verify", action="store_true")
    parser.add_argument("--emit-baseline", action="store_true", help="Treat first-seen pages as changed (for testing)")
    args = parser.parse_args()

    pages = [p for p in load_page_watch(args.config) if p.get("enabled", True) and p.get("url")]
    state = load_state(args.state)
    state_pages = state.setdefault("pages", {})

    changed_items: list[dict] = []
    brief_rows: list[dict] = []

    for page in pages:
        name = page["name"]
        url = page["url"]
        key = page_key(name)
        row: dict = {
            "name": name,
            "url": url,
            "checked_at": now_utc(),
            "changed": False,
            "first_seen": False,
            "error": "",
        }
        body, error = fetch_bytes(
            url,
            timeout=args.timeout,
            insecure_skip_tls_verify=args.insecure_skip_tls_verify,
        )
        if body is None:
            row["error"] = error or "fetch failed"
            brief_rows.append(row)
            continue

        digest, text = content_fingerprint(body, args.max_chars)
        previous = state_pages.get(key, {})
        prev_hash = previous.get("content_hash", "")

        if not prev_hash:
            row["first_seen"] = True
            state_pages[key] = {
                "name": name,
                "url": url,
                "content_hash": digest,
                "last_checked_at": row["checked_at"],
                "last_changed_at": row["checked_at"],
            }
            if args.emit_baseline:
                row["changed"] = True
                changed_items.append(build_source_item(page, args.run_date, text, "first_baseline"))
            brief_rows.append(row)
            continue

        if digest != prev_hash:
            row["changed"] = True
            row["previous_hash"] = prev_hash
            row["content_hash"] = digest
            state_pages[key] = {
                "name": name,
                "url": url,
                "content_hash": digest,
                "last_checked_at": row["checked_at"],
                "last_changed_at": row["checked_at"],
            }
            changed_items.append(build_source_item(page, args.run_date, text, "content_changed"))
        else:
            state_pages[key]["last_checked_at"] = row["checked_at"]
            row["content_hash"] = digest

        brief_rows.append(row)

    state["updated_at"] = now_utc()
    save_state(args.state, state)

    if args.output_items:
        args.output_items.parent.mkdir(parents=True, exist_ok=True)
        args.output_items.write_text(json.dumps(changed_items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.output_brief:
        write_brief(args.output_brief, args.run_date, brief_rows)

    print(
        json.dumps(
            {
                "checked": len(brief_rows),
                "changed": len(changed_items),
                "output_items": str(args.output_items) if args.output_items else "",
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
