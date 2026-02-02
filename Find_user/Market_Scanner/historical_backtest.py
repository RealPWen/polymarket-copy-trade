"""
Historical Backtest for Insider Finder

Uses poly_data archive (34GB trades.csv) to perform TRUE historical simulation:

1. SIMULATION: At time T (e.g., Oct 15, 2024), run our insider detection algorithm 
   using ONLY data available at that time
2. VALIDATION: Check if detected "insiders" actually profited when market resolved

This tests: Can our algorithm detect insiders BEFORE they profit?

Key Markets for Testing:
- Trump Win 2024 (market_id=253591): High-profile, known insider activity
  - Resolution: Nov 6, 2024 (Trump won)
  - Known patterns: Theo4, multiple whale accounts

Workflow:
1. Read trades.csv data for target market
2. At simulation_date, compute insider scores for all wallets
3. At resolution_date, compute actual P&L for each wallet
4. Correlate: Did high insider_score predict high P&L?
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
import statistics

sys.stdout.reconfigure(encoding='utf-8')

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# =============================================================================
# Configuration
# =============================================================================

@dataclass
class BacktestConfig:
    """Configuration for historical backtest."""
    # Market info
    market_id: int = 253591  # Trump Win 2024
    market_name: str = "Trump Win 2024"
    
    # Resolution outcome (for P&L calculation)
    # In Trump market: token1 = Yes (Trump wins), token0 = No
    winning_token: str = "token1"  # Trump won
    
    # Time parameters
    # Simulation date: when we "run" our insider detection
    simulation_date: str = "2024-10-15"
    # Resolution date: when market resolved
    resolution_date: str = "2024-11-06"
    
    # Data source
    trades_file: str = "output/trump_win_trades_oct_nov.csv"
    
    # Analysis parameters
    min_volume_usd: float = 1000  # Minimum volume to consider
    min_trades: int = 5  # Minimum trades to analyze

# =============================================================================
# Wallet Profile (for a specific market)
# =============================================================================

@dataclass 
class WalletMarketProfile:
    """Wallet activity profile for a specific market."""
    address: str
    
    # Volume tracking
    buy_volume_token1_usd: float = 0.0  # Bought YES shares
    sell_volume_token1_usd: float = 0.0  # Sold YES shares
    buy_volume_token0_usd: float = 0.0  # Bought NO shares  
    sell_volume_token0_usd: float = 0.0  # Sold NO shares
    
    # Share tracking
    buy_shares_token1: float = 0.0
    sell_shares_token1: float = 0.0
    buy_shares_token0: float = 0.0
    sell_shares_token0: float = 0.0
    
    # Trade tracking
    trade_count: int = 0
    trade_sizes: List[float] = field(default_factory=list)
    
    # Time tracking
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
        """Net YES shares held."""
        return self.buy_shares_token1 - self.sell_shares_token1
    
    @property
    def net_token0_shares(self) -> float:
        """Net NO shares held."""
        return self.buy_shares_token0 - self.sell_shares_token0
    
    @property
    def net_token1_invested(self) -> float:
        """Net USD invested in YES."""
        return self.buy_volume_token1_usd - self.sell_volume_token1_usd
    
    @property
    def net_token0_invested(self) -> float:
        """Net USD invested in NO."""
        return self.buy_volume_token0_usd - self.sell_volume_token0_usd
    
    @property
    def active_days(self) -> int:
        return len(self.trades_by_day)
    
    @property
    def directional_ratio(self) -> float:
        """How directional is the trading? 1.0 = all one direction."""
        total_buy = self.buy_volume_token1_usd + self.buy_volume_token0_usd
        total_sell = self.sell_volume_token1_usd + self.sell_volume_token0_usd
        total = total_buy + total_sell
        if total == 0:
            return 0
        return abs(total_buy - total_sell) / total
    
    @property
    def token1_bias(self) -> float:
        """Bias towards YES. 1 = all YES, -1 = all NO, 0 = balanced."""
        token1_flow = self.net_token1_invested
        token0_flow = self.net_token0_invested
        total = abs(token1_flow) + abs(token0_flow)
        if total == 0:
            return 0
        return (token1_flow - token0_flow) / total

# =============================================================================
# Insider Detection Metrics (applied to market profile)
# =============================================================================

def calculate_volume_concentration(profile: WalletMarketProfile) -> Tuple[float, dict]:
    """
    Volume Anomaly: Is this wallet's trading concentrated in time?
    Insider behavior: Trade heavily in short window before resolution.
    """
    if not profile.volume_by_day:
        return 0, {"error": "No data"}
    
    volumes = list(profile.volume_by_day.values())
    if len(volumes) < 2:
        # Only 1 day of activity = suspicious one-shot
        return 50, {
            "signal": "ONE_DAY_TRADER",
            "active_days": 1,
            "total_volume": sum(volumes)
        }
    
    max_vol = max(volumes)
    median_vol = statistics.median(volumes)
    mean_vol = statistics.mean(volumes)
    
    # Peak day concentration
    total = sum(volumes)
    concentration = max_vol / total if total > 0 else 0
    
    details = {
        "active_days": len(volumes),
        "max_day_volume": round(max_vol, 0),
        "median_day_volume": round(median_vol, 0),
        "concentration_ratio": round(concentration, 3)
    }
    
    score = 0
    if concentration > 0.8:
        score = 50
        details["signal"] = "EXTREME_CONCENTRATION"
    elif concentration > 0.6:
        score = 35
        details["signal"] = "HIGH_CONCENTRATION"
    elif concentration > 0.4:
        score = 20
        details["signal"] = "MODERATE_CONCENTRATION"
    
    return score, details


def calculate_size_anomaly(profile: WalletMarketProfile) -> Tuple[float, dict]:
    """
    Size Anomaly: Are there unusually large trades?
    Insider behavior: Make large high-conviction bets.
    """
    if len(profile.trade_sizes) < 5:
        return 0, {"error": "Too few trades"}
    
    sizes = profile.trade_sizes
    max_size = max(sizes)
    median_size = statistics.median(sizes)
    
    details = {
        "total_trades": len(sizes),
        "max_trade_usd": round(max_size, 0),
        "median_trade_usd": round(median_size, 0)
    }
    
    if median_size > 0:
        ratio = max_size / median_size
        details["size_ratio"] = round(ratio, 1)
        
        score = 0
        if ratio > 50:
            score = 30
            details["signal"] = "EXTREME_SIZE_ANOMALY"
        elif ratio > 20:
            score = 20
            details["signal"] = "HIGH_SIZE_ANOMALY"
        elif ratio > 10:
            score = 10
            details["signal"] = "MODERATE_SIZE_ANOMALY"
        
        return score, details
    
    return 0, details


def calculate_timing_score(profile: WalletMarketProfile, simulation_date: datetime) -> Tuple[float, dict]:
    """
    Timing Anomaly: Did trading happen close to resolution?
    Insider behavior: Trade shortly before the event.
    """
    if not profile.last_trade_ts:
        return 0, {"error": "No trades"}
    
    # How recent was the last trade relative to simulation date?
    days_from_last = (simulation_date - profile.last_trade_ts).days
    
    details = {
        "first_trade": profile.first_trade_ts.strftime("%Y-%m-%d") if profile.first_trade_ts else None,
        "last_trade": profile.last_trade_ts.strftime("%Y-%m-%d") if profile.last_trade_ts else None,
        "days_active": profile.active_days,
        "days_from_last_trade": days_from_last
    }
    
    score = 0
    
    # Recency bonus (still active)
    if days_from_last <= 3:
        score += 10
        details["recency"] = "VERY_RECENT"
    elif days_from_last <= 7:
        score += 5
        details["recency"] = "RECENT"
    
    # Burst pattern: short activity window
    if profile.first_trade_ts and profile.last_trade_ts:
        trading_span = (profile.last_trade_ts - profile.first_trade_ts).days
        details["trading_span_days"] = trading_span
        
        if trading_span <= 3 and profile.total_volume_usd > 10000:
            score += 30
            details["pattern"] = "BURST_TRADER"
        elif trading_span <= 7 and profile.total_volume_usd > 10000:
            score += 15
            details["pattern"] = "SHORT_WINDOW_TRADER"
    
    return score, details


def calculate_directional_score(profile: WalletMarketProfile) -> Tuple[float, dict]:
    """
    Directional Bias: Is trading strongly directional?
    Insider behavior: High conviction in one direction.
    """
    bias = profile.token1_bias
    directional = profile.directional_ratio
    
    details = {
        "token1_bias": round(bias, 3),  # YES bias
        "directional_ratio": round(directional, 3),
        "net_token1_shares": round(profile.net_token1_shares, 0),
        "net_token0_shares": round(profile.net_token0_shares, 0)
    }
    
    score = 0
    
    # Strong directional trading
    if directional > 0.9:
        score += 25
        details["signal"] = "EXTREME_DIRECTIONAL"
    elif directional > 0.7:
        score += 15
        details["signal"] = "HIGH_DIRECTIONAL"
    elif directional > 0.5:
        score += 5
        details["signal"] = "MODERATE_DIRECTIONAL"
    
    return score, details


def calculate_insider_score(profile: WalletMarketProfile, simulation_date: datetime) -> Tuple[int, dict]:
    """
    Combined Insider Score for historical backtest.
    """
    total_score = 0
    all_metrics = {}
    
    # Basic info
    all_metrics["summary"] = {
        "address": profile.address[:12] + "...",
        "total_volume_usd": round(profile.total_volume_usd, 0),
        "trade_count": profile.trade_count,
        "active_days": profile.active_days
    }
    
    # Volume Concentration
    score1, details1 = calculate_volume_concentration(profile)
    total_score += score1
    all_metrics["volume_concentration"] = details1
    
    # Size Anomaly
    score2, details2 = calculate_size_anomaly(profile)
    total_score += score2
    all_metrics["size_anomaly"] = details2
    
    # Timing
    score3, details3 = calculate_timing_score(profile, simulation_date)
    total_score += score3
    all_metrics["timing"] = details3
    
    # Directional
    score4, details4 = calculate_directional_score(profile)
    total_score += score4
    all_metrics["directional"] = details4
    
    # Volume bonus
    vol = profile.total_volume_usd
    if vol > 100000:
        total_score += 20
        all_metrics["volume_bonus"] = "HIGH_VOLUME"
    elif vol > 50000:
        total_score += 10
        all_metrics["volume_bonus"] = "MODERATE_VOLUME"
    
    return total_score, all_metrics

# =============================================================================
# P&L Calculator
# =============================================================================

def calculate_pnl(profile: WalletMarketProfile, winning_token: str) -> dict:
    """
    Calculate actual P&L at resolution.
    
    Settlement: Winning shares pay $1, losing shares pay $0.
    """
    if winning_token == "token1":
        # YES won
        # Profit from YES shares held
        pnl_from_yes = profile.net_token1_shares * 1.0 - profile.net_token1_invested
        # Loss from NO shares held (worth 0)
        pnl_from_no = 0 - profile.net_token0_invested
        
        final_pnl = pnl_from_yes + pnl_from_no
        
    else:  # token0 won
        # NO won
        pnl_from_no = profile.net_token0_shares * 1.0 - profile.net_token0_invested
        pnl_from_yes = 0 - profile.net_token1_invested
        
        final_pnl = pnl_from_yes + pnl_from_no
    
    total_invested = abs(profile.net_token1_invested) + abs(profile.net_token0_invested)
    roi = final_pnl / total_invested if total_invested > 0 else 0
    
    return {
        "pnl_usd": round(final_pnl, 2),
        "total_invested": round(total_invested, 2),
        "roi": round(roi, 4),
        "net_token1_shares": round(profile.net_token1_shares, 2),
        "net_token0_shares": round(profile.net_token0_shares, 2),
        "correct_side": (profile.net_token1_shares > 0) if winning_token == "token1" 
                        else (profile.net_token0_shares > 0)
    }

# =============================================================================
# Trade Data Processor
# =============================================================================

def process_trade(row, profiles: Dict[str, WalletMarketProfile]):
    """Process a single trade row and update profiles."""
    try:
        maker = str(row['maker']).lower()
        taker = str(row['taker']).lower()
        usd = float(row.get('usd_amount', 0) or 0)
        shares = float(row.get('token_amount', 0) or 0)
        token_side = str(row.get('nonusdc_side', ''))  # token1 = YES, token0 = NO
        maker_dir = str(row.get('maker_direction', '')).upper()
        
        ts_str = str(row.get('timestamp', ''))
        try:
            if 'T' in ts_str:
                ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00').split('+')[0])
            else:
                ts = datetime.strptime(ts_str[:19], "%Y-%m-%d %H:%M:%S")
        except:
            return  # Skip invalid timestamps
        
        day_key = ts.strftime("%Y-%m-%d")
        
        # Update both maker and taker profiles
        for addr, is_buy in [(maker, maker_dir == 'BUY'), (taker, maker_dir != 'BUY')]:
            if addr not in profiles:
                profiles[addr] = WalletMarketProfile(address=addr)
            
            p = profiles[addr]
            p.trade_count += 1
            p.trade_sizes.append(usd)
            
            # Time tracking
            if p.first_trade_ts is None or ts < p.first_trade_ts:
                p.first_trade_ts = ts
            if p.last_trade_ts is None or ts > p.last_trade_ts:
                p.last_trade_ts = ts
            
            p.trades_by_day[day_key] = p.trades_by_day.get(day_key, 0) + 1
            p.volume_by_day[day_key] = p.volume_by_day.get(day_key, 0) + usd
            
            # Volume/share tracking by token and direction
            if token_side == 'token1':
                if is_buy:
                    p.buy_volume_token1_usd += usd
                    p.buy_shares_token1 += shares
                else:
                    p.sell_volume_token1_usd += usd
                    p.sell_shares_token1 += shares
            else:  # token0
                if is_buy:
                    p.buy_volume_token0_usd += usd
                    p.buy_shares_token0 += shares
                else:
                    p.sell_volume_token0_usd += usd
                    p.sell_shares_token0 += shares
                    
    except Exception as e:
        pass  # Skip problematic rows


def load_trades_until_date(trades_file: str, cutoff_date: str, market_id: int = None):
    """
    Load trades up to a specific date (simulation point).
    Returns wallet profiles containing only historical data.
    """
    profiles: Dict[str, WalletMarketProfile] = {}
    cutoff_dt = datetime.strptime(cutoff_date, "%Y-%m-%d")
    
    print(f"[INFO] Loading trades until {cutoff_date}...")
    
    chunksize = 500000
    total_rows = 0
    processed_rows = 0
    
    for chunk in pd.read_csv(trades_file, chunksize=chunksize):
        total_rows += len(chunk)
        
        # Filter by market if specified
        if market_id is not None and 'market_id' in chunk.columns:
            chunk = chunk[chunk['market_id'] == market_id]
        
        # Filter by date
        chunk['_ts'] = pd.to_datetime(chunk['timestamp'])
        chunk = chunk[chunk['_ts'] <= cutoff_dt]
        
        for _, row in chunk.iterrows():
            process_trade(row, profiles)
            processed_rows += 1
        
        if len(chunk) == 0:
            continue
        print(f"  Processed chunk: {processed_rows:,} trades, {len(profiles):,} wallets")
    
    print(f"[INFO] Loaded {processed_rows:,} trades for {len(profiles):,} wallets")
    return profiles


def load_all_trades(trades_file: str, market_id: int = None):
    """Load all trades for final P&L calculation."""
    profiles: Dict[str, WalletMarketProfile] = {}
    
    print(f"[INFO] Loading ALL trades for P&L calculation...")
    
    chunksize = 500000
    processed_rows = 0
    
    for chunk in pd.read_csv(trades_file, chunksize=chunksize):
        # Filter by market if specified
        if market_id is not None and 'market_id' in chunk.columns:
            chunk = chunk[chunk['market_id'] == market_id]
        
        for _, row in chunk.iterrows():
            process_trade(row, profiles)
            processed_rows += 1
        
        print(f"  Processed: {processed_rows:,} trades")
    
    print(f"[INFO] Loaded {processed_rows:,} total trades")
    return profiles

# =============================================================================
# Main Backtest Runner
# =============================================================================

def run_historical_backtest(config: BacktestConfig):
    """
    Run the complete historical backtest.
    
    1. Load trades up to simulation_date
    2. Calculate insider scores
    3. Load all trades
    4. Calculate actual P&L
    5. Analyze correlation
    """
    print("=" * 70)
    print(f"HISTORICAL BACKTEST: {config.market_name}")
    print("=" * 70)
    print(f"Simulation Date: {config.simulation_date}")
    print(f"Resolution Date: {config.resolution_date}")
    print(f"Winning Token: {config.winning_token}")
    print()
    
    # Step 1: Load historical trades (only data available at simulation time)
    simulation_dt = datetime.strptime(config.simulation_date, "%Y-%m-%d")
    historical_profiles = load_trades_until_date(
        config.trades_file, 
        config.simulation_date,
        config.market_id
    )
    
    # Step 2: Calculate insider scores based on historical data
    print(f"\n[STEP 2] Calculating insider scores...")
    scored_wallets = []
    
    for addr, profile in historical_profiles.items():
        if profile.total_volume_usd < config.min_volume_usd:
            continue
        if profile.trade_count < config.min_trades:
            continue
        
        score, metrics = calculate_insider_score(profile, simulation_dt)
        scored_wallets.append({
            "address": addr,
            "insider_score": score,
            "metrics": metrics,
            "historical_volume": profile.total_volume_usd,
            "historical_trades": profile.trade_count
        })
    
    # Sort by insider score
    scored_wallets.sort(key=lambda x: x["insider_score"], reverse=True)
    print(f"  Analyzed {len(scored_wallets)} wallets with sufficient activity")
    
    # Step 3: Load ALL trades for final P&L
    print(f"\n[STEP 3] Loading full trade history for P&L...")
    full_profiles = load_all_trades(config.trades_file, config.market_id)
    
    # Step 4: Calculate actual P&L
    print(f"\n[STEP 4] Calculating actual P&L...")
    results = []
    
    for wallet in scored_wallets:
        addr = wallet["address"]
        if addr in full_profiles:
            pnl_data = calculate_pnl(full_profiles[addr], config.winning_token)
            wallet["pnl"] = pnl_data
            results.append(wallet)
    
    # Step 5: Analyze correlation
    print(f"\n[STEP 5] Analyzing Score vs P&L correlation...")
    
    # Get scores and PnLs
    scores = [r["insider_score"] for r in results]
    pnls = [r["pnl"]["pnl_usd"] for r in results]
    
    if len(scores) > 10:
        correlation = np.corrcoef(scores, pnls)[0, 1]
    else:
        correlation = 0
    
    # Top insider candidates
    top_insiders = results[:20]
    
    # Top actual winners
    by_pnl = sorted(results, key=lambda x: x["pnl"]["pnl_usd"], reverse=True)
    top_winners = by_pnl[:20]
    
    # Overlap analysis
    top_insider_addrs = {w["address"] for w in top_insiders}
    top_winner_addrs = {w["address"] for w in top_winners}
    overlap = top_insider_addrs & top_winner_addrs
    
    # Print results
    print("\n" + "=" * 70)
    print("BACKTEST RESULTS")
    print("=" * 70)
    
    print(f"\nScore-PnL Correlation: {correlation:.4f}")
    print(f"Top 20 Overlap: {len(overlap)}/20 ({len(overlap)/20*100:.0f}%)")
    
    print(f"\n{'='*60}")
    print("TOP 10 INSIDER CANDIDATES (by score)")
    print(f"{'='*60}")
    for i, w in enumerate(top_insiders[:10]):
        pnl = w.get("pnl", {})
        print(f"\n{i+1}. Score={w['insider_score']} | PnL=${pnl.get('pnl_usd', 0):,.0f} | ROI={pnl.get('roi', 0):.1%}")
        print(f"   Address: {w['address']}")
        print(f"   Volume: ${w['historical_volume']:,.0f} | Trades: {w['historical_trades']}")
        
        timing = w.get("metrics", {}).get("timing", {})
        if timing.get("pattern"):
            print(f"   Pattern: {timing.get('pattern')}")
        
        directional = w.get("metrics", {}).get("directional", {})
        print(f"   Token1 Bias: {directional.get('token1_bias', 0):.2f} | Correct Side: {pnl.get('correct_side', False)}")
    
    print(f"\n{'='*60}")
    print("TOP 10 ACTUAL WINNERS (by P&L)")
    print(f"{'='*60}")
    for i, w in enumerate(top_winners[:10]):
        pnl = w.get("pnl", {})
        in_top_insiders = "[DETECTED]" if w["address"] in top_insider_addrs else ""
        print(f"\n{i+1}. PnL=${pnl.get('pnl_usd', 0):,.0f} | ROI={pnl.get('roi', 0):.1%} | Score={w['insider_score']} {in_top_insiders}")
        print(f"   Address: {w['address']}")
    
    # Save results
    output = {
        "config": {
            "market_name": config.market_name,
            "market_id": config.market_id,
            "simulation_date": config.simulation_date,
            "resolution_date": config.resolution_date,
            "winning_token": config.winning_token
        },
        "summary": {
            "total_wallets_analyzed": len(results),
            "correlation": round(correlation, 4) if not np.isnan(correlation) else 0,
            "top20_overlap": len(overlap),
            "overlap_addresses": list(overlap)
        },
        "top_insider_candidates": top_insiders,
        "top_actual_winners": top_winners
    }
    
    output_file = os.path.join(OUTPUT_DIR, "historical_backtest_results.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n\nResults saved to: {output_file}")
    
    return output


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    # Default config for Trump 2024 market
    config = BacktestConfig(
        market_id=253591,
        market_name="Trump Win 2024",
        winning_token="token1",  # YES = Trump wins
        simulation_date="2024-10-15",  # 3 weeks before election
        resolution_date="2024-11-06",
        trades_file="output/trump_win_trades_oct_nov.csv"
    )
    
    # Run backtest
    run_historical_backtest(config)
