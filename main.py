"""Daily News Aggregator - Main Entry Point"""

import logging
from datetime import datetime, timezone, timedelta

from scraper import scrape_all
from analyzer import analyze_all
from exporter import export

BJT = timezone(timedelta(hours=8))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def _normalize_url(url: str) -> str:
    """Normalize URL for dedup by stripping query params and fragments."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")


def _normalize_title(title: str) -> str:
    """Normalize title for fuzzy dedup."""
    import re
    t = title.strip().lower()
    # Strip common prefixes like [视频], 完整版, etc.
    t = re.sub(r"^\[.*?\]\s*", "", t)
    t = re.sub(r"^完整版\s*", "", t)
    # Strip trailing whitespace and special chars
    t = re.sub(r"\s+", " ", t).strip()
    return t


def deduplicate(news_list: list[dict]) -> list[dict]:
    """Remove duplicate news by URL and title similarity."""
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    unique = []
    for item in news_list:
        url_key = _normalize_url(item.get("url", ""))
        title_key = _normalize_title(item["title"])

        if url_key and url_key in seen_urls:
            continue
        if title_key in seen_titles:
            continue

        if url_key:
            seen_urls.add(url_key)
        seen_titles.add(title_key)
        unique.append(item)
    return unique


def main():
    today = datetime.now(BJT)
    date_str = today.strftime("%Y-%m-%d")
    logger.info(f"=== Daily News Aggregator - {date_str} ===")

    # Step 1: Scrape
    logger.info("Step 1/4: Scraping news sources...")
    raw_news = scrape_all()
    if not raw_news:
        logger.warning("No news items scraped. Exiting.")
        return
    logger.info(f"Scraped {len(raw_news)} raw items")

    # Step 2: Deduplicate
    logger.info("Step 2/4: Deduplicating...")
    unique_news = deduplicate(raw_news)
    logger.info(f"After dedup: {len(unique_news)} items")

    # Step 3: AI Analysis
    logger.info("Step 3/4: Running AI analysis...")
    analyzed_news = analyze_all(unique_news)
    logger.info(f"Analyzed {len(analyzed_news)} items")

    # Step 4: Export
    logger.info("Step 4/4: Exporting to CSV/Excel...")
    export(analyzed_news, date_str)

    logger.info("=== Done! ===")


if __name__ == "__main__":
    main()
