"""
Smart Money Detector V3 - With Entry Price Analysis

Key Insight:
- Smart money buys at FAVORABLE prices (below fair value)
- If a wallet is buying YES at 0.40 when it eventually settles at 1.0 -> high alpha

Entry Price Analysis:
1. Calculate avg entry price for each wallet
2. Compare to market price at that time
3. Lower entry = better value = smarter money

Combined Scoring:
- Conviction (how much)
- Timing (burst pattern)
- Entry Price (at what price level)
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
class SmartMoneyV3Config:
    market_id: int = 253591
    market_name: str = "Trump Win 2024"
    winning_token: str = "token1"
    
    simulation_date: str = "2024-10-15"
    trades_file: str = "output/trump_win_trades_oct_nov.csv"
    
    min_volume_usd: float = 10000
    min_conviction: float = 50000
    top_n: int = 50

# =============================================================================
# Wallet Profile with Entry Price
# =============================================================================

@dataclass 
class WalletProfile:
    address: str
    
    # YES side
    buy_vol_yes: float = 0.0
    sell_vol_yes: float = 0.0
    buy_shares_yes: float = 0.0
    sell_shares_yes: float = 0.0
    
    # NO side
    buy_vol_no: float = 0.0
    sell_vol_no: float = 0.0
    buy_shares_no: float = 0.0
    sell_shares_no: float = 0.0
    
    trade_count: int = 0
    trade_sizes: List[float] = field(default_factory=list)
    
    first_trade_ts: Optional[datetime] = None
    last_trade_ts: Optional[datetime] = None
    volume_by_day: Dict[str, float] = field(default_factory=dict)
    
    # NEW: Entry prices
    entry_prices_yes: List[float] = field(default_factory=list)  # Per-trade entry prices
    entry_prices_no: List[float] = field(default_factory=list)
    entry_amounts_yes: List[float] = field(default_factory=list)  # Corresponding amounts
    entry_amounts_no: List[float] = field(default_factory=list)
    
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
        return max(abs(self.net_yes_invested), abs(self.net_no_invested))
    
    @property
    def active_days(self) -> int:
        return len(self.volume_by_day)
    
    @property
    def avg_entry_price_yes(self) -> Optional[float]:
        """Volume-weighted average entry price for YES buys."""
        if not self.entry_amounts_yes or sum(self.entry_amounts_yes) == 0:
            return None
        
        weighted_sum = sum(p * a for p, a in zip(self.entry_prices_yes, self.entry_amounts_yes))
        return weighted_sum / sum(self.entry_amounts_yes)
    
    @property
    def avg_entry_price_no(self) -> Optional[float]:
        """Volume-weighted average entry price for NO buys."""
        if not self.entry_amounts_no or sum(self.entry_amounts_no) == 0:
            return None
        
        weighted_sum = sum(p * a for p, a in zip(self.entry_prices_no, self.entry_amounts_no))
        return weighted_sum / sum(self.entry_amounts_no)

# =============================================================================
# Smart Money Score V3 - With Entry Price
# =============================================================================

def calculate_smart_money_score_v3(profile: WalletProfile, sim_date: datetime) -> Tuple[int, dict]:
    """
    Smart money score with entry price analysis.
    
    Key insight:
    - Lower entry price for YES = better value (if YES wins)
    - Entry price < 0.50 = contrarian bet
    - Entry price < 0.30 = extreme contrarian (could be insider)
    """
    score = 0
    metrics = {}
    
    # 1. Conviction size
    conviction = profile.conviction_amount
    metrics["conviction_usd"] = round(conviction, 0)
    
    if conviction >= 500000:
        score += 40
        metrics["conviction_tier"] = "WHALE"
    elif conviction >= 100000:
        score += 30
        metrics["conviction_tier"] = "HIGH"
    elif conviction >= 50000:
        score += 15
        metrics["conviction_tier"] = "MODERATE"
    
    # 2. Time concentration
    if profile.active_days <= 2:
        score += 35
        metrics["time_signal"] = "BURST"
    elif profile.active_days <= 5:
        score += 20
        metrics["time_signal"] = "CONCENTRATED"
    
    # 3. Entry Price Analysis (NEW)
    direction = profile.direction
    
    if direction == "YES" and profile.avg_entry_price_yes is not None:
        entry = profile.avg_entry_price_yes
        metrics["entry_price"] = round(entry, 4)
        
        # Lower entry = better value = higher score
        # At sim_date 2024-10-15, YES price was around 0.50-0.55
        if entry < 0.35:
            score += 40
            metrics["entry_signal"] = "EXTREME_VALUE"
        elif entry < 0.45:
            score += 30
            metrics["entry_signal"] = "HIGH_VALUE"
        elif entry < 0.55:
            score += 15
            metrics["entry_signal"] = "FAIR_VALUE"
        else:
            metrics["entry_signal"] = "PREMIUM"
            # Bought at high price = less smart
        
        # Potential profit calculation (if YES wins at $1)
        potential_roi = (1.0 - entry) / entry
        metrics["potential_roi"] = round(potential_roi, 2)
    
    elif direction == "NO" and profile.avg_entry_price_no is not None:
        entry = profile.avg_entry_price_no
        metrics["entry_price"] = round(entry, 4)
        
        # For NO, they're betting against YES
        # Lower NO price = cheaper hedge/bet
        if entry < 0.45:
            score += 40
            metrics["entry_signal"] = "EXTREME_VALUE"
        elif entry < 0.55:
            score += 30
            metrics["entry_signal"] = "HIGH_VALUE"
        elif entry < 0.65:
            score += 15
            metrics["entry_signal"] = "FAIR_VALUE"
        else:
            metrics["entry_signal"] = "PREMIUM"
        
        potential_roi = (1.0 - entry) / entry
        metrics["potential_roi"] = round(potential_roi, 2)
    
    # 4. Trade efficiency
    if profile.trade_count > 0:
        efficiency = conviction / profile.trade_count
        if efficiency >= 10000:
            score += 10
            metrics["efficiency"] = "HIGH"
    
    metrics["direction"] = direction
    
    return score, metrics

# =============================================================================
# Signal Analysis
# =============================================================================

def analyze_smart_money_v3(profiles: Dict[str, WalletProfile], 
                           sim_date: datetime,
                           config: SmartMoneyV3Config) -> dict:
    """
    Analyze with entry price weighting.
    
    Key: Weight wallets that bought at FAVORABLE prices higher.
    """
    
    scored = []
    for addr, profile in profiles.items():
        if profile.total_volume < config.min_volume_usd:
            continue
        if profile.conviction_amount < config.min_conviction:
            continue
        
        score, metrics = calculate_smart_money_score_v3(profile, sim_date)
        
        scored.append({
            "address": addr,
            "score": score,
            "metrics": metrics,
            "direction": profile.direction,
            "conviction": profile.conviction_amount,
            "entry_price": metrics.get("entry_price"),
            "potential_roi": metrics.get("potential_roi")
        })
    
    # Sort by score * conviction (quality-weighted conviction)
    scored.sort(key=lambda x: x["score"] * x["conviction"], reverse=True)
    
    top_wallets = scored[:config.top_n]
    
    # Separate by direction
    yes_wallets = [w for w in top_wallets if w["direction"] == "YES"]
    no_wallets = [w for w in top_wallets if w["direction"] == "NO"]
    
    # Calculate weighted signals
    yes_weighted = sum(w["score"] * w["conviction"] for w in yes_wallets)
    no_weighted = sum(w["score"] * w["conviction"] for w in no_wallets)
    total_weighted = yes_weighted + no_weighted
    
    if total_weighted > 0:
        signal = (yes_weighted - no_weighted) / total_weighted
    else:
        signal = 0
    
    # Entry price comparison
    yes_entries = [w["entry_price"] for w in yes_wallets if w.get("entry_price")]
    no_entries = [w["entry_price"] for w in no_wallets if w.get("entry_price")]
    
    avg_yes_entry = statistics.mean(yes_entries) if yes_entries else None
    avg_no_entry = statistics.mean(no_entries) if no_entries else None
    
    # Interpretation
    if signal > 0.3:
        interpretation = "STRONG_BULLISH"
    elif signal > 0.1:
        interpretation = "BULLISH"
    elif signal < -0.3:
        interpretation = "STRONG_BEARISH"
    elif signal < -0.1:
        interpretation = "BEARISH"
    else:
        interpretation = "NEUTRAL"
    
    return {
        "summary": {
            "top_wallets": len(top_wallets),
            "yes_wallets": len(yes_wallets),
            "no_wallets": len(no_wallets),
            "avg_yes_entry": round(avg_yes_entry, 4) if avg_yes_entry else None,
            "avg_no_entry": round(avg_no_entry, 4) if avg_no_entry else None
        },
        "signal": round(signal, 3),
        "interpretation": interpretation,
        "top_yes": sorted(yes_wallets, key=lambda x: x["conviction"], reverse=True)[:10],
        "top_no": sorted(no_wallets, key=lambda x: x["conviction"], reverse=True)[:10]
    }

# =============================================================================
# Data Loading - With Price Tracking
# =============================================================================

def process_trade(row, profiles: Dict[str, WalletProfile]):
    try:
        maker = str(row['maker']).lower()
        taker = str(row['taker']).lower()
        usd = float(row.get('usd_amount', 0) or 0)
        shares = float(row.get('token_amount', 0) or 0)
        token_side = str(row.get('nonusdc_side', ''))
        maker_dir = str(row.get('maker_direction', '')).upper()
        
        # Calculate per-share price
        if shares > 0 and usd > 0:
            price_per_share = usd / shares
        else:
            price_per_share = None
        
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
            
            if token_side == 'token1':  # YES
                if is_buy:
                    p.buy_vol_yes += usd
                    p.buy_shares_yes += shares
                    # Track entry price
                    if price_per_share is not None:
                        p.entry_prices_yes.append(price_per_share)
                        p.entry_amounts_yes.append(usd)
                else:
                    p.sell_vol_yes += usd
                    p.sell_shares_yes += shares
            else:  # NO
                if is_buy:
                    p.buy_vol_no += usd
                    p.buy_shares_no += shares
                    if price_per_share is not None:
                        p.entry_prices_no.append(price_per_share)
                        p.entry_amounts_no.append(usd)
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
# Main
# =============================================================================

def run_analysis(config: SmartMoneyV3Config):
    print("=" * 70)
    print(f"SMART MONEY V3 (WITH ENTRY PRICE): {config.market_name}")
    print("=" * 70)
    print(f"Simulation Date: {config.simulation_date}")
    print()
    
    sim_date = datetime.strptime(config.simulation_date, "%Y-%m-%d")
    
    profiles = load_trades_until(config.trades_file, config.simulation_date)
    
    result = analyze_smart_money_v3(profiles, sim_date, config)
    
    # Print results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    s = result["summary"]
    print(f"\nTop {config.top_n} Smart Money Wallets:")
    print(f"  YES bettors: {s['yes_wallets']}")
    print(f"  NO  bettors: {s['no_wallets']}")
    print(f"\nAverage Entry Prices:")
    print(f"  YES buyers avg entry: {s['avg_yes_entry']}")
    print(f"  NO  buyers avg entry: {s['avg_no_entry']}")
    
    print(f"\nSIGNAL: {result['signal']:+.3f}")
    print(f"INTERPRETATION: {result['interpretation']}")
    
    # Validate
    print(f"\n[VALIDATION]")
    actual = "YES" if config.winning_token == "token1" else "NO"
    predicted = "YES" if result["signal"] > 0 else "NO"
    print(f"Actual: {actual}")
    print(f"Predicted: {predicted}")
    print(f"Correct: {'[SUCCESS]' if actual == predicted else '[WRONG]'}")
    
    # Top YES whales with entry prices
    print(f"\n{'='*70}")
    print("TOP 5 YES WHALES (with entry price)")
    print(f"{'='*70}")
    for i, w in enumerate(result["top_yes"][:5]):
        entry = w.get("entry_price", "?")
        roi = w.get("potential_roi", "?")
        signal = w.get("metrics", {}).get("entry_signal", "?")
        print(f"{i+1}. ${w['conviction']:,.0f} | Entry=${entry} | Potential ROI={roi} | {signal}")
        print(f"   {w['address'][:20]}...")
    
    print(f"\n{'='*70}")
    print("TOP 5 NO WHALES (with entry price)")
    print(f"{'='*70}")
    for i, w in enumerate(result["top_no"][:5]):
        entry = w.get("entry_price", "?")
        roi = w.get("potential_roi", "?")
        signal = w.get("metrics", {}).get("entry_signal", "?")
        print(f"{i+1}. ${w['conviction']:,.0f} | Entry=${entry} | Potential ROI={roi} | {signal}")
        print(f"   {w['address'][:20]}...")
    
    # Save
    output = {
        "config": {
            "market_name": config.market_name,
            "simulation_date": config.simulation_date
        },
        "results": result,
        "validation": {
            "actual": actual,
            "predicted": predicted,
            "correct": actual == predicted
        }
    }
    
    output_file = os.path.join(OUTPUT_DIR, "smart_money_v3.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n\nResults saved to: {output_file}")
    return output


def run_multi_date():
    """Run at multiple dates."""
    print("=" * 70)
    print("SMART MONEY V3 - MULTI-DATE WITH ENTRY PRICE")
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
        config = SmartMoneyV3Config(simulation_date=date)
        profiles = load_trades_until(config.trades_file, date)
        
        sim_date = datetime.strptime(date, "%Y-%m-%d")
        analysis = analyze_smart_money_v3(profiles, sim_date, config)
        
        results.append({
            "date": date,
            "signal": analysis["signal"],
            "interpretation": analysis["interpretation"],
            "yes_wallets": analysis["summary"]["yes_wallets"],
            "no_wallets": analysis["summary"]["no_wallets"],
            "avg_yes_entry": analysis["summary"]["avg_yes_entry"],
            "avg_no_entry": analysis["summary"]["avg_no_entry"],
            "correct": analysis["signal"] > 0
        })
    
    # Print table
    print("\n" + "=" * 100)
    print("SIGNAL EVOLUTION WITH ENTRY PRICES")
    print("=" * 100)
    print(f"\n{'Date':<12} {'Signal':>10} {'Interp':<18} {'YES Entry':>12} {'NO Entry':>12} {'Correct':>10}")
    print("-" * 100)
    
    for r in results:
        ye = f"${r['avg_yes_entry']:.3f}" if r['avg_yes_entry'] else "N/A"
        ne = f"${r['avg_no_entry']:.3f}" if r['avg_no_entry'] else "N/A"
        check = "[OK]" if r["correct"] else "[WRONG]"
        print(f"{r['date']:<12} {r['signal']:>+10.3f} {r['interpretation']:<18} {ye:>12} {ne:>12} {check:>10}")
    
    # Summary
    correct = sum(1 for r in results if r["correct"] and r["signal"] != 0)
    total = sum(1 for r in results if r["signal"] != 0)
    
    print(f"\nCorrect predictions: {correct}/{total} ({correct/total*100:.0f}%)")
    
    # Save
    output_file = os.path.join(OUTPUT_DIR, "smart_money_v3_evolution.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--multi", action="store_true")
    parser.add_argument("--date", type=str, default="2024-10-15")
    args = parser.parse_args()
    
    if args.multi:
        run_multi_date()
    else:
        config = SmartMoneyV3Config(simulation_date=args.date)
        run_analysis(config)
