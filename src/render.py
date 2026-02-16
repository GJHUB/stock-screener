"""页面渲染模块 - 使用 Jinja2"""

import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import pandas as pd
from .backtest import BacktestResult


def get_template_env(template_dir: str = None) -> Environment:
    """获取 Jinja2 模板环境"""
    if template_dir is None:
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
    return Environment(loader=FileSystemLoader(template_dir))


def render_daily_result(stocks: pd.DataFrame, date: str, template_dir: str = None) -> str:
    """渲染每日选股结果
    
    Args:
        stocks: 选股结果 DataFrame
        date: 日期字符串
        template_dir: 模板目录
        
    Returns:
        str: 渲染后的 HTML
    """
    env = get_template_env(template_dir)
    template = env.get_template('daily.html')
    
    stocks_list = stocks.to_dict('records') if not stocks.empty else []
    
    return template.render(
        date=date,
        stocks=stocks_list,
        count=len(stocks_list),
        generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )


def render_backtest_report(result: BacktestResult, template_dir: str = None) -> str:
    """渲染回测报告
    
    Args:
        result: 回测结果
        template_dir: 模板目录
        
    Returns:
        str: 渲染后的 HTML
    """
    env = get_template_env(template_dir)
    template = env.get_template('backtest.html')
    
    # 转换交易记录为字典列表
    trades_list = [
        {
            'code': t.code,
            'name': t.name,
            'buy_date': t.buy_date,
            'buy_price': t.buy_price,
            'sell_date': t.sell_date,
            'sell_price': t.sell_price,
            'sell_reason': t.sell_reason,
            'return_pct': f"{t.return_pct * 100:.2f}%",
            'return_class': 'positive' if t.return_pct > 0 else 'negative',
            'holding_days': t.holding_days
        }
        for t in result.trades
    ]
    
    return template.render(
        start_date=result.start_date,
        end_date=result.end_date,
        total_trades=result.total_trades,
        win_rate=f"{result.win_rate * 100:.1f}%",
        avg_return=f"{result.avg_return * 100:.2f}%",
        max_profit=f"{result.max_profit * 100:.2f}%",
        max_loss=f"{result.max_loss * 100:.2f}%",
        profit_loss_ratio=f"{result.profit_loss_ratio:.2f}",
        cumulative_return=f"{result.cumulative_return * 100:.2f}%",
        trades=trades_list,
        generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )


def render_history_index(dates: list, template_dir: str = None) -> str:
    """渲染历史归档索引
    
    Args:
        dates: 日期列表
        template_dir: 模板目录
        
    Returns:
        str: 渲染后的 HTML
    """
    env = get_template_env(template_dir)
    template = env.get_template('history.html')
    
    return template.render(
        dates=sorted(dates, reverse=True),
        generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )


def save_pages(output_dir: str, daily_html: str, date: str,
               backtest_html: str = None, history_dates: list = None,
               template_dir: str = None):
    """保存所有页面到指定目录
    
    Args:
        output_dir: 输出目录（docs/）
        daily_html: 每日结果 HTML
        date: 当前日期
        backtest_html: 回测报告 HTML（可选）
        history_dates: 历史日期列表（可选）
        template_dir: 模板目录
    """
    # 确保目录存在
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'history'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'assets'), exist_ok=True)
    
    # 保存最新结果为 index.html
    with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(daily_html)
    
    # 保存到历史目录
    with open(os.path.join(output_dir, 'history', f'{date}.html'), 'w', encoding='utf-8') as f:
        f.write(daily_html)
    
    # 保存回测报告
    if backtest_html:
        with open(os.path.join(output_dir, 'backtest.html'), 'w', encoding='utf-8') as f:
            f.write(backtest_html)
    
    # 更新历史索引
    if history_dates:
        history_html = render_history_index(history_dates, template_dir)
        with open(os.path.join(output_dir, 'history', 'index.html'), 'w', encoding='utf-8') as f:
            f.write(history_html)
    
    # 复制 CSS 文件
    css_content = get_css_content()
    with open(os.path.join(output_dir, 'assets', 'style.css'), 'w', encoding='utf-8') as f:
        f.write(css_content)


def get_css_content() -> str:
    """获取 CSS 样式内容"""
    return """
:root {
    --primary-color: #1a73e8;
    --success-color: #34a853;
    --danger-color: #ea4335;
    --bg-color: #f8f9fa;
    --card-bg: #ffffff;
    --text-color: #202124;
    --text-secondary: #5f6368;
    --border-color: #dadce0;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background-color: var(--bg-color);
    color: var(--text-color);
    line-height: 1.6;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

header {
    background: var(--primary-color);
    color: white;
    padding: 20px 0;
    margin-bottom: 30px;
}

header h1 {
    font-size: 24px;
    font-weight: 500;
}

header .date {
    opacity: 0.9;
    font-size: 14px;
}

.card {
    background: var(--card-bg);
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    padding: 20px;
    margin-bottom: 20px;
}

.card h2 {
    font-size: 18px;
    margin-bottom: 15px;
    color: var(--text-color);
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 15px;
}

.stat-item {
    text-align: center;
    padding: 15px;
    background: var(--bg-color);
    border-radius: 8px;
}

.stat-value {
    font-size: 24px;
    font-weight: 600;
    color: var(--primary-color);
}

.stat-label {
    font-size: 12px;
    color: var(--text-secondary);
    margin-top: 5px;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}

th {
    background: var(--bg-color);
    font-weight: 500;
    color: var(--text-secondary);
    font-size: 12px;
    text-transform: uppercase;
}

tr:hover {
    background: var(--bg-color);
}

.positive {
    color: var(--success-color);
}

.negative {
    color: var(--danger-color);
}

.reason {
    font-size: 12px;
    color: var(--text-secondary);
    max-width: 300px;
}

.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: var(--text-secondary);
}

.empty-state svg {
    width: 64px;
    height: 64px;
    margin-bottom: 20px;
    opacity: 0.5;
}

footer {
    text-align: center;
    padding: 20px;
    color: var(--text-secondary);
    font-size: 12px;
}

.nav-links {
    margin-top: 10px;
}

.nav-links a {
    color: rgba(255,255,255,0.9);
    text-decoration: none;
    margin-right: 20px;
}

.nav-links a:hover {
    text-decoration: underline;
}

.history-list {
    list-style: none;
}

.history-list li {
    padding: 10px 0;
    border-bottom: 1px solid var(--border-color);
}

.history-list a {
    color: var(--primary-color);
    text-decoration: none;
}

.history-list a:hover {
    text-decoration: underline;
}

@media (max-width: 768px) {
    .container {
        padding: 10px;
    }
    
    table {
        font-size: 14px;
    }
    
    th, td {
        padding: 8px;
    }
    
    .reason {
        display: none;
    }
}
"""
