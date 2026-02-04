"""
Insider Direction Analyzer

Responsibilities:
1. Analyze a single market's trading data
2. Identify insider wallets based on scoring
3. Calculate daily direction signals
4. Support both daily breakdown and aggregate analysis

This module is called by batch_validation.py for each market.
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import statistics

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class AnalysisConfig:
    min_insider_score: int = 80       # Minimum score to be considered insider
    min_wallet_volume: float = 10000  # Minimum volume per wallet
    lookback_days: int = 30           # Days before close to analyze


# =============================================================================
# Wallet Profile
# =============================================================================

@dataclass 
class DailyWalletProfile:
    """Profile of a wallet's activity on a specific day."""
    address: str
    date: str
    buy_vol_yes: float = 0.0
    buy_vol_no: float = 0.0
    trade_sizes: List[float] = field(default_factory=list)
    first_ts: Optional[datetime] = None
    last_ts: Optional[datetime] = None
    
    @property
    def total_volume(self) -> float:
        return self.buy_vol_yes + self.buy_vol_no
    
    @property
    def direction(self) -> str:
        if self.buy_vol_yes > self.buy_vol_no:
            return "YES"
        elif self.buy_vol_no > self.buy_vol_yes:
            return "NO"
        return "NEUTRAL"
    
    @property
    def conviction(self) -> float:
        return max(self.buy_vol_yes, self.buy_vol_no)


# =============================================================================
# Insider Score Calculation
# =============================================================================

def calculate_insider_score(p: DailyWalletProfile) -> Tuple[int, dict]:
    """
    Calculate insider score for a wallet's daily activity.
    
    Components:
    1. Conviction (volume in dominant direction): 10-40 points
    2. Size anomaly (max trade >> median): 10-30 points
    3. Timing burst (concentrated trading): 10-30 points
    4. Directional bias (one-sided trading): 10-20 points
    
    Max score: ~120
    """
    score = 0
    metrics = {}
    
    # 1. Conviction
    conviction = p.conviction
    metrics["conviction"] = round(conviction, 0)
    
    if conviction >= 100000:
        score += 40
        metrics["conviction_tier"] = "WHALE"
    elif conviction >= 50000:
        score += 30
        metrics["conviction_tier"] = "HIGH"
    elif conviction >= 20000:
        score += 20
        metrics["conviction_tier"] = "MODERATE"
    elif conviction >= 10000:
        score += 10
        metrics["conviction_tier"] = "LOW"
    
    # 2. Trade size anomaly
    if len(p.trade_sizes) >= 2:
        max_size = max(p.trade_sizes)
        median_size = statistics.median(p.trade_sizes)
        
        if median_size > 0:
            ratio = max_size / median_size
            metrics["size_ratio"] = round(ratio, 1)
            
            if ratio > 50:
                score += 30
                metrics["size_signal"] = "EXTREME"
            elif ratio > 20:
                score += 20
                metrics["size_signal"] = "HIGH"
            elif ratio > 10:
                score += 10
                metrics["size_signal"] = "MODERATE"
    
    # 3. Timing burst
    if p.first_ts and p.last_ts:
        span_hours = (p.last_ts - p.first_ts).total_seconds() / 3600
        metrics["span_hours"] = round(span_hours, 1)
        
        if span_hours <= 2 and p.total_volume > 20000:
            score += 30
            metrics["timing"] = "EXTREME_BURST"
        elif span_hours <= 6:
            score += 20
            metrics["timing"] = "BURST"
        elif span_hours <= 12:
            score += 10
            metrics["timing"] = "CONCENTRATED"
    
    # 4. Directional conviction
    total = p.buy_vol_yes + p.buy_vol_no
    if total > 0:
        directional = abs(p.buy_vol_yes - p.buy_vol_no) / total
        metrics["directional_ratio"] = round(directional, 3)
        
        if directional > 0.9:
            score += 20
            metrics["directional"] = "EXTREME"
        elif directional > 0.7:
            score += 10
            metrics["directional"] = "HIGH"
    
    metrics["direction"] = p.direction
    return score, metrics


