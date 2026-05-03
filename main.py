"""Daily News Aggregator - Main Entry Point"""

import logging
import os
import subprocess
import sys
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


def deduplicate(news_list: list[dict]) -> list[dict]:
    """Remove duplicate news by title similarity."""
    seen_titles = set()
    unique = []
    for item in news_list:
        # Normalize title for dedup
        key = item["title"].strip().lower()
        if key not in seen_titles:
            seen_titles.add(key)
            unique.append(item)
    return unique


def git_commit_and_push(date_str: str):
    """Commit and push the updated data files to the repository."""
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(repo_dir)

    try:
        subprocess.run(["git", "add", "data/"], check=True)
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            capture_output=True,
        )
        if result.returncode == 0:
            logger.info("No changes to commit")
            return

        subprocess.run(
            ["git", "commit", "-m", f"📰 Daily news update: {date_str}"],
            check=True,
        )
        subprocess.run(["git", "push"], check=True)
        logger.info(f"Git: committed and pushed news for {date_str}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Git operation failed: {e}")


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

    # Step 5: Git commit (only in CI)
    if os.environ.get("CI"):
        logger.info("CI environment detected, committing results...")
        git_commit_and_push(date_str)
    else:
        logger.info("Local run — skipping git commit")

    logger.info("=== Done! ===")


if __name__ == "__main__":
    main()
