from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.trips import router as trips_router
from app.routers.itinerary import router as itinerary_router  # ❌ problematic

app = FastAPI(title="Travel AI App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trips_router, prefix="/api/trips", tags=["trips"])
app.include_router(itinerary_router, prefix="/api/itinerary", tags=["itinerary"])  # ❌ problematic


@app.get("/")
def root():
    return {"message": "Travel AI backend is running"}