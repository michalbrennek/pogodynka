import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import math
import requests

logger = logging.getLogger(__name__)

NAN = float("nan")

LAT = 52.2858
LON = 20.9329
TIMEZONE = "Europe/Warsaw"

ECMWF_URL = (
    "https://api.open-meteo.com/v1/ecmwf"
    "?latitude={lat}&longitude={lon}"
    "&hourly=temperature_2m,precipitation,wind_speed_10m,wind_gusts_10m,"
    "pressure_msl,cloud_cover,weather_code"
    "&timezone={tz}"
)

ICON_EU_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude={lat}&longitude={lon}"
    "&hourly=temperature_2m,precipitation,wind_speed_10m,wind_gusts_10m,"
    "pressure_msl,cloud_cover,weather_code"
    "&timezone={tz}"
    "&models=icon_eu"
)


@dataclass
class ModelData:
    model_name: str
    times: list = field(default_factory=list)
    temperature: list = field(default_factory=list)
    precipitation: list = field(default_factory=list)
    wind_speed: list = field(default_factory=list)
    wind_gusts: list = field(default_factory=list)
    pressure: list = field(default_factory=list)
    cloud_cover: list = field(default_factory=list)
    weather_code: list = field(default_factory=list)
    generation_time: Optional[float] = None


def _sanitize(values: list, default=NAN) -> list:
    """Replace None values from API with a safe default.

    NaN causes matplotlib to break lines at missing points.
    Use 0 for integer fields like weather_code.
    """
    return [v if v is not None else default for v in values]


def _trim_trailing_nan(times: list, *series) -> tuple:
    """Remove trailing time steps where ALL numeric series are NaN."""
    if not times:
        return (times, *series)
    last_valid = -1
    for i in range(len(times) - 1, -1, -1):
        if any(
            i < len(s) and not (isinstance(s[i], float) and math.isnan(s[i]))
            for s in series
        ):
            last_valid = i
            break
    end = last_valid + 1
    return (times[:end], *(s[:end] for s in series))


def _fetch_model(url_template: str, lat: float, lon: float, model_name: str) -> Optional[ModelData]:
    url = url_template.format(lat=lat, lon=lon, tz=TIMEZONE)
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        hourly = data.get("hourly", {})

        times = hourly.get("time", [])
        temperature = _sanitize(hourly.get("temperature_2m", []))
        precipitation = _sanitize(hourly.get("precipitation", []), 0.0)
        wind_speed = _sanitize(hourly.get("wind_speed_10m", []))
        wind_gusts = _sanitize(hourly.get("wind_gusts_10m", []))
        pressure = _sanitize(hourly.get("pressure_msl", []))
        cloud_cover = _sanitize(hourly.get("cloud_cover", []))
        weather_code = _sanitize(hourly.get("weather_code", []), 0)

        # Trim trailing all-NaN hours so lines don't extend into empty data
        times, temperature, wind_speed, wind_gusts, pressure, cloud_cover = \
            _trim_trailing_nan(
                times, temperature, wind_speed, wind_gusts, pressure, cloud_cover,
            )
        # Also trim precipitation and weather_code to same length
        precipitation = precipitation[:len(times)]
        weather_code = weather_code[:len(times)]

        return ModelData(
            model_name=model_name,
            times=times,
            temperature=temperature,
            precipitation=precipitation,
            wind_speed=wind_speed,
            wind_gusts=wind_gusts,
            pressure=pressure,
            cloud_cover=cloud_cover,
            weather_code=weather_code,
            generation_time=data.get("generationtime_ms"),
        )
    except Exception as e:
        logger.error(f"Failed to fetch {model_name} data: {e}")
        return None


def fetch_ecmwf(lat: float = LAT, lon: float = LON) -> Optional[ModelData]:
    return _fetch_model(ECMWF_URL, lat, lon, "ECMWF")


def fetch_icon_eu(lat: float = LAT, lon: float = LON) -> Optional[ModelData]:
    return _fetch_model(ICON_EU_URL, lat, lon, "ICON-EU")


# --- Astronomical data ---

DAILY_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude={lat}&longitude={lon}"
    "&daily=sunrise,sunset"
    "&timezone={tz}"
    "&forecast_days=1"
)


@dataclass
class AstroData:
    sunrise: Optional[str] = None
    sunset: Optional[str] = None
    moon_phase: float = 0.0
    moon_icon: str = ""
    moon_name: str = ""


def _compute_moon_phase(dt: datetime) -> tuple:
    """Compute moon phase from date. Returns (phase 0-1, icon, name)."""
    # Reference new moon: 2024-01-11 11:57 UTC
    ref = datetime(2024, 1, 11, 11, 57)
    days = (dt - ref).total_seconds() / 86400
    cycle = 29.53059
    phase = (days % cycle) / cycle

    phases = [
        (0.0625, "\U0001f311", "New Moon"),
        (0.1875, "\U0001f312", "Waxing Crescent"),
        (0.3125, "\U0001f313", "First Quarter"),
        (0.4375, "\U0001f314", "Waxing Gibbous"),
        (0.5625, "\U0001f315", "Full Moon"),
        (0.6875, "\U0001f316", "Waning Gibbous"),
        (0.8125, "\U0001f317", "Last Quarter"),
        (0.9375, "\U0001f318", "Waning Crescent"),
    ]
    for threshold, icon, name in phases:
        if phase < threshold:
            return phase, icon, name
    return phase, "\U0001f311", "New Moon"


def fetch_astro(lat: float = LAT, lon: float = LON) -> AstroData:
    """Fetch sunrise/sunset from Open-Meteo and compute moon phase."""
    phase, icon, name = _compute_moon_phase(datetime.now())
    astro = AstroData(moon_phase=phase, moon_icon=icon, moon_name=name)

    url = DAILY_URL.format(lat=lat, lon=lon, tz=TIMEZONE)
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        daily = data.get("daily", {})
        sunrise_list = daily.get("sunrise", [])
        sunset_list = daily.get("sunset", [])
        if sunrise_list:
            astro.sunrise = sunrise_list[0]
        if sunset_list:
            astro.sunset = sunset_list[0]
    except Exception as e:
        logger.error(f"Failed to fetch astro data: {e}")

    return astro
