import os
import requests
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

OWM_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
BASE_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

mcp = FastMCP("OpenWeather MCP")


def _call_api(url, params) -> dict:
    params = params.copy()
    params.setdefault("APPID", OWM_API_KEY)
    try:
        resp = requests.get(url, params=params, timeout=10)
    except requests.RequestException as exc:
        return {"error": {"type": "request", "message": str(exc)}}

    if not resp.ok:
        return {
            "error": {
                "type": "http",
                "status": resp.status_code,
                "message": resp.text,
            }
        }

    try:
        return resp.json()
    except ValueError:
        return {"error": {"type": "parse", "message": "Invalid JSON response"}}


@mcp.tool(description="Get current weather for a city. Returns temperature, humidity, description, wind, sunrise/sunset.")
def get_current_weather(city, units) -> dict:
    params = {"q": city, "units": units}
    data = _call_api(BASE_WEATHER_URL, params)

    if "error" in data:
        return data

    main = data.get("main", {})
    weather = (data.get("weather") or [{}])[0]
    wind = data.get("wind", {})
    sys = data.get("sys", {})

    return {
        "city": data.get("name"),
        "country": sys.get("country"),
        "coord": data.get("coord"),
        "dt": data.get("dt"),
        "timezone": data.get("timezone"),
        "temperature": main.get("temp"),
        "feels_like": main.get("feels_like"),
        "temp_min": main.get("temp_min"),
        "temp_max": main.get("temp_max"),
        "pressure": main.get("pressure"),
        "humidity": main.get("humidity"),
        "weather": weather.get("description"),
        "weather_main": weather.get("main"),
        "wind_speed": wind.get("speed"),
        "wind_deg": wind.get("deg"),
        "sunrise": sys.get("sunrise"),
        "sunset": sys.get("sunset"),
        "raw": data,
    }

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8002)
