"""
Insider Trading Strategy

Based on findings from BACKTEST_REPORT.md:
1. Daily direction signals from insider activity
2. Incremental flow analysis for entry timing
3. Position sizing based on signal strength

Strategy Components:
- Entry Signal: When insider direction score exceeds threshold
- Entry Timing: Based on signal stability and strength trend
- Position Sizing: Based on direction score confidence
- Exit Rules: Pre-event exit to avoid slippage

Author: Claude
Date: 2025-02-03
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from enum import Enum

sys.stdout.reconfigure(encoding='utf-8')

from insider_analyzer import InsiderDirectionAnalyzer, AnalysisConfig
from data_extractor import MarketDataExtractor


# =============================================================================
# Strategy Configuration
# =============================================================================

class SignalStrength(Enum):
    """Signal strength levels for position sizing."""
    NONE = 0
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    EXTREME = 4


@dataclass
class StrategyConfig:
    """Trading strategy parameters."""
    
    # Entry thresholds
    min_direction_score: float = 0.15       # Minimum direction score to consider
    strong_signal_threshold: float = 0.30   # Strong signal threshold
    
    # Timing parameters
    min_signal_days: int = 3                # Need at least N days of consistent signal
    signal_consistency: float = 0.6         # 60% of days must agree with overall signal
    
    # Position sizing (as % of capital)
    base_position_pct: float = 0.05         # 5% base position
    max_position_pct: float = 0.20          # 20% max position
    
    # Price constraints
    max_entry_price: float = 0.70           # Don't buy if price > 70%
    min_entry_price: float = 0.10           # Don't buy if price < 10%
    
    # Exit timing
    exit_hours_before_close: int = 2        # Exit 2 hours before market close
    
    # Insider analysis config
    insider_min_score: int = 80
    insider_lookback_days: int = 30


@dataclass
class TradingSignal:
    """Represents a trading signal for a market."""
    market_id: int
    timestamp: datetime
    
    # Direction
    direction: str              # "YES", "NO", or "NEUTRAL"
    direction_score: float      # -1 to +1
    
    # Confidence metrics
    signal_strength: SignalStrength
    days_consistent: int        # How many days signal has been consistent
    insider_count: int          # Number of insiders supporting this direction
    
    # Recommended action
    recommended_action: str     # "BUY_YES", "BUY_NO", "HOLD", "EXIT"
    position_size_pct: float    # Recommended position size as % of capital
    max_entry_price: float      # Maximum price to pay
    
    # Context
    market_question: str = ""
    current_price: Optional[float] = None
    
    def to_dict(self) -> dict:
        return {
            "market_id": self.market_id,
            "timestamp": self.timestamp.isoformat(),
            "direction": self.direction,
            "direction_score": round(self.direction_score, 4),
            "signal_strength": self.signal_strength.name,
            "days_consistent": self.days_consistent,
            "insider_count": self.insider_count,
            "recommended_action": self.recommended_action,
            "position_size_pct": round(self.position_size_pct, 4),
            "max_entry_price": round(self.max_entry_price, 4),
            "market_question": self.market_question,
            "current_price": self.current_price
        }


# =============================================================================
# Entry Price Calculator
# =============================================================================

class EntryPriceCalculator:
    """
    Calculate optimal entry price based on:
    1. Direction score (higher score = willing to pay more)
    2. Position sizing (larger position = need better price)
    3. Market liquidity (implicit)
    
    Philosophy:
    - At 50% direction score, fair value is ~65-70%
    - Strong signals (80%+) suggest fair value ~75-85%
    - We want to buy BELOW fair value for edge
    """
    
    def __init__(self, config: StrategyConfig):
        self.config = config
    
    def calculate(
        self, 
        direction_score: float,
        signal_strength: SignalStrength,
        current_price: Optional[float] = None
    ) -> Tuple[float, float]:
        """
        Calculate entry price range.
        
        Returns:
            (target_price, max_price) - target to aim for, max willing to pay
        """
        # Base fair value estimation from direction score
        # direction_score: -1 to +1
        # If +0.5, implies ~70-75% probability
        abs_score = abs(direction_score)
        
        # Map direction score to implied probability
        # 0.1 -> 55%, 0.3 -> 65%, 0.5 -> 75%, 0.8 -> 85%
        implied_prob = 0.50 + (abs_score * 0.40)  # 50% to 90% range
        
        # We want to buy below implied probability for edge
        # Edge target: 5-15% below fair value
        if signal_strength == SignalStrength.EXTREME:
            edge_discount = 0.05  # 5% discount - willing to pay more for extreme signals
        elif signal_strength == SignalStrength.STRONG:
            edge_discount = 0.08  # 8% discount
        elif signal_strength == SignalStrength.MODERATE:
            edge_discount = 0.12  # 12% discount
        else:
            edge_discount = 0.15  # 15% discount for weak signals
        
        target_price = implied_prob * (1 - edge_discount)
        max_price = min(implied_prob, self.config.max_entry_price)
        
        # Clamp to config limits
        target_price = max(self.config.min_entry_price, min(target_price, self.config.max_entry_price))
        max_price = max(self.config.min_entry_price, min(max_price, self.config.max_entry_price))
        
        return target_price, max_price
    
    def should_enter(
        self, 
        current_price: float, 
        max_price: float
    ) -> Tuple[bool, str]:
        """
        Determine if current price is good for entry.
        
        Returns:
            (should_buy, reason)
        """
        if current_price <= 0 or current_price >= 1:
            return False, "Invalid price"
        
        if current_price > self.config.max_entry_price:
            return False, f"Price {current_price:.2%} exceeds max {self.config.max_entry_price:.0%}"
        
        if current_price < self.config.min_entry_price:
            return False, f"Price {current_price:.2%} too low, possible dead market"
        
        if current_price <= max_price:
            discount = (max_price - current_price) / max_price
            return True, f"Good entry: {discount:.1%} below max price"
        else:
            premium = (current_price - max_price) / max_price
            return False, f"Too expensive: {premium:.1%} above max price"


# =============================================================================
# Position Sizer
# =============================================================================

class PositionSizer:
    """
    Calculate position size based on:
    1. Signal strength
    2. Signal consistency
    3. Price attractiveness
    
    Uses a tiered approach:
    - Weak signal: base position
    - Moderate: 1.5x base
    - Strong: 2x base
    - Extreme: 3x base (capped at max)
    """
    
    def __init__(self, config: StrategyConfig):
        self.config = config
    
    def calculate(
        self, 
        signal_strength: SignalStrength,
        days_consistent: int,
        entry_discount: float = 0.0
    ) -> float:
        """
        Calculate position size as percentage of capital.
        
        Args:
            signal_strength: Signal strength level
            days_consistent: Days of consistent signal
            entry_discount: How much below max price (0.1 = 10% discount)
        
        Returns:
            Position size as percentage (0.0 to max_position_pct)
        """
        base = self.config.base_position_pct
        
        # Signal strength multiplier
        if signal_strength == SignalStrength.EXTREME:
            strength_mult = 3.0
        elif signal_strength == SignalStrength.STRONG:
            strength_mult = 2.0
        elif signal_strength == SignalStrength.MODERATE:
            strength_mult = 1.5
        else:
            strength_mult = 1.0
        
        # Consistency bonus (up to 50% extra for 10+ days consistent)
        consistency_mult = 1.0 + min(0.5, days_consistent / 20.0)
        
        # Price bonus (up to 30% extra for 15%+ discount)
        price_mult = 1.0 + min(0.3, entry_discount * 2)
        
        position = base * strength_mult * consistency_mult * price_mult
        
        # Cap at maximum
        return min(position, self.config.max_position_pct)


# =============================================================================
# Trading Strategy Engine
# =============================================================================

class InsiderTradingStrategy:
    """
    Main strategy class that combines:
    - Insider direction analysis
    - Entry timing
    - Entry price calculation
    - Position sizing
    
    Usage:
        strategy = InsiderTradingStrategy()
        signal = strategy.analyze_market(market_id, current_price=0.55)
        if signal.recommended_action.startswith("BUY"):
            execute_trade(...)
    """
    
    def __init__(self, config: StrategyConfig = None):
        self.config = config or StrategyConfig()
        
        # Initialize components
        self.analyzer = InsiderDirectionAnalyzer(AnalysisConfig(
            min_insider_score=self.config.insider_min_score,
            lookback_days=self.config.insider_lookback_days
        ))
        self.price_calc = EntryPriceCalculator(self.config)
        self.position_sizer = PositionSizer(self.config)
        self.extractor = MarketDataExtractor()
    
    def _calculate_signal_strength(
        self, 
        direction_score: float, 
        days_consistent: int,
        insider_count: int
    ) -> SignalStrength:
        """Determine signal strength from metrics."""
        abs_score = abs(direction_score)
        
        # Score-based thresholds
        if abs_score >= 0.50 and days_consistent >= 5 and insider_count >= 15:
            return SignalStrength.EXTREME
        elif abs_score >= 0.30 and days_consistent >= 3 and insider_count >= 8:
            return SignalStrength.STRONG
        elif abs_score >= 0.15 and days_consistent >= 2 and insider_count >= 3:
            return SignalStrength.MODERATE
        elif abs_score >= 0.10:
            return SignalStrength.WEAK
        else:
            return SignalStrength.NONE
    
    def _count_consistent_days(self, daily_results: List[dict], overall_direction: str) -> int:
        """Count how many recent days are consistent with overall signal."""
        if not daily_results or overall_direction == "NEUTRAL":
            return 0
        
        # Look at last N days
        recent = daily_results[-10:]  # Last 10 days
        consistent = 0
        
        for day in recent:
            signal = day.get("signal", "NEUTRAL")
            if overall_direction == "YES" and signal in ["YES", "STRONG_YES"]:
                consistent += 1
            elif overall_direction == "NO" and signal in ["NO", "STRONG_NO"]:
                consistent += 1
        
        return consistent
    
    def analyze_market(
        self, 
        market_id: int,
        current_price: Optional[float] = None,
        simulation_time: Optional[datetime] = None
    ) -> TradingSignal:
        """
        Analyze a market and generate trading signal.
        
        Args:
            market_id: Polymarket market ID
            current_price: Current YES price (0-1), if available
            simulation_time: For backtesting - treat this as "now"
        
        Returns:
            TradingSignal with all recommendation details
        """
        # Get market info
        market_info = self.extractor.get_market_info(market_id)
        question = str(market_info.get('question', 'Unknown'))[:80] if market_info is not None else "Unknown"
        
        # Get close time for analysis window
        closed_time = simulation_time or self.extractor.get_closed_time(market_id)
        if closed_time is None:
            closed_time = datetime.now()
        
        # Get trades and analyze
        trades_df = self.extractor.extract_single_market(market_id, use_cache=True)
        
        if trades_df is None or len(trades_df) < 50:
            return TradingSignal(
                market_id=market_id,
                timestamp=datetime.now(),
                direction="NEUTRAL",
                direction_score=0.0,
                signal_strength=SignalStrength.NONE,
                days_consistent=0,
                insider_count=0,
                recommended_action="HOLD",
                position_size_pct=0.0,
                max_entry_price=0.0,
                market_question=question,
                current_price=current_price
            )
        
        # Run insider analysis
        analysis = self.analyzer.analyze_market(
            trades_df,
            closed_time=closed_time,
            return_daily=True
        )
        
        # Extract key metrics
        direction_score = analysis.get("direction_score", 0)
        predicted = analysis.get("predicted", "NEUTRAL")
        daily_results = analysis.get("daily_results", [])
        total_insiders = analysis.get("total_insiders", 0)
        
        # Calculate derived metrics
        days_consistent = self._count_consistent_days(daily_results, predicted)
        signal_strength = self._calculate_signal_strength(
            direction_score, days_consistent, total_insiders
        )
        
        # Calculate entry price
        target_price, max_price = self.price_calc.calculate(
            direction_score, signal_strength, current_price
        )
        
        # Calculate position size
        entry_discount = 0.0
        if current_price is not None and max_price > 0:
            entry_discount = max(0, (max_price - current_price) / max_price)
        
        position_pct = self.position_sizer.calculate(
            signal_strength, days_consistent, entry_discount
        )
        
        # Determine action
        if signal_strength == SignalStrength.NONE:
            action = "HOLD"
            position_pct = 0.0
        elif abs(direction_score) < self.config.min_direction_score:
            action = "HOLD"
            position_pct = 0.0
        elif current_price is not None:
            should_enter, reason = self.price_calc.should_enter(current_price, max_price)
            if should_enter:
                action = f"BUY_{predicted}" if predicted != "NEUTRAL" else "HOLD"
            else:
                action = "WAIT"  # Wait for better price
        else:
            action = f"BUY_{predicted}" if predicted != "NEUTRAL" else "HOLD"
        
        return TradingSignal(
            market_id=market_id,
            timestamp=datetime.now(),
            direction=predicted,
            direction_score=direction_score,
            signal_strength=signal_strength,
            days_consistent=days_consistent,
            insider_count=total_insiders,
            recommended_action=action,
            position_size_pct=position_pct,
            max_entry_price=max_price,
            market_question=question,
            current_price=current_price
        )
    
    def backtest_market(
        self,
        market_id: int,
        entry_days_before_close: int = 7
    ) -> Dict:
        """
        Backtest strategy on a historical market.
        
        Simulates:
        1. Generate signal N days before close
        2. Check if entry conditions were met
        3. Calculate PnL based on outcome
        
        Args:
            market_id: Market to backtest
            entry_days_before_close: Days before close to generate signal
        
        Returns:
            Backtest result with signal, entry, and PnL details
        """
        # Get market info
        closed_time = self.extractor.get_closed_time(market_id)
        if closed_time is None:
            return {"error": "No close time found"}
        
        # Set simulation time to N days before close
        simulation_time = closed_time - timedelta(days=entry_days_before_close)
        
        # Get trades up to simulation time
        trades_df = self.extractor.extract_single_market(market_id, use_cache=True)
        if trades_df is None or len(trades_df) < 50:
            return {"error": "Insufficient trades"}
        
        trades_df = trades_df.copy()
        trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'], errors='coerce')
        if trades_df['timestamp'].dt.tz is not None:
            trades_df['timestamp'] = trades_df['timestamp'].dt.tz_localize(None)
        
        # Filter to trades before simulation time
        pre_sim_trades = trades_df[trades_df['timestamp'] < simulation_time]
        
        # Get price at simulation time (average of last 10 trades)
        last_trades = pre_sim_trades.tail(10)
        yes_trades = last_trades[last_trades['nonusdc_side'] == 'token1']
        if len(yes_trades) > 0:
            sim_price = float(yes_trades['price'].mean())
        else:
            sim_price = 0.50
        
        # Generate signal at simulation time
        signal = self.analyze_market(
            market_id, 
            current_price=sim_price,
            simulation_time=simulation_time
        )
        
        # Infer actual outcome from final trades
        from batch_validation import infer_market_winner
        actual_winner = infer_market_winner(trades_df)
        
        # Calculate hypothetical PnL
        if signal.recommended_action.startswith("BUY_"):
            bet_direction = signal.recommended_action.replace("BUY_", "")
            entry_price = min(sim_price, signal.max_entry_price)
            
            if bet_direction == actual_winner:
                # Won: payout is 1.0 per share
                pnl_per_dollar = (1.0 / entry_price) - 1.0
                outcome = "WIN"
            elif actual_winner is not None:
                # Lost: lose entry
                pnl_per_dollar = -1.0
                outcome = "LOSS"
            else:
                pnl_per_dollar = 0.0
                outcome = "UNKNOWN"
        else:
            pnl_per_dollar = 0.0
            outcome = "NO_TRADE"
            entry_price = None
            bet_direction = None
        
        return {
            "market_id": market_id,
            "market_question": signal.market_question,
            "simulation_time": simulation_time.isoformat(),
            "closed_time": closed_time.isoformat(),
            "days_before_close": entry_days_before_close,
            "signal": signal.to_dict(),
            "sim_price": round(sim_price, 4),
            "entry_price": round(entry_price, 4) if entry_price else None,
            "bet_direction": bet_direction,
            "actual_winner": actual_winner,
            "outcome": outcome,
            "pnl_per_dollar": round(pnl_per_dollar, 4) if pnl_per_dollar else 0,
            "position_pct": round(signal.position_size_pct, 4)
        }


# =============================================================================
# CLI Interface
# =============================================================================

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def print_signal(signal: TradingSignal):
    """Pretty print a trading signal."""
    print("\n" + "=" * 70)
    print(f"TRADING SIGNAL: Market {signal.market_id}")
    print("=" * 70)
    print(f"Question: {signal.market_question}")
    print(f"Timestamp: {signal.timestamp.strftime('%Y-%m-%d %H:%M')}")
    print()
    print(f"[DIRECTION]")
    print(f"  Signal: {signal.direction}")
    print(f"  Score: {signal.direction_score:+.4f}")
    print(f"  Strength: {signal.signal_strength.name}")
    print(f"  Days Consistent: {signal.days_consistent}")
    print(f"  Insider Count: {signal.insider_count}")
    print()
    print(f"[TRADING]")
    print(f"  Action: {signal.recommended_action}")
    print(f"  Position Size: {signal.position_size_pct:.1%}")
    print(f"  Max Entry Price: {signal.max_entry_price:.2%}")
    if signal.current_price:
        print(f"  Current Price: {signal.current_price:.2%}")
        if signal.current_price <= signal.max_entry_price:
            discount = (signal.max_entry_price - signal.current_price) / signal.max_entry_price
            print(f"  [GOOD ENTRY] {discount:.1%} below max price")
        else:
            premium = (signal.current_price - signal.max_entry_price) / signal.max_entry_price
            print(f"  [TOO EXPENSIVE] {premium:.1%} above max price")
    print("=" * 70)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Insider Trading Strategy")
    parser.add_argument("--market", type=int, help="Market ID to analyze")
    parser.add_argument("--price", type=float, help="Current YES price (0-1)")
    parser.add_argument("--backtest", action="store_true", help="Run backtest mode")
    parser.add_argument("--days", type=int, default=7, help="Days before close for backtest")
    args = parser.parse_args()
    
    strategy = InsiderTradingStrategy()
    
    if args.market:
        if args.backtest:
            print(f"[BACKTEST] Market {args.market}, {args.days} days before close")
            result = strategy.backtest_market(args.market, entry_days_before_close=args.days)
            print(json.dumps(result, indent=2))
            
            # Save result
            output_file = OUTPUT_DIR / f"backtest_{args.market}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            print(f"\nSaved to: {output_file}")
        else:
            print(f"[ANALYZE] Market {args.market}")
            signal = strategy.analyze_market(args.market, current_price=args.price)
            print_signal(signal)
            
            # Save signal
            output_file = OUTPUT_DIR / f"signal_{args.market}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(signal.to_dict(), f, indent=2)
            print(f"\nSaved to: {output_file}")
    else:
        print("Usage:")
        print("  Analyze: python trading_strategy.py --market 253591 --price 0.55")
        print("  Backtest: python trading_strategy.py --market 253591 --backtest --days 7")
