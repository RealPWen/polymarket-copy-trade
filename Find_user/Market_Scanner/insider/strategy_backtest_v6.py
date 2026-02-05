"""
Strategy Backtest V6 - Incremental Cache + Exponential Sampling

Two key optimizations:

1. INCREMENTAL CACHE
   - Pre-compute daily profiles ONCE for each market
   - Reuse cached profiles across scan points
   - Only filter by date range on each scan

2. EXPONENTIAL DENSITY SAMPLING
   - Sparse sampling far from endDate
   - Dense sampling near endDate
   - More likely to catch critical signals

Usage:
    python strategy_backtest_v6.py --target 200 --threads 8
"""
import os
import sys
import json
import random
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from collections import defaultdict
from dataclasses import dataclass, field
import warnings

warnings.filterwarnings('ignore', category=UserWarning)

sys.stdout.reconfigure(encoding='utf-8')

from insider_analyzer import (
    InsiderDirectionAnalyzer, AnalysisConfig,
    DailyWalletProfile, calculate_insider_score
)
from trading_strategy import (
    StrategyConfig, EntryPriceCalculator, PositionSizer, SignalStrength
)

# Paths
ARCHIVE_DIR = Path(__file__).parent.parent / "archive"
CACHE_DIR = ARCHIVE_DIR / "market_trades"
MARKETS_FILE = ARCHIVE_DIR / "markets.csv"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

results_lock = threading.Lock()


def generate_exponential_scan_points(
    window_start: datetime,
    window_end: datetime,
    base_points: int = 10
) -> List[datetime]:
    """
    Generate scan points with exponential density near window_end.
    More points near the end, fewer points at the start.
    """
    total_hours = (window_end - window_start).total_seconds() / 3600
    
    if total_hours <= 0:
        return [window_end]
    
    points = []
    for i in range(base_points):
        ratio = i / (base_points - 1) if base_points > 1 else 0
        exp_ratio = 1 - np.exp(-3 * ratio)
        offset_hours = total_hours * (1 - exp_ratio)
        
        point = window_end - timedelta(hours=offset_hours)
        if point >= window_start:
            points.append(point)
    
    points.sort()
    
    filtered = []
    for p in points:
        if not filtered or (p - filtered[-1]).total_seconds() > 3600:
            filtered.append(p)
    
    return filtered


