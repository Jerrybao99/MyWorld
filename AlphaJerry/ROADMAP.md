---

tags: [协作]  
date: 2026-06-21  

---

# AlphaJerry 实现路线图

## Phase 1：核心引擎

> Phase 1 完成后可运行 `python -m engine.collector` → `python -m engine.scorer` → `python -m engine.reporter` 产出荐股 xlsx，不依赖 CLI / Agent / UI。

---

### Task 1.1：项目骨架与依赖

- [x] **Step 1：创建 AlphaJerry/requirements.txt**

- [x] **Step 2：创建空模块和目录**

```bash
# 在 AlphaJerry 目录下执行
New-Item -ItemType Directory -Force -Path "config", "engine", "utils", "agent", "ui", "data\财务", "data\分析", "data\持股", "data\热点", "data\缓存", "data\日志", "tests"
New-Item -ItemType File -Force -Path "config\__init__.py", "engine\__init__.py", "utils\__init__.py", "agent\__init__.py", "ui\__init__.py", "tests\__init__.py"
New-Item -ItemType File -Force -Path "data\财务\.gitkeep", "data\分析\.gitkeep", "data\持股\.gitkeep", "data\热点\.gitkeep", "data\缓存\.gitkeep", "data\日志\.gitkeep"
```

- [x] **Step 3：本地提交**

```bash
git add AlphaJerry/requirements.txt AlphaJerry/config/ AlphaJerry/engine/ AlphaJerry/utils/ AlphaJerry/agent/ AlphaJerry/ui/ AlphaJerry/data/ AlphaJerry/tests/
git commit -m "feat: init project skeleton and dependencies"
```

---

### Task 1.2：配置模块

- [x] **Step 1：编写 AlphaJerry/config/settings.py**

- [x] **Step 2：编写 AlphaJerry/.env.example**

- [x] **Step 3：编写 AlphaJerry/config/scoring_rules.py**

- [x] **Step 4：编写 AlphaJerry/config/industry_map.py**

- [x] **Step 5：编写 AlphaJerry/config/industry_weights.py**

**验证方法：**
```bash
python -c "from config.scoring_rules import score_metric, GROWTH_REVENUE_THRESHOLDS; print(score_metric(45, GROWTH_REVENUE_THRESHOLDS))"
# 应输出：9.5
python -c "from config.industry_map import map_industry; print(map_industry('食品饮料'))"
# 应输出：大消费
```

- [x] **Step 6：提交**

```bash
git add config/ .env.example
git commit -m "feat: add config module with scoring rules and industry maps"
```

---

### Task 1.3：工具函数

- [x] **Step 1：编写 AlphaJerry/tests/test_formulas.py**

- [x] **Step 2：运行测试验证失败**

```bash
pytest tests/test_formulas.py -v
```
预期：FAIL，`ModuleNotFoundError: No module named 'utils.formulas'`

- [x] **Step 3：编写 AlphaJerry/utils/formulas.py**

- [x] **Step 4：运行测试验证通过**

```bash
pytest tests/test_formulas.py -v
```
预期：PASS（2 passed）

- [x] **Step 5：编写 AlphaJerry/utils/helpers.py**

**验证方法：**
```bash
python -c "from utils.formulas import safe_divide, calc_derived_indicators; print('formulas OK')"
python -c "from utils.helpers import today_str, read_xlsx, write_xlsx; print('helpers OK')"
# 均无报错
```

- [x] **Step 6：提交**

```bash
git add utils/ tests/
git commit -m "feat: add formulas and helpers with tests"
```

---

### Task 1.4：数据采集引擎

- [x] **Step 0：THS 接口验证**

**统一返回格式（10 列长表）：** `report_date | report_name | report_period | quarter_name | metric_name | value | single | yoy | mom | single_yoy`

- [x] **Step 1：编写 AlphaJerry/tests/test_collector.py**

- [x] **Step 2：运行测试验证失败**

```bash
pytest tests/test_collector.py -v
```
预期：FAIL，`ModuleNotFoundError`

- [x] **Step 3：编写 AlphaJerry/engine/collector.py**

- [x] **Step 4：运行单元测试**

```bash
python -m pytest tests/test_collector.py -v
```
预期：PASS（3 passed）

- [x] **Step 5：行业映射重构 —— `sw_index_first_info` + `index_component_sw`**

> 废弃 cninfo 的 `所属行业`（非标准证监会分类），改用申万指数成分股接口批量构建 **股票代码→申万一级行业** 映射。
> 缓存文件：`data/缓存/sw_mapping.json`，31 次 API 调用，一次构建后可复用。
> 新增 `utils/sw_mapper.py`，更新 `config/industry_map.py` 为 31 个申万一级行业名精确映射 5 大类。

- [ ] **Step 6：创建临时验证脚本，真实采集 5 只股票**

运行：
```bash
python tests\verify_collect.py
```

- [ ] **Step 7：提交**

```bash
git add AlphaJerry/engine/collector.py AlphaJerry/tests/test_collector.py AlphaJerry/utils/sw_mapper.py AlphaJerry/config/industry_map.py
git commit -m "feat: add data collection engine with akshare and sw industry mapping"
```

---

### Task 1.5：评分引擎

**Files:**
- Create: `AlphaJerry/engine/scorer.py`
- Create: `AlphaJerry/tests/test_scorer.py`

