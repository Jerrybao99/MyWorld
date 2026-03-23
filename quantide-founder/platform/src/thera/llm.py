import os
import time
import logging
from typing import Optional, Dict, Any

try:
    import requests
except ImportError:
    raise ImportError("请先安装 requests: pip install requests")

from .config import Settings, load_config

logger = logging.getLogger(__name__)


def get_annotation(
    text: str, settings: Optional[Settings] = None, config_path: Optional[str] = None
) -> Optional[str]:
    if settings is None:
        if config_path is None:
            config_path = _get_default_config_path()
        settings = load_config(config_path)

    assert settings is not None
    url: str = f"{settings.deepseek_base_url}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }

    system_prompt = """阅读以下段落，判断其核心价值。

段落内容：
{text}

如果它包含洞察、决策或风险，请按以下格式输出批注(>)：

🤖 观察者注：[简短标识]

🏷️ 标签：#标签1 #标签2

💎 提炼：[提取的标准化知识]

⚠️ 状态：[状态说明]（可选）

🔗 关联：[关联说明]（可选）

🔑 关键：[关键要点]（可选）

🔄 模式：[模式说明]（可选）

注意：
1. 只输出批注内容，不修改用户原文
2. 不重写用户内容
3. 仅提供观察者视角的洞察
4. 提炼要简洁，不超过 50 字
5. 标签使用 # 前缀
6. 非必填项可省略
7. 如果段落仅为闲聊或无信息价值，输出：SKIP"""

    payload: Dict[str, Any] = {
        "model": settings.deepseek_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": system_prompt.format(text=text)},
        ],
        "temperature": 0.7,
        "max_tokens": 1000,
    }

    last_error = None
    for attempt in range(settings.deepseek_max_retries):
        try:
            response = requests.post(
                url, headers=headers, json=payload, timeout=settings.deepseek_timeout
            )
            response.raise_for_status()
            result = response.json()

            content = (
                result.get("choices", [{}])[0].get("message", {}).get("content", "")
            )
            if content.strip() == "SKIP":
                return None
            return content

        except requests.exceptions.RequestException as e:
            last_error = e
            logger.warning(
                f"API request failed (attempt {attempt + 1}/{settings.deepseek_max_retries}): {e}"
            )
            if attempt < settings.deepseek_max_retries - 1:
                time.sleep(settings.output_retry_delay)
                continue
            break
        except (KeyError, ValueError) as e:
            logger.error(f"Failed to parse API response: {e}")
            return None

    logger.error(f"Failed after {settings.deepseek_max_retries} retries: {last_error}")
    raise RuntimeError(
        f"LLM request failed after {settings.deepseek_max_retries} retries: {last_error}"
    )


def _get_default_config_path() -> str:
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.yaml"
    )
