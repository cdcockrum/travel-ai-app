from fastapi import APIRouter
from app.services.weather_service import get_weather_forecast

router = APIRouter()


@router.get("/{city}/{country}")
def weather(city: str, country: str):
    forecast = get_weather_forecast(city, country)

    return {
        "city": city,
        "country": country,
        "forecast": forecast,
    }