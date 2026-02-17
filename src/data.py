"""数据获取模块 - 使用 Tushare Pro（第三方代理）"""

import os
import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
import time

# 初始化 Tushare
TUSHARE_TOKEN = os.environ.get('TUSHARE_TOKEN', '')
pro = None

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 2  # 秒


def retry_on_failure(func):
    """重试装饰器"""
    def wrapper(*args, **kwargs):
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    print(f"   ⚠️ {func.__name__} 失败，{RETRY_DELAY}秒后重试 ({attempt + 1}/{MAX_RETRIES}): {e}")
                    time.sleep(RETRY_DELAY)
        raise last_error
    return wrapper


def init_tushare():
    """初始化 Tushare API（使用第三方代理）"""
    global pro
    if not TUSHARE_TOKEN:
        raise ValueError("TUSHARE_TOKEN 未设置，请设置环境变量")
    
    pro = ts.pro_api(TUSHARE_TOKEN)
    # 配置第三方代理
    pro._DataApi__token = TUSHARE_TOKEN
    pro._DataApi__http_url = 'http://lianghua.nanyangqiankun.top'
    return pro


@retry_on_failure
def _fetch_stock_basic():
    """获取股票基本信息（带重试）"""
    global pro
    if pro is None:
        init_tushare()
    return pro.stock_basic(
        exchange='',
        list_status='L',
        fields='ts_code,symbol,name,list_date'
    )


@retry_on_failure
def _fetch_daily(trade_date=None, ts_code=None, start_date=None, end_date=None):
    """获取日线数据（带重试）"""
    global pro
    if pro is None:
        init_tushare()
    
    if trade_date:
        return pro.daily(trade_date=trade_date)
    else:
        return pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)


def get_stock_list() -> pd.DataFrame:
    """获取A股列表，剔除ST和停牌
    
    Returns:
        DataFrame with columns: 代码, 名称, 最新价, 涨跌幅
    """
    try:
        # 获取股票基本信息
        df = _fetch_stock_basic()
        
        # 剔除ST股票
        df = df[~df['name'].str.contains('ST', na=False)]
        
        # 获取最近交易日行情
        daily_df = None
        for i in range(7):
            trade_date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
            try:
                daily_df = _fetch_daily(trade_date=trade_date)
                if daily_df is not None and len(daily_df) > 0:
                    print(f"   获取到 {trade_date} 的行情数据")
                    break
            except Exception as e:
                continue
        
        if daily_df is None or daily_df.empty:
            raise ValueError("无法获取行情数据")
        
        # 合并数据
        df = df.merge(daily_df[['ts_code', 'close', 'pct_chg', 'vol']], on='ts_code', how='inner')
        
        # 剔除停牌股票（成交量为0）
        df = df[df['vol'] > 0]
        
        # 重命名列
        result = df[['symbol', 'name', 'close', 'pct_chg']].copy()
        result.columns = ['代码', '名称', '最新价', '涨跌幅']
        result = result.reset_index(drop=True)
        
        return result
        
    except Exception as e:
        raise ValueError(f"获取股票列表失败: {e}")


def get_stock_history(code: str, days: int = 120) -> pd.DataFrame:
    """获取单只股票日K数据
    
    Args:
        code: 股票代码，如 '000001'
        days: 获取天数
        
    Returns:
        DataFrame with columns: 日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 涨跌幅
    """
    try:
        # 转换为 Tushare 格式的代码
        if code.startswith('6'):
            ts_code = f"{code}.SH"
        else:
            ts_code = f"{code}.SZ"
        
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days * 2)).strftime('%Y%m%d')
        
        # 获取日K数据（带重试）
        df = _fetch_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        
        if df is None or df.empty:
            return pd.DataFrame()
        
        # 按日期排序（从旧到新）
        df = df.sort_values('trade_date').reset_index(drop=True)
        
        # 重命名列
        df = df.rename(columns={
            'trade_date': '日期',
            'open': '开盘',
            'close': '收盘',
            'high': '最高',
            'low': '最低',
            'vol': '成交量',
            'amount': '成交额',
            'pct_chg': '涨跌幅'
        })
        
        # 只保留需要的列和最近 days 天
        df = df[['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '涨跌幅']]
        df = df.tail(days).reset_index(drop=True)
        
        return df
        
    except Exception as e:
        print(f"   获取 {code} 数据失败: {e}")
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
    failed_count = 0
    
    for i, code in enumerate(codes):
        if (i + 1) % 100 == 0:
            print(f"   进度: {i + 1}/{total}，成功: {len(result)}，失败: {failed_count}")
        
        # Tushare 有频率限制，适当延迟
        if i > 0 and i % 50 == 0:
            time.sleep(0.5)
        
        df = get_stock_history(code, days)
        if not df.empty and len(df) >= 30:  # 至少30天数据
            result[code] = df
        else:
            failed_count += 1
    
    print(f"   完成！成功获取 {len(result)} 只，失败 {failed_count} 只")
    return result
