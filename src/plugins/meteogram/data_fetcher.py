import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import requests

logger = logging.getLogger(__name__)

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

METNO_URL = (
    "https://api.open-meteo.com/v1/metno"
    "?latitude={lat}&longitude={lon}"
    "&hourly=temperature_2m,precipitation,wind_speed_10m,wind_gusts_10m,"
    "pressure_msl,cloud_cover,weather_code"
    "&timezone={tz}"
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


def _fetch_model(url_template: str, lat: float, lon: float, model_name: str) -> Optional[ModelData]:
    url = url_template.format(lat=lat, lon=lon, tz=TIMEZONE)
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        hourly = data.get("hourly", {})
        return ModelData(
            model_name=model_name,
            times=hourly.get("time", []),
            temperature=hourly.get("temperature_2m", []),
            precipitation=hourly.get("precipitation", []),
            wind_speed=hourly.get("wind_speed_10m", []),
            wind_gusts=hourly.get("wind_gusts_10m", []),
            pressure=hourly.get("pressure_msl", []),
            cloud_cover=hourly.get("cloud_cover", []),
            weather_code=hourly.get("weather_code", []),
            generation_time=data.get("generationtime_ms"),
        )
    except Exception as e:
        logger.error(f"Failed to fetch {model_name} data: {e}")
        return None


def fetch_ecmwf(lat: float = LAT, lon: float = LON) -> Optional[ModelData]:
    return _fetch_model(ECMWF_URL, lat, lon, "ECMWF")


def fetch_metno(lat: float = LAT, lon: float = LON) -> Optional[ModelData]:
    return _fetch_model(METNO_URL, lat, lon, "MetNo")
