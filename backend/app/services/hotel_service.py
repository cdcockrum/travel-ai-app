from typing import Any


def _score_hotel(hotel: dict[str, Any], notes: str, budget_level: str) -> int:
    notes = (notes or "").lower()
    budget_level = (budget_level or "moderate").lower()

    score = 0
    name = hotel["name"].lower()
    area = hotel["area"].lower()
    style = hotel["style"].lower()
    price_band = hotel["price_band"].lower()

    if "food" in notes and ("market" in area or "central" in area or "trendy" in area):
        score += 3
    if "culture" in notes or "architecture" in notes:
        if "cultural" in area or "design" in style or "boutique" in style:
            score += 3
    if "relaxed" in notes or "balanced" in notes:
        if "walkable" in area or "boutique" in style:
            score += 2
    if "packed" in notes or "high-energy" in notes:
        if "central" in area or "prestige" in area:
            score += 2
    if budget_level == "luxury" and price_band == "luxury":
        score += 3
    if budget_level == "premium" and price_band in ["premium", "moderate"]:
        score += 2
    if budget_level == "budget" and price_band == "moderate":
        score += 1
    if "authentic" in notes or "local culture" in notes:
        if "local" in name or "boutique" in style:
            score += 2

    return score


def get_hotel_recommendations(
    city: str,
    country: str,
    notes: str = "",
    budget_level: str = "moderate",
) -> list[dict[str, Any]]:
    notes = (notes or "").lower()
    budget = (budget_level or "moderate").lower()

    base_hotels = [
        {
            "id": f"{city.lower()}-central-boutique",
            "name": f"{city} Central Boutique Hotel",
            "area": "Central walkable district",
            "style": "Boutique",
            "price_band": "Moderate",
            "why": "Great balance of location, walkability, and local character.",
        },
        {
            "id": f"{city.lower()}-design-house",
            "name": f"{city} Design House",
            "area": "Trendy neighborhood",
            "style": "Design-forward hotel",
            "price_band": "Premium",
            "why": "Ideal for travelers who enjoy aesthetics and neighborhood culture.",
        },
        {
            "id": f"{city.lower()}-grand",
            "name": f"The Grand {city}",
            "area": "Prestige central district",
            "style": "Luxury hotel",
            "price_band": "Luxury",
            "why": "High-end comfort with excellent service and central access.",
        },
        {
            "id": f"{city.lower()}-local-stay",
            "name": f"{city} Local Stay",
            "area": "Cultural district",
            "style": "Local boutique stay",
            "price_band": "Moderate",
            "why": "Best for experiencing local life and cultural surroundings.",
        },
    ]

    if budget == "budget":
        filtered = [h for h in base_hotels if h["price_band"] in ["Moderate"]]
    elif budget == "luxury":
        filtered = [h for h in base_hotels if h["price_band"] in ["Luxury", "Premium"]]
    elif budget == "premium":
        filtered = [h for h in base_hotels if h["price_band"] in ["Premium", "Moderate"]]
    else:
        filtered = base_hotels

    enhanced = []
    for h in filtered:
        hotel = h.copy()

        if "food" in notes:
            hotel["why"] += " Strong access to restaurants and food neighborhoods."
        if "culture" in notes or "architecture" in notes:
            if "cultural" in hotel["area"].lower() or "design" in hotel["style"].lower():
                hotel["why"] += " Strong fit for museums, architecture, and local texture."
        if "balanced" in notes or "relaxed" in notes:
            hotel["why"] += " Well suited to a moderate, non-rushed trip."
        if "packed" in notes:
            hotel["why"] += " Useful as an efficient base for fuller sightseeing days."

        enhanced.append(hotel)

    ranked = sorted(
        enhanced,
        key=lambda h: _score_hotel(h, notes, budget),
        reverse=True,
    )

    return ranked[:3]