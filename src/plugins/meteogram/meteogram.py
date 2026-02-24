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
