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
