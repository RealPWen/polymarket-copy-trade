import os
import sys
# 添加模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'user_listener'))

from polymarket_data_fetcher import PolymarketDataFetcher
import json

def check():
    fetcher = PolymarketDataFetcher()
    # 使用环境变量中的地址，或者硬编码一个测试地址
    address = "0xdb27bf2ac5d428a9c63dbc914611036855a6c56e" # 之前看到的那个活跃地址
    
    print(f"Checking positions for {address}...")
    df = fetcher.get_user_positions(address, limit=5)
    
    if not df.empty:
        print("\nColumns:", df.columns.tolist())
        print("\nFirst record example:")
        print(json.dumps(df.iloc[0].to_dict(), indent=2, default=str))
    else:
        print("No positions found.")

if __name__ == "__main__":
    check()
