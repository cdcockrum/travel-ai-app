from collections import defaultdict
from datetime import date

from app.services.hotel_service import get_hotel_recommendations
from app.services.places_service import (
    get_attraction_recommendations,
    get_restaurant_recommendations,
    simplify_places,
)
from app.services.trip_store import get_trip


def _extract_area(address: str | None) -> str:
    if not address:
        return "Central District"

    parts = [p.strip() for p in address.split(",") if p.strip()]
    if len(parts) >= 2:
        return parts[1]
    return parts[0] if parts else "Central District"


def _cluster_places_by_area(places: list[dict]) -> dict[str, list[dict]]:
    clusters: dict[str, list[dict]] = defaultdict(list)
    for place in places:
        area = _extract_area(place.get("address"))
        clusters[area].append(place)
    return dict(clusters)


def _rank_places(
    places: list[dict], food_weight: int = 0, culture_weight: int = 0
) -> list[dict]:
    def score(p: dict) -> tuple:
        base_rating = p.get("rating") or 0
        review_count = p.get("user_rating_count") or 0
        type_text = " ".join(p.get("types", []) or []).lower()

        boost = 0
        if food_weight and (
            "restaurant" in type_text or "food" in type_text or "cafe" in type_text
        ):
            boost += food_weight
        if culture_weight and (
            "museum" in type_text
            or "tourist_attraction" in type_text
            or "art_gallery" in type_text
            or "cultural" in type_text
            or "temple" in type_text
        ):
            boost += culture_weight

        return (base_rating + boost, review_count)

    return sorted(places, key=score, reverse=True)


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


def _pick_restaurants_for_day(
    area_restaurants: list[dict],
    all_restaurants: list[dict],
) -> list[dict]:
    ranked_area = _rank_places(area_restaurants, food_weight=1)
    if len(ranked_area) >= 3:
        return ranked_area[:3]

    ranked_all = _rank_places(all_restaurants, food_weight=1)

    seen_ids = set()
    chosen: list[dict] = []

    for place in ranked_area + ranked_all:
        place_id = place.get("id")
        if place_id in seen_ids:
            continue
        seen_ids.add(place_id)
        chosen.append(place)
        if len(chosen) == 3:
            break

    return chosen


def _build_day(
    day_number: int,
    theme: str,
    neighborhood: str,
    hotel: dict | None,
    attractions: list[dict],
    restaurants_for_day: list[dict],
    balanced: bool,
    food_focused: bool,
    adventurous_food: bool,
    walking_tolerance: str,
    structure_preference: str,
    day_start_preference: str,
    relaxed: bool,
) -> dict:
    day_places: list[dict] = []

    a1 = attractions[0] if len(attractions) > 0 else None
    a2 = attractions[1] if len(attractions) > 1 else None

    r1 = restaurants_for_day[0] if len(restaurants_for_day) > 0 else None
    r2 = restaurants_for_day[1] if len(restaurants_for_day) > 1 else None
    r3 = restaurants_for_day[2] if len(restaurants_for_day) > 2 else None

    morning = []
    breakfast = []
    lunch = []
    afternoon = []
    dinner = []
    evening = []

    if day_number == 1 and hotel:
        morning.append(f"Check-in at {hotel['name']}")
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
    elif day_start_preference == "late":
        morning.append("Start slowly and ease into the day with a lighter first stop")
        if a1:
            afternoon.insert(0, f"Visit {a1['name']}")
            _add_place(day_places, a1, "attraction")
    elif a1:
        morning.append(f"Start the day at {a1['name']}")
        _add_place(day_places, a1, "attraction")
    else:
        morning.append("Start with a gentle neighborhood walk")

    if food_focused and r1:
        if adventurous_food:
            breakfast.append(
                f"Try a distinctive local breakfast, pastry, or coffee near {r1['name']}"
            )
        else:
            breakfast.append(f"Have an easy breakfast or coffee near {r1['name']}")
        _add_place(day_places, r1, "restaurant")
    else:
        breakfast.append("Take a relaxed breakfast near your first stop")

    if not relaxed:
        if a2:
            afternoon.append(f"Continue on to {a2['name']}")
            _add_place(day_places, a2, "attraction")
        elif a1 and day_start_preference != "late":
            afternoon.append(f"Spend more time around {a1['name']}")
        elif not afternoon:
            afternoon.append("Keep the afternoon open for neighborhood exploration")
    else:
        if a1 and day_start_preference != "late":
            afternoon.append(f"Take your time around {a1['name']}")
        else:
            afternoon.append("Keep the afternoon intentionally light and flexible")

    if r2:
        lunch.append(f"Lunch at or near {r2['name']}")
        _add_place(day_places, r2, "restaurant")
    elif r1:
        lunch.append(f"Lunch in the area around {r1['name']}")
    else:
        lunch.append("Pick a well-rated local lunch spot nearby")

    if r3 and not relaxed:
        dinner.append(f"Dinner at {r3['name']}")
        _add_place(day_places, r3, "restaurant")
    elif r2:
        dinner.append(f"Dinner near {r2['name']}")
    elif r1:
        dinner.append(f"Return to the area around {r1['name']} for dinner")
    else:
        dinner.append("Choose a memorable local dinner")

    if walking_tolerance == "low":
        afternoon = afternoon[:1]
        evening = ["Keep the evening quiet and close to your base"]
        note = "This day is intentionally compact to reduce walking and keep transitions easy."
    elif relaxed:
        evening = ["Leave room for rest, wandering, or one spontaneous stop"]
        note = "This is a lighter day with more breathing room, but it still preserves the full trip length."
    elif structure_preference == "fully planned":
        evening = ["End the day with a planned final stop or a reservation"]
        note = "This day is structured clearly so you do not need to improvise much."
    elif balanced:
        evening = ["Keep the evening flexible for a walk or a relaxed drink"]
        note = "Meals and activities are spaced out to keep the day enjoyable and realistic."
    else:
        evening = ["Use the evening for one final stop or an easy neighborhood stroll"]
        note = "The day is grouped geographically to reduce transit and create a smoother flow."

    return {
        "day_number": day_number,
        "theme": theme,
        "neighborhood": neighborhood,
        "morning": morning,
        "breakfast": breakfast,
        "lunch": lunch,
        "afternoon": afternoon,
        "dinner": dinner,
        "evening": evening,
        "places": day_places,
        "practical_note": note,
    }


