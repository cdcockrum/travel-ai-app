from fastapi import APIRouter
from datetime import datetime, timedelta

from app.schemas import TripRequest, TripResponse
from app.services.google_places import search_places
from app.services.weather import get_weather_for_destination


def build_dynamic_itinerary(payload: TripRequest) -> list[dict]:
    prefs = payload.preferences or {}

    dietary = prefs.get("dietary_preferences") or []
    allergies = prefs.get("allergies") or []
    accessibility = prefs.get("accessibility_needs") or []
    meal_times = prefs.get("preferred_meal_times") or []
    neighborhood_style = prefs.get("neighborhood_style") or []
    top_interests = prefs.get("top_interests") or []
    crowd_tolerance = prefs.get("crowd_tolerance")
    day_start = prefs.get("day_start_preference")
    nightlife = prefs.get("nightlife_interest")
    shopping = prefs.get("shopping_interest")
    wellness = prefs.get("wellness_interest")
    photography = prefs.get("photography_interest")
    transport = prefs.get("transport_preferences") or []

    start = datetime.fromisoformat(payload.start_date).date()
    end = datetime.fromisoformat(payload.end_date).date()
    total_days = max(1, (end - start).days + 1)

    itinerary = []

    for i in range(total_days):
        current_day = i + 1
        notes = []

        if dietary:
            notes.append(f"Prioritize dining that supports {', '.join(dietary)}.")
        if allergies:
            notes.append(f"Avoid places involving {', '.join(allergies)}.")
        if accessibility:
            notes.append(f"Keep logistics aligned with {', '.join(accessibility)}.")
        if crowd_tolerance == "low":
            notes.append("Favor quieter time windows and lower-crowd stops.")
        if transport:
            notes.append(f"Prefer movement by {', '.join(transport[:3])}.")
        if neighborhood_style:
            notes.append(f"Spend time in areas that feel {', '.join(neighborhood_style[:2])}.")
        if meal_times:
            notes.append(f"Anchor meals around {', '.join(meal_times[:3])}.")
        if photography == "high":
            notes.append("Include photogenic locations.")
        if shopping == "high":
            notes.append("Include dedicated browsing or shopping time.")
        if wellness == "high":
            notes.append("Protect time for calmer restorative experiences.")

        if current_day == 1:
            title = f"Arrival and orientation in {payload.destination}"
            morning = (
                "Begin with a slower start and an easy breakfast nearby."
                if day_start == "late"
                else "Start with a smooth orientation walk and an easy first stop."
            )
            afternoon = "Explore one manageable neighborhood with low-friction logistics."
            evening = "Settle into a dinner plan that matches your comfort, pace, and food preferences."
        elif current_day == total_days:
            title = f"Final favorites in {payload.destination}"
            morning = "Revisit a favorite café, market, or neighborhood at an easy pace."
            afternoon = "Use the afternoon for one last signature experience or scenic walk."
            evening = "Finish with a memorable last dinner in an area that best fits your travel style."
        else:
            title = f"Day {current_day}: neighborhood discovery and signature experiences"
            morning = "Start with coffee, breakfast, or a gentle local walk depending on preferred pace."

            if "local culture" in top_interests or "architecture" in top_interests:
                afternoon = "Explore a culturally rich district with food, design, and local atmosphere."
            elif "museums" in top_interests:
                afternoon = "Spend time around museums and nearby café or design-oriented stops."
            elif "nature" in top_interests:
                afternoon = "Spend time in parks, gardens, or calmer open-air spaces."
            elif "shopping" in top_interests:
                afternoon = "Focus on shopping streets, boutiques, and stylish neighborhood browsing."
            else:
                afternoon = "Spend the afternoon in a neighborhood that matches your saved preferences."

            evening = (
                "End with a lively dinner and optional nightlife."
                if nightlife == "high"
                else "End with a comfortable dinner and relaxed evening."
            )

        itinerary.append(
            {
                "day": current_day,
                "title": title,
                "morning": morning,
                "afternoon": afternoon,
                "evening": evening,
                "meals": [
                    "Choose a breakfast or café stop that fits the saved meal rhythm.",
                    "Pick lunch and dinner aligned with dietary preferences and convenience level.",
                ],
                "notes": notes,
            }
        )

    return itinerary

router = APIRouter()


