from fastapi import APIRouter

from app.schemas import TripRequest, TripResponse

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

    pieces = []

    if personality_label:
        pieces.append(f"This itinerary is shaped for a {personality_label.lower()}.")

    if personality_summary:
        pieces.append(personality_summary)

    if top_interests:
        pieces.append(
            f"The plan leans into {', '.join(top_interests[:4])}."
        )

    if neighborhood_style:
        pieces.append(
            f"It favors areas that feel {', '.join(neighborhood_style[:3])}."
        )

    if dietary:
        pieces.append(
          f"Dining recommendations reflect {', '.join(dietary)} preferences."
        )

    if allergies:
        pieces.append(
          f"Food suggestions are mindful of {', '.join(allergies)}."
        )

    if accessibility:
        pieces.append(
          f"Mobility and comfort planning accounts for {', '.join(accessibility)}."
        )

    if crowd_tolerance == "low":
        pieces.append("Lower-crowd environments are prioritized where possible.")

    if day_start == "late":
        pieces.append("The schedule avoids overly early starts.")
    elif day_start == "early":
        pieces.append("Earlier starts are used when they improve flow and crowd avoidance.")

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
        pieces.append(f"Must-see priorities include {', '.join(payload.must_see[:5])}.")

    return " ".join(pieces) or f"A personalized itinerary for {payload.destination}."


def build_restaurants(payload: TripRequest) -> list[str]:
    prefs = payload.preferences or {}
    dietary = prefs.get("dietary_preferences") or []
    meal_style = prefs.get("meal_style")
    food_adventure = prefs.get("food_adventure_level")
    neighborhood_style = prefs.get("neighborhood_style") or []

    restaurants = []

    if dietary:
        restaurants.append(
            f"{payload.destination} restaurants suited to {', '.join(dietary)} dining"
        )

    if meal_style:
        restaurants.append(
            f"{meal_style.title()} dining options in {payload.destination}"
        )

    if food_adventure == "high":
        restaurants.append(
            f"More adventurous local food experiences in {payload.destination}"
        )
    elif food_adventure == "low":
        restaurants.append(
            f"Comfortable and approachable dining in {payload.destination}"
        )

    if neighborhood_style:
        restaurants.append(
            f"Cafés and restaurants in {', '.join(neighborhood_style[:2])}-style neighborhoods"
        )

    restaurants.append(f"Reliable neighborhood cafés in {payload.destination}")

    return restaurants[:5]


def build_neighborhoods(payload: TripRequest) -> list[str]:
    prefs = payload.preferences or {}
    neighborhood_style = prefs.get("neighborhood_style") or []
    top_interests = prefs.get("top_interests") or []

    neighborhoods = []

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

    day1_notes = []
    day2_notes = []

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
        day2_notes.append(
            f"Anchor food stops around {', '.join(meal_times[:3])}."
        )
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


@router.post("/generate", response_model=TripResponse)
def generate_trip(payload: TripRequest) -> TripResponse:
    return TripResponse(
        destination=payload.destination,
        summary=build_trip_summary(payload),
        itinerary=build_mock_itinerary(payload),
        tips=[
            "Cluster activities by neighborhood to reduce transit friction.",
            "Use saved dietary and allergy signals before locking restaurant choices.",
            "Match reservation timing to the saved day-start and meal-rhythm preferences.",
            "Use quieter time windows for major sights if crowd tolerance is low.",
        ],
        restaurants=build_restaurants(payload),
        neighborhoods=build_neighborhoods(payload),
    )