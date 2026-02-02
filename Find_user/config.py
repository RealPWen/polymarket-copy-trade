"""
Configuration settings for the Smart Trader Discovery Engine.
"""

from dataclasses import dataclass

@dataclass
class APIConfig:
    LEADERBOARD_URL = "https://data-api.polymarket.com/v1/leaderboard"
    TRADES_URL = "https://data-api.polymarket.com/trades"  # For history
    POSITIONS_URL = "https://data-api.polymarket.com/v1/closed-positions" # Alternative for PnL
    POSITIONS_ACTIVE_URL = "https://data-api.polymarket.com/positions" # Active positions
    
    # Rate Limiting
    REQUEST_DELAY = 0.2
    MAX_RETRIES = 3
    
    # Leaderboard Fetching
    FETCH_LIMIT = 500  # How many top traders to fetch initially
    BATCH_SIZE = 50   # Max API limit per request
    
    # Profile URL Construction
    PROFILE_URL_PREFIX = "https://polymarket.com/profile/"

@dataclass
class FilterConfig:
    # 1. Market Maker Logic
    # High volume but low PnL/Volume ratio = Market Maker
    MM_VOLUME_THRESHOLD = 500_000   # > $500k volume
    MM_ROI_THRESHOLD = 0.05         # < 5% ROI

    # 2. Capital Threshold
    MIN_TOTAL_PROFIT = 1_000        # Minimum $1,000 PnL

    # 3. Consistency (One-Hit Wonder)
    # If single best trade accounts for > X% of total pnl
    MAX_SINGLE_TRADE_RATIO = 0.90   # 90%

    # 4. Inactivity Filter
    MAX_INACTIVITY_DAYS = 21        # Exclude if no trades in last 21 days

@dataclass
class OutputConfig:
    OUTPUT_DIR = "output"
    FILENAME_CSV = "smart_traders_final.csv"
    FILENAME_JSON = "smart_traders_final.json"

# Instantiate for global access
api_config = APIConfig()
filter_config = FilterConfig()
output_config = OutputConfig()
