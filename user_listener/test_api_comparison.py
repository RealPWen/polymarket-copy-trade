
import requests
import pandas as pd
import json
from datetime import datetime

# Setup
WALLET = "0xd82079c0d6b837bad90abf202befc079da5819f6"
DATA_API_BASE = "https://data-api.polymarket.com"

def fetch_activity(wallet, limit=20):
    url = f"{DATA_API_BASE}/activity"
    params = {"user": wallet, "limit": limit}
    r = requests.get(url, params=params)
    if r.status_code == 200:
        return r.json()
    return []

def fetch_trades(wallet, limit=20, taker_only=True):
    url = f"{DATA_API_BASE}/trades"
    params = {
        "user": wallet, 
        "limit": limit,
        "takerOnly": str(taker_only).lower()
    }
    r = requests.get(url, params=params)
    if r.status_code == 200:
        return r.json()
    return []


# Redirect output to file
import sys

class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("comparison_report.txt", "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

sys.stdout = Logger()

# 1. Fetch Data
print(f"🔍 Analyzing Wallet: {WALLET}")

print("\n--- 1. Fetching Activity API (Generic) ---")
activities = fetch_activity(WALLET)
df_activity = pd.DataFrame(activities)
print(f"Fetched {len(activities)} activity records.")
if not df_activity.empty:
    print(df_activity[['timestamp', 'type', 'side', 'size', 'title']].head(10).to_string())

print("\n--- 2. Fetching Trade API (takerOnly=true [Default]) ---")
trades_taker = fetch_trades(WALLET, taker_only=True)
df_trades_taker = pd.DataFrame(trades_taker)
print(f"Fetched {len(trades_taker)} taker-only trades.")
if not df_trades_taker.empty:
    print(df_trades_taker[['timestamp', 'side', 'size', 'title']].head(10).to_string())

print("\n--- 3. Fetching Trade API (takerOnly=false [Full]) ---")
trades_full = fetch_trades(WALLET, taker_only=False)
df_trades_full = pd.DataFrame(trades_full)
print(f"Fetched {len(trades_full)} full trades (Maker+Taker).")
if not df_trades_full.empty:
    print(df_trades_full[['timestamp', 'side', 'size', 'title']].head(10).to_string())


# 2. Detailed Comparison (Last 5 transactions)
print("\n" + "="*50)
print("COMPARING LAST 5 TRANSACTIONS")
print("="*50)

# We will look at unique timestamps to group events
timestamps = set()
for a in activities[:10]: timestamps.add(a.get('timestamp'))
for t in trades_full[:10]: timestamps.add(t.get('timestamp'))

sorted_ts = sorted(list(timestamps), reverse=True)[:5]

for ts in sorted_ts:
    time_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n⏰ Time: {time_str} ({ts})")
    
    # Activity
    act_match = [a for a in activities if a.get('timestamp') == ts]
    if act_match:
        print(f"  [Activity API]: Found {len(act_match)} records")
        for a in act_match:
            print(f"    - Type: {a.get('type')} | Side: {a.get('side')} | Size: {a.get('size')} | Price: {a.get('price')}")
    else:
        print(f"  [Activity API]: No records")

    # Trade (Full)
    trade_match = [t for t in trades_full if t.get('timestamp') == ts]
    if trade_match:
        print(f"  [Trade API]   : Found {len(trade_match)} records")
        for t in trade_match:
            # Check if it exists in taker list
            is_taker = any(t.get('transactionHash') == tt.get('transactionHash') and t.get('size') == tt.get('size') for tt in trades_taker)
            role = "TAKER" if is_taker else "MAKER"
            print(f"    - Role: {role} | Side: {t.get('side')} | Size: {t.get('size')} | Price: {t.get('price')}")
    else:
        print(f"  [Trade API]   : No records")

