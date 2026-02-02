"""
Smart Money Detector V2 - Conviction-Weighted Analysis

Key Insight from V1:
- Just counting insider-like wallets by direction gives WRONG signal
- There were MORE bearish insider-like wallets, but they LOST money

New Approach:
1. Focus on CONVICTION AMOUNT, not just count
2. Weight by trade size (bigger bets = more conviction)
3. Consider: True insiders make LARGER bets with HIGHER concentration

Hypothesis:
- Retail "wannabe insiders" make many small burst trades
- Real insiders make FEWER but LARGER concentrated bets
- Volume-weighted signal should be more accurate
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
class SmartMoneyConfig:
    market_id: int = 253591
    market_name: str = "Trump Win 2024"
    winning_token: str = "token1"
    
    simulation_date: str = "2024-10-15"
    trades_file: str = "output/trump_win_trades_oct_nov.csv"
    
    # Thresholds
    min_volume_usd: float = 10000  # Higher threshold for "smart money"
    min_trades: int = 3
    min_conviction: float = 50000  # Min conviction amount to be considered
    
    # Top N thresholds
    top_n: int = 50  # Focus on top N by conviction

# =============================================================================
# Wallet Profile
# =============================================================================

@dataclass 
class WalletProfile:
    address: str
    
    buy_vol_yes: float = 0.0
    sell_vol_yes: float = 0.0
    buy_shares_yes: float = 0.0
    sell_shares_yes: float = 0.0
    
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
        yes_signal = self.net_yes_invested
        no_signal = self.net_no_invested
        
        if yes_signal > abs(no_signal):
            return "YES"
        elif no_signal > abs(yes_signal):
            return "NO"
        elif yes_signal < 0:
            return "NO"
        elif no_signal < 0:
            return "YES"
        return "NEUTRAL"
    
    @property
    def conviction_amount(self) -> float:
        """Net USD committed in dominant direction."""
        return max(abs(self.net_yes_invested), abs(self.net_no_invested))
    
    @property
    def active_days(self) -> int:
        return len(self.volume_by_day)
    
    @property
    def avg_trade_size(self) -> float:
        return statistics.mean(self.trade_sizes) if self.trade_sizes else 0
    
    @property
    def max_trade_size(self) -> float:
        return max(self.trade_sizes) if self.trade_sizes else 0

# =============================================================================
# Smart Money Score - Focus on HIGH CONVICTION
# =============================================================================

def calculate_smart_money_score(profile: WalletProfile, sim_date: datetime) -> Tuple[int, dict]:
    """
    Calculate smart money score - emphasizes:
    1. HIGH conviction (large bets)
    2. CONCENTRATED timing (burst)
    3. LARGE individual trades
    """
    score = 0
    metrics = {}
    
    # 1. Conviction size (most important)
    conviction = profile.conviction_amount
    metrics["conviction_usd"] = round(conviction, 0)
    
    if conviction >= 500000:
        score += 50
        metrics["conviction_tier"] = "WHALE"
    elif conviction >= 100000:
        score += 35
        metrics["conviction_tier"] = "HIGH"
    elif conviction >= 50000:
        score += 20
        metrics["conviction_tier"] = "MODERATE"
    elif conviction >= 10000:
        score += 10
        metrics["conviction_tier"] = "LOW"
    
    # 2. Time concentration (short window = signal)
    if profile.active_days <= 2:
        score += 40
        metrics["time_signal"] = "EXTREME_BURST"
    elif profile.active_days <= 5:
        score += 25
        metrics["time_signal"] = "BURST"
    elif profile.active_days <= 10:
        score += 10
        metrics["time_signal"] = "CONCENTRATED"
    
    # 3. Trade size quality (big trades = conviction)
    avg_size = profile.avg_trade_size
    max_size = profile.max_trade_size
    
    metrics["avg_trade_size"] = round(avg_size, 0)
    metrics["max_trade_size"] = round(max_size, 0)
    
    if max_size >= 50000:
        score += 30
        metrics["size_signal"] = "WHALE_TRADE"
    elif max_size >= 20000:
        score += 20
        metrics["size_signal"] = "LARGE_TRADE"
    elif max_size >= 10000:
        score += 10
        metrics["size_signal"] = "MODERATE_TRADE"
    
    # 4. Efficiency (conviction per trade)
    if profile.trade_count > 0:
        efficiency = conviction / profile.trade_count
        metrics["efficiency"] = round(efficiency, 0)
        
        if efficiency >= 10000:
            score += 15
            metrics["efficiency_signal"] = "HIGH_EFFICIENCY"
        elif efficiency >= 5000:
            score += 8
            metrics["efficiency_signal"] = "MODERATE_EFFICIENCY"
    
    metrics["direction"] = profile.direction
    
    return score, metrics


def calculate_pnl(profile: WalletProfile, winning_token: str) -> float:
    """Calculate P&L for a profile."""
    if winning_token == "token1":  # YES wins
        pnl = (profile.net_yes_shares - profile.net_yes_invested) - profile.net_no_invested
    else:  # NO wins  
        pnl = (profile.net_no_shares - profile.net_no_invested) - profile.net_yes_invested
    return pnl

# =============================================================================
# Smart Money Directional Signal
# =============================================================================

def analyze_smart_money_signal(profiles: Dict[str, WalletProfile], 
                                sim_date: datetime,
                                config: SmartMoneyConfig) -> dict:
    """
    Analyze smart money by focusing on TOP conviction wallets only.
    
    Key difference from V1:
    - Only look at top N by conviction
    - Weight by conviction amount, not count
    """
    
    # Filter and score
    scored = []
    for addr, profile in profiles.items():
        if profile.total_volume < config.min_volume_usd:
            continue
        if profile.conviction_amount < config.min_conviction:
            continue
        
        score, metrics = calculate_smart_money_score(profile, sim_date)
        
        scored.append({
            "address": addr,
            "score": score,
            "metrics": metrics,
            "direction": profile.direction,
            "conviction": profile.conviction_amount,
            "net_yes": profile.net_yes_invested,
            "net_no": profile.net_no_invested
        })
    
    # Sort by conviction (focus on biggest players)
    scored.sort(key=lambda x: x["conviction"], reverse=True)
    
    # Take top N
    top_wallets = scored[:config.top_n]
    
    # Calculate conviction-weighted signal
    yes_conviction = sum(w["conviction"] for w in top_wallets if w["direction"] == "YES")
    no_conviction = sum(w["conviction"] for w in top_wallets if w["direction"] == "NO")
    total_conviction = yes_conviction + no_conviction
    
    # Also calculate score-weighted conviction
    yes_score_weighted = sum(w["conviction"] * w["score"] for w in top_wallets if w["direction"] == "YES")
    no_score_weighted = sum(w["conviction"] * w["score"] for w in top_wallets if w["direction"] == "NO")
    total_score_weighted = yes_score_weighted + no_score_weighted
    
    # Signals
    if total_conviction > 0:
        conviction_signal = (yes_conviction - no_conviction) / total_conviction
    else:
        conviction_signal = 0
    
    if total_score_weighted > 0:
        quality_signal = (yes_score_weighted - no_score_weighted) / total_score_weighted
    else:
        quality_signal = 0
    
    # Combined (weight quality more)
    combined = conviction_signal * 0.4 + quality_signal * 0.6
    
    # Interpretation
    if combined > 0.3:
        interpretation = "STRONG_BULLISH"
    elif combined > 0.1:
        interpretation = "BULLISH"
    elif combined < -0.3:
        interpretation = "STRONG_BEARISH"
    elif combined < -0.1:
        interpretation = "BEARISH"
    else:
        interpretation = "NEUTRAL"
    
    # Top wallets by direction
    yes_wallets = [w for w in top_wallets if w["direction"] == "YES"]
    no_wallets = [w for w in top_wallets if w["direction"] == "NO"]
    
    yes_wallets.sort(key=lambda x: x["conviction"], reverse=True)
    no_wallets.sort(key=lambda x: x["conviction"], reverse=True)
    
    return {
        "summary": {
            "total_top_wallets": len(top_wallets),
            "yes_wallets": len(yes_wallets),
            "no_wallets": len(no_wallets),
            "yes_conviction": round(yes_conviction, 0),
            "no_conviction": round(no_conviction, 0)
        },
        "signals": {
            "conviction_signal": round(conviction_signal, 3),
            "quality_signal": round(quality_signal, 3),
            "combined_signal": round(combined, 3)
        },
        "interpretation": interpretation,
        "top_yes": yes_wallets[:10],
        "top_no": no_wallets[:10]
    }

# =============================================================================
# Data Loading
# =============================================================================

def process_trade(row, profiles: Dict[str, WalletProfile]):
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
            
            if token_side == 'token1':
                if is_buy:
                    p.buy_vol_yes += usd
                    p.buy_shares_yes += shares
                else:
                    p.sell_vol_yes += usd
                    p.sell_shares_yes += shares
            else:
                if is_buy:
                    p.buy_vol_no += usd
                    p.buy_shares_no += shares
                else:
                    p.sell_vol_no += usd
                    p.sell_shares_no += shares
    except:
        pass


def load_trades_until(trades_file: str, cutoff_date: str) -> Dict[str, WalletProfile]:
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


def load_all_trades(trades_file: str) -> Dict[str, WalletProfile]:
    profiles = {}
    
    print(f"[INFO] Loading ALL trades...")
    
    for chunk in pd.read_csv(trades_file, chunksize=500000):
        for _, row in chunk.iterrows():
            process_trade(row, profiles)
        print(f"  Profiles: {len(profiles):,}")
    
    return profiles

# =============================================================================
# Main Analysis
# =============================================================================

def run_smart_money_analysis(config: SmartMoneyConfig):
    """Run smart money analysis with conviction weighting."""
    print("=" * 70)
    print(f"SMART MONEY DETECTOR V2: {config.market_name}")
    print("=" * 70)
    print(f"Simulation Date: {config.simulation_date}")
    print(f"Min Conviction: ${config.min_conviction:,}")
    print(f"Top N Wallets: {config.top_n}")
    print()
    
    sim_date = datetime.strptime(config.simulation_date, "%Y-%m-%d")
    
    # Load historical data
    profiles = load_trades_until(config.trades_file, config.simulation_date)
    
    # Analyze
    result = analyze_smart_money_signal(profiles, sim_date, config)
    
    # Print results
    print("\n" + "=" * 70)
    print("SMART MONEY SIGNAL")
    print("=" * 70)
    
    s = result["summary"]
    print(f"\nTop {config.top_n} Wallets by Conviction:")
    print(f"  YES bettors: {s['yes_wallets']} (${s['yes_conviction']:,.0f})")
    print(f"  NO  bettors: {s['no_wallets']} (${s['no_conviction']:,.0f})")
    
    sig = result["signals"]
    print(f"\nSignals:")
    print(f"  Conviction Signal:  {sig['conviction_signal']:+.3f}")
    print(f"  Quality Signal:     {sig['quality_signal']:+.3f}")
    print(f"  COMBINED:           {sig['combined_signal']:+.3f}")
    
    print(f"\n{'='*70}")
    print(f"INTERPRETATION: {result['interpretation']}")
    print(f"{'='*70}")
    
    # Validate
    print(f"\n[VALIDATION]")
    actual = "YES" if config.winning_token == "token1" else "NO"
    predicted = "YES" if sig["combined_signal"] > 0 else "NO"
    correct = actual == predicted
    
    print(f"Actual Winner: {actual}")
    print(f"Signal Says: {predicted}")
    print(f"Correct: {'[SUCCESS]' if correct else '[FAILED]'}")
    
    # Top wallets
    print(f"\n{'='*70}")
    print("TOP 5 YES-SIDE WHALES")
    print(f"{'='*70}")
    for i, w in enumerate(result["top_yes"][:5]):
        tier = w["metrics"].get("conviction_tier", "?")
        print(f"{i+1}. ${w['conviction']:,.0f} | Score={w['score']} | {tier} | {w['address'][:16]}...")
    
    print(f"\n{'='*70}")
    print("TOP 5 NO-SIDE WHALES")
    print(f"{'='*70}")
    for i, w in enumerate(result["top_no"][:5]):
        tier = w["metrics"].get("conviction_tier", "?")
        print(f"{i+1}. ${w['conviction']:,.0f} | Score={w['score']} | {tier} | {w['address'][:16]}...")
    
    # Save
    output = {
        "config": {
            "market_name": config.market_name,
            "simulation_date": config.simulation_date,
            "min_conviction": config.min_conviction,
            "top_n": config.top_n
        },
        "results": result,
        "validation": {
            "actual": actual,
            "predicted": predicted,
            "correct": correct
        }
    }
    
    output_file = os.path.join(OUTPUT_DIR, "smart_money_signal.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n\nResults saved to: {output_file}")
    return output


def run_multi_date():
    """Run at multiple dates to test signal consistency."""
    print("=" * 70)
    print("SMART MONEY SIGNAL - MULTI-DATE ANALYSIS")
    print("=" * 70)
    
    dates = [
        "2024-10-01",
        "2024-10-08", 
        "2024-10-15",
        "2024-10-22",
        "2024-10-29",
        "2024-11-04",
    ]
    
    results = []
    
    for date in dates:
        config = SmartMoneyConfig(simulation_date=date)
        profiles = load_trades_until(config.trades_file, date)
        
        sim_date = datetime.strptime(date, "%Y-%m-%d")
        analysis = analyze_smart_money_signal(profiles, sim_date, config)
        
        sig = analysis["signals"]
        
        results.append({
            "date": date,
            "combined_signal": sig["combined_signal"],
            "interpretation": analysis["interpretation"],
            "yes_conviction": analysis["summary"]["yes_conviction"],
            "no_conviction": analysis["summary"]["no_conviction"],
            "correct": sig["combined_signal"] > 0  # YES won
        })
    
    # Print table
    print("\n" + "=" * 90)
    print("SIGNAL EVOLUTION")
    print("=" * 90)
    print(f"\n{'Date':<12} {'Signal':>10} {'Interpretation':<18} {'YES Conv':>15} {'NO Conv':>15} {'Correct':>10}")
    print("-" * 90)
    
    for r in results:
        check = "[OK]" if r["correct"] else "[WRONG]"
        print(f"{r['date']:<12} {r['combined_signal']:>+10.3f} {r['interpretation']:<18} "
              f"${r['yes_conviction']:>13,.0f} ${r['no_conviction']:>13,.0f} {check:>10}")
    
    # Summary
    correct_count = sum(1 for r in results if r["correct"])
    print(f"\nCorrect predictions: {correct_count}/{len(results)} ({correct_count/len(results)*100:.0f}%)")
    
    avg_signal = statistics.mean([r["combined_signal"] for r in results])
    print(f"Average signal: {avg_signal:+.3f}")
    
    # Save
    output_file = os.path.join(OUTPUT_DIR, "smart_money_evolution.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--multi", action="store_true")
    parser.add_argument("--date", type=str, default="2024-10-15")
    parser.add_argument("--top", type=int, default=50)
    parser.add_argument("--conviction", type=float, default=50000)
    args = parser.parse_args()
    
    if args.multi:
        run_multi_date()
    else:
        config = SmartMoneyConfig(
            simulation_date=args.date,
            top_n=args.top,
            min_conviction=args.conviction
        )
        run_smart_money_analysis(config)
