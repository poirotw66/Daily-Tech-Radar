#!/usr/bin/env python3
"""Fetch RSS/Atom feeds into Daily Tech Radar source item JSON.

Uses only the Python standard library so it works with the embeddable Python
runtime on locked-down Windows machines.
"""

from __future__ import annotations

import argparse
import email.utils
import json
import ssl
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


RSS_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "dc": "http://purl.org/dc/elements/1.1/",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.date().isoformat()
    except (TypeError, ValueError):
        text = value.strip()
        return text[:10] if len(text) >= 10 else None


def text_of(node: ET.Element | None) -> str:
    if node is None:
        return ""
    return "".join(node.itertext()).strip()


def ssl_context(insecure_skip_tls_verify: bool) -> ssl.SSLContext:
    if insecure_skip_tls_verify:
        return ssl._create_unverified_context()
    return ssl.create_default_context()


def fetch_xml(url: str, timeout: int, insecure_skip_tls_verify: bool) -> ET.Element:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "DailyTechRadar/0.1 (+https://example.local)",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        },
    )
    context = ssl_context(insecure_skip_tls_verify)
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        content = response.read()
    return ET.fromstring(content)


def parse_feed(root: ET.Element, feed_url: str, limit: int, tags: list[str]) -> list[dict]:
    fetched_at = now_utc()
    publisher = urlparse(feed_url).netloc
    items: list[dict] = []

    if root.tag.endswith("rss") or root.find("channel") is not None:
        channel = root.find("channel")
        if channel is not None:
            publisher = text_of(channel.find("title")) or publisher
            entries = channel.findall("item")
            for entry in entries[:limit]:
                title = text_of(entry.find("title"))
                link = text_of(entry.find("link"))
                summary = text_of(entry.find("description"))
                published = parse_date(text_of(entry.find("pubDate")) or text_of(entry.find("dc:date", RSS_NS)))
                if title and link:
                    items.append(
                        {
                            "title": title,
                            "url": link,
                            "source_type": "official_blog",
                            "publisher": publisher,
                            "published_at": published,
                            "fetched_at": fetched_at,
                            "raw_summary": summary,
                            "tags": tags,
                            "language": "en",
                        }
                    )
        return items

    entries = root.findall("atom:entry", RSS_NS)
    publisher = text_of(root.find("atom:title", RSS_NS)) or publisher
    for entry in entries[:limit]:
        title = text_of(entry.find("atom:title", RSS_NS))
        link_node = entry.find("atom:link[@rel='alternate']", RSS_NS) or entry.find("atom:link", RSS_NS)
        link = link_node.attrib.get("href", "") if link_node is not None else ""
        summary = text_of(entry.find("atom:summary", RSS_NS)) or text_of(entry.find("atom:content", RSS_NS))
        published = parse_date(text_of(entry.find("atom:published", RSS_NS)) or text_of(entry.find("atom:updated", RSS_NS)))
        if title and link:
            items.append(
                {
                    "title": title,
                    "url": link,
                    "source_type": "official_blog",
                    "publisher": publisher,
                    "published_at": published,
                    "fetched_at": fetched_at,
                    "raw_summary": summary,
                    "tags": tags,
                    "language": "en",
                }
            )
    return items


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", action="append", required=True, help="RSS/Atom feed URL. Repeatable.")
    parser.add_argument("--tag", action="append", default=[], help="Tag to attach to every item. Repeatable.")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--insecure-skip-tls-verify", action="store_true", help="Disable TLS verification for corporate proxy smoke tests.")
    args = parser.parse_args()

    all_items: list[dict] = []
    errors: list[dict] = []
    for url in args.url:
        try:
            root = fetch_xml(url, timeout=args.timeout, insecure_skip_tls_verify=args.insecure_skip_tls_verify)
            all_items.extend(parse_feed(root, url, args.limit, args.tag))
        except Exception as exc:
            errors.append({"url": url, "error": str(exc)})

    if errors:
        print(json.dumps({"rss_errors": errors}, ensure_ascii=False), file=sys.stderr)
    if not all_items and errors:
        raise RuntimeError("All RSS feeds failed.")

    output = json.dumps(all_items, ensure_ascii=False, indent=2)
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
        print(f"fetch_rss.py failed: {exc}", file=sys.stderr)
        raise
