"""
Random Multi-Market Validation

Objective:
- Randomly sample N resolved markets
- Run insider direction analysis on each
- Calculate overall accuracy to prove it's not luck

Key: Use processed/trades.csv which has market_id column for easy filtering
"""

import os
import sys
import json
import random
import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import statistics

sys.stdout.reconfigure(encoding='utf-8')

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

ARCHIVE_DIR = os.path.join(os.path.dirname(__file__), "archive")
MARKETS_FILE = os.path.join(ARCHIVE_DIR, "markets.csv")
TRADES_FILE = os.path.join(ARCHIVE_DIR, "processed", "trades.csv")

# =============================================================================
# Configuration
# =============================================================================

@dataclass
class Config:
    sample_size: int = 30  # Number of random markets to test
    min_market_volume: float = 100000  # Min $100K volume
    min_trades: int = 100  # Min trades in market  
    min_insider_score: int = 80
    min_wallet_volume: float = 10000
    random_seed: int = 42  # For reproducibility

# =============================================================================
# Wallet Profile
# =============================================================================

@dataclass 
class WalletProfile:
    address: str
    buy_vol_yes: float = 0.0
    buy_vol_no: float = 0.0
    trade_sizes: List[float] = field(default_factory=list)
    first_ts: Optional[datetime] = None
    last_ts: Optional[datetime] = None
    
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
# Insider Score
# =============================================================================

def calculate_insider_score(p: WalletProfile) -> int:
    score = 0
    
    # Conviction
    if p.conviction >= 100000:
        score += 40
    elif p.conviction >= 50000:
        score += 30
    elif p.conviction >= 20000:
        score += 20
    elif p.conviction >= 10000:
        score += 10
    
    # Size anomaly
    if len(p.trade_sizes) >= 2:
        max_s = max(p.trade_sizes)
        med_s = statistics.median(p.trade_sizes)
        if med_s > 0:
            ratio = max_s / med_s
            if ratio > 50:
                score += 30
            elif ratio > 20:
                score += 20
            elif ratio > 10:
                score += 10
    
    # Timing
    if p.first_ts and p.last_ts:
        span_h = (p.last_ts - p.first_ts).total_seconds() / 3600
        if span_h <= 2 and p.total_volume > 20000:
            score += 30
        elif span_h <= 6:
            score += 20
        elif span_h <= 12:
            score += 10
    
    # Directional
    total = p.buy_vol_yes + p.buy_vol_no
    if total > 0:
        d = abs(p.buy_vol_yes - p.buy_vol_no) / total
        if d > 0.9:
            score += 20
        elif d > 0.7:
            score += 10
    
    return score

# =============================================================================
# Market Analysis
# =============================================================================

def analyze_market(trades_df: pd.DataFrame, config: Config) -> dict:
    """Analyze a single market's insider direction."""
    profiles: Dict[str, WalletProfile] = {}
    
    for _, row in trades_df.iterrows():
        try:
            maker = str(row.get('maker', '')).lower()
            taker = str(row.get('taker', '')).lower()
            usd = float(row.get('usd_amount', 0) or 0)
            token_side = str(row.get('nonusdc_side', ''))
            maker_dir = str(row.get('maker_direction', '')).upper()
            
            ts_str = str(row.get('timestamp', ''))
            try:
                ts = datetime.fromisoformat(ts_str.replace('Z', ''))
            except:
                continue
            
            for addr, is_buy in [(maker, maker_dir == 'BUY'), (taker, maker_dir != 'BUY')]:
                if not is_buy or not addr:
                    continue
                
                if addr not in profiles:
                    profiles[addr] = WalletProfile(address=addr)
                
                p = profiles[addr]
                p.trade_sizes.append(usd)
                
                if p.first_ts is None or ts < p.first_ts:
                    p.first_ts = ts
                if p.last_ts is None or ts > p.last_ts:
                    p.last_ts = ts
                
                if token_side == 'token1':
                    p.buy_vol_yes += usd
                else:
                    p.buy_vol_no += usd
        except:
            continue
    
    # Find insiders
    insiders = []
    for addr, p in profiles.items():
        if p.total_volume < config.min_wallet_volume:
            continue
        score = calculate_insider_score(p)
        if score >= config.min_insider_score:
            insiders.append({
                "direction": p.direction,
                "conviction": p.conviction,
                "score": score
            })
    
    if not insiders:
        return {"signal": "NO_DATA"}
    
    yes_conv = sum(i["conviction"] for i in insiders if i["direction"] == "YES")
    no_conv = sum(i["conviction"] for i in insiders if i["direction"] == "NO")
    total = yes_conv + no_conv
    
    if total == 0:
        return {"signal": "NO_DATA"}
    
    direction_score = (yes_conv - no_conv) / total
    
    return {
        "signal": "YES" if direction_score > 0 else "NO",
        "direction_score": round(direction_score, 3),
        "insiders": len(insiders),
        "yes_conviction": yes_conv,
        "no_conviction": no_conv
    }

# =============================================================================
# Main
# =============================================================================

