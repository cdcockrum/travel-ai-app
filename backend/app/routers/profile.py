from fastapi import APIRouter

from app.schemas import QuizResult, QuizSubmission
from app.services.personality import compute_personality_profile

router = APIRouter()


@router.post("/quiz", response_model=QuizResult)
def submit_quiz(payload: QuizSubmission) -> dict:
    return compute_personality_profile(payload.model_dump())


@router.get("/me")
def get_profile() -> dict:
    return {
        "profile_id": "demo-profile-id",
        "personality_label": "Balanced Discoverer",
        "summary": "You enjoy a thoughtful mix of culture, food, and iconic experiences without overpacking your days.",
        "scores": {
            "food": 8,
            "culture": 9,
            "architecture": 8,
            "pace": 6,
            "hidden_gems": 7,
        },
    }