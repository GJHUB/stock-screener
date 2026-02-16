"""策略筛选模块 - 趋势回调买入策略"""

import pandas as pd
import numpy as np
from .indicator import add_all_indicators


def check_trend(df: pd.DataFrame, params: dict) -> bool:
    """检查是否处于上涨趋势
    
    条件:
    - MA20 > MA60（均线多头排列）
    - 当前收盘价 > MA20（价格在均线上方）
    
    Args:
        df: 包含指标的 DataFrame
        params: 参数配置
        
    Returns:
        bool: 是否处于上涨趋势
    """
    if df.empty:
        return False
    
    last = df.iloc[-1]
    ma_short = f"MA{params['ma_short']}"
    ma_long = f"MA{params['ma_long']}"
    
    if pd.isna(last[ma_short]) or pd.isna(last[ma_long]):
        return False
    
    # MA20 > MA60 且 收盘价 > MA20
    return last[ma_short] > last[ma_long] and last['收盘'] > last[ma_short]


def find_swing_points(df: pd.DataFrame, window: int = 5) -> tuple:
    """识别波段高点和低点
    
    Args:
        df: K线数据
        window: 判断高低点的窗口大小
        
    Returns:
        tuple: (highs, lows) 高点和低点的索引列表
    """
    highs = []
    lows = []
    
    for i in range(window, len(df) - window):
        # 判断高点：当前最高价是窗口内最高
        if df['最高'].iloc[i] == df['最高'].iloc[i-window:i+window+1].max():
            highs.append(i)
        # 判断低点：当前最低价是窗口内最低
        if df['最低'].iloc[i] == df['最低'].iloc[i-window:i+window+1].min():
            lows.append(i)
    
    return highs, lows


def check_pullback_pattern(df: pd.DataFrame, params: dict) -> tuple:
    """检查回调是否不破前高90%
    
    条件: 每次回调的最低点 >= 上一波段最高点 × 90%
    
    Args:
        df: K线数据（最近 lookback_days 天）
        params: 参数配置
        
    Returns:
        tuple: (is_valid, pullback_pct, recent_high)
    """
    lookback = min(params['lookback_days'], len(df))
    recent_df = df.tail(lookback).copy()
    
    if len(recent_df) < 20:
        return False, 0, 0
    
    highs, lows = find_swing_points(recent_df, window=5)
    
    if len(highs) < 1:
        return False, 0, 0
    
    # 找到最近的高点
    recent_high_idx = highs[-1]
    recent_high = recent_df['最高'].iloc[recent_high_idx]
    
    # 计算当前价格相对高点的回调幅度
    current_price = recent_df['收盘'].iloc[-1]
    pullback_pct = (current_price - recent_high) / recent_high
    
    # 检查回调是否不破位（当前价 >= 高点 * 90%）
    threshold = recent_high * params['pullback_ratio']
    is_valid = current_price >= threshold
    
    return is_valid, pullback_pct, recent_high


def check_buy_signal(df: pd.DataFrame, params: dict) -> tuple:
    """检查当日是否满足买点条件
    
    条件:
    - 缩量: 当日成交量 < 5日均量 × 70%
    - KDJ超卖: J 值 < 0
    - MACD多头: DIFF > 0
    - 下跌/横盘: 当日涨跌幅 <= 1%
    
    Args:
        df: 包含指标的 DataFrame
        params: 参数配置
        
    Returns:
        tuple: (is_signal, details_dict)
    """
    if df.empty:
        return False, 
    
    last = df.iloc[-1]
    
    details = {
        'volume_ratio': last['成交量'] / last['VOL_MA5'] if last['VOL_MA5'] > 0 else 1,
        'j_value': last['J'],
        'diff_value': last['DIFF'],
        'change_pct': last['涨跌幅']
    }
    
    # 检查各项条件
    volume_ok = details['volume_ratio'] < params['volume_ratio']
    kdj_ok = details['j_value'] < params['j_threshold']
    macd_ok = details['diff_value'] > params['diff_threshold']
    change_ok = details['change_pct'] <= params['change_threshold']
    
    is_signal = volume_ok and kdj_ok and macd_ok and change_ok
    
    return is_signal, details


def generate_reason(df: pd.DataFrame, params: dict, details: dict, pullback_pct: float, recent_high: float) -> str:
    """生成选股理由文本
    
    Args:
        df: K线数据
        params: 参数配置
        details: 买点信号详情
        pullback_pct: 回调幅度
        recent_high: 近期高点
        
    Returns:
        str: 选股理由
    """
    last = df.iloc[-1]
    ma_short = params['ma_short']
    ma_long = params['ma_long']
    
    reason = (
        f"MA{ma_short}>MA{ma_long}多头趋势，"
        f"近期高点{recent_high:.2f}元，"
        f"当前回调至{last['收盘']:.2f}元（{pullback_pct*100:.1f}%）未破{int(params['pullback_ratio']*100)}%线，"
        f"今日缩量（量比{details['volume_ratio']:.2f}）"
        f"涨跌{details['change_pct']:.1f}%，"
        f"J值{details['j_value']:.1f}超卖，"
        f"DIFF {details['diff_value']:.2f}保持多头，符合回调买点。"
    )
    
    return reason


def screen_single_stock(code: str, name: str, df: pd.DataFrame, params: dict) -> dict:
    """筛选单只股票
    
    Args:
        code: 股票代码
        name: 股票名称
        df: K线数据
        params: 参数配置
        
    Returns:
        dict: 筛选结果，如果不符合条件返回 None
    """
    # 添加指标
    df = add_all_indicators(df, params)
    
    # 检查数据完整性
    if len(df) < params['ma_long']:
        return None
    
    # 排除当日涨停（涨幅 >= 9.5%）
    if df.iloc[-1]['涨跌幅'] >= 9.5:
        return None
    
    # 检查趋势
    if not check_trend(df, params):
        return None
    
    # 检查回调形态
    is_pullback_valid, pullback_pct, recent_high = check_pullback_pattern(df, params)
    if not is_pullback_valid:
        return None
    
    # 检查买点信号
    is_signal, details = check_buy_signal(df, params)
    if not is_signal:
        return None
    
    # 生成选股理由
    reason = generate_reason(df, params, details, pullback_pct, recent_high)
    
    last = df.iloc[-1]
    return {
        '代码': code,
        '名称': name,
        '当前价': last['收盘'],
        '涨跌幅': f"{last['涨跌幅']:.2f}%",
        'J值': round(details['j_value'], 1),
        'DIFF': round(details['diff_value'], 2),
        '回调幅度': f"{pullback_pct*100:.1f}%",
        '量比': round(details['volume_ratio'], 2),
        '选择理由': reason
    }


def screen_stocks(stock_data: dict, stock_names: dict, params: dict) -> pd.DataFrame:
    """主筛选函数
    
    Args:
        stock_data: {code: DataFrame} 股票数据字典
        stock_names: {code: name} 股票名称字典
        params: 参数配置
        
    Returns:
        DataFrame: 符合条件的股票列表
    """
    results = []
    
    for code, df in stock_data.items():
        name = stock_names.get(code, code)
        result = screen_single_stock(code, name, df, params)
        if result:
            results.append(result)
    
    if not results:
        return pd.DataFrame()
    
    return pd.DataFrame(results)
