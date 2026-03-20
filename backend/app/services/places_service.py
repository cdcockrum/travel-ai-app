import os
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"


def _post_text_search(
    text_query: str,
    included_type: str | None = None,
    page_size: int = 10,
) -> list[dict[str, Any]]:
    if not GOOGLE_PLACES_API_KEY:
        raise ValueError("GOOGLE_PLACES_API_KEY is not set in backend/.env")

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": ",".join(
            [
                "places.id",
                "places.displayName",
                "places.formattedAddress",
                "places.rating",
                "places.userRatingCount",
                "places.primaryType",
                "places.googleMapsUri",
                "places.websiteUri",
                "places.location",
                "places.types",
            ]
        ),
    }

    payload: dict[str, Any] = {
        "textQuery": text_query,
        "pageSize": page_size,
    }

    if included_type:
        payload["includedType"] = included_type

    response = requests.post(
        PLACES_TEXT_SEARCH_URL,
        headers=headers,
        json=payload,
        timeout=20,
    )

    if not response.ok:
        raise ValueError(
            f"Google Places error {response.status_code}: {response.text}"
        )

    data = response.json()
    return data.get("places", [])


def _is_good_place_name(name: str | None) -> bool:
    if not name:
        return False

    cleaned = name.strip()

    if len(cleaned) < 3:
        return False

    bad_exact = {
        "culture",
        "food",
        "restaurant",
        "attraction",
        "museum",
        "shopping",
        "nightlife",
        "photography",
        "local culture",
        "architecture",
    }

    if cleaned.lower() in bad_exact:
        return False

    if cleaned.isupper() and len(cleaned) < 20:
        return False

    return True


def simplify_places(places: list[dict]) -> list[dict]:
    simplified = []

    for p in places:
        name = p.get("displayName", {}).get("text")
        if not _is_good_place_name(name):
            continue

        location = p.get("location", {})

        simplified.append(
            {
                "id": p.get("id"),
                "name": name,
                "address": p.get("formattedAddress"),
                "rating": p.get("rating"),
                "user_rating_count": p.get("userRatingCount"),
                "lat": location.get("latitude"),
                "lng": location.get("longitude"),
                "primary_type": p.get("primaryType"),
                "types": p.get("types", []),
                "google_maps_url": p.get("googleMapsUri"),
                "website_url": p.get("websiteUri"),
            }
        )

    return simplified


def get_restaurant_recommendations(city: str, country: str, notes: str = "") -> list[dict[str, Any]]:
    notes = (notes or "").lower()

    if "vegan" in notes or "vegetarian" in notes:
        query = f"best vegan and vegetarian restaurants in {city}, {country}"
    elif "halal" in notes:
        query = f"best halal restaurants in {city}, {country}"
    elif "gluten-free" in notes:
        query = f"best gluten-free friendly restaurants in {city}, {country}"
    elif "food" in notes:
        query = f"best local restaurants, cafes, and food spots in {city}, {country}"
    else:
        query = f"best restaurants and cafes in {city}, {country}"

    return _post_text_search(query, included_type="restaurant", page_size=10)


def get_attraction_recommendations(city: str, country: str, notes: str = "") -> list[dict[str, Any]]:
    if "architecture" in notes or "culture" in notes:
        query = f"best cultural landmarks, architecture sites, museums, and temples in {city}, {country}"
    else:
        query = f"top tourist attractions and landmarks in {city}, {country}"

    return _post_text_search(query, included_type=None, page_size=10)

def score_place(place: dict, dietary_prefs: list[str] | None = None) -> float:
    rating = place.get("rating", 0) or 0
    reviews = place.get("user_rating_count", 0) or 0
    types = " ".join(place.get("types", [])).lower()

    score = rating * 2 + min(reviews / 100, 5)

    if dietary_prefs:
        if "vegan" in dietary_prefs and "vegan" in types:
            score += 3
        if "vegetarian" in dietary_prefs and "vegetarian" in types:
            score += 2
        if "gluten" in dietary_prefs and "gluten" in types:
            score += 1

    if "restaurant" in types:
        score += 1

    return score


def rank_places(places: list[dict], dietary_prefs=None):
    return sorted(
        places,
        key=lambda p: score_place(p, dietary_prefs),
        reverse=True,
    )