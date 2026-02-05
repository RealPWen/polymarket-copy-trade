"""
Batch Cache Builder

Build cache for more markets by scanning the trades.csv file once.
This script will:
1. Load all closed markets with sufficient volume
2. Check which ones are already cached
3. Extract uncached markets in a single pass

Usage:
    python batch_cache_builder.py --target 3000 --volume 50000
"""
import os
import sys
import time
import pandas as pd
import random
from pathlib import Path
from typing import Set, Dict

sys.stdout.reconfigure(encoding='utf-8')

# Paths
ARCHIVE_DIR = Path(__file__).parent.parent / "archive"
TRADES_FILE = ARCHIVE_DIR / "processed" / "trades.csv"
MARKETS_FILE = ARCHIVE_DIR / "markets.csv"
CACHE_DIR = ARCHIVE_DIR / "market_trades"
CACHE_DIR.mkdir(exist_ok=True)


def get_cached_market_ids() -> Set[int]:
    """Get set of already cached market IDs."""
    cached = set()
    for f in CACHE_DIR.glob("market_*.csv"):
        try:
            mid = int(f.stem.replace("market_", ""))
            cached.add(mid)
        except:
            pass
    return cached


def get_high_volume_closed_markets(min_volume: float) -> pd.DataFrame:
    """Get list of closed markets with sufficient volume."""
    print(f"[INFO] Loading markets metadata...")
    df = pd.read_csv(MARKETS_FILE)
    
    # Filter closed markets
    df = df[df['closedTime'].notna()]
    
    # Filter by volume
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
    df = df[df['volume'] >= min_volume]
    
    print(f"[INFO] Found {len(df)} closed markets with volume >= ${min_volume:,.0f}")
    return df


def build_cache(
    target_new: int,
    min_volume: float,
    min_trades: int = 100,
    chunk_size: int = 2000000,
    seed: int = 42
):
    """
    Build cache for more markets.
    
    Args:
        target_new: Target number of NEW markets to cache
        min_volume: Minimum market volume to consider
        min_trades: Minimum trades required for a market to be valid
        chunk_size: Chunk size for reading trades.csv
        seed: Random seed for market selection
    """
    print("=" * 80)
    print("BATCH CACHE BUILDER")
    print("=" * 80)
    
    # Get existing cache
    cached_ids = get_cached_market_ids()
    print(f"[INFO] Already cached: {len(cached_ids)} markets")
    
    # Get target markets
    markets_df = get_high_volume_closed_markets(min_volume)
    
    # Filter out already cached
    uncached_markets = markets_df[~markets_df['id'].isin(cached_ids)]
    print(f"[INFO] Uncached high-volume markets: {len(uncached_markets)}")
    
    if len(uncached_markets) == 0:
        print("[DONE] All high-volume markets are already cached!")
        return
    
    # Sample target markets
    random.seed(seed)
    if len(uncached_markets) > target_new:
        sample = uncached_markets.sample(n=target_new, random_state=seed)
    else:
        sample = uncached_markets
    
    target_ids = set(sample['id'].tolist())
    print(f"[INFO] Targeting {len(target_ids)} new markets to cache")
    
    # Track trades per market
    trades_by_market: Dict[int, list] = {mid: [] for mid in target_ids}
    markets_completed = set()
    
    # Scan trades.csv
    print(f"\n[STEP 1] Scanning trades.csv (this may take a while)...")
    start_time = time.time()
    chunks_processed = 0
    total_trades_found = 0
    
    try:
        for chunk in pd.read_csv(TRADES_FILE, chunksize=chunk_size, low_memory=False):
            chunks_processed += 1
            
            # Filter to target markets
            chunk['market_id'] = pd.to_numeric(chunk['market_id'], errors='coerce')
            matched = chunk[chunk['market_id'].isin(target_ids)]
            
            if len(matched) > 0:
                total_trades_found += len(matched)
                
                for mid, group in matched.groupby('market_id'):
                    mid_int = int(mid)
                    if mid_int not in markets_completed:
                        trades_by_market[mid_int].extend(group.to_dict('records'))
                        
                        # Check if this market has enough trades
                        if len(trades_by_market[mid_int]) >= min_trades:
                            markets_completed.add(mid_int)
            
            # Progress
            if chunks_processed % 3 == 0:
                elapsed = time.time() - start_time
                print(f"  Chunks: {chunks_processed} | "
                      f"Trades found: {total_trades_found:,} | "
                      f"Markets with data: {len(markets_completed)} | "
                      f"Time: {elapsed:.1f}s")
            
            # Stop if all targets have data
            if len(markets_completed) >= len(target_ids):
                print(f"[INFO] All target markets have sufficient trades!")
                break
    
    except KeyboardInterrupt:
        print("\n[WARN] Interrupted by user, saving collected data...")
    
    elapsed = time.time() - start_time
    print(f"\n[STEP 2] Saving to cache...")
    
    saved_count = 0
    for mid, trades in trades_by_market.items():
        if len(trades) >= min_trades:
            df = pd.DataFrame(trades)
            cache_path = CACHE_DIR / f"market_{mid}.csv"
            df.to_csv(cache_path, index=False)
            saved_count += 1
    
    print(f"\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  Time elapsed: {elapsed:.1f}s")
    print(f"  Chunks processed: {chunks_processed}")
    print(f"  Total trades found: {total_trades_found:,}")
    print(f"  Markets saved to cache: {saved_count}")
    print(f"  New total cached: {len(cached_ids) + saved_count}")
    print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Build market trade cache")
    parser.add_argument("--target", type=int, default=500, help="Target number of new markets to cache")
    parser.add_argument("--volume", type=float, default=50000, help="Min volume filter")
    parser.add_argument("--trades", type=int, default=100, help="Min trades per market")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    build_cache(
        target_new=args.target,
        min_volume=args.volume,
        min_trades=args.trades,
        seed=args.seed
    )
