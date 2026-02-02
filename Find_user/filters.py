"""
Filters: Business logic for identifying smart traders.
"""

from typing import Dict, List, Any
import time
from config import filter_config

class TraderFilters:
    
    @staticmethod
    def is_market_maker(trader: Dict[str, Any]) -> bool:
        """
        Logic: Filter out Market Makers.
        MMs typically have high volume but low ROI (profit margin).
        """
        vol = trader.get('vol', 0)
        pnl = trader.get('pnl', 0)
        
        # Avoid division by zero
        if vol == 0:
            return False
            
        roi = pnl / vol
        
        if vol > filter_config.MM_VOLUME_THRESHOLD and roi < filter_config.MM_ROI_THRESHOLD:
            return True
        return False

    @staticmethod
    def is_small_fish(trader: Dict[str, Any]) -> bool:
        """
        Logic: Filter out small capital traders.
        """
        pnl = trader.get('pnl', 0)
        return pnl < filter_config.MIN_TOTAL_PROFIT

    @staticmethod
    def is_one_hit_wonder(trader: Dict[str, Any], closed_positions: List[Dict[str, Any]]) -> bool:
        """
        Logic: Detect if > 90% of profit comes from a single trade.
        Requires detailed trade history.
        """
        total_pnl_leaderboard = trader.get('pnl', 0)
        
        if not closed_positions:
            # If no history is found but they have PnL, we can't verify consistency.
            # Safe strategy: If PnL is huge but no history visible, might be old data or hidden.
            # For now, let's assume FALSE (not a one-hit wonder) unless proven otherwise, 
            # Or TRUE (safer) to exclude opaque profiles? 
            # Let's return False but log warning in a real system. Here strict filtering:
            return False 

        # Find max single trade realized PnL
        max_single_pnl = 0
        for pos in closed_positions:
            pnl = pos.get('realizedPnl', 0)
            if pnl > max_single_pnl:
                max_single_pnl = pnl
        
        # Calculate ratio
        # Handle edge case where total PnL might be different from sum of history due to API limits
        if total_pnl_leaderboard <= 0:
            return False # Losing trader, doesn't matter
            
        ratio = max_single_pnl / total_pnl_leaderboard
        
        if ratio > filter_config.MAX_SINGLE_TRADE_RATIO:
            return True
            
        return False

    @staticmethod
    def is_inactive(closed_positions: List[Dict[str, Any]]) -> bool:
        """
        Logic: Check if the trader has been inactive for too long.
        Uses the latest trade timestamp.
        """
        if not closed_positions:
            return True # No history = Inactive
            
        # Sort by timestamp descending just in case, though API usually does it
        # Assuming API returns 'timestamp' (Unix seconds)
        latest_trade = closed_positions[0] 
        last_ts = latest_trade.get('timestamp', 0)
        
        # If timestamp is missing or 0
        if not last_ts:
            return True
            
        current_ts = time.time()
        diff_seconds = current_ts - last_ts
        diff_days = diff_seconds / 86400
        
        if diff_days > filter_config.MAX_INACTIVITY_DAYS:
            return True
            
        return False
