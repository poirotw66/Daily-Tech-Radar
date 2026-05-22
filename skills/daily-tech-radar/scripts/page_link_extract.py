"""Extract likely article links from listing pages (blog index, newsroom)."""

from __future__ import annotations

import html
import re
from urllib.parse import urljoin, urlparse

from html_extract import extract_main_html

HREF_RE = re.compile(
    r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
TAG_INNER = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")

SKIP_PATH_PARTS = (
    "/login",
    "/sign",
    "/pricing",
    "/legal",
    "/privacy",
    "/terms",
    "/contact",
    "/careers",
    "/download",
    "/app",
    "/api",
    "#",
    "javascript:",
    "mailto:",
)

ARTICLE_PATH_HINTS = (
    "/blog/",
    "/news/",
    "/articles/",
    "/posts/",
    "/engineering/",
    "/research/",
    "/product/",
    "/announcements/",
)

HOST_RULES: dict[str, dict] = {
    "claude.com": {
        "require_hints": ("/blog/",),
        "exclude_suffixes": ("/blog", "/blog/"),
    },
    "www.anthropic.com": {
        "require_hints": ("/news/",),
        "exclude_suffixes": ("/news", "/news/"),
    },
    "anthropic.com": {
        "require_hints": ("/news/",),
        "exclude_suffixes": ("/news", "/news/"),
    },
}


def clean_title(raw: str) -> str:
    text = TAG_INNER.sub(" ", raw or "")
    text = html.unescape(text)
    text = WS.sub(" ", text).strip()
    return text[:200] if text else ""


def normalize_link(page_url: str, href: str) -> str | None:
    href = (href or "").strip()
    if not href or href.startswith(SKIP_PATH_PARTS):
        return None
    absolute = urljoin(page_url, href)
    parsed = urlparse(absolute)
    if parsed.scheme not in ("http", "https"):
        return None
    path = parsed.path.rstrip("/") or "/"
    return f"{parsed.scheme}://{parsed.netloc.lower()}{path}"


def host_rules(page_url: str) -> dict | None:
    netloc = urlparse(page_url).netloc.lower()
    if netloc in HOST_RULES:
        return HOST_RULES[netloc]
    for key, rules in HOST_RULES.items():
        if netloc.endswith(key):
            return rules
    return None


def looks_like_article(page_url: str, link_url: str) -> bool:
    page_host = urlparse(page_url).netloc.lower()
    link_parsed = urlparse(link_url)
    if link_parsed.netloc.lower() != page_host:
        return False
    path = link_parsed.path.lower()
    if any(part in path for part in SKIP_PATH_PARTS if part.startswith("/")):
        return False

    rules = host_rules(page_url)
    if rules:
        if not any(hint in path for hint in rules["require_hints"]):
            return False
        for suffix in rules["exclude_suffixes"]:
            if path.rstrip("/") == suffix.rstrip("/"):
                return False
        # require slug segment after hint, e.g. /news/foo not only /news
        for hint in rules["require_hints"]:
            if hint in path:
                rest = path.split(hint, 1)[1].strip("/")
                if len(rest) >= 3:
                    return True
        return False

    if not any(hint in path for hint in ARTICLE_PATH_HINTS):
        return False
    return len(path.strip("/").split("/")) >= 2


def extract_article_links(raw_html: str, page_url: str, limit: int = 40) -> list[dict[str, str]]:
    fragment = extract_main_html(raw_html)
    found: dict[str, dict[str, str]] = {}

    for match in HREF_RE.finditer(fragment):
        href, inner = match.group(1), match.group(2)
        url = normalize_link(page_url, href)
        if not url or not looks_like_article(page_url, url):
            continue
        title = clean_title(inner)
        if url not in found or (title and not found[url].get("title")):
            found[url] = {"url": url, "title": title or url}

    links = list(found.values())
    links.sort(key=lambda item: item["url"])
    return links[:limit]
