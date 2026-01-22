
import os
import json
from polymarket_data_fetcher import PolymarketDataFetcher
import config

def test_balance():
    fetcher = PolymarketDataFetcher()
    address = config.FUNDER_ADDRESS
    print(f"Checking balance for: {address}")
    
    val_data = fetcher.get_user_value(address)
    print("Full Portfolio Data:")
    print(json.dumps(val_data, indent=2))
    
    cash = val_data.get('cash')
    print(f"Cash (raw): {cash}")
    
    balance = fetcher.get_user_cash_balance(address)
    print(f"Balance (method): {balance}")

if __name__ == "__main__":
    test_balance()
