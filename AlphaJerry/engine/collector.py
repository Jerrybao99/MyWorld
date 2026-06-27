import time
import pandas as pd
import numpy as np
from pathlib import Path

import akshare as ak

from config.settings import FINANCIAL_DIR, LOG_DIR, RETRY_MAX, REQUEST_DELAY
from utils.formulas import calc_derived_indicators
from utils.helpers import today_str, write_xlsx
from config.industry_map import map_industry
from utils.sw_mapper import load_sw_mapping, get_sw_industry

REQUIRED_FIELDS = ["股票代码", "股票名称", "主营收入", "净利润", "总资产", "总负债", "股东权益", "流动资产", "流动负债", "经营现金流量", "行业分类", "财报发布日期", "财报所属期间", "上市日期"]
DEFAULT_ZERO_FIELDS = ["投资收益", "营业外收支", "长期负债", "固定资产", "无形资产", "投资现金流量", "筹资现金流量"]

FIELD_MAP = {
    "code": "股票代码", 
    "name": "股票名称",
    "operating_income_total": "主营收入",
    "operating_profit": "营业利润",
    "profit_total": "利润总额",
    "net_profit": "净利润",
    "assets_total": "总资产",
    "total_debt": "总负债",
    "total_current_assets": "流动资产",
    "current_total_debt": "流动负债",
    "non_current_debt_total": "长期负债",
    "fixed_assets_total": "固定资产",
    "intangible_assets": "无形资产",
    "holder_equity_total": "股东权益",
    "capital_reserve": "资本公积金",
    "undistributed_profits": "未分配利润",
    "act_cash_flow_net": "经营现金流量",
    "invest_cash_flow_net": "投资现金流量",
    "financing_cash_flow_net": "筹资现金流量",
    "basic_eps": "每股收益",
    "invest_income": "投资收益",
    "operating_costs_total": "营业总成本",
    "ListDate": "上市日期",
    "行业属性": "行业属性",
    "PubDate": "财报发布日期",
}

# 三张报表各自需要提取的字段列表

THS_DEBT_METRICS = [
    "assets_total", "total_debt", "holder_equity_total",
    "total_current_assets", "current_total_debt",
    "fixed_assets_total", "intangible_assets",
    "non_current_debt_total", "capital_reserve",
    "undistributed_profits",
]
THS_BENEFIT_METRICS = [
    "operating_income_total", "operating_profit",
    "net_profit", "profit_total", "invest_income",
    "basic_eps", "operating_costs_total",
]
THS_CASH_METRICS = [
    "act_cash_flow_net", "invest_cash_flow_net",
    "financing_cash_flow_net",
]


def _extract_from_ths(df: pd.DataFrame, metrics: list, extract_yoy: bool = False) -> dict:
    if df is None or df.empty:
        return {}
    latest_date = df["report_date"].max()
    latest = df[df["report_date"] == latest_date]
    row = {}
    row["PubDate"] = str(latest_date)
    for _, r in latest.iterrows():
        if r["metric_name"] in metrics:
            val = r["value"]
            try:
                val = float(val) if val and val != "" else np.nan
            except (ValueError, TypeError):
                pass
            row[r["metric_name"]] = val
            if extract_yoy and pd.notna(r.get("yoy")):
                yoy_val = r["yoy"]
                try:
                    yoy_val = float(yoy_val) if yoy_val and yoy_val != "" else np.nan
                except (ValueError, TypeError):
                    pass
                row[f"{r['metric_name']}_yoy"] = yoy_val
    return row


