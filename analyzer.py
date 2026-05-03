"""Daily News Aggregator - AI Analysis Module (DeepSeek)"""

import json
import logging
import time

from openai import OpenAI

import config

logger = logging.getLogger(__name__)


def _build_prompt(batch: list[dict]) -> str:
    """Build the analysis prompt for a batch of news items."""
    items_text = ""
    for i, item in enumerate(batch):
        items_text += f"\n---\n[{i}] 标题: {item['title']}\n来源: {item['source']}\n内容: {item['content'][:500]}\n"

    tags_str = "、".join(config.TAGS)

    return f"""你是一位专业的新闻编辑。请分析以下新闻条目，为每条新闻生成：
1. summary：不超过50个字的中文精华摘要
2. tags：从以下标签中选择1-3个最相关的标签：{tags_str}

请严格按以下JSON格式返回（不要添加其他文字）：
[
  {{"index": 0, "summary": "...", "tags": ["标签1", "标签2"]}},
  {{"index": 1, "summary": "...", "tags": ["标签1"]}}
]

新闻条目：
{items_text}"""


def _call_deepseek(prompt: str) -> str:
    """Call the DeepSeek API with retries."""
    client = OpenAI(
        api_key=config.DEEPSEEK_API_KEY,
        base_url=config.DEEPSEEK_BASE_URL,
    )

    for attempt in range(config.MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=config.DEEPSEEK_MODEL,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"API call attempt {attempt + 1} failed: {e}")
            if attempt < config.MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
            else:
                raise


def _parse_response(response_text: str, batch_size: int) -> list[dict]:
    """Parse the JSON response from DeepSeek."""
    text = response_text.strip()
    # Extract JSON array from response (handle markdown code blocks)
    if "```" in text:
        start = text.find("[")
        end = text.rfind("]") + 1
        if start != -1 and end > start:
            text = text[start:end]
    else:
        start = text.find("[")
        end = text.rfind("]") + 1
        if start != -1 and end > start:
            text = text[start:end]

    try:
        results = json.loads(text)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse API response as JSON: {response_text[:200]}")
        return [{"summary": "", "tags": []} for _ in range(batch_size)]

    parsed = {}
    for item in results:
        idx = item.get("index", -1)
        parsed[idx] = {
            "summary": item.get("summary", ""),
            "tags": item.get("tags", []),
        }

    return [parsed.get(i, {"summary": "", "tags": []}) for i in range(batch_size)]


def analyze_batch(batch: list[dict]) -> list[dict]:
    """Analyze a batch of news items with DeepSeek."""
    prompt = _build_prompt(batch)
    response_text = _call_deepseek(prompt)
    analyses = _parse_response(response_text, len(batch))

    enriched = []
    for item, analysis in zip(batch, analyses):
        enriched.append({
            **item,
            "summary": analysis["summary"] or item["title"][:50],
            "tags": analysis["tags"] or ["未分类"],
        })
    return enriched


def analyze_all(news_list: list[dict]) -> list[dict]:
    """Analyze all news items in batches."""
    if not news_list:
        return []

    if not config.DEEPSEEK_API_KEY:
        logger.error("DEEPSEEK_API_KEY not set, skipping AI analysis")
        return [
            {**item, "summary": item["title"][:50], "tags": ["未分类"]}
            for item in news_list
        ]

    enriched = []
    for i in range(0, len(news_list), config.BATCH_SIZE):
        batch = news_list[i : i + config.BATCH_SIZE]
        logger.info(f"Analyzing batch {i // config.BATCH_SIZE + 1} ({len(batch)} items)")
        try:
            enriched.extend(analyze_batch(batch))
        except Exception as e:
            logger.error(f"Batch analysis failed: {e}, using fallback")
            enriched.extend([
                {**item, "summary": item["title"][:50], "tags": ["未分类"]}
                for item in batch
            ])

    return enriched
