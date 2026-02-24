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


@patch("plugins.meteogram.meteogram.MeteogramCache")
@patch("plugins.meteogram.data_fetcher.requests.get")
def test_generate_image_returns_correct_size(mock_get, mock_cache_cls):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = SAMPLE_RESPONSE
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp

    mock_cache = MagicMock()
    mock_cache.has_new_data.return_value = True
    mock_cache.get_last_image.return_value = None
    mock_cache_cls.return_value = mock_cache

    plugin_config = {"id": "meteogram"}
    plugin = Meteogram(plugin_config)
    img = plugin.generate_image({}, _mock_device_config())
    assert isinstance(img, Image.Image)
    assert img.size == (800, 480)
