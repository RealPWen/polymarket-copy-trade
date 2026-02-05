"""
Live Analyzer Module

Wraps the existing insider_analyzer.py for real-time analysis.
Uses current time instead of historical closedTime.
"""
import sys
import pandas as pd
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional, Dict, List, Any
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Import from parent directory
sys.path.insert(0, str(Path(__file__).parent.parent))
from insider_analyzer import InsiderDirectionAnalyzer, AnalysisConfig


@dataclass
class AnalysisResult:
    """Result of insider analysis."""
    market_id: int
    analysis_time: datetime
    signal: str  # "YES", "NO", "NEUTRAL", "NO_DATA"
    direction_score: float  # -1.0 to +1.0 (positive = YES, negative = NO)
    total_insiders: int
    total_volume: float
    days_analyzed: int
    daily_results: List[dict]
    raw_result: dict  # Full analysis output
    
    @property
    def is_valid_signal(self) -> bool:
        """Check if we have a valid non-neutral signal."""
        return self.signal in ("YES", "NO") and abs(self.direction_score) >= 0.15
    
    @property
    def direction(self) -> str:
        """Get human-readable direction."""
        if self.direction_score > 0:
            return "YES"
        elif self.direction_score < 0:
            return "NO"
        return "NEUTRAL"
    
    def to_dict(self) -> dict:
        return {
            "market_id": self.market_id,
            "analysis_time": self.analysis_time.isoformat(),
            "signal": self.signal,
            "direction_score": round(self.direction_score, 4),
            "total_insiders": self.total_insiders,
            "total_volume": round(self.total_volume, 2),
            "days_analyzed": self.days_analyzed,
        }


class LiveAnalyzer:
    """
    Real-time insider analysis for live markets.
    
    Wraps InsiderDirectionAnalyzer with live-specific logic:
    - Uses current time instead of closedTime
    - Optimized for quick analysis
    - Returns structured AnalysisResult
    
    Usage:
        analyzer = LiveAnalyzer()
        result = analyzer.analyze(trades_df, market_id=12345)
    """
    
    def __init__(
        self,
        min_insider_score: int = 80,
        min_wallet_volume: float = 10000,
        lookback_days: int = 30
    ):
        self.config = AnalysisConfig(
            min_insider_score=min_insider_score,
            min_wallet_volume=min_wallet_volume,
            lookback_days=lookback_days
        )
        self.analyzer = InsiderDirectionAnalyzer(self.config)
    
    def analyze(
        self,
        trades_df: pd.DataFrame,
        market_id: int,
        analysis_time: Optional[datetime] = None
    ) -> AnalysisResult:
        """
        Analyze trades for insider signals.
        
        Args:
            trades_df: DataFrame with trade data
            market_id: Market ID for reference
            analysis_time: Time to analyze at (default: now)
            
        Returns:
            AnalysisResult with signal details
        """
        if analysis_time is None:
            analysis_time = datetime.now(timezone.utc)
        
        # Ensure timezone-naive for consistency
        if analysis_time.tzinfo is not None:
            analysis_time = analysis_time.replace(tzinfo=None)
        
        # Handle empty data
        if trades_df is None or len(trades_df) == 0:
            return AnalysisResult(
                market_id=market_id,
                analysis_time=analysis_time,
                signal="NO_DATA",
                direction_score=0.0,
                total_insiders=0,
                total_volume=0.0,
                days_analyzed=0,
                daily_results=[],
                raw_result={}
            )
        
        # Ensure timestamp is datetime
        trades_df = trades_df.copy()
        trades_df["timestamp"] = pd.to_datetime(trades_df["timestamp"], errors="coerce")
        
        # Make timezone-naive
        if trades_df["timestamp"].dt.tz is not None:
            trades_df["timestamp"] = trades_df["timestamp"].dt.tz_localize(None)
        
        # Run analysis
        try:
            result = self.analyzer.analyze_market(
                trades_df=trades_df,
                closed_time=analysis_time,  # Use current time as "close" time
                return_daily=True
            )
        except Exception as e:
            print(f"[ERROR] Analysis failed for market {market_id}: {e}")
            return AnalysisResult(
                market_id=market_id,
                analysis_time=analysis_time,
                signal="NO_DATA",
                direction_score=0.0,
                total_insiders=0,
                total_volume=0.0,
                days_analyzed=0,
                daily_results=[],
                raw_result={"error": str(e)}
            )
        
        # Extract results
        signal = result.get("predicted", "NEUTRAL")
        direction_score = result.get("direction_score", 0.0)
        total_insiders = result.get("total_insiders", 0)
        total_volume = result.get("total_insider_volume", 0.0)
        daily_results = result.get("daily_results", [])
        days_analyzed = len(daily_results)
        
        return AnalysisResult(
            market_id=market_id,
            analysis_time=analysis_time,
            signal=signal,
            direction_score=direction_score,
            total_insiders=total_insiders,
            total_volume=total_volume,
            days_analyzed=days_analyzed,
            daily_results=daily_results,
            raw_result=result
        )
    
    def count_consistent_days(
        self,
        daily_results: List[dict],
        overall_direction: str
    ) -> int:
        """Count how many recent days have consistent signal."""
        if not daily_results or overall_direction == "NEUTRAL":
            return 0
        
        recent = daily_results[-10:]  # Last 10 days
        consistent = 0
        
        for day in recent:
            signal = day.get("signal", "NEUTRAL")
            if overall_direction == "YES" and signal in ("YES", "STRONG_YES"):
                consistent += 1
            elif overall_direction == "NO" and signal in ("NO", "STRONG_NO"):
                consistent += 1
        
        return consistent


# =============================================================================
# CLI for testing
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test live analyzer")
    parser.add_argument("csv_file", type=str, help="Path to trades CSV")
    parser.add_argument("--market-id", type=int, default=0, help="Market ID")
    args = parser.parse_args()
    
    # Load trades
    trades = pd.read_csv(args.csv_file)
    print(f"Loaded {len(trades)} trades")
    
    # Run analysis
    analyzer = LiveAnalyzer()
    result = analyzer.analyze(trades, market_id=args.market_id)
    
    print(f"\n{'='*60}")
    print("ANALYSIS RESULT")
    print(f"{'='*60}")
    print(f"Signal: {result.signal}")
    print(f"Direction Score: {result.direction_score:+.4f}")
    print(f"Total Insiders: {result.total_insiders}")
    print(f"Total Volume: ${result.total_volume:,.2f}")
    print(f"Days Analyzed: {result.days_analyzed}")
    
    if result.daily_results:
        print(f"\nLast 5 Daily Signals:")
        for day in result.daily_results[-5:]:
            print(f"  {day.get('date')}: {day.get('signal')} (score: {day.get('direction_signal', 0):+.2f})")