def build_trip_summary(payload: TripRequest) -> str:
    prefs = payload.preferences or {}
    profile = payload.traveler_profile or {}

    personality_label = profile.get("personality_label")
    personality_summary = profile.get("summary")

    top_interests = prefs.get("top_interests") or []
    dietary = prefs.get("dietary_preferences") or []
    allergies = prefs.get("allergies") or []
    accessibility = prefs.get("accessibility_needs") or []
    crowd_tolerance = prefs.get("crowd_tolerance")
    day_start = prefs.get("day_start_preference")
    neighborhood_style = prefs.get("neighborhood_style") or []
    transport_preferences = prefs.get("transport_preferences") or []
    meal_times = prefs.get("preferred_meal_times") or []
    budget = prefs.get("budget")
    pace = prefs.get("pace")
    structure = prefs.get("structure_preference")
    nightlife = prefs.get("nightlife_interest")
    shopping = prefs.get("shopping_interest")
    wellness = prefs.get("wellness_interest")
    photography = prefs.get("photography_interest")

    pieces: list[str] = []

    if personality_label:
        pieces.append(f"This itinerary is shaped for a {personality_label.lower()}.")

    if personality_summary:
        pieces.append(personality_summary)

    if top_interests:
        pieces.append(f"The plan leans into {', '.join(top_interests[:4])}.")

    if neighborhood_style:
        pieces.append(
            f"It favors areas that feel {', '.join(neighborhood_style[:3])}."
        )

    if dietary:
        pieces.append(
            f"Dining recommendations reflect {', '.join(dietary)} preferences."
        )

    if allergies:
        pieces.append(f"Food suggestions are mindful of {', '.join(allergies)}.")

    if accessibility:
        pieces.append(
            f"Mobility and comfort planning accounts for {', '.join(accessibility)}."
        )

    if crowd_tolerance == "low":
        pieces.append("Lower-crowd environments are prioritized where possible.")

    if day_start == "late":
        pieces.append("The schedule avoids overly early starts.")
    elif day_start == "early":
        pieces.append(
            "Earlier starts are used when they improve flow and crowd avoidance."
        )

    if transport_preferences:
        pieces.append(
            f"Getting around is shaped around {', '.join(transport_preferences[:3])}."
        )

    if meal_times:
        pieces.append(
            f"Meal pacing follows preferences like {', '.join(meal_times[:3])}."
        )

    if budget:
        pieces.append(f"The overall tone matches a {budget} budget.")

    if pace:
        pieces.append(f"Daily pacing is kept {pace}.")

    if structure:
        pieces.append(f"The trip structure is {structure}.")

    if nightlife == "high":
        pieces.append("Evenings include stronger nightlife potential.")
    if shopping == "high":
        pieces.append("Shopping opportunities are intentionally included.")
    if wellness == "high":
        pieces.append("Restorative and wellness-oriented moments are included.")
    if photography == "high":
        pieces.append("Photogenic stops and visual atmosphere are emphasized.")

    if payload.notes:
        pieces.append(f"Custom notes: {payload.notes}")

    if payload.must_see:
        pieces.append(
            f"Must-see priorities include {', '.join(payload.must_see[:5])}."
        )

    return " ".join(pieces) or f"A personalized itinerary for {payload.destination}."


def build_place_queries(payload: TripRequest) -> dict[str, str]:
    prefs = payload.preferences or {}
    dietary = prefs.get("dietary_preferences") or []
    neighborhood_style = prefs.get("neighborhood_style") or []
    top_interests = prefs.get("top_interests") or []

    food_phrase = "restaurants"
    if dietary:
        food_phrase = f"{' '.join(dietary)} restaurants"

    hotel_phrase = "boutique hotels"
    budget = prefs.get("budget")
    if budget == "budget":
        hotel_phrase = "budget hotels"
    elif budget == "luxury":
        hotel_phrase = "luxury hotels"
    elif budget == "premium":
        hotel_phrase = "premium hotels"

    highlight_phrase = "top attractions"
    if "architecture" in top_interests:
        highlight_phrase = "architecture landmarks"
    elif "museums" in top_interests:
        highlight_phrase = "best museums"
    elif "nature" in top_interests:
        highlight_phrase = "best parks and gardens"
    elif "shopping" in top_interests:
        highlight_phrase = "shopping districts and landmarks"
    elif "local culture" in top_interests:
        highlight_phrase = "cultural attractions and neighborhoods"

    neighborhood_phrase = "best neighborhoods"
    if neighborhood_style:
        neighborhood_phrase = f"{' '.join(neighborhood_style[:2])} neighborhoods"

    return {
        "restaurants": f"{food_phrase} in {payload.destination}",
        "hotels": f"{hotel_phrase} in {payload.destination}",
        "highlights": f"{highlight_phrase} in {payload.destination}",
        "neighborhoods": f"{neighborhood_phrase} in {payload.destination}",
    }


