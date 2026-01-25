import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'user_listener'))
import config
from polymarket_data_fetcher import PolymarketDataFetcher
import pandas as pd

def main():
    f = PolymarketDataFetcher()
    address = config.FUNDER_ADDRESS
    print(f"Checking positions for: {address}")
    
    positions = f.get_user_positions(address)
    if not positions.empty:
        print("Columns:", positions.columns.tolist())
        print("\nAll Positions Data:")
        # Print all columns for the first few rows to see what we can filter on
        for idx, row in positions.iterrows():
            print(f"\n--- Item {idx} ---")
            print(f"Title: {row.get('title')}")
            print(f"Size: {row.get('size')}")
            print(f"Value: {row.get('currentValue')}") # Check if this exists
            print(f"Price: {row.get('price')}") # Check if this exists
            print(row.to_dict())
    else:
        print("No positions found.")

if __name__ == "__main__":
    main()
