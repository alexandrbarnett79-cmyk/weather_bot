from __future__ import annotations

import logging
from datetime import datetime, timezone as _tz
import aiohttp
from dataclasses import dataclass, field
from bot.config import OWM_API_KEY, OWM_CURRENT_URL, OWM_FORECAST_URL, OWM_GEOCODE_URL, OWM_REVERSE_GEOCODE_URL

logger = logging.getLogger(__name__)

_TIMEOUT = aiohttp.ClientTimeout(total=15)


@dataclass
class WeatherData:
    city: str = ""
    temp: float = 0.0
    feels_like: float = 0.0
    description: str = ""
    icon: str = ""
    humidity: int = 0
    pressure: int = 0
    wind_speed: float = 0.0
    wind_deg: int = 0
    clouds: int = 0
    rain_1h: float = 0.0
    snow_1h: float = 0.0
    visibility: int = 10000
    dt: int = 0
    sunrise: int = 0
    sunset: int = 0


@dataclass
class ForecastItem:
    dt: int = 0
    dt_txt: str = ""
    temp: float = 0.0
    feels_like: float = 0.0
    description: str = ""
    icon: str = ""
    humidity: int = 0
    pressure: int = 0
    wind_speed: float = 0.0
    wind_deg: int = 0
    rain_3h: float = 0.0
    snow_3h: float = 0.0
    pop: float = 0.0


@dataclass
class ForecastData:
    city: str = ""
    timezone: int = 0
    items: list[ForecastItem] = field(default_factory=list)


WIND_DIRECTIONS = [
    "С", "ССВ", "СВ", "ВСВ", "В", "ВЮВ", "ЮВ", "ЮЮВ",
    "Ю", "ЮЮЗ", "ЮЗ", "ЗЮЗ", "З", "ЗСЗ", "СЗ", "ССЗ",
]


def wind_direction(deg: int) -> str:
    idx = round(deg / 22.5) % 16
    return WIND_DIRECTIONS[idx]


def _parse_current(data: dict) -> WeatherData:
    main = data.get("main", {})
    w = data.get("wind", {})
    weather_list = data.get("weather", [{}])
    weather = weather_list[0] if weather_list else {}
    rain = data.get("rain", {})
    snow = data.get("snow", {})
    sys = data.get("sys", {})
    return WeatherData(
        city=data.get("name", ""),
        temp=main.get("temp", 0),
        feels_like=main.get("feels_like", 0),
        description=weather.get("description", ""),
        icon=weather.get("icon", ""),
        humidity=main.get("humidity", 0),
        pressure=main.get("pressure", 0),
        wind_speed=w.get("speed", 0),
        wind_deg=w.get("deg", 0),
        clouds=data.get("clouds", {}).get("all", 0),
        rain_1h=rain.get("1h", 0),
        snow_1h=snow.get("1h", 0),
        visibility=data.get("visibility", 10000),
        dt=data.get("dt", 0),
        sunrise=sys.get("sunrise", 0),
        sunset=sys.get("sunset", 0),
    )


def _parse_forecast_item(item: dict) -> ForecastItem:
    main = item.get("main", {})
    w = item.get("wind", {})
    weather_list = item.get("weather", [{}])
    weather = weather_list[0] if weather_list else {}
    rain = item.get("rain", {})
    snow = item.get("snow", {})
    return ForecastItem(
        dt=item.get("dt", 0),
        dt_txt=item.get("dt_txt", ""),
        temp=main.get("temp", 0),
        feels_like=main.get("feels_like", 0),
        description=weather.get("description", ""),
        icon=weather.get("icon", ""),
        humidity=main.get("humidity", 0),
        pressure=main.get("pressure", 0),
        wind_speed=w.get("speed", 0),
        wind_deg=w.get("deg", 0),
        rain_3h=rain.get("3h", 0),
        snow_3h=snow.get("3h", 0),
        pop=item.get("pop", 0),
    )


async def _get_json(url: str, params: dict) -> dict | list | None:
    try:
        async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    logger.warning("API %s returned %s", url, resp.status)
                    return None
                return await resp.json()
    except Exception as e:
        logger.error("API request failed (%s): %s", url, e)
        return None


async def geocode_city(city: str) -> tuple[float, float] | None:
    params = {"q": city, "limit": 1, "appid": OWM_API_KEY}
    data = await _get_json(OWM_GEOCODE_URL, params)
    if not data:
        return None
    return data[0]["lat"], data[0]["lon"]


async def reverse_geocode(lat: float, lon: float) -> str:
    params = {"lat": lat, "lon": lon, "limit": 1, "appid": OWM_API_KEY}
    data = await _get_json(OWM_REVERSE_GEOCODE_URL, params)
    if not data:
        return ""
    item = data[0]
    return item.get("local_names", {}).get("ru", item.get("name", ""))


async def get_current_weather(lat: float, lon: float) -> WeatherData | None:
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OWM_API_KEY,
        "units": "metric",
        "lang": "ru",
    }
    data = await _get_json(OWM_CURRENT_URL, params)
    if not data or isinstance(data, list):
        return None
    return _parse_current(data)


async def get_forecast(lat: float, lon: float) -> ForecastData | None:
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OWM_API_KEY,
        "units": "metric",
        "lang": "ru",
    }
    data = await _get_json(OWM_FORECAST_URL, params)
    if not data or isinstance(data, list):
        return None
    items = [_parse_forecast_item(i) for i in data.get("list", [])]
    city_info = data.get("city", {})
    return ForecastData(
        city=city_info.get("name", ""),
        timezone=int(city_info.get("timezone", 0)),
        items=items,
    )


def interpolate_forecast(items: list[ForecastItem], target_ts: int) -> ForecastItem | None:
    """Возвращает ForecastItem на момент target_ts (UTC-секунды),
    линейно интерполируя между двумя соседними 3-часовыми слотами OWM."""
    if not items:
        return None
    if target_ts <= items[0].dt:
        return items[0]
    if target_ts >= items[-1].dt:
        return items[-1]

    for a, b in zip(items, items[1:]):
        if a.dt <= target_ts <= b.dt:
            span = b.dt - a.dt
            t = (target_ts - a.dt) / span if span else 0.0
            nearest = a if t < 0.5 else b
            dt_txt = datetime.fromtimestamp(target_ts, tz=_tz.utc).strftime("%Y-%m-%d %H:%M:%S")
            return ForecastItem(
                dt=target_ts,
                dt_txt=dt_txt,
                temp=a.temp + (b.temp - a.temp) * t,
                feels_like=a.feels_like + (b.feels_like - a.feels_like) * t,
                description=nearest.description,
                icon=nearest.icon,
                humidity=int(round(a.humidity + (b.humidity - a.humidity) * t)),
                pressure=int(round(a.pressure + (b.pressure - a.pressure) * t)),
                wind_speed=a.wind_speed + (b.wind_speed - a.wind_speed) * t,
                wind_deg=nearest.wind_deg,
                rain_3h=max(a.rain_3h, b.rain_3h),
                snow_3h=max(a.snow_3h, b.snow_3h),
                pop=max(a.pop, b.pop),
            )
    return items[-1]