- [ ] **Step 1：编写 test_scorer.py**

```python
import pandas as pd
import numpy as np
from engine.scorer import veto_check, calc_growth_score, calc_stability_score, calc_return_score, calc_composite_score


def make_row(**overrides):
    defaults = {
        "股票代码": "600000", "股票名称": "测试", "行业分类": "大消费",
        "主营收入同比增长率": 20, "净利润同比增长率": 25,
        "销售毛利率": 30, "净利率": 15, "经营现金流量": 100, "净利润": 80,
        "资产负债率": 50, "流动比率": 2.0,
        "净资产收益率": 18, "现金流量比率": 80,
        "总资产": 1000, "流动负债": 200, "总负债": 500, "股东权益": 500,
    }
    defaults.update(overrides)
    return pd.Series(defaults)


def test_veto_pass():
    row = make_row()
    assert veto_check(row) == "Pass"


def test_veto_fraud():
    row = make_row(总资产=1000, 经营现金流量=-200, 净利润=100)
    assert veto_check(row) == "Fraud"


def test_veto_negative_equity():
    row = make_row(股东权益=-100)
    assert veto_check(row) == "Fraud"


def test_calc_growth_score():
    row = make_row(主营收入同比增长率=45, 净利润同比增长率=55, 销售毛利率=35)
    score = calc_growth_score(row)
    assert score > 8.0


def test_calc_growth_score_missing():
    row = make_row(主营收入同比增长率=None, 净利润同比增长率=25)
    score = calc_growth_score(row)
    assert score is not None


def test_calc_stability_score():
    row = make_row(资产负债率=35, 流动比率=3.0)
    score = calc_stability_score(row)
    assert score > 8.0


def test_calc_return_score():
    row = make_row(净资产收益率=22)
    score = calc_return_score(row)
    assert score > 8.0


def test_calc_composite_score():
    row = make_row()
    result = calc_composite_score(row, 0.30, 0.30, 0.40)
    assert 0 <= result <= 10


def test_calc_composite_vetoed():
    row = make_row(股东权益=-100)
    row["否决"] = "Fraud"
    result = calc_composite_score(row, 0.30, 0.30, 0.40)
    assert result is None
```

- [ ] **Step 2：运行测试验证失败**

```bash
pytest tests/test_scorer.py -v
```
预期：FAIL，`ModuleNotFoundError`

- [ ] **Step 3：编写 scorer.py**

```python
import pandas as pd
import numpy as np
from pathlib import Path

from config.settings import FINANCIAL_DIR
from config.scoring_rules import (
    GROWTH_REVENUE_THRESHOLDS, GROWTH_PROFIT_THRESHOLDS,
    STABILITY_DEBT_THRESHOLDS, STABILITY_LIQUIDITY_THRESHOLDS,
    RETURN_ROE_THRESHOLDS, score_metric, RATING_MAP,
)
from config.industry_weights import INDUSTRY_WEIGHTS
from utils.helpers import read_xlsx, write_xlsx, today_str


def veto_check(row: pd.Series) -> str:
    ta = row.get("总资产", 0) or 0
    ocf = row.get("经营现金流量", 0) or 0
    np_val = row.get("净利润", 0) or 0
    se = row.get("股东权益", 0) or 0

    if se <= 0 or ta <= 0:
        return "Fraud"
    cash_ratio = row.get("货币资金", 0) or 0
    if cash_ratio > ta * 0.2 and np_val > 0 and ocf / np_val < 0.5:
        return "Fraud"
    return "Pass"


def calc_growth_score(row: pd.Series) -> float | None:
    scores = []
    for val, thresholds in [
        (row.get("主营收入同比增长率"), GROWTH_REVENUE_THRESHOLDS),
        (row.get("净利润同比增长率"), GROWTH_PROFIT_THRESHOLDS),
    ]:
        s = score_metric(val, thresholds)
        if s is not None:
            scores.append(s)
    if not scores:
        return None
    return round(sum(scores) / len(scores), 1)


def calc_stability_score(row: pd.Series) -> float | None:
    scores = []
    for val, thresholds in [
        (row.get("资产负债率"), STABILITY_DEBT_THRESHOLDS),
        (row.get("流动比率"), STABILITY_LIQUIDITY_THRESHOLDS),
    ]:
        s = score_metric(val, thresholds)
        if s is not None:
            scores.append(s)
    if not scores:
        return None
    return round(sum(scores) / len(scores), 1)


def calc_return_score(row: pd.Series) -> float | None:
    s = score_metric(row.get("净资产收益率"), RETURN_ROE_THRESHOLDS)
    return round(s, 1) if s is not None else None


def calc_composite_score(row: pd.Series, w_growth: float, w_stability: float, w_return: float) -> float | None:
    if row.get("否决", "Pass") != "Pass":
        return None
    g = row.get("成长性")
    s = row.get("稳健性")
    r = row.get("回报性")
    parts = []
    if g is not None:
        parts.append(g * w_growth)
    if s is not None:
        parts.append(s * w_stability)
    if r is not None:
        parts.append(r * w_return)
    if not parts:
        return None
    total_weight = 0
    if g is not None:
        total_weight += w_growth
    if s is not None:
        total_weight += w_stability
    if r is not None:
        total_weight += w_return
    if total_weight == 0:
        return None
    return round(sum(parts) / total_weight * (w_growth + w_stability + w_return), 1)


def score_all(input_path: Path | None = None, output_path: Path | None = None):
    if input_path is None:
        import glob
        files = sorted(Path(FINANCIAL_DIR).glob("*.xlsx"))
        if not files:
            raise FileNotFoundError(f"未找到财务数据文件: {FINANCIAL_DIR}")
        input_path = files[-1]

    print(f"读取数据: {input_path}")
    df = read_xlsx(input_path)

    df["否决"] = df.apply(veto_check, axis=1)
    veto_count = (df["否决"] != "Pass").sum()
    print(f"一票否决: {veto_count} 只")

    df["成长性"] = df.apply(calc_growth_score, axis=1)
    df["稳健性"] = df.apply(calc_stability_score, axis=1)
    df["回报性"] = df.apply(calc_return_score, axis=1)

    df["综合分"] = df.apply(
        lambda r: calc_composite_score(
            r,
            INDUSTRY_WEIGHTS.get(r.get("行业分类", ""), INDUSTRY_WEIGHTS["科技/制造"])["growth"],
            INDUSTRY_WEIGHTS.get(r.get("行业分类", ""), INDUSTRY_WEIGHTS["科技/制造"])["stability"],
            INDUSTRY_WEIGHTS.get(r.get("行业分类", ""), INDUSTRY_WEIGHTS["科技/制造"])["return"],
        ), axis=1,
    )

    invalid = df["数据质量"] > 3
    df.loc[invalid, "综合分"] = None
    print(f"数据不足标记: {invalid.sum()} 只")

    if output_path is None:
        output_path = FINANCIAL_DIR / f"{today_str()}-评分.xlsx"
    write_xlsx(df, output_path)
    print(f"评分完成: {len(df)} 条 → {output_path}")
    return df


if __name__ == "__main__":
    score_all()
```