def generate_itinerary(trip_id: str) -> dict:
    trip = get_trip(trip_id)

    if not trip:
        return {"trip_summary": "No trip was found.", "days": []}

    destination_city = trip.get("destination_city", "the city")
    destination_country = trip.get("destination_country", "")
    notes = (trip.get("notes") or "").lower()
    budget_level = trip.get("budget_level", "moderate")
    profile = trip.get("profile") or {}

    pace_level = profile.get("pace_level", "balanced")
    walking_tolerance = profile.get("walking_tolerance", "moderate")
    food_adventure_level = profile.get("food_adventure_level", "moderate")
    structure_preference = profile.get(
        "structure_preference", "some structure with flexibility"
    )
    authenticity = profile.get("convenience_vs_authenticity", 3)
    top_interests = profile.get("top_interests", [])
    day_start_preference = profile.get("day_start_preference", "mid-morning")

    is_food_focused = "food" in top_interests or "food" in notes
    is_culture_focused = (
        "architecture" in top_interests
        or "local culture" in top_interests
        or "culture" in notes
        or "architecture" in notes
    )
    is_balanced_discoverer = pace_level == "balanced" or "balanced discoverer" in notes
    adventurous_food = food_adventure_level == "high"
    relaxed = pace_level == "relaxed"

    restaurants = []
    attractions = []

    try:
        restaurants = simplify_places(
            get_restaurant_recommendations(
                city=destination_city,
                country=destination_country,
                notes=notes,
            )
        )
    except Exception:
        restaurants = []

    try:
        attractions = simplify_places(
            get_attraction_recommendations(
                city=destination_city,
                country=destination_country,
                notes=notes,
            )
        )
    except Exception:
        attractions = []

    restaurant_food_weight = 2 if is_food_focused else 0
    attraction_culture_weight = 1 if is_culture_focused else 0

    restaurants = _rank_places(restaurants, food_weight=restaurant_food_weight)
    attractions = _rank_places(attractions, culture_weight=attraction_culture_weight)

    if authenticity >= 4:
        restaurants = restaurants[:10]
        attractions = attractions[:10]

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

    start_date = date.fromisoformat(trip["start_date"])
    end_date = date.fromisoformat(trip["end_date"])
    trip_length = max(1, (end_date - start_date).days + 1)

    day_count = trip_length

    if len(all_areas) < day_count:
        while len(all_areas) < day_count:
            all_areas.append(all_areas[-1])

    days = []
    for idx in range(day_count):
        area = all_areas[idx]
        area_attractions = attraction_clusters.get(area, [])
        area_restaurants = restaurant_clusters.get(area, [])
        restaurants_for_day = _pick_restaurants_for_day(area_restaurants, restaurants)

        if idx == 0:
            theme = "Arrival and gentle immersion"
        elif idx == day_count - 1:
            theme = f"Final day in {area}"
        else:
            theme = f"Explore {area}"

        day = _build_day(
            day_number=idx + 1,
            theme=theme,
            neighborhood=area,
            hotel=selected_hotel if idx == 0 else None,
            attractions=area_attractions,
            restaurants_for_day=restaurants_for_day,
            balanced=is_balanced_discoverer,
            food_focused=is_food_focused,
            adventurous_food=adventurous_food,
            walking_tolerance=walking_tolerance,
            structure_preference=structure_preference,
            day_start_preference=day_start_preference,
            relaxed=relaxed,
        )
        days.append(day)

    summary_parts = [
        f"A personalized itinerary for {destination_city}, {destination_country}."
    ]
    if selected_hotel:
        summary_parts.append(
            f"Suggested hotel base: {selected_hotel['name']} in {selected_hotel['area']}."
        )
    if is_food_focused:
        summary_parts.append("Food experiences are weighted more heavily throughout the trip.")
    if is_culture_focused:
        summary_parts.append("Cultural and architectural stops are prioritized.")
    if relaxed:
        summary_parts.append("The schedule is intentionally lighter with more breathing room.")
    elif pace_level == "packed":
        summary_parts.append("The trip packs in more activity and variety each day.")
    if walking_tolerance == "low":
        summary_parts.append("Walking demands are kept lower and transitions are simplified.")
    if structure_preference == "fully planned":
        summary_parts.append("Each day is laid out in a more structured way.")
    if authenticity >= 4:
        summary_parts.append("Recommendations lean more local and less convenience-driven.")
    summary_parts.append(
        "Days are grouped by neighborhood to reduce backtracking and make the trip feel more natural."
    )

    return {
        "trip_summary": " ".join(summary_parts),
        "days": days,
    }