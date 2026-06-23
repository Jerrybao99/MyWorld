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
    df["ALR"] = df.apply(lambda r: safe_divide(r["TL"], r["TA"]), axis=1)
    df["CR"] = df.apply(lambda r: safe_divide(r["CA"], r["CL"]), axis=1)
    df["QR"] = df["CR"]
    df["EM"] = df.apply(lambda r: safe_divide(r["TA"], r["SE"]), axis=1)
    df["NPR"] = df.apply(lambda r: safe_divide(r["NP"], r["OP"]), axis=1)
    df["OPM"] = df.apply(lambda r: safe_divide(r["GP"], r["Rev"]), axis=1)
    df["NPM"] = df.apply(lambda r: safe_divide(r["NP"], r["Rev"]), axis=1)
    df["IPR"] = df.apply(lambda r: safe_divide(r["InvP"], r["OP"]), axis=1)
    df["CFR"] = df.apply(lambda r: safe_divide(r["OCF"], r["CL"]), axis=1)
    df["EQ_TA"] = df.apply(lambda r: safe_divide(r["SE"], r["TA"]), axis=1)

    na_count = df[["ALR", "CR", "QR", "EM", "NPR", "OPM", "NPM", "IPR", "CFR"]].isna().sum(axis=1)
    df["QualityFlag"] = na_count
    return df
