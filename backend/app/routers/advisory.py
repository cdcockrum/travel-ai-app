from fastapi import APIRouter

from app.schemas import AdvisoryCreate

router = APIRouter()


@router.post("")
def create_advisory_request(payload: AdvisoryCreate) -> dict:
    return {
        "request_id": "demo-request-id",
        "status": "new",
        "service_type": payload.service_type,
        "notes": payload.notes,
    }