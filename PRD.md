# 股票日K筛选器 - 产品需求文档

> 版本：v1.0  
> 日期：2025-02-17  
> 作者：PM Agent  

---

## 1. 项目概述

### 1.1 项目背景
个人投资者需要一个自动化工具，基于技术分析筛选出处于「上涨趋势 + 回调买点」的股票，减少人工盯盘时间，提高选股效率。

### 1.2 项目目标
- 每日自动筛选符合策略的 A 股标的
- 提供回测功能验证策略有效性
- 通过 GitHub Pages 发布结果，随时随地查看

### 1.3 核心价值
- **省时**：自动化筛选，无需逐个翻看 K 线
- **可验证**：回测功能量化策略胜率和收益
- **零成本**：免费数据源 + 免费托管

---

## 2. 数据源

### 2.1 选型：AKShare
- **理由**：开源免费、数据全面、底层对接东方财富/新浪等多源
- **安装**：`pip install akshare`
- **文档**：https://akshare.akfamily.xyz/

### 2.2 所需数据
| 数据类型 | 接口 | 说明 |
|----------|------|------|
| A股列表 | `ak.stock_zh_a_spot_em()` | 获取全部A股基本信息 |
| 日K数据 | `ak.stock_zh_a_hist()` | 获取单只股票历史日K |
| 实时行情 | `ak.stock_zh_a_spot_em()` | 获取最新价格 |

### 2.3 数据字段
```
日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率
```

---

## 3. 策略定义

### 3.1 策略名称
**趋势回调买入策略（Trend Pullback Buy）**

### 3.2 策略逻辑

#### 3.2.1 趋势判断
股票处于中期上涨趋势：
- MA20 > MA60（均线多头排列）
- 当前收盘价 > MA20（价格在均线上方）

#### 3.2.2 波动上涨特征
近期走势呈现「涨-回调-涨」的波动上行形态：
- 在过去 N 日（默认60日）内识别波段高点和低点
- 每次回调的最低点 >= 上一波段最高点 × 90%

#### 3.2.3 买点信号
当日满足以下全部条件：
| 条件 | 说明 | 参数 |
|------|------|------|
| 缩量 | 当日成交量 < 5日均量 × 70% | volume_ratio = 0.7 |
| KDJ超卖 | J 值 < 0 | j_threshold = 0 |
| MACD多头 | DIFF > 0 | diff_threshold = 0 |
| 下跌/横盘 | 当日涨跌幅 <= 1% | change_threshold = 1 |

#### 3.2.4 排除条件
- ST / *ST 股票
- 停牌股票
- 上市不足 60 个交易日
- 当日涨停（无法买入）

### 3.3 参数汇总
```python
PARAMS = {
    # 趋势判断
    "ma_short": 20,           # 短期均线
    "ma_long": 60,            # 长期均线
    
    # 回调判断
    "lookback_days": 60,      # 回溯天数
    "pullback_ratio": 0.9,    # 回调不破位比例（90%）
    
    # 买点信号
    "volume_ratio": 0.7,      # 缩量阈值（70%）
    "j_threshold": 0,         # KDJ J值阈值
    "diff_threshold": 0,      # MACD DIFF阈值
    "change_threshold": 1,    # 涨跌幅阈值（%）
    
    # KDJ参数
    "kdj_n": 9,
    "kdj_m1": 3,
    "kdj_m2": 3,
    
    # MACD参数
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
}
```

---

## 4. 功能模块

### 4.1 数据获取模块（data.py）

#### 功能
- 获取 A 股股票列表
- 获取单只/批量股票日K历史数据
- 数据缓存（避免重复请求）

#### 接口设计
```python
def get_stock_list() -> pd.DataFrame:
    """获取A股列表，剔除ST和停牌"""
    
def get_stock_history(code: str, days: int = 120) -> pd.DataFrame:
    """获取单只股票日K数据"""
    
def get_all_stocks_history(codes: list, days: int = 120) -> dict:
    """批量获取，返回 {code: DataFrame}"""
```

### 4.2 指标计算模块（indicator.py）

#### 功能
计算技术指标并添加到 DataFrame

#### 接口设计
```python
def add_ma(df: pd.DataFrame, periods: list = [5, 20, 60]) -> pd.DataFrame:
    """计算移动平均线"""

def add_kdj(df: pd.DataFrame, n=9, m1=3, m2=3) -> pd.DataFrame:
    """计算KDJ指标，返回K, D, J"""

def add_macd(df: pd.DataFrame, fast=12, slow=26, signal=9) -> pd.DataFrame:
    """计算MACD指标，返回DIFF, DEA, MACD"""

def add_volume_ma(df: pd.DataFrame, period: int = 5) -> pd.DataFrame:
    """计算成交量均线"""

def add_all_indicators(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """一次性添加所有指标"""
```

