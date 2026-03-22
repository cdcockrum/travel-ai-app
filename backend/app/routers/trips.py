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


def _place_line(place: dict[str, Any]) -> str:
    name = place.get("name") or "a place"
    addr = place.get("address")
    if addr:
        return f"{name} — {addr}"
    return name


def build_place_based_itinerary(
    *,
    destination: str,
    start_date: str,
    end_date: str,
    restaurants: list[dict[str, Any]],
    highlights: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Produces a day-by-day itinerary that names real places.
    Uses 2 highlights + 2 restaurants per day (best-effort).
    """
    days = _trip_days(start_date, end_date)

    highlight_groups = _chunk(highlights, 2) or [[]]
    restaurant_groups = _chunk(restaurants, 2) or [[]]

    itinerary: list[dict[str, Any]] = []
    for i in range(days):
        hs = highlight_groups[i % len(highlight_groups)]
        rs = restaurant_groups[i % len(restaurant_groups)]

        morning = hs[0] if len(hs) > 0 else None
        afternoon = hs[1] if len(hs) > 1 else None
        dinner = rs[0] if len(rs) > 0 else None
        optional = rs[1] if len(rs) > 1 else None

        itinerary.append(
            {
                "day": i + 1,
                "title": f"Day {i+1} in {destination}",
                "morning": f"Start with { _place_line(morning) }." if morning else "Start with a neighborhood walk and coffee.",
                "afternoon": f"Then visit { _place_line(afternoon) }." if afternoon else "Pick one major attraction and explore nearby.",
                "evening": f"Dinner at { _place_line(dinner) }." if dinner else "Dinner at a well-rated local restaurant.",
                "meals": [
                    f"Dinner: {_place_line(dinner)}" if dinner else "Dinner: choose a top-rated local spot",
                    f"Optional: {_place_line(optional)}" if optional else "Optional: dessert / nightcap spot",
                ],
                "notes": [],
            }
        )

    return itinerary


@router.post("/generate", response_model=TripResponse)
def generate_trip(payload: TripRequest) -> TripResponse:
    """
    Generates a trip with real places + real weather.
    """
    destination = payload.destination
    prefs = payload.preferences or {}
    dietary = prefs.get("dietary_preferences") or []
    notes = (payload.notes or "").strip()

    # Split destination into "city, country" best-effort (keeps your existing API signatures)
    # Example: "Chicago, IL" -> city="Chicago" country="IL"
    parts = [p.strip() for p in destination.split(",")]
    city = parts[0] if parts else destination
    country = parts[1] if len(parts) > 1 else ""

    restaurants = get_restaurant_recommendations(
        city=city,
        country=country,
        notes=notes,
        dietary_prefs=dietary,
        max_results=12,
    )
    highlights = get_attraction_recommendations(
        city=city,
        country=country,
        notes=notes,
        max_results=12,
    )

    itinerary = build_place_based_itinerary(
        destination=destination,
        start_date=payload.start_date,
        end_date=payload.end_date,
        restaurants=restaurants,
        highlights=highlights,
    )

    # Weather: your weather service returns a forecast list; keep it as-is
    weather = None
    try:
        weather = get_weather_forecast(city=city)
    except Exception:
        weather = None

    return TripResponse(
        destination=destination,
        summary=f"Your trip to {destination} with real places pulled from Google Places.",
        itinerary=itinerary,
        tips=[
            "Cluster stops by neighborhood to reduce transit time.",
            "Make dinner reservations for top-rated places (especially weekends).",
            "Check weather each morning and swap indoor/outdoor highlights as needed.",
        ],
        restaurants=restaurants,
        neighborhoods=[],  # keep schema happy if it expects this field
        weather=weather,
    )