class IncrementalProfileCache:
    """
    Pre-compute daily profiles ONCE, then reuse across multiple scans.
    
    This avoids recomputing profiles from trades each time we scan.
    Only the date filtering is done on each scan.
    """
    
    def __init__(self, trades_df: pd.DataFrame, config: AnalysisConfig):
        self.config = config
        
        trades_df = trades_df.copy()
        trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'], errors='coerce')
        if trades_df['timestamp'].dt.tz is not None:
            trades_df['timestamp'] = trades_df['timestamp'].dt.tz_localize(None)
        trades_df = trades_df.dropna(subset=['timestamp'])
        
        # Build ALL daily profiles once
        analyzer = InsiderDirectionAnalyzer(config)
        self.all_daily_profiles = analyzer.build_daily_profiles(trades_df)
        
        # Pre-analyze each day's insider results
        self.all_daily_results = {}
        for day, profiles in self.all_daily_profiles.items():
            self.all_daily_results[day] = self._analyze_day(profiles)
    
    def _analyze_day(self, wallets: Dict[str, DailyWalletProfile]) -> dict:
        """Analyze a single day using cached profiles."""
        day_insiders = []
        
        for addr, profile in wallets.items():
            if profile.total_volume < self.config.min_wallet_volume:
                continue
            
            score, metrics = calculate_insider_score(profile)
            
            if score >= self.config.min_insider_score:
                day_insiders.append({
                    "address": addr,
                    "score": score,
                    "direction": profile.direction,
                    "conviction": profile.conviction,
                })
        
        yes_conv = sum(w["conviction"] for w in day_insiders if w["direction"] == "YES")
        no_conv = sum(w["conviction"] for w in day_insiders if w["direction"] == "NO")
        total_conv = yes_conv + no_conv
        
        yes_count = sum(1 for w in day_insiders if w["direction"] == "YES")
        no_count = sum(1 for w in day_insiders if w["direction"] == "NO")
        
        if total_conv > 0:
            direction_score = (yes_conv - no_conv) / total_conv
        else:
            direction_score = 0
        
        if direction_score > 0.3:
            signal = "STRONG_YES"
        elif direction_score > 0.1:
            signal = "YES"
        elif direction_score < -0.3:
            signal = "STRONG_NO"
        elif direction_score < -0.1:
            signal = "NO"
        else:
            signal = "NEUTRAL"
        
        return {
            "insider_count": len(day_insiders),
            "yes_insiders": yes_count,
            "no_insiders": no_count,
            "yes_conviction": yes_conv,
            "no_conviction": no_conv,
            "direction_score": direction_score,
            "signal": signal,
        }
    
    def analyze_at_time(
        self, 
        scan_time: datetime, 
        lookback_days: int
    ) -> Optional[dict]:
        """
        Run analysis using cached data, filtered by time window.
        
        This is FAST because:
        - Daily profiles already computed
        - Daily results already analyzed
        - Just filter by date and aggregate
        """
        cutoff_date = (scan_time - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        exclude_date = (scan_time - timedelta(hours=1)).strftime('%Y-%m-%d')
        
        # Filter daily results by date range
        daily_results = []
        for day in sorted(self.all_daily_results.keys()):
            if cutoff_date <= day <= exclude_date:
                result = self.all_daily_results[day].copy()
                result["date"] = day
                daily_results.append(result)
        
        if not daily_results:
            return None
        
        # Calculate aggregate - use same logic as InsiderDirectionAnalyzer
        yes_days = sum(1 for r in daily_results if r['signal'] in ['YES', 'STRONG_YES'])
        no_days = sum(1 for r in daily_results if r['signal'] in ['NO', 'STRONG_NO'])
        
        total_weight = 0.0
        weighted_score = 0.0
        
        n = len(daily_results)
        for i, r in enumerate(daily_results):
            days_from_end = n - 1 - i
            
            if days_from_end == 0:
                weight = 3.0
            elif days_from_end <= 2:
                weight = 2.0
            elif days_from_end <= 6:
                weight = 1.5
            else:
                weight = 1.0
            
            weighted_score += r['direction_score'] * weight
            total_weight += weight
        
        avg_direction = weighted_score / total_weight if total_weight > 0 else 0
        
        if avg_direction > 0.3:
            signal = "STRONG_YES"
            predicted = "YES"
        elif avg_direction > 0.1:
            signal = "YES"
            predicted = "YES"
        elif avg_direction < -0.3:
            signal = "STRONG_NO"
            predicted = "NO"
        elif avg_direction < -0.1:
            signal = "NO"
            predicted = "NO"
        else:
            signal = "NEUTRAL"
            predicted = "NEUTRAL"
        
        return {
            "signal": signal,
            "predicted": predicted,
            "direction_score": avg_direction,
            "yes_days": yes_days,
            "no_days": no_days,
            "total_insiders": sum(r['insider_count'] for r in daily_results),
            "daily_results": daily_results
        }


def infer_market_winner(trades_df: pd.DataFrame) -> Optional[str]:
    """Infer winning side from final trades."""
    try:
        trades_df = trades_df.copy()
        trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'], errors='coerce')
        trades_df = trades_df.dropna(subset=['timestamp'])
        
        if len(trades_df) < 10:
            return None
        
        last_trades = trades_df.sort_values('timestamp').tail(50)
        
        yes_trades = last_trades[last_trades['nonusdc_side'] == 'token1']
        if len(yes_trades) >= 2:
            avg_yes_price = yes_trades['price'].astype(float).mean()
            if avg_yes_price > 0.75:
                return "YES"
            elif avg_yes_price < 0.25:
                return "NO"
        
        no_trades = last_trades[last_trades['nonusdc_side'] == 'token0']
        if len(no_trades) >= 2:
            avg_no_price = no_trades['price'].astype(float).mean()
            if avg_no_price > 0.75:
                return "NO"
            elif avg_no_price < 0.25:
                return "YES"
        
        if len(yes_trades) >= 1:
            final_price = float(yes_trades.iloc[-1]['price'])
            if final_price > 0.70:
                return "YES"
            elif final_price < 0.30:
                return "NO"
        
        return None
    except:
        return None


def calculate_signal_strength(direction_score, days_consistent, insider_count):
    """Determine signal strength."""
    abs_score = abs(direction_score)
    
    if abs_score >= 0.50 and days_consistent >= 5 and insider_count >= 15:
        return SignalStrength.EXTREME
    elif abs_score >= 0.30 and days_consistent >= 3 and insider_count >= 8:
        return SignalStrength.STRONG
    elif abs_score >= 0.15 and days_consistent >= 2 and insider_count >= 3:
        return SignalStrength.MODERATE
    elif abs_score >= 0.10:
        return SignalStrength.WEAK
    return SignalStrength.NONE


def count_consistent_days(daily_results, overall_direction):
    """Count recent days consistent with overall signal."""
    if not daily_results or overall_direction == "NEUTRAL":
        return 0
    
    recent = daily_results[-10:]
    consistent = 0
    
    for day in recent:
        signal = day.get("signal", "NEUTRAL")
        if overall_direction == "YES" and signal in ["YES", "STRONG_YES"]:
            consistent += 1
        elif overall_direction == "NO" and signal in ["NO", "STRONG_NO"]:
            consistent += 1
    
    return consistent


def analyze_single_market(
    market_id: int,
    markets_df: pd.DataFrame,
    strategy_config: StrategyConfig,
    scan_window_days: int,
    scan_points: int,
    signal_threshold: float,
    min_insiders: int
) -> Tuple[Optional[dict], str]:
    """Analyze market with incremental cache + exponential sampling."""
    try:
        cache_file = CACHE_DIR / f"market_{market_id}.csv"
        if not cache_file.exists():
            return None, "no_cache"
        
        trades_df = pd.read_csv(cache_file, low_memory=False)
        if len(trades_df) < 100:
            return None, "insufficient_trades"
        
        market_row = markets_df[markets_df['id'] == market_id]
        if len(market_row) == 0:
            return None, "no_market_info"
        
        market_info = market_row.iloc[0]
        question = str(market_info.get('question', 'Unknown'))[:60]
        
        if pd.isna(market_info.get('closedTime')):
            return None, "no_close_time"
        
        closed_time = pd.to_datetime(market_info['closedTime'])
        if closed_time.tzinfo is not None:
            closed_time = closed_time.tz_localize(None)
        
        end_date = closed_time + timedelta(hours=random.uniform(-6, 6))
        
        trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'], errors='coerce')
        if trades_df['timestamp'].dt.tz is not None:
            trades_df['timestamp'] = trades_df['timestamp'].dt.tz_localize(None)
        
        actual_winner = infer_market_winner(trades_df)
        if actual_winner is None:
            return None, "no_winner"
        
        # === KEY OPTIMIZATION: Build cache ONCE ===
        analysis_config = AnalysisConfig(
            min_insider_score=int(strategy_config.insider_min_score * 100),
            lookback_days=strategy_config.insider_lookback_days
        )
        
        profile_cache = IncrementalProfileCache(trades_df, analysis_config)
        
        # Generate exponential scan points
        window_start = end_date - timedelta(days=scan_window_days)
        window_end = end_date
        
        exp_scan_points = generate_exponential_scan_points(
            window_start, window_end, scan_points
        )
        
        if not exp_scan_points:
            return None, "no_scan_points"
        
        # Find first strong signal (FAST with cache!)
        detection_time = None
        detection_result = None
        
        for scan_time in exp_scan_points:
            analysis = profile_cache.analyze_at_time(
                scan_time,
                strategy_config.insider_lookback_days
            )
            
            if analysis is None:
                continue
            
            direction_score = analysis.get("direction_score", 0)
            predicted = analysis.get("predicted", "NEUTRAL")
            total_insiders = analysis.get("total_insiders", 0)
            
            if (abs(direction_score) >= signal_threshold and
                total_insiders >= min_insiders and
                predicted != "NEUTRAL"):
                detection_time = scan_time
                detection_result = analysis
                break
        
        if detection_result is None:
            return None, "no_strong_signal"
        
        hours_before_close = (closed_time - detection_time).total_seconds() / 3600
        
        direction_score = detection_result.get("direction_score", 0)
        predicted = detection_result.get("predicted", "NEUTRAL")
        daily_results = detection_result.get("daily_results", [])
        total_insiders = detection_result.get("total_insiders", 0)
        
        # Get price at detection time
        pre_detection = trades_df[trades_df['timestamp'] < detection_time]
        if len(pre_detection) < 10:
            return None, "insufficient_pre_detection"
        
        last_trades = pre_detection.tail(10)
        yes_trades = last_trades[last_trades['nonusdc_side'] == 'token1']
        yes_price = float(yes_trades['price'].mean()) if len(yes_trades) > 0 else 0.50
        
        if predicted == "YES":
            sim_price = yes_price
        else:
            sim_price = 1.0 - yes_price
        
        days_consistent = count_consistent_days(daily_results, predicted)
        signal_strength = calculate_signal_strength(direction_score, days_consistent, total_insiders)
        
        price_calc = EntryPriceCalculator(strategy_config)
        position_sizer = PositionSizer(strategy_config)
        
        target_price, max_price = price_calc.calculate(direction_score, signal_strength, sim_price)
        
        entry_discount = max(0, (max_price - sim_price) / max_price) if max_price > 0 else 0
        position_pct = position_sizer.calculate(signal_strength, days_consistent, entry_discount)
        
        should_enter, _ = price_calc.should_enter(sim_price, max_price)
        
        if not should_enter:
            outcome = "NO_TRADE"
            pnl_per_dollar = 0
            entry_price = None
        else:
            entry_price = min(sim_price, max_price)
            if predicted == actual_winner:
                pnl_per_dollar = (1.0 / entry_price) - 1.0
                outcome = "WIN"
            else:
                pnl_per_dollar = -1.0
                outcome = "LOSS"
        
        if outcome in ["WIN", "LOSS"]:
            position_value = 10000 * position_pct
            pnl = position_value * pnl_per_dollar
        else:
            position_value = 0
            pnl = 0
        
        return {
            "market_id": market_id,
            "question": question,
            "detection_time": detection_time.isoformat(),
            "end_date": end_date.isoformat(),
            "closed_time": closed_time.isoformat(),
            "hours_before_close": round(hours_before_close, 1),
            "scan_points_used": len(exp_scan_points),
            "yes_price": round(yes_price, 4),
            "sim_price": round(sim_price, 4),
            "direction": predicted,
            "direction_score": round(direction_score, 4),
            "signal_strength": signal_strength.name,
            "days_consistent": days_consistent,
            "insider_count": total_insiders,
            "max_entry_price": round(max_price, 4),
            "entry_price": round(entry_price, 4) if entry_price else None,
            "position_pct": round(position_pct, 4),
            "position_value": round(position_value, 2),
            "actual_winner": actual_winner,
            "outcome": outcome,
            "pnl_per_dollar": round(pnl_per_dollar, 4),
            "pnl_dollars": round(pnl, 2)
        }, "ok"
        
    except Exception as e:
        return None, f"error: {str(e)[:50]}"


def run_parallel_backtest(
    target_results: int,
    strategy_config: StrategyConfig,
    scan_window_days: int,
    scan_points: int,
    signal_threshold: float,
    min_insiders: int,
    min_volume: float,
    seed: int,
    num_threads: int
) -> Dict:
    """Run optimized backtest."""
    print("=" * 80)
    print("STRATEGY BACKTEST V6 (Incremental + Exponential)")
    print("=" * 80)
    print(f"Target results: {target_results}")
    print(f"Scan window: {scan_window_days} days before endDate")
    print(f"Scan points: {scan_points} (exponentially distributed)")
    print(f"Signal threshold: score >= {signal_threshold}, insiders >= {min_insiders}")
    print(f"Threads: {num_threads}")
    print()
    
    print("[OPT 1] Incremental cache - build daily profiles ONCE per market")
    print("[OPT 2] Exponential sampling - more points near endDate")
    print()
    
    markets_df = pd.read_csv(MARKETS_FILE)
    markets_df = markets_df[markets_df['closedTime'].notna()]
    markets_df['volume'] = pd.to_numeric(markets_df['volume'], errors='coerce')
    markets_df = markets_df[markets_df['volume'] >= min_volume]
    
    cached_files = list(CACHE_DIR.glob("market_*.csv"))
    cached_ids = [int(f.stem.replace("market_", "")) for f in cached_files]
    valid_ids = [mid for mid in cached_ids if mid in markets_df['id'].values]
    
    random.seed(seed)
    random.shuffle(valid_ids)
    
    print(f"[INFO] Cached markets: {len(cached_ids)}")
    print(f"[INFO] High-volume cached: {len(valid_ids)}")
    
    results = []
    skipped = {}
    trades = {"WIN": 0, "LOSS": 0, "NO_TRADE": 0}
    total_pnl = 0.0
    total_invested = 0.0
    hours_before_stats = []
    
    print(f"\n[STEP 1] Analyzing markets...")
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {
            executor.submit(
                analyze_single_market, 
                mid, 
                markets_df, 
                strategy_config,
                scan_window_days,
                scan_points,
                signal_threshold,
                min_insiders
            ): mid for mid in valid_ids
        }
        
        for future in as_completed(futures):
            if len(results) >= target_results:
                break
            
            market_id = futures[future]
            try:
                result, skip_reason = future.result()
                
                if result is None:
                    skipped[skip_reason] = skipped.get(skip_reason, 0) + 1
                    continue
                
                results.append(result)
                outcome = result["outcome"]
                trades[outcome] = trades.get(outcome, 0) + 1
                
                if outcome in ["WIN", "LOSS"]:
                    total_invested += result["position_value"]
                    total_pnl += result["pnl_dollars"]
                    hours_before_stats.append(result["hours_before_close"])
                
                status = {"WIN": "[WIN]", "LOSS": "[LOSS]", "NO_TRADE": "[SKIP]"}.get(outcome, "[???]")
                hours_str = f"{result['hours_before_close']:.0f}h"
                print(f"  {len(results):3d}/{target_results} {status:7s} "
                      f"Dir={result['direction']:3s} @{hours_str:>5s} "
                      f"| {result['question'][:30]}...")
                
            except Exception as e:
                skipped["thread_error"] = skipped.get("thread_error", 0) + 1
    
    # Summary
    print("\n" + "=" * 80)
    print("BACKTEST RESULTS (V6 - Optimized)")
    print("=" * 80)
    
    total_trades = trades["WIN"] + trades["LOSS"]
    win_rate = trades["WIN"] / total_trades if total_trades > 0 else 0
    
    print(f"\n[TRADE OUTCOMES]")
    print(f"  Total Trades: {total_trades}")
    print(f"  Wins: {trades['WIN']}")
    print(f"  Losses: {trades['LOSS']}")
    print(f"  Win Rate: {win_rate:.1%}")
    print(f"  No Trade: {trades['NO_TRADE']}")
    
    print(f"\n[PNL SIMULATION] ($10,000 capital)")
    print(f"  Total Invested: ${total_invested:,.2f}")
    print(f"  Total PnL: ${total_pnl:,.2f}")
    if total_invested > 0:
        roi = total_pnl / total_invested
        print(f"  ROI: {roi:.1%}")
    
    if hours_before_stats:
        avg_hours = sum(hours_before_stats) / len(hours_before_stats)
        print(f"\n[DETECTION TIMING]")
        print(f"  Avg hours before close: {avg_hours:.1f}h ({avg_hours/24:.1f} days)")
    
    print(f"\n[SKIPPED]")
    for k, v in sorted(skipped.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    
    p_value = None
    if total_trades >= 10:
        try:
            from scipy import stats
            result_test = stats.binomtest(trades["WIN"], total_trades, 0.5, alternative='greater')
            p_value = result_test.pvalue
            print(f"\n[STATISTICAL SIGNIFICANCE]")
            print(f"  P-value (vs 50%): {p_value:.4f}")
            print(f"  Significant at 5%: {'YES' if p_value < 0.05 else 'NO'}")
        except:
            pass
    
    # Save
    summary = {
        "version": "V6_Optimized",
        "config": {
            "scan_window_days": scan_window_days,
            "scan_points": scan_points,
            "signal_threshold": signal_threshold,
            "min_insiders": min_insiders,
        },
        "summary": {
            "markets_analyzed": len(results),
            "total_trades": total_trades,
            "wins": trades["WIN"],
            "losses": trades["LOSS"],
            "win_rate": round(win_rate, 4),
            "total_pnl": round(total_pnl, 2),
            "roi": round(total_pnl / total_invested, 4) if total_invested > 0 else 0,
            "p_value": p_value,
        },
        "results": results
    }
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"strategy_backtest_v6_{timestamp}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\n\nResults saved to: {output_file}")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Strategy Backtest V6 (Optimized)")
    parser.add_argument("--target", type=int, default=200, help="Target results")
    parser.add_argument("--threads", type=int, default=8, help="Threads")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--window", type=int, default=5, help="Scan window days (default: 5)")
    parser.add_argument("--points", type=int, default=10, help="Scan points (default: 10)")
    parser.add_argument("--threshold", type=float, default=0.25, help="Signal threshold")
    parser.add_argument("--min-insiders", type=int, default=3, help="Min insiders")
    parser.add_argument("--volume", type=float, default=100000, help="Min volume")
    parser.add_argument("--score", type=float, default=0.15, help="Min direction score")
    args = parser.parse_args()
    
    strategy_config = StrategyConfig(min_direction_score=args.score)
    
    run_parallel_backtest(
        target_results=args.target,
        strategy_config=strategy_config,
        scan_window_days=args.window,
        scan_points=args.points,
        signal_threshold=args.threshold,
        min_insiders=args.min_insiders,
        min_volume=args.volume,
        seed=args.seed,
        num_threads=args.threads
    )
