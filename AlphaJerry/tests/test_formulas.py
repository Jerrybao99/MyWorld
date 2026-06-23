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
        "TL": 100, "TA": 200, "CA": 50, "CL": 25,
        "SE": 100, "NP": 30, "OP": 40, "Rev": 200,
        "GP": 80, "InvP": 5, "OCF": 20,
    }])
    result = calc_derived_indicators(df)
    assert result.loc[0, "ALR"] == 50.0
    assert result.loc[0, "CR"] == 2.0
    assert result.loc[0, "EM"] == 2.0
    assert result.loc[0, "NPR"] == 75.0
    assert result.loc[0, "OPM"] == 40.0
    assert result.loc[0, "NPM"] == 15.0
    assert result.loc[0, "IPR"] == 12.5
    assert result.loc[0, "CFR"] == 80.0