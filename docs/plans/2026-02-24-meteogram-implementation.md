# Meteogram Plugin Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an InkyPi plugin that renders a dual-model (ECMWF + Norwegian) weather meteogram on an Inky Impression 7.3" e-ink display.

**Architecture:** InkyPi plugin inheriting `BasePlugin`. Matplotlib renders a 3/4 + 1/4 layout: left panel has 4 stacked meteogram subplots (temp, precip, wind, pressure/clouds) with both models overlaid; right panel shows 24h hourly detail with weather icons. Smart caching skips re-renders when model data hasn't changed.

**Tech Stack:** Python, matplotlib, PIL/Pillow, numpy, requests, InkyPi plugin framework, Open-Meteo API

---

### Task 1: Set Up InkyPi and Plugin Scaffold

This task sets up InkyPi on the Raspberry Pi and creates the bare plugin skeleton.

**Files:**
- Create: `src/plugins/meteogram/meteogram.py`
- Create: `src/plugins/meteogram/plugin-info.json`
- Create: `src/plugins/meteogram/__init__.py`

**Prerequisites:** InkyPi must be cloned and installed on pogodynka.local. The plugin development happens locally and gets deployed via SSH/git.

**Step 1: Clone InkyPi locally as a submodule or reference**

We develop the plugin inside the pogodynka repo. Create the plugin directory structure:

```bash
mkdir -p src/plugins/meteogram
```

**Step 2: Create plugin-info.json**

Create `src/plugins/meteogram/plugin-info.json`:
```json
{
    "display_name": "Meteogram",
    "id": "meteogram",
    "class": "Meteogram"
}
```

**Step 3: Create minimal plugin class**

Create `src/plugins/meteogram/meteogram.py`:
```python
import logging
from plugins.base_plugin.base_plugin import BasePlugin
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)


class Meteogram(BasePlugin):
    def generate_image(self, settings, device_config):
        dimensions = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]

        # Placeholder: solid white image with "Meteogram" text
        img = Image.new("RGB", dimensions, "white")
        draw = ImageDraw.Draw(img)
        draw.text((20, 20), "Meteogram Plugin - Loading...", fill="black")
        return img
```

**Step 4: Create empty __init__.py**

Create `src/plugins/meteogram/__init__.py`:
```python
```

**Step 5: Commit**

```bash
git add src/plugins/meteogram/
git commit -m "feat: scaffold meteogram plugin with placeholder image"
```

---

### Task 2: Data Fetcher — Open-Meteo API Client

Fetches forecast data from both ECMWF and MET Nordic (Norwegian) models via Open-Meteo.

**Files:**
- Create: `src/plugins/meteogram/data_fetcher.py`
- Create: `tests/test_data_fetcher.py`

**Step 1: Write the failing test**

Create `tests/test_data_fetcher.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from plugins.meteogram.data_fetcher import fetch_ecmwf, fetch_metno, ModelData


def _make_response(json_data, status=200):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = json_data
    resp.raise_for_status.return_value = None
    return resp


SAMPLE_RESPONSE = {
    "generationtime_ms": 1.5,
    "hourly": {
        "time": ["2026-02-24T00:00", "2026-02-24T01:00"],
        "temperature_2m": [5.0, 4.5],
        "precipitation": [0.0, 0.2],
        "wind_speed_10m": [3.0, 4.0],
        "wind_gusts_10m": [6.0, 8.0],
        "pressure_msl": [1013.0, 1012.5],
        "cloud_cover": [50, 70],
        "weather_code": [3, 61],
    },
}


@patch("plugins.meteogram.data_fetcher.requests.get")
def test_fetch_ecmwf_returns_model_data(mock_get):
    mock_get.return_value = _make_response(SAMPLE_RESPONSE)
    result = fetch_ecmwf(52.2858, 20.9329)
    assert isinstance(result, ModelData)
    assert len(result.times) == 2
    assert result.temperature[0] == 5.0
    assert result.model_name == "ECMWF"


@patch("plugins.meteogram.data_fetcher.requests.get")
def test_fetch_metno_returns_model_data(mock_get):
    mock_get.return_value = _make_response(SAMPLE_RESPONSE)
    result = fetch_metno(52.2858, 20.9329)
    assert isinstance(result, ModelData)
    assert result.model_name == "MetNo"


@patch("plugins.meteogram.data_fetcher.requests.get")
def test_fetch_ecmwf_handles_api_error(mock_get):
    mock_get.return_value = _make_response({}, status=500)
    mock_get.return_value.raise_for_status.side_effect = Exception("Server error")
    result = fetch_ecmwf(52.2858, 20.9329)
    assert result is None
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_data_fetcher.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'plugins.meteogram.data_fetcher'`

