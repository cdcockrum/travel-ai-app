from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    advisory,
    auth,
    itinerary,
    profile,
    recommendations,
    trips,
    weather,
)
from app.services.trip_store import init_db

app = FastAPI(title="Travel Advisory App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    init_db()


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(trips.router, prefix="/api/trips", tags=["trips"])
app.include_router(itinerary.router, prefix="/api/itinerary", tags=["itinerary"])
app.include_router(advisory.router, prefix="/api/advisory", tags=["advisory"])
app.include_router(
    recommendations.router,
    prefix="/api/recommendations",
    tags=["recommendations"],
)
app.include_router(weather.router, prefix="/api/weather", tags=["weather"])


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/intelligence/{city}")
def intelligence(city: str) -> dict:
    return {
        "city": city,
        "best_times": "Morning and late evening",
        "crowds": "High in central districts midday",
        "tip": "Explore side streets for better food options",
    }