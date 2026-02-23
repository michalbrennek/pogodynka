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