### 4.3 策略筛选模块（strategy.py）

#### 功能
- 判断趋势
- 识别波段高低点
- 检测买点信号
- 生成选股理由

#### 接口设计
```python
def check_trend(df: pd.DataFrame, params: dict) -> bool:
    """检查是否处于上涨趋势"""

def find_swing_points(df: pd.DataFrame, window: int = 5) -> list:
    """识别波段高点和低点"""

def check_pullback_pattern(df: pd.DataFrame, params: dict) -> bool:
    """检查回调是否不破前高90%"""

def check_buy_signal(df: pd.DataFrame, params: dict) -> bool:
    """检查当日是否满足买点条件"""

def generate_reason(df: pd.DataFrame, params: dict) -> str:
    """生成选股理由文本"""

def screen_stocks(stock_data: dict, params: dict) -> pd.DataFrame:
    """主筛选函数，返回符合条件的股票DataFrame"""
```

#### 选股理由示例
```
"MA20>MA60多头趋势，近20日高点15.8元，当前回调至14.5元（-8.2%）未破90%线，
今日缩量（量比0.58）下跌-0.5%，J值-8.3超卖，DIFF 0.12保持多头，符合回调买点。"
```

### 4.4 回测模块（backtest.py）

#### 功能
- 历史信号回测
- 计算策略绩效指标
- 生成回测报告

#### 回测逻辑
```
买入条件：策略信号触发当日收盘价买入
卖出条件（三选一，先触发者执行）：
  1. 止盈：收盘价 >= 买入价 × 110%（+10%）
  2. 止损：收盘价 <= 买入价 × 95%（-5%）
  3. 超时：持有满 10 个交易日
```

#### 绩效指标
| 指标 | 说明 |
|------|------|
| 总交易次数 | 回测期间触发的信号数 |
| 胜率 | 盈利交易 / 总交易 |
| 平均收益率 | 所有交易收益率的均值 |
| 最大单笔盈利 | 单笔最高收益率 |
| 最大单笔亏损 | 单笔最大亏损率 |
| 盈亏比 | 平均盈利 / 平均亏损 |
| 累计收益率 | 假设等仓位的累计收益 |

#### 接口设计
```python
@dataclass
class TradeRecord:
    code: str
    name: str
    buy_date: str
    buy_price: float
    sell_date: str
    sell_price: float
    sell_reason: str  # "止盈" / "止损" / "超时"
    return_pct: float
    holding_days: int

@dataclass
class BacktestResult:
    start_date: str
    end_date: str
    total_trades: int
    win_rate: float
    avg_return: float
    max_profit: float
    max_loss: float
    profit_loss_ratio: float
    cumulative_return: float
    trades: list[TradeRecord]

def backtest_single(df: pd.DataFrame, params: dict) -> list[TradeRecord]:
    """单只股票回测"""

def backtest_all(stock_data: dict, params: dict, 
                 start_date: str, end_date: str) -> BacktestResult:
    """全市场回测"""

def generate_backtest_report(result: BacktestResult) -> str:
    """生成回测报告HTML"""
```

### 4.5 渲染模块（render.py）

#### 功能
- 生成每日选股结果 HTML
- 生成回测报告 HTML
- 生成历史归档页面

#### 页面结构
```
docs/
├── index.html          # 最新选股结果
├── backtest.html       # 回测报告
├── history/
│   ├── 2025-02-17.html
│   ├── 2025-02-16.html
│   └── ...
└── assets/
    └── style.css
```

#### 接口设计
```python
def render_daily_result(stocks: pd.DataFrame, date: str) -> str:
    """渲染每日选股结果"""

def render_backtest_report(result: BacktestResult) -> str:
    """渲染回测报告"""

def render_history_index(dates: list) -> str:
    """渲染历史归档索引"""

def save_pages(output_dir: str):
    """保存所有页面到指定目录"""
```

---

## 5. 输出规格

### 5.1 每日选股表格

| 字段 | 说明 | 示例 |
|------|------|------|
| 代码 | 股票代码 | 000001 |
| 名称 | 股票名称 | 平安银行 |
| 当前价 | 最新收盘价 | 12.35 |
| 涨跌幅 | 当日涨跌幅 | -0.56% |
| J值 | KDJ J值 | -8.3 |
| DIFF | MACD DIFF值 | 0.12 |
| 回调幅度 | 距前高回调比例 | -8.2% |
| 量比 | 当日量/5日均量 | 0.58 |
| 选择理由 | 自动生成的文字说明 | （见上文示例） |