- [ ] **Step 4：运行测试**

```bash
python -m pytest tests/test_scorer.py -v
```
预期：PASS（9 passed）

- [ ] **Step 5：功能验证——全流程串联**

> **检验方法：** 用 Phase 1 采集的 5 只数据验证评分流程。

```bash
python -c "
import sys; sys.path.insert(0, '.')
from engine.scorer import score_all
df = score_all()
print('评选完成，前5综合分:')
print(df[['股票代码', '股票名称', '成长性', '稳健性', '回报性', '综合分', '否决']].head())
"
```
预期：输出 5 只股票的各维度分和综合分，格式正常。

- [ ] **Step 6：提交**

```bash
git add AlphaJerry/engine/scorer.py AlphaJerry/tests/test_scorer.py
git commit -m "feat: add scoring engine with veto and composite scoring"
```

---

### Task 1.6：评级 + 报告引擎

**Files:**
- Create: `AlphaJerry/engine/rater.py`
- Create: `AlphaJerry/engine/reporter.py`
- Create: `AlphaJerry/tests/test_rater.py`
- Create: `AlphaJerry/tests/test_reporter.py`

- [ ] **Step 1：编写 test_rater.py**

```python
import pandas as pd
from engine.rater import apply_rating


def test_apply_rating():
    df = pd.DataFrame([
        {"综合分": 9.0},
        {"综合分": 7.5},
        {"综合分": 6.0},
        {"综合分": 3.0},
        {"综合分": None},
        {"综合分": 7.0, "否决": "Fraud"},
    ])
    result = apply_rating(df)
    assert result.loc[0, "评级"] == "皇冠明珠"
    assert result.loc[1, "评级"] == "优秀白马"
    assert result.loc[2, "评级"] == "鸡肋/观察"
    assert result.loc[3, "评级"] == "垃圾时间"
    assert "数据不足" in str(result.loc[4, "评级"])
    assert result.loc[5, "评级"] == "否决"
```

- [ ] **Step 2：编写 test_reporter.py**

```python
import pandas as pd
from engine.reporter import classify_company, classify_industry_group


def test_classify_company_qianlima():
    row = pd.Series({"主营收入同比增长率": 20, "销售毛利率": 30, "净资产收益率": 12, "行业分类": "科技/制造"})
    assert classify_company(row) == "千里马"


def test_classify_company_moat():
    row = pd.Series({"主营收入同比增长率": 5, "销售毛利率": 55, "净资产收益率": 18, "行业分类": "大消费"})
    assert classify_company(row) == "护城河"


def test_classify_company_cashcow():
    row = pd.Series({"主营收入同比增长率": 5, "销售毛利率": 25, "净资产收益率": 8, "行业分类": "公用事业/基建"})
    assert classify_company(row) == "现金牛"
```

- [ ] **Step 3：运行测试验证失败**

```bash
pytest tests/test_rater.py tests/test_reporter.py -v
```
预期：FAIL

- [ ] **Step 4：编写 rater.py**

