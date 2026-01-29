import pandas as pd
import json
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from polymarket_data_fetcher import PolymarketDataFetcher


class FixedBetStrategyAnalyzer:
    def __init__(self):
        self.fetcher = PolymarketDataFetcher()
        self.market_cache = {}

    def analyze_strategy(self, address: str, limit: int = 500):
        print(f"📊 正在分析跟单策略 (固定金额 $5): {address} ...")
        
        # 1. 获取交易数据
        trades = self.fetcher.get_trades(wallet_address=address, limit=limit)
        
        if trades.empty:
            print("❌ 未找到交易记录")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        # print(f"\n📋 原始交易记录 ({len(trades)} 条):")
        # 尝试只打印关键列，如果存在
        # display_cols = ['matchTime', 'title', 'outcome', 'side', 'price', 'size']
        # cols_to_show = [c for c in display_cols if c in trades.columns]
        # if cols_to_show:
        #     pd.set_option('display.max_rows', None)  # 允许打印所有行
        #     pd.set_option('display.max_columns', None)
        #     pd.set_option('display.width', 1000)
        #     # print(trades[cols_to_show].to_string())
        #     pd.reset_option('display.max_rows') # 重置
        # else:
        #     # print(trades.to_string())

        # 2. 数据清洗和策略模拟
        print("\n🤖 开始模拟策略交易执行... (已隐藏详细日志)")
        analysis_df, active_pos_df, stats = self._simulate_strategy(trades)
        
        return analysis_df, trades, active_pos_df, stats

    def _simulate_strategy(self, trades_df):
        """
        模拟策略执行：
        - 每次对方买入，我们尝试买入 $5 (取整股数)
        - 对方卖出，我们清仓 (Sell All)
        - 计算持有到期盈亏
        """
        df = trades_df.copy()
        
        # 格式转换
        df['size'] = pd.to_numeric(df['size'], errors='coerce').fillna(0)
        df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
        df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
        df['date'] = pd.to_datetime(df['timestamp'], unit='s')
        
        # 按时间正序排列
        df = df.sort_values('date')
        
        # 策略状态维护
        # positions key=(conditionId, outcome) 
        # value={'vol': int (股数), 'cost': float (总成本), 'avg_price': float}
        my_positions = {} 
        pnl_events = []
        
        FIXED_BET_AMOUNT = 5.0  # 每次定投金额
        
        # 策略统计计数器
        stats = {
            'processed_rows': 0,
            'strategy_buys': 0,
            'strategy_sells': 0,
            'settlements': 0,
            'total_investment': 0.0,
            'unique_targets': set()  # 统计涉及的独立标的
        }

        # 1. 第一遍扫描：模拟交易流程
        for row in df.itertuples():
            stats['processed_rows'] += 1
            cid = row.conditionId
            side = str(row.side).strip().upper()
            price = row.price
            market_name = getattr(row, 'title', 'Unknown Market')
            outcome = getattr(row, 'outcome', '-')
            date = row.date
            slug = getattr(row, 'slug', None)
            
            key = (cid, outcome)
            
            if key not in my_positions:
                my_positions[key] = {
                    'vol': 0, 
                    'cost': 0.0, 
                    'market_name': market_name, 
                    'slug': slug,
                    'condition_id': cid,
                    'last_date': date
                }
                
            pos = my_positions[key]
            pos['last_date'] = date 
            
            pnl = 0
            is_close = False
            
            if side == 'BUY':
                # 策略：买入 $5
                if price > 0:
                    vol_to_buy = int(FIXED_BET_AMOUNT / price)
                    
                    if vol_to_buy > 0:
                        cost_for_buy = vol_to_buy * price
                        
                        pos['vol'] += vol_to_buy
                        pos['cost'] += cost_for_buy
                        
                        stats['strategy_buys'] += 1
                        stats['total_investment'] += cost_for_buy
                        stats['unique_targets'].add(key)
                        
                        # (已隐藏详细买入日志)
                        # print(f"🔵 [{date}] 跟单买入 | 市场: {market_name[:30]}... | 选项: {outcome} | 价格: {price} | 股数: {vol_to_buy} | 花费: ${cost_for_buy:.2f}")

            elif side == 'SELL':
                # 策略：如果对方卖出，我们全卖 (Sell All)
                if pos['vol'] > 0:
                    sell_price = price
                    sell_vol = pos['vol'] # 全部卖出
                    
                    revenue = sell_vol * sell_price
                    cost_basis = pos['cost']
                    
                    pnl = revenue - cost_basis
                    is_close = True
                    
                    stats['strategy_sells'] += 1
                    # print(f"🔴 [{date}] 触发卖出 | 市场: {market_name[:30]}... | 选项: {outcome} | 价格: {price} | 卖出股数: {sell_vol} | 收入: ${revenue:.2f} | 盈亏: ${pnl:.2f}")

                    # 清空持仓
                    pos['vol'] = 0
                    pos['cost'] = 0.0
            
            if is_close:
                pnl_events.append({
                    'date': date,
                    'pnl': pnl,
                    'market': market_name,
                    'outcome': outcome,
                    'type': 'Trade'
                })

        # --- 并行预取市场信息 (用于结算计算) ---
        unique_markets = {}
        for (cid, outcome), pos in my_positions.items():
            if cid not in unique_markets:
                unique_markets[cid] = pos.get('slug')
        
        self._prefetch_markets(unique_markets)
        # ------------------------------------

        # print(f"\n🔍 结算前持仓诊断 (Unique Positions: {len(my_positions)}):")
        # 2. 第二遍扫描：计算结算盈亏 (Settlement)
        # 对剩余持仓进行结算检查
        for (cid, outcome), pos in my_positions.items():
            # status_msg = ""
            is_settled = False
            
            if pos['vol'] > 0: # 还有持仓
                market_info = self._get_market_info_cached(cid, slug=pos.get('slug'))
                
                is_closed = market_info and market_info.get('closed', False)
                # closed_time = market_info.get('closedTime') if market_info else 'N/A'
                
                if market_info and is_closed:
                    # 尝试结算
                    try:
                        outcomes_list = json.loads(market_info.get('outcomes', '[]'))
                        prices_list = json.loads(market_info.get('outcomePrices', '[]'))
                        if outcomes_list and prices_list:
                            is_settled = True
                    except:
                        pass

                # print(f"  - [{outcome}] {pos['market_name'][:40]}... | 持仓: {pos['vol']} | {status_msg}")

                if not is_settled:
                    continue
                
                # 获取结算结果 (原有逻辑)
                try:
                    outcomes_list = json.loads(market_info.get('outcomes', '[]'))
                    prices_list = json.loads(market_info.get('outcomePrices', '[]'))
                except:
                    continue
                    
                if not outcomes_list or not prices_list:
                    continue
                    
                # 判定赢家
                winner_outcome = None
                for idx, price_str in enumerate(prices_list):
                    try:
                        if float(price_str) > 0.95:
                            winner_outcome = outcomes_list[idx]
                            break
                    except:
                        pass
                
                # 计算结算价值
                settlement_val = 0
                if winner_outcome and outcome == winner_outcome:
                    settlement_val = pos['vol'] * 1.0 # 赢了，$1/股
                else:
                    settlement_val = 0 # 输了，归零
                
                # 结算盈亏 = 最终价值 - 成本
                settlement_pnl = settlement_val - pos['cost']
                
                settle_date = pos['last_date'] 
                if market_info.get('closedTime'):
                    try:
                        dt = pd.to_datetime(market_info['closedTime'])
                        if dt.tzinfo is not None:
                            dt = dt.tz_localize(None)
                        if dt.year >= 2021 and dt >= pos['last_date']:
                            settle_date = dt
                    except:
                        pass
                
                stats['settlements'] += 1
                pnl_events.append({
                    'date': settle_date,
                    'pnl': settlement_pnl,
                    'market': pos['market_name'],
                    'outcome': outcome,
                    'type': 'Settlement'
                })
            else:
                # 仓位已在之前的 Sell 操作中清空
                # print(f"  - [{outcome}] {pos['market_name'][:30]}... | 持仓: 0 (已平仓)")
                pass

        # 3. 收集当前活跃仓位 (Strategy Active Positions)
        active_pos_list = []
        for (cid, outcome), pos in my_positions.items():
            if pos['vol'] > 0:
                market_info = self._get_market_info_cached(cid, slug=pos.get('slug'))
                # 只有市场未结束的才算“活跃仓位”
                if not market_info or not market_info.get('closed', False):
                    active_pos_list.append({
                        'market': pos['market_name'],
                        'outcome': outcome,
                        'size': pos['vol'],
                        'cost': pos['cost']
                    })
        
        active_pos_df = pd.DataFrame(active_pos_list)
        if not active_pos_df.empty:
            total_cost = active_pos_df['cost'].sum()
            active_pos_df['weight'] = (active_pos_df['cost'] / total_cost * 100) if total_cost > 0 else 0
            active_pos_df = active_pos_df.sort_values('cost', ascending=False)

        result_df = pd.DataFrame(pnl_events)
        if not result_df.empty:
            result_df = result_df.sort_values('date')
            result_df['cumulative_pnl'] = result_df['pnl'].cumsum()
            
        return result_df, active_pos_df, stats

    def _prefetch_markets(self, market_dict: dict):
        # 复用原有的逻辑，需保留
        todo = []
        for cid, slug in market_dict.items():
            if cid not in self.market_cache:
                todo.append((cid, slug))
        
        if not todo:
            return

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_cid = {executor.submit(self._get_market_info_inner, cid, slug): cid for cid, slug in todo}
            for future in as_completed(future_to_cid):
                cid = future_to_cid[future]
                try:
                    info = future.result()
                    self.market_cache[cid] = info
                except:
                    self.market_cache[cid] = None

    def _get_market_info_inner(self, condition_id, slug=None):
        try:
            df = pd.DataFrame()
            if slug:
                df = self.fetcher.get_markets(slug=slug)
            
            if df.empty:
                df = self.fetcher.get_markets(condition_id=condition_id)
            
            if not df.empty:
                match_row = None
                for _, row in df.iterrows():
                    fetched_cid = row.get('conditionId') or row.get('condition_id')
                    if fetched_cid and str(fetched_cid).lower() == str(condition_id).lower():
                        match_row = row
                        break
                if match_row is not None:
                    return match_row.to_dict()
        except:
            pass
        return None

    def _get_market_info_cached(self, condition_id, slug=None):
        if condition_id in self.market_cache:
            return self.market_cache[condition_id]
        info = self._get_market_info_inner(condition_id, slug)
        self.market_cache[condition_id] = info
        return info

