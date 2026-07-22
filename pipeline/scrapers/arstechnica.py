"""Scrape the latest articles from arstechnica.com with Playwright.

Ars is classic WordPress: the article page's schema.org NewsArticle JSON-LD
gives title/date/author, but not body or topics. Body comes from the
`.post-content` paragraphs (long articles are split into several
`.post-content` blocks, all rendered on the same page load). Topics aren't
shown as tag chips on the page, but the `<article class="... category-x
tag-y ...">` element carries them as WordPress category/tag CSS classes.
"""

import html
import json
from datetime import datetime, timezone

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

BASE_URL = "https://arstechnica.com"
LISTING_URL = f"{BASE_URL}/"
SOURCE = "arstechnica.com"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

ARTICLE_LINK_SELECTOR = "article[id^='card-'] h2 a[href]"
BODY_SELECTOR = ".post-content p"
HENTRY_SELECTOR = "article.hentry"


def _collect_article_urls(page: Page, limit: int) -> list[str]:
    page.goto(LISTING_URL, wait_until="domcontentloaded")
    page.wait_for_selector(ARTICLE_LINK_SELECTOR, state="attached")

    hrefs = page.eval_on_selector_all(
        ARTICLE_LINK_SELECTOR, "els => els.map(e => e.href)"
    )

    urls: list[str] = []
    seen: set[str] = set()
    for href in hrefs:
        if href not in seen:
            seen.add(href)
            urls.append(href)
        if len(urls) >= limit:
            break

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


def _extract_topics(page: Page) -> list[str]:
    class_attr = page.locator(HENTRY_SELECTOR).first.get_attribute("class") or ""
    topics: list[str] = []
    seen: set[str] = set()
    for token in class_attr.split():
        for prefix in ("category-", "tag-"):
            if token.startswith(prefix):
                label = token[len(prefix) :].replace("-", " ").title()
                key = label.lower()
                if key not in seen:
                    seen.add(key)
                    topics.append(label)
    return topics


def _extract_body(page: Page) -> str:
    paragraphs = page.locator(BODY_SELECTOR).all_inner_texts()
    return "\n\n".join(p.strip() for p in paragraphs if p.strip())


def _scrape_article(page: Page, url: str) -> dict:
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_selector(BODY_SELECTOR)

    data = _extract_json_ld(page)

    title = data.get("headline")
    title = html.unescape(title).strip() if title else None

    author = data.get("author") or {}

    return {
        "creation_date": datetime.now(timezone.utc).isoformat(),
        "publish_date": data.get("datePublished"),
        "title": title,
        "body": _extract_body(page),
        "topics": _extract_topics(page),
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
