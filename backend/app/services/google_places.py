import os
from typing import Any

import requests

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
TEXT_SEARCH_NEW_URL = "https://places.googleapis.com/v1/places:searchText"

print("GOOGLE_PLACES_API_KEY loaded:", bool(GOOGLE_PLACES_API_KEY))


def _text_search(query: str) -> list[dict[str, Any]]:
    if not GOOGLE_PLACES_API_KEY:
        return []

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": (
            "places.displayName,"
            "places.formattedAddress,"
            "places.rating,"
            "places.types,"
            "places.priceLevel,"
            "places.location"
        ),
    }

    body = {
        "textQuery": query,
        "languageCode": "en",
        "maxResultCount": 5,
    }

    resp = requests.post(
        TEXT_SEARCH_NEW_URL,
        headers=headers,
        json=body,
        timeout=20,
    )
    resp.raise_for_status()

    data = resp.json()
    print("GOOGLE RAW JSON:", data)

    return data.get("places", [])


def _normalize_price_level(value: str | None) -> int | None:
    if not value:
        return None

    mapping = {
        "PRICE_LEVEL_FREE": 0,
        "PRICE_LEVEL_INEXPENSIVE": 1,
        "PRICE_LEVEL_MODERATE": 2,
        "PRICE_LEVEL_EXPENSIVE": 3,
        "PRICE_LEVEL_VERY_EXPENSIVE": 4,
    }
    return mapping.get(value)


def search_places(query: str, limit: int = 5) -> list[dict[str, Any]]:
    results = _text_search(query)[:limit]
    places: list[dict[str, Any]] = []

    for item in results:
        location = item.get("location", {})
        display_name = item.get("displayName", {}) or {}

        places.append(
            {
                "name": display_name.get("text"),
                "address": item.get("formattedAddress"),
                "rating": item.get("rating"),
                "types": item.get("types", []),
                "price_level": _normalize_price_level(item.get("priceLevel")),
                "summary": None,
                "lat": location.get("latitude"),
                "lng": location.get("longitude"),
            }
        )

    return places