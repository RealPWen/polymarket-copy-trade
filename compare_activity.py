"""
Simple comparison script with focused output.
"""
import requests
import json
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

def fetch_wallet_activity(wallet_address, condition_ids, limit=500):
    all_activity = []
    
    for cid in condition_ids:
        offset = 0
        while True:
            url = "https://data-api.polymarket.com/activity"
            params = {
                "user": wallet_address,
                "market": cid,
                "limit": limit,
                "offset": offset
            }
            
            try:
                resp = requests.get(url, params=params, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                
                if not data:
                    break
                    
                all_activity.extend(data)
                
                if len(data) < limit:
                    break
                    
                offset += limit
                time.sleep(0.1)
                
            except Exception as e:
                break
    
    return all_activity

def main():
    wallet = "0xd82079c0d6b837bad90abf202befc079da5819f6"
    
    condition_ids = [
        "0xe986a6eb382842e20ef258af982525779d01a1d1a7d58700c42364da8c43e838",
        "0xea49f0969abc80cf7ddbc9d3435c81d3a63cc6b73ebf8d6420f59b0557cf188e",
        "0x3d7f69428530284e2f164e26dd230a8bfdb729d506442879b65d6b80863e814e"
    ]
    
    activity = fetch_wallet_activity(wallet, condition_ids)
    
    with open("filtered_trades.json", "r", encoding="utf-8") as f:
        filtered_trades = json.load(f)
    
    filtered_by_hash = {t.get("transaction_hash"): t for t in filtered_trades if t.get("transaction_hash")}
    
    # Focus on discrepancies
    discrepancies = []
    
    for act in activity:
        tx_hash = act.get("transactionHash")
        if tx_hash in filtered_by_hash:
            filtered_record = filtered_by_hash[tx_hash]
            
            api_outcome = act.get("outcome")
            filtered_outcome = filtered_record.get("outcome")
            api_side = act.get("side")
            filtered_side = filtered_record.get("side")
            
            if api_outcome != filtered_outcome or api_side != filtered_side:
                discrepancies.append({
                    "tx_hash": tx_hash,
                    "timestamp": act.get("timestamp"),
                    "activity_api": {
                        "side": api_side,
                        "outcome": api_outcome,
                        "price": act.get("price"),
                        "size": act.get("size"),
                        "usdcSize": act.get("usdcSize")
                    },
                    "filtered_trades": {
                        "side": filtered_side,
                        "outcome": filtered_outcome,
                        "price": filtered_record.get("price"),
                        "size": filtered_record.get("size"),
                        "volume_usd": filtered_record.get("volume_usd")
                    }
                })
    
    result = {
        "wallet": wallet,
        "total_wallet_activity": len(activity),
        "total_discrepancies": len(discrepancies),
        "discrepancies": discrepancies[:20]  # First 20 only
    }
    
    with open("discrepancies.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"Total wallet activity: {len(activity)}")
    print(f"Total discrepancies: {len(discrepancies)}")
    print("Saved to discrepancies.json")

if __name__ == "__main__":
    main()
