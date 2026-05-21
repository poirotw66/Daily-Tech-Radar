#!/usr/bin/env python3
"""Fetch GitHub repositories through the official REST Search API."""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path


def ssl_context(insecure_skip_tls_verify: bool) -> ssl.SSLContext:
    if insecure_skip_tls_verify:
        return ssl._create_unverified_context()
    return ssl.create_default_context()


def fetch_github(query: str, sort: str, order: str, per_page: int, timeout: int, insecure_skip_tls_verify: bool) -> list[dict]:
    params = urllib.parse.urlencode({"q": query, "sort": sort, "order": order, "per_page": per_page})
    url = f"https://api.github.com/search/repositories?{params}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "DailyTechRadar/0.1",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=ssl_context(insecure_skip_tls_verify)) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API returned HTTP {exc.code}: {body}") from exc

    items: list[dict] = []
    for repo in payload.get("items", []):
        name = repo.get("full_name", "")
        description = repo.get("description") or ""
        topics = repo.get("topics") or []
        stars = repo.get("stargazers_count", 0)
        updated = (repo.get("updated_at") or "")[:10] or None
        language = repo.get("language")
        summary = f"{description}\nStars: {stars}. Language: {language}. Topics: {', '.join(topics[:8])}."
        items.append(
            {
                "title": name,
                "url": repo.get("html_url", ""),
                "source_type": "github",
                "publisher": "GitHub",
                "published_at": updated,
                "fetched_at": repo.get("updated_at"),
                "raw_summary": summary.strip(),
                "tags": ["DevTools", "Open Source"] + [topic for topic in topics[:5]],
                "language": "en",
            }
        )
    return items


def default_query(days: int, min_stars: int) -> str:
    since = (date.today() - timedelta(days=days)).isoformat()
    return f"llm pushed:>={since} stars:>={min_stars}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", help="GitHub repository search query.")
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--min-stars", type=int, default=50)
    parser.add_argument("--sort", default="stars", choices=["stars", "forks", "help-wanted-issues", "updated"])
    parser.add_argument("--order", default="desc", choices=["asc", "desc"])
    parser.add_argument("--per-page", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--insecure-skip-tls-verify", action="store_true", help="Disable TLS verification for corporate proxy smoke tests.")
    args = parser.parse_args()

    query = args.query or default_query(args.days, args.min_stars)
    items = fetch_github(query, args.sort, args.order, args.per_page, args.timeout, args.insecure_skip_tls_verify)
    output = json.dumps(items, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"fetch_github_repos.py failed: {exc}", file=sys.stderr)
        raise
