#!/usr/bin/env python3
"""股票日K筛选器 - 入口脚本"""

import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import PARAMS, DATA_DAYS
from src.data import get_stock_list, get_all_stocks_history
from src.strategy import screen_stocks
from src.backtest import backtest_all
from src.render import render_daily_result, render_backtest_report, save_pages


def get_history_dates(output_dir: str) -> list:
    """获取已有的历史日期列表"""
    history_dir = os.path.join(output_dir, 'history')
    if not os.path.exists(history_dir):
        return []
    
    dates = []
    for f in os.listdir(history_dir):
        if f.endswith('.html') and f != 'index.html':
            dates.append(f.replace('.html', ''))
    return dates


def main():
    """主函数"""
    print("=" * 50)
    print("股票日K筛选器 - 缩量超卖买点策略")
    print("=" * 50)
    
    # 检查 Tushare Token
    if not os.environ.get('TUSHARE_TOKEN'):
        print("\n❌ 错误: TUSHARE_TOKEN 环境变量未设置")
        print("请设置 Tushare Pro Token:")
        print("  export TUSHARE_TOKEN='your_token_here'")
        print("或在 GitHub Secrets 中添加 TUSHARE_TOKEN")
        sys.exit(1)
    
    # 获取当前日期
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"\n📅 运行日期: {today}")
    
    # 输出目录
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs')
    
    try:
        # Step 1: 获取股票列表
        print("\n📊 Step 1: 获取A股列表...")
        stock_list = get_stock_list()
        print(f"   共 {len(stock_list)} 只股票（已剔除ST和停牌）")
        
        # 构建名称字典
        stock_names = dict(zip(stock_list['代码'], stock_list['名称']))
        codes = stock_list['代码'].tolist()
        
        # Step 2: 获取历史数据
        print(f"\n📈 Step 2: 获取历史K线数据（最近{DATA_DAYS}天）...")
        stock_data = get_all_stocks_history(codes, days=DATA_DAYS)
        
        if not stock_data:
            print("   ⚠️ 未获取到有效数据")
            result_df = None
        else:
            # Step 3: 策略筛选
            print("\n🔍 Step 3: 执行策略筛选...")
            result_df = screen_stocks(stock_data, stock_names, PARAMS)
            print(f"   筛选出 {len(result_df)} 只符合条件的股票")
            
            if not result_df.empty:
                print("\n📋 筛选结果:")
                print(result_df[['代码', '名称', '当前价', '涨跌幅', 'J值', 'DIFF']].to_string(index=False))
        
        # Step 4: 渲染页面
        print("\n🎨 Step 4: 生成HTML页面...")
        if result_df is None:
            import pandas as pd
            result_df = pd.DataFrame()
        daily_html = render_daily_result(result_df, today)
        
        # Step 5: 回测（可选）
        backtest_html = None
        if stock_data:
            try:
                print("\n📊 Step 5: 执行策略回测...")
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
                
                backtest_result = backtest_all(stock_data, stock_names, PARAMS, start_date, end_date)
                
                if backtest_result.total_trades > 0:
                    print(f"   回测区间: {start_date} ~ {end_date}")
                    print(f"   总交易次数: {backtest_result.total_trades}")
                    print(f"   胜率: {backtest_result.win_rate * 100:.1f}%")
                    print(f"   平均收益: {backtest_result.avg_return * 100:.2f}%")
                    print(f"   累计收益: {backtest_result.cumulative_return * 100:.2f}%")
                    
                    backtest_html = render_backtest_report(backtest_result)
                else:
                    print("   回测期间无交易信号")
            except Exception as e:
                print(f"   回测跳过: {e}")
        
        # Step 6: 保存页面
        print("\n💾 Step 6: 保存页面...")
        history_dates = get_history_dates(output_dir)
        if today not in history_dates:
            history_dates.append(today)
        
        save_pages(
            output_dir=output_dir,
            daily_html=daily_html,
            date=today,
            backtest_html=backtest_html,
            history_dates=history_dates
        )
        
        print(f"\n✅ 完成！结果已保存到 {output_dir}/")
        
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("=" * 50)


if __name__ == '__main__':
    main()
