"""
Historical Backtest V2 - With Directional Analysis

Key Insight from V1:
- High insider scores were assigned to BURST_TRADERS who bet AGAINST Trump
- These wallets LOST money because Trump won
- We need to add directional context to insider detection

New Approach:
1. Keep anomaly detection metrics
2. Add DIRECTIONAL ANALYSIS - filter for wallets betting on correct outcome
3. For historical backtest, we can test: "If we knew the direction, would our algo work?"

Two modes:
- Mode A: Pure detection (no hindsight) - can we identify "smart money"?
- Mode B: With direction filter - can we identify insiders betting correctly?
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
class BacktestConfig:
    market_id: int = 253591
    market_name: str = "Trump Win 2024"
    winning_token: str = "token1"  # YES = Trump wins
    
    simulation_date: str = "2024-10-15"
    resolution_date: str = "2024-11-06"
    trades_file: str = "output/trump_win_trades_oct_nov.csv"
    
    min_volume_usd: float = 5000
    min_trades: int = 3
    
    # Direction filter: only analyze wallets betting in this direction
    # None = analyze all, "token1" = only YES bettors, "token0" = only NO bettors
    direction_filter: Optional[str] = None

# =============================================================================
# Wallet Profile
# =============================================================================

@dataclass 
class WalletMarketProfile:
    address: str
    
    buy_volume_token1_usd: float = 0.0
    sell_volume_token1_usd: float = 0.0
    buy_volume_token0_usd: float = 0.0
    sell_volume_token0_usd: float = 0.0
    
    buy_shares_token1: float = 0.0
    sell_shares_token1: float = 0.0
    buy_shares_token0: float = 0.0
    sell_shares_token0: float = 0.0
    
    trade_count: int = 0
    trade_sizes: List[float] = field(default_factory=list)
    
    first_trade_ts: Optional[datetime] = None
    last_trade_ts: Optional[datetime] = None
    trades_by_day: Dict[str, int] = field(default_factory=dict)
    volume_by_day: Dict[str, float] = field(default_factory=dict)
    
    @property
    def total_volume_usd(self) -> float:
        return (self.buy_volume_token1_usd + self.sell_volume_token1_usd + 
                self.buy_volume_token0_usd + self.sell_volume_token0_usd)
    
    @property
    def net_token1_shares(self) -> float:
        return self.buy_shares_token1 - self.sell_shares_token1
    
    @property
    def net_token0_shares(self) -> float:
        return self.buy_shares_token0 - self.sell_shares_token0
    
    @property
    def net_token1_invested(self) -> float:
        return self.buy_volume_token1_usd - self.sell_volume_token1_usd
    
    @property
    def net_token0_invested(self) -> float:
        return self.buy_volume_token0_usd - self.sell_volume_token0_usd
    
    @property
    def active_days(self) -> int:
        return len(self.trades_by_day)
    
    @property
    def is_net_long_token1(self) -> bool:
        """Is this wallet net long YES?"""
        return self.net_token1_shares > 0
    
    @property
    def is_net_long_token0(self) -> bool:
        """Is this wallet net long NO?"""
        return self.net_token0_shares > 0
    
    @property
    def dominant_direction(self) -> str:
        """Which token is this wallet primarily betting on?"""
        if self.net_token1_invested > 0 and abs(self.net_token1_invested) > abs(self.net_token0_invested):
            return "token1"  # Betting on YES
        elif self.net_token0_invested > 0 and abs(self.net_token0_invested) > abs(self.net_token1_invested):
            return "token0"  # Betting on NO
        elif self.net_token1_invested < 0:
            return "token0"  # Selling YES = betting on NO
        else:
            return "token1"  # Selling NO = betting on YES

# =============================================================================
# Insider Metrics (refined)
# =============================================================================

def calculate_concentration_score(profile: WalletMarketProfile) -> Tuple[float, dict]:
    """Time concentration: is trading clustered in short window?"""
    if not profile.volume_by_day:
        return 0, {}
    
    volumes = list(profile.volume_by_day.values())
    
    if len(volumes) <= 2:
        return 50, {"signal": "SHORT_WINDOW", "active_days": len(volumes)}
    
    max_vol = max(volumes)
    total = sum(volumes)
    concentration = max_vol / total if total > 0 else 0
    
    score = 0
    details = {"concentration_ratio": round(concentration, 3), "active_days": len(volumes)}
    
    if concentration > 0.8:
        score = 40
        details["signal"] = "EXTREME"
    elif concentration > 0.6:
        score = 25
        details["signal"] = "HIGH"
    elif concentration > 0.4:
        score = 10
        details["signal"] = "MODERATE"
    
    return score, details


def calculate_size_anomaly_score(profile: WalletMarketProfile) -> Tuple[float, dict]:
    """Trade size anomaly: are there unusually large trades?"""
    if len(profile.trade_sizes) < 3:
        return 0, {}
    
    sizes = profile.trade_sizes
    max_size = max(sizes)
    median_size = statistics.median(sizes)
    
    details = {"max_trade": round(max_size, 0), "median_trade": round(median_size, 0)}
    
    if median_size > 0:
        ratio = max_size / median_size
        details["size_ratio"] = round(ratio, 1)
        
        if ratio > 50:
            return 30, {**details, "signal": "EXTREME"}
        elif ratio > 20:
            return 20, {**details, "signal": "HIGH"}
        elif ratio > 10:
            return 10, {**details, "signal": "MODERATE"}
    
    return 0, details


def calculate_timing_score(profile: WalletMarketProfile, sim_date: datetime) -> Tuple[float, dict]:
    """Timing analysis: burst pattern detection"""
    if not profile.first_trade_ts or not profile.last_trade_ts:
        return 0, {}
    
    trading_span = (profile.last_trade_ts - profile.first_trade_ts).days
    days_since = (sim_date - profile.last_trade_ts).days
    
    details = {
        "trading_span_days": trading_span,
        "days_since_last_trade": days_since,
        "active_days": profile.active_days
    }
    
    score = 0
    
    # Burst pattern bonus
    if trading_span <= 3 and profile.total_volume_usd > 10000:
        score += 30
        details["pattern"] = "BURST"
    elif trading_span <= 7:
        score += 15
        details["pattern"] = "SHORT_WINDOW"
    
    # Recency bonus
    if days_since <= 3:
        score += 10
        details["recency"] = "VERY_RECENT"
    
    return score, details


def calculate_conviction_score(profile: WalletMarketProfile) -> Tuple[float, dict]:
    """
    Conviction score: how one-directional is the trading?
    High conviction = insider with specific info
    """
    total_buy = profile.buy_volume_token1_usd + profile.buy_volume_token0_usd
    total_sell = profile.sell_volume_token1_usd + profile.sell_volume_token0_usd
    total = total_buy + total_sell
    
    if total == 0:
        return 0, {}
    
    # Directional ratio: 1.0 = all one direction
    directional = abs(total_buy - total_sell) / total
    
    # Token1 vs Token0 bias
    net_token1 = profile.net_token1_invested
    net_token0 = profile.net_token0_invested
    total_net = abs(net_token1) + abs(net_token0)
    
    if total_net > 0:
        token1_bias = net_token1 / total_net  # +1 = all YES, -1 = all NO
    else:
        token1_bias = 0
    
    details = {
        "directional_ratio": round(directional, 3),
        "token1_bias": round(token1_bias, 3),
        "dominant_direction": profile.dominant_direction,
        "net_token1_invested": round(profile.net_token1_invested, 0),
        "net_token0_invested": round(profile.net_token0_invested, 0)
    }
    
    score = 0
    if directional > 0.9:
        score += 25
        details["signal"] = "EXTREME_CONVICTION"
    elif directional > 0.7:
        score += 15
        details["signal"] = "HIGH_CONVICTION"
    elif directional > 0.5:
        score += 5
        details["signal"] = "MODERATE_CONVICTION"
    
    return score, details


def calculate_insider_score_v2(profile: WalletMarketProfile, sim_date: datetime) -> Tuple[int, dict]:
    """Combined insider score with all metrics."""
    total_score = 0
    metrics = {}
    
    # Basic info
    metrics["summary"] = {
        "address": profile.address[:12] + "...",
        "total_volume": round(profile.total_volume_usd, 0),
        "trades": profile.trade_count,
        "active_days": profile.active_days,
        "dominant_direction": profile.dominant_direction
    }
    
    # Metrics
    s1, d1 = calculate_concentration_score(profile)
    total_score += s1
    if d1: metrics["concentration"] = d1
    
    s2, d2 = calculate_size_anomaly_score(profile)
    total_score += s2
    if d2: metrics["size_anomaly"] = d2
    
    s3, d3 = calculate_timing_score(profile, sim_date)
    total_score += s3
    if d3: metrics["timing"] = d3
    
    s4, d4 = calculate_conviction_score(profile)
    total_score += s4
    if d4: metrics["conviction"] = d4
    
    # Volume bonus
    vol = profile.total_volume_usd
    if vol > 100000:
        total_score += 20
    elif vol > 50000:
        total_score += 10
    
    return total_score, metrics


def calculate_pnl(profile: WalletMarketProfile, winning_token: str) -> dict:
    """Calculate P&L at resolution."""
    if winning_token == "token1":
        # YES wins - shares worth $1
        pnl_from_yes = profile.net_token1_shares - profile.net_token1_invested
        pnl_from_no = -profile.net_token0_invested  # NO shares worth $0
        final_pnl = pnl_from_yes + pnl_from_no
    else:
        pnl_from_no = profile.net_token0_shares - profile.net_token0_invested
        pnl_from_yes = -profile.net_token1_invested
        final_pnl = pnl_from_yes + pnl_from_no
    
    total_invested = abs(profile.net_token1_invested) + abs(profile.net_token0_invested)
    roi = final_pnl / total_invested if total_invested > 0 else 0
    
    return {
        "pnl_usd": round(final_pnl, 2),
        "total_invested": round(total_invested, 2),
        "roi": round(roi, 4),
        "correct_side": (profile.net_token1_shares > 0) if winning_token == "token1" 
                        else (profile.net_token0_shares > 0)
    }

# =============================================================================
# Data Loading
# =============================================================================

def process_trade(row, profiles: Dict[str, WalletMarketProfile]):
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
                profiles[addr] = WalletMarketProfile(address=addr)
            
            p = profiles[addr]
            p.trade_count += 1
            p.trade_sizes.append(usd)
            
            if p.first_trade_ts is None or ts < p.first_trade_ts:
                p.first_trade_ts = ts
            if p.last_trade_ts is None or ts > p.last_trade_ts:
                p.last_trade_ts = ts
            
            p.trades_by_day[day_key] = p.trades_by_day.get(day_key, 0) + 1
            p.volume_by_day[day_key] = p.volume_by_day.get(day_key, 0) + usd
            
            if token_side == 'token1':
                if is_buy:
                    p.buy_volume_token1_usd += usd
                    p.buy_shares_token1 += shares
                else:
                    p.sell_volume_token1_usd += usd
                    p.sell_shares_token1 += shares
            else:
                if is_buy:
                    p.buy_volume_token0_usd += usd
                    p.buy_shares_token0 += shares
                else:
                    p.sell_volume_token0_usd += usd
                    p.sell_shares_token0 += shares
    except:
        pass


def load_trades_until_date(trades_file: str, cutoff_date: str):
    """Load trades up to cutoff date."""
    profiles: Dict[str, WalletMarketProfile] = {}
    cutoff_dt = datetime.strptime(cutoff_date, "%Y-%m-%d")
    
    print(f"[INFO] Loading trades until {cutoff_date}...")
    
    for chunk in pd.read_csv(trades_file, chunksize=500000):
        chunk['_ts'] = pd.to_datetime(chunk['timestamp'])
        chunk = chunk[chunk['_ts'] <= cutoff_dt]
        
        for _, row in chunk.iterrows():
            process_trade(row, profiles)
        
        print(f"  Profiles: {len(profiles):,}")
    
    return profiles


def load_all_trades(trades_file: str):
    """Load all trades for P&L."""
    profiles: Dict[str, WalletMarketProfile] = {}
    
    print(f"[INFO] Loading ALL trades...")
    
    for chunk in pd.read_csv(trades_file, chunksize=500000):
        for _, row in chunk.iterrows():
            process_trade(row, profiles)
        print(f"  Profiles: {len(profiles):,}")
    
    return profiles

# =============================================================================
# Main Backtest with Direction Analysis
# =============================================================================

def run_backtest_v2(config: BacktestConfig):
    """
    Run backtest with optional direction filter.
    """
    print("=" * 70)
    print(f"HISTORICAL BACKTEST V2: {config.market_name}")
    print("=" * 70)
    print(f"Simulation Date: {config.simulation_date}")
    print(f"Direction Filter: {config.direction_filter or 'None (all wallets)'}")
    print()
    
    sim_dt = datetime.strptime(config.simulation_date, "%Y-%m-%d")
    
    # Load historical data
    historical = load_trades_until_date(config.trades_file, config.simulation_date)
    
    # Calculate scores
    print(f"\n[SCORING] Calculating insider scores...")
    results = []
    
    for addr, profile in historical.items():
        if profile.total_volume_usd < config.min_volume_usd:
            continue
        if profile.trade_count < config.min_trades:
            continue
        
        # Direction filter
        if config.direction_filter:
            if profile.dominant_direction != config.direction_filter:
                continue
        
        score, metrics = calculate_insider_score_v2(profile, sim_dt)
        
        results.append({
            "address": addr,
            "insider_score": score,
            "metrics": metrics,
            "historical_volume": profile.total_volume_usd,
            "dominant_direction": profile.dominant_direction
        })
    
    results.sort(key=lambda x: x["insider_score"], reverse=True)
    print(f"  Analyzed {len(results)} wallets")
    
    # Load full data for P&L
    print(f"\n[PNL] Loading full history...")
    full = load_all_trades(config.trades_file)
    
    # Add P&L
    for wallet in results:
        addr = wallet["address"]
        if addr in full:
            wallet["pnl"] = calculate_pnl(full[addr], config.winning_token)
    
    # Analyze
    scores = [r["insider_score"] for r in results]
    pnls = [r.get("pnl", {}).get("pnl_usd", 0) for r in results]
    
    correlation = np.corrcoef(scores, pnls)[0, 1] if len(scores) > 10 else 0
    
    top_insiders = results[:20]
    by_pnl = sorted(results, key=lambda x: x.get("pnl", {}).get("pnl_usd", 0), reverse=True)
    top_winners = by_pnl[:20]
    
    overlap = {w["address"] for w in top_insiders} & {w["address"] for w in top_winners}
    
    # Print results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Direction Filter: {config.direction_filter or 'All'}")
    print(f"Wallets Analyzed: {len(results)}")
    print(f"Score-PnL Correlation: {correlation:.4f}")
    print(f"Top 20 Overlap: {len(overlap)}/20 ({len(overlap)/20*100:.0f}%)")
    
    # Top insider candidates
    print(f"\n{'='*60}")
    print("TOP 10 INSIDER CANDIDATES")
    print(f"{'='*60}")
    
    for i, w in enumerate(top_insiders[:10]):
        pnl = w.get("pnl", {})
        direction = "YES" if w["dominant_direction"] == "token1" else "NO"
        correct = "[CORRECT]" if pnl.get("correct_side") else "[WRONG]"
        
        print(f"\n{i+1}. Score={w['insider_score']} | PnL=${pnl.get('pnl_usd', 0):,.0f} | {direction} {correct}")
        print(f"   Address: {w['address']}")
        print(f"   Volume: ${w['historical_volume']:,.0f}")
        
        timing = w.get("metrics", {}).get("timing", {})
        if timing.get("pattern"):
            print(f"   Pattern: {timing['pattern']}")
    
    # Top winners
    print(f"\n{'='*60}")
    print("TOP 10 ACTUAL WINNERS")
    print(f"{'='*60}")
    
    for i, w in enumerate(top_winners[:10]):
        pnl = w.get("pnl", {})
        in_top = "[DETECTED]" if w["address"] in {x["address"] for x in top_insiders} else ""
        
        print(f"\n{i+1}. PnL=${pnl.get('pnl_usd', 0):,.0f} | Score={w['insider_score']} {in_top}")
        print(f"   Address: {w['address']}")
    
    # Save
    output = {
        "config": {
            "market_name": config.market_name,
            "simulation_date": config.simulation_date,
            "direction_filter": config.direction_filter,
            "winning_token": config.winning_token
        },
        "summary": {
            "wallets_analyzed": len(results),
            "correlation": round(correlation, 4) if not np.isnan(correlation) else 0,
            "top20_overlap": len(overlap),
            "overlap_addresses": list(overlap)
        },
        "top_insider_candidates": top_insiders,
        "top_winners": top_winners
    }
    
    suffix = f"_{config.direction_filter}" if config.direction_filter else "_all"
    output_file = os.path.join(OUTPUT_DIR, f"backtest_v2{suffix}.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n\nResults saved to: {output_file}")
    return output


def run_comparison_backtest():
    """
    Run both modes and compare:
    1. All wallets (no direction filter)
    2. Only YES bettors (token1 direction filter)
    """
    print("=" * 70)
    print("COMPARISON BACKTEST")
    print("=" * 70)
    print("Running two modes to compare detection effectiveness...\n")
    
    base_config = BacktestConfig(
        trades_file="output/trump_win_trades_oct_nov.csv",
        simulation_date="2024-10-15"
    )
    
    # Mode 1: All wallets
    print("\n" + "=" * 70)
    print("MODE 1: ALL WALLETS (no direction filter)")
    print("=" * 70)
    config1 = BacktestConfig(**vars(base_config))
    config1.direction_filter = None
    result1 = run_backtest_v2(config1)
    
    # Mode 2: Only YES bettors
    print("\n\n" + "=" * 70)
    print("MODE 2: ONLY YES BETTORS (direction filter = token1)")
    print("=" * 70)
    config2 = BacktestConfig(**vars(base_config))
    config2.direction_filter = "token1"
    result2 = run_backtest_v2(config2)
    
    # Summary
    print("\n\n" + "=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)
    print(f"\n{'Mode':<30} {'Wallets':<12} {'Correlation':<15} {'Overlap':<10}")
    print("-" * 70)
    print(f"{'All Wallets':<30} {result1['summary']['wallets_analyzed']:<12} "
          f"{result1['summary']['correlation']:.4f}{'':>8} {result1['summary']['top20_overlap']}/20")
    print(f"{'Only YES Bettors (token1)':<30} {result2['summary']['wallets_analyzed']:<12} "
          f"{result2['summary']['correlation']:.4f}{'':>8} {result2['summary']['top20_overlap']}/20")
    
    print("\n[INSIGHT] With direction filtering, we can evaluate if our behavior metrics")
    print("          correctly identify 'smart money' among those betting correctly.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--compare", action="store_true", help="Run comparison between modes")
    parser.add_argument("--direction", choices=["token1", "token0", "all"], default="all",
                        help="Direction filter: token1=YES, token0=NO, all=no filter")
    args = parser.parse_args()
    
    if args.compare:
        run_comparison_backtest()
    else:
        config = BacktestConfig()
        if args.direction != "all":
            config.direction_filter = args.direction
        run_backtest_v2(config)
