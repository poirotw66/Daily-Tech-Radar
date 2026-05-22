#!/usr/bin/env python3
"""Check configured web pages for content changes (no RSS required).

Primary signal: new article links on listing pages (Claude Blog, Anthropic Newsroom).
Fallback: content fingerprint when link extraction finds nothing.
"""

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
from page_link_extract import extract_article_links
from page_watch_io import load_page_watch


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def content_fingerprint(html: bytes, max_chars: int) -> tuple[str, str]:
    text = html_to_text(html.decode("utf-8", errors="replace"), max_chars)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return digest, text


def link_urls(links: list[dict]) -> list[str]:
    return sorted({str(item["url"]) for item in links if item.get("url")})


def load_state(path: Path) -> dict:
    if not path.exists():
        return {"pages": {}}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def page_key(name: str) -> str:
    return hashlib.sha1(name.strip().lower().encode("utf-8")).hexdigest()[:12]


def build_link_source_item(page: dict, run_date: str, link: dict) -> dict:
    title = link.get("title") or "New listing link"
    url = link["url"]
    return {
        "title": title,
        "url": url,
        "source_type": "official_blog",
        "publisher": page["name"],
        "published_at": run_date,
        "fetched_at": now_utc(),
        "raw_summary": f"New link detected on {page['name']} listing page ({page['url']}).",
        "tags": page.get("categories") or [],
        "language": "en",
        "trust_level": "high",
        "watch_signal": "new_listing_link",
    }


