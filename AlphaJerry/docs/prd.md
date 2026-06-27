---

tags: [协作]  
date: 2026-06-21  

---

# prd

开发一套低成本、开源的 AI Agent 工具，覆盖 A 股基本面分析的完整工作流，帮助投资者识别优质公司并监控持仓。

## 技术选型

| 层级 | 技术 | 理由 |
|:--|:--|:--|
| 语言 | Python 3.11+ | 数据处理 + AI 生态最成熟 |
| LLM API | DeepSeek API | 国产性价比最优，百万 token 约 ¥1-2 |
| 网页 UI | Gradio | 聊天界面 + DataFrame 表格，组件丰富 |
| 数据采集 | akshare | 开源 A 股数据接口，覆盖东财/同花顺 |
| 数据处理 | pandas / openpyxl | xlsx 读写 + 向量化计算 |
| 定时调度 | schedule | 轻量级 Python 调度库 |
| 推送 | smtplib + 企业微信 webhook | 免费稳定 |

## 项目结构

```
AlphaJerry/
├── main.py              # CLI 入口 (click)
├── config/
│   ├── settings.py      # API keys / 路径 / 阈值
│   ├── scoring_rules.py # 评分阈值表
│   ├── industry_map.py  # 申万 → 5 大行业映射
│   └── industry_weights.py # 行业权重配置
├── engine/
│   ├── collector.py     # 数据采集
│   ├── scorer.py        # 评分引擎
│   ├── rater.py         # 评级引擎
│   ├── reporter.py      # 报告输出
│   ├── monitor.py       # 持股监控
│   ├── hot_tracker.py   # 热点追踪
│   ├── pusher.py        # 推送
│   └── scheduler.py     # 定时调度
├── agent/
│   └── orchestrator.py  # LLM Agent 编排 + 工具定义
├── ui/
│   └── app.py           # Gradio Web UI
├── utils/
│   ├── formulas.py      # 衍生指标计算
│   └── helpers.py       # xlsx 读写 / 缓存 / 日志
├── data/
│   ├── 财务/
│   ├── 分析/
│   ├── 持股/
│   ├── 热点/
│   ├── 缓存/
│   └── 日志/
├── requirements.txt
├── PRD.md
└── ROADMAP.md
```

## 架构总览

```
┌──────────────────────────────────────────┐
│              Gradio Web UI               │
│         (对话面板 + 表格 + 图表)           │
└────────────────┬─────────────────────────┘
                 │
┌────────────────▼─────────────────────────┐
│           Agent 编排层 (orchestrator)     │
│   自然语言 → LLM 意图识别 → 路由引擎      │
│   工具: collect / score / report         │
│         hold / monitor / hot / push      │
└────────────────┬─────────────────────────┘
                 │
┌────────────────▼─────────────────────────┐
│              核心引擎层 (engine)           │
│                                         │
│  collector  scorer  rater  reporter     │
│  monitor  hot_tracker  pusher  scheduler│
└────────────────┬─────────────────────────┘
                 │
┌────────────────▼─────────────────────────┐
│              数据层 (data/)               │
│  财务/ 分析/ 持股/ 热点/ 缓存/ 日志/       │
└──────────────────────────────────────────┘
```

三层分离：Core Engine 不依赖 UI 和 Agent，可独立脚本调用；Agent 层封装 LLM，做意图识别和工具编排；Gradio UI 只负责展示和交互。

## 数据采集引擎

### 流程

```
akshare 获取全 A 股票列表
  → 逐只爬取最新财报（资产负债表 + 利润表 + 现金流量表）
  → 字段映射标准化
  → 计算衍生指标（ALR / CR / EM / NPR / OPM / NPM / IPR / CFR）
  → 保存 data/财务/YYMMDD.xlsx
```

### 数据源接口

| 接口 | 数据源 | 用途 |
|:--|:--|:--|
| `ak.stock_info_a_code_name()` | 东财 | 全部 A 股代码 + 名称（批量 1 次） |
| `ak.stock_financial_debt_new_ths(symbol, "按报告期")` | 同花顺 | 资产负债表：TA / TL / SE / CA / CL / FA / IA / LTL 等 |
| `ak.stock_financial_benefit_new_ths(symbol, "按报告期")` | 同花顺 | 利润表：Rev / OP / NP / InvP / EPS；yoy 列提供同比增速 |
| `ak.stock_financial_cash_new_ths(symbol, "按报告期")` | 同花顺 | 现金流量表：OCF / ICF / CFF |
| `ak.stock_profile_cninfo(symbol)` | 巨潮 | 个股概况：上市日期 |
| `sw_index_first_info()` + `index_component_sw(code)` | 申万指数 | 全 A 股 → 申万一级行业映射（批量预加载，缓存至 `data/缓存/sw_mapping.json`，复用） |

