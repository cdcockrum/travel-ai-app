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
        return "Arrival and first impressions"
    if day_number == total_days:
        return f"Last looks around {area}"

    if has_food_focus and has_culture_focus:
        return f"Taste and texture of {area}"
    if has_food_focus:
        return f"A day shaped around food in {area}"
    if has_culture_focus:
        return f"Cultural landmarks and slower wandering in {area}"

    return f"A day unfolding through {area}"


def _restaurant_reason(place: dict, dietary_prefs: list[str]) -> str:
    name = (place.get("name") or "").lower()
    types = " ".join(place.get("types", [])).lower()
    rating = place.get("rating") or 0

    if "vegan" in dietary_prefs and ("vegan" in name or "vegan" in types):
        return "Chosen because it appears to align especially well with vegan preferences."
    if "vegetarian" in dietary_prefs and (
        "vegetarian" in name or "vegetarian" in types or "veggie" in name
    ):
        return "Chosen because it appears to align well with vegetarian preferences."
    if rating >= 4.6:
        return "Chosen for its especially strong rating and local popularity."
    if "cafe" in types:
        return "Chosen as an easy, well-placed stop that fits naturally into the day."
    return "Chosen because it fits the area well and helps keep the day geographically smooth."


def _attraction_reason(place: dict) -> str:
    types = " ".join(place.get("types", [])).lower()
    rating = place.get("rating") or 0

    if "museum" in types:
        return "Included as a strong cultural stop that adds depth to the day."
    if "temple" in types or "shrine" in types or "church" in types:
        return "Included because it offers a memorable sense of place and atmosphere."
    if rating >= 4.6:
        return "Included because it stands out as one of the stronger-rated stops nearby."
    return "Included because it fits naturally with the surrounding neighborhood."


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
    dietary_prefs: list[str],
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
        morning.append(f"Drop bags and settle in at {hotel['name']} before heading out.")
        day_places.append(
            {
                "name": hotel["name"],
                "address": hotel["area"],
                "lat": None,
                "lng": None,
                "category": "hotel",
                "google_maps_url": None,
                "why": "Used as the practical base for the first day.",
                "best_for": "hotel base",
            }
        )

    if day_start_preference == "late":
        if attraction_1:
            morning.append(f"Start later and ease into the neighborhood around {attraction_1['name']}.")
            _add_place(day_places, attraction_1, "attraction")
            day_places[-1]["why"] = _attraction_reason(attraction_1)
            day_places[-1]["best_for"] = "culture" if has_culture_focus else "landmark"
        else:
            morning.append(f"Take a slower start and let {area} set the tone for the day.")
    else:
        if attraction_1:
            morning.append(f"Begin the day at {attraction_1['name']}, then let the area unfold from there.")
            _add_place(day_places, attraction_1, "attraction")
            day_places[-1]["why"] = _attraction_reason(attraction_1)
            day_places[-1]["best_for"] = "culture" if has_culture_focus else "landmark"
        else:
            morning.append(f"Begin with an easy walk through {area} to get your bearings.")

    if breakfast_spot:
        breakfast.append(f"Pause for breakfast or coffee near {breakfast_spot['name']}.")
        _add_place(day_places, breakfast_spot, "restaurant")
        day_places[-1]["why"] = _restaurant_reason(breakfast_spot, dietary_prefs)
        day_places[-1]["best_for"] = "breakfast"
    else:
        breakfast.append(f"Keep breakfast light and flexible somewhere nearby in {area}.")

    if attraction_2:
        lunch.append(f"Continue toward {attraction_2['name']} before breaking for lunch.")
        _add_place(day_places, attraction_2, "attraction")
        day_places[-1]["why"] = _attraction_reason(attraction_2)
        day_places[-1]["best_for"] = "sightseeing"
    elif has_culture_focus and attraction_1:
        lunch.append(f"Spend a little longer around {attraction_1['name']} and the surrounding streets before lunch.")
    else:
        lunch.append(f"Keep the middle of the day flexible while exploring {area}.")

    if lunch_spot:
        lunch.append(f"Plan lunch at or near {lunch_spot['name']}.")
        _add_place(day_places, lunch_spot, "restaurant")
        day_places[-1]["why"] = _restaurant_reason(lunch_spot, dietary_prefs)
        day_places[-1]["best_for"] = "lunch"
    else:
        lunch.append("Pick a well-reviewed local lunch spot without over-structuring the day.")

    if attraction_3:
        afternoon.append(f"Use the afternoon for {attraction_3['name']} and the nearby streets around it.")
        _add_place(day_places, attraction_3, "attraction")
        day_places[-1]["why"] = _attraction_reason(attraction_3)
        day_places[-1]["best_for"] = "afternoon stop"
    elif attraction_2:
        afternoon.append(f"Let the afternoon drift through the surrounding blocks after {attraction_2['name']}.")
    elif has_food_focus:
        afternoon.append(f"Leave space to browse smaller food spots and side streets around {area}.")
    else:
        afternoon.append(f"Keep the afternoon open for unplanned wandering in {area}.")

    if dinner_spot:
        dinner.append(f"End the day with dinner at {dinner_spot['name']}.")
        _add_place(day_places, dinner_spot, "restaurant")
        day_places[-1]["why"] = _restaurant_reason(dinner_spot, dietary_prefs)
        day_places[-1]["best_for"] = "dinner"
    elif lunch_spot:
        dinner.append(f"Stay in the same general area for dinner so the evening remains easy and relaxed.")
    else:
        dinner.append("Choose one memorable dinner rather than overfilling the evening.")

    if pace_level == "relaxed":
        evening.append("Leave the evening open for a soft landing: dessert, a short walk, or simply rest.")
        practical_note = "This day is intentionally lighter and leaves room for detours, slower meals, and recovery time."
    elif pace_level == "packed":
        evening.append("If energy is still high, add one final stop, dessert counter, or viewpoint nearby.")
        practical_note = "This day carries more momentum, but it is still grouped to avoid excessive transit."
    else:
        evening.append("Keep the evening mostly flexible so the day can end naturally rather than feeling over-managed.")
        practical_note = "The pacing aims to feel intentional without becoming rigid."

    narrative = (
        f"Day {day_number} is built around {area}, using a tighter neighborhood focus so meals, sights, "
        f"and walking all connect more naturally."
    )

    return {
        "day_number": day_number,
        "theme": theme,
        "neighborhood": area,
        "narrative": narrative,
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
    except Exception as exc:
        print("ITINERARY RESTAURANT ERROR:", repr(exc))
        restaurants = []

    try:
        attractions = get_attraction_recommendations(
            city=destination_city,
            country=destination_country,
            notes=notes,
            max_results=18,
        )
    except Exception as exc:
        print("ITINERARY ATTRACTION ERROR:", repr(exc))
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
            dietary_prefs=dietary_prefs,
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
        summary_parts.append("Food is weighted more heavily, so the trip is shaped around stronger meal moments and nearby discoveries.")

    if has_culture_focus:
        summary_parts.append("Cultural and architectural stops are given more prominence throughout the trip.")

    if dietary_prefs:
        summary_parts.append(
            f"Dining suggestions also reflect these preferences: {', '.join(dietary_prefs)}."
        )

    summary_parts.append(
        "The days are grouped geographically to reduce backtracking and make the rhythm of the trip feel smoother."
    )

    return {
        "trip_summary": " ".join(summary_parts),
        "days": days,
    }