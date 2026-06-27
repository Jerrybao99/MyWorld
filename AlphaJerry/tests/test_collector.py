import pandas as pd
import numpy as np
from engine.collector import map_fields, filter_missing, clean_data

# 验证 `collector.py` 中三个不依赖网络不调 akshare 的纯数据处理函数
# 采用 mock 数据单元测试，采集流水线中数据清洗环节的正确性

# 验证字段重命名映射正确
def test_map_fields():
    raw = pd.DataFrame([{
        "Code": "600000", "Name": "浦发银行",
        "operating_income_total": 263952, "operating_profit": 10284,
        "net_profit": 9397, "assets_total": 492021,
        "total_debt": 73865, "holder_equity_total": 186236,
        "total_current_assets": 384157, "current_total_debt": 18218,
        "act_cash_flow_net": -67670,
    }])
    result = map_fields(raw)
    assert result.loc[0, "股票代码"] == "600000"
    assert result.loc[0, "股票名称"] == "浦发银行"
    assert result.loc[0, "主营收入"] == 263952
    assert result.loc[0, "营业利润"] == 10284
    assert result.loc[0, "净利润"] == 9397
    assert result.loc[0, "总资产"] == 492021
    assert result.loc[0, "总负债"] == 73865
    assert result.loc[0, "股东权益"] == 186236
    assert result.loc[0, "流动资产"] == 384157
    assert result.loc[0, "流动负债"] == 18218
    assert result.loc[0, "经营现金流量"] == -67670

# 验证缺失值过滤
def test_filter_missing():
    df = pd.DataFrame([
        {"股票代码": "600000", "股票名称": "A", "主营收入": 100, "净利润": 10, "总资产": 200, "总负债": 100, "股东权益": 100, "流动资产": 50, "流动负债": 25, "经营现金流量": 5, "行业分类": "银行", "财报发布日期": "20251025", "财报所属期间": "三季报", "上市日期": "20121009"},
        {"股票代码": "600001", "股票名称": None, "主营收入": 100, "净利润": 10, "总资产": 200, "总负债": 100, "股东权益": 100, "流动资产": 50, "流动负债": 25, "经营现金流量": 5, "行业分类": "银行", "财报发布日期": "20251025", "财报所属期间": "三季报", "上市日期": "20121009"},
    ])
    result = filter_missing(df)
    assert len(result) == 1
    assert result.iloc[0]["股票代码"] == "600000"

# 验证数据清洗
def test_clean_data():
    df = pd.DataFrame([{
        "股票代码": "600000", "股票名称": "A", "主营收入": 10, "净利润": 0, "总资产": 200, "总负债": 100, "股东权益": 50, "流动资产": 50, "流动负债": 25, "经营现金流量": 5, "投资收益": np.nan, "营业外收支": np.nan, "主营收入同比增长率": 600, "行业分类": "银行", "财报发布日期": "20251025", "财报所属期间": "三季报", "上市日期": "20121009",
    }])
    result = clean_data(df)
    assert result.loc[0, "投资收益"] == 0
    assert result.loc[0, "营业外收支"] == 0
    assert result.loc[0, "主营收入同比增长率"] == 500