**Step 3: Write the implementation**

Create `src/plugins/meteogram/data_fetcher.py`:
```python
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
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_data_fetcher.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add src/plugins/meteogram/data_fetcher.py tests/test_data_fetcher.py
git commit -m "feat: add Open-Meteo data fetcher for ECMWF and MetNo models"
```

---

### Task 3: Cache Module — Smart Model Update Tracking

Tracks model run timestamps and avoids redundant renders.

**Files:**
- Create: `src/plugins/meteogram/cache.py`
- Create: `tests/test_cache.py`

**Step 1: Write the failing test**

Create `tests/test_cache.py`:
```python
import pytest
import json
import os
from plugins.meteogram.cache import MeteogramCache


@pytest.fixture
def cache_file(tmp_path):
    return str(tmp_path / "cache.json")


def test_fresh_cache_has_no_data(cache_file):
    cache = MeteogramCache(cache_file)
    assert cache.has_new_data("ECMWF", 1.5) is True
    assert cache.has_new_data("MetNo", 2.0) is True


def test_cache_stores_and_detects_same_data(cache_file):
    cache = MeteogramCache(cache_file)
    cache.update("ECMWF", 1.5)
    cache.update("MetNo", 2.0)
    assert cache.has_new_data("ECMWF", 1.5) is False
    assert cache.has_new_data("MetNo", 2.0) is False


def test_cache_detects_new_data(cache_file):
    cache = MeteogramCache(cache_file)
    cache.update("ECMWF", 1.5)
    assert cache.has_new_data("ECMWF", 1.8) is True


def test_cache_persists_to_disk(cache_file):
    cache1 = MeteogramCache(cache_file)
    cache1.update("ECMWF", 1.5)

    cache2 = MeteogramCache(cache_file)
    assert cache2.has_new_data("ECMWF", 1.5) is False


def test_cache_stores_image_path(cache_file):
    cache = MeteogramCache(cache_file)
    cache.set_last_image("/tmp/test.png")
    assert cache.get_last_image() == "/tmp/test.png"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cache.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write the implementation**

Create `src/plugins/meteogram/cache.py`:
```python
import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class MeteogramCache:
    def __init__(self, cache_path: str):
        self.cache_path = cache_path
        self.data = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Cache read failed: {e}")
        return {}

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
            with open(self.cache_path, "w") as f:
                json.dump(self.data, f)
        except IOError as e:
            logger.error(f"Cache write failed: {e}")

    def has_new_data(self, model_name: str, generation_time: float) -> bool:
        key = f"{model_name}_generation_time"
        return self.data.get(key) != generation_time

    def update(self, model_name: str, generation_time: float):
        self.data[f"{model_name}_generation_time"] = generation_time
        self._save()

    def set_last_image(self, path: str):
        self.data["last_image_path"] = path
        self._save()

    def get_last_image(self) -> Optional[str]:
        return self.data.get("last_image_path")
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cache.py -v`
Expected: 5 passed

**Step 5: Commit**

```bash
git add src/plugins/meteogram/cache.py tests/test_cache.py
git commit -m "feat: add smart cache for tracking model update timestamps"
```

---

### Task 4: Weather Icons — WMO Code Mapping

Maps WMO weather codes to simple text-based icons for the right panel.

**Files:**
- Create: `src/plugins/meteogram/weather_icons.py`
- Create: `tests/test_weather_icons.py`

**Step 1: Write the failing test**

Create `tests/test_weather_icons.py`:
```python
from plugins.meteogram.weather_icons import wmo_to_icon, wmo_to_description


def test_clear_sky():
    assert wmo_to_icon(0) is not None
    assert wmo_to_description(0) == "Clear"


def test_rain_codes():
    assert wmo_to_icon(61) is not None  # Slight rain
    assert wmo_to_icon(63) is not None  # Moderate rain
    assert "rain" in wmo_to_description(61).lower()


def test_snow_codes():
    assert wmo_to_icon(71) is not None
    assert "snow" in wmo_to_description(71).lower()


def test_thunderstorm():
    assert wmo_to_icon(95) is not None
    assert "thunder" in wmo_to_description(95).lower()


def test_unknown_code_returns_default():
    assert wmo_to_icon(999) is not None
    assert wmo_to_description(999) == "Unknown"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_weather_icons.py -v`
Expected: FAIL

**Step 3: Write the implementation**

Create `src/plugins/meteogram/weather_icons.py`:
```python
"""Maps WMO weather codes to display icons and descriptions.

WMO codes: https://www.nodc.noaa.gov/archive/arc0021/0002199/1.1/data/0-data/HTML/WMO-CODE/WMO4677.HTM
Open-Meteo uses a subset of these codes.
"""