```python
import pandas as pd
from pathlib import Path

from config.settings import FINANCIAL_DIR
from config.scoring_rules import RATING_MAP
from utils.helpers import read_xlsx, write_xlsx, today_str


def apply_rating(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    def _rate(row):
        if row.get("否决", "Pass") != "Pass":
            return "否决"
        score = row.get("综合分")
        if score is None or (isinstance(score, float) and pd.isna(score)):
            return "数据不足"
        for lo, hi, label in RATING_MAP:
            if lo <= score <= hi:
                return label
        return "垃圾时间"

    df["评级"] = df.apply(_rate, axis=1)
    return df


def rate_all(input_path: Path | None = None, output_path: Path | None = None):
    if input_path is None:
        input_path = FINANCIAL_DIR / f"{today_str()}-评分.xlsx"
    print(f"读取评分数据: {input_path}")
    df = read_xlsx(input_path)
    df = apply_rating(df)

    if output_path is None:
        output_path = FINANCIAL_DIR / f"{today_str()}-评级.xlsx"
    write_xlsx(df, output_path)
    print(f"评级完成: {len(df)} 条 → {output_path}")
    return df
```

- [ ] **Step 5：编写 reporter.py**

```python
import json
import hashlib
import pandas as pd
from pathlib import Path
from datetime import datetime

from config.settings import FINANCIAL_DIR, ANALYSIS_DIR, CACHE_DIR
from utils.helpers import read_xlsx, write_xlsx, today_str


def classify_company(row: pd.Series) -> str:
    rev_growth = row.get("主营收入同比增长率") or 0
    gpm = row.get("销售毛利率") or 0
    roe = row.get("净资产收益率") or 0
    industry = row.get("行业分类", "")

    if industry in ["科技/制造"] and rev_growth > 15:
        return "千里马"
    if industry in ["公用事业/基建"] and rev_growth > 15:
        return "千里马"
    if industry in ["周期资源"] and rev_growth > 30:
        return "千里马"
    if industry in ["大消费"] and gpm > 50:
        return "护城河"
    if gpm > 40 and roe > 15:
        return "护城河"
    return "现金牛"


def classify_industry_group(industry: str) -> str:
    for group in ["周期资源", "大消费", "证券金融", "科技/制造", "公用事业/基建"]:
        if group in str(industry):
            return group
    return "科技/制造"


def generate_report(input_path: Path | None = None, output_path: Path | None = None):
    if input_path is None:
        input_path = FINANCIAL_DIR / f"{today_str()}-评级.xlsx"

    print(f"读取评级数据: {input_path}")
    df = read_xlsx(input_path)

    valid = df[df["评级"].isin(["皇冠明珠", "优秀白马", "鸡肋/观察", "垃圾时间"])]
    top20 = valid.sort_values("综合分", ascending=False).head(20).copy()

    top20["公司类型"] = top20.apply(classify_company, axis=1)
    top20["行业分组"] = top20["行业分类"].apply(classify_industry_group)

    report = top20[[
        "股票代码", "股票名称", "公司类型", "行业分组",
        "成长性", "稳健性", "回报性",
        "综合分", "评级",
    ]].copy()

    report.columns = [
        "股票代码", "股票名称", "公司类型", "行业分类",
        "成长性", "稳健性", "回报性", "综合分", "评级",
    ]

    report["核心亮点"] = ""
    report["点评"] = ""

    if output_path is None:
        output_path = ANALYSIS_DIR / f"{today_str()}-荐股.xlsx"
    write_xlsx(report, output_path)
    print(f"报告生成: Top {len(report)} → {output_path}")
    return report


if __name__ == "__main__":
    generate_report()
```

- [ ] **Step 6：运行测试**

```bash
python -m pytest tests/test_rater.py tests/test_reporter.py -v
```
预期：PASS（4 passed）

- [ ] **Step 7：功能验证——端到端串联**

> **检验方法：** 从采集到报告完整跑通。

```bash
python -c "
import sys; sys.path.insert(0, '.')
from engine.collector import collect_all
from engine.scorer import score_all
from engine.rater import rate_all
from engine.reporter import generate_report

# Phase 1 全流程
df = collect_all()
df = score_all()
df = rate_all()
report = generate_report()
print(report[['股票代码', '股票名称', '综合分', '评级']].to_string())
"
```
预期：输出全 A 股 Top 20 荐股表格（耗时约 20-40 分钟，取决于网络）。

- [ ] **Step 8：提交**

```bash
git add AlphaJerry/engine/rater.py AlphaJerry/engine/reporter.py AlphaJerry/tests/test_rater.py AlphaJerry/tests/test_reporter.py
git commit -m "feat: add rating and report engines"
```

---

## Phase 2：CLI + Agent 骨架

> Phase 2 完成后可通过 `python main.py collect` 等命令操作，不依赖 UI。

---

### Task 2.1：CLI 入口

**Files:**
- Create: `AlphaJerry/main.py`

- [ ] **Step 1：编写 main.py**