def run_validation(config: Config):
    print("=" * 70)
    print("RANDOM MULTI-MARKET VALIDATION")
    print("=" * 70)
    print(f"Sample size: {config.sample_size}")
    print(f"Min volume: ${config.min_market_volume:,}")
    print(f"Random seed: {config.random_seed}")
    print()
    
    random.seed(config.random_seed)
    
    # Load markets
    print("[INFO] Loading markets...")
    markets_df = pd.read_csv(MARKETS_FILE)
    markets_df = markets_df[markets_df['closedTime'].notna()]
    markets_df['volume'] = pd.to_numeric(markets_df['volume'], errors='coerce')
    markets_df = markets_df[markets_df['volume'] >= config.min_market_volume]
    
    print(f"  Eligible markets: {len(markets_df)}")
    
    # Random sample
    sample_ids = random.sample(list(markets_df['id'].astype(int)), min(config.sample_size * 3, len(markets_df)))
    
    print(f"  Sampled {len(sample_ids)} market IDs for testing")
    
    # Load trades in chunks, filter to our sample
    print("\n[INFO] Loading trades (may take a while)...")
    
    trades_by_market = defaultdict(list)
    chunks_processed = 0
    
    for chunk in pd.read_csv(TRADES_FILE, chunksize=2000000, low_memory=False):
        chunks_processed += 1
        
        # Filter to sample markets
        chunk['market_id'] = pd.to_numeric(chunk['market_id'], errors='coerce')
        matched = chunk[chunk['market_id'].isin(sample_ids)]
        
        if len(matched) > 0:
            for mid, group in matched.groupby('market_id'):
                trades_by_market[int(mid)].extend(group.to_dict('records'))
        
        if chunks_processed % 10 == 0:
            print(f"  Chunks: {chunks_processed}, Markets found: {len(trades_by_market)}")
        
        # Stop if we have enough
        if len(trades_by_market) >= config.sample_size:
            have_enough = sum(1 for mid in trades_by_market if len(trades_by_market[mid]) >= config.min_trades)
            if have_enough >= config.sample_size:
                print(f"  Found enough markets ({have_enough}), stopping.")
                break
    
    print(f"\n[INFO] Found trades for {len(trades_by_market)} markets")
    
    # Analyze each market
    print("\n[ANALYZING]...")
    results = []
    
    for market_id in list(trades_by_market.keys())[:config.sample_size]:
        trades = trades_by_market[market_id]
        
        if len(trades) < config.min_trades:
            continue
        
        trades_df = pd.DataFrame(trades)
        
        # Get market info
        market_row = markets_df[markets_df['id'] == market_id]
        if len(market_row) == 0:
            continue
        
        market_info = market_row.iloc[0]
        
        # Determine actual winner from LAST TRADE PRICE
        # If final YES price -> 1.0, YES won
        # If final YES price -> 0.0, NO won
        last_trades = trades_df.sort_values('timestamp').tail(10)
        
        # Get last YES token price
        yes_trades = last_trades[last_trades['nonusdc_side'] == 'token1']
        if len(yes_trades) > 0:
            last_yes_price = yes_trades['price'].astype(float).mean()
        else:
            last_yes_price = 0.5  # Unknown
        
        # Infer winner
        if last_yes_price > 0.8:
            actual = "YES"
        elif last_yes_price < 0.2:
            actual = "NO"
        else:
            # Skip markets with unclear outcome
            continue
        
        # Analyze
        analysis = analyze_market(trades_df, config)
        
        if analysis["signal"] == "NO_DATA":
            continue
        
        correct = analysis["signal"] == actual
        
        results.append({
            "market_id": market_id,
            "question": str(market_info.get('question', ''))[:50],
            "volume": float(market_info.get('volume', 0)),
            "trades": len(trades),
            "predicted": analysis["signal"],
            "actual": actual,
            "correct": correct,
            "direction_score": analysis["direction_score"],
            "insiders": analysis["insiders"]
        })
        
        status = "[OK]" if correct else "[WRONG]"
        print(f"  {len(results)}. {status} Pred={analysis['signal']} | Insiders={analysis['insiders']} | {market_info.get('question', '')[:40]}...")
    
    # Summary
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    if not results:
        print("No results!")
        return
    
    correct_count = sum(1 for r in results if r["correct"])
    total = len(results)
    accuracy = correct_count / total
    
    print(f"\nMarkets tested: {total}")
    print(f"Correct: {correct_count}")
    print(f"Accuracy: {accuracy*100:.1f}%")
    
    # Significance test
    if total >= 10:
        try:
            from scipy import stats
            p_value = stats.binom_test(correct_count, total, 0.5, alternative='greater')
            print(f"\nP-value (vs 50% random): {p_value:.4f}")
            print(f"Significant at 5%: {'YES' if p_value < 0.05 else 'NO'}")
        except:
            p_value = None
    
    # Save
    output = {
        "config": vars(config),
        "summary": {
            "total": total,
            "correct": correct_count,
            "accuracy": round(accuracy, 4)
        },
        "results": results
    }
    
    output_file = os.path.join(OUTPUT_DIR, "random_validation.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\nSaved to: {output_file}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--volume", type=float, default=100000)
    args = parser.parse_args()
    
    config = Config(
        sample_size=args.sample,
        random_seed=args.seed,
        min_market_volume=args.volume
    )
    run_validation(config)
