"""
Simulation Module: Backtest specific wallets with fixed capital allocation.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from config import api_config 
from data_handler import DataHandler
from utils import logger, save_to_csv

@dataclass
class SimConfig:
    CAPITAL_PER_TRADE = 1.0  # $1 per trade
    MAX_TRADES_PER_USER = 10 # Last 10 trades to verify
    
    # Fees & Slippage simulation
    SLIPPAGE_RATE = 0.01     # 1% simulated slippage on entry
    
    # Valuation assumption for Active markets if price unavailable
    # 0.5 is neutral, 0.0 is conservative.
    DEFAULT_ACTIVE_PRICE = 0.5 

class CopyTradingSimulator:
    def __init__(self, data_handler: DataHandler):
        self.handler = data_handler

    def run_simulation(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Run simulation on a list of candidate traders.
        Returns the candidates list enriched with simulation stats.
        """
        logger.info(f"Starting Copy Trading Simulation on {len(candidates)} candidates...")
        logger.info(f"Config: ${SimConfig.CAPITAL_PER_TRADE}/trade, Max {SimConfig.MAX_TRADES_PER_USER} trades.")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_trader = {
                executor.submit(self._simulate_user, t): t 
                for t in candidates
            }
            
            for future in tqdm(as_completed(future_to_trader), total=len(candidates), desc="Simulating"):
                trader = future_to_trader[future]
                try:
                    sim_stats = future.result()
                    
                    # Merge stats into trader dict
                    trader.update(sim_stats)
                    results.append(trader)
                    
                except Exception as e:
                    logger.error(f"Sim error for {trader['proxyWallet']}: {e}")
                    results.append(trader) # Keep original if sim fails
        
        return results

    def _simulate_user(self, wallet: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate copy trading for a single user.
        """
        address = wallet['proxyWallet']
        
        # 1. Fetch recent trades (Not used directly now, we rely on Position APIs)
        # trades = self.handler.fetch_user_trades(address, limit=50) 
        
        total_invested = 0.0
        current_value = 0.0
        trades_executed = 0
        
        # 2. Strategy: Combine Closed (Realized) + Active (Unrealized)
        
        limit_per_type = SimConfig.MAX_TRADES_PER_USER
        
        # A. Fetch Closed
        closed_positions = self.handler.fetch_user_closed_positions(address, limit=limit_per_type)
        
        # B. Fetch Active
        active_positions = self.handler.fetch_user_active_positions(address, limit=limit_per_type)
        
        # Combine
        all_positions_to_sim = []
        
        # Add closed
        for p in closed_positions:
            p['__type'] = 'closed'
            all_positions_to_sim.append(p)
            
        # Add active
        for p in active_positions:
            p['__type'] = 'active'
            all_positions_to_sim.append(p)
            
        # Slice to max (prioritize closed as they are verifiable outcomes, but ideally should be time sorted)
        # Without accurate timestamp on active, we just mix them.
        all_positions_to_sim = all_positions_to_sim[:SimConfig.MAX_TRADES_PER_USER]
        
        for pos in all_positions_to_sim:
            # Simulated Entry: $1
            invest = SimConfig.CAPITAL_PER_TRADE
            
            roi = 0.0
            
            if pos['__type'] == 'closed':
                # --- Closed Logic ---
                # percentRoi is usually None, but if present, assume it is percentage (e.g. 50.0) based on naming convention
                raw_roi = pos.get('percentRoi')
                
                if raw_roi is not None:
                    roi = raw_roi / 100.0
                else:
                    # Fallback to manual calc (returns fraction directly)
                    pnl = pos.get('realizedPnl', 0)
                    cost = pos.get('totalBought', 0)
                    if cost > 0:
                        roi = pnl / cost

            elif pos['__type'] == 'active':
                # --- Active Logic ---
                # percentPnl is confirmed to be a Percentage (e.g. -99.99 or 50.0) -> Needs / 100
                raw_roi = pos.get('percentPnl')
                
                if raw_roi is not None:
                   roi = raw_roi / 100.0
                else:
                   roi = 0.0

                # Fallback if 0 (sometimes API returns 0 for active)
                if roi == 0 and 'cashPnl' in pos:
                    pnl = pos.get('cashPnl', 0)
                    cost = pos.get('totalBought', 0)
                    # For active, if totalBought is 0, try size*avgPrice
                    if cost == 0:
                        cost = pos.get('size', 0) * pos.get('avgPrice', 0)
                    
                    if cost > 0:
                        roi = pnl / cost
                        
            total_invested += invest
            
            # Apply Slippage
            # Adjusted ROI = ROI - Slippage
            adj_roi = roi - SimConfig.SLIPPAGE_RATE
            
            # Value = Principal * (1 + adj_roi)
            # Max loss is capped at -100% (value 0)
            final_val = invest * (1 + adj_roi)
            if final_val < 0: final_val = 0
            
            current_value += final_val
            trades_executed += 1
            
        sim_pnl = current_value - total_invested
        sim_roi = (sim_pnl / total_invested) * 100 if total_invested > 0 else 0
        
        return {
            'sim_invested': total_invested,
            'sim_value': current_value,
            'sim_pnl': sim_pnl,
            'sim_roi_percent': sim_roi,
            'sim_count': trades_executed
        }
