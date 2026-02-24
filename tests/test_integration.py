import pytest
from unittest.mock import patch, MagicMock
from PIL import Image
from plugins.meteogram.data_fetcher import fetch_ecmwf, fetch_icon_eu
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

ICON_EU_HOURS = 48
SAMPLE_ICON_EU = {
    "generationtime_ms": 1.0,
    "hourly": {
        "time": [f"2026-02-{24 + h // 24}T{h % 24:02d}:00" for h in range(ICON_EU_HOURS)],
        "temperature_2m": [3.0 + 9 * (h % 24) / 24 for h in range(ICON_EU_HOURS)],
        "precipitation": [0.3 if h % 6 == 0 else 0.0 for h in range(ICON_EU_HOURS)],
        "wind_speed_10m": [3.5 + 1.5 * (h % 12) / 12 for h in range(ICON_EU_HOURS)],
        "wind_gusts_10m": [7.0 + 2.5 * (h % 12) / 12 for h in range(ICON_EU_HOURS)],
        "pressure_msl": [1014.0 + 4 * (h % 24 - 12) / 12 for h in range(ICON_EU_HOURS)],
        "cloud_cover": [25 + 35 * (h % 24) / 24 for h in range(ICON_EU_HOURS)],
        "weather_code": [2 if h % 6 != 0 else 80 for h in range(ICON_EU_HOURS)],
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
        return _mock_response(SAMPLE_ICON_EU)
    mock_get.side_effect = side_effect

    ecmwf = fetch_ecmwf()
    icon_eu = fetch_icon_eu()

    assert ecmwf is not None
    assert icon_eu is not None

    img = render_full_meteogram(ecmwf, icon_eu, (800, 480))
    assert img.size == (800, 480)
    assert img.mode == "RGB"

    # Save for visual inspection
    img.save("tests/test_output_meteogram.png")
