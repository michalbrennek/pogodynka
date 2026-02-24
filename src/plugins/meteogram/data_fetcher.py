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
    "&hourly=temperature_2m,apparent_temperature,precipitation,"
    "precipitation_probability,relative_humidity_2m,"
    "wind_speed_10m,wind_gusts_10m,"
    "wind_direction_10m,pressure_msl,cloud_cover,weather_code"
    "&timezone={tz}"
)

ICON_EU_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude={lat}&longitude={lon}"
    "&hourly=temperature_2m,apparent_temperature,precipitation,"
    "precipitation_probability,relative_humidity_2m,"
    "wind_speed_10m,wind_gusts_10m,wind_direction_10m,"
    "pressure_msl,cloud_cover,weather_code"
    "&timezone={tz}"
    "&models=icon_eu"
)

BEST_MATCH_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude={lat}&longitude={lon}"
    "&hourly=temperature_2m,apparent_temperature,precipitation,"
    "precipitation_probability,relative_humidity_2m,"
    "wind_speed_10m,wind_gusts_10m,wind_direction_10m,"
    "pressure_msl,cloud_cover,weather_code"
    "&timezone={tz}"
)


@dataclass
class ModelData:
    model_name: str
    times: list = field(default_factory=list)
    temperature: list = field(default_factory=list)
    apparent_temperature: list = field(default_factory=list)
    humidity: list = field(default_factory=list)
    precipitation: list = field(default_factory=list)
    precip_probability: list = field(default_factory=list)
    wind_speed: list = field(default_factory=list)
    wind_gusts: list = field(default_factory=list)
    wind_direction: list = field(default_factory=list)
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
        apparent_temperature = _sanitize(hourly.get("apparent_temperature", []))
        humidity = _sanitize(hourly.get("relative_humidity_2m", []))
        precipitation = _sanitize(hourly.get("precipitation", []), 0.0)
        precip_probability = _sanitize(hourly.get("precipitation_probability", []), 0.0)
        wind_speed = _sanitize(hourly.get("wind_speed_10m", []))
        wind_gusts = _sanitize(hourly.get("wind_gusts_10m", []))
        wind_direction = _sanitize(hourly.get("wind_direction_10m", []), 0.0)
        pressure = _sanitize(hourly.get("pressure_msl", []))
        cloud_cover = _sanitize(hourly.get("cloud_cover", []))
        weather_code = _sanitize(hourly.get("weather_code", []), 0)

        # Trim trailing all-NaN hours so lines don't extend into empty data
        times, temperature, apparent_temperature, wind_speed, wind_gusts, \
            wind_direction, pressure, cloud_cover, humidity = \
            _trim_trailing_nan(
                times, temperature, apparent_temperature, wind_speed,
                wind_gusts, wind_direction, pressure, cloud_cover, humidity,
            )
        # Also trim other series to same length
        precipitation = precipitation[:len(times)]
        precip_probability = precip_probability[:len(times)]
        weather_code = weather_code[:len(times)]

        return ModelData(
            model_name=model_name,
            times=times,
            temperature=temperature,
            apparent_temperature=apparent_temperature,
            humidity=humidity,
            precipitation=precipitation,
            precip_probability=precip_probability,
            wind_speed=wind_speed,
            wind_gusts=wind_gusts,
            wind_direction=wind_direction,
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


def fetch_best_match(lat: float = LAT, lon: float = LON) -> Optional[ModelData]:
    return _fetch_model(BEST_MATCH_URL, lat, lon, "Best Match")


# --- Synoptic chart ---

SYNOPTIC_URL = "https://www.weathercharts.net/ukmo_mslp_analysis/ppva.gif"


def fetch_synoptic_chart() -> Optional[bytes]:
    """Download UKMO surface pressure analysis chart from weathercharts.org.

    Black & white fax-style chart, ~80KB, updated every 6 hours.
    """
    headers = {"User-Agent": "pogodynka/1.0"}
    try:
        resp = requests.get(SYNOPTIC_URL, timeout=30, headers=headers)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        logger.error(f"Failed to fetch synoptic chart: {e}")
        return None


# --- Astronomical data ---

DAILY_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude={lat}&longitude={lon}"
    "&daily=sunrise,sunset"
    "&timezone={tz}"
    "&forecast_days=1"
)

METNO_MOON_URL = (
    "https://api.met.no/weatherapi/sunrise/3.0/moon"
    "?lat={lat}&lon={lon}&date={date}&offset={offset}"
)


@dataclass
class AstroData:
    sunrise: Optional[str] = None
    sunset: Optional[str] = None
    moonrise: Optional[str] = None
    moonset: Optional[str] = None
    moon_phase: float = 0.0
    moon_icon: str = ""
    moon_name: str = ""


# DejaVu Sans compatible moon symbols (U+263D/E range)
_MOON_PHASES = [
    (0.0625, "\u25CF", "New Moon"),        # ● (filled circle)
    (0.1875, "\u263D", "Waxing Crescent"), # ☽
    (0.3125, "\u25D0", "First Quarter"),   # ◐
    (0.4375, "\u263D", "Waxing Gibbous"),  # ☽
    (0.5625, "\u25CB", "Full Moon"),       # ○ (open circle)
    (0.6875, "\u263E", "Waning Gibbous"),  # ☾
    (0.8125, "\u25D1", "Last Quarter"),    # ◑
    (0.9375, "\u263E", "Waning Crescent"), # ☾
]


def _compute_moon_phase(dt: datetime) -> tuple:
    """Compute moon phase from date. Returns (phase 0-1, icon, name)."""
    # Reference new moon: 2024-01-11 11:57 UTC
    ref = datetime(2024, 1, 11, 11, 57)
    days = (dt - ref).total_seconds() / 86400
    cycle = 29.53059
    phase = (days % cycle) / cycle

    for threshold, icon, name in _MOON_PHASES:
        if phase < threshold:
            return phase, icon, name
    return phase, "\u25CF", "New Moon"


def _extract_time(iso_str: str) -> str:
    """Extract HH:MM from an ISO timestamp like '2026-02-24T06:45+01:00'."""
    if "T" in iso_str:
        return iso_str.split("T")[1][:5]
    return iso_str


def fetch_astro(lat: float = LAT, lon: float = LON) -> AstroData:
    """Fetch sunrise/sunset + moonrise/moonset and compute moon phase."""
    phase, icon, name = _compute_moon_phase(datetime.now())
    astro = AstroData(moon_phase=phase, moon_icon=icon, moon_name=name)

    # Sunrise/sunset from Open-Meteo
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
        logger.error(f"Failed to fetch sun data: {e}")

    # Moonrise/moonset from MET Norway astronomical API
    today = datetime.now().strftime("%Y-%m-%d")
    moon_url = METNO_MOON_URL.format(lat=lat, lon=lon, date=today, offset="%2B01:00")
    try:
        resp = requests.get(moon_url, timeout=15,
                            headers={"User-Agent": "pogodynka/1.0"})
        resp.raise_for_status()
        data = resp.json()
        props = data.get("properties", {})
        mr = props.get("moonrise", {})
        ms = props.get("moonset", {})
        if mr and "time" in mr:
            astro.moonrise = mr["time"]
        if ms and "time" in ms:
            astro.moonset = ms["time"]
    except Exception as e:
        logger.error(f"Failed to fetch moon data: {e}")

    return astro
