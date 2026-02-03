"""
Market Data Extractor

Responsibilities:
1. Extract trades from large 35GB trades.csv file
2. Cache extracted data to individual market files
3. Provide fast loading from cache for subsequent runs

Usage:
    extractor = MarketDataExtractor()
    trades_df = extractor.get_market_trades(market_id=253591)
"""
import os
import sys
import time
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Paths
ARCHIVE_DIR = Path(__file__).parent / "archive"
TRADES_FILE = ARCHIVE_DIR / "processed" / "trades.csv"
MARKETS_FILE = ARCHIVE_DIR / "markets.csv"
CACHE_DIR = ARCHIVE_DIR / "market_trades"  # Cache directory


class MarketDataExtractor:
    """
    Extract and cache market trades from large CSV file.
    """
    
    def __init__(self, chunk_size: int = 2000000):
        self.chunk_size = chunk_size
        self.cache_dir = CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load markets metadata
        self.markets_df = pd.read_csv(MARKETS_FILE)
    
    def get_cache_path(self, market_id: int) -> Path:
        """Get cache file path for a market."""
        return self.cache_dir / f"market_{market_id}.csv"
    
    def is_cached(self, market_id: int) -> bool:
        """Check if market data is already cached."""
        return self.get_cache_path(market_id).exists()
    
    def load_from_cache(self, market_id: int) -> Optional[pd.DataFrame]:
        """Load market trades from cache."""
        cache_path = self.get_cache_path(market_id)
        if cache_path.exists():
            return pd.read_csv(cache_path)
        return None
    
    def save_to_cache(self, market_id: int, trades_df: pd.DataFrame):
        """Save market trades to cache."""
        cache_path = self.get_cache_path(market_id)
        trades_df.to_csv(cache_path, index=False)
        print(f"  [CACHE] Saved {len(trades_df)} trades to {cache_path.name}")
    
    def extract_single_market(self, market_id: int, use_cache: bool = True) -> pd.DataFrame:
        """
        Extract trades for a single market.
        Uses cache if available, otherwise extracts from large file.
        """
        # Check cache first
        if use_cache and self.is_cached(market_id):
            print(f"  [CACHE] Loading market {market_id} from cache...")
            return self.load_from_cache(market_id)
        
        # Extract from large file
        print(f"  [EXTRACT] Extracting market {market_id} from trades.csv...")
        start_time = time.time()
        
        trades = []
        consecutive_empty = 0
        
        for chunk in pd.read_csv(TRADES_FILE, chunksize=self.chunk_size, low_memory=False):
            chunk['market_id'] = pd.to_numeric(chunk['market_id'], errors='coerce')
            matched = chunk[chunk['market_id'] == market_id]
            
            if len(matched) > 0:
                trades.extend(matched.to_dict('records'))
                consecutive_empty = 0
            else:
                consecutive_empty += 1
            
            # Early stop: 3 consecutive empty chunks
            if consecutive_empty >= 3 and len(trades) > 0:
                break
        
        trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()
        elapsed = time.time() - start_time
        print(f"  [EXTRACT] Found {len(trades_df)} trades in {elapsed:.1f}s")
        
        # Save to cache
        if len(trades_df) > 0:
            self.save_to_cache(market_id, trades_df)
        
        return trades_df
    
    def extract_multiple_markets(
        self, 
        market_ids: List[int], 
        use_cache: bool = True,
        min_trades: int = 100
    ) -> Dict[int, pd.DataFrame]:
        """
        Extract trades for multiple markets in a single pass.
        Much more efficient than extracting one by one.
        
        Returns: {market_id: trades_df}
        """
        # Separate cached vs uncached
        cached_ids = [mid for mid in market_ids if use_cache and self.is_cached(mid)]
        uncached_ids = [mid for mid in market_ids if mid not in cached_ids]
        
        result = {}
        
        # Load from cache
        for mid in cached_ids:
            df = self.load_from_cache(mid)
            if df is not None and len(df) >= min_trades:
                result[mid] = df
        
        if cached_ids:
            print(f"[CACHE] Loaded {len(result)} markets from cache")
        
        # Extract uncached markets in single pass
        if uncached_ids:
            print(f"[EXTRACT] Extracting {len(uncached_ids)} markets from trades.csv...")
            start_time = time.time()
            
            trades_by_market: Dict[int, list] = {mid: [] for mid in uncached_ids}
            consecutive_empty = 0
            chunks_processed = 0
            
            for chunk in pd.read_csv(TRADES_FILE, chunksize=self.chunk_size, low_memory=False):
                chunks_processed += 1
                
                chunk['market_id'] = pd.to_numeric(chunk['market_id'], errors='coerce')
                matched = chunk[chunk['market_id'].isin(uncached_ids)]
                
                if len(matched) > 0:
                    for mid, group in matched.groupby('market_id'):
                        trades_by_market[int(mid)].extend(group.to_dict('records'))
                    consecutive_empty = 0
                else:
                    consecutive_empty += 1
                
                # Progress every 5 chunks
                if chunks_processed % 5 == 0:
                    valid = sum(1 for mid in trades_by_market if len(trades_by_market[mid]) >= min_trades)
                    print(f"  Chunks: {chunks_processed}, Markets with trades: {valid}")
                
                # Early stop if all markets have enough data
                all_have_data = all(
                    len(trades_by_market[mid]) >= min_trades 
                    for mid in uncached_ids
                )
                if all_have_data or consecutive_empty >= 5:
                    break
            
            elapsed = time.time() - start_time
            print(f"[EXTRACT] Completed in {elapsed:.1f}s")
            
            # Save to cache and add to result
            for mid, trades in trades_by_market.items():
                if len(trades) >= min_trades:
                    df = pd.DataFrame(trades)
                    self.save_to_cache(mid, df)
                    result[mid] = df
        
        return result
    
    def get_market_info(self, market_id: int) -> Optional[pd.Series]:
        """Get market metadata."""
        row = self.markets_df[self.markets_df['id'] == market_id]
        if len(row) > 0:
            return row.iloc[0]
        return None
    
    def get_closed_time(self, market_id: int) -> Optional[datetime]:
        """Get market close time (timezone-naive)."""
        info = self.get_market_info(market_id)
        if info is not None and pd.notna(info.get('closedTime')):
            closed_time = pd.to_datetime(info['closedTime'])
            if closed_time.tzinfo is not None:
                closed_time = closed_time.tz_localize(None)
            return closed_time
        return None


# =============================================================================
# CLI for standalone extraction
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract market trades from archive")
    parser.add_argument("--market", type=int, help="Single market ID to extract")
    parser.add_argument("--markets", type=str, help="Comma-separated market IDs")
    parser.add_argument("--no-cache", action="store_true", help="Skip cache, force re-extract")
    args = parser.parse_args()
    
    extractor = MarketDataExtractor()
    
    if args.market:
        df = extractor.extract_single_market(args.market, use_cache=not args.no_cache)
        print(f"\nResult: {len(df)} trades for market {args.market}")
    
    elif args.markets:
        ids = [int(x.strip()) for x in args.markets.split(",")]
        results = extractor.extract_multiple_markets(ids, use_cache=not args.no_cache)
        print(f"\nResults: {len(results)} markets extracted")
        for mid, df in results.items():
            print(f"  Market {mid}: {len(df)} trades")
    
    else:
        print("Usage:")
        print("  python data_extractor.py --market 253591")
        print("  python data_extractor.py --markets 253591,504603,503303")
