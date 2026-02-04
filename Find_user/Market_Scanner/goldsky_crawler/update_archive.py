"""
Archive Data Updater - Standalone Version

A self-contained script to update Polymarket trade data:
1. Pulls order events from Goldsky API
2. Updates markets metadata from Polymarket API
3. Processes orders into structured trades
4. Splits trades into per-market files for fast analysis

This script is fully independent and does not require poly_data project.

Usage:
    python update_archive.py              # Full update
    python update_archive.py --status     # Show current data status
    python update_archive.py --split-only # Only split existing trades.csv
    python update_archive.py --markets    # Only update markets metadata
    python update_archive.py --process    # Only process goldsky to trades

Requirements:
    pip install polars requests gql flatten-json

Author: Archive Updater
Date: 2026-02-04
"""
import os
import sys
import time
import json
import csv
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, List

sys.stdout.reconfigure(encoding='utf-8')

# ============================================================================
# Configuration
# ============================================================================

# Script directory
SCRIPT_DIR = Path(__file__).parent.resolve()

# Archive directory (sibling folder containing data)
ARCHIVE_DIR = SCRIPT_DIR.parent / "archive"

# Data directories
GOLDSKY_DIR = ARCHIVE_DIR / "goldsky"
PROCESSED_DIR = ARCHIVE_DIR / "processed"
MARKET_TRADES_DIR = ARCHIVE_DIR / "market_trades"

# Data files
GOLDSKY_FILE = GOLDSKY_DIR / "orderFilled.csv"
TRADES_FILE = PROCESSED_DIR / "trades.csv"
MARKETS_FILE = ARCHIVE_DIR / "markets.csv"
MISSING_MARKETS_FILE = ARCHIVE_DIR / "missing_markets.csv"

# State files (keep in script directory for git tracking)
STATE_FILE = SCRIPT_DIR / "update_state.json"
GOLDSKY_CURSOR_FILE = SCRIPT_DIR / "cursor_state.json"

# Goldsky API
GOLDSKY_URL = "https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/orderbook-subgraph/0.0.1/gn"

# Polymarket API
POLYMARKET_API = "https://gamma-api.polymarket.com/markets"


