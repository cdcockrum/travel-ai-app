from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, Field


class QuizSubmission(BaseModel):
    pace_level: str
    budget_level: str
    travel_party: str
    walking_tolerance: str
    top_interests: list[str]
    food_adventure_level: str
    lodging_preference: str
    convenience_vs_authenticity: int = Field(ge=1, le=5)
    structure_preference: str
    transit_confidence: str
    deal_breakers: list[str]
    meal_style: str
    trip_values: list[str]

    dietary_preferences: list[str] = []
    allergies: list[str] = []
    accessibility_needs: list[str] = []
    crowd_tolerance: str = "moderate"
    day_start_preference: str = "mid-morning"


class QuizResult(BaseModel):
    profile_id: str
    personality_label: str
    summary: str
    scores: dict[str, int]


class TripCreate(BaseModel):
    title: Optional[str] = None
    destination_city: str
    destination_country: str
    start_date: date
    end_date: date
    budget_level: str
    must_do_items: list[str] = []
    avoid_items: list[str] = []
    notes: Optional[str] = None
    profile: Optional[dict[str, Any]] = None


class TripResponse(BaseModel):
    trip_id: str
    status: str
    trip: dict


class ItineraryGenerateRequest(BaseModel):
    trip_id: str


class AdvisoryCreate(BaseModel):
    trip_id: str
    service_type: str
    notes: Optional[str] = None