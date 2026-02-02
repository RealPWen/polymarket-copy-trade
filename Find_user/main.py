"""
Main execution script for Smart Trader Discovery.
"""

import os
import time
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import api_config, output_config
from data_handler import DataHandler
from filters import TraderFilters
from simulation import CopyTradingSimulator
from utils import setup_output_dir, save_to_csv, save_to_json, logger

def main():
    logger.info("=== Polymarket Smart Trader Discovery Engine ===")
    
    # 0. Setup
    setup_output_dir(output_config.OUTPUT_DIR)
    handler = DataHandler()
    
    # 1. Fetch Leaderboard
    raw_traders = handler.fetch_leaderboard_all(limit=api_config.FETCH_LIMIT)
    logger.info(f"Fetched {len(raw_traders)} raw candidates.")
    
    # 2. Phase 1 Filtering: Cheap Filters (Local calculation)
    phase1_survivors = []
    dropped_mm = 0
    dropped_small = 0
    
    for t in raw_traders:
        if TraderFilters.is_small_fish(t):
            dropped_small += 1
            continue
        if TraderFilters.is_market_maker(t):
            dropped_mm += 1
            continue
        phase1_survivors.append(t)
        
    logger.info(f"Phase 1 Complete. Survivors: {len(phase1_survivors)}")
    logger.info(f"  - Dropped (Small Capital): {dropped_small}")
    logger.info(f"  - Dropped (Market Makers): {dropped_mm}")
    
    # 3. Phase 2 Filtering: Deep Analysis (Requires API calls)
    logger.info("Starting Phase 2: History Analysis (One-Hit Wonder Detection)...")
    
    final_candidates = []
    
    # Use threading for faster history fetching
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Map futures to traders
        future_to_trader = {
            executor.submit(handler.fetch_user_closed_positions, t['proxyWallet']): t 
            for t in phase1_survivors
        }
        
        for future in tqdm(as_completed(future_to_trader), total=len(phase1_survivors), desc="Analyzing History"):
            trader = future_to_trader[future]
            try:
                history = future.result()
                
                # Apply Filter 4: Inactivity
                if TraderFilters.is_inactive(history):
                    # logger.debug(f"Dropped {trader['proxyWallet'][:6]} (Inactive)")
                    continue

                # Apply Filter 3: One-Hit Wonder
                if TraderFilters.is_one_hit_wonder(trader, history):
                    # logger.debug(f"Dropped {trader['proxyWallet'][:6]} (One-Hit Wonder)")
                    continue
                
                # If passed, add some derived consistency stats
                # (Optional: compute win rate here if needed, but keeping it simple for now)
                trader['consistency_check'] = "Passed"
                
                # Add Profile URL
                trader['profile_url'] = f"{api_config.PROFILE_URL_PREFIX}{trader['proxyWallet']}"
                
                final_candidates.append(trader)
                
            except Exception as e:
                logger.error(f"Error processing {trader['proxyWallet']}: {e}")
                
    # 4. Phase 3: Copy Trading Simulation
    logger.info("Starting Phase 3: Copy Trading Simulation (Backtest)...")
    simulator = CopyTradingSimulator(handler)
    # Run sim on the filtered list
    final_candidates = simulator.run_simulation(final_candidates)

    # 5. Reporting
    logger.info("=" * 40)
    logger.info(f"FINAL RESULT: Found {len(final_candidates)} Candidates. Filtering Top 10 by Sim ROI...")
    logger.info("=" * 40)
    
    # Sort by Simulation ROI (Highest First)
    final_candidates.sort(key=lambda x: x.get('sim_roi_percent', -999), reverse=True)
    
    # Keep only Top 10
    final_candidates = final_candidates[:10]
    
    # Print Top 10
    print(f"\n{'Rank':<5} {'Address':<44} {'PnL ($)':<12} {'ROI':<8} {'Sim ROI':<8} {'Profile Link'}")
    print("-" * 130)
    for i, t in enumerate(final_candidates):
        roi = (t['pnl'] / t['vol']) * 100 if t['vol'] > 0 else 0
        sim_roi = t.get('sim_roi_percent', 0)
        print(f"{t.get('rank', 'N/A'):<5} {t['proxyWallet']:<44} {t['pnl']:<12.0f} {roi:<8.1f}% {sim_roi:<8.1f}% {t['profile_url']}")
        
    # Save to disk
    csv_path = os.path.join(output_config.OUTPUT_DIR, output_config.FILENAME_CSV)
    json_path = os.path.join(output_config.OUTPUT_DIR, output_config.FILENAME_JSON)
    
    save_to_csv(final_candidates, csv_path)
    save_to_json(final_candidates, json_path)

if __name__ == "__main__":
    main()
