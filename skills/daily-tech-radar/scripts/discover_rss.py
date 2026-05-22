#!/usr/bin/env python3
"""Discover RSS/Atom feed URLs from a site or blog homepage."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from http_fetch import fetch_bytes


CANDIDATE_PATHS = (
    "/feed",
    "/rss",
    "/rss.xml",
    "/feed.xml",
    "/atom.xml",
    "/blog/feed",
    "/blog/rss",
    "/blog/rss.xml",
    "/news/rss.xml",
    "/news/feed",
)

LINK_RE = re.compile(
    r'<link[^>]+rel=["\']alternate["\'][^>]+type=["\']application/(?:rss\+xml|atom\+xml)["\'][^>]+href=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
LINK_RE2 = re.compile(
    r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']alternate["\'][^>]+type=["\']application/(?:rss\+xml|atom\+xml)["\']',
    re.IGNORECASE,
)


def normalize_base(url: str) -> str:
    parsed = urlparse(url.strip())
    if not parsed.scheme:
        parsed = urlparse("https://" + url.strip())
    return f"{parsed.scheme}://{parsed.netloc}"


def candidate_urls(page_url: str) -> list[str]:
    base = normalize_base(page_url)
    path = urlparse(page_url).path.rstrip("/") or ""
    urls: list[str] = []
    for suffix in CANDIDATE_PATHS:
        urls.append(urljoin(base + "/", suffix.lstrip("/")))
    if path:
        for suffix in ("/feed", "/rss", "/rss.xml", "/feed.xml"):
            urls.append(urljoin(base, path + suffix))
    seen: set[str] = set()
    ordered: list[str] = []
    for item in urls:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def extract_link_feeds(html: str, page_url: str) -> list[str]:
    found: list[str] = []
    for pattern in (LINK_RE, LINK_RE2):
        for match in pattern.finditer(html):
            href = match.group(1).strip()
            found.append(urljoin(page_url, href))
    return found


def looks_like_feed(body: bytes) -> bool:
    text = body[:8000].lstrip().lower()
    return text.startswith(b"<?xml") and (
        b"<rss" in text or b"<feed" in text or b"<rdf:" in text
    )


def discover(page_url: str, *, timeout: int, insecure: bool) -> dict:
    results: list[dict] = []
    body, error = fetch_bytes(page_url, timeout=timeout, insecure_skip_tls_verify=insecure)
    html = ""
    if body:
        html = body.decode("utf-8", errors="replace")
        for feed_url in extract_link_feeds(html, page_url):
            fb, err = fetch_bytes(feed_url, timeout=timeout, insecure_skip_tls_verify=insecure)
            ok = fb is not None and looks_like_feed(fb)
            results.append(
                {
                    "url": feed_url,
                    "source": "html_link",
                    "status": "ok" if ok else "failed",
                    "error": err or "",
                }
            )

    for feed_url in candidate_urls(page_url):
        if any(r["url"] == feed_url for r in results):
            continue
        fb, err = fetch_bytes(feed_url, timeout=timeout, insecure_skip_tls_verify=insecure)
        ok = fb is not None and looks_like_feed(fb)
        if ok or err:
            results.append(
                {
                    "url": feed_url,
                    "source": "path_guess",
                    "status": "ok" if ok else "failed",
                    "error": err or "",
                }
            )

    ok_feeds = [r for r in results if r["status"] == "ok"]
    return {
        "page_url": page_url,
        "page_fetch_error": error or "",
        "feeds": results,
        "recommended_feed": ok_feeds[0]["url"] if ok_feeds else "",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="Blog or site homepage URL")
    parser.add_argument("--timeout", type=int, default=25)
    parser.add_argument("--insecure-skip-tls-verify", action="store_true")
    args = parser.parse_args()
    report = discover(args.url, timeout=args.timeout, insecure=args.insecure_skip_tls_verify)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("recommended_feed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
