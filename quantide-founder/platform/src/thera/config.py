import os
import yaml
from pathlib import Path
from typing import Optional


class Settings:
    _instance: Optional["Settings"] = None

    def __init__(self):
        self.deepseek_api_key: str = ""
        self.deepseek_base_url: str = "https://api.deepseek.com"
        self.deepseek_model: str = "deepseek-chat"
        self.deepseek_max_retries: int = 3
        self.deepseek_timeout: int = 30
        self.filter_min_paragraph_length: int = 20
        self.filter_annotation_marker: str = "🤖 观察者注"
        self.output_max_retries: int = 3
        self.output_retry_delay: int = 1

    @classmethod
    def get_instance(cls) -> "Settings":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_from_yaml(self, config_path: str) -> None:
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_file, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        deepseek_config = config_data.get("deepseek", {})
        self.deepseek_api_key = os.environ.get(
            "DEEPSEEK_API_KEY", deepseek_config.get("api_key", "")
        )
        self.deepseek_base_url = deepseek_config.get(
            "base_url", "https://api.deepseek.com"
        )
        self.deepseek_model = deepseek_config.get("model", "deepseek-chat")
        self.deepseek_max_retries = deepseek_config.get("max_retries", 3)
        self.deepseek_timeout = deepseek_config.get("timeout", 30)

        filter_config = config_data.get("filter", {})
        self.filter_min_paragraph_length = filter_config.get("min_paragraph_length", 20)
        self.filter_annotation_marker = filter_config.get(
            "annotation_marker", "🤖 观察者注"
        )

        output_config = config_data.get("output", {})
        self.output_max_retries = output_config.get("max_retries", 3)
        self.output_retry_delay = output_config.get("retry_delay", 1)


def load_config(config_path: str) -> Settings:
    settings = Settings.get_instance()
    settings.load_from_yaml(config_path)
    return settings
