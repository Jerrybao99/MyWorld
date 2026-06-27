import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

FINANCIAL_DIR = DATA_DIR / "财务"
ANALYSIS_DIR = DATA_DIR / "分析"
HOLDING_DIR = DATA_DIR / "持股"
HOT_DIR = DATA_DIR / "热点"
CACHE_DIR = DATA_DIR / "缓存"
LOG_DIR = DATA_DIR / "日志"

for d in [FINANCIAL_DIR, ANALYSIS_DIR, HOLDING_DIR, HOT_DIR, CACHE_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

RETRY_MAX = 3
REQUEST_DELAY = 0.5