```python
import sys
import click
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


@click.group()
def cli():
    """AlphaJerry - A 股基本面分析 AI Agent"""
    pass


@cli.command()
def collect():
    """采集全 A 股财报数据"""
    from engine.collector import collect_all
    collect_all()


@cli.command()
def score():
    """执行评分 + 评级"""
    from engine.scorer import score_all
    from engine.rater import rate_all
    score_all()
    rate_all()


@cli.command()
def report():
    """生成 Top 20 荐股报告"""
    from engine.reporter import generate_report
    generate_report()


@cli.command()
@click.argument("code")
@click.argument("name")
def hold_add(code, name):
    """添加持仓: hold-add 600000 浦发银行"""
    import pandas as pd
    from config.settings import HOLDING_DIR
    from utils.helpers import today_str

    path = HOLDING_DIR / f"{today_str()}.xlsx"
    if path.exists():
        df = pd.read_excel(path, dtype={"股票代码": str})
    else:
        df = pd.DataFrame(columns=["股票代码", "股票名称", "添加日期"])

    if code in df["股票代码"].values:
        print(f"股票 {code} 已在持仓中")
        return

    new_row = pd.DataFrame([{"股票代码": code, "股票名称": name, "添加日期": today_str()}])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_excel(path, index=False)
    print(f"已添加持仓: {code} {name} → {path}")


@cli.command()
def hold_list():
    """查看持仓列表"""
    from config.settings import HOLDING_DIR
    from utils.helpers import today_str
    path = HOLDING_DIR / f"{today_str()}.xlsx"
    if not path.exists():
        print("暂无持仓记录")
        return
    df = pd.read_excel(path, dtype={"股票代码": str})
    print(df.to_string(index=False))


@cli.command()
def ui():
    """启动 Gradio Web 界面"""
    from ui.app import launch
    launch()


@cli.command()
def schedule_start():
    """启动定时任务"""
    from engine.scheduler import start
    start()


if __name__ == "__main__":
    cli()
```

- [ ] **Step 2：安装 click**

```bash
pip install click
```

- [ ] **Step 3：验证 CLI**

```bash
python main.py --help
```
预期：输出命令列表（collect / score / report / hold-add / hold-list / ui / schedule-start）

```bash
python main.py hold-add 600000 浦发银行
python main.py hold-list
```
预期：输出 600000 浦发银行

```bash
Remove-Item -Force "data\持股\*.xlsx"
```

- [ ] **Step 4：提交**

```bash
git add AlphaJerry/main.py
git commit -m "feat: add CLI entry with click"
```

---

### Task 2.2：Agent 编排层

**Files:**
- Create: `AlphaJerry/agent/orchestrator.py`

- [ ] **Step 1：编写 orchestrator.py**

```python
import json
from openai import OpenAI

from config.settings import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "collect_data",
            "description": "采集全 A 股最新财报数据。当用户要求更新数据、刷新财报、爬取数据时调用。",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "score_stocks",
            "description": "对全部 A 股进行评分和评级。当用户要求评分、评级、分析股票时调用。",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_report",
            "description": "生成 Top 20 荐股报告。当用户要求推荐、荐股、看排名时调用。",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_holding",
            "description": "添加持仓股票。当用户告知持有某股票时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "6 位股票代码"},
                    "name": {"type": "string", "description": "股票名称"},
                },
                "required": ["code", "name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_holdings",
            "description": "查看当前持仓列表。当用户询问持仓、持有哪些股票时调用。",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "monitor_holdings",
            "description": "监控持仓股票风险。当用户要求检查持仓、监控风险时调用。",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "track_hotspots",
            "description": "追踪市场热点。当用户询问热点、热搜、市场情绪时调用。",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


def execute_tool(name: str, args: dict) -> str:
    if name == "collect_data":
        from engine.collector import collect_all
        collect_all()
        return "数据采集完成"
    elif name == "score_stocks":
        from engine.scorer import score_all
        from engine.rater import rate_all
        score_all()
        rate_all()
        return "评分评级完成"
    elif name == "generate_report":
        from engine.reporter import generate_report
        report = generate_report()
        return f"荐股报告已生成，共 {len(report)} 只"
    elif name == "add_holding":
        import pandas as pd
        from config.settings import HOLDING_DIR
        from utils.helpers import today_str
        path = HOLDING_DIR / f"{today_str()}.xlsx"
        if path.exists():
            df = pd.read_excel(path, dtype={"股票代码": str})
        else:
            df = pd.DataFrame(columns=["股票代码", "股票名称", "添加日期"])
        new_row = pd.DataFrame([{"股票代码": args["code"], "股票名称": args["name"], "添加日期": today_str()}])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_excel(path, index=False)
        return f"已添加持仓: {args['code']} {args['name']}"
    elif name == "list_holdings":
        from config.settings import HOLDING_DIR
        from utils.helpers import today_str
        path = HOLDING_DIR / f"{today_str()}.xlsx"
        if not path.exists():
            return "暂无持仓记录"
        df = pd.read_excel(path, dtype={"股票代码": str})
        return df.to_string(index=False)
    elif name == "monitor_holdings":
        return "持仓监控功能将在 Phase 4 实现"
    elif name == "track_hotspots":
        return "热点追踪功能将在 Phase 4 实现"
    return "未知操作"


def chat(user_message: str, history: list | None = None) -> str:
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    messages = [{"role": "system", "content": "你是 AlphaJerry，一个 A 股基本面分析助手。帮助用户采集数据、评分股票、生成推荐、管理持仓。回复简洁专业，30 字以内。"}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=messages,
        tools=TOOLS,
        temperature=0.3,
    )

    msg = response.choices[0].message
    if msg.tool_calls:
        results = []
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments) if tc.function.arguments else {}
            result = execute_tool(tc.function.name, args)
            results.append(result)
        return "\n".join(results)
    return msg.content or ""


if __name__ == "__main__":
    print("AlphaJerry Agent 测试")
    print(chat("帮我看看现在持有哪些股票"))
```

- [ ] **Step 2：验证 Agent**

```bash
python -c "
import sys; sys.path.insert(0, '.')
from agent.orchestrator import chat
print(chat('你好'))
"
```
预期：返回友好问候（DeepSeek API 需配置了 key）。

