import requests
import json
import time

def fetch_event_data(slug):
    url = f"https://gamma-api.polymarket.com/events/slug/{slug}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching event: {e}")
        return None

def fetch_trades(condition_id, limit=1000):
    all_trades = []
    offset = 0
    base_url = "https://data-api.polymarket.com/trades"
    
    while True:
        try:
            params = {
                "market": condition_id,
                "limit": limit,
                "offset": offset
            }
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                break
                
            all_trades.extend(data)
            
            if len(data) < limit:
                break
                
            offset += limit
            # Safety break to avoid infinite loops if API behaves unexpectedly
            if offset > 10000: 
                print(f"Warning: Reached max offset 10000 for condition {condition_id}. Some data might be missing.")
                break
                
            time.sleep(0.1) # Rate limit protection
            
        except Exception as e:
            print(f"Error fetching trades: {e}")
            break
            
    return all_trades

def main():
    slug = "ucl-ben1-rma1-2026-01-28"
    print(f"Fetching event data for slug: {slug}...")
    event_data = fetch_event_data(slug)
    
    if not event_data:
        return

    markets = event_data.get("markets", [])
    if not markets:
        print("No markets found for this event.")
        return

    print(f"Found {len(markets)} markets.")
    
    filtered_trades = []

    for market in markets:
        condition_id = market.get("conditionId")
        question = market.get("question")
        print(f"Processing market: {question} ({condition_id})")
        
        trades = fetch_trades(condition_id)
        print(f"  Fetched {len(trades)} trades.")
        
        for trade in trades:
            # Safely get values, defaulting to 0/None
            try:
                price = float(trade.get("price", 0))
                size = float(trade.get("size", 0))
                side = trade.get("side")
                outcome = trade.get("outcome")
                
                # Filter Logic:
                # 1. Transaction Amount > $1000  (Size * Price > 1000)
                # 2. Buy Price < 0.8 (Price < 0.8)
                # 3. Assuming user wants 'Buy' side trades or just matches where price < 0.8?
                # User said: "成交金额大于1000$ 买入价 小于 0.8" 
                # (Transaction Amount > 1000 AND Buy Price < 0.8)
                
                transaction_amount = size * price
                
                if transaction_amount > 1000 and price < 0.8:
                     # Add readable details
                    trade_info = {
                        "market_question": question,
                        "outcome": outcome,
                        "side": side,
                        "price": price,
                        "size": size,
                        "volume_usd": transaction_amount,
                        "timestamp": trade.get("timestamp"),
                        "date": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(trade.get("timestamp"))),
                        "transaction_hash": trade.get("transactionHash"),
                        "maker_address": trade.get("maker_address", "N/A"), # Note: Data API might not return maker info in all endpoints 
                        "conditionId": condition_id
                    }
                    filtered_trades.append(trade_info)
                    
            except ValueError:
                continue

    # Sort results by timestamp desc
    filtered_trades.sort(key=lambda x: x["timestamp"], reverse=True)

    print(f"\nFound {len(filtered_trades)} matching trades.")
    
    # Save to JSON file for inspection
    with open("filtered_trades.json", "w", encoding='utf-8') as f:
        json.dump(filtered_trades, f, indent=4, ensure_ascii=False)
    
    # Print first few results
    for t in filtered_trades[:10]:
        print(f"[{t['date']}] {t['market_question']} | {t['side']} {t['outcome']} | Price: {t['price']:.3f} | Amt: ${t['volume_usd']:.2f}")

if __name__ == "__main__":
    main()
