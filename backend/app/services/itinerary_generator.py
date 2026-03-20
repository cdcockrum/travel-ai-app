from collections import defaultdict
from datetime import date

from app.services.hotel_service import get_hotel_recommendations
from app.services.places_service import (
    get_attraction_recommendations,
    get_restaurant_recommendations,
)
from app.services.trip_store import get_trip


def _extract_area(address: str | None) -> str:
    if not address:
        return "Central District"

    parts = [p.strip() for p in address.split(",") if p.strip()]

    if len(parts) >= 3:
        return parts[-3]
    if len(parts) >= 2:
        return parts[-2]
    return parts[0]


def _cluster_places_by_area(places: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)

    for place in places:
        area = _extract_area(place.get("address"))
        grouped[area].append(place)

    return dict(grouped)


def _rank_places(places: list[dict]) -> list[dict]:
    return sorted(
        places,
        key=lambda p: (
            p.get("rating") or 0,
            p.get("user_rating_count") or 0,
        ),
        reverse=True,
    )


def _unique_by_id(places: list[dict]) -> list[dict]:
    seen = set()
    unique = []

    for place in places:
        pid = place.get("id")
        if not pid or pid in seen:
            continue
        seen.add(pid)
        unique.append(place)

    return unique


def _add_place(day_places: list[dict], place: dict | None, category: str) -> None:
    if not place:
        return

    day_places.append(
        {
            "name": place.get("name"),
            "address": place.get("address"),
            "lat": place.get("lat"),
            "lng": place.get("lng"),
            "category": category,
            "google_maps_url": place.get("google_maps_url"),
        }
    )


def _rotate_list(items: list[dict], start_idx: int, count: int) -> list[dict]:
    if not items:
        return []

    result = []
    n = len(items)

    for i in range(count):
        result.append(items[(start_idx + i) % n])

    return result


def _theme_for_day(
    day_number: int,
    total_days: int,
    has_food_focus: bool,
    has_culture_focus: bool,
    area: str,
) -> str:
    if day_number == 1:
        return "Arrival and neighborhood immersion"
    if day_number == total_days:
        return f"Final day in {area}"

    if has_food_focus and has_culture_focus:
        return f"Food and culture in {area}"
    if has_food_focus:
        return f"Culinary exploration in {area}"
    if has_culture_focus:
        return f"Cultural highlights in {area}"

    return f"Explore {area}"


def _build_day_plan(
    day_number: int,
    total_days: int,
    area: str,
    hotel: dict | None,
    attractions: list[dict],
    restaurants: list[dict],
    pace_level: str,
    day_start_preference: str,
    has_food_focus: bool,
    has_culture_focus: bool,
) -> dict:
    day_places: list[dict] = []

    attraction_1 = attractions[0] if len(attractions) > 0 else None
    attraction_2 = attractions[1] if len(attractions) > 1 else None
    attraction_3 = attractions[2] if len(attractions) > 2 else None

    breakfast_spot = restaurants[0] if len(restaurants) > 0 else None
    lunch_spot = restaurants[1] if len(restaurants) > 1 else None
    dinner_spot = restaurants[2] if len(restaurants) > 2 else None

    morning: list[str] = []
    breakfast: list[str] = []
    lunch: list[str] = []
    afternoon: list[str] = []
    dinner: list[str] = []
    evening: list[str] = []

    theme = _theme_for_day(
        day_number=day_number,
        total_days=total_days,
        has_food_focus=has_food_focus,
        has_culture_focus=has_culture_focus,
        area=area,
    )

    if day_number == 1 and hotel:
        morning.append(f"Check in or drop bags at {hotel['name']}")
        day_places.append(
            {
                "name": hotel["name"],
                "address": hotel["area"],
                "lat": None,
                "lng": None,
                "category": "hotel",
                "google_maps_url": None,
            }
        )

    if day_start_preference == "late":
        if attraction_1:
            morning.append(f"Ease into the day with a later start near {attraction_1['name']}")
            _add_place(day_places, attraction_1, "attraction")
        else:
            morning.append(f"Take a relaxed start in {area}")
    else:
        if attraction_1:
            morning.append(f"Start the day at {attraction_1['name']}")
            _add_place(day_places, attraction_1, "attraction")
        else:
            morning.append(f"Begin with a walk through {area}")

    if breakfast_spot:
        breakfast.append(f"Breakfast or coffee near {breakfast_spot['name']}")
        _add_place(day_places, breakfast_spot, "restaurant")
    else:
        breakfast.append(f"Have a relaxed breakfast in {area}")

    if attraction_2:
        lunch.append(f"Continue toward {attraction_2['name']} before lunch")
        _add_place(day_places, attraction_2, "attraction")
    elif has_culture_focus and attraction_1:
        lunch.append(f"Spend more time exploring around {attraction_1['name']}")
    else:
        lunch.append(f"Keep lunch flexible while exploring {area}")

    if lunch_spot:
        lunch.append(f"Lunch at or near {lunch_spot['name']}")
        _add_place(day_places, lunch_spot, "restaurant")
    else:
        lunch.append("Choose a highly rated local lunch spot nearby")

    if attraction_3:
        afternoon.append(f"Visit {attraction_3['name']} in the afternoon")
        _add_place(day_places, attraction_3, "attraction")
    elif attraction_2:
        afternoon.append(f"Explore the surrounding streets after {attraction_2['name']}")
    elif has_food_focus:
        afternoon.append(f"Use the afternoon to browse food-focused areas in {area}")
    else:
        afternoon.append(f"Keep the afternoon open for neighborhood exploration in {area}")

    if dinner_spot:
        dinner.append(f"Dinner at {dinner_spot['name']}")
        _add_place(day_places, dinner_spot, "restaurant")
    elif lunch_spot:
        dinner.append(f"Choose another well-rated dinner spot in the same area as {lunch_spot['name']}")
    else:
        dinner.append("Choose a memorable local dinner")

    if pace_level == "relaxed":
        evening.append("Leave the evening flexible for wandering, rest, or one spontaneous stop")
        practical_note = "This day is intentionally lighter and more flexible while still staying anchored to one neighborhood."
    elif pace_level == "packed":
        evening.append("Add one final stop, dessert spot, or evening viewpoint if energy allows")
        practical_note = "This day is designed to fit in more variety while keeping the route geographically coherent."
    else:
        evening.append("Keep the evening open for a stroll, dessert, or a relaxed drink nearby")
        practical_note = "Meals and activities are spaced out to keep the day enjoyable and realistic."

    return {
        "day_number": day_number,
        "theme": theme,
        "neighborhood": area,
        "morning": morning,
        "breakfast": breakfast,
        "lunch": lunch,
        "afternoon": afternoon,
        "dinner": dinner,
        "evening": evening,
        "places": day_places,
        "practical_note": practical_note,
    }


