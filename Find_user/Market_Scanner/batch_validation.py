"""
Batch Validation of Insider Direction Strategy

Objective:
- Test the insider direction strategy on MANY resolved markets
- Calculate overall accuracy to prove it's not luck

Data:
- archive/markets.csv: Market metadata (119K markets)
- archive/goldsky/orderFilled.csv: 39GB complete trade history

Strategy:
1. Select a sample of resolved markets with sufficient volume
2. For each market, run insider direction analysis
3. Compare predicted direction vs actual outcome
4. Calculate overall accuracy
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import statistics

sys.stdout.reconfigure(encoding='utf-8')

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

ARCHIVE_DIR = os.path.join(os.path.dirname(__file__), "archive")
MARKETS_FILE = os.path.join(ARCHIVE_DIR, "markets.csv")
TRADES_FILE = os.path.join(ARCHIVE_DIR, "goldsky", "orderFilled.csv")

# =============================================================================
# Configuration
# =============================================================================

@dataclass
class ValidationConfig:
    min_volume: float = 100000  # Min market volume to test
    min_trades: int = 100  # Min trades in market
    sample_size: int = 50  # Number of markets to test
    min_insider_score: int = 80  # Insider threshold
    min_wallet_volume: float = 10000  # Min volume per wallet

# =============================================================================
# Wallet Profile (simplified for batch processing)
# =============================================================================

@dataclass 
class WalletProfile:
    address: str
    buy_vol_yes: float = 0.0
    buy_vol_no: float = 0.0
    trade_count: int = 0
    trade_sizes: List[float] = field(default_factory=list)
    first_trade_ts: Optional[datetime] = None
    last_trade_ts: Optional[datetime] = None
    
    @property
    def total_volume(self) -> float:
        return self.buy_vol_yes + self.buy_vol_no
    
    @property
    def direction(self) -> str:
        if self.buy_vol_yes > self.buy_vol_no:
            return "YES"
        elif self.buy_vol_no > self.buy_vol_yes:
            return "NO"
        return "NEUTRAL"
    
    @property
    def conviction(self) -> float:
        return max(self.buy_vol_yes, self.buy_vol_no)

# =============================================================================
# Insider Score (simplified)
# =============================================================================

def calculate_insider_score(profile: WalletProfile) -> int:
    """Simplified insider score for batch processing."""
    score = 0
    
    # Conviction tier
    if profile.conviction >= 100000:
        score += 40
    elif profile.conviction >= 50000:
        score += 30
    elif profile.conviction >= 20000:
        score += 20
    elif profile.conviction >= 10000:
        score += 10
    
    # Size anomaly
    if len(profile.trade_sizes) >= 2:
        max_size = max(profile.trade_sizes)
        median_size = statistics.median(profile.trade_sizes)
        if median_size > 0:
            ratio = max_size / median_size
            if ratio > 50:
                score += 30
            elif ratio > 20:
                score += 20
            elif ratio > 10:
                score += 10
    
    # Timing burst
    if profile.first_trade_ts and profile.last_trade_ts:
        span = (profile.last_trade_ts - profile.first_trade_ts).total_seconds() / 3600
        if span <= 2 and profile.total_volume > 20000:
            score += 30
        elif span <= 6:
            score += 20
        elif span <= 12:
            score += 10
    
    # Directional conviction
    total = profile.buy_vol_yes + profile.buy_vol_no
    if total > 0:
        directional = abs(profile.buy_vol_yes - profile.buy_vol_no) / total
        if directional > 0.9:
            score += 20
        elif directional > 0.7:
            score += 10
    
    return score

# =============================================================================
# Market Analysis
# =============================================================================

def analyze_market_trades(trades_df: pd.DataFrame, config: ValidationConfig) -> dict:
    """
    Analyze a single market's trades and return insider direction signal.
    """
    profiles: Dict[str, WalletProfile] = {}
    
    for _, row in trades_df.iterrows():
        try:
            # Parse trade
            maker = str(row.get('maker', '')).lower()
            taker = str(row.get('taker', '')).lower()
            
            # Handle different column names
            usd = float(row.get('usd_amount', 0) or row.get('amount', 0) or 0)
            
            # Determine token side
            # In orderFilled.csv, we need to check the outcome/asset column
            outcome = str(row.get('outcome', row.get('asset_id', ''))).lower()
            
            # Simplified: assume "yes" or "1" in outcome = YES token
            is_yes_token = 'yes' in outcome or outcome == '1' or 'token1' in outcome
            
            maker_dir = str(row.get('maker_direction', row.get('side', ''))).upper()
            
            ts_str = str(row.get('timestamp', row.get('block_timestamp', '')))
            try:
                if 'T' in ts_str:
                    ts = datetime.fromisoformat(ts_str.split('+')[0].replace('Z', ''))
                else:
                    ts = datetime.fromtimestamp(float(ts_str))
            except:
                continue
            
            # Process each buyer
            for addr, is_buy in [(maker, maker_dir == 'BUY'), (taker, maker_dir != 'BUY')]:
                if not is_buy or not addr:
                    continue
                
                if addr not in profiles:
                    profiles[addr] = WalletProfile(address=addr)
                
                p = profiles[addr]
                p.trade_count += 1
                p.trade_sizes.append(usd)
                
                if p.first_trade_ts is None or ts < p.first_trade_ts:
                    p.first_trade_ts = ts
                if p.last_trade_ts is None or ts > p.last_trade_ts:
                    p.last_trade_ts = ts
                
                if is_yes_token:
                    p.buy_vol_yes += usd
                else:
                    p.buy_vol_no += usd
        except Exception as e:
            continue
    
    # Find insiders
    insiders = []
    for addr, profile in profiles.items():
        if profile.total_volume < config.min_wallet_volume:
            continue
        
        score = calculate_insider_score(profile)
        
        if score >= config.min_insider_score:
            insiders.append({
                "address": addr,
                "score": score,
                "direction": profile.direction,
                "conviction": profile.conviction
            })
    
    if not insiders:
        return {"signal": "NO_DATA", "insiders": 0}
    
    # Calculate direction
    yes_conviction = sum(i["conviction"] for i in insiders if i["direction"] == "YES")
    no_conviction = sum(i["conviction"] for i in insiders if i["direction"] == "NO")
    total = yes_conviction + no_conviction
    
    if total > 0:
        direction_score = (yes_conviction - no_conviction) / total
    else:
        direction_score = 0
    
    predicted = "YES" if direction_score > 0 else "NO"
    
    return {
        "signal": predicted,
        "direction_score": round(direction_score, 3),
        "insiders": len(insiders),
        "yes_insiders": sum(1 for i in insiders if i["direction"] == "YES"),
        "no_insiders": sum(1 for i in insiders if i["direction"] == "NO"),
        "yes_conviction": round(yes_conviction, 0),
        "no_conviction": round(no_conviction, 0)
    }

# =============================================================================
# Batch Validation
# =============================================================================

def load_markets(min_volume: float) -> pd.DataFrame:
    """Load markets with sufficient volume."""
    print(f"[INFO] Loading markets from {MARKETS_FILE}...")
    
    df = pd.read_csv(MARKETS_FILE)
    
    # Filter closed markets with volume
    df = df[df['closedTime'].notna()]
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
    df = df[df['volume'] >= min_volume]
    
    print(f"[INFO] Found {len(df)} closed markets with volume >= ${min_volume:,.0f}")
    return df


def run_batch_validation(config: ValidationConfig):
    """
    Run validation on multiple markets.
    """
    print("=" * 70)
    print("BATCH VALIDATION: Insider Direction Strategy")
    print("=" * 70)
    print(f"Sample size: {config.sample_size}")
    print(f"Min market volume: ${config.min_volume:,}")
    print(f"Min insider score: {config.min_insider_score}")
    print()
    
    # Load markets
    markets = load_markets(config.min_volume)
    
    # Sort by volume and take top N
    markets = markets.nlargest(config.sample_size * 2, 'volume')  # Get more to filter
    
    print(f"\n[INFO] Will analyze up to {config.sample_size} markets")
    print(f"[INFO] Loading trades from {TRADES_FILE}...")
    print("[INFO] This may take a while for 39GB file...")
    
    # We need to scan the big file and extract trades for selected markets
    # First, get the condition_ids we need
    market_ids = set(markets['id'].astype(str).tolist())
    condition_ids = set(markets['condition_id'].astype(str).tolist())
    
    print(f"[INFO] Looking for {len(market_ids)} market IDs / {len(condition_ids)} condition IDs")
    
    # Process trades file in chunks
    results = []
    trades_by_market = defaultdict(list)
    
    chunk_count = 0
    for chunk in pd.read_csv(TRADES_FILE, chunksize=500000, low_memory=False):
        chunk_count += 1
        
        # Filter to our markets (check multiple possible ID columns)
        id_cols = ['market_id', 'condition_id', 'market', 'asset_id']
        
        for col in id_cols:
            if col in chunk.columns:
                mask = chunk[col].astype(str).isin(market_ids) | chunk[col].astype(str).isin(condition_ids)
                matched = chunk[mask]
                
                if len(matched) > 0:
                    # Group by market
                    for col2 in id_cols:
                        if col2 in matched.columns:
                            for mid, group in matched.groupby(col2):
                                trades_by_market[str(mid)].extend(group.to_dict('records'))
                            break
                break
        
        if chunk_count % 10 == 0:
            print(f"  Processed {chunk_count} chunks, found trades for {len(trades_by_market)} markets...")
        
        # Stop early if we have enough
        if len(trades_by_market) >= config.sample_size:
            print(f"  Found enough markets, stopping early...")
            break
    
    print(f"\n[INFO] Found trades for {len(trades_by_market)} markets")
    
    # Analyze each market
    print("\n[ANALYZING] Markets...")
    
    for market_id, trades in list(trades_by_market.items())[:config.sample_size]:
        if len(trades) < config.min_trades:
            continue
        
        trades_df = pd.DataFrame(trades)
        
        # Get market info
        market_row = markets[
            (markets['id'].astype(str) == market_id) | 
            (markets['condition_id'].astype(str) == market_id)
        ]
        
        if len(market_row) == 0:
            continue
        
        market_info = market_row.iloc[0]
        
        # Determine actual winner
        # In Polymarket, answer1 = YES typically
        actual = "YES" if str(market_info.get('answer1', '')).lower() in ['yes', '1', 'true'] else "NO"
        
        # Analyze
        analysis = analyze_market_trades(trades_df, config)
        
        if analysis["signal"] == "NO_DATA":
            continue
        
        correct = analysis["signal"] == actual
        
        results.append({
            "market_id": market_id,
            "question": str(market_info.get('question', ''))[:50] + "...",
            "volume": float(market_info.get('volume', 0)),
            "trades": len(trades),
            "predicted": analysis["signal"],
            "actual": actual,
            "correct": correct,
            "direction_score": analysis["direction_score"],
            "insiders": analysis["insiders"]
        })
        
        status = "[OK]" if correct else "[WRONG]"
        print(f"  {len(results)}. {status} {analysis['signal']} (actual: {actual}) | {analysis['insiders']} insiders | {market_info.get('question', '')[:40]}...")
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)
    
    if not results:
        print("No results! Check if trades file has matching market IDs.")
        return
    
    correct_count = sum(1 for r in results if r["correct"])
    total = len(results)
    accuracy = correct_count / total if total > 0 else 0
    
    print(f"\nTotal markets tested: {total}")
    print(f"Correct predictions: {correct_count}")
    print(f"Accuracy: {accuracy*100:.1f}%")
    
    # Statistical significance
    # If random, expected accuracy = 50%
    # Use binomial test
    from scipy import stats
    if total >= 10:
        p_value = stats.binom_test(correct_count, total, 0.5, alternative='greater')
        print(f"\nStatistical test (vs random 50%):")
        print(f"  P-value: {p_value:.4f}")
        print(f"  Significant at 5%: {'YES' if p_value < 0.05 else 'NO'}")
        print(f"  Significant at 1%: {'YES' if p_value < 0.01 else 'NO'}")
    
    # Save results
    output = {
        "config": {
            "sample_size": config.sample_size,
            "min_volume": config.min_volume,
            "min_insider_score": config.min_insider_score
        },
        "summary": {
            "total_markets": total,
            "correct": correct_count,
            "accuracy": round(accuracy, 4),
            "p_value": p_value if total >= 10 else None
        },
        "results": results
    }
    
    output_file = os.path.join(OUTPUT_DIR, "batch_validation.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n\nResults saved to: {output_file}")


if __name__ == "__main__":
    config = ValidationConfig(
        sample_size=30,  # Start with 30 markets
        min_volume=100000,  # Markets with $100K+ volume
    )
    run_batch_validation(config)