### 5.2 回测报告内容

1. **概览卡片**
   - 回测区间
   - 总交易次数
   - 胜率
   - 累计收益率

2. **绩效指标表**
   - 所有指标详细数值

3. **收益分布图**
   - 每笔交易收益率柱状图

4. **交易明细表**
   - 所有交易记录

---

## 6. 技术架构

### 6.1 技术栈
| 组件 | 选型 | 版本 |
|------|------|------|
| 语言 | Python | 3.10+ |
| 数据源 | AKShare | latest |
| 数据处理 | Pandas | 2.0+ |
| 模板引擎 | Jinja2 | 3.0+ |
| 定时任务 | GitHub Actions | - |
| 静态托管 | GitHub Pages | - |

### 6.2 目录结构
```
stock-screener/
├── src/
│   ├── __init__.py
│   ├── data.py          # 数据获取
│   ├── indicator.py     # 指标计算
│   ├── strategy.py      # 策略筛选
│   ├── backtest.py      # 回测引擎
│   ├── render.py        # 页面渲染
│   └── config.py        # 参数配置
├── templates/
│   ├── base.html        # 基础模板
│   ├── daily.html       # 每日结果
│   ├── backtest.html    # 回测报告
│   └── history.html     # 历史归档
├── docs/                # GitHub Pages 输出
│   ├── index.html
│   ├── backtest.html
│   ├── history/
│   └── assets/
├── tests/
│   ├── test_indicator.py
│   ├── test_strategy.py
│   └── test_backtest.py
├── .github/
│   └── workflows/
│       └── daily.yml    # 每日定时任务
├── requirements.txt
├── main.py              # 入口脚本
└── README.md
```

### 6.3 GitHub Actions 配置
```yaml
name: Daily Stock Screening

on:
  schedule:
    # 北京时间 18:00（UTC 10:00）
    - cron: '0 10 * * 1-5'
  workflow_dispatch:  # 支持手动触发

jobs:
  screen:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: pip install -r requirements.txt
        
      - name: Run screening
        run: python main.py
        
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs
```

---

## 7. 开发计划

### 7.1 里程碑

| 阶段 | 内容 | 预计工时 |
|------|------|----------|
| M1 | 数据获取 + 指标计算 | 2h |
| M2 | 策略筛选逻辑 | 2h |
| M3 | 回测引擎 | 3h |
| M4 | 页面渲染 | 2h |
| M5 | GitHub Actions 部署 | 1h |
| M6 | 测试 + 调优 | 2h |

**总计：约 12 小时**

### 7.2 优先级
1. P0：数据获取、指标计算、策略筛选（核心功能）
2. P1：页面渲染、GitHub 部署（可用性）
3. P2：回测功能（验证性）

---

## 8. 后续扩展（v2.0）

以下功能不在本期范围，作为后续迭代方向：

1. **消息推送**
   - 微信推送（Server酱/PushPlus）
   - Telegram Bot 推送

2. **参数优化**
   - 网格搜索最优参数
   - 不同市场环境的参数自适应

3. **多策略支持**
   - 突破策略
   - 均线金叉策略
   - 策略组合

4. **可视化增强**
   - K线图展示
   - 交互式图表（ECharts）

5. **数据持久化**
   - SQLite 存储历史数据
   - 减少 API 调用

---

## 9. 风险提示

⚠️ **免责声明**

本工具仅供学习和研究使用，不构成任何投资建议。股市有风险，投资需谨慎。

- 历史回测结果不代表未来收益
- 策略可能在特定市场环境下失效
- 请结合基本面分析和个人风险承受能力做出投资决策

---

## 10. 附录

### 10.1 KDJ 计算公式
```
RSV = (C - L9) / (H9 - L9) × 100
K = 2/3 × K(-1) + 1/3 × RSV
D = 2/3 × D(-1) + 1/3 × K
J = 3K - 2D
```

### 10.2 MACD 计算公式
```
EMA12 = EMA(C, 12)
EMA26 = EMA(C, 26)
DIFF = EMA12 - EMA26
DEA = EMA(DIFF, 9)
MACD = 2 × (DIFF - DEA)
```

### 10.3 参考资料
- AKShare 文档：https://akshare.akfamily.xyz/
- GitHub Pages 文档：https://pages.github.com/
- GitHub Actions 文档：https://docs.github.com/en/actions

---

*文档结束*
