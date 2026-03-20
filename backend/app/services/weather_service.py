import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")


def get_weather_forecast(city: str, country: str):
    if not API_KEY:
        raise ValueError("Missing OPENWEATHER_API_KEY")

    query = f"{city},{country}"

    url = "https://api.openweathermap.org/data/2.5/forecast"

    response = requests.get(
        url,
        params={
            "q": query,
            "appid": API_KEY,
            "units": "metric",
        },
        timeout=10,
    )

    if not response.ok:
        raise ValueError(f"Weather API error: {response.text}")

    data = response.json()

    daily = {}

    for item in data["list"]:
        date_str = item["dt_txt"].split(" ")[0]

        if date_str not in daily:
            daily[date_str] = {
                "temps": [],
                "conditions": [],
            }

        daily[date_str]["temps"].append(item["main"]["temp"])
        daily[date_str]["conditions"].append(item["weather"][0]["main"])

    result = []

    for date, info in daily.items():
        avg_temp = sum(info["temps"]) / len(info["temps"])
        condition = max(set(info["conditions"]), key=info["conditions"].count)

        result.append(
            {
                "date": date,
                "avg_temp": round(avg_temp, 1),
                "condition": condition,
            }
        )

    return result[:5]