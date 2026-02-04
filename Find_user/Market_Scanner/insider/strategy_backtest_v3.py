"""
Strategy Backtest V3 - Multi-threaded, Cache-only

Optimizations:
1. Load only from cached market files (no 35GB file scan)
2. Multi-threaded market analysis
3. Continue until 200 valid results

Usage:
    python strategy_backtest_v3.py --target 200 --threads 8
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

# Thread-safe counter
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
    config: StrategyConfig,
    entry_hours: float  # Changed from days to hours
) -> Tuple[Optional[dict], str]:
    """
    Analyze a single market from cache.
    Returns (result_dict, skip_reason) - result is None if skipped
    """
    try:
        # Load from cache
        cache_file = CACHE_DIR / f"market_{market_id}.csv"
        if not cache_file.exists():
            return None, "no_cache"
        
        trades_df = pd.read_csv(cache_file, low_memory=False)
        if len(trades_df) < 100:
            return None, "insufficient_trades"
        
        # Get market info
        market_row = markets_df[markets_df['id'] == market_id]
        if len(market_row) == 0:
            return None, "no_market_info"
        
        market_info = market_row.iloc[0]
        question = str(market_info.get('question', 'Unknown'))[:60]
        
        # Get close time
        if pd.isna(market_info.get('closedTime')):
            return None, "no_close_time"
        
        closed_time = pd.to_datetime(market_info['closedTime'])
        if closed_time.tzinfo is not None:
            closed_time = closed_time.tz_localize(None)
        
        # Simulation time - now supports hours
        simulation_time = closed_time - timedelta(hours=entry_hours)
        
        # Prepare trades
        trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'], errors='coerce')
        if trades_df['timestamp'].dt.tz is not None:
            trades_df['timestamp'] = trades_df['timestamp'].dt.tz_localize(None)
        
        # Get actual winner
        actual_winner = infer_market_winner(trades_df)
        if actual_winner is None:
            return None, "no_winner"
        
        # Get YES price at simulation time
        pre_sim = trades_df[trades_df['timestamp'] < simulation_time]
        if len(pre_sim) < 50:
            return None, "insufficient_pre_sim"
        
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
        
        # CRITICAL: Use correct price based on direction
        if predicted == "YES":
            sim_price = yes_price
        else:
            sim_price = 1.0 - yes_price
        
        # Calculate signal metrics
        days_consistent = count_consistent_days(daily_results, predicted)
        signal_strength = calculate_signal_strength(direction_score, days_consistent, total_insiders)
        
        # Calculate entry price
        price_calc = EntryPriceCalculator(config)
        position_sizer = PositionSizer(config)
        
        target_price, max_price = price_calc.calculate(direction_score, signal_strength, sim_price)
        
        # Calculate position size
        entry_discount = max(0, (max_price - sim_price) / max_price) if max_price > 0 else 0
        position_pct = position_sizer.calculate(signal_strength, days_consistent, entry_discount)
        
        # Determine if we would trade
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
        
        # Calculate dollar PnL
        if outcome in ["WIN", "LOSS"]:
            position_value = 10000 * position_pct
            pnl = position_value * pnl_per_dollar
        else:
            position_value = 0
            pnl = 0
        
        return {
            "market_id": market_id,
            "question": question,
            "simulation_time": simulation_time.isoformat(),
            "closed_time": closed_time.isoformat(),
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
    entry_hours: float,  # Changed to hours
    config: StrategyConfig,
    min_volume: float,
    seed: int,
    num_threads: int
) -> Dict:
    """Run backtest with multi-threading."""
    print("=" * 80)
    print("STRATEGY BACKTEST V3 (Multi-threaded, Cache-only)")
    print("=" * 80)
    print(f"Target results: {target_results}")
    if entry_hours >= 24:
        print(f"Entry timing: {entry_hours/24:.1f} days before close")
    else:
        print(f"Entry timing: {entry_hours:.1f} hours before close")
    print(f"Threads: {num_threads}")
    print()
    
    # Load markets metadata
    markets_df = pd.read_csv(MARKETS_FILE)
    markets_df = markets_df[markets_df['closedTime'].notna()]
    markets_df['volume'] = pd.to_numeric(markets_df['volume'], errors='coerce')
    markets_df = markets_df[markets_df['volume'] >= min_volume]
    
    # Get cached market IDs
    cached_files = list(CACHE_DIR.glob("market_*.csv"))
    cached_ids = [int(f.stem.replace("market_", "")) for f in cached_files]
    
    # Filter to high-volume cached markets
    valid_ids = [mid for mid in cached_ids if mid in markets_df['id'].values]
    
    random.seed(seed)
    random.shuffle(valid_ids)
    
    print(f"[INFO] Cached markets: {len(cached_ids)}")
    print(f"[INFO] High-volume cached: {len(valid_ids)}")
    
    # Results tracking
    results = []
    skipped = {}
    trades = {"WIN": 0, "LOSS": 0, "NO_TRADE": 0}
    total_pnl = 0.0
    total_invested = 0.0
    
    print(f"\n[STEP 1] Analyzing markets (parallel)...")
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {
            executor.submit(
                analyze_single_market, 
                mid, 
                markets_df, 
                config, 
                entry_hours  # Changed to hours
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
                
                # Progress
                status = {"WIN": "[WIN]", "LOSS": "[LOSS]", "NO_TRADE": "[SKIP]"}.get(outcome, "[???]")
                print(f"  {len(results):3d}/{target_results} {status:7s} "
                      f"Dir={result['direction']:3s} Score={result['direction_score']:+.2f} "
                      f"| {result['question'][:35]}...")
                
            except Exception as e:
                skipped["thread_error"] = skipped.get("thread_error", 0) + 1
    
    # Summary
    print("\n" + "=" * 80)
    print("BACKTEST RESULTS")
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
    
    # Statistical significance
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
    
    # Breakdown by signal strength
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
    
    # Save results
    summary = {
        "config": {
            "entry_hours": entry_hours,
            "min_direction_score": config.min_direction_score,
            "base_position_pct": config.base_position_pct,
            "max_position_pct": config.max_position_pct,
            "max_entry_price": config.max_entry_price
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
            "p_value": p_value,
            "skipped": skipped
        },
        "results": results
    }
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"strategy_backtest_{timestamp}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\n\nResults saved to: {output_file}")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Strategy Backtest V3 (Multi-threaded)")
    parser.add_argument("--target", type=int, default=200, help="Target number of valid results")
    parser.add_argument("--threads", type=int, default=8, help="Number of threads")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--hours", type=float, default=1.0, help="Hours before close (default: 1 hour)")
    parser.add_argument("--days", type=float, default=None, help="Days before close (alternative to --hours)")
    parser.add_argument("--volume", type=float, default=100000, help="Min volume")
    parser.add_argument("--score", type=float, default=0.15, help="Min direction score")
    args = parser.parse_args()
    
    # Convert days to hours if specified
    if args.days is not None:
        entry_hours = args.days * 24
    else:
        entry_hours = args.hours
    
    config = StrategyConfig(min_direction_score=args.score)
    
    run_parallel_backtest(
        target_results=args.target,
        entry_hours=entry_hours,
        config=config,
        min_volume=args.volume,
        seed=args.seed,
        num_threads=args.threads
    )