- [ ] **Step 3：提交**

```bash
git add AlphaJerry/agent/
git commit -m "feat: add agent orchestrator with tool calling"
```

---

## Phase 3：Gradio UI

> Phase 3 完成后可通过浏览器打开对话界面，自然语言操作全部功能。

---

### Task 3.1：Gradio UI

**Files:**
- Create: `AlphaJerry/ui/app.py`

- [ ] **Step 1：编写 app.py**

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gradio as gr
import pandas as pd
from agent.orchestrator import chat
from engine.collector import collect_all
from engine.scorer import score_all
from engine.rater import rate_all
from engine.reporter import generate_report


def respond(message, history):
    history_list = []
    for h in history:
        history_list.append({"role": "user", "content": h[0]})
        if h[1]:
            history_list.append({"role": "assistant", "content": h[1]})
    reply = chat(message, history_list)
    return reply


def refresh_report():
    try:
        from config.settings import ANALYSIS_DIR
        from utils.helpers import today_str
        path = ANALYSIS_DIR / f"{today_str()}-荐股.xlsx"
        if path.exists():
            df = pd.read_excel(path, dtype={"股票代码": str})
            return df
    except Exception:
        pass
    return pd.DataFrame()


def run_full_pipeline():
    yield "开始采集数据..."
    collect_all()
    yield "数据采集完成，开始评分..."
    score_all()
    yield "评分完成，开始评级..."
    rate_all()
    yield "评级完成，生成报告..."
    generate_report()
    yield "全部完成！"


with gr.Blocks(title="AlphaJerry", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# AlphaJerry - A 股基本面分析 AI Agent")

    with gr.Tab("对话"):
        gr.ChatInterface(
            respond,
            examples=["帮我分析一下当前市场", "推荐几只优质股票", "我持有 600000 浦发银行"],
        )

    with gr.Tab("一键分析"):
        run_btn = gr.Button("全流程执行（采集 → 评分 → 评级 → 报告）", variant="primary")
        status = gr.Textbox(label="状态")
        run_btn.click(run_full_pipeline, outputs=[status])

    with gr.Tab("最新荐股"):
        report_table = gr.Dataframe(refresh_report, label="Top 20 荐股", interactive=False)
        refresh_btn = gr.Button("刷新")
        refresh_btn.click(refresh_report, outputs=[report_table])


def launch():
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)


if __name__ == "__main__":
    launch()
```

- [ ] **Step 2：验证 UI**

```bash
python ui/app.py
```
预期：控制台输出 `Running on local URL: http://127.0.0.1:7860`，浏览器打开可见对话界面和表格。

- [ ] **Step 3：提交**

```bash
git add AlphaJerry/ui/
git commit -m "feat: add Gradio web UI with chat and report tabs"
```

---

## Phase 4：监控运维

> Phase 4 完成后系统可自动定时运行，推送分析结果。

---

### Task 4.1：持股监控

**Files:**
- Create: `AlphaJerry/engine/monitor.py`
- Create: `AlphaJerry/tests/test_monitor.py`

- [ ] **Step 1：编写 test_monitor.py**

```python
import pandas as pd
from engine.monitor import suggest_action


def test_suggest_action_hold():
    assert suggest_action(0.3) == "持有"


def test_suggest_action_add():
    assert suggest_action(1.5) == "加仓"


def test_suggest_action_reduce():
    assert suggest_action(-1.5) == "减仓"


def test_suggest_action_stop():
    assert suggest_action(-2.5) == "止损"
```

- [ ] **Step 2：运行测试验证失败**

```bash
pytest tests/test_monitor.py -v
```
预期：FAIL

- [ ] **Step 3：编写 monitor.py**

```python
import pandas as pd
from pathlib import Path

from config.settings import HOLDING_DIR
from engine.collector import collect_single_stock, map_fields, filter_missing, clean_data
from engine.scorer import veto_check, calc_growth_score, calc_stability_score, calc_return_score, calc_composite_score
from config.industry_weights import INDUSTRY_WEIGHTS
from config.industry_map import map_industry
from utils.formulas import calc_derived_indicators
from utils.helpers import read_xlsx, write_xlsx, today_str


def suggest_action(score_change: float) -> str:
    if score_change > 1:
        return "加仓"
    elif score_change < -2:
        return "止损"
    elif -2 <= score_change < -1:
        return "减仓"
    else:
        return "持有"


def monitor_holdings(session: str = "09"):
    holding_path = HOLDING_DIR / f"{today_str()}.xlsx"
    if not holding_path.exists():
        print("无持仓记录，跳过监控")
        return

    holdings = read_xlsx(holding_path)
    print(f"监控 {len(holdings)} 只持仓...")

    prev_path = HOLDING_DIR / f"{today_str()}-上次.xlsx"
    prev_scores = {}
    if prev_path.exists():
        prev = read_xlsx(prev_path)
        for _, row in prev.iterrows():
            prev_scores[row["股票代码"]] = row.get("综合分")

    rows = []
    alerts = []
    for _, holding in holdings.iterrows():
        code = str(holding["股票代码"])
        name = holding["股票名称"]

        raw = collect_single_stock(code)
        if raw is None:
            continue

        df = pd.DataFrame([raw])
        df = map_fields(df)
        df = filter_missing(df)
        df = clean_data(df)
        df = calc_derived_indicators(df)
        df["行业分类"] = df.get("行业属性", "").apply(map_industry)

        row = df.iloc[0]
        row["Code"] = code
        row["Name"] = name

        veto = veto_check(row)
        if veto != "Pass":
            alerts.append(f"风险警报: {code} {name} 触发一票否决 ({veto})")

        weights = INDUSTRY_WEIGHTS.get(row.get("行业分类", ""), INDUSTRY_WEIGHTS["科技/制造"])
        row["成长性"] = calc_growth_score(row)
        row["稳健性"] = calc_stability_score(row)
        row["回报性"] = calc_return_score(row)
        row["综合分"] = calc_composite_score(row, weights["growth"], weights["stability"], weights["return"])

        prev = prev_scores.get(code)
        if prev is not None and row["综合分"] is not None:
            change = row["综合分"] - prev
            row["评分变化"] = change
            row["操作建议"] = suggest_action(change)
        else:
            row["评分变化"] = None
            row["操作建议"] = "首次监控"

        rows.append(row)

    result = pd.DataFrame(rows)
    output_path = HOLDING_DIR / f"{today_str()}-{session}.xlsx"
    write_xlsx(result, output_path)

    if prev_path.exists():
        result.to_excel(prev_path, index=False)
    else:
        result.to_excel(prev_path, index=False)

    if alerts:
        print("\n".join(alerts))

    print(f"监控完成 → {output_path}")
    return result


if __name__ == "__main__":
    monitor_holdings()
```