def map_fields(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.rename(columns=FIELD_MAP, inplace=True)
    existing = [c for c in set(FIELD_MAP.values()) if c in df.columns]
    return df[existing]


def filter_missing(df: pd.DataFrame) -> pd.DataFrame:
    available = [f for f in REQUIRED_FIELDS if f in df.columns]
    before = len(df)
    df = df.dropna(subset=available)
    after = len(df)
    if before > after:
        print(f"  丢弃 {before - after} 条缺失必填字段的记录")
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in DEFAULT_ZERO_FIELDS:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    if "主营收入同比增长率" in df.columns:
        df["主营收入同比增长率"] = df["主营收入同比增长率"].clip(upper=500)
    if "净利润同比增长率" in df.columns:
        df["净利润同比增长率"] = df["净利润同比增长率"].clip(upper=500)
    if "总资产" in df.columns:
        df = df[df["总资产"] > 0]
    if "股东权益" in df.columns:
        df = df[df["股东权益"] > 0]
    if "主营收入" in df.columns:
        df = df[df["主营收入"] > 0]
    return df


def collect_single_stock(code: str) -> dict | None:
    row = {"股票代码": code}

    for attempt in range(RETRY_MAX):
        try:
            debt = ak.stock_financial_debt_new_ths(symbol=code, indicator="按报告期")
            row.update(_extract_from_ths(debt, THS_DEBT_METRICS))

            benefit = ak.stock_financial_benefit_new_ths(symbol=code, indicator="按报告期")
            row.update(_extract_from_ths(benefit, THS_BENEFIT_METRICS, extract_yoy=True))

            cash = ak.stock_financial_cash_new_ths(symbol=code, indicator="按报告期")
            row.update(_extract_from_ths(cash, THS_CASH_METRICS))

            profile = ak.stock_profile_cninfo(symbol=code)
            if profile is not None and not profile.empty:
                row["ListDate"] = str(profile["上市日期"].iloc[0]) if "上市日期" in profile.columns else ""

            if "operating_income_total_yoy" in row:
                row["主营收入同比增长率"] = row.pop("operating_income_total_yoy")
            if "net_profit_yoy" in row:
                row["净利润同比增长率"] = row.pop("net_profit_yoy")

            return row

        except Exception as e:
            if attempt < RETRY_MAX - 1:
                time.sleep(REQUEST_DELAY * (attempt + 1))
            else:
                _log_failure(code, str(e))
                return None


def _log_failure(code: str, error: str):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_DIR / "failures.log", "a", encoding="utf-8") as f:
        f.write(f"{today_str()} | {code} | {error}\n")


def collect_all(output_path: Path | None = None):
    print("获取全部 A 股列表...")
    stock_list = ak.stock_info_a_code_name()
    name_map = dict(zip(stock_list["code"], stock_list["name"]))
    codes = list(name_map.keys())
    total = len(codes)
    print(f"共 {total} 只股票，开始采集...")

    rows = []
    for i, code in enumerate(codes):
        if (i + 1) % 100 == 0:
            print(f"  进度: {i+1}/{total}")
        row = collect_single_stock(code)
        if row:
            row["股票名称"] = name_map.get(code, "")
            rows.append(row)
        time.sleep(REQUEST_DELAY)

    df = pd.DataFrame(rows)
    df = map_fields(df)

    sw_map = load_sw_mapping()
    if "行业属性" not in df.columns:
        df["行业属性"] = ""
    df["行业属性"] = df["股票代码"].apply(lambda c: get_sw_industry(c, sw_map))
    df["行业分类"] = df["行业属性"].apply(map_industry)

    if "主营收入" in df.columns and "营业总成本" in df.columns:
        df["主营利润"] = df["主营收入"] - df["营业总成本"]
    else:
        df["主营利润"] = np.nan

    df["财报所属期间"] = ""
    df["财报发布日期"] = df.get("财报发布日期", "").fillna("")

    df = filter_missing(df)
    df = clean_data(df)
    df = calc_derived_indicators(df)

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

    if output_path is None:
        output_path = FINANCIAL_DIR / f"{today_str()}.xlsx"
    write_xlsx(df, output_path)
    print(f"采集完成：{len(df)} 条记录 → {output_path}")
    return df


if __name__ == "__main__":
    collect_all()
