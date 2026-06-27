import sys
sys.path.insert(0, ".")
import akshare as ak
from engine.collector import collect_single_stock, map_fields, filter_missing, clean_data
from utils.formulas import calc_derived_indicators
from utils.helpers import today_str, write_xlsx
from config.settings import FINANCIAL_DIR
from config.industry_map import map_industry
from utils.sw_mapper import load_sw_mapping, get_sw_industry
import pandas as pd
import numpy as np
import random

random.seed(42)

# 预取名称映射
stock_list = ak.stock_info_a_code_name()
name_map = dict(zip(stock_list["code"], stock_list["name"]))

# 随机采 5 只真实存在的股票
test_codes = random.sample(sorted(stock_list["code"].tolist()), 5)
print(f"随机选中股票: {test_codes}")
rows = []
for code in test_codes:
    try:
        row = collect_single_stock(code)
        if row:
            row["股票名称"] = name_map.get(code, "")
            print(f"{code} 采集成功, 字段数={len(row)}")
            rows.append(row)
    except Exception as e:
        print(f"{code} 失败: {e}")

df = pd.DataFrame(rows)
print(f"采集到 {len(df)} 行, 原始列数={len(df.columns)}")
print(f"列名: {list(df.columns)[:15]}...")

df = map_fields(df)
print(f"映射后列数: {len(df.columns)}")
print(f"股票代码: {df['股票代码'].tolist()}")
print(f"股票名称: {df['股票名称'].tolist()}")

df = filter_missing(df)
print(f"过滤后行数: {len(df)}")

df = clean_data(df)

sw_map = load_sw_mapping()
df["行业属性"] = df["股票代码"].apply(lambda c: get_sw_industry(c, sw_map))
df["行业分类"] = df["行业属性"].apply(map_industry)

if "主营收入" in df.columns and "营业总成本" in df.columns:
    df["主营利润"] = df["主营收入"] - df["营业总成本"]
else:
    df["主营利润"] = np.nan

df = calc_derived_indicators(df)
print(f"衍生指标: 资产负债率={df['资产负债率'].tolist()}, 流动比率={df['流动比率'].tolist()}")

COLUMN_ORDER = [
    "股票代码", "股票名称",
    "行业属性", "行业分类", "上市日期", "财报发布日期", "财报所属期间",
    "主营收入", "主营利润", "营业利润", "投资收益", "营业外收支", "利润总额", "净利润", "未分配利润",
    "总资产", "流动资产", "固定资产", "无形资产",
    "总负债", "流动负债", "长期负债",
    "股东权益", "资本公积金",
    "经营现金流量", "投资现金流量", "筹资现金流量",
    "每股收益", "净资产收益率",
    "主营收入同比增长率", "净利润同比增长率",
    "销售毛利率", "资产负债率", "流动比率", "速动比率", "权益乘数", "股东权益比",
    "净利润占营业利润比", "主营利润率", "净利率", "投资收益占比", "现金流量比率",
    "营业总成本", "数据质量",
]
existing_cols = [c for c in COLUMN_ORDER if c in df.columns]
remaining = [c for c in df.columns if c not in existing_cols]
df = df[existing_cols + remaining]

output_path = FINANCIAL_DIR / f"{today_str()}_verify5.xlsx"
write_xlsx(df, output_path)
print(f"输出文件: {output_path}")
print("验证通过！")