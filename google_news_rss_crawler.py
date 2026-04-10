#!/usr/bin/env python3
"""Google News RSS crawler that fetches full article content.

Example keyword: "2330 台積電"
"""

from __future__ import annotations

import argparse
import html
import json
import re
import time
from dataclasses import asdict, dataclass
from typing import Iterable
from urllib.parse import quote_plus

import feedparser
import requests
from bs4 import BeautifulSoup

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)


@dataclass
class NewsItem:
    title: str
    published: str
    source: str
    rss_link: str
    final_url: str
    summary: str
    content: str


def build_rss_url(query: str, hl: str = "zh-TW", gl: str = "TW", ceid: str = "TW:zh-Hant") -> str:
    encoded = quote_plus(query)
    return f"https://news.google.com/rss/search?q={encoded}&hl={hl}&gl={gl}&ceid={ceid}"


def resolve_google_link(url: str, session: requests.Session, timeout: int = 12) -> str:
    """Resolve Google News tracking URL to destination URL."""
    try:
        resp = session.get(url, timeout=timeout, allow_redirects=True)
        return resp.url
    except requests.RequestException:
        return url


def clean_text(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_article_text(url: str, session: requests.Session, timeout: int = 15) -> str:
    """Fetch and extract article body from a news page."""
    try:
        resp = session.get(url, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException:
        return ""

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove non-content tags
    for bad in soup(["script", "style", "noscript", "header", "footer", "nav", "aside", "form"]):
        bad.extract()

    # Prefer article container
    container = soup.find("article")

    candidates: Iterable = container.find_all("p") if container else soup.find_all("p")
    paragraphs = [clean_text(p.get_text(" ", strip=True)) for p in candidates]
    paragraphs = [p for p in paragraphs if len(p) >= 30]

    content = "\n".join(paragraphs)

    # Fallback to meta description when body is blocked
    if not content:
        meta = soup.find("meta", attrs={"name": "description"}) or soup.find(
            "meta", attrs={"property": "og:description"}
        )
        if meta and meta.get("content"):
            return clean_text(meta["content"])

    return content


def crawl_google_news(query: str, limit: int = 5, sleep_sec: float = 1.0) -> list[NewsItem]:
    rss_url = build_rss_url(query)

    session = requests.Session()
    session.headers.update({"User-Agent": DEFAULT_UA})

    feed = feedparser.parse(rss_url)

    items: list[NewsItem] = []
    for entry in feed.entries[:limit]:
        rss_link = entry.get("link", "")
        final_url = resolve_google_link(rss_link, session)
        article_content = extract_article_text(final_url, session)

        item = NewsItem(
            title=clean_text(entry.get("title", "")),
            published=clean_text(entry.get("published", "")),
            source=clean_text((entry.get("source") or {}).get("title", "")),
            rss_link=rss_link,
            final_url=final_url,
            summary=clean_text(entry.get("summary", "")),
            content=article_content,
        )
        items.append(item)

        time.sleep(max(0.0, sleep_sec))

    return items


def main() -> None:
    parser = argparse.ArgumentParser(description="Crawl Google News RSS and fetch article content")
    parser.add_argument("--query", default="2330 台積電", help='Search keyword, e.g. "2330 台積電"')
    parser.add_argument("--limit", type=int, default=5, help="Number of items to crawl")
    parser.add_argument("--sleep", type=float, default=1.0, help="Sleep seconds between requests")
    parser.add_argument("--output", default="", help="Output JSON file path")
    args = parser.parse_args()

    news = crawl_google_news(query=args.query, limit=args.limit, sleep_sec=args.sleep)

    payload = [asdict(item) for item in news]

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"已輸出 {len(payload)} 筆至 {args.output}")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
