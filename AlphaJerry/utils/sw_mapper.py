import json
import time
from pathlib import Path

import akshare as ak
import pandas as pd

from config.settings import CACHE_DIR
from config.industry_map import SW_TO_GROUP, DEFAULT_GROUP

SW_CACHE_PATH = CACHE_DIR / "sw_mapping.json"
SW_FIRST_CODES = [
    "801010", "801030", "801040", "801050", "801080", "801110", "801120",
    "801130", "801140", "801150", "801160", "801170", "801180", "801200",
    "801210", "801230", "801710", "801720", "801730", "801740", "801750",
    "801760", "801770", "801780", "801790", "801880", "801890", "801950",
    "801960", "801970", "801980",
]


def build_sw_mapping() -> dict:
    mapping = {}
    total = len(SW_FIRST_CODES)
    print(f"构建申万行业映射，共 {total} 个一级行业...")

    info = ak.sw_index_first_info()
    code_to_name = {}
    for _, r in info.iterrows():
        raw_code = str(r["行业代码"])
        code = raw_code.replace(".SI", "")
        code_to_name[code] = str(r["行业名称"])

    for i, code in enumerate(SW_FIRST_CODES):
        try:
            df = ak.index_component_sw(symbol=code)
            industry_name = code_to_name.get(code, "")
            for _, r in df.iterrows():
                stock_code = str(r["证券代码"]).zfill(6)
                mapping[stock_code] = industry_name
            print(f"  [{i+1}/{total}] {code} {industry_name}: {len(df)} 只")
            time.sleep(0.3)
        except Exception as e:
            print(f"  [{i+1}/{total}] {code} 失败: {e}")
            time.sleep(1)
    print(f"映射完成: {len(mapping)} 只股票")
    return mapping


def load_sw_mapping(force_rebuild: bool = False) -> dict:
    if not force_rebuild and SW_CACHE_PATH.exists():
        try:
            with open(SW_CACHE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"加载申万缓存: {len(data)} 只股票")
            return data
        except Exception:
            pass
    mapping = build_sw_mapping()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(SW_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False)
    print(f"缓存已保存: {SW_CACHE_PATH}")
    return mapping


def get_sw_industry(code: str, mapping: dict | None = None) -> str:
    if mapping is None:
        mapping = load_sw_mapping()
    code = str(code).zfill(6)
    return mapping.get(code, "")


def get_industry_group(sw_industry: str) -> str:
    return SW_TO_GROUP.get(sw_industry, DEFAULT_GROUP)


if __name__ == "__main__":
    mapping = load_sw_mapping(force_rebuild=True)
    test_codes = ["600000", "600519", "000858", "002415", "300750", "601857"]
    for c in test_codes:
        ind = mapping.get(c, "未找到")
        grp = get_industry_group(ind)
        print(f"{c}: {ind} → {grp}")
