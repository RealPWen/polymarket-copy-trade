"""
Real-time Insider Detection with Directional Asymmetry

Core Insight:
- We don't know which direction is "correct" in real-time
- BUT if one direction has significantly more insider-like activity, that's a signal

Approach:
1. For each market, track insider scores for BOTH directions (YES and NO)
2. Calculate "Directional Asymmetry Score" = diff between YES-side and NO-side insider activity
3. If asymmetry is high -> strong directional signal

Example:
- Market: "Trump wins 2024"
- YES side: 5 wallets with avg insider_score=140
- NO side: 2 wallets with avg insider_score=80
- Asymmetry = strongly favors YES -> bullish signal

This can be validated with historical data first, then applied in real-time.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime
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
class DirectionalConfig:
    market_id: int = 253591
    market_name: str = "Trump Win 2024"
    winning_token: str = "token1"  # For validation only
    
    simulation_date: str = "2024-10-15"
    trades_file: str = "output/trump_win_trades_oct_nov.csv"
    
    # Thresholds
    min_volume_usd: float = 5000
    min_trades: int = 3
    min_insider_score: int = 100  # Only count high-score wallets

# =============================================================================
# Wallet Profile (simplified)
# =============================================================================

@dataclass 
class WalletProfile:
    address: str
    
    # Token1 (YES) activity
    buy_vol_yes: float = 0.0
    sell_vol_yes: float = 0.0
    buy_shares_yes: float = 0.0
    sell_shares_yes: float = 0.0
    
    # Token0 (NO) activity  
    buy_vol_no: float = 0.0
    sell_vol_no: float = 0.0
    buy_shares_no: float = 0.0
    sell_shares_no: float = 0.0
    
    trade_count: int = 0
    trade_sizes: List[float] = field(default_factory=list)
    
    first_trade_ts: Optional[datetime] = None
    last_trade_ts: Optional[datetime] = None
    volume_by_day: Dict[str, float] = field(default_factory=dict)
    
    @property
    def total_volume(self) -> float:
        return self.buy_vol_yes + self.sell_vol_yes + self.buy_vol_no + self.sell_vol_no
    
    @property
    def net_yes_invested(self) -> float:
        return self.buy_vol_yes - self.sell_vol_yes
    
    @property
    def net_no_invested(self) -> float:
        return self.buy_vol_no - self.sell_vol_no
    
    @property
    def net_yes_shares(self) -> float:
        return self.buy_shares_yes - self.sell_shares_yes
    
    @property
    def net_no_shares(self) -> float:
        return self.buy_shares_no - self.sell_shares_no
    
    @property
    def direction(self) -> str:
        """Which side is this wallet betting on?"""
        # Positive net investment = betting on that side
        yes_signal = self.net_yes_invested
        no_signal = self.net_no_invested
        
        if yes_signal > abs(no_signal):
            return "YES"
        elif no_signal > abs(yes_signal):
            return "NO"
        else:
            # Selling YES = betting NO, Selling NO = betting YES
            if yes_signal < 0:
                return "NO"
            elif no_signal < 0:
                return "YES"
            return "NEUTRAL"
    
    @property
    def conviction_amount(self) -> float:
        """How much is invested in the dominant direction?"""
        return max(abs(self.net_yes_invested), abs(self.net_no_invested))
    
    @property
    def active_days(self) -> int:
        return len(self.volume_by_day)

# =============================================================================
# Insider Score Calculation
# =============================================================================

def calculate_insider_score(profile: WalletProfile, sim_date: datetime) -> Tuple[int, dict]:
    """Calculate insider score based on behavioral metrics."""
    score = 0
    metrics = {}
    
    # 1. Time concentration (short window = suspicious)
    if profile.active_days <= 2:
        score += 50
        metrics["time_signal"] = "SHORT_WINDOW"
    elif profile.active_days <= 5:
        score += 20
        metrics["time_signal"] = "MODERATE_WINDOW"
    
    # 2. Size anomaly
    if len(profile.trade_sizes) >= 3:
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
    
    # 3. Timing (burst pattern)
    if profile.first_trade_ts and profile.last_trade_ts:
        span = (profile.last_trade_ts - profile.first_trade_ts).days
        if span <= 3 and profile.total_volume > 10000:
            score += 30
            metrics["pattern"] = "BURST"
        elif span <= 7:
            score += 15
            metrics["pattern"] = "SHORT_WINDOW"
    
    # 4. Conviction (directional strength)
    total_buy = profile.buy_vol_yes + profile.buy_vol_no
    total_sell = profile.sell_vol_yes + profile.sell_vol_no
    total = total_buy + total_sell
    
    if total > 0:
        directional = abs(total_buy - total_sell) / total
        metrics["directional_ratio"] = round(directional, 3)
        
        if directional > 0.9:
            score += 25
        elif directional > 0.7:
            score += 15
        elif directional > 0.5:
            score += 5
    
    # 5. Volume bonus
    if profile.total_volume > 100000:
        score += 20
    elif profile.total_volume > 50000:
        score += 10
    
    metrics["direction"] = profile.direction
    metrics["conviction_amount"] = round(profile.conviction_amount, 0)
    
    return score, metrics

# =============================================================================
# Directional Asymmetry Analysis
# =============================================================================

@dataclass
class DirectionalStats:
    """Statistics for one direction (YES or NO)."""
    wallet_count: int = 0
    high_score_count: int = 0  # wallets with score >= threshold
    total_volume: float = 0.0
    avg_score: float = 0.0
    max_score: int = 0
    total_conviction: float = 0.0
    
    def to_dict(self):
        return {
            "wallet_count": self.wallet_count,
            "high_score_count": self.high_score_count,
            "total_volume": round(self.total_volume, 0),
            "avg_score": round(self.avg_score, 1),
            "max_score": self.max_score,
            "total_conviction": round(self.total_conviction, 0)
        }


def analyze_directional_asymmetry(profiles: Dict[str, WalletProfile], 
                                    sim_date: datetime,
                                    config: DirectionalConfig) -> dict:
    """
    Analyze insider activity by direction and calculate asymmetry.
    
    Returns signal indicating which direction has more "insider-like" activity.
    """
    yes_wallets = []
    no_wallets = []
    
    for addr, profile in profiles.items():
        if profile.total_volume < config.min_volume_usd:
            continue
        if profile.trade_count < config.min_trades:
            continue
        
        score, metrics = calculate_insider_score(profile, sim_date)
        
        wallet_data = {
            "address": addr,
            "score": score,
            "metrics": metrics,
            "volume": profile.total_volume,
            "conviction": profile.conviction_amount,
            "direction": profile.direction
        }
        
        if profile.direction == "YES":
            yes_wallets.append(wallet_data)
        elif profile.direction == "NO":
            no_wallets.append(wallet_data)
    
    # Calculate stats for each direction
    def calc_stats(wallets: List[dict], threshold: int) -> DirectionalStats:
        if not wallets:
            return DirectionalStats()
        
        high_score = [w for w in wallets if w["score"] >= threshold]
        scores = [w["score"] for w in wallets]
        
        return DirectionalStats(
            wallet_count=len(wallets),
            high_score_count=len(high_score),
            total_volume=sum(w["volume"] for w in wallets),
            avg_score=statistics.mean(scores) if scores else 0,
            max_score=max(scores) if scores else 0,
            total_conviction=sum(w["conviction"] for w in wallets)
        )
    
    yes_stats = calc_stats(yes_wallets, config.min_insider_score)
    no_stats = calc_stats(no_wallets, config.min_insider_score)
    
    # Calculate asymmetry scores
    # Higher = more bullish (YES side has more insider activity)
    
    # Method 1: High-score wallet count ratio
    total_high = yes_stats.high_score_count + no_stats.high_score_count
    if total_high > 0:
        count_asymmetry = (yes_stats.high_score_count - no_stats.high_score_count) / total_high
    else:
        count_asymmetry = 0
    
    # Method 2: Average score difference
    score_asymmetry = (yes_stats.avg_score - no_stats.avg_score) / 100  # Normalize
    
    # Method 3: High-conviction volume ratio
    total_conviction = yes_stats.total_conviction + no_stats.total_conviction
    if total_conviction > 0:
        volume_asymmetry = (yes_stats.total_conviction - no_stats.total_conviction) / total_conviction
    else:
        volume_asymmetry = 0
    
    # Combined signal (weighted average)
    combined_signal = (
        count_asymmetry * 0.4 +    # Weight count of insiders
        score_asymmetry * 0.3 +     # Weight quality of insiders
        volume_asymmetry * 0.3      # Weight conviction amount
    )
    
    # Interpret signal
    if combined_signal > 0.3:
        interpretation = "STRONG_BULLISH"
        confidence = "HIGH"
    elif combined_signal > 0.1:
        interpretation = "BULLISH"
        confidence = "MODERATE"
    elif combined_signal < -0.3:
        interpretation = "STRONG_BEARISH"
        confidence = "HIGH"
    elif combined_signal < -0.1:
        interpretation = "BEARISH"
        confidence = "MODERATE"
    else:
        interpretation = "NEUTRAL"
        confidence = "LOW"
    
    # Top insiders for each direction
    yes_top = sorted(yes_wallets, key=lambda x: x["score"], reverse=True)[:5]
    no_top = sorted(no_wallets, key=lambda x: x["score"], reverse=True)[:5]
    
    return {
        "yes_stats": yes_stats.to_dict(),
        "no_stats": no_stats.to_dict(),
        "asymmetry": {
            "count_asymmetry": round(count_asymmetry, 3),
            "score_asymmetry": round(score_asymmetry, 3),
            "volume_asymmetry": round(volume_asymmetry, 3),
            "combined_signal": round(combined_signal, 3)
        },
        "interpretation": interpretation,
        "confidence": confidence,
        "top_yes_insiders": yes_top,
        "top_no_insiders": no_top
    }

# =============================================================================
# Data Loading
# =============================================================================

def process_trade(row, profiles: Dict[str, WalletProfile]):
    """Process single trade row."""
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
            return
        
        day_key = ts.strftime("%Y-%m-%d")
        
        for addr, is_buy in [(maker, maker_dir == 'BUY'), (taker, maker_dir != 'BUY')]:
            if addr not in profiles:
                profiles[addr] = WalletProfile(address=addr)
            
            p = profiles[addr]
            p.trade_count += 1
            p.trade_sizes.append(usd)
            
            if p.first_trade_ts is None or ts < p.first_trade_ts:
                p.first_trade_ts = ts
            if p.last_trade_ts is None or ts > p.last_trade_ts:
                p.last_trade_ts = ts
            
            p.volume_by_day[day_key] = p.volume_by_day.get(day_key, 0) + usd
            
            # Track by token
            if token_side == 'token1':  # YES
                if is_buy:
                    p.buy_vol_yes += usd
                    p.buy_shares_yes += shares
                else:
                    p.sell_vol_yes += usd
                    p.sell_shares_yes += shares
            else:  # NO
                if is_buy:
                    p.buy_vol_no += usd
                    p.buy_shares_no += shares
                else:
                    p.sell_vol_no += usd
                    p.sell_shares_no += shares
    except:
        pass


def load_trades_until(trades_file: str, cutoff_date: str) -> Dict[str, WalletProfile]:
    """Load trades up to cutoff date."""
    profiles = {}
    cutoff_dt = datetime.strptime(cutoff_date, "%Y-%m-%d")
    
    print(f"[INFO] Loading trades until {cutoff_date}...")
    
    for chunk in pd.read_csv(trades_file, chunksize=500000):
        chunk['_ts'] = pd.to_datetime(chunk['timestamp'])
        chunk = chunk[chunk['_ts'] <= cutoff_dt]
        
        for _, row in chunk.iterrows():
            process_trade(row, profiles)
        
        print(f"  Profiles: {len(profiles):,}")
    
    return profiles

# =============================================================================
# Main Analysis
# =============================================================================

def run_directional_analysis(config: DirectionalConfig):
    """
    Run directional asymmetry analysis on historical data.
    """
    print("=" * 70)
    print(f"DIRECTIONAL ASYMMETRY ANALYSIS: {config.market_name}")
    print("=" * 70)
    print(f"Simulation Date: {config.simulation_date}")
    print(f"Min Insider Score: {config.min_insider_score}")
    print()
    
    sim_date = datetime.strptime(config.simulation_date, "%Y-%m-%d")
    
    # Load data
    profiles = load_trades_until(config.trades_file, config.simulation_date)
    
    # Analyze
    result = analyze_directional_asymmetry(profiles, sim_date, config)
    
    # Print results
    print("\n" + "=" * 70)
    print("DIRECTIONAL ANALYSIS RESULTS")
    print("=" * 70)
    
    yes = result["yes_stats"]
    no = result["no_stats"]
    asym = result["asymmetry"]
    
    print(f"\n{'Direction':<12} {'Wallets':<10} {'High Score':<12} {'Avg Score':<12} {'Conviction':<15}")
    print("-" * 70)
    print(f"{'YES':<12} {yes['wallet_count']:<10} {yes['high_score_count']:<12} {yes['avg_score']:<12.1f} ${yes['total_conviction']:,.0f}")
    print(f"{'NO':<12} {no['wallet_count']:<10} {no['high_score_count']:<12} {no['avg_score']:<12.1f} ${no['total_conviction']:,.0f}")
    
    print(f"\n{'='*70}")
    print("ASYMMETRY METRICS")
    print(f"{'='*70}")
    print(f"Count Asymmetry:  {asym['count_asymmetry']:+.3f}  (+ = more YES insiders)")
    print(f"Score Asymmetry:  {asym['score_asymmetry']:+.3f}  (+ = higher YES scores)")
    print(f"Volume Asymmetry: {asym['volume_asymmetry']:+.3f}  (+ = more YES conviction)")
    print(f"\nCOMBINED SIGNAL:  {asym['combined_signal']:+.3f}")
    
    print(f"\n{'='*70}")
    print(f"INTERPRETATION: {result['interpretation']} (Confidence: {result['confidence']})")
    print(f"{'='*70}")
    
    # Validate against actual outcome
    print(f"\n[VALIDATION] Actual outcome: {config.winning_token.upper()} won")
    if config.winning_token == "token1":
        actual = "YES"
    else:
        actual = "NO"
    
    predicted = "YES" if asym['combined_signal'] > 0 else "NO"
    correct = predicted == actual
    
    print(f"Signal predicted: {predicted}")
    print(f"Prediction correct: {'[SUCCESS]' if correct else '[FAILED]'}")
    
    # Top insiders
    print(f"\n{'='*70}")
    print("TOP 5 YES-SIDE INSIDERS")
    print(f"{'='*70}")
    for i, w in enumerate(result["top_yes_insiders"][:5]):
        print(f"{i+1}. Score={w['score']} | ${w['conviction']:,.0f} | {w['address'][:16]}...")
    
    print(f"\n{'='*70}")
    print("TOP 5 NO-SIDE INSIDERS")
    print(f"{'='*70}")
    for i, w in enumerate(result["top_no_insiders"][:5]):
        print(f"{i+1}. Score={w['score']} | ${w['conviction']:,.0f} | {w['address'][:16]}...")
    
    # Save results
    output = {
        "config": {
            "market_name": config.market_name,
            "simulation_date": config.simulation_date,
            "actual_winner": config.winning_token
        },
        "results": result,
        "validation": {
            "actual": actual,
            "predicted": predicted,
            "correct": correct
        }
    }
    
    output_file = os.path.join(OUTPUT_DIR, "directional_asymmetry.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n\nResults saved to: {output_file}")
    return output


def run_multi_date_analysis():
    """
    Run analysis at multiple dates to see how signal evolves over time.
    """
    print("=" * 70)
    print("MULTI-DATE DIRECTIONAL ANALYSIS")
    print("=" * 70)
    print("Testing signal strength at different points before election...\n")
    
    dates = [
        "2024-10-01",  # 5 weeks before
        "2024-10-08",  # 4 weeks before  
        "2024-10-15",  # 3 weeks before
        "2024-10-22",  # 2 weeks before
        "2024-10-29",  # 1 week before
        "2024-11-04",  # 2 days before
    ]
    
    results = []
    
    for date in dates:
        config = DirectionalConfig(simulation_date=date)
        profiles = load_trades_until(config.trades_file, date)
        
        sim_date = datetime.strptime(date, "%Y-%m-%d")
        analysis = analyze_directional_asymmetry(profiles, sim_date, config)
        
        results.append({
            "date": date,
            "signal": analysis["asymmetry"]["combined_signal"],
            "interpretation": analysis["interpretation"],
            "yes_insiders": analysis["yes_stats"]["high_score_count"],
            "no_insiders": analysis["no_stats"]["high_score_count"]
        })
    
    # Print summary table
    print("\n" + "=" * 80)
    print("SIGNAL EVOLUTION OVER TIME")
    print("=" * 80)
    print(f"\n{'Date':<12} {'Signal':>10} {'Interpretation':<20} {'YES Insiders':>14} {'NO Insiders':>12}")
    print("-" * 80)
    
    for r in results:
        print(f"{r['date']:<12} {r['signal']:>+10.3f} {r['interpretation']:<20} {r['yes_insiders']:>14} {r['no_insiders']:>12}")
    
    # Save
    output_file = os.path.join(OUTPUT_DIR, "directional_evolution.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n\nResults saved to: {output_file}")
    
    # Analysis
    print("\n" + "=" * 70)
    print("SIGNAL ANALYSIS")
    print("=" * 70)
    
    avg_signal = statistics.mean([r["signal"] for r in results])
    print(f"Average Signal: {avg_signal:+.3f}")
    print(f"Consistent direction: {'YES' if avg_signal > 0 else 'NO'}")
    print(f"Actual winner: YES (Trump)")
    
    correct_predictions = sum(1 for r in results if r["signal"] > 0)
    print(f"Correct predictions: {correct_predictions}/{len(results)} ({correct_predictions/len(results)*100:.0f}%)")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--multi", action="store_true", help="Run multi-date analysis")
    parser.add_argument("--date", type=str, default="2024-10-15", help="Simulation date")
    args = parser.parse_args()
    
    if args.multi:
        run_multi_date_analysis()
    else:
        config = DirectionalConfig(simulation_date=args.date)
        run_directional_analysis(config)
