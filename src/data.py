"""数据获取模块 - 使用 AKShare"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta


def get_stock_list() -> pd.DataFrame:
    """获取A股列表，剔除ST和停牌
    
    Returns:
        DataFrame with columns: 代码, 名称, 最新价, 涨跌幅
    """
    df = ak.stock_zh_a_spot_em()
    
    # 剔除ST股票
    df = df[~df['名称'].str.contains('ST', na=False)]
    
    # 剔除停牌股票（成交量为0或最新价为空）
    df = df[df['成交量'] > 0]
    df = df[df['最新价'].notna()]
    
    # 选择需要的列
    result = df[['代码', '名称', '最新价', '涨跌幅']].copy()
    result = result.reset_index(drop=True)
    
    return result


def get_stock_history(code: str, days: int = 120) -> pd.DataFrame:
    """获取单只股票日K数据
    
    Args:
        code: 股票代码，如 '000001'
        days: 获取天数
        
    Returns:
        DataFrame with columns: 日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 涨跌幅
    """
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days * 2)).strftime('%Y%m%d')
    
    try:
        df = ak.stock_zh_a_hist(
            symbol=code,
            period='daily',
            start_date=start_date,
            end_date=end_date,
            adjust='qfq'  # 前复权
        )
        
        if df is None or df.empty:
            return pd.DataFrame()
        
        # 重命名列
        df = df.rename(columns={
            '日期': '日期',
            '开盘': '开盘',
            '收盘': '收盘',
            '最高': '最高',
            '最低': '最低',
            '成交量': '成交量',
            '成交额': '成交额',
            '涨跌幅': '涨跌幅'
        })
        
        # 只保留最近 days 天
        df = df.tail(days).reset_index(drop=True)
        
        return df
        
    except Exception as e:
        print(f"获取 {code} 数据失败: {e}")
        return pd.DataFrame()


def get_all_stocks_history(codes: list, days: int = 120) -> dict:
    """批量获取股票历史数据
    
    Args:
        codes: 股票代码列表
        days: 获取天数
        
    Returns:
        dict: {code: DataFrame}
    """
    result = {}
    total = len(codes)
    
    for i, code in enumerate(codes):
        if (i + 1) % 100 == 0:
            print(f"进度: {i + 1}/{total}")
        
        df = get_stock_history(code, days)
        if not df.empty and len(df) >= 60:  # 至少60天数据
            result[code] = df
    
    print(f"成功获取 {len(result)} 只股票数据")
    return result
