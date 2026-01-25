import sys
import os

# Add user_listener to path
sys.path.append(os.path.join(os.getcwd(), 'user_listener'))

import config
from polymarket_data_fetcher import PolymarketDataFetcher
import pandas as pd

def main():
    try:
        f = PolymarketDataFetcher()
        address = config.FUNDER_ADDRESS
        print(f"Checking address: {address}")

        # 1. Check Trades (for API check)
        print("\n--- TRADES (API) ---")
        trades_df = f.get_trades(wallet_address=address, limit=5)
        if not trades_df.empty:
            print("Columns:", trades_df.columns.tolist())
            first_trade = trades_df.iloc[0].to_dict()
            print("Sample Trade keys:", first_trade.keys())
            if 'title' in first_trade:
                print(f"Title present: {first_trade['title']}")
            else:
                print("WARNING: 'title' field NOT found in trades API response.")
        else:
            print("No trades found.")

        # 2. Check Positions (for UFC issue)
        print("\n--- POSITIONS (API) ---")
        pos_df = f.get_user_positions(address)
        if not pos_df.empty:
            if 'title' in pos_df.columns and 'size' in pos_df.columns:
                print(pos_df[['title', 'size']].to_string())
            else:
                print(pos_df.head().to_string())
        else:
            print("No positions found.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
