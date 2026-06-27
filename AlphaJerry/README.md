## data

`缓存\sw_mapping.json`
  - Key: 6 位股票代码（字符串）
  - Value: 申万一级行业中文名称（字符串）

## config

`industry_map.py`

- 31 个申万一级行业名精确映射到 5 大类

## utils

`sw_mapper.py`

- 获取 31 个申万一级行业代码与名称，再逐行业调用获取下辖股票，缓存至 `data\缓存\sw_mapping.json`，方便复用

## engine

### `collector.py`

- 每只股票 4 次 API 调用，组合为一行 dict

| # | 接口 | 数据源 | 用途 |
|---|------|--------|------|
| 0 | `stock_info_a_code_name()` | 东财 | 全 A 股代码+名称（批量 1 次） |
| ① | `stock_financial_debt_new_ths(symbol, "按报告期")` | 同花顺 | 资产负债表 |
| ② | `stock_financial_benefit_new_ths(symbol, "按报告期")` | 同花顺 | 利润表 |
| ③ | `stock_financial_cash_new_ths(symbol, "按报告期")` | 同花顺 | 现金流量表 |
| ④ | `stock_profile_cninfo(symbol)` | 巨潮 | 上市日期 |

- 缺失值处理策略
  - REQUIRED_FIELDS — 14 个必填字段，缺失则整行丢弃
  - DEFAULT_ZERO_FIELDS — 7 个可空字段，空值补 `0`
