"""Maps WMO weather codes to display icons and descriptions.

WMO codes: https://www.nodc.noaa.gov/archive/arc0021/0002199/1.1/data/0-data/HTML/WMO-CODE/WMO4677.HTM
Open-Meteo uses a subset of these codes.
"""

_WMO_ICONS = {
    0: "\u2600",      # Clear sky
    1: "\u26C5",      # Mainly clear
    2: "\u26C5",      # Partly cloudy
    3: "\u2601",      # Overcast
    45: "\u2601",     # Fog
    48: "\u2601",     # Depositing rime fog
    51: "\u2602",     # Light drizzle
    53: "\u2602",     # Moderate drizzle
    55: "\u2602",     # Dense drizzle
    61: "\u2614",     # Slight rain
    63: "\u2614",     # Moderate rain
    65: "\u2614",     # Heavy rain
    66: "\u2614",     # Light freezing rain
    67: "\u2614",     # Heavy freezing rain
    71: "\u2744",     # Slight snow
    73: "\u2744",     # Moderate snow
    75: "\u2744",     # Heavy snow
    77: "\u2744",     # Snow grains
    80: "\u2614",     # Slight rain showers
    81: "\u2614",     # Moderate rain showers
    82: "\u2614",     # Violent rain showers
    85: "\u2744",     # Slight snow showers
    86: "\u2744",     # Heavy snow showers
    95: "\u26A1",     # Thunderstorm
    96: "\u26A1",     # Thunderstorm with slight hail
    99: "\u26A1",     # Thunderstorm with heavy hail
}

_WMO_DESCRIPTIONS = {
    0: "Clear",
    1: "Mostly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Rain showers",
    81: "Mod. showers",
    82: "Heavy showers",
    85: "Snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "T-storm + hail",
    99: "T-storm + heavy hail",
}

_DEFAULT_ICON = "\u2601"


def wmo_to_icon(code: int) -> str:
    return _WMO_ICONS.get(code, _DEFAULT_ICON)


def wmo_to_description(code: int) -> str:
    return _WMO_DESCRIPTIONS.get(code, "Unknown")


# Wind direction arrows — shows where wind BLOWS TO
# (meteorological convention: degrees = direction wind comes FROM)
_WIND_ARROWS = [
    "\u2193",  # 0° N  → blows south ↓
    "\u2199",  # 45° NE → blows SW ↙
    "\u2190",  # 90° E  → blows west ←
    "\u2196",  # 135° SE → blows NW ↖
    "\u2191",  # 180° S  → blows north ↑
    "\u2197",  # 225° SW → blows NE ↗
    "\u2192",  # 270° W  → blows east →
    "\u2198",  # 315° NW → blows SE ↘
]


def wind_direction_arrow(degrees: float) -> str:
    """Convert wind direction in degrees to an arrow character."""
    idx = round(degrees / 45) % 8
    return _WIND_ARROWS[idx]
