import time
from datetime import datetime
try:
    from user_listener.polymarket_data_fetcher import PolymarketDataFetcher
except ImportError:
    from polymarket_data_fetcher import PolymarketDataFetcher
import pandas as pd

class AccountListener:
    def __init__(self, wallet_address: str, poll_interval: int = 5):
        self.fetcher = PolymarketDataFetcher()
        self.wallet_address = wallet_address.lower()
        self.poll_interval = poll_interval
        self.last_timestamp = 0
        self.last_hashes = set()

    def _format_trade(self, trade):
        """格式化输出单条交易信息"""
        ts = datetime.fromtimestamp(trade['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        side = trade['side']
        outcome = trade['outcome']
        size = trade['size']
        price = trade['price']
        title = trade['title']
        tx_hash = trade['transactionHash']
        
        # 简单颜色模拟 (ANSI)
        color = "\033[92m" if side == "BUY" else "\033[91m"
        reset = "\033[0m"
        
        return f"[{ts}] {color}{side}{reset} {size:.2f} @ {price:.3f} | {outcome} | {title} | Hash: {tx_hash[:10]}..."

    def start_listening(self):
        print(f"🚀 开始监听账户: {self.wallet_address}")
        print(f"⏱️  轮询间隔: {self.poll_interval} 秒")
        print("-" * 80)

        # 首次运行时，获取最新的一条作为起点，避免打印历史交易
        try:
            initial_trades = self.fetcher.get_trades(wallet_address=self.wallet_address, limit=1, silent=True)
            if not initial_trades.empty:
                self.last_timestamp = initial_trades.iloc[0]['timestamp']
                self.last_hashes.add(initial_trades.iloc[0]['transactionHash'])
                print(f"📍 设置初始起点: {datetime.fromtimestamp(self.last_timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print("⚠️  该账户目前没有任何历史交易。")
        except Exception as e:
            print(f"❌ 初始化失败: {e}")

        while True:
            try:
                now = datetime.now().strftime('%H:%M:%S')
                # 获取最近的交易
                trades_df = self.fetcher.get_trades(wallet_address=self.wallet_address, limit=10, silent=True)
                
                num_fetched = len(trades_df)
                new_count = 0

                if not trades_df.empty:
                    # 过滤出新的交易 (timestamp >= last_timestamp 且 hash 不在已记录中)
                    new_trades = trades_df[
                        (trades_df['timestamp'] >= self.last_timestamp) & 
                        (~trades_df['transactionHash'].isin(self.last_hashes))
                    ]

                    if not new_trades.empty:
                        new_count = len(new_trades)
                        # 如果有新交易，先换行避免覆盖 heartbeat
                        print(f"\n🔔 [发现新交易] {now}")
                        
                        # 按时间正序排列（先打印旧的，再打印新的）
                        new_trades = new_trades.sort_values('timestamp', ascending=True)
                        
                        for _, trade in new_trades.iterrows():
                            print(self._format_trade(trade))
                            
                            # 更新状态
                            self.last_timestamp = max(self.last_timestamp, trade['timestamp'])
                            self.last_hashes.add(trade['transactionHash'])
                        
                        if len(self.last_hashes) > 100:
                            self.last_hashes = set(new_trades['transactionHash'].tolist())
                
                # 如果没有新交易，打印一个原地更新的“心跳”信息
                if new_count == 0:
                    print(f"\r🔍 [{now}] 正在监听... (获取到 {num_fetched} 条历史数据，无新动态)", end="", flush=True)

                time.sleep(self.poll_interval)
                
            except KeyboardInterrupt:
                print("\n🛑 停止监听。")
                break
            except Exception as e:
                print(f"❌ 监听出错: {e}")
                time.sleep(self.poll_interval)

if __name__ == "__main__":
    import sys
    
    # 默认账户（用户刚才查询的那个）
    default_wallet = "0xdb27bf2ac5d428a9c63dbc914611036855a6c56e"
    
    target_wallet = sys.argv[1] if len(sys.argv) > 1 else default_wallet
    
    listener = AccountListener(target_wallet)
    listener.start_listening()
