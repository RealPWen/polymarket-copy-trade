"""
Strategy Backtest V3b - Using endDate (simulated)

Same as V3 but uses endDate instead of closedTime.
This simulates real trading where closedTime is unknown.

Since local cache doesn't have endDate, we simulate it as:
    endDate = closedTime + random(-12h, +12h)

This tests: "If we only know approximate end time, is strategy still profitable?"

Usage:
    python strategy_backtest_v3b.py --target 1000 --threads 8 --hours 1 --score 0.30
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
import warnings

warnings.filterwarnings('ignore')
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
    config: StrategyConfig,
    entry_hours: float,
    enddate_variance_hours: float = 12.0  # How much endDate differs from closedTime
) -> Tuple[Optional[dict], str]:
    """
    Analyze market using endDate (simulated) instead of closedTime.
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
        
        # SIMULATE endDate: closedTime + random variance
        # In real trading, endDate is known but not exact
        variance = random.uniform(-enddate_variance_hours, enddate_variance_hours)
        end_date = closed_time + timedelta(hours=variance)
        
        # Entry time based on endDate (not closedTime!)
        simulation_time = end_date - timedelta(hours=entry_hours)
        
        trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'], errors='coerce')
        if trades_df['timestamp'].dt.tz is not None:
            trades_df['timestamp'] = trades_df['timestamp'].dt.tz_localize(None)
        
        actual_winner = infer_market_winner(trades_df)
        if actual_winner is None:
            return None, "no_winner"
        
        # Get price at simulation time
        pre_sim = trades_df[trades_df['timestamp'] < simulation_time]
        if len(pre_sim) < 10:
            return None, "insufficient_data"
        
        last_trades = pre_sim.tail(10)
        yes_trades = last_trades[last_trades['nonusdc_side'] == 'token1']
        yes_price = float(yes_trades['price'].mean()) if len(yes_trades) > 0 else 0.50
        
        # Run insider analysis
        analyzer = InsiderDirectionAnalyzer(AnalysisConfig(
            min_insider_score=config.insider_min_score,
            lookback_days=config.insider_lookback_days
        ))
        
        analysis = analyzer.analyze_market(
            trades_df,
            closed_time=simulation_time,
            return_daily=True
        )
        
        if analysis.get("signal") == "NO_DATA":
            return None, "no_signal"
        
        direction_score = analysis.get("direction_score", 0)
        predicted = analysis.get("predicted", "NEUTRAL")
        daily_results = analysis.get("daily_results", [])
        total_insiders = analysis.get("total_insiders", 0)
        
        if predicted == "NEUTRAL" or abs(direction_score) < config.min_direction_score:
            return None, "weak_signal"
        
        if predicted == "YES":
            sim_price = yes_price
        else:
            sim_price = 1.0 - yes_price
        
        days_consistent = count_consistent_days(daily_results, predicted)
        signal_strength = calculate_signal_strength(direction_score, days_consistent, total_insiders)
        
        price_calc = EntryPriceCalculator(config)
        position_sizer = PositionSizer(config)
        
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
        
        # Calculate actual timing (for reference)
        hours_before_close = (closed_time - simulation_time).total_seconds() / 3600
        
        return {
            "market_id": market_id,
            "question": question,
            "simulation_time": simulation_time.isoformat(),
            "end_date": end_date.isoformat(),
            "closed_time": closed_time.isoformat(),
            "enddate_variance_h": round(variance, 1),
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
    entry_hours: float,
    config: StrategyConfig,
    min_volume: float,
    seed: int,
    num_threads: int,
    enddate_variance: float
) -> Dict:
    """Run backtest with endDate simulation."""
    print("=" * 80)
    print("STRATEGY BACKTEST V3b (Using endDate)")
    print("=" * 80)
    print(f"Target results: {target_results}")
    print(f"Entry: endDate - {entry_hours}h")
    print(f"endDate variance: +/-{enddate_variance}h from closedTime")
    print(f"Min direction score: {config.min_direction_score}")
    print(f"Threads: {num_threads}")
    print()
    
    print("[KEY] Using endDate (simulated) instead of closedTime")
    print("[KEY] This tests real-world scenario where closedTime is unknown")
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
    
    print(f"\n[STEP 1] Analyzing markets...")
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {
            executor.submit(
                analyze_single_market, 
                mid, 
                markets_df, 
                config,
                entry_hours,
                enddate_variance
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
                
                status = {"WIN": "[WIN]", "LOSS": "[LOSS]", "NO_TRADE": "[SKIP]"}.get(outcome, "[???]")
                print(f"  {len(results):3d}/{target_results} {status:7s} "
                      f"Dir={result['direction']:3s} Score={result['direction_score']:+.2f} "
                      f"| {result['question'][:35]}...")
                
            except Exception as e:
                skipped["thread_error"] = skipped.get("thread_error", 0) + 1
    
    # Summary
    print("\n" + "=" * 80)
    print("BACKTEST RESULTS (V3b - endDate)")
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
    
    # Save
    summary = {
        "version": "V3b_endDate",
        "config": {
            "entry_hours": entry_hours,
            "enddate_variance_hours": enddate_variance,
            "min_direction_score": config.min_direction_score,
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
    output_file = OUTPUT_DIR / f"strategy_backtest_v3b_{timestamp}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\n\nResults saved to: {output_file}")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Strategy Backtest V3b (endDate)")
    parser.add_argument("--target", type=int, default=200, help="Target results")
    parser.add_argument("--threads", type=int, default=8, help="Threads")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--hours", type=float, default=1.0, help="Hours before endDate")
    parser.add_argument("--variance", type=float, default=12.0, help="endDate variance hours")
    parser.add_argument("--volume", type=float, default=100000, help="Min volume")
    parser.add_argument("--score", type=float, default=0.15, help="Min direction score")
    args = parser.parse_args()
    
    config = StrategyConfig(min_direction_score=args.score)
    
    run_parallel_backtest(
        target_results=args.target,
        entry_hours=args.hours,
        config=config,
        min_volume=args.volume,
        seed=args.seed,
        num_threads=args.threads,
        enddate_variance=args.variance
    )
