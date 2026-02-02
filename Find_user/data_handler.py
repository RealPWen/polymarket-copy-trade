"""
Data Handler: Manages API communication with Polymarket.
"""

import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List, Dict, Optional, Any
from tqdm import tqdm

from config import api_config
from utils import logger

class DataHandler:
    def __init__(self):
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=api_config.MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        return session

    def fetch_leaderboard_all(self, limit: int = 500) -> List[Dict[str, Any]]:
        """
        Fetch top N traders from the leaderboard.
        """
        all_traders = []
        offset = 0
        
        logger.info(f"Fetching Top {limit} traders from Leaderboard...")
        
        pbar = tqdm(total=limit, desc="Leaderboard", unit="traders")
        
        while offset < limit:
            batch_limit = min(api_config.BATCH_SIZE, limit - offset)
            params = {
                "category": "OVERALL",
                "timePeriod": "ALL",
                "orderBy": "PNL",
                "limit": batch_limit,
                "offset": offset
            }
            
            try:
                resp = self.session.get(api_config.LEADERBOARD_URL, params=params, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    if not data:
                        break
                    
                    all_traders.extend(data)
                    offset += len(data)
                    pbar.update(len(data))
                    
                    time.sleep(api_config.REQUEST_DELAY)
                else:
                    logger.error(f"API Error {resp.status_code}: {resp.text}")
                    break
            except Exception as e:
                logger.error(f"Request failed: {e}")
                break
                
        pbar.close()
        return all_traders

    def fetch_user_closed_positions(self, wallet_address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch closed positions for a specific user to analyze trade history.
        We use closed-positions endpoint as it's cleaner for PnL analysis.
        """
        params = {
            "user": wallet_address,
            "limit": limit,
            "offset": 0
        }
        
        try:
            # Note: This endpoint is used for detailed PnL breakdown per trade
            resp = self.session.get(api_config.POSITIONS_URL, params=params, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            else:
                # logger.warning(f"Failed to fetch positions for {wallet_address[:6]}... ({resp.status_code})")
                return []
        except Exception as e:
            # logger.warning(f"Error fetching positions for {wallet_address[:6]}...: {e}")
            return []

    def fetch_user_trades(self, wallet_address: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch raw trade history (BUY/SELL) for simulation.
        """
        params = {
            "user": wallet_address,
            "limit": limit,
            "offset": 0
        }
        
        try:
            resp = self.session.get(api_config.TRADES_URL, params=params, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            else:
                return []
        except Exception as e:
            return []

    def fetch_user_active_positions(self, wallet_address: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch OPEN positions for a specific user to evaluate floating PnL.
        """
        params = {
            "user": wallet_address,
            "limit": limit
        }
        
        try:
            resp = self.session.get(api_config.POSITIONS_ACTIVE_URL, params=params, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            else:
                return []
        except Exception as e:
            # logger.warning(f"Error fetching active positions for {wallet_address[:6]}: {e}")
            return []
