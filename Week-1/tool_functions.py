def calculator(expression: str) -> str:
    try:
        # eval is fine here since it's your own local tool, not exposed to untrusted input
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as e:
        return f"Error: {e}"

def get_weather(city: str) -> str:
    # Mocked for now — swap in a real API (e.g. Open-Meteo, free, no key needed) later
    fake_data = {"tokyo": "24°C, clear", "san francisco": "16°C, foggy", "new york": "28°C, sunny"}
    return fake_data.get(city.lower(), f"No data for {city}")

import requests

def get_live_weather(city: str) -> str:
    # Step 1: geocode the city name to lat/lon
    geo_resp = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1}
    )
    geo_data = geo_resp.json()

    if "results" not in geo_data or len(geo_data["results"]) == 0:
        return f"Could not find location: {city}"

    location = geo_data["results"][0]
    lat, lon = location["latitude"], location["longitude"]
    resolved_name = location["name"]
    country = location.get("country", "")

    # Step 2: fetch current weather for those coordinates
    weather_resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,weather_code,wind_speed_10m"
        }
    )
    weather_data = weather_resp.json()
    current = weather_data["current"]

    temp = current["temperature_2m"]
    wind = current["wind_speed_10m"]
    code = current["weather_code"]

    condition = weather_code_to_text(code)

    return f"{resolved_name}, {country}: {temp}°C, {condition}, wind {wind} km/h"


def weather_code_to_text(code: int) -> str:
    # Open-Meteo uses WMO weather codes — this is a simplified mapping
    mapping = {
        0: "clear sky",
        1: "mainly clear", 2: "partly cloudy", 3: "overcast",
        45: "fog", 48: "depositing rime fog",
        51: "light drizzle", 53: "moderate drizzle", 55: "dense drizzle",
        61: "slight rain", 63: "moderate rain", 65: "heavy rain",
        71: "slight snow", 73: "moderate snow", 75: "heavy snow",
        80: "rain showers", 81: "moderate rain showers", 82: "violent rain showers",
        95: "thunderstorm",
    }
    return mapping.get(code, f"unknown conditions (code {code})")

# Dispatch table — maps tool name to the real function
tool_functions = {"calculator": calculator, "get_weather": get_weather, "get_live_weather": get_live_weather}