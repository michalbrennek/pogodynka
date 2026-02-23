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
