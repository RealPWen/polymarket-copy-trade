"""
Strategy Backtest - Batch Testing on Random Markets

Test the insider trading strategy on N random resolved markets.
Calculate overall accuracy, ROI, and statistical significance.

Usage:
    python strategy_backtest.py --sample 200 --seed 42 --days 7
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
from typing import List, Dict, Optional

sys.stdout.reconfigure(encoding='utf-8')

from data_extractor import MarketDataExtractor
from trading_strategy import InsiderTradingStrategy, StrategyConfig


OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def sample_markets(
    extractor: MarketDataExtractor,
    sample_size: int,
    min_volume: float,
    seed: int
) -> List[int]:
    """Sample random resolved markets for testing."""
    random.seed(seed)
    
    df = extractor.markets_df.copy()
    
    # Filter for resolved markets
    df = df[df['closedTime'].notna()]
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
    df = df[df['volume'] >= min_volume]
    
    # Get market IDs
    available = list(df['id'].astype(int))
    print(f"[INFO] Available resolved markets with volume >= ${min_volume:,.0f}: {len(available)}")
    
    # Sample more than needed (some will fail)
    sample = random.sample(available, min(sample_size * 3, len(available)))
    
    return sample


def run_batch_backtest(
    market_ids: List[int],
    entry_days: int,
    max_markets: int,
    config: StrategyConfig
) -> Dict:
    """
    Run backtest on multiple markets.
    
    Returns summary statistics and individual results.
    """
    print("=" * 80)
    print("STRATEGY BACKTEST")
    print("=" * 80)
    print(f"Markets to test: {len(market_ids)} (target: {max_markets})")
    print(f"Entry timing: {entry_days} days before close")
    print(f"Min direction score: {config.min_direction_score}")
    print()
    
    strategy = InsiderTradingStrategy(config)
    
    results = []
    trades = {"WIN": 0, "LOSS": 0, "NO_TRADE": 0, "UNKNOWN": 0}
    total_pnl = 0.0
    total_invested = 0.0
    
    skipped = {"no_trades": 0, "error": 0, "no_close_time": 0}
    
    for idx, market_id in enumerate(market_ids, 1):
        if len(results) >= max_markets:
            break
        
        try:
            result = strategy.backtest_market(market_id, entry_days_before_close=entry_days)
            
            if "error" in result:
                skipped["error"] += 1
                continue
            
            # Track results
            outcome = result.get("outcome", "UNKNOWN")
            trades[outcome] = trades.get(outcome, 0) + 1
            
            if outcome in ["WIN", "LOSS"]:
                position_pct = result.get("position_pct", 0)
                pnl_per_dollar = result.get("pnl_per_dollar", 0)
                
                # Simulate $10,000 capital
                position_value = 10000 * position_pct
                pnl = position_value * pnl_per_dollar
                
                result["position_value"] = round(position_value, 2)
                result["pnl_dollars"] = round(pnl, 2)
                
                total_invested += position_value
                total_pnl += pnl
            
            results.append(result)
            
            # Progress output
            status_icon = {
                "WIN": "[WIN]",
                "LOSS": "[LOSS]",
                "NO_TRADE": "[SKIP]",
                "UNKNOWN": "[???]"
            }.get(outcome, "[???]")
            
            signal = result.get("signal", {})
            direction = signal.get("direction", "N/A")
            score = signal.get("direction_score", 0)
            
            print(f"  {len(results):3d}/{max_markets} {status_icon:7s} "
                  f"Dir={direction:3s} Score={score:+.2f} "
                  f"| {result.get('market_question', '')[:40]}...")
            
        except Exception as e:
            skipped["error"] += 1
            continue
    
    # Calculate summary statistics
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
    print(f"  No Trade (NEUTRAL signal): {trades['NO_TRADE']}")
    
    print(f"\n[PNL SIMULATION] ($10,000 capital)")
    print(f"  Total Invested: ${total_invested:,.2f}")
    print(f"  Total PnL: ${total_pnl:,.2f}")
    if total_invested > 0:
        roi = total_pnl / total_invested
        print(f"  ROI on Invested: {roi:.1%}")
    
    print(f"\n[SKIPPED]")
    print(f"  Errors: {skipped['error']}")
    
    # Statistical significance
    if total_trades >= 10:
        try:
            from scipy import stats
            result_test = stats.binomtest(trades["WIN"], total_trades, 0.5, alternative='greater')
            p_value = result_test.pvalue
            print(f"\n[STATISTICAL SIGNIFICANCE]")
            print(f"  P-value (vs 50% baseline): {p_value:.4f}")
            print(f"  Significant at 5%: {'YES' if p_value < 0.05 else 'NO'}")
            print(f"  Significant at 1%: {'YES' if p_value < 0.01 else 'NO'}")
        except Exception:
            p_value = None
    else:
        p_value = None
    
    # Breakdown by signal strength
    print("\n[BREAKDOWN BY SIGNAL STRENGTH]")
    for strength in ["EXTREME", "STRONG", "MODERATE", "WEAK"]:
        strength_results = [r for r in results 
                          if r.get("signal", {}).get("signal_strength") == strength 
                          and r.get("outcome") in ["WIN", "LOSS"]]
        if strength_results:
            wins = sum(1 for r in strength_results if r["outcome"] == "WIN")
            total = len(strength_results)
            acc = wins / total * 100
            print(f"  {strength:12s}: {wins}/{total} ({acc:.0f}%)")
    
    # Save results
    summary = {
        "config": {
            "entry_days_before_close": entry_days,
            "min_direction_score": config.min_direction_score,
            "strong_signal_threshold": config.strong_signal_threshold,
            "base_position_pct": config.base_position_pct,
            "max_position_pct": config.max_position_pct,
            "max_entry_price": config.max_entry_price
        },
        "summary": {
            "total_markets_analyzed": len(results),
            "total_trades": total_trades,
            "wins": trades["WIN"],
            "losses": trades["LOSS"],
            "no_trade": trades["NO_TRADE"],
            "win_rate": round(win_rate, 4),
            "total_invested": round(total_invested, 2),
            "total_pnl": round(total_pnl, 2),
            "roi": round(total_pnl / total_invested, 4) if total_invested > 0 else 0,
            "p_value": p_value
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
    parser = argparse.ArgumentParser(description="Strategy Backtest on Random Markets")
    parser.add_argument("--sample", type=int, default=200, help="Number of markets to test")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--days", type=int, default=7, help="Days before close to enter")
    parser.add_argument("--volume", type=float, default=50000, help="Minimum market volume")
    parser.add_argument("--score", type=float, default=0.15, help="Min direction score")
    args = parser.parse_args()
    
    # Initialize
    extractor = MarketDataExtractor()
    
    config = StrategyConfig(
        min_direction_score=args.score
    )
    
    # Sample markets
    print(f"[STEP 1] Sampling markets...")
    market_ids = sample_markets(
        extractor,
        sample_size=args.sample,
        min_volume=args.volume,
        seed=args.seed
    )
    
    # Run backtest
    print(f"\n[STEP 2] Running backtest...")
    run_batch_backtest(
        market_ids=market_ids,
        entry_days=args.days,
        max_markets=args.sample,
        config=config
    )
