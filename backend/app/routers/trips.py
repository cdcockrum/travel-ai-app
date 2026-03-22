# backend/app/routers/trips.py
from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter

from app.schemas import TripRequest, TripResponse
from app.services.places_service import (
    get_attraction_recommendations,
    get_restaurant_recommendations,
)
from app.services.weather_service import get_weather_forecast

router = APIRouter()


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
    addr = place.get("address")
    return f"{name} — {addr}" if addr else name


def _push_place(
    places: list[dict[str, Any]],
    *,
    day: int,
    category: str,
    place: dict[str, Any] | None,
) -> None:
    if not place:
        return
    lat = place.get("lat")
    lng = place.get("lng")
    if lat is None or lng is None:
        return

    places.append(
        {
            "day": day,
            "category": category,
            "id": place.get("id"),
            "name": place.get("name"),
            "address": place.get("address"),
            "lat": lat,
            "lng": lng,
            "google_maps_url": place.get("google_maps_url"),
            "website_url": place.get("website_url"),
            "rating": place.get("rating"),
            "user_rating_count": place.get("user_rating_count"),
        }
    )


def build_place_based_itinerary_and_places(
    *,
    destination: str,
    start_date: str,
    end_date: str,
    restaurants: list[dict[str, Any]],
    highlights: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Builds:
      - itinerary: day-by-day text using real POI names
      - places: flat list for map markers, with day numbers
    """
    days = _trip_days(start_date, end_date)

    highlight_groups = _chunk(highlights, 2) or [[]]
    restaurant_groups = _chunk(restaurants, 2) or [[]]

    itinerary: list[dict[str, Any]] = []
    places: list[dict[str, Any]] = []

    for i in range(days):
        day_num = i + 1
        hs = highlight_groups[i % len(highlight_groups)]
        rs = restaurant_groups[i % len(restaurant_groups)]

        morning_h = hs[0] if len(hs) > 0 else None
        afternoon_h = hs[1] if len(hs) > 1 else None

        lunch_r = rs[0] if len(rs) > 0 else None
        dinner_r = rs[1] if len(rs) > 1 else None

        _push_place(places, day=day_num, category="attraction", place=morning_h)
        _push_place(places, day=day_num, category="attraction", place=afternoon_h)
        _push_place(places, day=day_num, category="restaurant", place=lunch_r)
        _push_place(places, day=day_num, category="restaurant", place=dinner_r)

        itinerary.append(
            {
                "day": day_num,
                "title": f"Day {day_num} in {destination}",
                "morning": f"Start with {_place_line(morning_h)}.",
                "afternoon": f"Then visit {_place_line(afternoon_h)}.",
                "evening": f"Lunch at {_place_line(lunch_r)}. Dinner at {_place_line(dinner_r)}.",
                "meals": [
                    f"Lunch: {_place_line(lunch_r)}",
                    f"Dinner: {_place_line(dinner_r)}",
                ],
                "notes": [],
            }
        )

    # De-dupe places by (day, category, name)
    seen: set[tuple[Any, ...]] = set()
    deduped: list[dict[str, Any]] = []
    for p in places:
        key = (p.get("day"), p.get("category"), p.get("name"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(p)

    return itinerary, deduped


@router.post("/generate", response_model=TripResponse)
def generate_trip(payload: TripRequest) -> TripResponse:
    destination = payload.destination
    prefs = payload.preferences or {}
    dietary = prefs.get("dietary_preferences") or []
    notes = (payload.notes or "").strip()

    # best-effort split "City, Country/State"
    parts = [p.strip() for p in destination.split(",")]
    city = parts[0] if parts else destination
    country = parts[1] if len(parts) > 1 else ""

    restaurants = get_restaurant_recommendations(
        city=city,
        country=country,
        notes=notes,
        dietary_prefs=dietary,
        max_results=14,
    )
    highlights = get_attraction_recommendations(
        city=city,
        country=country,
        notes=notes,
        max_results=14,
    )

    itinerary, places = build_place_based_itinerary_and_places(
        destination=destination,
        start_date=payload.start_date,
        end_date=payload.end_date,
        restaurants=restaurants,
        highlights=highlights,
    )

    weather = None
    try:
        weather = get_weather_forecast(city=city)
    except Exception:
        weather = None

    return TripResponse(
        destination=destination,
        summary=f"Your trip to {destination} tailored with real places from Google Places.",
        itinerary=itinerary,
        tips=[
            "Cluster stops by neighborhood to reduce transit time.",
            "Reserve popular restaurants on weekends.",
            "Swap indoor/outdoor activities based on weather.",
        ],
        restaurants=restaurants,
        highlights=highlights,
        neighborhoods=[],
        weather=weather,
        places=places,  # <- map uses this
    )