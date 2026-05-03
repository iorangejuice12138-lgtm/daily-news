"""Daily News Aggregator - News Scraper Module"""

import re
import logging
from datetime import datetime, timezone, timedelta

import httpx
import feedparser
from bs4 import BeautifulSoup

import config

logger = logging.getLogger(__name__)

BJT = timezone(timedelta(hours=8))


def _get_today_bjt() -> datetime:
    return datetime.now(BJT)


def _fetch(url: str) -> str:
    """Fetch a URL and return the response text."""
    with httpx.Client(
        timeout=config.REQUEST_TIMEOUT,
        headers=config.REQUEST_HEADERS,
        follow_redirects=True,
    ) as client:
        resp = client.get(url)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        return resp.text


# ─── CCTV News (新闻联播) ───────────────────────────────────────────────


def scrape_cctv_news() -> list[dict]:
    """Scrape today's CCTV News Broadcast (新闻联播) text summaries."""
    news_items = []
    today = _get_today_bjt()

    try:
        # The list page shows dated segments; we look for today's date in the URL path
        html = _fetch(config.CCTV_NEWS_LIST_URL)
        soup = BeautifulSoup(html, "lxml")

        # Find links to individual news segments for today
        today_path = today.strftime("/%Y/%m/%d/")
        links = []

        for a_tag in soup.select("a[href]"):
            href = a_tag.get("href", "")
            if today_path in href and href.endswith(".shtml"):
                full_url = href if href.startswith("http") else config.CCTV_BASE_URL + href
                title = a_tag.get_text(strip=True)
                # Clean up title prefix
                title = re.sub(r"^完整版\s*", "", title)
                if title:
                    links.append((full_url, title))

        if not links:
            # Fallback: try to find the latest day's content
            logger.info("No news found for today, trying to find latest available links")
            for a_tag in soup.select("a[href]"):
                href = a_tag.get("href", "")
                text = a_tag.get_text(strip=True)
                if re.search(r"/\d{4}/\d{2}/\d{2}/", href) and href.endswith(".shtml") and text:
                    text = re.sub(r"^完整版\s*", "", text)
                    if text:
                        full_url = href if href.startswith("http") else config.CCTV_BASE_URL + href
                        links.append((full_url, text))
                        if len(links) >= 20:
                            break

        # De-duplicate by URL
        seen = set()
        unique_links = []
        for url, title in links:
            if url not in seen:
                seen.add(url)
                unique_links.append((url, title))

        logger.info(f"Found {len(unique_links)} CCTV news links")

        for url, title in unique_links[:20]:  # limit to 20 items
            try:
                content = _extract_cctv_article(url)
                if content:
                    news_items.append({
                        "title": title,
                        "content": content,
                        "source": "新闻联播",
                        "url": url,
                    })
            except Exception as e:
                logger.warning(f"Failed to fetch CCTV article {url}: {e}")

    except Exception as e:
        logger.error(f"Failed to scrape CCTV news list: {e}")

    return news_items


def _extract_cctv_article(url: str) -> str:
    """Extract the main text content from a CCTV article page."""
    html = _fetch(url)
    soup = BeautifulSoup(html, "lxml")

    # Try common CCTV content containers
    for selector in ["div.content_area", "div.text", "div.cnt_bd", "div.content"]:
        container = soup.select_one(selector)
        if container:
            paragraphs = container.find_all("p")
            text = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            if len(text) > 20:
                return text

    # Fallback: grab all <p> tags
    paragraphs = soup.find_all("p")
    text = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
    return text if len(text) > 20 else ""


# ─── RSS News ────────────────────────────────────────────────────────────


def scrape_rss_news() -> list[dict]:
    """Fetch news from configured RSS feeds."""
    news_items = []
    today = _get_today_bjt()
    today_date = today.date()

    for feed_cfg in config.RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_cfg["url"])
            count = 0
            for entry in feed.entries:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", entry.get("description", "")).strip()
                summary = BeautifulSoup(summary, "lxml").get_text(strip=True)
                link = entry.get("link", "")

                if not title or not summary:
                    continue

                # Try date filtering: prefer today's items, but allow recent ones
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                if published:
                    pub_date = datetime(*published[:6]).date()
                    if pub_date != today_date:
                        continue

                news_items.append({
                    "title": title,
                    "content": summary,
                    "source": feed_cfg["name"],
                    "url": link,
                })
                count += 1

                if count >= 10:
                    break

            logger.info(f"RSS [{feed_cfg['name']}]: fetched {count} items")

        except Exception as e:
            logger.warning(f"Failed to fetch RSS feed {feed_cfg['name']}: {e}")

    # If date filtering yielded nothing, grab the latest entries without date filter
    if not news_items:
        logger.info("No RSS items for today, falling back to latest entries")
        for feed_cfg in config.RSS_FEEDS:
            try:
                feed = feedparser.parse(feed_cfg["url"])
                for entry in feed.entries[:5]:
                    title = entry.get("title", "").strip()
                    summary = entry.get("summary", entry.get("description", "")).strip()
                    summary = BeautifulSoup(summary, "lxml").get_text(strip=True)
                    link = entry.get("link", "")
                    if title and summary:
                        news_items.append({
                            "title": title,
                            "content": summary,
                            "source": feed_cfg["name"],
                            "url": link,
                        })
            except Exception as e:
                logger.warning(f"Failed to fetch fallback RSS {feed_cfg['name']}: {e}")

    return news_items


def scrape_all() -> list[dict]:
    """Run all scrapers and return combined news list."""
    cctv = scrape_cctv_news()
    rss = scrape_rss_news()
    logger.info(f"Total scraped: {len(cctv)} CCTV + {len(rss)} RSS = {len(cctv) + len(rss)}")
    return cctv + rss
