# backend/app/routers/itinerary.py
from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Reuse your existing working logic (queries, google places safe wrappers, fallbacks, weather)
# These functions already exist in app/routers/trips.py in your repo.
from app.routers.trips import (  # type: ignore
    build_place_queries,
    build_highlights_fallback,
    build_hotels_fallback,
    build_neighborhoods_fallback,
    build_restaurants_fallback,
    safe_get_weather,
    safe_search_places,
)

router = APIRouter()


class ItineraryGenerateRequest(BaseModel):
    destination: str
    start_date: str
    end_date: str
    notes: str | None = None
    budget_level: str | None = "moderate"
    preferences: dict[str, Any] | None = None
    traveler_profile: dict[str, Any] | None = None


def _trip_days(start_date: str, end_date: str) -> int:
    s = date.fromisoformat(start_date)
    e = date.fromisoformat(end_date)
    return max(1, (e - s).days + 1)


def _chunk(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def _place_line(place: dict[str, Any] | None) -> str:
    if not place:
        return "a local spot"
    name = place.get("name") or "a local spot"
    addr = place.get("address") or place.get("formatted_address")
    return f"{name} — {addr}" if addr else name


def _infer_neighborhood_from_address(place: dict[str, Any] | None) -> str:
    if not place:
        return "Central"
    addr = str(place.get("address") or place.get("formatted_address") or "").strip()
    if not addr:
        return "Central"

    first = addr.split(",")[0].strip()
    # If it looks like a street address (has digits), try token #2
    if any(ch.isdigit() for ch in first):
        parts = [p.strip() for p in addr.split(",") if p.strip()]
        if len(parts) >= 2 and not any(ch.isdigit() for ch in parts[1]):
            return parts[1]
        return "Central"
    return first or "Central"


def _blurb(place: dict[str, Any] | None, kind: str) -> str:
    if not place:
        return "A solid pick based on reviews and location."
    name = place.get("name") or "This spot"
    rating = place.get("rating")
    cnt = place.get("user_ratings_total") or place.get("user_rating_count")

    rating_part = ""
    if rating is not None:
        rating_part = f"Rated {rating}"
        if cnt:
            rating_part += f" ({cnt} reviews)"
        rating_part += ". "

    if kind in {"breakfast", "lunch"}:
        return f"{rating_part}{name} is convenient and well-reviewed—perfect for refueling between stops."
    if kind == "dinner":
        return f"{rating_part}{name} is a standout dinner option—great reviews and a strong local feel."
    if kind == "site":
        return f"{rating_part}{name} is a signature stop worth prioritizing for the experience."
    return f"{rating_part}{name} is a highly rated option."


def _push_place(
    out: list[dict[str, Any]],
    *,
    day: int,
    category: str,
    place: dict[str, Any] | None,
) -> None:
    if not place:
        return

    lat = (
        place.get("lat")
        or place.get("latitude")
        or (place.get("geometry") or {}).get("location", {}).get("lat")
    )
    lng = (
        place.get("lng")
        or place.get("longitude")
        or (place.get("geometry") or {}).get("location", {}).get("lng")
    )

    if lat is None or lng is None:
        return

    out.append(
        {
            "day": day,
            "category": category,
            "name": place.get("name"),
            "address": place.get("address") or place.get("formatted_address"),
            "lat": lat,
            "lng": lng,
            "google_maps_url": place.get("google_maps_url") or place.get("url"),
            "rating": place.get("rating"),
            "user_rating_count": place.get("user_ratings_total") or place.get("user_rating_count"),
        }
    )


def build_rich_days_and_places(
    *,
    destination: str,
    start_date: str,
    end_date: str,
    restaurants: list[dict[str, Any]],
    highlights: list[dict[str, Any]],
    neighborhoods: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Day plan:
      - 3 attractions per day (morning/midday/afternoon)
      - breakfast/lunch/dinner
      - spotlight: neighborhood + featured restaurant/site with blurbs
    Also returns:
      - places: flat list with day+category for your map.
    """
    days = _trip_days(start_date, end_date)

    attraction_groups = _chunk(highlights, 3) or [[]]
    meal_groups = _chunk(restaurants, 3) or [[]]  # breakfast/lunch/dinner candidates

    itinerary: list[dict[str, Any]] = []
    places: list[dict[str, Any]] = []

    for i in range(days):
        day_num = i + 1
        ats = attraction_groups[i % len(attraction_groups)]
        ms = meal_groups[i % len(meal_groups)]

        breakfast = ms[0] if len(ms) > 0 else None
        lunch = ms[1] if len(ms) > 1 else None
        dinner = ms[2] if len(ms) > 2 else None

        a1 = ats[0] if len(ats) > 0 else None
        a2 = ats[1] if len(ats) > 1 else None
        a3 = ats[2] if len(ats) > 2 else None

        _push_place(places, day=day_num, category="breakfast", place=breakfast)
        _push_place(places, day=day_num, category="attraction", place=a1)
        _push_place(places, day=day_num, category="attraction", place=a2)
        _push_place(places, day=day_num, category="attraction", place=a3)
        _push_place(places, day=day_num, category="lunch", place=lunch)
        _push_place(places, day=day_num, category="dinner", place=dinner)

        hood = neighborhoods[i % len(neighborhoods)] if neighborhoods else _infer_neighborhood_from_address(a1 or dinner or lunch)

        itinerary.append(
            {
                "day": day_num,
                "title": f"Day {day_num} in {destination}",
                "meals": {
                    "breakfast": {"place": _place_line(breakfast), "blurb": _blurb(breakfast, "breakfast")},
                    "lunch": {"place": _place_line(lunch), "blurb": _blurb(lunch, "lunch")},
                    "dinner": {"place": _place_line(dinner), "blurb": _blurb(dinner, "dinner")},
                },
                "stops": [
                    {"time_block": "Breakfast", "place": _place_line(breakfast)},
                    {"time_block": "Morning", "place": _place_line(a1)},
                    {"time_block": "Midday", "place": _place_line(a2)},
                    {"time_block": "Afternoon", "place": _place_line(a3)},
                    {"time_block": "Lunch", "place": _place_line(lunch)},
                    {"time_block": "Dinner", "place": _place_line(dinner)},
                ],
                "spotlight": {
                    "neighborhood": {
                        "name": hood,
                        "blurb": f"Today is centered around **{hood}**—keep your stops close to cut transit time.",
                    },
                    "restaurant": {
                        "name": (dinner or lunch or breakfast or {}).get("name"),
                        "google_maps_url": (dinner or lunch or breakfast or {}).get("google_maps_url")
                        or (dinner or lunch or breakfast or {}).get("url"),
                        "blurb": _blurb(dinner or lunch or breakfast, "dinner"),
                    },
                    "site": {
                        "name": (a1 or a2 or a3 or {}).get("name"),
                        "google_maps_url": (a1 or a2 or a3 or {}).get("google_maps_url")
                        or (a1 or a2 or a3 or {}).get("url"),
                        "blurb": _blurb(a1 or a2 or a3, "site"),
                    },
                },
                "notes": [],
            }
        )

    # De-dupe pins by (day, category, name)
    seen = set()
    deduped: list[dict[str, Any]] = []
    for p in places:
        key = (p.get("day"), p.get("category"), p.get("name"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(p)

    return itinerary, deduped


@router.post("/generate")
def generate_itinerary(payload: ItineraryGenerateRequest) -> dict[str, Any]:
    """
    Generates itinerary + map places without creating/storing a trip.
    Mount this router at /api/itinerary in app/main.py to use it.
    """
    try:
        # Reuse your existing query builder and safe wrappers from trips.py
        # Build a TripRequest-like object using payload dict
        payload_dict = payload.model_dump()
        queries = build_place_queries(payload_dict)  # your trips.py accepts payload-ish input

        restaurants = safe_search_places(queries["restaurants"], limit=12)
        highlights = safe_search_places(queries["highlights"], limit=18)
        neighborhood_results = safe_search_places(queries["neighborhoods"], limit=6)
        weather = safe_get_weather(payload.destination)

        if not restaurants:
            restaurants = build_restaurants_fallback(payload_dict)
        if not highlights:
            highlights = build_highlights_fallback(payload_dict)

        neighborhoods = [x["name"] for x in neighborhood_results if x.get("name")]
        if not neighborhoods:
            neighborhoods = build_neighborhoods_fallback(payload_dict)

        itinerary, places = build_rich_days_and_places(
            destination=payload.destination,
            start_date=payload.start_date,
            end_date=payload.end_date,
            restaurants=restaurants,
            highlights=highlights,
            neighborhoods=neighborhoods,
        )

        return {
            "destination": payload.destination,
            "summary": payload.notes or "",
            "weather": weather,
            "neighborhoods": neighborhoods,
            "restaurants": restaurants,
            "highlights": highlights,
            "itinerary": itinerary,
            "places": places,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))