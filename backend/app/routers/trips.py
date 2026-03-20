import uuid

from fastapi import APIRouter

from app.schemas import TripCreate, TripResponse
from app.services.trip_store import get_trip as get_trip_from_store
from app.services.trip_store import list_all_trips, save_trip

router = APIRouter()


@router.post("", response_model=TripResponse)
def create_trip(payload: TripCreate) -> dict:
    trip_id = str(uuid.uuid4())

    trip_data = {
        "id": trip_id,
        "title": payload.title,
        "destination_city": payload.destination_city,
        "destination_country": payload.destination_country,
        "start_date": payload.start_date.isoformat(),
        "end_date": payload.end_date.isoformat(),
        "budget_level": payload.budget_level,
        "must_do_items": payload.must_do_items,
        "avoid_items": payload.avoid_items,
        "notes": payload.notes,
        "profile": getattr(payload, "profile", None),
        "status": "draft",
    }

    save_trip(trip_id, trip_data)

    return {
        "trip_id": trip_id,
        "status": "draft",
        "trip": trip_data,
    }


@router.get("")
def list_trips() -> dict:
    return {"trips": list_all_trips()}


@router.get("/{trip_id}")
def get_trip(trip_id: str) -> dict:
    trip = get_trip_from_store(trip_id)
    if trip:
        return trip
    return {"detail": "Trip not found"}