if __name__ == "__main__":
    import sys
    # Default: tyson
    demo_addr = "0xdb27bf2ac5d428a9c63dbc914611036855a6c56e"
    if len(sys.argv) > 1:
        demo_addr = sys.argv[1]
        
    print(f"🚀 运行固定金额($5)跟单模拟 (Address: {demo_addr})...")
    
    analyzer = FixedBetStrategyAnalyzer()
    pnl_df, raw_trades, active_df, stats = analyzer.analyze_strategy(demo_addr, limit=5000)
    
    if not raw_trades.empty:
        csv_filename = f"trades_{demo_addr}.csv"
        raw_trades.to_csv(csv_filename, index=False)
        print(f"\n💾 原始交易流水已保存至: {csv_filename}")

    if not pnl_df.empty or stats['processed_rows'] > 0:
        print("\n📈 模拟策略统计结果:")
        print(f"  - 处理原始交易数: {stats['processed_rows']}")
        print(f"  - 策略主动买入次数: {stats['strategy_buys']}")
        print(f"  - 涉及独立标的数: {len(stats['unique_targets'])} (平均每标的买入 {stats['strategy_buys']/len(stats['unique_targets']):.1f} 次)")
        print(f"  - 策略主动卖出次数: {stats['strategy_sells']}")
        print(f"  - 市场自动结算次数: {stats['settlements']}")
        print(f"  - 总投入本金(估算): ${stats['total_investment']:.2f}")
        print(f"  ---------------------------")
        if not pnl_df.empty:
            print(f"  - 累计盈亏: ${pnl_df['cumulative_pnl'].iloc[-1]:.2f}")
            print(f"  - 实现盈亏事件数: {len(pnl_df)} (卖出+结算)")
        else:
            print(f"  - 累计盈亏: $0.00")
    
    if not active_df.empty:
        print("\n💰 当前活跃模拟仓位:")
        print(active_df[['market', 'outcome', 'cost', 'weight']].to_string(index=False))
