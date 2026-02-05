"""
Signal Generator Module

Generates trading signals from analysis results.
Combines insider analysis with price and timing filters.
"""
import sys
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional, List
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Import from parent
sys.path.insert(0, str(Path(__file__).parent.parent))
from trading_strategy import SignalStrength, StrategyConfig, EntryPriceCalculator, PositionSizer


@dataclass
class LiveSignal:
    """A trading signal for a live market."""
    
    # Market info
    market_id: int
    question: str
    slug: str
    
    # Signal
    direction: str  # "YES" or "NO"
    direction_score: float  # -1.0 to +1.0
    signal_strength: SignalStrength
    
    # Analysis details
    days_consistent: int
    insider_count: int
    insider_volume: float
    
    # Timing
    hours_until_end: float
    analysis_time: datetime
    
    # Price info
    current_price: float  # Current price of predicted side
    max_entry_price: float  # Maximum price to enter
    target_price: float  # Target entry price
    
    # Position sizing
    position_pct: float  # Recommended position %
    
    # Actionability
    is_actionable: bool  # Whether to act on this signal
    rejection_reason: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "market_id": self.market_id,
            "question": self.question,
            "slug": self.slug,
            "direction": self.direction,
            "direction_score": round(self.direction_score, 4),
            "signal_strength": self.signal_strength.name,
            "days_consistent": self.days_consistent,
            "insider_count": self.insider_count,
            "insider_volume": round(self.insider_volume, 2),
            "hours_until_end": round(self.hours_until_end, 2),
            "analysis_time": self.analysis_time.isoformat(),
            "current_price": round(self.current_price, 4),
            "max_entry_price": round(self.max_entry_price, 4),
            "target_price": round(self.target_price, 4),
            "position_pct": round(self.position_pct, 4),
            "is_actionable": self.is_actionable,
            "rejection_reason": self.rejection_reason,
        }
    
    @property
    def strength_label(self) -> str:
        """Human-readable strength label."""
        labels = {
            SignalStrength.NONE: "NONE",
            SignalStrength.WEAK: "WEAK",
            SignalStrength.MODERATE: "MODERATE",
            SignalStrength.STRONG: "STRONG",
            SignalStrength.EXTREME: "EXTREME",
        }
        return labels.get(self.signal_strength, "UNKNOWN")
    
    @property
    def summary(self) -> str:
        """One-line summary of the signal."""
        status = "[BUY]" if self.is_actionable else "[SKIP]"
        return (
            f"{status} {self.direction} @ {self.current_price:.2f} | "
            f"Score: {self.direction_score:+.2f} | "
            f"Strength: {self.strength_label} | "
            f"End: {self.hours_until_end:.1f}h"
        )