def generate_itinerary(trip_id: str) -> dict:
    trip = get_trip(trip_id)

    if not trip:
        return {"trip_summary": "No trip was found.", "days": []}

    destination_city = trip.get("destination_city", "the city")
    destination_country = trip.get("destination_country", "")
    notes = trip.get("notes", "")
    notes_lower = notes.lower()
    budget_level = trip.get("budget_level", "moderate")
    profile = trip.get("profile") or {}

    dietary_prefs = profile.get("dietary_preferences", [])
    pace_level = profile.get("pace_level", "balanced")
    day_start_preference = profile.get("day_start_preference", "mid-morning")
    top_interests = profile.get("top_interests", [])

    has_food_focus = "food" in top_interests or "food" in notes_lower
    has_culture_focus = (
        "local culture" in top_interests
        or "architecture" in top_interests
        or "culture" in notes_lower
        or "architecture" in notes_lower
        or "museum" in notes_lower
    )

    start_date = date.fromisoformat(trip["start_date"])
    end_date = date.fromisoformat(trip["end_date"])
    trip_length = max(1, (end_date - start_date).days + 1)

    restaurants: list[dict] = []
    attractions: list[dict] = []

    try:
        restaurants = get_restaurant_recommendations(
            city=destination_city,
            country=destination_country,
            notes=notes,
            dietary_prefs=dietary_prefs,
            max_results=18,
        )
    except Exception:
        restaurants = []

    try:
        attractions = get_attraction_recommendations(
            city=destination_city,
            country=destination_country,
            notes=notes,
            max_results=18,
        )
    except Exception:
        attractions = []

    restaurants = _unique_by_id(_rank_places(restaurants))
    attractions = _unique_by_id(_rank_places(attractions))

    restaurant_clusters = _cluster_places_by_area(restaurants)
    attraction_clusters = _cluster_places_by_area(attractions)

    all_areas = list(
        dict.fromkeys(
            list(attraction_clusters.keys()) + list(restaurant_clusters.keys())
        )
    )

    hotels = get_hotel_recommendations(
        city=destination_city,
        country=destination_country,
        notes=notes,
        budget_level=budget_level,
    )
    selected_hotel = hotels[0] if hotels else None

    if not all_areas:
        all_areas = [selected_hotel["area"] if selected_hotel else "Central District"]

    days = []
    for i in range(trip_length):
        area = all_areas[i % len(all_areas)]

        area_attractions = attraction_clusters.get(area, [])
        area_restaurants = restaurant_clusters.get(area, [])

        # fall back to rotated global results if local cluster is sparse
        if len(area_attractions) < 3:
            needed = 3 - len(area_attractions)
            extra = _rotate_list(attractions, i, needed + 2)
            area_attractions = _unique_by_id(area_attractions + extra)

        if len(area_restaurants) < 3:
            needed = 3 - len(area_restaurants)
            extra = _rotate_list(restaurants, i, needed + 2)
            area_restaurants = _unique_by_id(area_restaurants + extra)

        day = _build_day_plan(
            day_number=i + 1,
            total_days=trip_length,
            area=area,
            hotel=selected_hotel if i == 0 else None,
            attractions=area_attractions[:3],
            restaurants=area_restaurants[:3],
            pace_level=pace_level,
            day_start_preference=day_start_preference,
            has_food_focus=has_food_focus,
            has_culture_focus=has_culture_focus,
        )
        days.append(day)

    summary_parts = [
        f"A personalized itinerary for {destination_city}, {destination_country}.",
    ]

    if selected_hotel:
        summary_parts.append(
            f"Suggested hotel base: {selected_hotel['name']} in {selected_hotel['area']}."
        )

    if has_food_focus:
        summary_parts.append(
            "Food experiences are weighted more heavily throughout the trip."
        )

    if has_culture_focus:
        summary_parts.append(
            "Cultural and architectural stops are prioritized."
        )

    if dietary_prefs:
        summary_parts.append(
            f"Dining suggestions reflect these preferences: {', '.join(dietary_prefs)}."
        )

    summary_parts.append(
        "Days are grouped by neighborhood to reduce backtracking and make the trip feel more natural."
    )

    return {
        "trip_summary": " ".join(summary_parts),
        "days": days,
    }