# =============================================================================
# Market Analyzer
# =============================================================================

class InsiderDirectionAnalyzer:
    """
    Analyze a market's trades to detect insider direction signals.
    """
    
    def __init__(self, config: AnalysisConfig = None):
        self.config = config or AnalysisConfig()
    
    def build_daily_profiles(
        self, 
        trades_df: pd.DataFrame
    ) -> Dict[str, Dict[str, DailyWalletProfile]]:
        """
        Build wallet profiles grouped by day.
        Returns: {date: {address: DailyWalletProfile}}
        """
        daily_profiles: Dict[str, Dict[str, DailyWalletProfile]] = defaultdict(dict)
        
        # Ensure timestamp is datetime
        if not pd.api.types.is_datetime64_any_dtype(trades_df['timestamp']):
            trades_df = trades_df.copy()
            trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'], errors='coerce')
        
        for _, row in trades_df.iterrows():
            try:
                maker = str(row.get('maker', '')).lower().strip()
                taker = str(row.get('taker', '')).lower().strip()
                usd = float(row.get('usd_amount', 0) or 0)
                token_side = str(row.get('nonusdc_side', '')).strip()
                maker_dir = str(row.get('maker_direction', '')).upper().strip()
                ts = row['timestamp']
                
                if pd.isna(ts):
                    continue
                    
                day = ts.strftime('%Y-%m-%d')
                
                for addr, is_buy in [(maker, maker_dir == 'BUY'), (taker, maker_dir != 'BUY')]:
                    if not is_buy or not addr or addr in ['nan', 'none', '']:
                        continue
                    
                    if addr not in daily_profiles[day]:
                        daily_profiles[day][addr] = DailyWalletProfile(address=addr, date=day)
                    
                    p = daily_profiles[day][addr]
                    p.trade_sizes.append(usd)
                    
                    if p.first_ts is None or ts < p.first_ts:
                        p.first_ts = ts
                    if p.last_ts is None or ts > p.last_ts:
                        p.last_ts = ts
                    
                    if token_side == 'token1':
                        p.buy_vol_yes += usd
                    else:
                        p.buy_vol_no += usd
            except Exception:
                continue
        
        return daily_profiles
    
    def analyze_daily(
        self, 
        daily_profiles: Dict[str, Dict[str, DailyWalletProfile]]
    ) -> List[dict]:
        """
        Analyze each day's insider direction.
        Returns list of daily results.
        """
        results = []
        
        for day in sorted(daily_profiles.keys()):
            wallets = daily_profiles[day]
            
            # Score each wallet
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
                        "metrics": metrics
                    })
            
            # Calculate direction
            yes_conv = sum(w["conviction"] for w in day_insiders if w["direction"] == "YES")
            no_conv = sum(w["conviction"] for w in day_insiders if w["direction"] == "NO")
            total_conv = yes_conv + no_conv
            
            yes_count = sum(1 for w in day_insiders if w["direction"] == "YES")
            no_count = sum(1 for w in day_insiders if w["direction"] == "NO")
            
            if total_conv > 0:
                direction_score = (yes_conv - no_conv) / total_conv
            else:
                direction_score = 0
            
            # Determine signal
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
            
            results.append({
                "date": day,
                "insider_count": len(day_insiders),
                "yes_insiders": yes_count,
                "no_insiders": no_count,
                "yes_conviction": round(yes_conv, 0),
                "no_conviction": round(no_conv, 0),
                "direction_score": round(direction_score, 3),
                "signal": signal,
                "top_insiders": sorted(day_insiders, key=lambda x: x["score"], reverse=True)[:5]
            })
        
        return results
    
    def get_aggregate_signal(self, daily_results: List[dict]) -> dict:
        """
        Calculate aggregate signal from daily results with TIME WEIGHTING.
        Recent days (especially last 1-3 days) get higher weight.
        """
        if not daily_results:
            return {"signal": "NO_DATA", "direction_score": 0}
        
        # Count signal days
        yes_days = sum(1 for r in daily_results if r['signal'] in ['YES', 'STRONG_YES'])
        no_days = sum(1 for r in daily_results if r['signal'] in ['NO', 'STRONG_NO'])
        neutral_days = sum(1 for r in daily_results if r['signal'] == 'NEUTRAL')
        
        # WEIGHTED direction score - recent days count more
        # Last day (index -1) = 3x weight
        # Days -2, -3 = 2x weight
        # Days -4 to -7 = 1.5x weight
        # Older days = 1x weight
        total_weight = 0.0
        weighted_score = 0.0
        
        n = len(daily_results)
        for i, r in enumerate(daily_results):
            days_from_end = n - 1 - i  # 0 = last day
            
            if days_from_end == 0:
                weight = 3.0  # Last day - highest weight
            elif days_from_end <= 2:
                weight = 2.0  # Days 2-3
            elif days_from_end <= 6:
                weight = 1.5  # Days 4-7
            else:
                weight = 1.0  # Older days
            
            weighted_score += r['direction_score'] * weight
            total_weight += weight
        
        avg_direction = weighted_score / total_weight if total_weight > 0 else 0
        
        # Also check if last day has strong signal (burst detection)
        last_day_signal = daily_results[-1] if daily_results else None
        last_day_score = last_day_signal['direction_score'] if last_day_signal else 0
        last_day_insiders = last_day_signal['insider_count'] if last_day_signal else 0
        
        # If last day has EXTREME signal, boost overall confidence
        if last_day_signal and abs(last_day_score) > 0.5 and last_day_insiders >= 5:
            # Last minute surge detected - use last day's direction
            avg_direction = (avg_direction + last_day_score) / 2  # Blend with last day
        
        # Determine overall signal
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
            "direction_score": round(avg_direction, 4),
            "yes_days": yes_days,
            "no_days": no_days,
            "neutral_days": neutral_days,
            "total_insiders": sum(r['insider_count'] for r in daily_results),
            "last_day_score": round(last_day_score, 4),
            "last_day_insiders": last_day_insiders
        }
    
    def analyze_market(
        self, 
        trades_df: pd.DataFrame,
        closed_time: Optional[datetime] = None,
        return_daily: bool = True
    ) -> dict:
        """
        Full analysis pipeline for a market.
        
        Args:
            trades_df: DataFrame with trade data
            closed_time: Market close time (for time window filtering)
            return_daily: Whether to include daily breakdown
        
        Returns:
            Analysis results including signal, prediction, and optionally daily breakdown
        """
        # Apply time window filter if closed_time provided
        if closed_time is not None:
            trades_df = trades_df.copy()
            trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'], errors='coerce')
            
            # Remove timezone if present
            if trades_df['timestamp'].dt.tz is not None:
                trades_df['timestamp'] = trades_df['timestamp'].dt.tz_localize(None)
            
            cutoff_time = closed_time - timedelta(days=self.config.lookback_days)
            exclude_time = closed_time - timedelta(hours=1)
            
            trades_df = trades_df[
                (trades_df['timestamp'] >= cutoff_time) & 
                (trades_df['timestamp'] < exclude_time)
            ]
        
        if len(trades_df) < 50:
            return {"signal": "NO_DATA", "reason": "insufficient_trades"}
        
        # Build daily profiles and analyze
        daily_profiles = self.build_daily_profiles(trades_df)
        daily_results = self.analyze_daily(daily_profiles)
        
        if not daily_results:
            return {"signal": "NO_DATA", "reason": "no_daily_data"}
        
        # Get aggregate signal
        result = self.get_aggregate_signal(daily_results)
        result["analyzed_trades"] = len(trades_df)
        result["days_analyzed"] = len(daily_results)
        
        if return_daily:
            result["daily_results"] = daily_results
        
        return result