class SignalGenerator:
    """
    Generate trading signals from analysis results.
    
    Applies:
    1. Direction score threshold
    2. Price filter (max entry price)
    3. Timing filter (hours until end)
    4. Signal strength classification
    5. Position sizing
    
    Usage:
        generator = SignalGenerator()
        signal = generator.generate(
            analysis_result=...,
            market_info=...,
            current_price=0.55
        )
    """
    
    def __init__(self, config: StrategyConfig = None):
        self.config = config or StrategyConfig()
        self.price_calculator = EntryPriceCalculator(self.config)
        self.position_sizer = PositionSizer(self.config)
    
    def _calculate_signal_strength(
        self,
        direction_score: float,
        days_consistent: int,
        insider_count: int
    ) -> SignalStrength:
        """Determine signal strength from metrics."""
        abs_score = abs(direction_score)
        
        # EXTREME: Very high score + consistency + many insiders
        if abs_score >= 0.50 and days_consistent >= 5 and insider_count >= 15:
            return SignalStrength.EXTREME
        
        # STRONG: High score + some consistency
        if abs_score >= 0.30 and days_consistent >= 3 and insider_count >= 8:
            return SignalStrength.STRONG
        
        # MODERATE: Decent score
        if abs_score >= 0.15 and days_consistent >= 2 and insider_count >= 3:
            return SignalStrength.MODERATE
        
        # WEAK: Low but present
        if abs_score >= 0.10:
            return SignalStrength.WEAK
        
        return SignalStrength.NONE
    
    def generate(
        self,
        analysis_result,  # AnalysisResult from live_analyzer
        market_info,      # MarketInfo from market_discovery
        days_consistent: int = 0
    ) -> Optional[LiveSignal]:
        """
        Generate a trading signal from analysis result.
        
        Args:
            analysis_result: AnalysisResult from LiveAnalyzer
            market_info: MarketInfo from MarketDiscovery
            days_consistent: Number of consistent signal days
            
        Returns:
            LiveSignal or None if no signal
        """
        # Check for valid signal
        if analysis_result.signal in ("NO_DATA", "NEUTRAL"):
            return None
        
        direction = analysis_result.signal
        direction_score = analysis_result.direction_score
        
        # Get current price for the predicted direction
        if direction == "YES":
            current_price = market_info.yes_price
        else:
            current_price = market_info.no_price
        
        # Calculate signal strength
        signal_strength = self._calculate_signal_strength(
            direction_score=direction_score,
            days_consistent=days_consistent,
            insider_count=analysis_result.total_insiders
        )
        
        # Check minimum score threshold
        if abs(direction_score) < self.config.min_direction_score:
            return LiveSignal(
                market_id=market_info.market_id,
                question=market_info.question,
                slug=market_info.slug,
                direction=direction,
                direction_score=direction_score,
                signal_strength=signal_strength,
                days_consistent=days_consistent,
                insider_count=analysis_result.total_insiders,
                insider_volume=analysis_result.total_volume,
                hours_until_end=market_info.hours_until_end,
                analysis_time=analysis_result.analysis_time,
                current_price=current_price,
                max_entry_price=0,
                target_price=0,
                position_pct=0,
                is_actionable=False,
                rejection_reason=f"Score too low ({abs(direction_score):.2f} < {self.config.min_direction_score})"
            )
        
        # Calculate entry prices
        target_price, max_price = self.price_calculator.calculate(
            direction_score=direction_score,
            signal_strength=signal_strength,
            current_price=current_price
        )
        
        # Check price filter
        should_enter, enter_reason = self.price_calculator.should_enter(
            current_price=current_price,
            max_price=max_price
        )
        
        # Calculate position size
        entry_discount = max(0, (max_price - current_price) / max_price) if max_price > 0 else 0
        position_pct = self.position_sizer.calculate(
            signal_strength=signal_strength,
            days_consistent=days_consistent,
            entry_discount=entry_discount
        )
        
        # Check timing
        rejection_reason = None
        if not should_enter:
            rejection_reason = enter_reason
        elif market_info.hours_until_end < 0.5:
            should_enter = False
            rejection_reason = "Too close to end (<30min)"
        elif not market_info.accepting_orders:
            should_enter = False
            rejection_reason = "Market not accepting orders"
        
        return LiveSignal(
            market_id=market_info.market_id,
            question=market_info.question,
            slug=market_info.slug,
            direction=direction,
            direction_score=direction_score,
            signal_strength=signal_strength,
            days_consistent=days_consistent,
            insider_count=analysis_result.total_insiders,
            insider_volume=analysis_result.total_volume,
            hours_until_end=market_info.hours_until_end,
            analysis_time=analysis_result.analysis_time,
            current_price=current_price,
            max_entry_price=max_price,
            target_price=target_price,
            position_pct=position_pct,
            is_actionable=should_enter,
            rejection_reason=rejection_reason
        )
    
    def filter_signals(
        self,
        signals: List[LiveSignal],
        min_strength: SignalStrength = SignalStrength.MODERATE,
        only_actionable: bool = True
    ) -> List[LiveSignal]:
        """Filter signals by criteria."""
        filtered = []
        
        for signal in signals:
            if only_actionable and not signal.is_actionable:
                continue
            
            if signal.signal_strength.value < min_strength.value:
                continue
            
            filtered.append(signal)
        
        # Sort by signal strength (descending), then by direction score
        filtered.sort(
            key=lambda s: (s.signal_strength.value, abs(s.direction_score)),
            reverse=True
        )
        
        return filtered


# =============================================================================
# CLI for testing
# =============================================================================

if __name__ == "__main__":
    print("SignalGenerator module - import and use in other scripts")
    print("See live_scanner.py for usage example")
