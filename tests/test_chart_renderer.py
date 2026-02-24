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
    icon_eu = _make_model_data("ICON-EU", 48)
    img = render_meteogram(ecmwf, icon_eu, (800, 480))
    assert isinstance(img, Image.Image)
    assert img.size == (800, 480)


def test_render_meteogram_without_icon_eu():
    ecmwf = _make_model_data("ECMWF", 48)
    img = render_meteogram(ecmwf, None, (800, 480))
    assert isinstance(img, Image.Image)
    assert img.size == (800, 480)


def test_render_meteogram_rgb_mode():
    ecmwf = _make_model_data("ECMWF", 48)
    icon_eu = _make_model_data("ICON-EU", 48)
    img = render_meteogram(ecmwf, icon_eu, (800, 480))
    assert img.mode == "RGB"
