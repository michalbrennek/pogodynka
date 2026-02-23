from plugins.meteogram.weather_icons import wmo_to_icon, wmo_to_description


def test_clear_sky():
    assert wmo_to_icon(0) is not None
    assert wmo_to_description(0) == "Clear"


def test_rain_codes():
    assert wmo_to_icon(61) is not None
    assert wmo_to_icon(63) is not None
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
