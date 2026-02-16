# 股票日K筛选器

基于技术分析的 A 股自动筛选工具，采用「趋势回调买入策略」，每日自动筛选处于上涨趋势且出现回调买点的股票。

## 功能特点

- 📈 **趋势识别**：MA20 > MA60 多头排列
- 📉 **回调检测**：回调不破前高 90%
- 🎯 **买点信号**：缩量 + KDJ 超卖 + MACD 多头
- 📊 **策略回测**：验证策略历史表现
- 🌐 **自动发布**：GitHub Pages 托管结果

## 策略逻辑

### 趋势判断
- MA20 > MA60（均线多头排列）
- 收盘价 > MA20（价格在均线上方）

### 买点信号
| 条件 | 说明 |
|------|------|
| 缩量 | 当日成交量 < 5日均量 × 70% |
| KDJ超卖 | J 值 < 0 |
| MACD多头 | DIFF > 0 |
| 下跌/横盘 | 当日涨跌幅 <= 1% |

### 回测规则
- 止盈：+10%
- 止损：-5%
- 超时：持有满 10 个交易日

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行筛选

```bash
python main.py
```

### 查看结果

打开 `docs/index.html` 查看选股结果。

## 项目结构

```
stock-screener/
├── src/
│   ├── config.py      # 参数配置
│   ├── data.py        # 数据获取（AKShare）
│   ├── indicator.py   # 指标计算（MA/KDJ/MACD）
│   ├── strategy.py    # 策略筛选
│   ├── backtest.py    # 回测引擎
│   └── render.py      # 页面渲染（Jinja2）
├── templates/         # HTML 模板
├── docs/              # GitHub Pages 输出
├── main.py            # 入口脚本
└── requirements.txt
```

## 自动运行

项目配置了 GitHub Actions，每个交易日北京时间 18:00 自动运行，结果发布到 GitHub Pages。

也可以手动触发：Actions → Daily Stock Screening → Run workflow

## 技术栈

- Python 3.10+
- AKShare - 数据获取
- Pandas - 数据处理
- Jinja2 - 模板渲染
- GitHub Actions - 定时任务
- GitHub Pages - 静态托管

## 免责声明

⚠️ **本工具仅供学习和研究使用，不构成任何投资建议。**

- 历史回测结果不代表未来收益
- 策略可能在特定市场环境下失效
- 请结合基本面分析和个人风险承受能力做出投资决策

股市有风险，投资需谨慎。

## License

MIT
