"""
Strategy Backtest V2 - Optimized Batch Testing

Key optimization: Extract ALL market trades in a SINGLE pass through the 35GB file.

Usage:
    python strategy_backtest_v2.py --sample 200 --seed 42 --days 7
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
from insider_analyzer import InsiderDirectionAnalyzer, AnalysisConfig
from trading_strategy import (
    InsiderTradingStrategy, StrategyConfig, 
    EntryPriceCalculator, PositionSizer, SignalStrength
)


OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def infer_market_winner(trades_df: pd.DataFrame) -> Optional[str]:
    """Infer winning side from final trades - improved version."""
    try:
        trades_df = trades_df.copy()
        trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'], errors='coerce')
        trades_df = trades_df.dropna(subset=['timestamp'])
        
        if len(trades_df) < 10:
            return None
        
        last_trades = trades_df.sort_values('timestamp').tail(50)
        
        # Check YES (token1) trades with relaxed threshold
        yes_trades = last_trades[last_trades['nonusdc_side'] == 'token1']
        if len(yes_trades) >= 2:
            avg_yes_price = yes_trades['price'].astype(float).mean()
            if avg_yes_price > 0.75:  # Relaxed from 0.85
                return "YES"
            elif avg_yes_price < 0.25:  # Relaxed from 0.15
                return "NO"
        
        # Check NO (token0) trades
        no_trades = last_trades[last_trades['nonusdc_side'] == 'token0']
        if len(no_trades) >= 2:
            avg_no_price = no_trades['price'].astype(float).mean()
            if avg_no_price > 0.75:
                return "NO"
            elif avg_no_price < 0.25:
                return "YES"
        
        # Fallback: check absolute final price
        if len(yes_trades) >= 1:
            final_price = float(yes_trades.iloc[-1]['price'])
            if final_price > 0.70:
                return "YES"
            elif final_price < 0.30:
                return "NO"
        
        return None
    except:
        return None


def sample_markets(
    extractor: MarketDataExtractor,
    sample_size: int,
    min_volume: float,
    seed: int
) -> List[int]:
    """Sample random resolved markets."""
    random.seed(seed)
    
    df = extractor.markets_df.copy()
    df = df[df['closedTime'].notna()]
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
    df = df[df['volume'] >= min_volume]
    
    available = list(df['id'].astype(int))
    print(f"[INFO] Available resolved markets: {len(available)}")
    
    # Sample 5x to account for failures with strict conditions
    sample = random.sample(available, min(sample_size * 5, len(available)))
    return sample


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


def run_batch_backtest(
    market_ids: List[int],
    entry_days: int,
    max_markets: int,
    config: StrategyConfig
) -> Dict:
    """
    Optimized batch backtest:
    1. Extract ALL market data in single pass
    2. Analyze each market
    3. Calculate strategy performance
    """
    print("=" * 80)
    print("STRATEGY BACKTEST V2 (Optimized)")
    print("=" * 80)
    print(f"Target markets: {max_markets}")
    print(f"Entry timing: {entry_days} days before close")
    print()
    
    extractor = MarketDataExtractor()
    analyzer = InsiderDirectionAnalyzer(AnalysisConfig(
        min_insider_score=config.insider_min_score,
        lookback_days=config.insider_lookback_days
    ))
    price_calc = EntryPriceCalculator(config)
    position_sizer = PositionSizer(config)
    
    # Step 1: Batch extract all market data
    print("[STEP 1] Extracting market data (single pass)...")
    trades_data = extractor.extract_multiple_markets(
        market_ids,
        use_cache=True,
        min_trades=100
    )
    print(f"[INFO] Markets with trades: {len(trades_data)}")
    
    # Step 2: Analyze each market
    print("\n[STEP 2] Analyzing markets...")
    results = []
    trades = {"WIN": 0, "LOSS": 0, "NO_TRADE": 0, "UNKNOWN": 0}
    total_pnl = 0.0
    total_invested = 0.0
    skipped = {"no_close": 0, "no_winner": 0, "no_signal": 0, "error": 0}
    
    for market_id, trades_df in trades_data.items():
        if len(results) >= max_markets:
            break
        
        try:
            # Get market info
            market_info = extractor.get_market_info(market_id)
            if market_info is None:
                skipped["error"] += 1
                continue
            
            question = str(market_info.get('question', 'Unknown'))[:60]
            closed_time = extractor.get_closed_time(market_id)
            
            if closed_time is None:
                skipped["no_close"] += 1
                continue
            
            # Set simulation time to N days before close
            simulation_time = closed_time - timedelta(days=entry_days)
            
            # Prepare trades
            trades_df = trades_df.copy()
            trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'], errors='coerce')
            if trades_df['timestamp'].dt.tz is not None:
                trades_df['timestamp'] = trades_df['timestamp'].dt.tz_localize(None)
            
            # Get actual winner
            actual_winner = infer_market_winner(trades_df)
            if actual_winner is None:
                skipped["no_winner"] += 1
                continue
            
            # Get YES price at simulation time
            pre_sim = trades_df[trades_df['timestamp'] < simulation_time]
            if len(pre_sim) < 50:
                skipped["error"] += 1
                continue
            
            last_trades = pre_sim.tail(10)
            yes_trades = last_trades[last_trades['nonusdc_side'] == 'token1']
            yes_price = float(yes_trades['price'].mean()) if len(yes_trades) > 0 else 0.50
            
            # Run insider analysis
            analysis = analyzer.analyze_market(
                trades_df,
                closed_time=simulation_time,
                return_daily=True
            )
            
            if analysis.get("signal") == "NO_DATA":
                skipped["no_signal"] += 1
                continue
            
            direction_score = analysis.get("direction_score", 0)
            predicted = analysis.get("predicted", "NEUTRAL")
            daily_results = analysis.get("daily_results", [])
            total_insiders = analysis.get("total_insiders", 0)
            
            if predicted == "NEUTRAL" or abs(direction_score) < config.min_direction_score:
                skipped["no_signal"] += 1
                continue
            
            # CRITICAL: Use correct price based on direction
            # If buying YES, use yes_price; if buying NO, use no_price (1 - yes_price)
            if predicted == "YES":
                sim_price = yes_price
            else:  # predicted == "NO"
                sim_price = 1.0 - yes_price  # NO price = 1 - YES price
            
            # Calculate signal metrics
            days_consistent = count_consistent_days(daily_results, predicted)
            signal_strength = calculate_signal_strength(direction_score, days_consistent, total_insiders)
            
            # Calculate entry price (based on direction-correct price)
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
            
            trades[outcome] += 1
            
            # Calculate dollar PnL (simulate $10,000 capital)
            if outcome in ["WIN", "LOSS"]:
                position_value = 10000 * position_pct
                pnl = position_value * pnl_per_dollar
                total_invested += position_value
                total_pnl += pnl
            else:
                position_value = 0
                pnl = 0
            
            result = {
                "market_id": market_id,
                "question": question,
                "simulation_time": simulation_time.isoformat(),
                "closed_time": closed_time.isoformat(),
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
            }
            results.append(result)
            
            # Progress output
            status = {"WIN": "[WIN]", "LOSS": "[LOSS]", "NO_TRADE": "[SKIP]"}.get(outcome, "[???]")
            print(f"  {len(results):3d}/{max_markets} {status:7s} "
                  f"Dir={predicted:3s} Score={direction_score:+.2f} "
                  f"Str={signal_strength.name[:4]} | {question[:35]}...")
            
        except Exception as e:
            skipped["error"] += 1
            continue
    
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
    for k, v in skipped.items():
        if v > 0:
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
            "entry_days": entry_days,
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
    parser = argparse.ArgumentParser(description="Strategy Backtest V2")
    parser.add_argument("--sample", type=int, default=200, help="Number of markets")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--days", type=int, default=7, help="Days before close")
    parser.add_argument("--volume", type=float, default=50000, help="Min volume")
    parser.add_argument("--score", type=float, default=0.15, help="Min direction score")
    args = parser.parse_args()
    
    extractor = MarketDataExtractor()
    config = StrategyConfig(min_direction_score=args.score)
    
    print(f"[STEP 1] Sampling {args.sample} markets...")
    market_ids = sample_markets(extractor, args.sample, args.volume, args.seed)
    
    print(f"\n[STEP 2] Running backtest...")
    run_batch_backtest(market_ids, args.days, args.sample, config)
