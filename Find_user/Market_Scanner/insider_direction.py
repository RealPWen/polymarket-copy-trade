"""
Combined Insider Direction Detector

Combines:
1. Insider scoring logic (from historical_backtest_v2.py)
2. Incremental/daily analysis (from spike_detector.py)

For each day:
- Calculate insider score for active wallets
- Filter to high-score wallets (insider candidates)
- Calculate direction ratio for ONLY insider candidates
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

# =============================================================================
# Configuration
# =============================================================================

@dataclass
class Config:
    market_name: str = "Trump Win 2024"
    winning_token: str = "token1"
    trades_file: str = "output/trump_win_trades_oct_nov.csv"
    
    # Insider thresholds
    min_insider_score: int = 80  # Only count wallets above this score
    min_volume: float = 10000  # Min volume to be considered

# =============================================================================
# Wallet Profile
# =============================================================================

@dataclass 
class DailyWalletProfile:
    """Profile of a wallet's activity on a specific day."""
    address: str
    date: str
    
    # Volume
    buy_vol_yes: float = 0.0
    buy_vol_no: float = 0.0
    buy_shares_yes: float = 0.0
    buy_shares_no: float = 0.0
    
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
# Insider Score Calculation (from historical_backtest_v2.py)
# =============================================================================

def calculate_insider_score(profile: DailyWalletProfile) -> Tuple[int, dict]:
    """
    Calculate insider score for a wallet's daily activity.
    
    Key features:
    1. High conviction (large bets)
    2. Size anomaly (max trade >> median)
    3. Trading burst (concentrated in short time)
    """
    score = 0
    metrics = {}
    
    # 1. Conviction (volume in dominant direction)
    conviction = profile.conviction
    metrics["conviction"] = round(conviction, 0)
    
    if conviction >= 100000:
        score += 40
        metrics["conviction_tier"] = "WHALE"
    elif conviction >= 50000:
        score += 30
        metrics["conviction_tier"] = "HIGH"
    elif conviction >= 20000:
        score += 20
        metrics["conviction_tier"] = "MODERATE"
    elif conviction >= 10000:
        score += 10
        metrics["conviction_tier"] = "LOW"
    
    # 2. Trade size anomaly
    if len(profile.trade_sizes) >= 2:
        max_size = max(profile.trade_sizes)
        median_size = statistics.median(profile.trade_sizes)
        
        if median_size > 0:
            ratio = max_size / median_size
            metrics["size_ratio"] = round(ratio, 1)
            
            if ratio > 50:
                score += 30
                metrics["size_signal"] = "EXTREME"
            elif ratio > 20:
                score += 20
                metrics["size_signal"] = "HIGH"
            elif ratio > 10:
                score += 10
                metrics["size_signal"] = "MODERATE"
    
    # 3. Single-day burst (trading concentrated in one day = suspicious)
    if profile.first_trade_ts and profile.last_trade_ts:
        span_hours = (profile.last_trade_ts - profile.first_trade_ts).total_seconds() / 3600
        
        if span_hours <= 2 and profile.total_volume > 20000:
            score += 30
            metrics["timing"] = "EXTREME_BURST"
        elif span_hours <= 6:
            score += 20
            metrics["timing"] = "BURST"
        elif span_hours <= 12:
            score += 10
            metrics["timing"] = "CONCENTRATED"
    
    # 4. High directional conviction ratio
    total = profile.buy_vol_yes + profile.buy_vol_no
    if total > 0:
        directional = abs(profile.buy_vol_yes - profile.buy_vol_no) / total
        metrics["directional_ratio"] = round(directional, 3)
        
        if directional > 0.9:
            score += 20
            metrics["directional"] = "EXTREME"
        elif directional > 0.7:
            score += 10
            metrics["directional"] = "HIGH"
    
    metrics["direction"] = profile.direction
    
    return score, metrics

# =============================================================================
# Daily Insider Analysis
# =============================================================================

def process_trades_by_day(trades_file: str) -> Dict[str, Dict[str, DailyWalletProfile]]:
    """
    Process trades and group by day -> wallet.
    Returns: {date: {wallet_address: DailyWalletProfile}}
    """
    print(f"[INFO] Loading trades from {trades_file}...")
    
    daily_profiles: Dict[str, Dict[str, DailyWalletProfile]] = defaultdict(dict)
    
    for chunk in pd.read_csv(trades_file, chunksize=500000):
        for _, row in chunk.iterrows():
            try:
                maker = str(row['maker']).lower()
                taker = str(row['taker']).lower()
                usd = float(row.get('usd_amount', 0) or 0)
                shares = float(row.get('token_amount', 0) or 0)
                token_side = str(row.get('nonusdc_side', ''))
                maker_dir = str(row.get('maker_direction', '')).upper()
                
                ts_str = str(row.get('timestamp', ''))
                try:
                    ts = datetime.fromisoformat(ts_str.split('+')[0].replace('Z', ''))
                except:
                    continue
                
                day = ts.strftime('%Y-%m-%d')
                
                # Process each participant
                for addr, is_buy in [(maker, maker_dir == 'BUY'), (taker, maker_dir != 'BUY')]:
                    if not is_buy:
                        continue  # Only track buyers
                    
                    if addr not in daily_profiles[day]:
                        daily_profiles[day][addr] = DailyWalletProfile(address=addr, date=day)
                    
                    p = daily_profiles[day][addr]
                    p.trade_count += 1
                    p.trade_sizes.append(usd)
                    
                    if p.first_trade_ts is None or ts < p.first_trade_ts:
                        p.first_trade_ts = ts
                    if p.last_trade_ts is None or ts > p.last_trade_ts:
                        p.last_trade_ts = ts
                    
                    if token_side == 'token1':  # YES
                        p.buy_vol_yes += usd
                        p.buy_shares_yes += shares
                    else:  # NO
                        p.buy_vol_no += usd
                        p.buy_shares_no += shares
            except:
                pass
        
        print(f"  Processed chunk, {len(daily_profiles)} days...")
    
    return daily_profiles