def build_restaurants_fallback(payload: TripRequest) -> list[dict]:
    prefs = payload.preferences or {}
    dietary = prefs.get("dietary_preferences") or []
    meal_style = prefs.get("meal_style")
    food_adventure = prefs.get("food_adventure_level")
    neighborhood_style = prefs.get("neighborhood_style") or []

    restaurants: list[dict] = []

    if dietary:
        restaurants.append(
            {
                "name": f"{payload.destination} dining for {', '.join(dietary)} preferences",
                "address": None,
                "rating": None,
                "types": ["restaurant"],
                "price_level": None,
                "summary": "Use this as a starting point for diet-friendly restaurant discovery.",
                "lat": None,
                "lng": None,
            }
        )

    if meal_style:
        restaurants.append(
            {
                "name": f"{meal_style.title()} dining in {payload.destination}",
                "address": None,
                "rating": None,
                "types": ["restaurant"],
                "price_level": None,
                "summary": "Suggested to match your preferred dining style.",
                "lat": None,
                "lng": None,
            }
        )

    if food_adventure == "high":
        restaurants.append(
            {
                "name": f"Adventurous local food experiences in {payload.destination}",
                "address": None,
                "rating": None,
                "types": ["restaurant", "food"],
                "price_level": None,
                "summary": "More exploratory dining ideas based on your profile.",
                "lat": None,
                "lng": None,
            }
        )
    elif food_adventure == "low":
        restaurants.append(
            {
                "name": f"Comfortable and approachable dining in {payload.destination}",
                "address": None,
                "rating": None,
                "types": ["restaurant"],
                "price_level": None,
                "summary": "Gentler food choices based on your comfort level.",
                "lat": None,
                "lng": None,
            }
        )

    if neighborhood_style:
        restaurants.append(
            {
                "name": f"Cafés and restaurants in {' / '.join(neighborhood_style[:2])}-style areas",
                "address": None,
                "rating": None,
                "types": ["cafe", "restaurant"],
                "price_level": None,
                "summary": "Dining ideas aligned with your preferred neighborhood vibe.",
                "lat": None,
                "lng": None,
            }
        )

    restaurants.append(
        {
            "name": f"Reliable neighborhood cafés in {payload.destination}",
            "address": None,
            "rating": None,
            "types": ["cafe"],
            "price_level": None,
            "summary": "Useful everyday stops for coffee, breakfast, or a casual reset.",
            "lat": None,
            "lng": None,
        }
    )

    return restaurants[:5]


def build_hotels_fallback(payload: TripRequest) -> list[dict]:
    prefs = payload.preferences or {}
    lodging = prefs.get("lodging_preference")
    budget = prefs.get("budget")

    summary_parts = []
    if lodging:
        summary_parts.append(lodging)
    if budget:
        summary_parts.append(budget)

    descriptor = " ".join(summary_parts).strip() or "well-located"

    return [
        {
            "name": f"{descriptor.title()} hotel options in {payload.destination}",
            "address": None,
            "rating": None,
            "types": ["lodging"],
            "price_level": None,
            "summary": "Hotel ideas matched to your saved lodging and budget preferences.",
            "lat": None,
            "lng": None,
        },
        {
            "name": f"Neighborhood-based stays in {payload.destination}",
            "address": None,
            "rating": None,
            "types": ["lodging"],
            "price_level": None,
            "summary": "Useful for choosing an area that fits your vibe and transit preferences.",
            "lat": None,
            "lng": None,
        },
    ]


