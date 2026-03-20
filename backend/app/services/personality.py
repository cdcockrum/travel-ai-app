def compute_personality_profile(data: dict) -> dict:
    interests = set(data.get("top_interests", []))
    pace = data.get("pace_level", "balanced")
    dietary_preferences = set(data.get("dietary_preferences", []))
    accessibility_needs = set(data.get("accessibility_needs", []))
    crowd_tolerance = data.get("crowd_tolerance", "moderate")
    day_start_preference = data.get("day_start_preference", "mid-morning")

    if {"food", "architecture", "local culture"}.intersection(interests):
        label = "Balanced Discoverer"
        summary = (
            "You enjoy a thoughtful mix of culture, food, and iconic experiences "
            "without overpacking your days."
        )
    elif "nature" in interests:
        label = "Nature Seeker"
        summary = "You prefer scenic, restorative experiences with room to breathe."
    else:
        label = "Curious Traveler"
        summary = "You enjoy a balanced trip with room for discovery."

    if dietary_preferences:
        summary += f" Your trip should also respect dietary needs such as {', '.join(dietary_preferences)}."

    if accessibility_needs:
        summary += f" Accessibility and comfort considerations include {', '.join(accessibility_needs)}."

    if crowd_tolerance == "low":
        summary += " Lower-crowd environments are likely to be a better fit for you."

    if day_start_preference == "late":
        summary += " Your ideal days begin later and should avoid overly early starts."

    scores = {
        "food": 8 if "food" in interests else 4,
        "culture": 9 if "local culture" in interests else 5,
        "architecture": 8 if "architecture" in interests else 4,
        "nature": 8 if "nature" in interests else 3,
        "pace": 6 if pace == "balanced" else (3 if pace == "relaxed" else 8),
        "hidden_gems": 7 if data.get("structure_preference") != "fully planned" else 4,
        "dietary_complexity": 8 if dietary_preferences else 2,
        "accessibility_support": 8 if accessibility_needs else 2,
        "crowd_sensitivity": 8 if crowd_tolerance == "low" else (5 if crowd_tolerance == "moderate" else 2),
        "late_start_preference": 8 if day_start_preference == "late" else 3,
    }

    return {
        "profile_id": "demo-profile-id",
        "personality_label": label,
        "summary": summary,
        "scores": scores,
    }