def build_fingerprint_source_item(page: dict, run_date: str, excerpt: str, signal: str) -> dict:
    summary = excerpt[:500] + ("…" if len(excerpt) > 500 else "")
    if signal == "content_changed":
        lead = f"Page content fingerprint changed (no new links parsed). Excerpt: {summary}"
    else:
        lead = f"First baseline stored. Excerpt: {summary}"
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
        f"- Pages with changes: {sum(1 for r in results if r.get('changed'))}",
        f"- New article links total: {sum(len(r.get('new_links') or []) for r in results)}",
        "",
        "Detection uses **article link list** comparison on listing pages; fingerprint is fallback only.",
        "",
    ]
    for row in results:
        if row.get("error"):
            status = "ERROR"
        elif row.get("first_seen"):
            status = "BASELINE"
        elif row.get("changed"):
            status = "CHANGED"
        else:
            status = "unchanged"
        lines.append(f"## {row['name']} — {status}")
        lines.append(f"- URL: {row['url']}")
        lines.append(f"- Checked at: {row.get('checked_at', '')}")
        lines.append(f"- Mode: {row.get('mode', 'links')}")
        lines.append(f"- Tracked links: {row.get('link_count', 0)}")
        if row.get("error"):
            lines.append(f"- Error: {row['error']}")
        new_links = row.get("new_links") or []
        if new_links:
            lines.append("- New links:")
            for link in new_links:
                title = link.get("title") or link["url"]
                lines.append(f"  - [{title}]({link['url']})")
        elif row.get("changed") and row.get("mode") == "fingerprint":
            lines.append(f"- Content hash changed: `{str(row.get('content_hash', ''))[:12]}…`")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def evaluate_page(
    page: dict,
    body: bytes,
    previous: dict,
    *,
    max_chars: int,
    emit_baseline: bool,
    run_date: str,
    link_limit: int,
) -> tuple[dict, list[dict], dict]:
    """Return (brief_row, changed_source_items, new_state_slice)."""
    name = page["name"]
    url = page["url"]
    html = body.decode("utf-8", errors="replace")
    links = extract_article_links(html, url, limit=link_limit)
    current_urls = link_urls(links)
    digest, text = content_fingerprint(body, max_chars)

    row: dict = {
        "name": name,
        "url": url,
        "checked_at": now_utc(),
        "changed": False,
        "first_seen": False,
        "error": "",
        "link_count": len(current_urls),
        "new_links": [],
        "mode": "links",
        "content_hash": digest,
    }
    items: list[dict] = []

    prev_urls = previous.get("article_link_urls") or []
    has_link_baseline = bool(prev_urls)

    if current_urls:
        if not has_link_baseline:
            row["first_seen"] = True
            new_state = {
                "name": name,
                "url": url,
                "article_link_urls": current_urls,
                "article_links": links,
                "content_hash": digest,
                "last_checked_at": row["checked_at"],
                "last_changed_at": row["checked_at"],
            }
            if emit_baseline:
                row["changed"] = True
                for link in links[:5]:
                    items.append(build_link_source_item(page, run_date, link))
            return row, items, new_state

        new_url_set = sorted(set(current_urls) - set(prev_urls))
        if new_url_set:
            row["changed"] = True
            link_by_url = {link["url"]: link for link in links}
            row["new_links"] = [link_by_url[u] for u in new_url_set if u in link_by_url]
            for link_url in new_url_set:
                items.append(build_link_source_item(page, run_date, link_by_url[link_url]))
            new_state = {
                "name": name,
                "url": url,
                "article_link_urls": current_urls,
                "article_links": links,
                "content_hash": digest,
                "last_checked_at": row["checked_at"],
                "last_changed_at": row["checked_at"],
            }
            return row, items, new_state

        new_state = {
            "name": name,
            "url": url,
            "article_link_urls": current_urls,
            "article_links": links,
            "content_hash": digest,
            "last_checked_at": row["checked_at"],
            "last_changed_at": previous.get("last_changed_at", row["checked_at"]),
        }
        return row, items, new_state

    # Fallback: no links parsed
    row["mode"] = "fingerprint"
    prev_hash = previous.get("content_hash", "")
    if not prev_hash:
        row["first_seen"] = True
        new_state = {
            "name": name,
            "url": url,
            "article_link_urls": [],
            "article_links": [],
            "content_hash": digest,
            "last_checked_at": row["checked_at"],
            "last_changed_at": row["checked_at"],
        }
        if emit_baseline:
            row["changed"] = True
            items.append(build_fingerprint_source_item(page, run_date, text, "first_baseline"))
        return row, items, new_state

    if digest != prev_hash:
        row["changed"] = True
        items.append(build_fingerprint_source_item(page, run_date, text, "content_changed"))
        new_state = {
            "name": name,
            "url": url,
            "article_link_urls": [],
            "article_links": [],
            "content_hash": digest,
            "last_checked_at": row["checked_at"],
            "last_changed_at": row["checked_at"],
        }
        return row, items, new_state

    new_state = dict(previous)
    new_state["last_checked_at"] = row["checked_at"]
    new_state["content_hash"] = digest
    return row, items, new_state


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path(__file__).resolve().parent.parent / "config" / "page_watch.yaml")
    parser.add_argument("--state", type=Path, default=Path(__file__).resolve().parent.parent / "memory" / "page_watch_state.json")
    parser.add_argument("--run-date", default=today_iso())
    parser.add_argument("--output-items", type=Path, help="JSON array of synthetic source items when changed")
    parser.add_argument("--output-brief", type=Path)
    parser.add_argument("--max-chars", type=int, default=12000)
    parser.add_argument("--link-limit", type=int, default=40)
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
        body, error = fetch_bytes(
            url,
            timeout=args.timeout,
            insecure_skip_tls_verify=args.insecure_skip_tls_verify,
        )
        if body is None:
            brief_rows.append(
                {
                    "name": name,
                    "url": url,
                    "checked_at": now_utc(),
                    "changed": False,
                    "error": error or "fetch failed",
                }
            )
            continue

        row, items, new_slice = evaluate_page(
            page,
            body,
            state_pages.get(key, {}),
            max_chars=args.max_chars,
            emit_baseline=args.emit_baseline,
            run_date=args.run_date,
            link_limit=args.link_limit,
        )
        state_pages[key] = new_slice
        changed_items.extend(items)
        brief_rows.append(row)

    state["updated_at"] = now_utc()
    state["version"] = 2
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
