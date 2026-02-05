"""
Alert System Module

Output alerts and notifications for detected signals.
Supports multiple output channels:
- Terminal (colored output)
- JSON log file
- (Optional) Webhook (Discord/Telegram)
"""
import sys
import json
from datetime import datetime, timezone
from typing import List, Optional, Dict
from pathlib import Path
from dataclasses import dataclass

sys.stdout.reconfigure(encoding='utf-8')


class AlertSystem:
    """
    Output alerts for detected signals.
    
    Channels:
    - Terminal: Colored, formatted output
    - JSON Log: Detailed log file
    - Webhook: (Optional) External notifications
    
    Usage:
        alerts = AlertSystem()
        alerts.signal_detected(signal)
        alerts.scan_complete(stats)
    """
    
    def __init__(
        self,
        log_dir: Optional[Path] = None,
        webhook_url: Optional[str] = None
    ):
        if log_dir is None:
            log_dir = Path(__file__).parent / "logs"
        
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.webhook_url = webhook_url
        self.current_log_file = self.log_dir / f"scan_{datetime.now().strftime('%Y%m%d')}.json"
        
        # Log entries for current session
        self.session_logs: List[dict] = []
    
    def _log_to_file(self, entry: dict):
        """Append entry to log file."""
        entry["logged_at"] = datetime.now(timezone.utc).isoformat()
        self.session_logs.append(entry)
        
        try:
            # Append to daily log file
            logs = []
            if self.current_log_file.exists():
                with open(self.current_log_file, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            
            logs.append(entry)
            
            with open(self.current_log_file, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2, default=str)
        except Exception as e:
            print(f"[WARNING] Failed to write log: {e}")
    
    def _send_webhook(self, message: str, embeds: List[dict] = None):
        """Send webhook notification (Discord format)."""
        if not self.webhook_url:
            return
        
        try:
            import requests
            
            payload = {"content": message}
            if embeds:
                payload["embeds"] = embeds
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code not in (200, 204):
                print(f"[WARNING] Webhook failed: {response.status_code}")
        except Exception as e:
            print(f"[WARNING] Webhook error: {e}")
    
    def scan_started(self, market_count: int):
        """Log scan start."""
        now = datetime.now()
        
        print(f"\n{'='*80}")
        print(f"LIVE SCANNER - {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        print(f"[SCAN] Scanning {market_count} markets...")
        print()
        
        self._log_to_file({
            "type": "scan_started",
            "market_count": market_count,
            "timestamp": now.isoformat()
        })
    
    def market_scanned(
        self,
        market_id: int,
        question: str,
        trade_count: int,
        has_signal: bool,
        signal_summary: Optional[str] = None
    ):
        """Log individual market scan result."""
        q_short = question[:50] + "..." if len(question) > 50 else question
        
        if has_signal:
            print(f"  [SIGNAL] Market {market_id}: {signal_summary}")
        # Uncomment for verbose mode:
        # else:
        #     print(f"  [skip] Market {market_id}: {q_short}")
    
    def signal_detected(self, signal, is_new: bool = True):
        """Alert for a detected signal."""
        # Terminal output
        status = "[NEW SIGNAL]" if is_new else "[SIGNAL UPDATE]"
        strength = signal.strength_label
        
        print()
        print(f"  {'-'*70}")
        print(f"  {status} {strength} {signal.direction}")
        print(f"  Market: {signal.question[:60]}...")
        print(f"  ")
        print(f"    Direction Score: {signal.direction_score:+.4f}")
        print(f"    Current Price:   {signal.current_price:.4f}")
        print(f"    Max Entry Price: {signal.max_entry_price:.4f}")
        print(f"    Position Size:   {signal.position_pct:.1%}")
        print(f"    Hours Until End: {signal.hours_until_end:.1f}h")
        print(f"    Insider Count:   {signal.insider_count}")
        print(f"    Days Consistent: {signal.days_consistent}")
        
        if signal.is_actionable:
            print(f"  ")
            print(f"    [ACTION] BUY {signal.direction} @ {signal.current_price:.4f}")
        else:
            print(f"    [NO ACTION] {signal.rejection_reason}")
        
        print(f"  {'-'*70}")
        print()
        
        # Log to file
        self._log_to_file({
            "type": "signal_detected",
            "is_new": is_new,
            "signal": signal.to_dict()
        })
        
        # Webhook for actionable signals
        if signal.is_actionable and self.webhook_url:
            self._send_webhook(
                f"**{strength} Signal: {signal.direction}**\n"
                f"Market: {signal.question[:80]}\n"
                f"Price: {signal.current_price:.2f} | Score: {signal.direction_score:+.2f}\n"
                f"Position: {signal.position_pct:.1%} | End: {signal.hours_until_end:.1f}h"
            )
    
    def scan_complete(
        self,
        markets_scanned: int,
        signals_found: int,
        actionable_signals: int,
        duration_seconds: float,
        active_signals: List = None
    ):
        """Log scan completion summary."""
        print()
        print(f"{'='*80}")
        print(f"SCAN COMPLETE")
        print(f"{'='*80}")
        print(f"  Markets Scanned:    {markets_scanned}")
        print(f"  Signals Found:      {signals_found}")
        print(f"  Actionable Signals: {actionable_signals}")
        print(f"  Duration:           {duration_seconds:.1f}s")
        
        if active_signals:
            print()
            print(f"  ACTIVE SIGNALS:")
            for i, sig in enumerate(active_signals[:10], 1):
                strength = sig.strength_label
                print(f"    {i}. [{strength}] {sig.direction} @ {sig.current_price:.2f} | {sig.question[:40]}...")
        
        print(f"{'='*80}")
        print()
        
        self._log_to_file({
            "type": "scan_complete",
            "markets_scanned": markets_scanned,
            "signals_found": signals_found,
            "actionable_signals": actionable_signals,
            "duration_seconds": duration_seconds,
        })
    
    def error(self, message: str, market_id: int = None):
        """Log an error."""
        if market_id:
            print(f"[ERROR] Market {market_id}: {message}")
        else:
            print(f"[ERROR] {message}")
        
        self._log_to_file({
            "type": "error",
            "message": message,
            "market_id": market_id,
        })
    
    def warning(self, message: str):
        """Log a warning."""
        print(f"[WARNING] {message}")
        
        self._log_to_file({
            "type": "warning",
            "message": message,
        })
    
    def info(self, message: str):
        """Log info message."""
        print(f"[INFO] {message}")


# =============================================================================
# CLI for testing
# =============================================================================

if __name__ == "__main__":
    alerts = AlertSystem()
    
    # Test scan flow
    alerts.scan_started(10)
    alerts.market_scanned(123, "Test market question?", 500, False)
    alerts.scan_complete(
        markets_scanned=10,
        signals_found=2,
        actionable_signals=1,
        duration_seconds=5.5
    )
