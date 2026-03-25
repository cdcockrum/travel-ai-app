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


def _is_real_place(place: dict[str, Any] | None) -> bool:
    if not place:
        return False

    name = str(place.get("name") or "").strip().lower()
    bad_names = {
        "",
        "a place",
        "local spot",
        "top-rated local spot",
        "local restaurant",
    }
    return name not in bad_names


def _place_line(place: dict[str, Any]) -> str:
    name = place.get("name") or "a place"
    addr = place.get("address")
    if addr:
        return f"{name} — {addr}"
    return name


def _filter_real_places(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for item in items if _is_real_place(item)]


def build_place_based_itinerary(
    *,
    destination: str,
    start_date: str,
    end_date: str,
    restaurants: list[dict[str, Any]],
    highlights: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Produces a day-by-day itinerary using real named places only.
    """
    days = _trip_days(start_date, end_date)

    restaurants = _filter_real_places(restaurants)
    highlights = _filter_real_places(highlights)

    highlight_groups = _chunk(highlights, 2) or [[]]
    restaurant_groups = _chunk(restaurants, 2) or [[]]

    itinerary: list[dict[str, Any]] = []

    for i in range(days):
        hs = highlight_groups[i % len(highlight_groups)] if highlight_groups else []
        rs = restaurant_groups[i % len(restaurant_groups)] if restaurant_groups else []

        morning = hs[0] if len(hs) > 0 else None
        afternoon = hs[1] if len(hs) > 1 else None
        dinner = rs[0] if len(rs) > 0 else None
        optional = rs[1] if len(rs) > 1 else None

        meals: list[str] = []
        if dinner:
            meals.append(f"Dinner: {_place_line(dinner)}")
        if optional:
            meals.append(f"Optional: {_place_line(optional)}")

        itinerary.append(
            {
                "day": i + 1,
                "title": f"Day {i + 1} in {destination}",
                "morning": (
                    f"Start with { _place_line(morning) }."
                    if morning
                    else "Start with a neighborhood walk and coffee."
                ),
                "afternoon": (
                    f"Then visit { _place_line(afternoon) }."
                    if afternoon
                    else "Pick one major attraction and explore nearby."
                ),
                "evening": (
                    f"Dinner at { _place_line(dinner) }."
                    if dinner
                    else "Choose dinner from the restaurant ideas below."
                ),
                "meals": meals,
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
    restaurants = _filter_real_places(restaurants)

    highlights = get_attraction_recommendations(
        city=city,
        country=country,
        notes=notes,
        max_results=12,
    )
    highlights = _filter_real_places(highlights)

    itinerary = build_place_based_itinerary(
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
        summary=f"Your trip to {destination} with real places pulled from Google Places.",
        itinerary=itinerary,
        tips=[
            "Cluster stops by neighborhood to reduce transit time.",
            "Make dinner reservations for top-rated places (especially weekends).",
            "Check weather each morning and swap indoor/outdoor highlights as needed.",
        ],
        restaurants=restaurants,
        neighborhoods=[],
        weather=weather,
    )