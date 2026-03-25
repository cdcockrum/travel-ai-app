from dotenv import load_dotenv
load_dotenv()


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.profile import router as profile_router
from app.routers.itinerary import router as itinerary_router
from app.routers.advisory import router as advisory_router
from app.routers.itinerary import router as itinerary_router


app = FastAPI(title="Travel AI App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.1.165:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile_router, prefix="/api/profile", tags=["profile"])
app.include_router(itinerary_router, prefix="/api/trips", tags=["trips"])
app.include_router(advisory_router, prefix="/api/advisory", tags=["advisory"])
app.include_router(itinerary_router, prefix="/api/itinerary", tags=["itinerary"])

@app.get("/health")
def health_check():
    return {"status": "ok"}