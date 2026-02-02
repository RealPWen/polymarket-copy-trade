"""
Understand the specific trade issue by checking all recorded trades for a tx hash.
"""
import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

def main():
    # The two transactions in question
    tx_hash_4778_no = "0xdcdbadc6bf3fce24254d5ba1775d5be1da5784be891d3e913b9d3791578e41fa"
    tx_hash_26k_yes = "0xc7a4f8d80127ec3093dac49df9f832b1e4168202eab4cd4c051c51db2e481266"
    
    condition_id = "0xe986a6eb382842e20ef258af982525779d01a1d1a7d58700c42364da8c43e838"
    
    # Get event data to understand token mapping
    slug = "ucl-ben1-rma1-2026-01-28"
    event_url = f"https://gamma-api.polymarket.com/events/slug/{slug}"
    event_resp = requests.get(event_url)
    event = event_resp.json()
    
    benfica_market = None
    for market in event.get("markets", []):
        if "Benfica win" in market.get("question", ""):
            benfica_market = market
            break
    
    outcomes = json.loads(benfica_market.get('outcomes', '[]'))
    clob_token_ids = json.loads(benfica_market.get('clobTokenIds', '[]'))
    
    print("=== TOKEN MAPPING ===")
    print(f"Yes Token ID: {clob_token_ids[0]}")
    print(f"No Token ID:  {clob_token_ids[1]}")
    
    # Use CLOB API to get trades by maker/taker for more details
    # The Data API might be aggregating or showing only one side
    
    # Let's check the CLOB trades endpoint
    clob_trades_url = f"https://clob.polymarket.com/trades?market={condition_id}"
    headers = {"Accept": "application/json"}
    
    try:
        clob_resp = requests.get(clob_trades_url, headers=headers, timeout=10)
        print(f"\nCLOB API status: {clob_resp.status_code}")
        if clob_resp.status_code == 200:
            clob_trades = clob_resp.json()
            print(f"CLOB trades returned: {len(clob_trades) if isinstance(clob_trades, list) else 'N/A'}")
            if isinstance(clob_trades, list) and len(clob_trades) > 0:
                print(f"Sample trade structure: {json.dumps(clob_trades[0], indent=2)[:500]}")
    except Exception as e:
        print(f"CLOB API error: {e}")
    
    # The key insight: Let's analyze what the screenshot is showing vs API
    print("\n" + "=" * 60)
    print("ANALYSIS OF THE DISCREPANCY")
    print("=" * 60)
    print("""
From the data you provided:

API Record (4778 shares):
  - side: BUY
  - outcome: No
  - price: 0.44
  - volume: $2,102.32 (4778 * 0.44)

Screenshot (4778 shares):
  - Shows: "Buy Yes 56c"
  - Amount: $2,675.68 (4778 * 0.56)

These are DIFFERENT amounts, which means:
1. Either the screenshot is showing a DIFFERENT trade (same size, different direction)
2. Or the screenshot is calculating the "position value" differently

Key Question: Does the screenshot show the COST of purchasing, 
or the POTENTIAL PAYOUT?

If you BUY 4778 "No" shares at 0.44:
  - You PAY: 4778 * 0.44 = $2,102.32
  - If No wins, you GET: 4778 * 1.00 = $4,778.00

Alternatively, if you BUY 4778 "Yes" shares at 0.56:
  - You PAY: 4778 * 0.56 = $2,675.68
  - If Yes wins, you GET: 4778 * 1.00 = $4,778.00

The screenshot amount ($2,675.68) matches "Buy Yes @ 0.56".
The API amount ($2,102.32) matches "Buy No @ 0.44".

CONCLUSION: These appear to be TWO DIFFERENT TRADES with the same size!
The smart trader you're tracking likely made BOTH trades:
  - BUY No @ 0.44 (betting against Benfica)
  - BUY Yes @ 0.56 (betting for Benfica)

This is called HEDGING or could indicate market making activity.
""")

if __name__ == "__main__":
    main()
