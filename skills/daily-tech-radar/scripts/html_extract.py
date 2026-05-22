"""Extract main article text from HTML (stdlib only)."""

from __future__ import annotations

import html
import re

STRIP_TAGS = re.compile(r"<(script|style|noscript|svg|iframe|nav|footer|header)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")

MAIN_HTML_PATTERNS = [
    re.compile(r"<article[^>]*>(.*)</article>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<main[^>]*>(.*)</main>", re.IGNORECASE | re.DOTALL),
    re.compile(
        r'<div[^>]*class="[^"]*(?:post-content|blog-post|entry-content|article-body|prose)[^"]*"[^>]*>(.*)</div>',
        re.IGNORECASE | re.DOTALL,
    ),
]

TRIM_MARKERS = (
    "Related posts",
    "Related Posts",
    "Getting Started",
    "© 20",
    "Follow on X",
    "server-island-start",
    "Subscribe to receive notifications",
)


def extract_main_html(raw_html: str) -> str:
    for pattern in MAIN_HTML_PATTERNS:
        match = pattern.search(raw_html)
        if match and len(match.group(1)) >= 400:
            return match.group(1)
    return raw_html


def _tags_to_text(fragment: str) -> str:
    text = STRIP_TAGS.sub(" ", fragment)
    text = TAG_RE.sub(" ", text)
    text = html.unescape(text)
    return WS_RE.sub(" ", text).strip()


def trim_boilerplate(text: str) -> str:
    earliest = len(text)
    for marker in TRIM_MARKERS:
        index = text.find(marker)
        if index > 300:
            earliest = min(earliest, index)
    if earliest < len(text):
        return text[:earliest].strip()
    return text


def html_to_text(raw_html: str, max_chars: int) -> str:
    fragment = extract_main_html(raw_html)
    text = trim_boilerplate(_tags_to_text(fragment))
    if len(text) > max_chars:
        return text[:max_chars] + "\n\n[truncated]"
    return text
