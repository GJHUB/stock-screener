# 股票日K筛选器

基于技术分析的 A 股自动筛选工具，每日筛选符合「缩量超卖买点」策略的股票。

## 策略说明

**缩量超卖买点策略（Volume Shrink Oversold Buy）**

买点信号需同时满足以下 4 个条件：

| 条件 | 说明 | 判断标准 |
|------|------|----------|
| 缩量 | 成交量萎缩，卖压减弱 | 当日成交量 < 5日均量 × 70% |
| 下跌/横盘 | 当日收阴或小阳 | 当日涨跌幅 ≤ 1% |
| KDJ超卖 | J值进入超卖区域 | J 值 < 0 |
| MACD多头 | 中期趋势仍向上 | DIFF > 0 |

**策略原理：**
- 缩量下跌说明抛压减弱，空方力量衰竭
- J值<0 表示 KDJ 超卖，短期反弹概率增加
- DIFF>0 表示 MACD 仍在零轴上方，中期趋势未破坏
- 四个条件叠加，筛选出「短期超卖但中期趋势仍在」的股票

## 功能特性

- 📊 每日自动筛选 A 股
- 📈 KDJ/MACD 技术指标计算
- 📋 生成选股结果 HTML 页面
- 🔄 GitHub Actions 定时运行
- 📱 GitHub Pages 在线查看

## 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行筛选
python main.py
```

## 项目结构

```
stock-screener/
├── src/
│   ├── config.py      # 参数配置
│   ├── data.py        # 数据获取
│   ├── indicator.py   # 指标计算
│   ├── strategy.py    # 策略筛选
│   ├── backtest.py    # 回测引擎
│   └── render.py      # 页面渲染
├── templates/         # HTML 模板
├── docs/              # 输出页面
├── main.py            # 入口脚本
└── requirements.txt
```

## 风险提示

⚠️ 本工具仅供学习和研究使用，不构成任何投资建议。股市有风险，投资需谨慎。

## License

MIT
