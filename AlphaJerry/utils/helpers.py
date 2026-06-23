import pandas as pd
from pathlib import Path
from datetime import datetime


def today_str():
    return datetime.now().strftime("%y%m%d")


def read_xlsx(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    return pd.read_excel(path, dtype={"股票代码": str})


def write_xlsx(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(path, index=False)


def winsorize(series: pd.Series, lower: float = -5, upper: float = 5) -> pd.Series:
    return series.clip(lower, upper)
