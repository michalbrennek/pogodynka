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
    assert cache.has_new_data("ICON-EU", 2.0) is True


def test_cache_stores_and_detects_same_data(cache_file):
    cache = MeteogramCache(cache_file)
    cache.update("ECMWF", 1.5)
    cache.update("ICON-EU", 2.0)
    assert cache.has_new_data("ECMWF", 1.5) is False
    assert cache.has_new_data("ICON-EU", 2.0) is False


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
