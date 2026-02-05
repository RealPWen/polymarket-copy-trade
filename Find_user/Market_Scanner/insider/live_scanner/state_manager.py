"""
State Manager Module

Manages scanner state including:
- Active markets being tracked
- Signal history
- Alert deduplication
- Persistence to disk
"""
import sys
import json
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class MarketState:
    """State for a single market being tracked."""
    market_id: int
    first_seen: datetime
    last_scan: datetime
    last_signal: Optional[dict] = None
    signal_history: List[dict] = field(default_factory=list)
    alerts_sent: List[str] = field(default_factory=list)
    trade_count_at_last_scan: int = 0
    
    def to_dict(self) -> dict:
        return {
            "market_id": self.market_id,
            "first_seen": self.first_seen.isoformat(),
            "last_scan": self.last_scan.isoformat(),
            "last_signal": self.last_signal,
            "signal_history": self.signal_history[-20:],  # Keep last 20
            "alerts_sent": self.alerts_sent[-50:],  # Keep last 50
            "trade_count_at_last_scan": self.trade_count_at_last_scan,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MarketState":
        return cls(
            market_id=data["market_id"],
            first_seen=datetime.fromisoformat(data["first_seen"]),
            last_scan=datetime.fromisoformat(data["last_scan"]),
            last_signal=data.get("last_signal"),
            signal_history=data.get("signal_history", []),
            alerts_sent=data.get("alerts_sent", []),
            trade_count_at_last_scan=data.get("trade_count_at_last_scan", 0),
        )


class StateManager:
    """
    Manage scanner state with persistence.
    
    Features:
    - Track active markets
    - Store signal history
    - Deduplicate alerts
    - Persist to JSON file
    
    Usage:
        state = StateManager()
        state.update_market(market_id, signal)
        state.save()
    """
    
    def __init__(self, state_file: Optional[Path] = None):
        if state_file is None:
            state_file = Path(__file__).parent / "scanner_state.json"
        
        self.state_file = state_file
        self.markets: Dict[int, MarketState] = {}
        self.last_scan_time: Optional[datetime] = None
        self.scan_count: int = 0
        
        self._load()
    
    def _load(self):
        """Load state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                self.last_scan_time = datetime.fromisoformat(data["last_scan_time"]) if data.get("last_scan_time") else None
                self.scan_count = data.get("scan_count", 0)
                
                for market_data in data.get("markets", {}).values():
                    state = MarketState.from_dict(market_data)
                    self.markets[state.market_id] = state
                
                print(f"[STATE] Loaded state: {len(self.markets)} markets tracked")
            except Exception as e:
                print(f"[WARNING] Failed to load state: {e}")
    
    def save(self):
        """Save state to file."""
        data = {
            "last_scan_time": self.last_scan_time.isoformat() if self.last_scan_time else None,
            "scan_count": self.scan_count,
            "markets": {mid: state.to_dict() for mid, state in self.markets.items()},
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"[ERROR] Failed to save state: {e}")
    
    def start_scan(self):
        """Mark the start of a new scan."""
        self.last_scan_time = datetime.now(timezone.utc)
        self.scan_count += 1
    
    def get_market_state(self, market_id: int) -> Optional[MarketState]:
        """Get state for a specific market."""
        return self.markets.get(market_id)
    
    def update_market(
        self,
        market_id: int,
        signal: Optional[dict] = None,
        trade_count: int = 0
    ):
        """Update state for a market."""
        now = datetime.now(timezone.utc)
        
        if market_id not in self.markets:
            self.markets[market_id] = MarketState(
                market_id=market_id,
                first_seen=now,
                last_scan=now,
            )
        
        state = self.markets[market_id]
        state.last_scan = now
        state.trade_count_at_last_scan = trade_count
        
        if signal:
            state.last_signal = signal
            state.signal_history.append({
                "time": now.isoformat(),
                "signal": signal
            })
    
    def should_send_alert(
        self,
        market_id: int,
        alert_key: str,
        cooldown_hours: float = 1.0
    ) -> bool:
        """
        Check if we should send an alert (not recently sent).
        
        Args:
            market_id: Market ID
            alert_key: Unique key for this alert type
            cooldown_hours: Minimum hours between same alerts
            
        Returns:
            True if alert should be sent
        """
        state = self.markets.get(market_id)
        if not state:
            return True
        
        # Check if this exact alert was sent recently
        full_key = f"{market_id}_{alert_key}"
        
        for alert in state.alerts_sent:
            if alert.startswith(full_key):
                # Parse timestamp from alert
                try:
                    parts = alert.split("_")
                    if len(parts) >= 3:
                        ts_str = parts[-1]
                        ts = datetime.fromisoformat(ts_str)
                        if datetime.now(timezone.utc) - ts < timedelta(hours=cooldown_hours):
                            return False
                except:
                    pass
        
        return True
    
    def record_alert(self, market_id: int, alert_key: str):
        """Record that an alert was sent."""
        state = self.markets.get(market_id)
        if state:
            now = datetime.now(timezone.utc)
            full_key = f"{market_id}_{alert_key}_{now.isoformat()}"
            state.alerts_sent.append(full_key)
    
    def cleanup_old_markets(self, max_age_hours: float = 72):
        """Remove markets that haven't been scanned recently."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        
        to_remove = []
        for market_id, state in self.markets.items():
            if state.last_scan < cutoff:
                to_remove.append(market_id)
        
        for market_id in to_remove:
            del self.markets[market_id]
        
        if to_remove:
            print(f"[STATE] Cleaned up {len(to_remove)} old markets")
    
    def get_active_signals(self) -> List[dict]:
        """Get all markets with active signals."""
        signals = []
        
        for market_id, state in self.markets.items():
            if state.last_signal and state.last_signal.get("is_actionable"):
                signals.append({
                    "market_id": market_id,
                    "signal": state.last_signal,
                    "first_seen": state.first_seen.isoformat(),
                    "last_scan": state.last_scan.isoformat(),
                })
        
        return signals
    
    def get_statistics(self) -> dict:
        """Get scanning statistics."""
        total_markets = len(self.markets)
        actionable = sum(1 for s in self.markets.values() if s.last_signal and s.last_signal.get("is_actionable"))
        
        return {
            "total_markets_tracked": total_markets,
            "actionable_signals": actionable,
            "scan_count": self.scan_count,
            "last_scan": self.last_scan_time.isoformat() if self.last_scan_time else None,
        }


# =============================================================================
# CLI for testing
# =============================================================================

if __name__ == "__main__":
    state = StateManager()
    
    print(f"\n{'='*60}")
    print("STATE MANAGER")
    print(f"{'='*60}")
    
    stats = state.get_statistics()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    signals = state.get_active_signals()
    if signals:
        print(f"\nActive Signals: {len(signals)}")
        for s in signals[:5]:
            print(f"  - Market {s['market_id']}: {s['signal'].get('direction')}")
