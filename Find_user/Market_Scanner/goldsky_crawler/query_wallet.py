"""
Query recent trades for a specific wallet using Goldsky API.

Usage:
    python query_wallet.py <wallet_address>
    python query_wallet.py 0x6022a1784a55b8070de42d19484bbff95fa7c60a
"""
import sys
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

GOLDSKY_URL = "https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/orderbook-subgraph/0.0.1/gn"


def query_wallet(wallet: str, limit: int = 5) -> dict:
    """Query recent trades for a wallet."""
    wallet = wallet.lower()
    
    transport = RequestsHTTPTransport(url=GOLDSKY_URL, verify=True, retries=3)
    client = Client(transport=transport)
    
    # Query as taker
    query = f'''query {{
        orderFilledEvents(orderBy: timestamp, orderDirection: desc, first: {limit}, where: {{taker: "{wallet}"}}) {{
            timestamp makerAmountFilled takerAmountFilled makerAssetId takerAssetId transactionHash
        }}
    }}'''
    
    result = client.execute(gql(query))
    taker_events = result.get('orderFilledEvents', [])
    
    # Query as maker  
    query2 = f'''query {{
        orderFilledEvents(orderBy: timestamp, orderDirection: desc, first: {limit}, where: {{maker: "{wallet}"}}) {{
            timestamp makerAmountFilled takerAmountFilled makerAssetId takerAssetId transactionHash
        }}
    }}'''
    
    result2 = client.execute(gql(query2))
    maker_events = result2.get('orderFilledEvents', [])
    
    output = {
        "wallet": wallet,
        "query_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "taker_trades": len(taker_events),
        "maker_trades": len(maker_events),
        "recent_as_taker": [],
        "recent_as_maker": []
    }
    
    for e in taker_events[:limit]:
        ts = int(e['timestamp'])
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        if e['takerAssetId'] == '0':
            direction = 'BUY'
            usd = int(e['takerAmountFilled']) / 1e6
        else:
            direction = 'SELL'
            usd = int(e['makerAmountFilled']) / 1e6
        
        output["recent_as_taker"].append({
            "time": dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "direction": direction,
            "usd": round(usd, 2),
            "tx": e['transactionHash'][:20] + "..."
        })
    
    for e in maker_events[:limit]:
        ts = int(e['timestamp'])
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        if e['makerAssetId'] == '0':
            direction = 'SELL'
            usd = int(e['makerAmountFilled']) / 1e6
        else:
            direction = 'BUY'
            usd = int(e['takerAmountFilled']) / 1e6
        
        output["recent_as_maker"].append({
            "time": dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "direction": direction,
            "usd": round(usd, 2),
            "tx": e['transactionHash'][:20] + "..."
        })
    
    return output


def main():
    parser = argparse.ArgumentParser(description="Query recent trades for a wallet")
    parser.add_argument("wallet", help="Wallet address to query")
    parser.add_argument("-n", "--limit", type=int, default=5, help="Number of trades to fetch")
    parser.add_argument("-o", "--output", help="Output JSON file")
    
    args = parser.parse_args()
    
    result = query_wallet(args.wallet, args.limit)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()