# Unicode symbols for e-ink rendering (rendered via matplotlib text)
_WMO_ICONS = {
    0: "\u2600",      # Clear sky — sun
    1: "\u26C5",      # Mainly clear — sun behind cloud
    2: "\u26C5",      # Partly cloudy
    3: "\u2601",      # Overcast — cloud
    45: "\u2601",     # Fog
    48: "\u2601",     # Depositing rime fog
    51: "\u2602",     # Light drizzle — umbrella
    53: "\u2602",     # Moderate drizzle
    55: "\u2602",     # Dense drizzle
    61: "\u2614",     # Slight rain — umbrella with drops
    63: "\u2614",     # Moderate rain
    65: "\u2614",     # Heavy rain
    66: "\u2614",     # Light freezing rain
    67: "\u2614",     # Heavy freezing rain
    71: "\u2744",     # Slight snow — snowflake
    73: "\u2744",     # Moderate snow
    75: "\u2744",     # Heavy snow
    77: "\u2744",     # Snow grains
    80: "\u2614",     # Slight rain showers
    81: "\u2614",     # Moderate rain showers
    82: "\u2614",     # Violent rain showers
    85: "\u2744",     # Slight snow showers
    86: "\u2744",     # Heavy snow showers
    95: "\u26A1",     # Thunderstorm — lightning
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

_DEFAULT_ICON = "\u2601"  # Cloud as fallback


def wmo_to_icon(code: int) -> str:
    return _WMO_ICONS.get(code, _DEFAULT_ICON)


def wmo_to_description(code: int) -> str:
    return _WMO_DESCRIPTIONS.get(code, "Unknown")
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_weather_icons.py -v`
Expected: 5 passed

**Step 5: Commit**

```bash
git add src/plugins/meteogram/weather_icons.py tests/test_weather_icons.py
git commit -m "feat: add WMO weather code to icon/description mapping"
```

---

### Task 5: Chart Renderer — Left Panel Meteogram

The core rendering engine. Draws 4 stacked matplotlib subplots with both model traces.

**Files:**
- Create: `src/plugins/meteogram/chart_renderer.py`
- Create: `tests/test_chart_renderer.py`

**Step 1: Write the failing test**

Create `tests/test_chart_renderer.py`:
```python
import pytest
from PIL import Image
from plugins.meteogram.data_fetcher import ModelData
from plugins.meteogram.chart_renderer import render_meteogram


def _make_model_data(model_name, hours=48):
    return ModelData(
        model_name=model_name,
        times=[f"2026-02-24T{h:02d}:00" for h in range(min(hours, 24))]
              + [f"2026-02-25T{h:02d}:00" for h in range(max(0, min(hours - 24, 24)))],
        temperature=[5.0 + i * 0.1 for i in range(hours)],
        precipitation=[0.0 if i % 6 != 0 else 1.5 for i in range(hours)],
        wind_speed=[3.0 + i * 0.05 for i in range(hours)],
        wind_gusts=[6.0 + i * 0.1 for i in range(hours)],
        pressure=[1013.0 - i * 0.1 for i in range(hours)],
        cloud_cover=[50 + (i % 30) for i in range(hours)],
        weather_code=[3] * hours,
    )


def test_render_meteogram_returns_pil_image():
    ecmwf = _make_model_data("ECMWF", 48)
    metno = _make_model_data("MetNo", 48)
    img = render_meteogram(ecmwf, metno, (800, 480))
    assert isinstance(img, Image.Image)
    assert img.size == (800, 480)


def test_render_meteogram_without_metno():
    ecmwf = _make_model_data("ECMWF", 48)
    img = render_meteogram(ecmwf, None, (800, 480))
    assert isinstance(img, Image.Image)
    assert img.size == (800, 480)


def test_render_meteogram_rgb_mode():
    ecmwf = _make_model_data("ECMWF", 48)
    metno = _make_model_data("MetNo", 48)
    img = render_meteogram(ecmwf, metno, (800, 480))
    assert img.mode == "RGB"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_chart_renderer.py -v`
Expected: FAIL

**Step 3: Write the implementation**

Create `src/plugins/meteogram/chart_renderer.py`:

```python
import logging
from datetime import datetime
from io import BytesIO
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from PIL import Image

from plugins.meteogram.data_fetcher import ModelData
from plugins.meteogram.weather_icons import wmo_to_icon, wmo_to_description

logger = logging.getLogger(__name__)

# E-ink 7-color palette
ECMWF_COLOR = "#0000FF"     # Blue
METNO_COLOR = "#FF0000"     # Red
CLOUD_COLOR = "#FFFF00"     # Yellow
GRID_COLOR = "#00FF00"      # Green
BG_COLOR = "#FFFFFF"        # White
TEXT_COLOR = "#000000"       # Black
ACCENT_COLOR = "#FF8C00"    # Orange

# Plot settings
DPI = 100
FONT_FAMILY = "DejaVu Sans"
FONT_SIZE_TITLE = 9
FONT_SIZE_LABEL = 7
FONT_SIZE_TICK = 6


def _parse_times(time_strings: list) -> list:
    return [datetime.fromisoformat(t) for t in time_strings]


def render_meteogram(
    ecmwf: ModelData,
    metno: Optional[ModelData],
    dimensions: tuple,
) -> Image.Image:
    """Render the left 3/4 meteogram panel with 4 stacked subplots."""
    total_w, total_h = dimensions
    left_w = int(total_w * 0.75)

    fig_w = left_w / DPI
    fig_h = total_h / DPI

    plt.rcParams.update({
        "font.family": FONT_FAMILY,
        "font.size": FONT_SIZE_LABEL,
        "axes.labelsize": FONT_SIZE_LABEL,
        "axes.titlesize": FONT_SIZE_TITLE,
        "xtick.labelsize": FONT_SIZE_TICK,
        "ytick.labelsize": FONT_SIZE_TICK,
        "figure.facecolor": BG_COLOR,
        "axes.facecolor": BG_COLOR,
        "text.antialiased": False,
        "lines.antialiased": False,
    })

    fig, axes = plt.subplots(4, 1, figsize=(fig_w, fig_h), dpi=DPI, sharex=True)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.96, bottom=0.08, hspace=0.25)

    ecmwf_times = _parse_times(ecmwf.times)
    metno_times = _parse_times(metno.times) if metno else []

    # --- Temperature ---
    ax_temp = axes[0]
    ax_temp.plot(ecmwf_times, ecmwf.temperature, color=ECMWF_COLOR, linewidth=1.2, label="ECMWF")
    if metno:
        ax_temp.plot(metno_times, metno.temperature, color=METNO_COLOR, linewidth=1.2, label="MetNo")
    ax_temp.set_ylabel("Temp (°C)")
    ax_temp.legend(loc="upper right", fontsize=FONT_SIZE_TICK, framealpha=0.8)
    ax_temp.grid(True, linestyle=":", linewidth=0.3, color=GRID_COLOR)

    # --- Precipitation ---
    ax_precip = axes[1]
    bar_width = 0.02  # in days
    ax_precip.bar(ecmwf_times, ecmwf.precipitation, width=bar_width,
                  color=ECMWF_COLOR, alpha=0.7, label="ECMWF")
    if metno:
        ax_precip.bar(metno_times, metno.precipitation, width=bar_width,
                      color=METNO_COLOR, alpha=0.7, label="MetNo")
    ax_precip.set_ylabel("Precip (mm)")
    ax_precip.set_ylim(bottom=0)
    ax_precip.grid(True, linestyle=":", linewidth=0.3, color=GRID_COLOR)

    # --- Wind ---
    ax_wind = axes[2]
    ax_wind.plot(ecmwf_times, ecmwf.wind_speed, color=ECMWF_COLOR, linewidth=1.2, label="ECMWF")
    ax_wind.plot(ecmwf_times, ecmwf.wind_gusts, color=ECMWF_COLOR, linewidth=0.5,
                 linestyle="--", alpha=0.5)
    if metno:
        ax_wind.plot(metno_times, metno.wind_speed, color=METNO_COLOR, linewidth=1.2, label="MetNo")
        ax_wind.plot(metno_times, metno.wind_gusts, color=METNO_COLOR, linewidth=0.5,
                     linestyle="--", alpha=0.5)
    ax_wind.set_ylabel("Wind (m/s)")
    ax_wind.set_ylim(bottom=0)
    ax_wind.grid(True, linestyle=":", linewidth=0.3, color=GRID_COLOR)

    # --- Pressure + Cloud Cover ---
    ax_press = axes[3]
    ax_press.plot(ecmwf_times, ecmwf.pressure, color=ECMWF_COLOR, linewidth=1.2, label="ECMWF")
    if metno:
        ax_press.plot(metno_times, metno.pressure, color=METNO_COLOR, linewidth=1.2, label="MetNo")
    ax_press.set_ylabel("hPa")
    ax_press.grid(True, linestyle=":", linewidth=0.3, color=GRID_COLOR)

    # Cloud cover as filled area on secondary axis
    ax_cloud = ax_press.twinx()
    ax_cloud.fill_between(ecmwf_times, ecmwf.cloud_cover, alpha=0.15, color=CLOUD_COLOR)
    ax_cloud.set_ylabel("Cloud %", fontsize=FONT_SIZE_TICK)
    ax_cloud.set_ylim(0, 100)
    ax_cloud.tick_params(labelsize=FONT_SIZE_TICK)

    # X-axis formatting
    ax_press.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m\n%Hz"))
    ax_press.xaxis.set_major_locator(mdates.HourLocator(interval=12))
    plt.setp(ax_press.xaxis.get_majorticklabels(), rotation=0, ha="center")

    # Convert to PIL image
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=DPI, facecolor=BG_COLOR)
    plt.close(fig)
    buf.seek(0)
    left_img = Image.open(buf).convert("RGB")

    # Compose into full-size image (left 3/4)
    full_img = Image.new("RGB", dimensions, BG_COLOR)
    full_img.paste(left_img.resize((left_w, total_h)), (0, 0))

    return full_img
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_chart_renderer.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add src/plugins/meteogram/chart_renderer.py tests/test_chart_renderer.py
git commit -m "feat: add matplotlib meteogram renderer with 4 stacked subplots"
```

---

### Task 6: Right Panel — 24h Hourly Detail Sidebar

Renders the right 1/4 panel with current conditions, hourly forecast rows, and model info footer.

**Files:**
- Modify: `src/plugins/meteogram/chart_renderer.py`
- Create: `tests/test_right_panel.py`

**Step 1: Write the failing test**

Create `tests/test_right_panel.py`:
```python
import pytest
from PIL import Image
from plugins.meteogram.chart_renderer import render_right_panel
from plugins.meteogram.data_fetcher import ModelData


