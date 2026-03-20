from fastapi import APIRouter, HTTPException

from app.services.hotel_service import get_hotel_recommendations
from app.services.places_service import (
    get_attraction_recommendations,
    get_restaurant_recommendations,
    simplify_places,
)
from app.services.trip_store import get_trip

router = APIRouter()


@router.get("/{trip_id}")
def get_trip_recommendations(trip_id: str) -> dict:
    trip = get_trip(trip_id)

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    city = trip.get("destination_city")
    country = trip.get("destination_country")
    notes = trip.get("notes", "")
    budget_level = trip.get("budget_level", "moderate")

    restaurants = []
    attractions = []
    errors: list[str] = []

    try:
        restaurants = simplify_places(
            get_restaurant_recommendations(city=city, country=country, notes=notes)
        )
    except Exception as exc:
        errors.append(f"Restaurants unavailable: {exc}")

    try:
        attractions = simplify_places(
            get_attraction_recommendations(city=city, country=country, notes=notes)
        )
    except Exception as exc:
        errors.append(f"Attractions unavailable: {exc}")

    try:
        hotels = get_hotel_recommendations(
            city=city,
            country=country,
            notes=notes,
            budget_level=budget_level,
        )
    except Exception as exc:
        hotels = []
        errors.append(f"Hotels unavailable: {exc}")

    return {
        "trip_id": trip_id,
        "destination_city": city,
        "destination_country": country,
        "restaurants": restaurants,
        "attractions": attractions,
        "hotels": hotels,
        "errors": errors,
    }