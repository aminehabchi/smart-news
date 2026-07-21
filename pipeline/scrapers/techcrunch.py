"""Scrape the latest articles from techcrunch.com/latest/ with Playwright.

The site doesn't expose a distinct "creation" timestamp for an article (only
when it was published/updated), so `creation_date` here is when *this
scraper* recorded the article, and `publish_date` is the article's own
published time (from its schema.org NewsArticle JSON-LD).
"""

import html
import json
from datetime import datetime, timezone

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

LISTING_URL = "https://techcrunch.com/latest/"
SOURCE = "techcrunch.com"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

ARTICLE_LINK_SELECTOR = "a.loop-card__title-link"
BODY_SELECTOR = ".entry-content.wp-block-post-content > p"
TOPICS_SELECTOR = ".tc23-post-relevant-terms__terms a"
AUTHOR_SELECTOR = ".wp-block-tc23-author-card-name__link"


def _dismiss_cookie_banner(page: Page) -> None:
    try:
        page.locator("#onetrust-accept-btn-handler").click(timeout=2000)
    except PlaywrightTimeoutError:
        pass


def _collect_article_urls(page: Page, limit: int) -> list[str]:
    page.goto(LISTING_URL, wait_until="domcontentloaded")
    _dismiss_cookie_banner(page)
    page.wait_for_selector(ARTICLE_LINK_SELECTOR)

    urls: list[str] = []
    seen: set[str] = set()
    stagnant_rounds = 0

    while len(urls) < limit and stagnant_rounds < 3:
        hrefs = page.locator(ARTICLE_LINK_SELECTOR).evaluate_all(
            "els => els.map(e => e.href)"
        )
        before = len(urls)
        for href in hrefs:
            if href not in seen:
                seen.add(href)
                urls.append(href)
        if len(urls) >= limit:
            break
        stagnant_rounds = stagnant_rounds + 1 if len(urls) == before else 0
        page.mouse.wheel(0, 6000)
        page.wait_for_timeout(1000)

    return urls[:limit]


def _extract_json_ld(page: Page) -> dict:
    scripts = page.locator("script[type='application/ld+json']").all_inner_texts()
    for raw in scripts:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        graph = data.get("@graph", [data])
        article = next((n for n in graph if n.get("@type") == "NewsArticle"), None)
        if not article:
            continue
        author_refs = article.get("author") or []
        author_id = author_refs[0].get("@id") if author_refs else None
        person = next((n for n in graph if n.get("@id") == author_id), None)
        return {
            "headline": article.get("headline"),
            "date_published": article.get("datePublished"),
            "author_name": person.get("name") if person else None,
            "author_url": person.get("url") if person else None,
        }
    return {}


def _extract_topics(page: Page) -> list[str]:
    texts = page.locator(TOPICS_SELECTOR).all_inner_texts()
    return [t.strip() for t in texts if t.strip()]


def _extract_body(page: Page) -> str:
    paragraphs = page.locator(BODY_SELECTOR).all_inner_texts()
    return "\n\n".join(p.strip() for p in paragraphs if p.strip())


def _scrape_article(page: Page, url: str) -> dict:
    page.goto(url, wait_until="domcontentloaded")
    _dismiss_cookie_banner(page)
    page.wait_for_selector(BODY_SELECTOR)

    json_ld = _extract_json_ld(page)

    title = json_ld.get("headline")
    title = html.unescape(title).strip() if title else page.locator("h1").first.inner_text().strip()

    author_name = json_ld.get("author_name")
    author_url = json_ld.get("author_url")
    if not author_name:
        author_link = page.locator(AUTHOR_SELECTOR).first
        author_name = author_link.inner_text().strip()
        author_url = author_link.get_attribute("href")

    return {
        "creation_date": datetime.now(timezone.utc).isoformat(),
        "publish_date": json_ld.get("date_published"),
        "title": title,
        "body": _extract_body(page),
        "topics": _extract_topics(page),
        "author": {"name": author_name, "link": author_url},
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
