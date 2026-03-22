import os

import requests

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GEOCODE_URL = "https://api.openweathermap.org/geo/1.0/direct"
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

print("OPENWEATHER_API_KEY loaded:", bool(OPENWEATHER_API_KEY))


def get_weather_for_destination(destination: str) -> dict | None:
    if not OPENWEATHER_API_KEY:
        return None

    geo = requests.get(
        GEOCODE_URL,
        params={
            "q": destination,
            "limit": 1,
            "appid": OPENWEATHER_API_KEY,
        },
        timeout=20,
    )
    geo.raise_for_status()
    geo_data = geo.json()

    print("WEATHER GEO JSON:", geo_data)

    if not geo_data:
        return None

    lat = geo_data[0]["lat"]
    lon = geo_data[0]["lon"]

    weather = requests.get(
        WEATHER_URL,
        params={
            "lat": lat,
            "lon": lon,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric",
        },
        timeout=20,
    )
    weather.raise_for_status()
    data = weather.json()

    print("WEATHER RAW JSON:", data)

    return {
        "description": data["weather"][0]["description"] if data.get("weather") else None,
        "temperature_c": data["main"].get("temp") if data.get("main") else None,
        "feels_like_c": data["main"].get("feels_like") if data.get("main") else None,
        "humidity": data["main"].get("humidity") if data.get("main") else None,
    }