def build_highlights_fallback(payload: TripRequest) -> list[dict]:
    prefs = payload.preferences or {}
    top_interests = prefs.get("top_interests") or []

    highlights: list[dict] = []

    if "architecture" in top_interests:
        highlights.append(
            {
                "name": f"Architectural highlights in {payload.destination}",
                "address": None,
                "rating": None,
                "types": ["tourist_attraction", "point_of_interest"],
                "price_level": None,
                "summary": "Focus on visually striking buildings, districts, and design-forward areas.",
                "lat": None,
                "lng": None,
            }
        )

    if "museums" in top_interests:
        highlights.append(
            {
                "name": f"Museum picks in {payload.destination}",
                "address": None,
                "rating": None,
                "types": ["museum", "point_of_interest"],
                "price_level": None,
                "summary": "Suggested museum-oriented stops based on your interests.",
                "lat": None,
                "lng": None,
            }
        )

    if "nature" in top_interests:
        highlights.append(
            {
                "name": f"Parks and gardens in {payload.destination}",
                "address": None,
                "rating": None,
                "types": ["park", "point_of_interest"],
                "price_level": None,
                "summary": "Green spaces that suit a calmer or more restorative rhythm.",
                "lat": None,
                "lng": None,
            }
        )

    if "shopping" in top_interests:
        highlights.append(
            {
                "name": f"Shopping areas in {payload.destination}",
                "address": None,
                "rating": None,
                "types": ["shopping_mall", "point_of_interest"],
                "price_level": None,
                "summary": "Retail-oriented areas matched to your profile.",
                "lat": None,
                "lng": None,
            }
        )

    if not highlights:
        highlights.append(
            {
                "name": f"Signature highlights in {payload.destination}",
                "address": None,
                "rating": None,
                "types": ["tourist_attraction", "point_of_interest"],
                "price_level": None,
                "summary": "A general starting point for major sights and experiences.",
                "lat": None,
                "lng": None,
            }
        )

    return highlights[:6]


def build_neighborhoods_fallback(payload: TripRequest) -> list[str]:
    prefs = payload.preferences or {}
    neighborhood_style = prefs.get("neighborhood_style") or []
    top_interests = prefs.get("top_interests") or []

    neighborhoods: list[str] = []

    if neighborhood_style:
        neighborhoods.extend(neighborhood_style[:3])

    if not neighborhoods and top_interests:
        neighborhoods.extend(top_interests[:3])

    if not neighborhoods:
        neighborhoods = [
            "walkable central district",
            "quiet local neighborhood",
            "food-focused area",
        ]

    return neighborhoods[:4]


def build_mock_itinerary(payload: TripRequest) -> list[dict]:
    prefs = payload.preferences or {}

    dietary = prefs.get("dietary_preferences") or []
    allergies = prefs.get("allergies") or []
    accessibility = prefs.get("accessibility_needs") or []
    meal_times = prefs.get("preferred_meal_times") or []
    neighborhood_style = prefs.get("neighborhood_style") or []
    top_interests = prefs.get("top_interests") or []
    crowd_tolerance = prefs.get("crowd_tolerance")
    day_start = prefs.get("day_start_preference")
    nightlife = prefs.get("nightlife_interest")
    shopping = prefs.get("shopping_interest")
    wellness = prefs.get("wellness_interest")
    photography = prefs.get("photography_interest")
    transport = prefs.get("transport_preferences") or []

    day1_notes: list[str] = []
    day2_notes: list[str] = []

    if dietary:
        day1_notes.append(f"Prioritize dining options that support {', '.join(dietary)}.")
    if allergies:
        day1_notes.append(f"Avoid recommendations with {', '.join(allergies)}.")
    if accessibility:
        day1_notes.append(f"Keep logistics aligned with {', '.join(accessibility)}.")
    if crowd_tolerance == "low":
        day1_notes.append("Favor quieter time windows and less crowded stops.")
    if transport:
        day1_notes.append(f"Prefer movement by {', '.join(transport[:3])}.")

    if neighborhood_style:
        day2_notes.append(
            f"Spend more time in areas that feel {', '.join(neighborhood_style[:2])}."
        )
    if meal_times:
        day2_notes.append(f"Anchor food stops around {', '.join(meal_times[:3])}.")
    if photography == "high":
        day2_notes.append("Include visually strong and photogenic locations.")
    if shopping == "high":
        day2_notes.append("Include dedicated browsing or shopping time.")
    if wellness == "high":
        day2_notes.append("Protect time for calmer, restorative experiences.")

    morning_one = (
        "Begin with a slower start and an easy breakfast nearby."
        if day_start == "late"
        else "Start with a smooth orientation walk and an easy first stop."
    )

    evening_two = (
        "End with a lively dinner and optional nightlife."
        if nightlife == "high"
        else "End with a comfortable dinner and relaxed evening."
    )

    afternoon_two = (
        "Explore a culturally rich district with food, design, and local atmosphere."
        if "local culture" in top_interests or "architecture" in top_interests
        else "Spend the afternoon in a neighborhood that matches your saved preferences."
    )

    return [
        {
            "day": 1,
            "title": f"Arrival and easy orientation in {payload.destination}",
            "morning": morning_one,
            "afternoon": "Explore one manageable neighborhood with low-friction logistics and a good food anchor.",
            "evening": "Settle into a dinner plan that matches your comfort, pace, and dietary needs.",
            "meals": [
                "Choose a breakfast or café stop that fits the saved meal rhythm.",
                "Pick a dinner aligned with dietary preferences and convenience level.",
            ],
            "notes": day1_notes,
        },
        {
            "day": 2,
            "title": "Neighborhood discovery and signature experiences",
            "morning": "Start with coffee, breakfast, or a gentle local walk depending on preferred pace.",
            "afternoon": afternoon_two,
            "evening": evening_two,
            "meals": [
                "Lunch in a neighborhood spot with strong local character.",
                "Dinner selected for atmosphere, fit, and ease of access.",
            ],
            "notes": day2_notes,
        },
    ]


