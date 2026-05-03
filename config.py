"""Daily News Aggregator - Configuration"""

import os

# --- Anthropic API ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# --- CCTV News (新闻联播) ---
CCTV_NEWS_LIST_URL = "https://tv.cctv.com/lm/xwlb/"
CCTV_BASE_URL = "https://tv.cctv.com"

# --- RSS Sources ---
RSS_FEEDS = [
    {
        "name": "BBC News",
        "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "lang": "en",
    },
    {
        "name": "Reuters Top News",
        "url": "https://feeds.reuters.com/reuters/topNews",
        "lang": "en",
    },
    {
        "name": "NPR World",
        "url": "https://feeds.npr.org/1004/rss.xml",
        "lang": "en",
    },
]

# --- Tags ---
TAGS = ["政治", "经济", "科技", "军事", "民生", "国际", "社会", "文体"]

# --- Output ---
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CSV_PATH = os.path.join(DATA_DIR, "daily_news.csv")
XLSX_PATH = os.path.join(DATA_DIR, "daily_news.xlsx")

# --- Scraper ---
REQUEST_TIMEOUT = 30
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
}

# --- Analyzer ---
BATCH_SIZE = 8  # number of news items per API call
MAX_RETRIES = 3