def _make_model_data(hours=24):
    return ModelData(
        model_name="ECMWF",
        times=[f"2026-02-24T{h:02d}:00" for h in range(hours)],
        temperature=[5.0 + h * 0.5 for h in range(hours)],
        precipitation=[0.0] * hours,
        wind_speed=[3.0 + h * 0.1 for h in range(hours)],
        wind_gusts=[6.0] * hours,
        pressure=[1013.0] * hours,
        cloud_cover=[50] * hours,
        weather_code=[3] * hours,
    )


def test_render_right_panel_returns_image():
    data = _make_model_data()
    img = render_right_panel(data, width=200, height=480)
    assert isinstance(img, Image.Image)
    assert img.size == (200, 480)


def test_render_right_panel_rgb():
    data = _make_model_data()
    img = render_right_panel(data, width=200, height=480)
    assert img.mode == "RGB"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_right_panel.py -v`
Expected: FAIL — `ImportError: cannot import name 'render_right_panel'`

**Step 3: Add render_right_panel to chart_renderer.py**

Add to end of `src/plugins/meteogram/chart_renderer.py`:

```python
def render_right_panel(
    data: ModelData,
    width: int = 200,
    height: int = 480,
    model_info: str = "",
) -> Image.Image:
    """Render the right 1/4 sidebar with 24h hourly detail."""
    img = Image.new("RGB", (width, height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        font_icon = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except (IOError, OSError):
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_icon = ImageFont.load_default()

    # Draw left border separator
    draw.line([(0, 0), (0, height)], fill=TEXT_COLOR, width=2)

    y = 8
    pad = 8

    # --- Current conditions header ---
    if data.times and data.weather_code and data.temperature:
        icon = wmo_to_icon(data.weather_code[0])
        desc = wmo_to_description(data.weather_code[0])
        temp = f"{data.temperature[0]:.0f}°C"

        draw.text((pad, y), f"{icon} {temp}", fill=TEXT_COLOR, font=font_large)
        y += 24
        draw.text((pad, y), desc, fill=ACCENT_COLOR, font=font_medium)
        y += 18

    # Separator line
    draw.line([(pad, y), (width - pad, y)], fill=TEXT_COLOR, width=1)
    y += 6

    # --- Hourly rows (next 24h) ---
    max_rows = min(24, len(data.times))
    row_h = min(16, (height - y - 50) // max_rows) if max_rows > 0 else 16

    for i in range(max_rows):
        if y + row_h > height - 45:
            break

        time_str = data.times[i]
        hour = time_str.split("T")[1][:5] if "T" in time_str else time_str
        icon = wmo_to_icon(data.weather_code[i]) if i < len(data.weather_code) else ""
        temp = f"{data.temperature[i]:.0f}°" if i < len(data.temperature) else ""
        wind = f"{data.wind_speed[i]:.0f}m/s" if i < len(data.wind_speed) else ""

        draw.text((pad, y), hour, fill=TEXT_COLOR, font=font_small)
        draw.text((pad + 40, y), icon, fill=TEXT_COLOR, font=font_icon)
        draw.text((pad + 60, y), temp, fill=TEXT_COLOR, font=font_small)
        draw.text((pad + 95, y), wind, fill=TEXT_COLOR, font=font_small)

        y += row_h

    # --- Footer with model info ---
    y = height - 40
    draw.line([(pad, y), (width - pad, y)], fill=TEXT_COLOR, width=1)
    y += 4

    now_str = datetime.now().strftime("Updated: %H:%M")
    draw.text((pad, y), now_str, fill=TEXT_COLOR, font=font_small)
    y += 14
    if model_info:
        draw.text((pad, y), model_info, fill=TEXT_COLOR, font=font_small)

    return img
```

Also add these imports at the top of `chart_renderer.py`:
```python
from PIL import Image, ImageDraw, ImageFont
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_right_panel.py -v`
Expected: 2 passed

**Step 5: Commit**

```bash
git add src/plugins/meteogram/chart_renderer.py tests/test_right_panel.py
git commit -m "feat: add right panel 24h hourly sidebar with weather icons"
```

---

### Task 7: Compose Full Image and Wire Plugin

Combine left + right panels into final image. Wire everything into the `Meteogram` plugin class.

**Files:**
- Modify: `src/plugins/meteogram/chart_renderer.py` (add `render_full_meteogram`)
- Modify: `src/plugins/meteogram/meteogram.py` (implement `generate_image`)
- Create: `tests/test_meteogram_plugin.py`

**Step 1: Write the failing test**

Create `tests/test_meteogram_plugin.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image
from plugins.meteogram.meteogram import Meteogram


SAMPLE_RESPONSE = {
    "generationtime_ms": 1.5,
    "hourly": {
        "time": [f"2026-02-24T{h:02d}:00" for h in range(24)]
              + [f"2026-02-25T{h:02d}:00" for h in range(24)],
        "temperature_2m": [5.0 + i * 0.1 for i in range(48)],
        "precipitation": [0.0] * 48,
        "wind_speed_10m": [3.0] * 48,
        "wind_gusts_10m": [6.0] * 48,
        "pressure_msl": [1013.0] * 48,
        "cloud_cover": [50] * 48,
        "weather_code": [3] * 48,
    },
}


def _mock_device_config():
    config = MagicMock()
    config.get_resolution.return_value = (800, 480)
    config.get_config.return_value = "horizontal"
    return config


@patch("plugins.meteogram.data_fetcher.requests.get")
def test_generate_image_returns_correct_size(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = SAMPLE_RESPONSE
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp

    plugin_config = {"id": "meteogram"}
    plugin = Meteogram(plugin_config)
    img = plugin.generate_image({}, _mock_device_config())
    assert isinstance(img, Image.Image)
    assert img.size == (800, 480)
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_meteogram_plugin.py -v`
Expected: FAIL

**Step 3: Add render_full_meteogram to chart_renderer.py**

Add to `src/plugins/meteogram/chart_renderer.py`:
```python
def render_full_meteogram(
    ecmwf: ModelData,
    metno: Optional[ModelData],
    dimensions: tuple,
) -> Image.Image:
    """Compose the full 800x480 image: left meteogram + right sidebar."""
    total_w, total_h = dimensions
    left_w = int(total_w * 0.75)
    right_w = total_w - left_w

    # Render left panel (meteogram charts)
    left_img = render_meteogram(ecmwf, metno, dimensions)

    # Render right panel (24h detail) using the best short-range data
    sidebar_data = metno if metno else ecmwf
    model_info = f"ECMWF"
    if metno:
        model_info = f"ECMWF + MetNo"
    right_img = render_right_panel(sidebar_data, right_w, total_h, model_info)

    # Composite
    full_img = left_img.copy()
    full_img.paste(right_img, (left_w, 0))

    return full_img
```

**Step 4: Update meteogram.py with full implementation**

Replace `src/plugins/meteogram/meteogram.py`:
```python
import logging
import os
from plugins.base_plugin.base_plugin import BasePlugin
from plugins.meteogram.data_fetcher import fetch_ecmwf, fetch_metno
from plugins.meteogram.chart_renderer import render_full_meteogram
from plugins.meteogram.cache import MeteogramCache
from PIL import Image

logger = logging.getLogger(__name__)


class Meteogram(BasePlugin):
    def __init__(self, config, **dependencies):
        super().__init__(config, **dependencies)
        cache_path = os.path.join(self.get_plugin_dir(), "cache.json")
        self.cache = MeteogramCache(cache_path)

    def generate_image(self, settings, device_config):
        dimensions = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]

        # Fetch both models
        ecmwf = fetch_ecmwf()
        metno = fetch_metno()

        if ecmwf is None:
            logger.error("ECMWF fetch failed, cannot render meteogram")
            return self._fallback_image(dimensions)

        # Check cache — skip render if data unchanged
        ecmwf_gen = ecmwf.generation_time or 0
        metno_gen = metno.generation_time if metno else 0

        ecmwf_new = self.cache.has_new_data("ECMWF", ecmwf_gen)
        metno_new = self.cache.has_new_data("MetNo", metno_gen)

        if not ecmwf_new and not metno_new:
            cached_path = self.cache.get_last_image()
            if cached_path and os.path.exists(cached_path):
                logger.info("No new model data, returning cached image")
                return Image.open(cached_path).convert("RGB")

        # Render fresh meteogram
        img = render_full_meteogram(ecmwf, metno, dimensions)

        # Update cache
        self.cache.update("ECMWF", ecmwf_gen)
        if metno:
            self.cache.update("MetNo", metno_gen)

        # Save cached image
        cache_img_path = os.path.join(self.get_plugin_dir(), "last_meteogram.png")
        img.save(cache_img_path)
        self.cache.set_last_image(cache_img_path)

        return img

    def _fallback_image(self, dimensions):
        from PIL import ImageDraw
        img = Image.new("RGB", dimensions, "white")
        draw = ImageDraw.Draw(img)
        draw.text((20, 20), "Meteogram: API unavailable", fill="black")
        return img
```

**Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_meteogram_plugin.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/plugins/meteogram/meteogram.py src/plugins/meteogram/chart_renderer.py tests/test_meteogram_plugin.py
git commit -m "feat: wire full meteogram plugin with caching and dual-model rendering"
```

---

### Task 8: Settings Page

Minimal settings form for the InkyPi web UI.

**Files:**
- Create: `src/plugins/meteogram/settings.html`

**Step 1: Create settings.html**

Create `src/plugins/meteogram/settings.html`:
```html
<div class="form-group">
    <label>Temperature Units</label>
    <select name="temp_units" class="form-control">
        <option value="celsius">Celsius (°C)</option>
        <option value="fahrenheit">Fahrenheit (°F)</option>
    </select>
</div>

<div class="form-group">
    <label>Wind Units</label>
    <select name="wind_units" class="form-control">
        <option value="ms">m/s</option>
        <option value="kmh">km/h</option>
        <option value="knots">knots</option>
    </select>
</div>

<div class="form-group">
    <label>Forecast Range (days)</label>
    <select name="forecast_days" class="form-control">
        <option value="7">7 days</option>
        <option value="10" selected>10 days</option>
        <option value="14">14 days</option>
    </select>
</div>

<div class="form-group">
    <label>
        <input type="checkbox" name="show_cloud_cover" value="true" checked>
        Show cloud cover
    </label>
</div>

<div class="form-group">
    <label>
        <input type="checkbox" name="show_gusts" value="true" checked>
        Show wind gusts
    </label>
</div>

<script>
if (typeof loadPluginSettings !== 'undefined' && loadPluginSettings) {
    var s = pluginSettings;
    if (s.temp_units) document.querySelector('[name="temp_units"]').value = s.temp_units;
    if (s.wind_units) document.querySelector('[name="wind_units"]').value = s.wind_units;
    if (s.forecast_days) document.querySelector('[name="forecast_days"]').value = s.forecast_days;
    if (s.show_cloud_cover === "false") document.querySelector('[name="show_cloud_cover"]').checked = false;
    if (s.show_gusts === "false") document.querySelector('[name="show_gusts"]').checked = false;
}
</script>
```

**Step 2: Commit**

```bash
git add src/plugins/meteogram/settings.html
git commit -m "feat: add settings page for meteogram plugin"
```

---

### Task 9: Create Plugin Icon

Create a simple icon for the InkyPi web interface.

**Files:**
- Create: `src/plugins/meteogram/icon.png`

**Step 1: Generate a 128x128 icon using PIL**

Write a short Python script to generate the icon locally:

```python
from PIL import Image, ImageDraw
img = Image.new("RGB", (128, 128), "white")
draw = ImageDraw.Draw(img)
# Simple chart icon: axis lines + colored traces
draw.line([(15, 110), (15, 15)], fill="black", width=2)  # Y axis
draw.line([(15, 110), (115, 110)], fill="black", width=2)  # X axis
# ECMWF trace (blue)
points_blue = [(20, 80), (40, 60), (60, 70), (80, 45), (100, 55)]
draw.line(points_blue, fill="blue", width=2)
# MetNo trace (red, shorter)
points_red = [(20, 75), (40, 55), (55, 65)]
draw.line(points_red, fill="red", width=2)
img.save("src/plugins/meteogram/icon.png")
```

Run this locally to produce the icon.

**Step 2: Commit**

```bash
git add src/plugins/meteogram/icon.png
git commit -m "feat: add meteogram plugin icon"
```

---

### Task 10: Integration Test — Full Render Pipeline

End-to-end test that verifies the complete pipeline from API mock to final image.

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write the integration test**

Create `tests/test_integration.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image
from plugins.meteogram.data_fetcher import fetch_ecmwf, fetch_metno
from plugins.meteogram.chart_renderer import render_full_meteogram


HOURS = 72
SAMPLE_ECMWF = {
    "generationtime_ms": 2.1,
    "hourly": {
        "time": [f"2026-02-{24 + h // 24}T{h % 24:02d}:00" for h in range(HOURS)],
        "temperature_2m": [2.0 + 10 * (h % 24) / 24 for h in range(HOURS)],
        "precipitation": [0.5 if h % 8 == 0 else 0.0 for h in range(HOURS)],
        "wind_speed_10m": [4.0 + 2 * (h % 12) / 12 for h in range(HOURS)],
        "wind_gusts_10m": [8.0 + 3 * (h % 12) / 12 for h in range(HOURS)],
        "pressure_msl": [1013.0 + 5 * (h % 24 - 12) / 12 for h in range(HOURS)],
        "cloud_cover": [30 + 40 * (h % 24) / 24 for h in range(HOURS)],
        "weather_code": [3 if h % 6 != 0 else 61 for h in range(HOURS)],
    },
}

METNO_HOURS = 48
SAMPLE_METNO = {
    "generationtime_ms": 1.0,
    "hourly": {
        "time": [f"2026-02-{24 + h // 24}T{h % 24:02d}:00" for h in range(METNO_HOURS)],
        "temperature_2m": [3.0 + 9 * (h % 24) / 24 for h in range(METNO_HOURS)],
        "precipitation": [0.3 if h % 6 == 0 else 0.0 for h in range(METNO_HOURS)],
        "wind_speed_10m": [3.5 + 1.5 * (h % 12) / 12 for h in range(METNO_HOURS)],
        "wind_gusts_10m": [7.0 + 2.5 * (h % 12) / 12 for h in range(METNO_HOURS)],
        "pressure_msl": [1014.0 + 4 * (h % 24 - 12) / 12 for h in range(METNO_HOURS)],
        "cloud_cover": [25 + 35 * (h % 24) / 24 for h in range(METNO_HOURS)],
        "weather_code": [2 if h % 6 != 0 else 80 for h in range(METNO_HOURS)],
    },
}


def _mock_response(json_data):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = json_data
    resp.raise_for_status.return_value = None
    return resp


@patch("plugins.meteogram.data_fetcher.requests.get")
def test_full_pipeline(mock_get):
    def side_effect(url, **kwargs):
        if "ecmwf" in url:
            return _mock_response(SAMPLE_ECMWF)
        return _mock_response(SAMPLE_METNO)
    mock_get.side_effect = side_effect

    ecmwf = fetch_ecmwf()
    metno = fetch_metno()

    assert ecmwf is not None
    assert metno is not None

    img = render_full_meteogram(ecmwf, metno, (800, 480))
    assert img.size == (800, 480)
    assert img.mode == "RGB"

    # Save for visual inspection
    img.save("tests/test_output_meteogram.png")
```

**Step 2: Run the integration test**

Run: `python -m pytest tests/test_integration.py -v`
Expected: PASS, and `tests/test_output_meteogram.png` written for visual inspection

**Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add full integration test for meteogram pipeline"
```

---

### Task 11: Deploy to Raspberry Pi

Copy the plugin to pogodynka.local and verify it works with InkyPi.

**Step 1: Copy plugin files to the Pi**

```bash
scp -r src/plugins/meteogram/ pogodynka.local:~/InkyPi/src/plugins/meteogram/
```

**Step 2: SSH in and install matplotlib dependency**

```bash
ssh pogodynka.local
source ~/.virtualenvs/pimoroni/bin/activate
pip install matplotlib
```

**Step 3: Restart InkyPi service**

```bash
sudo systemctl restart inkypi.service
```

**Step 4: Verify in web UI**

Open `http://pogodynka.local/` in browser. The "Meteogram" plugin should appear in the plugin list. Add it to a playlist and trigger a manual refresh.

**Step 5: Check logs if needed**

```bash
journalctl -u inkypi -n 50 -f
```

**Step 6: Commit deployment notes**

```bash
git add -A
git commit -m "docs: deployment verified on pogodynka.local"
```
