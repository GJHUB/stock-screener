"""参数配置模块 - 缩量超卖买点策略"""

PARAMS = {
    # 买点信号
    "volume_ratio": 0.7,      # 缩量阈值（当日量/5日均量）
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
    
    # 成交量均线
    "volume_ma_period": 5,
    
    # 回测参数
    "take_profit": 0.10,      # 止盈比例 10%
    "stop_loss": 0.05,        # 止损比例 5%
    "max_holding_days": 10,   # 最大持有天数
}

# 数据获取参数
DATA_DAYS = 120  # 获取历史数据天数
