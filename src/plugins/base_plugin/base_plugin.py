import os


class BasePlugin:
    """Minimal stub of the InkyPi BasePlugin for local development and testing."""

    def __init__(self, config, **dependencies):
        self.config = config
        self.dependencies = dependencies

    def get_plugin_dir(self):
        return os.path.dirname(os.path.abspath(__file__))
