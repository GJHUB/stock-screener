"""策略筛选模块 - 缩量超卖买点策略"""

import pandas as pd
from .indicator import add_all_indicators


def check_buy_signal(df: pd.DataFrame, params: dict) -> tuple:
    """检查当日是否满足买点条件
    
    条件（全部满足）:
    1. 缩量: 当日成交量 < 5日均量 × 70%
    2. 下跌/横盘: 当日涨跌幅 <= 1%
    3. KDJ超卖: J 值 < 0
    4. MACD多头: DIFF > 0
    
    Args:
        df: 包含指标的 DataFrame
        params: 参数配置
        
    Returns:
        tuple: (is_signal, details_dict)
    """
    if df.empty:
        return False, {}
    
    last = df.iloc[-1]
    
    # 计算量比
    vol_ma = last.get('VOL_MA5', 0)
    volume_ratio = last['成交量'] / vol_ma if vol_ma > 0 else 1
    
    details = {
        'volume_ratio': volume_ratio,
        'j_value': last['J'],
        'diff_value': last['DIFF'],
        'change_pct': last['涨跌幅']
    }
    
    # 检查各项条件
    volume_ok = volume_ratio < params['volume_ratio']
    change_ok = details['change_pct'] <= params['change_threshold']
    kdj_ok = details['j_value'] < params['j_threshold']
    macd_ok = details['diff_value'] > params['diff_threshold']
    
    is_signal = volume_ok and change_ok and kdj_ok and macd_ok
    
    return is_signal, details


def generate_reason(details: dict) -> str:
    """生成选股理由文本
    
    Args:
        details: 买点信号详情
        
    Returns:
        str: 选股理由
    """
    reason = (
        f"缩量（量比{details['volume_ratio']:.2f}）"
        f"涨跌{details['change_pct']:.1f}%，"
        f"J值{details['j_value']:.1f}进入超卖区，"
        f"DIFF {details['diff_value']:.2f}保持多头，符合买点信号。"
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
    
    # 检查数据完整性（至少需要26天计算MACD）
    if len(df) < 30:
        return None
    
    # 排除当日涨停（涨幅 >= 9.5%）
    if df.iloc[-1]['涨跌幅'] >= 9.5:
        return None
    
    # 检查买点信号
    is_signal, details = check_buy_signal(df, params)
    if not is_signal:
        return None
    
    # 生成选股理由
    reason = generate_reason(details)
    
    last = df.iloc[-1]
    return {
        '代码': code,
        '名称': name,
        '当前价': last['收盘'],
        '涨跌幅': f"{last['涨跌幅']:.2f}%",
        'J值': round(details['j_value'], 1),
        'DIFF': round(details['diff_value'], 2),
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