def log(msg: str, level: str = "INFO"):
    """Print log message with timestamp."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")


def ensure_dirs():
    """Ensure all required directories exist."""
    GOLDSKY_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    MARKET_TRADES_DIR.mkdir(parents=True, exist_ok=True)


def get_file_stats(filepath: Path) -> Dict:
    """Get file statistics."""
    if not filepath.exists():
        return {"exists": False, "size_mb": 0, "lines": 0}
    
    size_bytes = filepath.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    
    # Estimate lines for large files
    if size_mb > 100:
        lines = int(size_bytes / 150)
    else:
        try:
            with open(filepath, 'rb') as f:
                lines = sum(1 for _ in f)
        except Exception:
            lines = int(size_bytes / 150)
    
    return {"exists": True, "size_mb": size_mb, "lines": lines}


def get_last_line(filepath: Path) -> Optional[str]:
    """Get last line of file efficiently."""
    if not filepath.exists():
        return None
    
    try:
        with open(filepath, 'rb') as f:
            f.seek(0, 2)
            file_size = f.tell()
            if file_size == 0:
                return None
            
            read_size = min(4096, file_size)
            f.seek(-read_size, 2)
            last_bytes = f.read()
            
            lines = last_bytes.decode('utf-8', errors='ignore').split('\n')
            for line in reversed(lines):
                if line.strip():
                    return line.strip()
            return None
    except Exception as e:
        log(f"Error reading last line: {e}", "WARNING")
        return None


def load_state() -> Dict:
    """Load update state."""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_state(state: Dict):
    """Save update state."""
    with open(STATE_FILE, "w", encoding='utf-8') as f:
        json.dump(state, f, indent=2, default=str)


# ============================================================================
# Goldsky Update (Order Events)
# ============================================================================

def load_goldsky_cursor() -> tuple:
    """Load goldsky cursor for resume."""
    if GOLDSKY_CURSOR_FILE.exists():
        try:
            with open(GOLDSKY_CURSOR_FILE, 'r') as f:
                state = json.load(f)
            return (
                state.get('last_timestamp', 0),
                state.get('last_id'),
                state.get('sticky_timestamp')
            )
        except Exception as e:
            log(f"Error reading cursor: {e}", "WARNING")
    
    # Fallback: read from CSV
    if GOLDSKY_FILE.exists():
        last_line = get_last_line(GOLDSKY_FILE)
        if last_line:
            try:
                parts = last_line.split(',')
                last_ts = int(parts[0])
                log(f"Resuming from CSV timestamp: {last_ts}")
                return (last_ts - 1, None, None)
            except Exception:
                pass
    
    return (0, None, None)


def save_goldsky_cursor(timestamp: int, last_id: Optional[str], sticky_timestamp: Optional[int],
                        total_records: int = 0, start_time: float = 0, target_ts: int = 0):
    """Save goldsky cursor with progress info."""
    state = {
        'last_timestamp': timestamp,
        'last_id': last_id,
        'sticky_timestamp': sticky_timestamp,
        'total_records': total_records,
        'start_time': start_time,
        'target_timestamp': target_ts,
        'saved_at': datetime.now().isoformat()
    }
    with open(GOLDSKY_CURSOR_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def update_goldsky(batch_size: int = 1000) -> bool:
    """
    Fetch order events from Goldsky API with resume support.
    
    Features:
    - Automatic resume from last position
    - Progress tracking with ETA
    - Rate limiting protection
    - Error recovery with exponential backoff
    """
    try:
        from gql import gql, Client
        from gql.transport.requests import RequestsHTTPTransport
        from flatten_json import flatten
        import pandas as pd
    except ImportError as e:
        log(f"Missing dependency: {e}. Run: pip install gql flatten-json pandas", "ERROR")
        return False
    
    log("Updating Goldsky order events...")
    ensure_dirs()
    
    # Load cursor and progress
    last_timestamp, last_id, sticky_timestamp = load_goldsky_cursor()
    
    # Get target timestamp (current time)
    target_ts = int(datetime.now(timezone.utc).timestamp())
    
    if last_timestamp > 0:
        start_date = datetime.fromtimestamp(last_timestamp, tz=timezone.utc)
        target_date = datetime.fromtimestamp(target_ts, tz=timezone.utc)
        gap_days = (target_date - start_date).days
        log(f"  Resuming from: {start_date.strftime('%Y-%m-%d %H:%M')} UTC")
        log(f"  Target: {target_date.strftime('%Y-%m-%d %H:%M')} UTC ({gap_days} days gap)")
    else:
        log("  Starting from beginning (this will take a long time)")
    
    columns = ['timestamp', 'maker', 'makerAssetId', 'makerAmountFilled', 
               'taker', 'takerAssetId', 'takerAmountFilled', 'transactionHash']
    
    total_records = 0
    batch_count = 0
    start_time = time.time()
    initial_timestamp = last_timestamp
    consecutive_errors = 0
    max_consecutive_errors = 10
    
    while True:
        # Build query
        if sticky_timestamp is not None:
            where_clause = f'timestamp: "{sticky_timestamp}", id_gt: "{last_id}"'
        else:
            where_clause = f'timestamp_gt: "{last_timestamp}"'
        
        query_str = f'''query {{
            orderFilledEvents(orderBy: timestamp, orderDirection: asc,
                             first: {batch_size}, where: {{{where_clause}}}) {{
                fee id maker makerAmountFilled makerAssetId orderHash
                taker takerAmountFilled takerAssetId timestamp transactionHash
            }}
        }}'''
        
        try:
            transport = RequestsHTTPTransport(url=GOLDSKY_URL, verify=True, retries=3)
            client = Client(transport=transport)
            result = client.execute(gql(query_str))
            consecutive_errors = 0  # Reset on success
        except Exception as e:
            consecutive_errors += 1
            wait_time = min(5 * (2 ** consecutive_errors), 300)  # Exponential backoff, max 5 min
            
            if consecutive_errors >= max_consecutive_errors:
                log(f"  Too many consecutive errors ({consecutive_errors}). Saving progress and exiting.", "ERROR")
                save_goldsky_cursor(last_timestamp, last_id, sticky_timestamp, 
                                   total_records, start_time, target_ts)
                return False
            
            log(f"  Query error: {e}. Retry {consecutive_errors}/{max_consecutive_errors} in {wait_time}s...", "WARNING")
            time.sleep(wait_time)
            continue
        
        events = result.get('orderFilledEvents', [])
        
        if not events:
            if sticky_timestamp is not None:
                last_timestamp = sticky_timestamp
                sticky_timestamp = None
                last_id = None
                continue
            log(f"  No more events. Total fetched: {total_records:,}")
            break
        
        # Convert to DataFrame
        df = pd.DataFrame([flatten(e) for e in events])
        df = df.sort_values(['timestamp', 'id']).reset_index(drop=True)
        
        batch_last_ts = int(df.iloc[-1]['timestamp'])
        batch_last_id = df.iloc[-1]['id']
        
        # Determine cursor mode
        if len(df) >= batch_size:
            sticky_timestamp = batch_last_ts
            last_id = batch_last_id
        else:
            if sticky_timestamp is not None:
                last_timestamp = sticky_timestamp
                sticky_timestamp = None
                last_id = None
            else:
                last_timestamp = batch_last_ts
        
        batch_count += 1
        total_records += len(df)
        
        # Calculate progress and ETA
        elapsed = time.time() - start_time
        if initial_timestamp > 0 and batch_last_ts > initial_timestamp:
            progress_ts = batch_last_ts - initial_timestamp
            total_ts = target_ts - initial_timestamp
            progress_pct = (progress_ts / total_ts) * 100 if total_ts > 0 else 0
            
            if progress_pct > 0:
                eta_seconds = (elapsed / progress_pct) * (100 - progress_pct)
                eta_hours = eta_seconds / 3600
            else:
                eta_hours = 0
        else:
            progress_pct = 0
            eta_hours = 0
        
        # Log progress every 50 batches
        if batch_count % 50 == 0:
            batch_date = datetime.fromtimestamp(batch_last_ts, tz=timezone.utc)
            log(f"  [{progress_pct:5.1f}%] {batch_date.strftime('%Y-%m-%d %H:%M')} | "
                f"Records: {total_records:,} | ETA: {eta_hours:.1f}h")
        
        # Save to file
        df = df.drop_duplicates(subset=['id'])
        df_save = df[columns].copy()
        
        if GOLDSKY_FILE.exists():
            df_save.to_csv(GOLDSKY_FILE, index=None, mode='a', header=None)
        else:
            df_save.to_csv(GOLDSKY_FILE, index=None)
        
        # Save cursor every batch for resume capability
        save_goldsky_cursor(last_timestamp, last_id, sticky_timestamp,
                           total_records, start_time, target_ts)
        
        # Check if we've caught up to current time (within 5 minutes)
        current_ts = int(datetime.now(timezone.utc).timestamp())
        time_gap = current_ts - batch_last_ts
        
        if len(df) < batch_size and sticky_timestamp is None and time_gap < 300:
            log(f"  Caught up to current time (gap: {time_gap}s)")
            break
        
        # Small delay to avoid rate limiting
        time.sleep(0.1)
    
    # Clear cursor on completion
    if GOLDSKY_CURSOR_FILE.exists():
        GOLDSKY_CURSOR_FILE.unlink()
    
    elapsed = time.time() - start_time
    log(f"  Goldsky update complete in {elapsed/3600:.1f}h. Added {total_records:,} records.")
    return True


# ============================================================================
# Markets Update
# ============================================================================

def update_markets(batch_size: int = 500) -> bool:
    """Update markets metadata from Polymarket API."""
    import requests
    
    log("Updating markets metadata...")
    ensure_dirs()
    
    headers = [
        'createdAt', 'id', 'question', 'answer1', 'answer2', 'neg_risk',
        'market_slug', 'token1', 'token2', 'condition_id', 'volume', 'ticker', 'closedTime'
    ]
    
    # Count existing records
    current_offset = 0
    if MARKETS_FILE.exists():
        with open(MARKETS_FILE, 'r', encoding='utf-8') as f:
            current_offset = sum(1 for _ in f) - 1  # Exclude header
        log(f"  Found {current_offset} existing markets, resuming...")
        mode = 'a'
    else:
        log("  Creating new markets file")
        mode = 'w'
    
    total_fetched = 0
    
    with open(MARKETS_FILE, mode, newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        if mode == 'w':
            writer.writerow(headers)
        
        while True:
            try:
                response = requests.get(
                    POLYMARKET_API,
                    params={
                        'order': 'createdAt',
                        'ascending': 'true',
                        'limit': batch_size,
                        'offset': current_offset
                    },
                    timeout=30
                )
                
                if response.status_code == 429:
                    log("  Rate limited, waiting 10s...", "WARNING")
                    time.sleep(10)
                    continue
                elif response.status_code == 500:
                    log("  Server error, retrying in 5s...", "WARNING")
                    time.sleep(5)
                    continue
                elif response.status_code != 200:
                    log(f"  API error {response.status_code}", "WARNING")
                    time.sleep(3)
                    continue
                
                markets = response.json()
                
                if not markets:
                    log(f"  Completed. Total: {current_offset + total_fetched}")
                    break
                
                for market in markets:
                    try:
                        # Parse outcomes
                        outcomes = market.get('outcomes', '[]')
                        if isinstance(outcomes, str):
                            outcomes = json.loads(outcomes)
                        answer1 = outcomes[0] if outcomes else ''
                        answer2 = outcomes[1] if len(outcomes) > 1 else ''
                        
                        # Parse tokens
                        tokens = market.get('clobTokenIds', '[]')
                        if isinstance(tokens, str):
                            tokens = json.loads(tokens)
                        token1 = tokens[0] if tokens else ''
                        token2 = tokens[1] if len(tokens) > 1 else ''
                        
                        neg_risk = market.get('negRiskAugmented', False) or market.get('negRiskOther', False)
                        
                        ticker = ''
                        if market.get('events'):
                            ticker = market['events'][0].get('ticker', '')
                        
                        row = [
                            market.get('createdAt', ''),
                            market.get('id', ''),
                            market.get('question', '') or market.get('title', ''),
                            answer1, answer2, neg_risk,
                            market.get('slug', ''),
                            token1, token2,
                            market.get('conditionId', ''),
                            market.get('volume', ''),
                            ticker,
                            market.get('closedTime', '')
                        ]
                        writer.writerow(row)
                        total_fetched += 1
                        
                    except Exception as e:
                        log(f"  Error parsing market: {e}", "WARNING")
                        continue
                
                current_offset += len(markets)
                
                if total_fetched % 1000 == 0:
                    log(f"  Fetched {total_fetched} new markets...")
                
                if len(markets) < batch_size:
                    break
                    
            except requests.exceptions.RequestException as e:
                log(f"  Network error: {e}, retrying...", "WARNING")
                time.sleep(5)
                continue
    
    log(f"  Markets update complete. Added {total_fetched} markets.")
    return True


# ============================================================================
# Process Goldsky to Trades
# ============================================================================

def process_goldsky_to_trades() -> bool:
    """Process goldsky order events into structured trades."""
    try:
        import polars as pl
    except ImportError:
        log("polars not installed. Run: pip install polars", "ERROR")
        return False
    
    log("Processing order events into trades...")
    
    if not GOLDSKY_FILE.exists():
        log("  No goldsky data found. Run update first.", "ERROR")
        return False
    
    if not MARKETS_FILE.exists():
        log("  No markets data found. Run markets update first.", "ERROR")
        return False
    
    # Load markets
    log("  Loading markets...")
    schema_overrides = {"token1": pl.Utf8, "token2": pl.Utf8}
    markets_df = pl.read_csv(str(MARKETS_FILE), schema_overrides=schema_overrides)
    markets_df = markets_df.rename({'id': 'market_id'})
    
    # Create token lookup
    markets_long = (
        markets_df
        .select(["market_id", "token1", "token2"])
        .melt(id_vars="market_id", value_vars=["token1", "token2"],
              variable_name="side", value_name="asset_id")
    )
    
    # Load goldsky data
    log("  Loading order events...")
    gs_schema = {"takerAssetId": pl.Utf8, "makerAssetId": pl.Utf8}
    df = pl.scan_csv(str(GOLDSKY_FILE), schema_overrides=gs_schema).collect(streaming=True)
    log(f"  Loaded {len(df):,} order events")
    
    # Convert timestamp
    df = df.with_columns(
        pl.from_epoch(pl.col('timestamp'), time_unit='s').alias('timestamp')
    )
    
    # Check for incremental processing
    start_idx = 0
    if TRADES_FILE.exists():
        last_line = get_last_line(TRADES_FILE)
        if last_line:
            parts = last_line.split(',')
            if len(parts) >= 10:
                last_hash = parts[-1]
                last_maker = parts[2]
                last_taker = parts[3]
                
                df = df.with_row_index()
                match = df.filter(
                    (pl.col("transactionHash") == last_hash) &
                    (pl.col("maker") == last_maker) &
                    (pl.col("taker") == last_taker)
                )
                
                if len(match) > 0:
                    start_idx = match.row(0)[0] + 1
                    log(f"  Resuming from row {start_idx:,}")
                    df = df.filter(pl.col('index') > start_idx - 1).drop('index')
                else:
                    df = df.drop('index')
    
    if len(df) == 0:
        log("  No new events to process")
        return True
    
    log(f"  Processing {len(df):,} new events...")
    
    # Identify non-USDC asset
    df = df.with_columns(
        pl.when(pl.col("makerAssetId") != "0")
        .then(pl.col("makerAssetId"))
        .otherwise(pl.col("takerAssetId"))
        .alias("nonusdc_asset_id")
    )
    
    # Join with markets
    df = df.join(markets_long, left_on="nonusdc_asset_id", right_on="asset_id", how="left")
    
    # Calculate trade details
    df = df.with_columns([
        pl.when(pl.col("makerAssetId") == "0").then(pl.lit("USDC")).otherwise(pl.col("side")).alias("makerAsset"),
        pl.when(pl.col("takerAssetId") == "0").then(pl.lit("USDC")).otherwise(pl.col("side")).alias("takerAsset"),
        (pl.col("makerAmountFilled") / 10**6).alias("makerAmountFilled"),
        (pl.col("takerAmountFilled") / 10**6).alias("takerAmountFilled"),
    ])
    
    df = df.with_columns([
        pl.when(pl.col("takerAsset") == "USDC").then(pl.lit("BUY")).otherwise(pl.lit("SELL")).alias("taker_direction"),
        pl.when(pl.col("takerAsset") == "USDC").then(pl.lit("SELL")).otherwise(pl.lit("BUY")).alias("maker_direction"),
        pl.when(pl.col("makerAsset") != "USDC").then(pl.col("makerAsset")).otherwise(pl.col("takerAsset")).alias("nonusdc_side"),
        pl.when(pl.col("takerAsset") == "USDC").then(pl.col("takerAmountFilled")).otherwise(pl.col("makerAmountFilled")).alias("usd_amount"),
        pl.when(pl.col("takerAsset") != "USDC").then(pl.col("takerAmountFilled")).otherwise(pl.col("makerAmountFilled")).alias("token_amount"),
    ])
    
    df = df.with_columns(
        (pl.col("usd_amount") / pl.col("token_amount")).cast(pl.Float64).alias("price")
    )
    
    # Select final columns
    result = df.select([
        'timestamp', 'market_id', 'maker', 'taker', 'nonusdc_side',
        'maker_direction', 'taker_direction', 'price', 'usd_amount',
        'token_amount', 'transactionHash'
    ])
    
    # Filter valid trades
    result = result.filter(pl.col("market_id").is_not_null())
    
    # Save
    if TRADES_FILE.exists() and start_idx > 0:
        with open(str(TRADES_FILE), "a", encoding='utf-8') as f:
            result.write_csv(f, include_header=False)
        log(f"  Appended {len(result):,} trades")
    else:
        result.write_csv(str(TRADES_FILE))
        log(f"  Created trades file with {len(result):,} trades")
    
    return True


# ============================================================================
# Split Trades to Markets
# ============================================================================

def split_trades_to_markets(incremental: bool = True, min_trades: int = 50) -> bool:
    """Split trades.csv into per-market files."""
    try:
        import polars as pl
    except ImportError:
        log("polars not installed. Run: pip install polars", "ERROR")
        return False
    
    if not TRADES_FILE.exists():
        log("No trades.csv found", "ERROR")
        return False
    
    log("Splitting trades into per-market files...")
    start_time = time.time()
    
    state = load_state()
    last_offset = state.get("last_split_offset", 0) if incremental else 0
    
    # Count rows
    total_rows = pl.scan_csv(str(TRADES_FILE)).select(pl.len()).collect().item()
    log(f"  Total rows: {total_rows:,}")
    
    if incremental and last_offset >= total_rows:
        log("  Already up to date")
        return True
    
    rows_to_process = total_rows - last_offset
    log(f"  Processing {rows_to_process:,} new rows...")
    
    # Load new data
    df = pl.scan_csv(str(TRADES_FILE))
    if last_offset > 0:
        df = df.slice(last_offset, rows_to_process)
    df = df.collect(streaming=True)
    
    # Group and save
    markets_updated = 0
    markets_created = 0
    small_markets: Dict[int, list] = {}
    
    for (market_id,), group in df.group_by(["market_id"]):
        if market_id is None:
            continue
        
        market_id = int(market_id)
        market_file = MARKET_TRADES_DIR / f"market_{market_id}.csv"
        
        if market_file.exists():
            existing = pl.read_csv(str(market_file))
            combined = pl.concat([existing, group])
            combined.write_csv(str(market_file))
            markets_updated += 1
        else:
            if len(group) >= min_trades:
                group.write_csv(str(market_file))
                markets_created += 1
            else:
                if market_id not in small_markets:
                    small_markets[market_id] = []
                small_markets[market_id].extend(group.to_dicts())
    
    # Handle small markets
    for market_id, trades in small_markets.items():
        if len(trades) >= min_trades:
            market_file = MARKET_TRADES_DIR / f"market_{market_id}.csv"
            pl.DataFrame(trades).write_csv(str(market_file))
            markets_created += 1
    
    # Update state
    state["last_split_offset"] = total_rows
    state["last_split_time"] = datetime.now().isoformat()
    state["total_market_files"] = len(list(MARKET_TRADES_DIR.glob("market_*.csv")))
    save_state(state)
    
    elapsed = time.time() - start_time
    log(f"  Split complete in {elapsed:.1f}s")
    log(f"    - Updated: {markets_updated}, Created: {markets_created}")
    log(f"    - Total market files: {state['total_market_files']}")
    
    return True


# ============================================================================
# Status and Main
# ============================================================================

def show_status():
    """Show current data status."""
    print("\n" + "=" * 60)
    print("ARCHIVE DATA STATUS")
    print("=" * 60)
    
    print("\n[DATA FILES]")
    
    for name, path in [
        ("goldsky/orderFilled.csv", GOLDSKY_FILE),
        ("processed/trades.csv", TRADES_FILE),
        ("markets.csv", MARKETS_FILE),
    ]:
        stats = get_file_stats(path)
        if stats["exists"]:
            print(f"  {name}: {stats['size_mb']:.1f} MB (~{stats['lines']:,} rows)")
        else:
            print(f"  {name}: NOT FOUND")
    
    if MARKET_TRADES_DIR.exists():
        files = list(MARKET_TRADES_DIR.glob("market_*.csv"))
        total_size = sum(f.stat().st_size for f in files) / (1024 * 1024)
        print(f"  market_trades/: {len(files)} files, {total_size:.1f} MB")
    else:
        print("  market_trades/: NOT FOUND")
    
    state = load_state()
    if state:
        print("\n[STATE]")
        print(f"  Last split offset: {state.get('last_split_offset', 0):,}")
        print(f"  Last split time: {state.get('last_split_time', 'N/A')}")
    
    print("=" * 60 + "\n")


def full_update() -> bool:
    """Run full update pipeline."""
    print("\n" + "=" * 60)
    print("STARTING FULL ARCHIVE UPDATE")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")
    
    start_time = time.time()
    
    log("Step 1/4: Updating Goldsky data...")
    if not update_goldsky():
        log("Failed at Goldsky step", "ERROR")
        return False
    
    log("Step 2/4: Updating markets...")
    if not update_markets():
        log("Failed at markets step (non-critical)", "WARNING")
    
    log("Step 3/4: Processing trades...")
    if not process_goldsky_to_trades():
        log("Failed at processing step", "ERROR")
        return False
    
    log("Step 4/4: Splitting to market files...")
    if not split_trades_to_markets():
        log("Failed at split step", "ERROR")
        return False
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 60)
    print(f"[SUCCESS] Update completed in {elapsed:.1f}s")
    print("=" * 60 + "\n")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Update Polymarket archive data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python update_archive.py              # Full update
  python update_archive.py --status     # Show data status
  python update_archive.py --goldsky    # Only update goldsky events
  python update_archive.py --markets    # Only update markets metadata
  python update_archive.py --process    # Only process goldsky to trades
  python update_archive.py --split-only # Only split trades to market files
        """
    )
    parser.add_argument("--status", action="store_true", help="Show data status")
    parser.add_argument("--goldsky", action="store_true", help="Only update goldsky")
    parser.add_argument("--markets", action="store_true", help="Only update markets")
    parser.add_argument("--process", action="store_true", help="Only process to trades")
    parser.add_argument("--split-only", action="store_true", help="Only split trades")
    parser.add_argument("--full-split", action="store_true", help="Full re-split")
    
    args = parser.parse_args()
    
    if args.status:
        show_status()
        return
    
    if args.goldsky:
        update_goldsky()
        return
    
    if args.markets:
        update_markets()
        return
    
    if args.process:
        process_goldsky_to_trades()
        return
    
    if args.split_only:
        split_trades_to_markets(incremental=not args.full_split)
        return
    
    full_update()


if __name__ == "__main__":
    main()
