"""
WeatherTool — uses Open-Meteo (no API key needed!)
Supports city name lookup via geocoding API.
"""
import time
import requests

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

_cache: dict = {}
CACHE_TTL = 600

def _get(url: str, params: dict) -> dict:
    cache_key = url + str(sorted(params.items()))
    if cache_key in _cache:
        ts, data = _cache[cache_key]
        if time.time() - ts < CACHE_TTL:
            return data
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    _cache[cache_key] = (time.time(), data)
    return data

def _get_coords(city: str) -> tuple:
    data = _get(GEO_URL, {"name": city, "count": 1, "language": "en", "format": "json"})
    results = data.get("results", [])
    if not results:
        raise ValueError(f"City '{city}' not found.")
    r = results[0]
    return r["latitude"], r["longitude"], r["name"], r.get("country", "")

WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy fog", 51: "Light drizzle", 61: "Slight rain",
    63: "Moderate rain", 65: "Heavy rain", 71: "Slight snow", 80: "Rain showers",
    95: "Thunderstorm",
}

def get_weather(city: str, units: str = "metric") -> dict:
    lat, lon, name, country = _get_coords(city)
    temp_unit = "celsius" if units == "metric" else "fahrenheit"
    data = _get(WEATHER_URL, {
        "latitude": lat, "longitude": lon,
        "current_weather": "true",
        "temperature_unit": temp_unit,
    })
    cw = data["current_weather"]
    unit_sym = "°C" if units == "metric" else "°F"
    return {
        "city": name, "country": country,
        "temperature": f"{cw['temperature']}{unit_sym}",
        "condition": WEATHER_CODES.get(cw["weathercode"], "Unknown"),
        "wind_speed": f"{cw['windspeed']} km/h",
    }

def get_forecast(city: str, days: int = 3, units: str = "metric") -> list:
    lat, lon, name, country = _get_coords(city)
    temp_unit = "celsius" if units == "metric" else "fahrenheit"
    data = _get(WEATHER_URL, {
        "latitude": lat, "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,weathercode",
        "temperature_unit": temp_unit,
        "timezone": "auto", "forecast_days": days,
    })
    unit_sym = "°C" if units == "metric" else "°F"
    daily = data.get("daily", {})
    result = []
    for i in range(min(days, len(daily.get("time", [])))):
        result.append({
            "date": daily["time"][i],
            "max_temp": f"{daily['temperature_2m_max'][i]}{unit_sym}",
            "min_temp": f"{daily['temperature_2m_min'][i]}{unit_sym}",
            "condition": WEATHER_CODES.get(daily["weathercode"][i], "Unknown"),
        })
    return result

def run(action: str, **kwargs) -> dict:
    actions = {"get_weather": get_weather, "get_forecast": get_forecast}
    if action not in actions:
        raise ValueError(f"WeatherTool: unknown action '{action}'")
    return actions[action](**kwargs)