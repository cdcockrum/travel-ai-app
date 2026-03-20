from __future__ import annotations

import os
from typing import Any

import requests

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
GOOGLE_PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"


def _headers() -> dict[str, str]:
    if not GOOGLE_PLACES_API_KEY:
        raise RuntimeError("GOOGLE_PLACES_API_KEY is missing")

    return {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": ",".join(
            [
                "places.id",
                "places.displayName",
                "places.formattedAddress",
                "places.location",
                "places.rating",
                "places.userRatingCount",
                "places.types",
                "places.websiteUri",
                "places.googleMapsUri",
                "places.primaryType",
            ]
        ),
    }


def _search_text(query: str, max_result_count: int = 10) -> list[dict[str, Any]]:
    payload = {
        "textQuery": query,
        "maxResultCount": max_result_count,
    }

    response = requests.post(
        GOOGLE_PLACES_TEXT_SEARCH_URL,
        headers=_headers(),
        json=payload,
        timeout=20,
    )
    response.raise_for_status()

    data = response.json()
    return data.get("places", [])


def simplify_places(places: list[dict[str, Any]]) -> list[dict[str, Any]]:
    simplified = []

    for place in places:
        location = place.get("location", {}) or {}
        display_name = place.get("displayName", {}) or {}

        simplified.append(
            {
                "id": place.get("id"),
                "name": display_name.get("text"),
                "address": place.get("formattedAddress"),
                "lat": location.get("latitude"),
                "lng": location.get("longitude"),
                "rating": place.get("rating"),
                "user_rating_count": place.get("userRatingCount"),
                "types": place.get("types", []),
                "primary_type": place.get("primaryType"),
                "website_url": place.get("websiteUri"),
                "google_maps_url": place.get("googleMapsUri"),
            }
        )

    return [p for p in simplified if p.get("name")]


def score_place(place: dict, dietary_prefs: list[str] | None = None) -> float:
    rating = place.get("rating", 0) or 0
    reviews = place.get("user_rating_count", 0) or 0
    types = " ".join(place.get("types", [])).lower()
    name = (place.get("name") or "").lower()
    address = (place.get("address") or "").lower()

    score = rating * 2 + min(reviews / 100, 5)

    if "restaurant" in types or "food" in types:
        score += 1

    if dietary_prefs:
        prefs = [p.lower() for p in dietary_prefs]

        if "vegan" in prefs and (
            "vegan" in types or "vegan" in name or "vegan" in address
        ):
            score += 3

        if "vegetarian" in prefs and (
            "vegetarian" in types
            or "vegetarian" in name
            or "vegetarian" in address
            or "veggie" in name
        ):
            score += 2

        if "gluten-free" in prefs and (
            "gluten-free" in types
            or "gluten free" in name
            or "gluten-free" in address
        ):
            score += 2

        if "halal" in prefs and ("halal" in types or "halal" in name):
            score += 2

        if "kosher" in prefs and ("kosher" in types or "kosher" in name):
            score += 2

        if "dairy-free" in prefs and (
            "dairy-free" in types or "dairy free" in name
        ):
            score += 1

    return score


def rank_places(
    places: list[dict[str, Any]], dietary_prefs: list[str] | None = None
) -> list[dict[str, Any]]:
    return sorted(
        places,
        key=lambda p: score_place(p, dietary_prefs),
        reverse=True,
    )


def _dedupe_places(places: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []

    for place in places:
        pid = place.get("id")
        if not pid or pid in seen:
            continue
        seen.add(pid)
        deduped.append(place)

    return deduped


def get_restaurant_recommendations(
    city: str,
    country: str,
    notes: str = "",
    dietary_prefs: list[str] | None = None,
    max_results: int = 12,
) -> list[dict[str, Any]]:
    queries = [
        f"best restaurants in {city}, {country}",
        f"top local food in {city}, {country}",
    ]

    prefs = [p.lower() for p in (dietary_prefs or [])]
    if "vegan" in prefs:
        queries.insert(0, f"best vegan restaurants in {city}, {country}")
    if "vegetarian" in prefs:
        queries.insert(0, f"best vegetarian restaurants in {city}, {country}")
    if "gluten-free" in prefs:
        queries.insert(0, f"best gluten-free restaurants in {city}, {country}")
    if "halal" in prefs:
        queries.insert(0, f"best halal restaurants in {city}, {country}")
    if "kosher" in prefs:
        queries.insert(0, f"best kosher restaurants in {city}, {country}")

    notes_lower = (notes or "").lower()
    if "food" in notes_lower:
        queries.insert(0, f"must-try food restaurants in {city}, {country}")
    if "fine dining" in notes_lower:
        queries.insert(0, f"best fine dining restaurants in {city}, {country}")
    if "hidden gems" in notes_lower or "local" in notes_lower:
        queries.insert(0, f"local hidden gem restaurants in {city}, {country}")

    all_places: list[dict[str, Any]] = []
    for query in queries[:5]:
        try:
            results = _search_text(query, max_result_count=8)
            all_places.extend(simplify_places(results))
        except Exception:
            continue

    all_places = _dedupe_places(all_places)
    ranked = rank_places(all_places, dietary_prefs=dietary_prefs)
    return ranked[:max_results]


def get_attraction_recommendations(
    city: str,
    country: str,
    notes: str = "",
    max_results: int = 12,
) -> list[dict[str, Any]]:
    queries = [
        f"top attractions in {city}, {country}",
        f"best things to do in {city}, {country}",
    ]

    notes_lower = (notes or "").lower()
    if "culture" in notes_lower or "architecture" in notes_lower:
        queries.insert(0, f"cultural attractions in {city}, {country}")
        queries.insert(0, f"architecture landmarks in {city}, {country}")
    if "museum" in notes_lower:
        queries.insert(0, f"best museums in {city}, {country}")
    if "nature" in notes_lower:
        queries.insert(0, f"best parks and gardens in {city}, {country}")

    all_places: list[dict[str, Any]] = []
    for query in queries[:5]:
        try:
            results = _search_text(query, max_result_count=8)
            all_places.extend(simplify_places(results))
        except Exception:
            continue

    all_places = _dedupe_places(all_places)
    ranked = sorted(
        all_places,
        key=lambda p: ((p.get("rating") or 0), (p.get("user_rating_count") or 0)),
        reverse=True,
    )
    return ranked[:max_results]