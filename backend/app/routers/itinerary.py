from fastapi import APIRouter

from app.schemas import ItineraryGenerateRequest
from app.services.itinerary_generator import generate_itinerary
from app.services.trip_scorer import score_itinerary

router = APIRouter()


@router.post("/generate")
def generate(payload: ItineraryGenerateRequest) -> dict:
    itinerary = generate_itinerary(payload.trip_id)
    score = score_itinerary(itinerary)
    return {"trip_id": payload.trip_id, **itinerary, **score}


@router.post("/regenerate")
def regenerate(payload: ItineraryGenerateRequest) -> dict:
    itinerary = generate_itinerary(payload.trip_id)
    score = score_itinerary(itinerary)
    return {"trip_id": payload.trip_id, **itinerary, **score}