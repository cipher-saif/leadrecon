"""
enrich.py — firmographic enrichment.

Design note: reliable company-size/industry data normally sits behind paid
APIs (Clearbit, ZoomInfo, Crunchbase Pro). Rather than depend on a key you
may not have, this module:
  1. Uses whatever firmographic data you already supply in the input CSV
     (company_size, industry columns) if present.
  2. Optionally enriches with a free-tier NewsAPI lookup for "trigger events"
     (funding, product launches, hiring pushes) if NEWSAPI_KEY is set.
  3. Falls back cleanly (no crash, just missing fields) with no key set.

This keeps the tool runnable out of the box, and the README explains how to
plug in a real firmographic API for a production version.
"""

from dataclasses import dataclass, field

import requests

from .config import NEWSAPI_KEY, REQUEST_TIMEOUT, USER_AGENT

TRIGGER_KEYWORDS = [
    "raises", "funding", "series a", "series b", "series c",
    "acquires", "acquisition", "launches", "hiring", "expands",
    "partnership", "ipo",
]


@dataclass
class EnrichmentResult:
    company_name: str
    employee_count: int | None = None
    industry: str | None = None
    trigger_events: list = field(default_factory=list)
    trigger_event_found: bool = False


def enrich_from_row(row: dict) -> EnrichmentResult:
    """
    Build an EnrichmentResult from a CSV row plus optional live news lookup.
    Expects row keys: company_name, employee_count (optional), industry (optional).
    """
    company_name = row.get("company_name", "").strip()
    result = EnrichmentResult(company_name=company_name)

    # Employee count from input data, if provided
    raw_count = row.get("employee_count", "").strip()
    if raw_count.isdigit():
        result.employee_count = int(raw_count)

    # Industry from input data, if provided
    industry = row.get("industry", "").strip()
    if industry:
        result.industry = industry.lower()

    # Optional live trigger-event lookup via NewsAPI free tier
    if NEWSAPI_KEY and company_name:
        result.trigger_events = _fetch_trigger_events(company_name)
        result.trigger_event_found = len(result.trigger_events) > 0

    return result


def _fetch_trigger_events(company_name: str) -> list:
    """Query NewsAPI for recent articles mentioning the company + trigger keywords."""
    try:
        resp = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": f'"{company_name}"',
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": 10,
                "apiKey": NEWSAPI_KEY,
            },
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
    except (requests.RequestException, ValueError):
        return []

    hits = []
    for article in articles:
        title = (article.get("title") or "").lower()
        desc = (article.get("description") or "").lower()
        if any(kw in title or kw in desc for kw in TRIGGER_KEYWORDS):
            hits.append({
                "title": article.get("title"),
                "url": article.get("url"),
                "publishedAt": article.get("publishedAt"),
            })
    return hits[:3]