def safe_search_places(query: str, limit: int) -> list[dict]:
    print(f"[PLACES] query={query} limit={limit}")
    try:
        results = search_places(query, limit=limit)
        print(f"[PLACES] returned {len(results)} results")
        if results:
            print(f"[PLACES] first result: {results[0]}")
        return results
    except Exception as exc:
        print(f"[PLACES] FAILED for query '{query}': {exc}")
        return []


def safe_get_weather(destination: str) -> dict | None:
    print(f"[WEATHER] destination={destination}")
    try:
        result = get_weather_for_destination(destination)
        print(f"[WEATHER] result={result}")
        return result
    except Exception as exc:
        print(f"[WEATHER] FAILED for destination '{destination}': {exc}")
        return None


@router.post("/generate", response_model=TripResponse)
def generate_trip(payload: TripRequest) -> TripResponse:
    queries = build_place_queries(payload)

    restaurants = safe_search_places(queries["restaurants"], limit=5)
    hotels = safe_search_places(queries["hotels"], limit=5)
    highlights = safe_search_places(queries["highlights"], limit=6)
    neighborhood_results = safe_search_places(queries["neighborhoods"], limit=4)
    weather = safe_get_weather(payload.destination)

    if not restaurants:
        restaurants = build_restaurants_fallback(payload)

    if not hotels:
        hotels = build_hotels_fallback(payload)

    if not highlights:
        highlights = build_highlights_fallback(payload)

    neighborhoods = [
        item["name"] for item in neighborhood_results if item.get("name")
    ]
    if not neighborhoods:
        neighborhoods = build_neighborhoods_fallback(payload)

    map_points: list[dict] = []
    for category, items in [
        ("restaurant", restaurants),
        ("hotel", hotels),
        ("highlight", highlights),
    ]:
        for item in items:
            if item.get("lat") is not None and item.get("lng") is not None:
                map_points.append(
                    {
                        "name": item["name"],
                        "category": category,
                        "lat": item["lat"],
                        "lng": item["lng"],
                    }
                )

    return TripResponse(
        destination=payload.destination,
        summary=build_trip_summary(payload),
        weather=weather,
        neighborhoods=neighborhoods,
        restaurants=restaurants,
        hotels=hotels,
        highlights=highlights,
        map_points=map_points,
        itinerary=build_dynamic_itinerary(payload),
        tips=[
            "Cluster activities by neighborhood to reduce transit friction.",
            "Use saved dietary and allergy signals before locking restaurant choices.",
            "Match reservation timing to the saved day-start and meal-rhythm preferences.",
            "Use quieter time windows for major sights if crowd tolerance is low.",
        ],
    )