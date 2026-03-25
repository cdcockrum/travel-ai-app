# backend/app/services/advisory_service.py
from __future__ import annotations

import os
from typing import Any

import feedparser
import requests

_CDC_RSS = "https://wwwnc.cdc.gov/travel/rss/notices.xml"
_TRAVELADVISORY_API_KEY = os.getenv("TRAVELADVISORY_API_KEY")


def get_cdc_travel_notices(limit: int = 15) -> list[dict[str, Any]]:
    """CDC Travel Notices via RSS (no API key required)."""
    feed = feedparser.parse(_CDC_RSS)
    items: list[dict[str, Any]] = []
    for entry in (feed.entries or [])[:limit]:
        items.append(
            {
                "source": "CDC",
                "title": entry.get("title"),
                "summary": entry.get("summary"),
                "link": entry.get("link"),
                "published": entry.get("published"),
                "category": "health",
            }
        )
    return [i for i in items if i.get("title")]


def get_country_risk(country_code: str) -> dict[str, Any] | None:
    """
    Optional: TravelAdvisory API (3rd party). If no key configured, returns None.
    """
    if not _TRAVELADVISORY_API_KEY:
        return None

    url = "https://traveladvisory.io/v1/advisory"
    resp = requests.get(
        url,
        params={"code": country_code.upper()},
        headers={"Authorization": f"Bearer {_TRAVELADVISORY_API_KEY}"},
        timeout=15,
    )
    if not resp.ok:
        return None

    data = resp.json()
    return {
        "source": "TravelAdvisory",
        "country_code": country_code.upper(),
        "raw": data,
        "category": "security",
    }


def build_alerts(country_code: str | None) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    alerts.extend(get_cdc_travel_notices(limit=15))
    if country_code:
        risk = get_country_risk(country_code)
        if risk:
            alerts.append(risk)
    return alerts