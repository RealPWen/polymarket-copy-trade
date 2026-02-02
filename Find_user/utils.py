"""
Utility functions for logging and formatting.
"""

import logging
import sys
import os
import json
import pandas as pd
from typing import Dict, List, Any

# Configure Logger
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("SmartTrader")

def setup_output_dir(directory: str):
    """Ensure output directory exists"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def save_to_csv(data: List[Dict[str, Any]], filepath: str):
    """Save list of dicts to CSV"""
    if not data:
        logger.warning("No data to save.")
        return
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    logger.info(f"Saved {len(data)} records to {filepath}")

def save_to_json(data: List[Dict[str, Any]], filepath: str):
    """Save list of dicts to JSON"""
    if not data:
        return
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved JSON to {filepath}")
