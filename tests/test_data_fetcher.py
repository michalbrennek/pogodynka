import pytest
from unittest.mock import patch, MagicMock
from plugins.meteogram.data_fetcher import fetch_ecmwf, fetch_icon_eu, ModelData


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
def test_fetch_icon_eu_returns_model_data(mock_get):
    mock_get.return_value = _make_response(SAMPLE_RESPONSE)
    result = fetch_icon_eu(52.2858, 20.9329)
    assert isinstance(result, ModelData)
    assert result.model_name == "ICON-EU"


@patch("plugins.meteogram.data_fetcher.requests.get")
def test_fetch_ecmwf_handles_api_error(mock_get):
    mock_get.return_value = _make_response({}, status=500)
    mock_get.return_value.raise_for_status.side_effect = Exception("Server error")
    result = fetch_ecmwf(52.2858, 20.9329)
    assert result is None
