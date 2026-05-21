#!/usr/bin/env python3
"""Fetch arXiv papers through the official Atom API."""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


ATOM = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def text_of(node: ET.Element | None) -> str:
    if node is None:
        return ""
    return " ".join("".join(node.itertext()).split())


def ssl_context(insecure_skip_tls_verify: bool) -> ssl.SSLContext:
    if insecure_skip_tls_verify:
        return ssl._create_unverified_context()
    return ssl.create_default_context()


def fetch_arxiv(categories: list[str], max_results: int, timeout: int, insecure_skip_tls_verify: bool) -> list[dict]:
    query = " OR ".join(f"cat:{category}" for category in categories)
    params = urllib.parse.urlencode(
        {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
    )
    url = f"https://export.arxiv.org/api/query?{params}"
    request = urllib.request.Request(url, headers={"User-Agent": "DailyTechRadar/0.1"})
    with urllib.request.urlopen(request, timeout=timeout, context=ssl_context(insecure_skip_tls_verify)) as response:
        root = ET.fromstring(response.read())

    fetched_at = now_utc()
    items: list[dict] = []
    for entry in root.findall("atom:entry", ATOM):
        title = text_of(entry.find("atom:title", ATOM))
        link = ""
        for link_node in entry.findall("atom:link", ATOM):
            if link_node.attrib.get("rel") == "alternate":
                link = link_node.attrib.get("href", "")
                break
        if not link:
            link_node = entry.find("atom:id", ATOM)
            link = text_of(link_node)
        summary = text_of(entry.find("atom:summary", ATOM))
        published = text_of(entry.find("atom:published", ATOM))[:10] or None
        authors = [text_of(author.find("atom:name", ATOM)) for author in entry.findall("atom:author", ATOM)]
        primary_category = entry.find("arxiv:primary_category", ATOM)
        category = primary_category.attrib.get("term", "") if primary_category is not None else ""
        tags = ["Research", "LLM"] + ([category] if category else [])
        items.append(
            {
                "title": title,
                "url": link,
                "source_type": "paper",
                "publisher": "arXiv",
                "published_at": published,
                "fetched_at": fetched_at,
                "raw_summary": f"{summary}\nAuthors: {', '.join(authors[:5])}",
                "tags": tags,
                "language": "en",
            }
        )
    return items


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", action="append", default=["cs.AI", "cs.CL", "cs.LG"])
    parser.add_argument("--max-results", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--insecure-skip-tls-verify", action="store_true", help="Disable TLS verification for corporate proxy smoke tests.")
    args = parser.parse_args()

    items = fetch_arxiv(args.category, args.max_results, args.timeout, args.insecure_skip_tls_verify)
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
        print(f"fetch_arxiv.py failed: {exc}", file=sys.stderr)
        raise