### 增量策略

- 初次运行：全量采集约 5000 只，每只 4 次 API 调用，耗时约 60-90 分钟
- 后续运行：仅更新 PubDate 晚于上次记录的股票
- 失败重试：单只失败 3 次跳过，记录到 `data/日志/failures.log`

### 字段空值策略

必填字段（缺失则丢弃整行）：`Code` `Name` `Rev` `NP` `TA` `TL` `SE` `CA` `CL` `OCF` `PubDate` `Period` `ListDate` `行业属性`

可空默认 `0`：`InvP` `NRI` `LTL` `FA` `IA` `ICF` `CFF`

可空保留：`GP` `OP` `RE` `APIC` `EPS` `BVPS` `ROE` `净利润同比增长率` `主营收入同比增长率` `TS` 及股本类字段

### 衍生指标除零处理

| 指标 | 分母 | 分母 ≤ 0 处理 |
|:--|:--|:--|
| ALR | TA | 不可能（有资产才有记录） |
| CR / CFR | CL | 填 `N/A`，记录 `数据质量=无负债` |
| EM | SE | 整行丢弃（资不抵债，ST 标的） |
| NPR / IPR | OP | 填 `N/A` |
| OPM / NPM | Rev | 整行丢弃 |

### 异常值处理

| 异常 | 判定 | 处理 |
|:--|:--|:--|
| TA ≤ 0 | 理论不可能 | 丢弃 |
| SE ≤ 0 | 资不抵债 | 丢弃，标注 ST |
| 同比增速 > 500% | 并购等非经营因素 | Winsorize 到 500% |
| 比率 > 1000% | 分母极小失真 | Winsorize 到 ±1000% |

`数据质量` 列记录 N/A 数量，超过衍生字段总数 1/3 则标注「数据不足」，不参与排名。

## 评分引擎

### 流程

```
读取 data/财务/YYMMDD.xlsx
  → 一票否决筛选
  → 行业分类映射（申万 → 5 大类）
  → 成长性评分（营收增速 + 净利增速 + 盈利质量 + 现金流匹配）
  → 稳健性评分（资产负债率 + 流动比率 + 存货周转率 + 审计意见）
  → 资金回报评分（ROE + 自由现金流 + 分红率 + 估值）
  → 读取行业权重表
  → 综合分 = 成长分×w1 + 稳健分×w2 + 回报分×w3
  → 保存 data/财务/YYMMDD-评分.xlsx
```

### 一票否决

| 否决项 | 实现方式 | 标记 |
|:--|:--|:--|
| 造假嫌疑 | 规则自动：货币资金 > TA×20% 且 OCF/NP<0.5 连续 2 期 | `Fraud` |
| 诚信问题 | LLM 联网搜索（二期实现） | `Credibility` |
| 行业毁灭 | LLM 联网搜索（二期实现） | `IndustryDeath` |

否决股票写入 `Veto` 列，不参与评分。`Veto=Pass` 的股票进入评分流程。

### 评分函数

每项子指标用 `score_metric(value, thresholds)`，thresholds 为 5 档阈值字典：

```python
GROWTH_REVENUE_THRESHOLDS = {
    (9, 10): lambda v: v > 40,
    (7, 8):  lambda v: 25 <= v <= 40,
    (5, 6):  lambda v: 15 <= v < 25,
    (3, 4):  lambda v: 5 <= v < 15,
    (1, 2):  lambda v: v < 5,
}
```

4 项子指标取均值得维度分。阈值集中管理于 `config/scoring_rules.py`。

### 缺失处理

子指标缺失 → 均不计入，分母自动减 1。4 项全缺 → 维度分标记为 `InsufficientData`。

### 行业权重

```python
INDUSTRY_WEIGHTS = {
    "周期资源":     {"growth": 0.25, "stability": 0.35, "return": 0.40},
    "大消费":       {"growth": 0.30, "stability": 0.30, "return": 0.40},
    "证券金融":     {"growth": 0.30, "stability": 0.30, "return": 0.40},
    "科技/制造":   {"growth": 0.50, "stability": 0.20, "return": 0.30},
    "公用事业/基建": {"growth": 0.20, "stability": 0.40, "return": 0.40},
}
```

