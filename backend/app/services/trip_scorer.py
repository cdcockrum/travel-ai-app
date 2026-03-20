def score_itinerary(itinerary: dict) -> dict:
    summary = itinerary.get("trip_summary", "").lower()

    score = 88
    strengths = [
        "Good pacing",
        "Strong neighborhood focus",
        "Aligned with food and culture interests",
    ]
    weaknesses = [
        "Could use one more flexible block in the middle of the trip"
    ]
    improvements = [
        "Add optional downtime or a short cafe break on the busiest day"
    ]

    if "food experiences" in summary:
        strengths.append("Good alignment with food-driven travel preferences")

    if "architecture" in summary or "culture" in summary:
        strengths.append("Strong cultural positioning")

    if "moderate" in summary:
        strengths.append("Pacing is well matched to a balanced traveler")

    return {
        "score": score,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "improvements": improvements,
    }