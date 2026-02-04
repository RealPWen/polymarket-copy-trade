"""
Batch Market Validation

Main entry point for validating insider direction strategy across multiple markets.

Flow:
1. Load market list from markets.csv
2. Sample/select markets for testing
3. Use DataExtractor to get trades (with caching)
4. Use InsiderDirectionAnalyzer to analyze each market
5. Compare predictions to actual outcomes
6. Report accuracy and significance

Usage:
    python batch_validation.py --sample 50 --seed 42
    python batch_validation.py --markets 253591,504603
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
from typing import List, Optional

sys.stdout.reconfigure(encoding='utf-8')

# Import our modules
from data_extractor import MarketDataExtractor
from insider_analyzer import InsiderDirectionAnalyzer, AnalysisConfig

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# =============================================================================
# Winner Detection
# =============================================================================

def infer_market_winner(trades_df: pd.DataFrame) -> Optional[str]:
    """
    Infer the winning side from final trades.
    If YES price -> 1.0, YES won. If -> 0.0, NO won.
    """
    try:
        trades_df = trades_df.copy()
        trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'], errors='coerce')
        trades_df = trades_df.dropna(subset=['timestamp'])
        
        if len(trades_df) < 10:
            return None
        
        last_trades = trades_df.sort_values('timestamp').tail(20)
        
        # Check YES (token1) trades
        yes_trades = last_trades[last_trades['nonusdc_side'] == 'token1']
        if len(yes_trades) >= 3:
            avg_yes_price = yes_trades['price'].astype(float).mean()
            if avg_yes_price > 0.85:
                return "YES"
            elif avg_yes_price < 0.15:
                return "NO"
        
        # Fallback: check NO trades
        no_trades = last_trades[last_trades['nonusdc_side'] == 'token0']
        if len(no_trades) >= 3:
            avg_no_price = no_trades['price'].astype(float).mean()
            if avg_no_price > 0.85:
                return "NO"
            elif avg_no_price < 0.15:
                return "YES"
        
        return None
    except:
        return None


# =============================================================================
# Main Validation
# =============================================================================

def run_validation(
    market_ids: List[int],
    config: AnalysisConfig,
    use_cache: bool = True
):
    """
    Run validation on specified markets.
    """
    print("=" * 80)
    print("BATCH MARKET VALIDATION")
    print("=" * 80)
    print(f"Markets to test: {len(market_ids)}")
    print(f"Min insider score: {config.min_insider_score}")
    print(f"Lookback days: {config.lookback_days}")
    print()
    
    # Initialize modules
    extractor = MarketDataExtractor()
    analyzer = InsiderDirectionAnalyzer(config)
    
    # Extract all market data
    print("[STEP 1] Extracting market data...")
    trades_data = extractor.extract_multiple_markets(
        market_ids, 
        use_cache=use_cache,
        min_trades=100
    )
    print(f"  Markets with data: {len(trades_data)}")
    
    # Analyze each market
    print("\n[STEP 2] Analyzing markets...")
    results = []
    skipped = {"no_trades": 0, "uncertain_outcome": 0, "no_insiders": 0}
    
    for idx, (market_id, trades_df) in enumerate(trades_data.items(), 1):
        market_info = extractor.get_market_info(market_id)
        if market_info is None:
            continue
        
        question = str(market_info.get('question', 'Unknown'))[:60]
        closed_time = extractor.get_closed_time(market_id)
        
        if closed_time is None:
            skipped["uncertain_outcome"] += 1
            continue
        
        # Get actual winner from final trades
        actual = infer_market_winner(trades_df)
        if actual is None:
            skipped["uncertain_outcome"] += 1
            continue
        
        # Run insider analysis
        analysis = analyzer.analyze_market(
            trades_df, 
            closed_time=closed_time,
            return_daily=True
        )
        
        if analysis.get("signal") == "NO_DATA":
            skipped["no_insiders"] += 1
            continue
        
        predicted = analysis.get("predicted", "NEUTRAL")
        if predicted == "NEUTRAL":
            skipped["no_insiders"] += 1
            continue
        
        correct = (predicted == actual)
        
        result = {
            "market_id": market_id,
            "question": question,
            "volume": float(market_info.get('volume', 0)),
            "total_trades": len(trades_df),
            "analyzed_trades": analysis.get("analyzed_trades", 0),
            "days_analyzed": analysis.get("days_analyzed", 0),
            "predicted": predicted,
            "actual": actual,
            "correct": correct,
            "direction_score": analysis.get("direction_score", 0),
            "signal": analysis.get("signal"),
            "yes_days": analysis.get("yes_days", 0),
            "no_days": analysis.get("no_days", 0),
            "total_insiders": analysis.get("total_insiders", 0)
        }
        results.append(result)
        
        # Progress output
        status = "[OK]" if correct else "[WRONG]"
        print(f"  {idx:3d}. {status} Pred={predicted:3s} Act={actual:3s} "
              f"Dir={analysis.get('direction_score',0):+.2f} "
              f"Days={analysis.get('days_analyzed',0):2d} | {question[:40]}...")
    
    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    
    if not results:
        print("\n[ERROR] No valid results!")
        print(f"Skipped - No trades: {skipped['no_trades']}")
        print(f"Skipped - Uncertain outcome: {skipped['uncertain_outcome']}")
        print(f"Skipped - No insider signal: {skipped['no_insiders']}")
        return None
    
    correct_count = sum(1 for r in results if r["correct"])
    total = len(results)
    accuracy = correct_count / total if total > 0 else 0
    
    print(f"\nMarkets analyzed: {total}")
    print(f"Correct predictions: {correct_count}")
    print(f"Accuracy: {accuracy * 100:.1f}%")
    print(f"\nSkipped markets:")
    print(f"  - Uncertain outcome: {skipped['uncertain_outcome']}")
    print(f"  - No insider signal: {skipped['no_insiders']}")
    
    # Significance test
    if total >= 10:
        try:
            from scipy import stats
            result = stats.binomtest(correct_count, total, 0.5, alternative='greater')
            p_value = result.pvalue
            print(f"\nStatistical Significance:")
            print(f"  P-value (vs 50% baseline): {p_value:.4f}")
            print(f"  Significant at 5%: {'YES' if p_value < 0.05 else 'NO'}")
        except:
            pass
    
    # Breakdown by signal strength
    print("\n\nBreakdown by Signal Strength:")
    for signal in ["STRONG_YES", "YES", "STRONG_NO", "NO"]:
        sig_results = [r for r in results if r["signal"] == signal]
        if sig_results:
            sig_correct = sum(1 for r in sig_results if r["correct"])
            sig_acc = sig_correct / len(sig_results) * 100
            print(f"  {signal:12s}: {sig_correct}/{len(sig_results)} ({sig_acc:.0f}%)")
    
    # Save results
    output = {
        "config": {
            "min_insider_score": config.min_insider_score,
            "min_wallet_volume": config.min_wallet_volume,
            "lookback_days": config.lookback_days
        },
        "summary": {
            "total_markets": total,
            "correct": correct_count,
            "accuracy": round(accuracy, 4),
            "skipped": skipped
        },
        "methodology": f"Daily insider signals from [close-{config.lookback_days}d, close-1h]. Aggregate signal from daily average.",
        "results": results
    }
    
    output_file = OUTPUT_DIR / "batch_validation_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n\nResults saved to: {output_file}")
    
    return output


def sample_markets(
    extractor: MarketDataExtractor,
    sample_size: int,
    min_volume: float,
    exclude_ids: List[int],
    seed: int
) -> List[int]:
    """
    Sample random resolved markets for testing.
    """
    random.seed(seed)
    
    df = extractor.markets_df
    
    # Filter
    df = df[df['closedTime'].notna()]
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
    df = df[df['volume'] >= min_volume]
    
    if exclude_ids:
        df = df[~df['id'].isin(exclude_ids)]
    
    # Sample
    available = list(df['id'].astype(int))
    sample = random.sample(available, min(sample_size * 3, len(available)))
    
    return sample


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch validate insider direction strategy")
    parser.add_argument("--sample", type=int, default=50, help="Number of random markets")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--volume", type=float, default=100000, help="Min market volume")
    parser.add_argument("--score", type=int, default=80, help="Min insider score")
    parser.add_argument("--lookback", type=int, default=30, help="Days before close")
    parser.add_argument("--markets", type=str, help="Specific market IDs (comma-separated)")
    parser.add_argument("--no-cache", action="store_true", help="Skip cache")
    args = parser.parse_args()
    
    config = AnalysisConfig(
        min_insider_score=args.score,
        lookback_days=args.lookback
    )
    
    extractor = MarketDataExtractor()
    
    if args.markets:
        # Specific markets
        market_ids = [int(x.strip()) for x in args.markets.split(",")]
    else:
        # Random sample
        exclude = [253591]  # Exclude Trump 2024
        market_ids = sample_markets(
            extractor,
            sample_size=args.sample,
            min_volume=args.volume,
            exclude_ids=exclude,
            seed=args.seed
        )
    
    run_validation(
        market_ids=market_ids,
        config=config,
        use_cache=not args.no_cache
    )