def analyze_daily_insiders(daily_profiles: Dict[str, Dict[str, DailyWalletProfile]], 
                           config: Config) -> List[dict]:
    """
    For each day, find insider candidates and calculate their direction.
    """
    results = []
    
    for day in sorted(daily_profiles.keys()):
        wallets = daily_profiles[day]
        
        # Score each wallet
        day_insiders = []
        for addr, profile in wallets.items():
            if profile.total_volume < config.min_volume:
                continue
            
            score, metrics = calculate_insider_score(profile)
            
            if score >= config.min_insider_score:
                day_insiders.append({
                    "address": addr,
                    "score": score,
                    "direction": profile.direction,
                    "conviction": profile.conviction,
                    "metrics": metrics
                })
        
        # Calculate insider direction
        yes_conviction = sum(w["conviction"] for w in day_insiders if w["direction"] == "YES")
        no_conviction = sum(w["conviction"] for w in day_insiders if w["direction"] == "NO")
        total_conviction = yes_conviction + no_conviction
        
        yes_count = sum(1 for w in day_insiders if w["direction"] == "YES")
        no_count = sum(1 for w in day_insiders if w["direction"] == "NO")
        
        if total_conviction > 0:
            insider_direction = (yes_conviction - no_conviction) / total_conviction
        else:
            insider_direction = 0
        
        # Interpretation
        if insider_direction > 0.3:
            signal = "STRONG_YES"
        elif insider_direction > 0.1:
            signal = "YES"
        elif insider_direction < -0.3:
            signal = "STRONG_NO"
        elif insider_direction < -0.1:
            signal = "NO"
        else:
            signal = "NEUTRAL"
        
        results.append({
            "date": day,
            "insider_count": len(day_insiders),
            "yes_insiders": yes_count,
            "no_insiders": no_count,
            "yes_conviction": round(yes_conviction, 0),
            "no_conviction": round(no_conviction, 0),
            "insider_direction": round(insider_direction, 3),
            "signal": signal,
            "top_insiders": sorted(day_insiders, key=lambda x: x["score"], reverse=True)[:5]
        })
    
    return results


def run_analysis():
    """Run the combined insider direction analysis."""
    config = Config()
    
    print("=" * 70)
    print(f"INSIDER DIRECTION ANALYSIS: {config.market_name}")
    print("=" * 70)
    print(f"Min Insider Score: {config.min_insider_score}")
    print(f"Min Volume: ${config.min_volume:,}")
    print()
    
    # Load and process
    daily_profiles = process_trades_by_day(config.trades_file)
    
    # Analyze
    print("\n[ANALYZING] Daily insider direction...")
    results = analyze_daily_insiders(daily_profiles, config)
    
    # Print results
    print("\n" + "=" * 90)
    print("DAILY INSIDER DIRECTION")
    print("=" * 90)
    print(f"\n{'Date':<12} {'Insiders':>10} {'YES':>6} {'NO':>6} {'YES Conv':>14} {'NO Conv':>14} {'Direction':>12} {'Signal':>12}")
    print("-" * 90)
    
    for r in results:
        print(f"{r['date']:<12} {r['insider_count']:>10} {r['yes_insiders']:>6} {r['no_insiders']:>6} "
              f"${r['yes_conviction']:>12,.0f} ${r['no_conviction']:>12,.0f} "
              f"{r['insider_direction']:>+11.3f} {r['signal']:>12}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    yes_days = sum(1 for r in results if r['signal'] in ['YES', 'STRONG_YES'])
    no_days = sum(1 for r in results if r['signal'] in ['NO', 'STRONG_NO'])
    neutral_days = sum(1 for r in results if r['signal'] == 'NEUTRAL')
    
    print(f"\nYES signal days: {yes_days}")
    print(f"NO signal days: {no_days}")
    print(f"NEUTRAL days: {neutral_days}")
    
    avg_direction = statistics.mean([r['insider_direction'] for r in results]) if results else 0
    print(f"\nAverage insider direction: {avg_direction:+.3f}")
    
    # Validation
    actual = "YES" if config.winning_token == "token1" else "NO"
    predicted = "YES" if avg_direction > 0 else "NO"
    
    print(f"\nActual winner: {actual}")
    print(f"Predicted: {predicted}")
    print(f"Correct: {'[SUCCESS]' if actual == predicted else '[WRONG]'}")
    
    # Accuracy
    if config.winning_token == "token1":
        correct_days = yes_days
        total_signal_days = yes_days + no_days
    else:
        correct_days = no_days
        total_signal_days = yes_days + no_days
    
    if total_signal_days > 0:
        accuracy = correct_days / total_signal_days
        print(f"Daily accuracy: {correct_days}/{total_signal_days} ({accuracy*100:.0f}%)")
    
    # Save
    output = {
        "config": {
            "market_name": config.market_name,
            "min_insider_score": config.min_insider_score,
            "winning_token": config.winning_token
        },
        "summary": {
            "yes_days": yes_days,
            "no_days": no_days,
            "neutral_days": neutral_days,
            "avg_direction": round(avg_direction, 3),
            "predicted": predicted,
            "actual": actual,
            "correct": actual == predicted
        },
        "daily_results": results
    }
    
    output_file = os.path.join(OUTPUT_DIR, "insider_direction.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n\nResults saved to: {output_file}")
    return output


if __name__ == "__main__":
    run_analysis()
