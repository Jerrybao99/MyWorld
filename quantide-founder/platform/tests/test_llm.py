import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from thera.llm import get_annotation
from thera.config import Settings


class TestLLM:
    def test_get_annotation_success(self):
        settings = Settings()
        settings.deepseek_api_key = "test_key"
        settings.deepseek_base_url = "https://api.deepseek.com"
        settings.deepseek_model = "deepseek-chat"
        settings.deepseek_max_retries = 1
        settings.deepseek_timeout = 30
        settings.output_retry_delay = 0

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "测试批注内容"}}]
        }

        with patch("thera.llm.requests.post", return_value=mock_response):
            result = get_annotation("测试段落内容", settings=settings)
            assert result == "测试批注内容"

    def test_get_annotation_skip(self):
        settings = Settings()
        settings.deepseek_api_key = "test_key"
        settings.deepseek_base_url = "https://api.deepseek.com"
        settings.deepseek_model = "deepseek-chat"
        settings.deepseek_max_retries = 1
        settings.deepseek_timeout = 30
        settings.output_retry_delay = 0

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "SKIP"}}]
        }

        with patch("thera.llm.requests.post", return_value=mock_response):
            result = get_annotation("闲聊内容", settings=settings)
            assert result is None

    def test_get_annotation_retry_on_failure(self):
        import requests

        settings = Settings()
        settings.deepseek_api_key = "test_key"
        settings.deepseek_base_url = "https://api.deepseek.com"
        settings.deepseek_model = "deepseek-chat"
        settings.deepseek_max_retries = 3
        settings.deepseek_timeout = 30
        settings.output_retry_delay = 0
        Settings._instance = None

        call_count = [0]

        def mock_post(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                raise requests.exceptions.RequestException("Network error")
            mock_resp = MagicMock()
            mock_resp.json.return_value = {
                "choices": [{"message": {"content": "成功"}}]
            }
            return mock_resp

        with patch("thera.llm.requests.post", side_effect=mock_post):
            with patch("thera.llm.time.sleep"):
                result = get_annotation("测试内容", settings=settings)
                assert result == "成功"

    def test_get_annotation_max_retries_exceeded(self):
        import requests

        settings = Settings()
        settings.deepseek_api_key = "test_key"
        settings.deepseek_base_url = "https://api.deepseek.com"
        settings.deepseek_model = "deepseek-chat"
        settings.deepseek_max_retries = 2
        settings.deepseek_timeout = 30
        settings.output_retry_delay = 0
        Settings._instance = None

        with patch(
            "thera.llm.requests.post",
            side_effect=requests.exceptions.RequestException("Network error"),
        ):
            with patch("thera.llm.time.sleep"):
                with pytest.raises(
                    RuntimeError, match="LLM request failed after .* retries"
                ):
                    get_annotation("测试内容", settings=settings)
