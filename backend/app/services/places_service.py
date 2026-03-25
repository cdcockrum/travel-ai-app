from __future__ import annotations

import os
import time
from typing import Any

import requests

GOOGLE_PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
GOOGLE_PLACES_NEARBY_SEARCH_URL = "https://places.googleapis.com/v1/places:searchNearby"

_DEFAULT_FIELD_MASK = ",".join(
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
)

# ---------
# Tiny TTL cache (in-memory)
# ---------
_CACHE: dict[str, tuple[float, Any]] = {}
_CACHE_TTL_SECONDS = 60 * 30  # 30 minutes


def _cache_get(key: str) -> Any | None:
    item = _CACHE.get(key)
    if not item:
        return None
    expires_at, value = item
    if time.time() > expires_at:
        _CACHE.pop(key, None)
        return None
    return value


def _cache_set(key: str, value: Any) -> None:
    _CACHE[key] = (time.time() + _CACHE_TTL_SECONDS, value)


def _headers() -> dict[str, str]:
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_PLACES_API_KEY is missing")

    return {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": _DEFAULT_FIELD_MASK,
    }


def _raise_google_error(resp: requests.Response) -> None:
    try:
        body = resp.json()
    except Exception:
        body = resp.text
    raise RuntimeError(f"Google Places API error {resp.status_code}: {body}")


def _text_search(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    cache_key = f"text:{query}:{max_results}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    payload = {
        "textQuery": query,
        "maxResultCount": max_results,
    }

    resp = requests.post(
        GOOGLE_PLACES_TEXT_SEARCH_URL,
        headers=_headers(),
        json=payload,
        timeout=20,
    )

    if not resp.ok:
        print("GOOGLE TEXT SEARCH ERROR:", resp.text)
        _raise_google_error(resp)

    places = (resp.json() or {}).get("places", []) or []
    _cache_set(cache_key, places)
    return places


def _get_destination_center(destination: str) -> tuple[float, float]:
    """
    Uses Places Text Search once to geocode the destination into a center point (lat/lng).
    """
    cache_key = f"center:{destination}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    results = _text_search(destination, max_results=1)
    if not results:
        raise RuntimeError(f"Could not find location for destination: {destination}")

    loc = (results[0].get("location") or {})
    lat = loc.get("latitude")
    lng = loc.get("longitude")

    if lat is None or lng is None:
        raise RuntimeError(f"Destination missing lat/lng: {destination}")

    center = (float(lat), float(lng))
    _cache_set(cache_key, center)
    return center


def _nearby_search(
    *,
    destination: str,
    included_types: list[str],
    radius_meters: int = 6000,
    max_results: int = 12,
) -> list[dict[str, Any]]:
    """
    Places Nearby Search around destination center.

    Important:
    Nearby Search (New) does NOT support 'keyword' or free-text input.
    Use Text Search (New) for text-based restaurant queries.
    """
    lat, lng = _get_destination_center(destination)

    cache_key = (
        f"nearby:{destination}:{','.join(included_types)}:"
        f"{radius_meters}:{max_results}"
    )
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    payload: dict[str, Any] = {
        "includedTypes": included_types,
        "maxResultCount": max_results,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": lat,
                    "longitude": lng,
                },
                "radius": float(radius_meters),
            }
        },
    }

    resp = requests.post(
        GOOGLE_PLACES_NEARBY_SEARCH_URL,
        headers=_headers(),
        json=payload,
        timeout=20,
    )

    if not resp.ok:
        print("GOOGLE NEARBY SEARCH ERROR:", resp.text)
        _raise_google_error(resp)

    places = (resp.json() or {}).get("places", []) or []
    _cache_set(cache_key, places)
    return places


def simplify_places(places: list[dict[str, Any]]) -> list[dict[str, Any]]:
    simplified: list[dict[str, Any]] = []

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


def _dedupe_places(places: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []

    for p in places:
        pid = p.get("id")
        if not pid or pid in seen:
            continue
        seen.add(pid)
        out.append(p)

    return out


def score_place(place: dict[str, Any], dietary_prefs: list[str] | None = None) -> float:
    rating = float(place.get("rating") or 0)
    reviews = float(place.get("user_rating_count") or 0)
    types = " ".join(place.get("types", [])).lower()
    name = (place.get("name") or "").lower()

    score = rating * 2 + min(reviews / 100.0, 5.0)

    if "restaurant" in types or "food" in types:
        score += 1.0

    if dietary_prefs:
        prefs = [p.lower() for p in dietary_prefs]

        if "vegan" in prefs and ("vegan" in types or "vegan" in name):
            score += 3.0
        if "vegetarian" in prefs and (
            "vegetarian" in types or "vegetarian" in name or "veggie" in name
        ):
            score += 2.0
        if "gluten-free" in prefs and ("gluten" in name or "gluten" in types):
            score += 2.0
        if "halal" in prefs and ("halal" in name or "halal" in types):
            score += 2.0
        if "kosher" in prefs and ("kosher" in name or "kosher" in types):
            score += 2.0

    return score


def rank_places(
    places: list[dict[str, Any]],
    dietary_prefs: list[str] | None = None,
) -> list[dict[str, Any]]:
    return sorted(places, key=lambda p: score_place(p, dietary_prefs), reverse=True)


def get_restaurant_recommendations(
    city: str,
    country: str,
    notes: str = "",
    dietary_prefs: list[str] | None = None,
    max_results: int = 12,
) -> list[dict[str, Any]]:
    destination = f"{city}, {country}".strip(", ").strip()
    notes_lower = (notes or "").lower()

    # For text-heavy intent like "fine dining", use Text Search (New),
    # because Nearby Search (New) does not support keyword.
    if "fine dining" in notes_lower:
        query = f"best fine dining restaurants in {destination}"
        places = _text_search(query, max_results=max_results * 2)
    else:
        places = _nearby_search(
            destination=destination,
            included_types=["restaurant", "cafe", "bar"],
            radius_meters=5000,
            max_results=max_results * 2,
        )

    simplified = simplify_places(places)
    deduped = _dedupe_places(simplified)
    ranked = rank_places(deduped, dietary_prefs=dietary_prefs)
    return ranked[:max_results]


def get_attraction_recommendations(
    city: str,
    country: str,
    notes: str = "",
    max_results: int = 12,
) -> list[dict[str, Any]]:
    destination = f"{city}, {country}".strip(", ").strip()
    notes_lower = (notes or "").lower()

    included = ["tourist_attraction", "museum", "park", "art_gallery", "zoo"]
    if "architecture" in notes_lower:
        included.append("historical_landmark")
    if "nature" in notes_lower:
        included.append("campground")

    places = _nearby_search(
        destination=destination,
        included_types=included,
        radius_meters=8000,
        max_results=max_results * 2,
    )

    simplified = simplify_places(places)
    deduped = _dedupe_places(simplified)
    ranked = sorted(
        deduped,
        key=lambda p: ((p.get("rating") or 0), (p.get("user_rating_count") or 0)),
        reverse=True,
    )
    return ranked[:max_results]