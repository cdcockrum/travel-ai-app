from typing import Any
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

    nightlife_interest: str | None = None
    shopping_interest: str | None = None
    wellness_interest: str | None = None
    photography_interest: str | None = None
    weather_tolerance: str | None = None
    social_energy: str | None = None
    seat_of_pants_factor: str | None = None
    neighborhood_style: list[str] = []
    preferred_meal_times: list[str] = []
    transport_preferences: list[str] = []


class QuizResult(BaseModel):
    profile_id: str
    personality_label: str
    summary: str
    scores: dict[str, int]


class TripRequest(BaseModel):
    destination: str
    start_date: str
    end_date: str
    notes: str | None = None
    must_see: list[str] = []
    traveler_profile: dict[str, Any] = {}
    preferences: dict[str, Any] = {}


class ItineraryDay(BaseModel):
    day: int
    title: str | None = None
    morning: str | None = None
    afternoon: str | None = None
    evening: str | None = None
    meals: list[str] = []
    notes: list[str] = []


class WeatherSummary(BaseModel):
    description: str | None = None
    temperature_c: float | None = None
    feels_like_c: float | None = None
    humidity: int | None = None


class PlaceCard(BaseModel):
    name: str
    address: str | None = None
    rating: float | None = None
    types: list[str] = []
    price_level: int | None = None
    summary: str | None = None
    lat: float | None = None
    lng: float | None = None


class MapPoint(BaseModel):
    name: str
    category: str
    lat: float
    lng: float


class ItineraryDay(BaseModel):
    day: int
    title: str | None = None
    morning: str | None = None
    afternoon: str | None = None
    evening: str | None = None
    meals: list[str] = []
    notes: list[str] = []


class TripRequest(BaseModel):
    destination: str
    start_date: str
    end_date: str
    notes: str | None = None
    must_see: list[str] = []
    traveler_profile: dict[str, Any] = {}
    preferences: dict[str, Any] = {}


class TripResponse(BaseModel):
    destination: str
    summary: str
    weather: WeatherSummary | None = None
    neighborhoods: list[str] = []
    restaurants: list[PlaceCard] = []
    hotels: list[PlaceCard] = []
    highlights: list[PlaceCard] = []
    map_points: list[MapPoint] = []
    itinerary: list[ItineraryDay] = []
    tips: list[str] = []