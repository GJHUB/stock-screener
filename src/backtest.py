"""回测模块 - 缩量超卖买点策略"""

from dataclasses import dataclass, field
from typing import List
import pandas as pd
from .indicator import add_all_indicators
from .strategy import check_buy_signal


@dataclass
class TradeRecord:
    """交易记录"""
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
    """回测结果"""
    start_date: str
    end_date: str
    total_trades: int
    win_rate: float
    avg_return: float
    max_profit: float
    max_loss: float
    profit_loss_ratio: float
    cumulative_return: float
    trades: List[TradeRecord] = field(default_factory=list)


def backtest_single(code: str, name: str, df: pd.DataFrame, params: dict,
                    start_date: str, end_date: str) -> List[TradeRecord]:
    """单只股票回测
    
    Args:
        code: 股票代码
        name: 股票名称
        df: K线数据
        params: 参数配置
        start_date: 回测开始日期
        end_date: 回测结束日期
        
    Returns:
        List[TradeRecord]: 交易记录列表
    """
    trades = []
    
    # 添加指标
    df = add_all_indicators(df, params)
    
    # 过滤日期范围
    df['日期'] = pd.to_datetime(df['日期'])
    df = df[(df['日期'] >= start_date) & (df['日期'] <= end_date)]
    df = df.reset_index(drop=True)
    
    if len(df) < 30:  # 至少需要30天数据
        return trades
    
    i = 30  # 从有足够数据的位置开始
    
    while i < len(df):
        # 获取到当前日期的数据
        current_df = df.iloc[:i+1].copy()
        
        # 检查是否满足买入条件
        is_signal, _ = check_buy_signal(current_df, params)
        if not is_signal:
            i += 1
            continue
        
        # 排除涨停
        if current_df.iloc[-1]['涨跌幅'] >= 9.5:
            i += 1
            continue
        
        # 买入
        buy_date = df.iloc[i]['日期'].strftime('%Y-%m-%d')
        buy_price = df.iloc[i]['收盘']
        
        # 模拟持有
        sell_date = None
        sell_price = None
        sell_reason = None
        
        for j in range(i + 1, min(i + params['max_holding_days'] + 1, len(df))):
            current_price = df.iloc[j]['收盘']
            
            # 止盈
            if current_price >= buy_price * (1 + params['take_profit']):
                sell_date = df.iloc[j]['日期'].strftime('%Y-%m-%d')
                sell_price = current_price
                sell_reason = "止盈"
                i = j + 1
                break
            
            # 止损
            if current_price <= buy_price * (1 - params['stop_loss']):
                sell_date = df.iloc[j]['日期'].strftime('%Y-%m-%d')
                sell_price = current_price
                sell_reason = "止损"
                i = j + 1
                break
            
            # 超时
            if j == i + params['max_holding_days'] or j == len(df) - 1:
                sell_date = df.iloc[j]['日期'].strftime('%Y-%m-%d')
                sell_price = current_price
                sell_reason = "超时"
                i = j + 1
                break
        
        if sell_date is None:
            i += 1
            continue
        
        # 计算收益
        return_pct = (sell_price - buy_price) / buy_price
        holding_days = (pd.to_datetime(sell_date) - pd.to_datetime(buy_date)).days
        
        trades.append(TradeRecord(
            code=code,
            name=name,
            buy_date=buy_date,
            buy_price=round(buy_price, 2),
            sell_date=sell_date,
            sell_price=round(sell_price, 2),
            sell_reason=sell_reason,
            return_pct=round(return_pct, 4),
            holding_days=holding_days
        ))
    
    return trades


def backtest_all(stock_data: dict, stock_names: dict, params: dict,
                 start_date: str, end_date: str) -> BacktestResult:
    """全市场回测
    
    Args:
        stock_data: {code: DataFrame} 股票数据字典
        stock_names: {code: name} 股票名称字典
        params: 参数配置
        start_date: 回测开始日期
        end_date: 回测结束日期
        
    Returns:
        BacktestResult: 回测结果
    """
    all_trades = []
    
    for code, df in stock_data.items():
        name = stock_names.get(code, code)
        trades = backtest_single(code, name, df.copy(), params, start_date, end_date)
        all_trades.extend(trades)
    
    # 计算统计指标
    if not all_trades:
        return BacktestResult(
            start_date=start_date,
            end_date=end_date,
            total_trades=0,
            win_rate=0,
            avg_return=0,
            max_profit=0,
            max_loss=0,
            profit_loss_ratio=0,
            cumulative_return=0,
            trades=[]
        )
    
    returns = [t.return_pct for t in all_trades]
    wins = [r for r in returns if r > 0]
    losses = [r for r in returns if r < 0]
    
    win_rate = len(wins) / len(returns) if returns else 0
    avg_return = sum(returns) / len(returns) if returns else 0
    max_profit = max(returns) if returns else 0
    max_loss = min(returns) if returns else 0
    
    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = abs(sum(losses) / len(losses)) if losses else 1
    profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0
    
    # 累计收益（假设等仓位）
    cumulative_return = sum(returns)
    
    return BacktestResult(
        start_date=start_date,
        end_date=end_date,
        total_trades=len(all_trades),
        win_rate=round(win_rate, 4),
        avg_return=round(avg_return, 4),
        max_profit=round(max_profit, 4),
        max_loss=round(max_loss, 4),
        profit_loss_ratio=round(profit_loss_ratio, 2),
        cumulative_return=round(cumulative_return, 4),
        trades=all_trades
    )
