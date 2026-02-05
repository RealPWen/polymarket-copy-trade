"""
Strategy Backtest V4 - Rolling Signal Detection

NEW APPROACH: Detect when insider signal FIRST becomes strong.

Simulate REAL live trading:
1. For each market, scan backwards from resolution
2. Find the FIRST time insider signal exceeds threshold
3. That's our entry point
4. Measure accuracy based on final outcome

This is realistic because:
- In live trading, we continuously monitor markets
- When signal first becomes strong, we enter
- We don't need to know closedTime in advance

Usage:
    python strategy_backtest_v4.py --target 200 --threads 8
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

sys.stdout.reconfigure(encoding='utf-8')

from insider_analyzer import InsiderDirectionAnalyzer, AnalysisConfig
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


class SignalDetectionConfig:
    """Configuration for rolling signal detection."""
    def __init__(
        self,
        scan_interval_hours: int = 6,      # How often we "check" the market
        max_scan_days: int = 30,           # How far back to scan
        signal_threshold: float = 0.25,    # Min direction score to trigger
        min_insiders: int = 3,             # Min insider count to trigger
    ):
        self.scan_interval_hours = scan_interval_hours
        self.max_scan_days = max_scan_days
        self.signal_threshold = signal_threshold
        self.min_insiders = min_insiders


def find_first_strong_signal(
    trades_df: pd.DataFrame,
    closed_time: datetime,
    strategy_config: StrategyConfig,
    detection_config: SignalDetectionConfig
) -> Optional[Tuple[datetime, dict]]:
    """
    Scan backwards from close to find FIRST strong insider signal.
    
    Returns: (detection_time, analysis_result) or None
    
    This simulates: "When did we first detect actionable insider activity?"
    """
    trades_df = trades_df.copy()
    trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'], errors='coerce')
    if trades_df['timestamp'].dt.tz is not None:
        trades_df['timestamp'] = trades_df['timestamp'].dt.tz_localize(None)
    trades_df = trades_df.dropna(subset=['timestamp'])
    
    if len(trades_df) < 100:
        return None
    
    analyzer = InsiderDirectionAnalyzer(AnalysisConfig(
        min_insider_score=strategy_config.insider_min_score,
        lookback_days=strategy_config.insider_lookback_days
    ))
    
    # Scan from earliest to latest (find FIRST strong signal)
    scan_points = []
    start_time = closed_time - timedelta(days=detection_config.max_scan_days)
    current = start_time
    
    while current < closed_time:
        scan_points.append(current)
        current += timedelta(hours=detection_config.scan_interval_hours)
    
    first_strong = None
    
    for scan_time in scan_points:
        # Only use data up to scan_time
        available_trades = trades_df[trades_df['timestamp'] < scan_time]
        
        if len(available_trades) < 50:
            continue
        
        try:
            analysis = analyzer.analyze_market(
                available_trades,
                closed_time=scan_time,
                return_daily=True
            )
            
            if analysis.get("signal") == "NO_DATA":
                continue
            
            direction_score = analysis.get("direction_score", 0)
            predicted = analysis.get("predicted", "NEUTRAL")
            total_insiders = analysis.get("total_insiders", 0)
            
            # Check if signal is strong enough
            if (abs(direction_score) >= detection_config.signal_threshold and
                total_insiders >= detection_config.min_insiders and
                predicted != "NEUTRAL"):
                
                # Found first strong signal!
                first_strong = (scan_time, analysis)
                break
                
        except:
            continue
    
    return first_strong


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
    detection_config: SignalDetectionConfig
) -> Tuple[Optional[dict], str]:
    """
    Analyze a single market using rolling signal detection.
    
    KEY POINT: Entry is triggered when insider signal FIRST becomes strong,
    not based on knowing closedTime.
    """
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
        
        # Prepare trades
        trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'], errors='coerce')
        if trades_df['timestamp'].dt.tz is not None:
            trades_df['timestamp'] = trades_df['timestamp'].dt.tz_localize(None)
        
        actual_winner = infer_market_winner(trades_df)
        if actual_winner is None:
            return None, "no_winner"
        
        # CORE V4: Find first strong signal
        signal_result = find_first_strong_signal(
            trades_df, closed_time, strategy_config, detection_config
        )
        
        if signal_result is None:
            return None, "no_strong_signal"
        
        detection_time, analysis = signal_result
        
        # Calculate how early we detected (for reference)
        hours_before_close = (closed_time - detection_time).total_seconds() / 3600
        
        direction_score = analysis.get("direction_score", 0)
        predicted = analysis.get("predicted", "NEUTRAL")
        daily_results = analysis.get("daily_results", [])
        total_insiders = analysis.get("total_insiders", 0)
        
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
            "closed_time": closed_time.isoformat(),
            "hours_before_close": round(hours_before_close, 1),
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
    detection_config: SignalDetectionConfig,
    min_volume: float,
    seed: int,
    num_threads: int
) -> Dict:
    """Run backtest with multi-threading."""
    print("=" * 80)
    print("STRATEGY BACKTEST V4 (Rolling Signal Detection)")
    print("=" * 80)
    print(f"Target results: {target_results}")
    print(f"Scan interval: every {detection_config.scan_interval_hours}h")
    print(f"Signal threshold: score >= {detection_config.signal_threshold}, insiders >= {detection_config.min_insiders}")
    print(f"Threads: {num_threads}")
    print()
    
    print("[KEY] This version finds FIRST strong insider signal")
    print("[KEY] Entry does NOT depend on knowing closedTime in advance")
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
                detection_config
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
    print("BACKTEST RESULTS (V4 - Rolling Signal Detection)")
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
        print(f"  Min: {min(hours_before_stats):.1f}h, Max: {max(hours_before_stats):.1f}h")
    
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
            print(f"  Significant at 1%: {'YES' if p_value < 0.01 else 'NO'}")
        except:
            pass
    
    print("\n[BREAKDOWN BY SIGNAL STRENGTH]")
    for strength in ["EXTREME", "STRONG", "MODERATE", "WEAK"]:
        strength_results = [r for r in results 
                          if r.get("signal_strength") == strength 
                          and r.get("outcome") in ["WIN", "LOSS"]]
        if strength_results:
            wins = sum(1 for r in strength_results if r["outcome"] == "WIN")
            total = len(strength_results)
            acc = wins / total * 100
            avg_pnl = sum(r["pnl_dollars"] for r in strength_results) / len(strength_results)
            print(f"  {strength:12s}: {wins}/{total} ({acc:.0f}%) | Avg PnL: ${avg_pnl:,.0f}")
    
    # Save
    summary = {
        "version": "V4_RollingSignal",
        "config": {
            "scan_interval_hours": detection_config.scan_interval_hours,
            "signal_threshold": detection_config.signal_threshold,
            "min_insiders": detection_config.min_insiders,
            "min_direction_score": strategy_config.min_direction_score,
        },
        "summary": {
            "markets_analyzed": len(results),
            "total_trades": total_trades,
            "wins": trades["WIN"],
            "losses": trades["LOSS"],
            "no_trade": trades["NO_TRADE"],
            "win_rate": round(win_rate, 4),
            "total_invested": round(total_invested, 2),
            "total_pnl": round(total_pnl, 2),
            "roi": round(total_pnl / total_invested, 4) if total_invested > 0 else 0,
            "avg_hours_before_close": round(sum(hours_before_stats) / len(hours_before_stats), 1) if hours_before_stats else None,
            "p_value": p_value,
            "skipped": skipped
        },
        "results": results
    }
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"strategy_backtest_v4_{timestamp}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\n\nResults saved to: {output_file}")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Strategy Backtest V4 (Rolling Signal)")
    parser.add_argument("--target", type=int, default=200, help="Target results")
    parser.add_argument("--threads", type=int, default=8, help="Threads")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--interval", type=int, default=6, help="Scan interval hours (default: 6)")
    parser.add_argument("--threshold", type=float, default=0.25, help="Signal threshold (default: 0.25)")
    parser.add_argument("--min-insiders", type=int, default=3, help="Min insiders (default: 3)")
    parser.add_argument("--volume", type=float, default=100000, help="Min volume")
    parser.add_argument("--score", type=float, default=0.15, help="Min direction score")
    args = parser.parse_args()
    
    strategy_config = StrategyConfig(min_direction_score=args.score)
    
    detection_config = SignalDetectionConfig(
        scan_interval_hours=args.interval,
        signal_threshold=args.threshold,
        min_insiders=args.min_insiders
    )
    
    run_parallel_backtest(
        target_results=args.target,
        strategy_config=strategy_config,
        detection_config=detection_config,
        min_volume=args.volume,
        seed=args.seed,
        num_threads=args.threads
    )
