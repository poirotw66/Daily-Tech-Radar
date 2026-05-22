"""Tests for page_link_extract."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from page_link_extract import extract_article_links, looks_like_article


def test_anthropic_news_link_filter() -> None:
    page = "https://www.anthropic.com/news"
    assert looks_like_article(page, "https://www.anthropic.com/news/claude-opus-4-7")
    assert not looks_like_article(page, "https://www.anthropic.com/news")


def test_extract_from_minimal_html() -> None:
    html = """
    <main>
      <a href="/news/first-post">First Post</a>
      <a href="/news/second-post">Second Post</a>
      <a href="/pricing">Pricing</a>
    </main>
    """
    links = extract_article_links(html, "https://www.anthropic.com/news")
    urls = {item["url"] for item in links}
    assert "https://www.anthropic.com/news/first-post" in urls
    assert "https://www.anthropic.com/news/second-post" in urls
    assert all("/pricing" not in u for u in urls)
