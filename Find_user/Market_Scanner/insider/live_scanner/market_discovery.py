"""
Market Discovery Module

Fetches active markets from Polymarket API and filters for:
1. High volume (liquidity)
2. Approaching end time
3. Non-converged prices (profit opportunity)
4. Still accepting orders
"""
import sys
import requests
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
import json

sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class MarketInfo:
    """Information about an active market."""
    market_id: int
    condition_id: str
    question: str
    slug: str
    volume: float
    end_date: datetime
    hours_until_end: float
    yes_price: float
    no_price: float
    token1_id: str  # YES token
    token2_id: str  # NO token
    accepting_orders: bool
    neg_risk: bool
    
    def to_dict(self) -> dict:
        return {
            "market_id": self.market_id,
            "condition_id": self.condition_id,
            "question": self.question,
            "slug": self.slug,
            "volume": self.volume,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "hours_until_end": round(self.hours_until_end, 2),
            "yes_price": self.yes_price,
            "no_price": self.no_price,
            "accepting_orders": self.accepting_orders,
        }


class MarketDiscovery:
    """
    Discover active markets from Polymarket API.
    
    Usage:
        discovery = MarketDiscovery()
        markets = discovery.get_active_markets()
    """
    
    GAMMA_API = "https://gamma-api.polymarket.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def _parse_market(self, data: dict) -> Optional[MarketInfo]:
        """Parse market data from API response."""
        try:
            # Get basic info
            market_id = int(data.get("id", 0))
            if not market_id:
                return None
            
            condition_id = data.get("conditionId", "")
            question = data.get("question") or data.get("title", "")
            slug = data.get("slug", "")
            
            # Volume
            volume = float(data.get("volume", 0) or 0)
            
            # End date
            end_date_str = data.get("endDate")
            if not end_date_str:
                return None
            
            end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            hours_until_end = (end_date - now).total_seconds() / 3600
            
            # Prices
            outcome_prices = data.get("outcomePrices")
            if outcome_prices:
                if isinstance(outcome_prices, str):
                    outcome_prices = json.loads(outcome_prices)
                yes_price = float(outcome_prices[0]) if outcome_prices else 0.5
                no_price = float(outcome_prices[1]) if len(outcome_prices) > 1 else (1 - yes_price)
            else:
                yes_price = 0.5
                no_price = 0.5
            
            # Token IDs
            clob_token_ids = data.get("clobTokenIds")
            if clob_token_ids:
                if isinstance(clob_token_ids, str):
                    clob_token_ids = json.loads(clob_token_ids)
                token1_id = clob_token_ids[0] if clob_token_ids else ""
                token2_id = clob_token_ids[1] if len(clob_token_ids) > 1 else ""
            else:
                token1_id = ""
                token2_id = ""
            
            # Status
            accepting_orders = data.get("acceptingOrders", True)
            neg_risk = data.get("negRisk", False)
            
            return MarketInfo(
                market_id=market_id,
                condition_id=condition_id,
                question=question,
                slug=slug,
                volume=volume,
                end_date=end_date,
                hours_until_end=hours_until_end,
                yes_price=yes_price,
                no_price=no_price,
                token1_id=token1_id,
                token2_id=token2_id,
                accepting_orders=accepting_orders,
                neg_risk=neg_risk,
            )
        except Exception as e:
            return None
    
    def get_active_markets(
        self,
        min_volume: float = 100000,
        hours_range: Tuple[float, float] = (1, 72),
        price_range: Tuple[float, float] = (0.15, 0.85),
        only_accepting_orders: bool = True,
        limit: int = 500
    ) -> List[MarketInfo]:
        """
        Get active markets matching criteria.
        
        Args:
            min_volume: Minimum market volume in USD
            hours_range: (min_hours, max_hours) until end date
            price_range: (min_price, max_price) to filter converged markets
            only_accepting_orders: Only include markets still accepting orders
            limit: Maximum markets to fetch from API
            
        Returns:
            List of MarketInfo matching criteria
        """
        print("[INFO] Fetching active markets from Polymarket API...")
        
        markets = []
        offset = 0
        batch_size = 100
        
        while len(markets) < limit:
            try:
                response = self.session.get(
                    f"{self.GAMMA_API}/markets",
                    params={
                        "closed": "false",  # Only open markets
                        "order": "volume",
                        "ascending": "false",  # Highest volume first
                        "limit": batch_size,
                        "offset": offset
                    },
                    timeout=30
                )
                
                if response.status_code != 200:
                    print(f"[WARNING] API returned {response.status_code}")
                    break
                
                data = response.json()
                if not data:
                    break
                
                for item in data:
                    market = self._parse_market(item)
                    if market is None:
                        continue
                    
                    # Apply filters
                    if market.volume < min_volume:
                        continue
                    
                    if not (hours_range[0] <= market.hours_until_end <= hours_range[1]):
                        continue
                    
                    if not (price_range[0] <= market.yes_price <= price_range[1]):
                        continue
                    
                    if only_accepting_orders and not market.accepting_orders:
                        continue
                    
                    markets.append(market)
                
                offset += batch_size
                
                # Stop if we got fewer than batch_size (no more data)
                if len(data) < batch_size:
                    break
                    
            except requests.exceptions.RequestException as e:
                print(f"[ERROR] API request failed: {e}")
                break
        
        # Sort by hours_until_end (soonest first)
        markets.sort(key=lambda m: m.hours_until_end)
        
        print(f"[INFO] Found {len(markets)} markets matching criteria")
        return markets
    
    def get_market_by_id(self, market_id: int) -> Optional[MarketInfo]:
        """Fetch a specific market by ID."""
        try:
            response = self.session.get(
                f"{self.GAMMA_API}/markets/{market_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                return self._parse_market(response.json())
            return None
        except Exception:
            return None
    
    def get_market_by_slug(self, slug: str) -> Optional[MarketInfo]:
        """Fetch a specific market by slug."""
        try:
            response = self.session.get(
                f"{self.GAMMA_API}/markets",
                params={"slug": slug},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return self._parse_market(data[0])
            return None
        except Exception:
            return None


# =============================================================================
# CLI for testing
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Discover active Polymarket markets")
    parser.add_argument("--min-volume", type=float, default=100000, help="Min volume USD")
    parser.add_argument("--hours-min", type=float, default=1, help="Min hours until end")
    parser.add_argument("--hours-max", type=float, default=72, help="Max hours until end")
    parser.add_argument("--limit", type=int, default=50, help="Max markets to show")
    args = parser.parse_args()
    
    discovery = MarketDiscovery()
    markets = discovery.get_active_markets(
        min_volume=args.min_volume,
        hours_range=(args.hours_min, args.hours_max),
        limit=args.limit
    )
    
    print(f"\n{'='*80}")
    print(f"ACTIVE MARKETS ({len(markets)} found)")
    print(f"{'='*80}\n")
    
    for i, m in enumerate(markets[:20], 1):
        print(f"{i:3d}. [{m.hours_until_end:5.1f}h] ${m.volume/1000:.0f}K | YES: {m.yes_price:.2f} | {m.question[:50]}...")
    
    if len(markets) > 20:
        print(f"... and {len(markets) - 20} more")
