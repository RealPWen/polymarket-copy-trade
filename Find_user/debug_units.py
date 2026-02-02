
import requests
import json
import sys

# 设置输出编码为 utf-8
sys.stdout.reconfigure(encoding='utf-8')

USER = "0xd82079c0d6b837bad90abf202befc079da5819f6" # Maze8
URL_CLOSED = "https://data-api.polymarket.com/v1/closed-positions"
URL_ACTIVE = "https://data-api.polymarket.com/positions"

print(f"Checking user: {USER}")

print("--- Active Positions ---")
try:
    resp = requests.get(URL_ACTIVE, params={"user": USER, "limit": 2})
    if resp.status_code == 200:
        data = resp.json()
        for item in data:
            print(f"Market: {item.get('slug')}")
            print(f"percentPnl: {item.get('percentPnl')} (Type: {type(item.get('percentPnl'))})")
            print(f"cashPnl: {item.get('cashPnl')}")
            print(f"totalBought: {item.get('totalBought')}")
            print("-" * 20)
    else:
        print(f"Error Active: {resp.status_code}")
except Exception as e:
    print(e)

print("\n--- Closed Positions ---")
try:
    resp = requests.get(URL_CLOSED, params={"user": USER, "limit": 2})
    if resp.status_code == 200:
        data = resp.json()
        for item in data:
            print(f"Market: {item.get('slug')}")
            print(f"percentRoi: {item.get('percentRoi')} (Type: {type(item.get('percentRoi'))})")
            print(f"realizedPnl: {item.get('realizedPnl')}")
            print(f"totalBought: {item.get('totalBought')}")
            if item.get('totalBought') and item.get('totalBought') > 0:
                print(f"Calculated ROI: {item.get('realizedPnl') / item.get('totalBought')}")
            print("-" * 20)
    else:
        print(f"Error Closed: {resp.status_code}")
except Exception as e:
    print(e)
