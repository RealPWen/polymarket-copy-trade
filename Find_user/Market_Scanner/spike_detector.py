"""
Event-Driven Insider Detection - Spike Analysis

User Insight:
- Real insiders don't enter early
- They SPIKE in right before an event
- Google Year in Search: days before announcement
- Maduro Out: HOURS before

New Approach:
1. Analyze trading INCREMENTALLY (not cumulative)
2. Detect VOLUME SPIKES (unusual activity windows)
3. Analyze direction of NEW money flowing in during spikes
4. Signal strength based on spike magnitude

This is closer to real insider behavior detection.
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
class SpikeConfig:
    market_id: int = 253591
    market_name: str = "Trump Win 2024"
    winning_token: str = "token1"
    trades_file: str = "output/trump_win_trades_oct_nov.csv"
    
    # Time windows
    spike_window_hours: int = 24  # What counts as a "spike window"
    lookback_days: int = 7  # How much history to compare against
    
    # Thresholds
    min_spike_volume: float = 100000  # Minimum volume to count as spike
    spike_ratio_threshold: float = 3.0  # Volume must be Nx higher than average

# =============================================================================
# Time-Series Volume Analysis
# =============================================================================

@dataclass
class TimeWindow:
    start_ts: datetime
    end_ts: datetime
    yes_volume: float = 0.0
    no_volume: float = 0.0
    yes_wallets: set = field(default_factory=set)
    no_wallets: set = field(default_factory=set)
    
    # New wallets that appeared in this window
    new_yes_wallets: set = field(default_factory=set)
    new_no_wallets: set = field(default_factory=set)
    new_wallet_yes_volume: float = 0.0
    new_wallet_no_volume: float = 0.0
    
    @property
    def total_volume(self) -> float:
        return self.yes_volume + self.no_volume
    
    @property
    def direction_ratio(self) -> float:
        """Positive = YES dominated, Negative = NO dominated"""
        total = self.yes_volume + self.no_volume
        if total == 0:
            return 0
        return (self.yes_volume - self.no_volume) / total
    
    @property
    def new_wallet_direction(self) -> float:
        """Direction of NEW money"""
        total = self.new_wallet_yes_volume + self.new_wallet_no_volume
        if total == 0:
            return 0
        return (self.new_wallet_yes_volume - self.new_wallet_no_volume) / total


def load_trades_as_df(trades_file: str) -> pd.DataFrame:
    """Load all trades into a DataFrame."""
    print(f"[INFO] Loading trades from {trades_file}...")
    
    chunks = []
    for chunk in pd.read_csv(trades_file, chunksize=500000):
        chunks.append(chunk)
        print(f"  Loaded {len(chunk):,} rows...")
    
    df = pd.concat(chunks, ignore_index=True)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    print(f"[INFO] Total trades: {len(df):,}")
    return df


def analyze_by_day(df: pd.DataFrame) -> Dict[str, TimeWindow]:
    """Analyze trading activity by day."""
    
    # Extract day
    df['day'] = df['timestamp'].dt.strftime('%Y-%m-%d')
    
    # Track which wallets we've seen
    all_seen_wallets = set()
    
    daily_windows = {}
    
    for day in sorted(df['day'].unique()):
        day_data = df[df['day'] == day]
        
        window = TimeWindow(
            start_ts=datetime.strptime(day, '%Y-%m-%d'),
            end_ts=datetime.strptime(day, '%Y-%m-%d') + timedelta(days=1)
        )
        
        for _, row in day_data.iterrows():
            try:
                maker = str(row['maker']).lower()
                taker = str(row['taker']).lower()
                usd = float(row.get('usd_amount', 0) or 0)
                token_side = str(row.get('nonusdc_side', ''))
                maker_dir = str(row.get('maker_direction', '')).upper()
                
                # Determine direction for each participant
                for addr, is_buy in [(maker, maker_dir == 'BUY'), (taker, maker_dir != 'BUY')]:
                    is_new = addr not in all_seen_wallets
                    
                    # Buying YES token = bullish (betting Trump wins)
                    # Buying NO token = bearish (betting Trump loses)
                    # Selling YES token = bearish
                    # Selling NO token = bullish
                    
                    if token_side == 'token1':  # YES token
                        if is_buy:
                            # Buying YES = bullish
                            window.yes_volume += usd
                            window.yes_wallets.add(addr)
                            if is_new:
                                window.new_yes_wallets.add(addr)
                                window.new_wallet_yes_volume += usd
                        # Don't count selling as bearish - let trades be one-sided
                    else:  # NO token
                        if is_buy:
                            # Buying NO = bearish
                            window.no_volume += usd
                            window.no_wallets.add(addr)
                            if is_new:
                                window.new_no_wallets.add(addr)
                                window.new_wallet_no_volume += usd
                    
                    all_seen_wallets.add(addr)
            except:
                pass
        
        daily_windows[day] = window
    
    return daily_windows


def detect_spikes(daily_windows: Dict[str, TimeWindow], 
                  config: SpikeConfig) -> List[dict]:
    """
    Detect volume spikes by comparing each day to rolling average.
    """
    days = sorted(daily_windows.keys())
    spikes = []
    
    for i, day in enumerate(days):
        window = daily_windows[day]
        
        # Need at least some lookback
        if i < config.lookback_days:
            continue
        
        # Calculate rolling average
        lookback_days = days[max(0, i - config.lookback_days):i]
        avg_volume = statistics.mean([
            daily_windows[d].total_volume for d in lookback_days
        ]) if lookback_days else 0
        
        # Is this a spike?
        if avg_volume > 0:
            spike_ratio = window.total_volume / avg_volume
        else:
            spike_ratio = float('inf') if window.total_volume > 0 else 0
        
        is_spike = (
            window.total_volume >= config.min_spike_volume and
            spike_ratio >= config.spike_ratio_threshold
        )
        
        if is_spike:
            spikes.append({
                "date": day,
                "total_volume": round(window.total_volume, 0),
                "avg_volume": round(avg_volume, 0),
                "spike_ratio": round(spike_ratio, 2),
                "yes_volume": round(window.yes_volume, 0),
                "no_volume": round(window.no_volume, 0),
                "direction_ratio": round(window.direction_ratio, 3),
                "new_wallet_direction": round(window.new_wallet_direction, 3),
                "new_yes_wallets": len(window.new_yes_wallets),
                "new_no_wallets": len(window.new_no_wallets),
                "signal": "BULLISH" if window.new_wallet_direction > 0.1 else 
                         "BEARISH" if window.new_wallet_direction < -0.1 else "NEUTRAL"
            })
    
    return spikes


def analyze_incremental_flow(daily_windows: Dict[str, TimeWindow]) -> List[dict]:
    """
    Analyze the INCREMENTAL (not cumulative) flow each day.
    This shows where NEW money is going.
    """
    days = sorted(daily_windows.keys())
    flows = []
    
    for day in days:
        window = daily_windows[day]
        
        # Only care about days with significant activity
        if window.total_volume < 10000:
            continue
        
        flows.append({
            "date": day,
            "daily_volume": round(window.total_volume, 0),
            "yes_volume": round(window.yes_volume, 0),
            "no_volume": round(window.no_volume, 0),
            "daily_direction": round(window.direction_ratio, 3),
            "new_wallet_yes_vol": round(window.new_wallet_yes_volume, 0),
            "new_wallet_no_vol": round(window.new_wallet_no_volume, 0),
            "new_wallet_direction": round(window.new_wallet_direction, 3),
            "signal": "YES" if window.direction_ratio > 0 else "NO"
        })
    
    return flows


def run_spike_analysis(config: SpikeConfig):
    """Run the spike detection analysis."""
    print("=" * 70)
    print(f"SPIKE DETECTION: {config.market_name}")
    print("=" * 70)
    print(f"Looking for volume spikes > {config.spike_ratio_threshold}x average")
    print()
    
    # Load data
    df = load_trades_as_df(config.trades_file)
    
    # Analyze by day
    print("\n[ANALYZING] Daily volumes...")
    daily = analyze_by_day(df)
    
    # Detect spikes
    print("\n[DETECTING] Volume spikes...")
    spikes = detect_spikes(daily, config)
    
    # Print spike summary
    print("\n" + "=" * 80)
    print("DETECTED VOLUME SPIKES")
    print("=" * 80)
    print(f"\n{'Date':<12} {'Volume':>12} {'Ratio':>8} {'YES':>12} {'NO':>12} {'Direction':>12} {'Signal':>10}")
    print("-" * 80)
    
    for s in spikes:
        print(f"{s['date']:<12} ${s['total_volume']:>10,.0f} {s['spike_ratio']:>7.1f}x "
              f"${s['yes_volume']:>10,.0f} ${s['no_volume']:>10,.0f} "
              f"{s['direction_ratio']:>+11.3f} {s['signal']:>10}")
    
    # Analyze incremental flow
    print("\n\n" + "=" * 80)
    print("DAILY INCREMENTAL FLOW (NEW MONEY DIRECTION)")
    print("=" * 80)
    
    flows = analyze_incremental_flow(daily)
    
    # Print last 20 days
    print(f"\n{'Date':<12} {'Volume':>12} {'New YES':>12} {'New NO':>12} {'New Direction':>15} {'Signal':>8}")
    print("-" * 80)
    
    for f in flows[-20:]:
        print(f"{f['date']:<12} ${f['daily_volume']:>10,.0f} "
              f"${f['new_wallet_yes_vol']:>10,.0f} ${f['new_wallet_no_vol']:>10,.0f} "
              f"{f['new_wallet_direction']:>+14.3f} {f['signal']:>8}")
    
    # Strong signal days
    print("\n\n" + "=" * 80)
    print("STRONG SIGNAL DAYS (|direction| > 0.3)")
    print("=" * 80)
    
    strong_days = [f for f in flows if abs(f['daily_direction']) > 0.3]
    
    yes_strong = sum(1 for f in strong_days if f['signal'] == 'YES')
    no_strong = sum(1 for f in strong_days if f['signal'] == 'NO')
    
    print(f"\nTotal strong signal days: {len(strong_days)}")
    print(f"  Strong YES days: {yes_strong}")
    print(f"  Strong NO days: {no_strong}")
    
    # Validation
    print("\n" + "=" * 80)
    print("VALIDATION")
    print("=" * 80)
    
    # Check spike signals
    if spikes:
        spike_yes = sum(1 for s in spikes if s['signal'] == 'BULLISH')
        spike_no = sum(1 for s in spikes if s['signal'] == 'BEARISH')
        print(f"\nSpike days signal: {spike_yes} BULLISH vs {spike_no} BEARISH")
        overall_spike_signal = "YES" if spike_yes > spike_no else "NO"
        print(f"Overall spike signal: {overall_spike_signal}")
        print(f"Actual winner: {'YES' if config.winning_token == 'token1' else 'NO'}")
        print(f"Correct: {'[SUCCESS]' if overall_spike_signal == ('YES' if config.winning_token == 'token1' else 'NO') else '[WRONG]'}")
    
    # Save results
    output = {
        "config": {
            "market_name": config.market_name,
            "spike_threshold": config.spike_ratio_threshold,
            "lookback_days": config.lookback_days
        },
        "spikes": spikes,
        "daily_flows": flows[-30:],  # Last 30 days
        "summary": {
            "total_spikes": len(spikes),
            "bullish_spikes": len([s for s in spikes if s['signal'] == 'BULLISH']),
            "bearish_spikes": len([s for s in spikes if s['signal'] == 'BEARISH']),
            "strong_yes_days": yes_strong,
            "strong_no_days": no_strong
        }
    }
    
    output_file = os.path.join(OUTPUT_DIR, "spike_analysis.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n\nResults saved to: {output_file}")
    return output


if __name__ == "__main__":
    config = SpikeConfig()
    run_spike_analysis(config)
