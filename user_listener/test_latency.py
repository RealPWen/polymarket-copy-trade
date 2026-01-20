import time
from user_listener.polymarket_data_fetcher import PolymarketDataFetcher

def test_api_latency():
    fetcher = PolymarketDataFetcher()
    wallet = "0xdb27bf2ac5d428a9c63dbc914611036855a6c56e"
    
    print(f"开始测试 Polymarket Data API 响应时间...")
    print(f"目标账户: {wallet}")
    print("-" * 50)
    
    latencies = []
    for i in range(5):
        start_time = time.perf_counter()
        # 模拟监听器中的调用：获取最近10条交易，不打印日志
        fetcher.get_trades(wallet_address=wallet, limit=10, silent=True)
        end_time = time.perf_counter()
        
        latency = (end_time - start_time) * 1000
        latencies.append(latency)
        print(f"第 {i+1} 次请求耗时: {latency:.2f} ms")
        time.sleep(1)  # 避免请求过快
        
    avg_latency = sum(latencies) / len(latencies)
    print("-" * 50)
    print(f"平均响应时间: {avg_latency:.2f} ms")
    print(f"最快响应: {min(latencies):.2f} ms")
    print(f"最慢响应: {max(latencies):.2f} ms")

if __name__ == "__main__":
    try:
        test_api_latency()
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
