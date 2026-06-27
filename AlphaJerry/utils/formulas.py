import pandas as pd
import numpy as np


def safe_divide(a, b):
    if b is None or b == 0 or (isinstance(b, float) and np.isnan(b)):
        return None
    a_is_na = a is None or (isinstance(a, float) and np.isnan(a))
    if a_is_na:
        return None
    if b < 0:
        return None
    result = a / b
    if abs(result) > 10:
        return np.clip(result, -10, 10)
    return round(result * 100, 2) if result < 1 else round(result, 2)


def calc_derived_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["资产负债率"] = df.apply(lambda r: safe_divide(r["总负债"], r["总资产"]), axis=1)
    df["流动比率"] = df.apply(lambda r: safe_divide(r["流动资产"], r["流动负债"]), axis=1)
    df["速动比率"] = df["流动比率"]
    df["权益乘数"] = df.apply(lambda r: safe_divide(r["总资产"], r["股东权益"]), axis=1)
    df["净利润占营业利润比"] = df.apply(lambda r: safe_divide(r["净利润"], r["营业利润"]), axis=1)
    df["主营利润率"] = df.apply(lambda r: safe_divide(r["主营利润"], r["主营收入"]), axis=1)
    df["净利率"] = df.apply(lambda r: safe_divide(r["净利润"], r["主营收入"]), axis=1)
    df["投资收益占比"] = df.apply(lambda r: safe_divide(r["投资收益"], r["营业利润"]), axis=1)
    df["现金流量比率"] = df.apply(lambda r: safe_divide(r["经营现金流量"], r["流动负债"]), axis=1)
    df["股东权益比"] = df.apply(lambda r: safe_divide(r["股东权益"], r["总资产"]), axis=1)
    df["销售毛利率"] = df.apply(lambda r: safe_divide(r["主营利润"], r["主营收入"]), axis=1)
    df["净资产收益率"] = df.apply(lambda r: safe_divide(r["净利润"], r["股东权益"]), axis=1)

    na_count = df[["资产负债率", "流动比率", "速动比率", "权益乘数", "净利润占营业利润比", "主营利润率", "净利率", "投资收益占比", "现金流量比率", "销售毛利率", "净资产收益率"]].isna().sum(axis=1)
    df["数据质量"] = na_count
    return df
