"""指标计算模块 - MA/KDJ/MACD"""

import pandas as pd
import numpy as np


def add_ma(df: pd.DataFrame, periods: list = [5, 20, 60]) -> pd.DataFrame:
    """计算移动平均线
    
    Args:
        df: 包含 '收盘' 列的 DataFrame
        periods: 均线周期列表
        
    Returns:
        添加了 MA5, MA20, MA60 等列的 DataFrame
    """
    df = df.copy()
    for period in periods:
        df[f'MA{period}'] = df['收盘'].rolling(window=period).mean()
    return df


def add_kdj(df: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
    """计算KDJ指标
    
    KDJ计算公式:
    RSV = (C - L9) / (H9 - L9) × 100
    K = 2/3 × K(-1) + 1/3 × RSV
    D = 2/3 × D(-1) + 1/3 × K
    J = 3K - 2D
    
    Args:
        df: 包含 '最高', '最低', '收盘' 列的 DataFrame
        n: RSV 周期，默认 9
        m1: K 平滑系数，默认 3
        m2: D 平滑系数，默认 3
        
    Returns:
        添加了 K, D, J 列的 DataFrame
    """
    df = df.copy()
    
    # 计算 n 日内最高价和最低价
    low_n = df['最低'].rolling(window=n).min()
    high_n = df['最高'].rolling(window=n).max()
    
    # 计算 RSV
    rsv = (df['收盘'] - low_n) / (high_n - low_n) * 100
    rsv = rsv.fillna(50)  # 处理除零情况
    
    # 计算 K, D, J
    k = np.zeros(len(df))
    d = np.zeros(len(df))
    
    k[0] = 50
    d[0] = 50
    
    for i in range(1, len(df)):
        k[i] = (m1 - 1) / m1 * k[i-1] + 1 / m1 * rsv.iloc[i]
        d[i] = (m2 - 1) / m2 * d[i-1] + 1 / m2 * k[i]
    
    df['K'] = k
    df['D'] = d
    df['J'] = 3 * df['K'] - 2 * df['D']
    
    return df


def add_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """计算MACD指标
    
    MACD计算公式:
    EMA12 = EMA(C, 12)
    EMA26 = EMA(C, 26)
    DIFF = EMA12 - EMA26
    DEA = EMA(DIFF, 9)
    MACD = 2 × (DIFF - DEA)
    
    Args:
        df: 包含 '收盘' 列的 DataFrame
        fast: 快线周期，默认 12
        slow: 慢线周期，默认 26
        signal: 信号线周期，默认 9
        
    Returns:
        添加了 DIFF, DEA, MACD 列的 DataFrame
    """
    df = df.copy()
    
    # 计算 EMA
    ema_fast = df['收盘'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['收盘'].ewm(span=slow, adjust=False).mean()
    
    # 计算 DIFF, DEA, MACD
    df['DIFF'] = ema_fast - ema_slow
    df['DEA'] = df['DIFF'].ewm(span=signal, adjust=False).mean()
    df['MACD'] = 2 * (df['DIFF'] - df['DEA'])
    
    return df


def add_volume_ma(df: pd.DataFrame, period: int = 5) -> pd.DataFrame:
    """计算成交量均线
    
    Args:
        df: 包含 '成交量' 列的 DataFrame
        period: 均线周期，默认 5
        
    Returns:
        添加了 VOL_MA5 列的 DataFrame
    """
    df = df.copy()
    df[f'VOL_MA{period}'] = df['成交量'].rolling(window=period).mean()
    return df


def add_all_indicators(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """一次性添加所有指标
    
    Args:
        df: 原始 K 线数据
        params: 参数配置字典
        
    Returns:
        添加了所有指标的 DataFrame
    """
    df = add_ma(df, periods=[5, params['ma_short'], params['ma_long']])
    df = add_kdj(df, n=params['kdj_n'], m1=params['kdj_m1'], m2=params['kdj_m2'])
    df = add_macd(df, fast=params['macd_fast'], slow=params['macd_slow'], signal=params['macd_signal'])
    df = add_volume_ma(df, period=5)
    
    return df
