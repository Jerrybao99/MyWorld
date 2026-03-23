import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from thera.config import Settings, load_config


class TestConfig:
    def test_settings_singleton(self):
        settings1 = Settings.get_instance()
        settings2 = Settings.get_instance()
        assert settings1 is settings2

    def test_settings_default_values(self):
        settings = Settings()
        assert settings.deepseek_base_url == "https://api.deepseek.com"
        assert settings.deepseek_model == "deepseek-chat"
        assert settings.deepseek_max_retries == 3
        assert settings.deepseek_timeout == 30
        assert settings.filter_min_paragraph_length == 20
        assert settings.filter_annotation_marker == "🤖 观察者注"

    def test_load_config_from_yaml(self, tmp_path):
        config_content = """
deepseek:
  api_key: test_key
  base_url: "https://test.api.com"
  model: "test-model"
  max_retries: 5
  timeout: 60

filter:
  min_paragraph_length: 30
  annotation_marker: "test marker"

output:
  max_retries: 2
  retry_delay: 2
"""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(config_content)

        settings = load_config(str(config_file))
        assert settings.deepseek_api_key == "test_key"
        assert settings.deepseek_base_url == "https://test.api.com"
        assert settings.deepseek_model == "test-model"
        assert settings.deepseek_max_retries == 5
        assert settings.deepseek_timeout == 60
        assert settings.filter_min_paragraph_length == 30
        assert settings.filter_annotation_marker == "test marker"
        assert settings.output_max_retries == 2
        assert settings.output_retry_delay == 2

    def test_load_config_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/config.yaml")