配置存储于 `config/industry_weights.py`。

## 评级引擎

```
读取 data/财务/YYMMDD-评分.xlsx
  → 按综合分映射评级
  → 追加「评级」列
  → 保存 data/财务/YYMMDD-评级.xlsx
```

| 综合分 | 评级 |
|:--|:--|
| 8.5 - 10.0 | 皇冠明珠 |
| 7.0 - 8.4 | 优秀白马 |
| 5.5 - 6.9 | 鸡肋/观察 |
| < 5.5 | 垃圾时间 |

否决股票标为「否决」，不参与评级。

## 报告引擎

```
读取 data/财务/YYMMDD-评级.xlsx
  → 按综合分降序，取前 20
  → 公司类型分类（千里马 / 现金牛 / 护城河）
  → 行业分类确认
  → LLM 生成：核心亮点（≤30 字）+ 点评（≤50 字）
  → 输出 data/分析/YYMMDD-荐股.xlsx
```

### 公司类型判定

```python
def classify_company(row):
    rev_growth = row["主营收入同比增长率"]
    gpm = row["销售毛利率"]
    industry = row["行业分类"]

    if industry in ["科技/制造"] and rev_growth > 15:
        return "千里马"
    if industry in ["公用事业/基建"] and rev_growth > 15:
        return "千里马"
    if industry in ["周期资源"] and rev_growth > 30:
        return "千里马"
    if industry in ["大消费"] and gpm > 50:
        return "护城河"
    if gpm > 40 and row.get("净资产收益率", 0) > 15:
        return "护城河"
    return "现金牛"
```

### LLM 点评缓存

同一天两组报告（9:00 / 17:00）数据若未更新则复用 LLM 结果，缓存 key 为 `日期 + 前 20 只 Code+综合分 hash`，存 `data/缓存/`。

### 日耗 LLM 估算

| 调用 | 日频 | Token 估算 | 花费 |
|:--|:--|:--|:--|
| 荐股点评 20 只 | 1 次 | ~3000 | < ¥0.01 |
| 热点分析 | 2 次 | ~2000/次 | < ¥0.01 |
| 一票否决联网搜索 | 按需 | ~500/只 | 视量 |
| 合计 | | | < ¥0.05/天 |

## 热点追踪

```
9:00 / 17:00 触发
  → 爬取百度 / 微博 / 东方财富热搜前 10
  → 合并去重，关键词匹配行业
  → LLM 分析：市场机会 + 受益板块 + 关联个股
  → 输出 data/热点/YYMMDD-09.md（-17.md）
```

## 持股监控

```
读取 data/持股/YYMMDD.xlsx
  → 逐只重新采集最新财报
  → 重新评分 + 一票否决检查
  → 对比上次评分 → 变化趋势
  → 生成操作建议：持有 / 加仓 / 减仓 / 止损
  → 否决触发 → 高亮标红
  → 保存 data/持股/YYMMDD-09.xlsx（-17.xlsx）
```

操作建议规则：

| 综合分变化 | 建议 |
|:--|:--|
| 上升 > 1 | 加仓 |
| 下降 1 - 2 | 减仓 |
| 下降 > 2 | 止损 |
| 其余 | 持有 |

## 消息推送

| 渠道 | 内容 | 方式 |
|:--|:--|:--|
| 邮件 | 完整分析 + HTML 表格 | `smtplib` |
| 微信（可选） | 持仓摘要 + Top 5 热点 | 企业微信群机器人 webhook |

## 定时调度

`stockcli schedule start` 后台常驻：

```
09:00  → hot_tracker + monitor + push
17:00  → hot_tracker + monitor + push
财报季后 → 手动全量更新
每月 1 日 → 全量数据更新（可选）
```

## CLI 命令清单

```
stockcli collect          数据采集
stockcli score            评分 + 评级
stockcli report           生成荐股报告
stockcli hold add <code>  添加持仓
stockcli hold list        查看持仓
stockcli hold remove      移除持仓
stockcli monitor          持股监控
stockcli hot              热点追踪
stockcli push             推送通知
stockcli schedule start   启动定时任务
stockcli schedule stop    停止定时任务
stockcli ui               启动 Gradio Web 界面
```