- [ ] **Step 4：运行测试**

```bash
python -m pytest tests/test_monitor.py -v
```
预期：PASS（4 passed）

- [ ] **Step 5：提交**

```bash
git add AlphaJerry/engine/monitor.py AlphaJerry/tests/test_monitor.py
git commit -m "feat: add holding monitor with risk alerts"
```

---

### Task 4.2：热点追踪

**Files:**
- Create: `AlphaJerry/engine/hot_tracker.py`

- [ ] **Step 1：编写 hot_tracker.py**

```python
import requests
from pathlib import Path
from datetime import datetime

from config.settings import HOT_DIR
from utils.helpers import today_str

HOT_SOURCES = {
    "weibo": "https://weibo.com/ajax/side/hotSearch",
    "baidu": "https://top.baidu.com/board?tab=realtime",
}


def fetch_weibo_hot() -> list[dict]:
    try:
        resp = requests.get(HOT_SOURCES["weibo"], timeout=10, headers={
            "User-Agent": "Mozilla/5.0",
        })
        data = resp.json()
        items = []
        for item in data.get("data", {}).get("realtime", [])[:10]:
            items.append({"source": "微博", "title": item.get("word", ""), "rank": item.get("rank", 0)})
        return items
    except Exception as e:
        print(f"微博热搜获取失败: {e}")
        return []


def fetch_baidu_hot() -> list[dict]:
    try:
        resp = requests.get(HOT_SOURCES["baidu"], timeout=10, headers={
            "User-Agent": "Mozilla/5.0",
        })
        import re
        titles = re.findall(r'"word":"([^"]+)"', resp.text)[:10]
        return [{"source": "百度", "title": t, "rank": i + 1} for i, t in enumerate(titles)]
    except Exception as e:
        print(f"百度热搜获取失败: {e}")
        return []


def analyze_with_llm(items: list[dict]) -> str:
    from openai import OpenAI
    from config.settings import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

    if not DEEPSEEK_API_KEY:
        return "未配置 LLM API Key"

    titles = [f"{i['source']}#{i['rank']}: {i['title']}" for i in items]
    prompt = f"""以下是当前热搜榜前 10：

{chr(10).join(titles)}

请分析：
1. 哪些热搜可能影响 A 股市场？
2. 受益行业和板块是什么？
3. 关联个股有哪些？（给出代码和名称）

用简洁的 markdown 格式回复。"""

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    resp = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return resp.choices[0].message.content or ""


def track_hotspots():
    print("采集热搜...")
    items = fetch_weibo_hot() + fetch_baidu_hot()
    seen = set()
    unique = []
    for item in items:
        if item["title"] not in seen:
            seen.add(item["title"])
            unique.append(item)
    unique.sort(key=lambda x: x["rank"])
    top10 = unique[:10]
    print(f"获取 {len(top10)} 条热搜")

    print("LLM 分析中...")
    analysis = analyze_with_llm(top10)

    output_path = HOT_DIR / f"{today_str()}-{datetime.now().strftime('%H')}.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# 热点追踪 {today_str()}\n\n")
        f.write("## 热搜 Top 10\n\n")
        for i, item in enumerate(top10, 1):
            f.write(f"{i}. [{item['source']}] {item['title']}\n")
        f.write(f"\n## AI 分析\n\n{analysis}\n")

    print(f"热点追踪完成 → {output_path}")
    return analysis


if __name__ == "__main__":
    print(track_hotspots())
```

- [ ] **Step 2：验证热点追踪**

```bash
python -c "
import sys; sys.path.insert(0, '.')
from engine.hot_tracker import fetch_weibo_hot, fetch_baidu_hot
weibo = fetch_weibo_hot()
baidu = fetch_baidu_hot()
print(f'微博: {len(weibo)} 条, 百度: {len(baidu)} 条')
if weibo:
    print(f'微博第一条: {weibo[0][\"title\"]}')
"
```
预期：输出热搜条数及第一条标题（取决于网络能不能通）。

