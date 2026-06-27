import pandas as pd
import numpy as np
from utils.formulas import safe_divide, calc_derived_indicators


def test_safe_divide_normal():
    assert safe_divide(10, 2) == 5.0


def test_safe_divide_zero_denom():
    assert safe_divide(10, 0) is None


def test_safe_divide_negative_denom():
    assert safe_divide(10, -1) is None


def test_calc_derived_indicators():
    df = pd.DataFrame([{
        "总负债": 100, "总资产": 200, "流动资产": 50, "流动负债": 25,
        "股东权益": 100, "净利润": 30, "营业利润": 40, "主营收入": 200,
        "主营利润": 80, "投资收益": 5, "经营现金流量": 20,
    }])
    result = calc_derived_indicators(df)
    assert result.loc[0, "资产负债率"] == 50.0
    assert result.loc[0, "流动比率"] == 2.0
    assert result.loc[0, "权益乘数"] == 2.0
    assert result.loc[0, "净利润占营业利润比"] == 75.0
    assert result.loc[0, "主营利润率"] == 40.0
    assert result.loc[0, "净利率"] == 15.0
    assert result.loc[0, "投资收益占比"] == 12.5
    assert result.loc[0, "现金流量比率"] == 80.0