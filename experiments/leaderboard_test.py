import requests
import time
import concurrent.futures
from datetime import datetime

BASE_URL = "https://data-api.polymarket.com/v1/leaderboard"

def get_leaderboard(offset=0, limit=50, time_period="DAY", order_by="PNL"):
    params = {
        "limit": limit,
        "offset": offset,
        "timePeriod": time_period,
        "orderBy": order_by
    }
    try:
        start = time.time()
        response = requests.get(BASE_URL, params=params, timeout=10)
        duration = time.time() - start
        
        if response.status_code == 200:
            return response.json(), duration, None
        else:
            return None, duration, f"Status {response.status_code}: {response.text}"
    except Exception as e:
        return None, 0, str(e)

def test_data_volume_and_speed():
    print("\n--- Test 1: Data Volume & Fetch Speed ---")
    
    # 1. Check strict limit of 1000
    print("Checking API limits...")
    _, _, err_1000 = get_leaderboard(offset=1000, limit=50) # Should verify if 1000 is start or end. Usually start=1000 implies items 1001-1050.
    
    # Docs say: offset Required range: 0 <= x <= 1000
    # Let's try to fetch the maximum allowed chunk.
    
    print(f"Fetching from offset 1000: {'Error: ' + str(err_1000) if err_1000 else 'Success'}")
    
    # 2. Fetch ALL available data (Top 1000) using threads
    print("Benchmarking download of Top 1000 traders (20 pages x 50 items)...")
    
    offsets = range(0, 1001, 50) # 0, 50, ... 1000 (21 requests)
    
    start_total = time.time()
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_offset = {executor.submit(get_leaderboard, offset=o): o for o in offsets}
        for future in concurrent.futures.as_completed(future_to_offset):
            o = future_to_offset[future]
            try:
                data, dur, err = future.result()
                if data and isinstance(data, list):
                    results.extend(data)
                elif err:
                    print(f"Request offset {o} failed: {err}")
            except Exception as exc:
                print(f"Offset {o} generated an exception: {exc}")
                
    total_time = time.time() - start_total
    
    print(f"Fetched {len(results)} records in {total_time:.2f} seconds.")
    print(f"Average records per second: {len(results)/total_time:.2f}")

def test_realtime_freshness():
    print("\n--- Test 2: Real-time Freshness (30s duration) ---")
    # Poll Top 10 users every 2 seconds to check for updates
    
    initial_data, _, _ = get_leaderboard(limit=10, time_period="DAY", order_by="VOL") # Volume changes most often?
    if not initial_data:
        print("Failed to get initial data for baseline.")
        return

    # Create a map of wallet -> data for comparison
    tracking = {item['proxyWallet']: item for item in initial_data}
    
    print("Monitoring Top 10 (by Volume) for 30 seconds...")
    changes_detected = 0
    start_monitor = time.time()
    
    for i in range(15): # 15 iterations x 2 seconds = 30s approx
        time.sleep(2)
        current_data, latency, err = get_leaderboard(limit=10, time_period="DAY", order_by="VOL")
        
        if not current_data:
            print(f"Iteration {i+1} failed: {err}")
            continue
            
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Check for diffs
        iteration_changes = 0
        for item in current_data:
            wallet = item.get('proxyWallet')
            if wallet in tracking:
                old_item = tracking[wallet]
                
                # Compare Vol and PnL
                if item['vol'] != old_item['vol'] or item['pnl'] != old_item['pnl']:
                    print(f"[{timestamp}] Change detected for {wallet[:6]}... | Vol: {old_item['vol']} -> {item['vol']} | PnL: {old_item['pnl']} -> {item['pnl']}")
                    tracking[wallet] = item # Update baseline
                    iteration_changes += 1
        
        if iteration_changes > 0:
            changes_detected += 1
        else:
            # excessive logging avoidance
            # print(f"[{timestamp}] No changes.")
            pass

    print(f"Finished monitoring. Detected updates in {changes_detected} / 15 polling cycles.")

if __name__ == "__main__":
    test_data_volume_and_speed()
    test_realtime_freshness()
