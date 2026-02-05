"""
Live Scanner - Main Entry Point

Scans active Polymarket markets for insider trading signals.
Based on validated strategy V6 (74.3% Win Rate, +61.5% ROI, P-value: 1.5e-21).

Usage:
    # Single scan
    python live_scanner.py --once
    
    # Continuous scanning (every 15 minutes)
    python live_scanner.py --interval 15
    
    # With custom parameters
    python live_scanner.py --interval 15 --min-volume 100000 --min-score 0.30
    
    # Monitor specific markets
    python live_scanner.py --markets 12345,67890 --interval 5

Author: Insider Scanner System
Date: 2026-02-05
"""
import sys
import time
import argparse
from datetime import datetime, timezone
from typing import List, Optional
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from live_scanner.market_discovery import MarketDiscovery, MarketInfo
from live_scanner.trade_fetcher import TradeFetcher
from live_scanner.live_analyzer import LiveAnalyzer
from live_scanner.signal_generator import SignalGenerator, LiveSignal
from live_scanner.state_manager import StateManager
from live_scanner.alert_system import AlertSystem

# Also import strategy config from parent
from trading_strategy import StrategyConfig, SignalStrength


class LiveScanner:
    """
    Main scanner class that orchestrates the scanning pipeline.
    
    Pipeline:
    1. Discover active markets (MarketDiscovery)
    2. Fetch recent trades (TradeFetcher)
    3. Analyze for insider signals (LiveAnalyzer)
    4. Generate trading signals (SignalGenerator)
    5. Track state and deduplicate (StateManager)
    6. Output alerts (AlertSystem)
    """
    
    def __init__(
        self,
        min_volume: float = 100000,
        hours_range: tuple = (1, 72),
        min_direction_score: float = 0.30,
        lookback_days: int = 30,
        webhook_url: Optional[str] = None
    ):
        # Configuration
        self.min_volume = min_volume
        self.hours_range = hours_range
        self.lookback_days = lookback_days
        
        # Strategy config
        self.strategy_config = StrategyConfig(
            min_direction_score=min_direction_score
        )
        
        # Initialize modules
        self.discovery = MarketDiscovery()
        self.fetcher = TradeFetcher()
        self.analyzer = LiveAnalyzer(lookback_days=lookback_days)
        self.signal_generator = SignalGenerator(self.strategy_config)
        self.state = StateManager()
        self.alerts = AlertSystem(webhook_url=webhook_url)
    
    def scan_single_market(self, market: MarketInfo) -> Optional[LiveSignal]:
        """
        Scan a single market for insider signals.
        
        Returns:
            LiveSignal if signal detected, None otherwise
        """
        try:
            # Fetch recent trades
            trades_df = self.fetcher.fetch_recent_trades(
                market_id=market.market_id,
                lookback_days=self.lookback_days
            )
            
            if trades_df is None or len(trades_df) < 50:
                return None
            
            # Run insider analysis
            analysis = self.analyzer.analyze(
                trades_df=trades_df,
                market_id=market.market_id
            )
            
            if not analysis.is_valid_signal:
                return None
            
            # Count consistent days
            days_consistent = self.analyzer.count_consistent_days(
                daily_results=analysis.daily_results,
                overall_direction=analysis.direction
            )
            
            # Generate signal
            signal = self.signal_generator.generate(
                analysis_result=analysis,
                market_info=market,
                days_consistent=days_consistent
            )
            
            # Update state
            self.state.update_market(
                market_id=market.market_id,
                signal=signal.to_dict() if signal else None,
                trade_count=len(trades_df)
            )
            
            return signal
            
        except Exception as e:
            self.alerts.error(str(e), market_id=market.market_id)
            return None
    
    def scan_all(
        self,
        specific_markets: List[int] = None,
        max_markets: int = 100
    ) -> List[LiveSignal]:
        """
        Scan all active markets or specific markets.
        
        Args:
            specific_markets: List of market IDs to scan (if None, discover markets)
            max_markets: Maximum markets to scan
            
        Returns:
            List of detected signals
        """
        start_time = time.time()
        self.state.start_scan()
        
        # Get markets to scan
        if specific_markets:
            markets = []
            for mid in specific_markets:
                market = self.discovery.get_market_by_id(mid)
                if market:
                    markets.append(market)
        else:
            markets = self.discovery.get_active_markets(
                min_volume=self.min_volume,
                hours_range=self.hours_range,
                limit=max_markets
            )
        
        if not markets:
            self.alerts.warning("No markets found matching criteria")
            return []
        
        self.alerts.scan_started(len(markets))
        
        # Scan each market
        all_signals: List[LiveSignal] = []
        actionable_signals: List[LiveSignal] = []
        
        for i, market in enumerate(markets):
            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i+1}/{len(markets)} markets...")
            
            signal = self.scan_single_market(market)
            
            if signal:
                all_signals.append(signal)
                
                # Check if we should alert
                alert_key = f"{signal.direction}_{signal.strength_label}"
                is_new = self.state.should_send_alert(
                    market_id=market.market_id,
                    alert_key=alert_key,
                    cooldown_hours=1.0
                )
                
                if signal.is_actionable:
                    actionable_signals.append(signal)
                    self.alerts.signal_detected(signal, is_new=is_new)
                    self.state.record_alert(market.market_id, alert_key)
                else:
                    self.alerts.market_scanned(
                        market_id=market.market_id,
                        question=market.question,
                        trade_count=0,
                        has_signal=True,
                        signal_summary=signal.summary
                    )
            
            # Rate limiting between markets
            time.sleep(0.2)
        
        # Save state
        self.state.save()
        
        # Summary
        duration = time.time() - start_time
        self.alerts.scan_complete(
            markets_scanned=len(markets),
            signals_found=len(all_signals),
            actionable_signals=len(actionable_signals),
            duration_seconds=duration,
            active_signals=actionable_signals
        )
        
        return all_signals
    
    def run_continuous(
        self,
        interval_minutes: float = 15,
        specific_markets: List[int] = None
    ):
        """
        Run continuous scanning loop.
        
        Args:
            interval_minutes: Minutes between scans
            specific_markets: Optional list of specific markets to monitor
        """
        print(f"\n[SCANNER] Starting continuous scanning (interval: {interval_minutes} min)")
        print(f"[SCANNER] Press Ctrl+C to stop\n")
        
        while True:
            try:
                self.scan_all(specific_markets=specific_markets)
                
                # Wait for next scan
                print(f"\n[SCANNER] Next scan in {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                print("\n[SCANNER] Stopped by user")
                self.state.save()
                break
            except Exception as e:
                self.alerts.error(f"Scan failed: {e}")
                time.sleep(60)  # Wait 1 minute before retry


def main():
    parser = argparse.ArgumentParser(
        description="Live Scanner for Polymarket Insider Detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Single scan
    python live_scanner.py --once
    
    # Continuous scanning every 15 minutes
    python live_scanner.py --interval 15
    
    # Custom parameters
    python live_scanner.py --interval 15 --min-volume 100000 --min-score 0.30
    
    # Monitor specific markets
    python live_scanner.py --markets 12345,67890 --interval 5
        """
    )
    
    # Mode
    parser.add_argument("--once", action="store_true", help="Single scan then exit")
    parser.add_argument("--interval", type=float, default=15, help="Scan interval in minutes")
    
    # Filters
    parser.add_argument("--min-volume", type=float, default=100000, help="Minimum market volume")
    parser.add_argument("--hours-min", type=float, default=1, help="Min hours until end")
    parser.add_argument("--hours-max", type=float, default=72, help="Max hours until end")
    parser.add_argument("--min-score", type=float, default=0.30, help="Minimum direction score")
    parser.add_argument("--lookback", type=int, default=30, help="Lookback days for analysis")
    
    # Specific markets
    parser.add_argument("--markets", type=str, help="Comma-separated market IDs to monitor")
    
    # Output
    parser.add_argument("--webhook", type=str, help="Discord/Slack webhook URL")
    parser.add_argument("--max-markets", type=int, default=100, help="Max markets to scan")
    
    args = parser.parse_args()
    
    # Parse specific markets
    specific_markets = None
    if args.markets:
        specific_markets = [int(m.strip()) for m in args.markets.split(",")]
    
    # Initialize scanner
    scanner = LiveScanner(
        min_volume=args.min_volume,
        hours_range=(args.hours_min, args.hours_max),
        min_direction_score=args.min_score,
        lookback_days=args.lookback,
        webhook_url=args.webhook
    )
    
    # Run
    if args.once:
        scanner.scan_all(specific_markets=specific_markets, max_markets=args.max_markets)
    else:
        scanner.run_continuous(
            interval_minutes=args.interval,
            specific_markets=specific_markets
        )


if __name__ == "__main__":
    main()