- [ ] **Step 3：提交**

```bash
git add AlphaJerry/engine/hot_tracker.py
git commit -m "feat: add hot topic tracking with LLM analysis"
```

---

### Task 4.3：推送 + 调度

**Files:**
- Create: `AlphaJerry/engine/pusher.py`
- Create: `AlphaJerry/engine/scheduler.py`

- [ ] **Step 1：编写 pusher.py**

```python
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

from config.settings import HOT_DIR, HOLDING_DIR
from utils.helpers import today_str


def send_email(subject: str, body_html: str):
    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")
    to_email = os.getenv("NOTIFY_EMAIL", "")

    if not all([smtp_host, smtp_user, smtp_pass, to_email]):
        print("邮件配置不完整，跳过发送")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [to_email], msg.as_string())
        print(f"邮件已发送 → {to_email}")
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False


def push_daily():
    """每日推送：整合热点 + 持股分析"""
    lines = [f"<h2>AlphaJerry 日报 {today_str()}</h2>"]

    hot_path = HOT_DIR / f"{today_str()}-09.md"
    if hot_path.exists():
        with open(hot_path, "r", encoding="utf-8") as f:
            content = f.read()
        lines.append(f"<pre>{content[:500]}</pre>")
    else:
        lines.append("<p>热点数据未生成</p>")

    hold_path = HOLDING_DIR / f"{today_str()}-09.xlsx"
    if hold_path.exists():
        import pandas as pd
        df = pd.read_excel(hold_path, dtype={"股票代码": str})
        cols = ["股票代码", "股票名称", "综合分", "评级", "操作建议"] if "操作建议" in df.columns else ["股票代码", "股票名称", "综合分"]
        available = [c for c in cols if c in df.columns]
        lines.append(df[available].to_html(index=False))
    else:
        lines.append("<p>持仓数据未生成</p>")

    body = "<br>".join(lines)
    send_email(f"AlphaJerry 日报 {today_str()}", body)
    print("推送完成")


if __name__ == "__main__":
    push_daily()
```

- [ ] **Step 2：编写 scheduler.py**

```python
import schedule
import time
import threading
from datetime import datetime


_running = False


def job_morning():
    print(f"[{datetime.now()}] 执行早间任务...")
    try:
        from engine.hot_tracker import track_hotspots
        track_hotspots()
    except Exception as e:
        print(f"热点追踪失败: {e}")
    try:
        from engine.monitor import monitor_holdings
        monitor_holdings("09")
    except Exception as e:
        print(f"持股监控失败: {e}")
    try:
        from engine.pusher import push_daily
        push_daily()
    except Exception as e:
        print(f"推送失败: {e}")


def job_evening():
    print(f"[{datetime.now()}] 执行晚间任务...")
    try:
        from engine.hot_tracker import track_hotspots
        track_hotspots()
    except Exception as e:
        print(f"热点追踪失败: {e}")
    try:
        from engine.monitor import monitor_holdings
        monitor_holdings("17")
    except Exception as e:
        print(f"持股监控失败: {e}")
    try:
        from engine.pusher import push_daily
        push_daily()
    except Exception as e:
        print(f"推送失败: {e}")


def _run_loop():
    global _running
    _running = True
    print("调度器已启动，等待触发时间 (9:00 / 17:00)...")
    while _running:
        schedule.run_pending()
        time.sleep(60)


def start():
    schedule.every().day.at("09:00").do(job_morning)
    schedule.every().day.at("17:00").do(job_evening)
    t = threading.Thread(target=_run_loop, daemon=True)
    t.start()
    print("定时调度已启动")


def stop():
    global _running
    _running = False
    schedule.clear()
    print("定时调度已停止")


if __name__ == "__main__":
    start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop()
```

- [ ] **Step 3：验证调度**

```bash
python -c "
import sys; sys.path.insert(0, '.')
from engine.scheduler import start, stop
start()
import time; time.sleep(2)
stop()
print('调度器启停正常')
"
```
预期：输出「调度器已启动」和「调度器已停止」。

- [ ] **Step 4：提交**

```bash
git add AlphaJerry/engine/pusher.py AlphaJerry/engine/scheduler.py
git commit -m "feat: add email push and daily scheduler"
```

---

## Phase 验收检查清单

| Phase | 验收标准 | 检验命令 |
|:--|:--|:--|
| 1 | 采集 → 评分 → 报告全流程可跑 | `python -m engine.collector && python -m engine.scorer && python -m engine.reporter` |
| 1 | 单元测试全部通过 | `pytest tests/ -v` |
| 2 | CLI 命令可用 | `python main.py --help` |
| 2 | Agent tool calling 正常 | `python -c "from agent.orchestrator import chat; print(chat('你好'))"` |
| 3 | Gradio 界面可打开 | `python main.py ui` → 浏览器访问 `http://127.0.0.1:7860` |
| 4 | 调度器启停正常 | `python -c "from engine.scheduler import start,stop; start(); ... ; stop()"` |
| 4 | 热点采集成功 | `python -c "from engine.hot_tracker import fetch_weibo_hot; print(len(fetch_weibo_hot()))"` |

接口更新  
