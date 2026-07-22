"""Scrape the latest articles from theverge.com with Playwright.

Unlike techcrunch.py, The Verge embeds the full article body directly in
each article page's schema.org NewsArticle JSON-LD (`articleBody`), so
extraction here is JSON-LD only — no DOM body-scraping needed.
"""

import html
import json
import re
from datetime import datetime, timezone

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

BASE_URL = "https://www.theverge.com"
LISTING_URL = f"{BASE_URL}/archives/full"
SOURCE = "theverge.com"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Each listing card's permalink is the one <a> with both an aria-label
# (carrying the headline) and an href; article paths look like
# /{category}/{numeric id}/{slug}.
CARD_LINK_SELECTOR = "a[aria-label][href]"
ARTICLE_PATH_RE = re.compile(r"^/(?:[a-z0-9-]+/)+\d{4,8}/[a-z0-9-]+/?$")


def _listing_page_url(page_num: int) -> str:
    return LISTING_URL if page_num == 1 else f"{BASE_URL}/archives/{page_num}"


def _collect_article_urls(page: Page, limit: int) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    page_num = 1

    while len(urls) < limit and page_num <= 6:
        page.goto(_listing_page_url(page_num), wait_until="domcontentloaded")
        page.wait_for_selector(CARD_LINK_SELECTOR, state="attached")

        paths = page.eval_on_selector_all(
            CARD_LINK_SELECTOR,
            "els => els.map(e => new URL(e.href).pathname)",
        )
        for path in paths:
            if ARTICLE_PATH_RE.match(path) and path not in seen:
                seen.add(path)
                urls.append(f"{BASE_URL}{path}")
            if len(urls) >= limit:
                break
        page_num += 1

    return urls[:limit]


def _extract_json_ld(page: Page) -> dict:
    scripts = page.locator("script[type='application/ld+json']").all_inner_texts()
    for raw in scripts:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if data.get("@type") == "NewsArticle":
            return data
    return {}


def _extract_body(article_body: str) -> str:
    paragraphs = html.unescape(article_body).split("\n")
    return "\n\n".join(p.strip() for p in paragraphs if p.strip())


def _scrape_article(page: Page, url: str) -> dict:
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_selector("script[type='application/ld+json']", state="attached")

    data = _extract_json_ld(page)

    authors = data.get("author") or []
    author = authors[0] if authors else {}

    title = data.get("headline")
    title = html.unescape(title).strip() if title else None

    return {
        "creation_date": datetime.now(timezone.utc).isoformat(),
        "publish_date": data.get("datePublished"),
        "title": title,
        "body": _extract_body(data.get("articleBody", "")),
        "topics": data.get("keywords") or [],
        "author": {"name": author.get("name"), "link": author.get("url")},
        "url": url,
        "source": SOURCE,
    }


def scrape_latest(limit: int = 20, headless: bool = True) -> list[dict]:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context(user_agent=USER_AGENT)
        page = context.new_page()

        urls = _collect_article_urls(page, limit)

        articles = []
        for url in urls:
            try:
                articles.append(_scrape_article(page, url))
            except PlaywrightTimeoutError:
                continue

        browser.close()
        return articles


if __name__ == "__main__":
    print(json.dumps(scrape_latest(), indent=2, ensure_ascii=False))
