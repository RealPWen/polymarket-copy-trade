"""
Trade Fetcher Module

Fetches real-time trade data from Goldsky Subgraph.
Supports both full fetch and incremental updates.
"""
import sys
import time
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Goldsky API endpoint
GOLDSKY_URL = "https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/orderbook-subgraph/0.0.1/gn"

# Local archive for market metadata
ARCHIVE_DIR = Path(__file__).parent.parent.parent / "archive"
MARKETS_FILE = ARCHIVE_DIR / "markets.csv"


class TradeFetcher:
    """
    Fetch trade data from Goldsky Subgraph.
    
    Usage:
        fetcher = TradeFetcher()
        trades_df = fetcher.fetch_recent_trades(market_id=12345, lookback_days=30)
    """
    
    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size
        self._markets_cache: Optional[pd.DataFrame] = None
        self._token_to_market: Dict[str, int] = {}
    
    def _load_markets(self):
        """Load markets metadata for token->market mapping."""
        if self._markets_cache is None:
            if MARKETS_FILE.exists():
                self._markets_cache = pd.read_csv(MARKETS_FILE, dtype={"token1": str, "token2": str})
                
                # Build token to market mapping
                for _, row in self._markets_cache.iterrows():
                    market_id = row.get("id")
                    token1 = str(row.get("token1", ""))
                    token2 = str(row.get("token2", ""))
                    
                    if token1 and token1 != "nan":
                        self._token_to_market[token1] = market_id
                    if token2 and token2 != "nan":
                        self._token_to_market[token2] = market_id
            else:
                self._markets_cache = pd.DataFrame()
    
    def _get_market_tokens(self, market_id: int) -> tuple:
        """Get token1 and token2 for a market."""
        self._load_markets()
        
        if self._markets_cache is None or len(self._markets_cache) == 0:
            return None, None
        
        row = self._markets_cache[self._markets_cache["id"] == market_id]
        if len(row) == 0:
            return None, None
        
        token1 = str(row.iloc[0].get("token1", ""))
        token2 = str(row.iloc[0].get("token2", ""))
        
        return token1 if token1 != "nan" else None, token2 if token2 != "nan" else None
    
    def _query_goldsky(self, query: str) -> Optional[dict]:
        """Execute GraphQL query against Goldsky."""
        try:
            from gql import gql, Client
            from gql.transport.requests import RequestsHTTPTransport
            
            transport = RequestsHTTPTransport(url=GOLDSKY_URL, verify=True, retries=3)
            client = Client(transport=transport)
            result = client.execute(gql(query))
            return result
        except Exception as e:
            print(f"[ERROR] Goldsky query failed: {e}")
            return None
    
    def fetch_by_token(
        self,
        token_id: str,
        since_timestamp: int = 0,
        max_records: int = 10000
    ) -> pd.DataFrame:
        """
        Fetch trades for a specific token ID.
        
        Args:
            token_id: The asset token ID (token1 or token2)
            since_timestamp: Only fetch trades after this timestamp
            max_records: Maximum records to fetch
            
        Returns:
            DataFrame with trade data
        """
        all_events = []
        last_timestamp = since_timestamp
        last_id = None
        sticky_timestamp = None
        
        while len(all_events) < max_records:
            # Build where clause
            if sticky_timestamp is not None:
                where = f'timestamp: "{sticky_timestamp}", id_gt: "{last_id}"'
            else:
                where = f'timestamp_gt: "{last_timestamp}"'
            
            # Query for both maker and taker asset
            query = f'''query {{
                orderFilledEvents(
                    orderBy: timestamp, 
                    orderDirection: asc,
                    first: {self.batch_size}, 
                    where: {{{where}, or: [
                        {{makerAssetId: "{token_id}"}},
                        {{takerAssetId: "{token_id}"}}
                    ]}}
                ) {{
                    id timestamp maker makerAssetId makerAmountFilled
                    taker takerAssetId takerAmountFilled transactionHash
                }}
            }}'''
            
            result = self._query_goldsky(query)
            if result is None:
                break
            
            events = result.get("orderFilledEvents", [])
            if not events:
                break
            
            all_events.extend(events)
            
            # Update pagination cursor
            last_event = events[-1]
            batch_ts = int(last_event["timestamp"])
            batch_id = last_event["id"]
            
            if len(events) >= self.batch_size:
                sticky_timestamp = batch_ts
                last_id = batch_id
            else:
                if sticky_timestamp is not None:
                    last_timestamp = sticky_timestamp
                    sticky_timestamp = None
                    last_id = None
                else:
                    break
            
            # Rate limiting
            time.sleep(0.1)
        
        if not all_events:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(all_events)
        df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), unit="s", utc=True)
        df["makerAmountFilled"] = df["makerAmountFilled"].astype(float) / 1e6
        df["takerAmountFilled"] = df["takerAmountFilled"].astype(float) / 1e6
        
        return df
    
    def fetch_recent_trades(
        self,
        market_id: int,
        lookback_days: int = 30,
        max_records: int = 50000
    ) -> pd.DataFrame:
        """
        Fetch recent trades for a market.
        
        Args:
            market_id: The market ID
            lookback_days: How many days of history to fetch
            max_records: Maximum records to fetch
            
        Returns:
            DataFrame with processed trade data
        """
        token1, token2 = self._get_market_tokens(market_id)
        
        if not token1:
            print(f"[WARNING] No token found for market {market_id}")
            return pd.DataFrame()
        
        since_ts = int((datetime.now(timezone.utc) - timedelta(days=lookback_days)).timestamp())
        
        print(f"[INFO] Fetching trades for market {market_id} (last {lookback_days} days)...")
        
        # Fetch trades for token1 (YES)
        df1 = self.fetch_by_token(token1, since_timestamp=since_ts, max_records=max_records)
        
        # Fetch trades for token2 (NO) if exists
        df2 = pd.DataFrame()
        if token2:
            df2 = self.fetch_by_token(token2, since_timestamp=since_ts, max_records=max_records)
        
        # Combine
        if len(df1) == 0 and len(df2) == 0:
            return pd.DataFrame()
        
        df = pd.concat([df1, df2], ignore_index=True)
        df = df.drop_duplicates(subset=["id"])
        df = df.sort_values("timestamp").reset_index(drop=True)
        
        # Process into standard trade format
        trades = self._process_trades(df, token1, token2, market_id)
        
        print(f"[INFO] Fetched {len(trades)} trades for market {market_id}")
        return trades
    
    def _process_trades(
        self,
        df: pd.DataFrame,
        token1: str,
        token2: str,
        market_id: int
    ) -> pd.DataFrame:
        """Process raw order events into trade format."""
        if len(df) == 0:
            return pd.DataFrame()
        
        records = []
        
        for _, row in df.iterrows():
            maker_asset = row["makerAssetId"]
            taker_asset = row["takerAssetId"]
            maker_amount = row["makerAmountFilled"]
            taker_amount = row["takerAmountFilled"]
            
            # Determine which side is the non-USDC asset
            if maker_asset == "0":  # Maker is USDC
                nonusdc_asset = taker_asset
                usd_amount = maker_amount
                token_amount = taker_amount
                taker_direction = "BUY"
                maker_direction = "SELL"
            else:  # Taker is USDC
                nonusdc_asset = maker_asset
                usd_amount = taker_amount
                token_amount = maker_amount
                taker_direction = "SELL"
                maker_direction = "BUY"
            
            # Determine token side (token1 = YES, token2 = NO)
            if nonusdc_asset == token1:
                nonusdc_side = "token1"
            elif nonusdc_asset == token2:
                nonusdc_side = "token2"
            else:
                continue  # Unknown token
            
            # Calculate price
            price = usd_amount / token_amount if token_amount > 0 else 0
            
            records.append({
                "timestamp": row["timestamp"],
                "market_id": market_id,
                "maker": row["maker"],
                "taker": row["taker"],
                "nonusdc_side": nonusdc_side,
                "maker_direction": maker_direction,
                "taker_direction": taker_direction,
                "price": price,
                "usd_amount": usd_amount,
                "token_amount": token_amount,
                "transactionHash": row["transactionHash"]
            })
        
        return pd.DataFrame(records)
    
    def fetch_incremental(
        self,
        market_id: int,
        since_timestamp: int
    ) -> pd.DataFrame:
        """
        Fetch only new trades since a given timestamp.
        For efficient incremental updates.
        """
        token1, token2 = self._get_market_tokens(market_id)
        
        if not token1:
            return pd.DataFrame()
        
        df1 = self.fetch_by_token(token1, since_timestamp=since_timestamp, max_records=5000)
        df2 = pd.DataFrame()
        if token2:
            df2 = self.fetch_by_token(token2, since_timestamp=since_timestamp, max_records=5000)
        
        if len(df1) == 0 and len(df2) == 0:
            return pd.DataFrame()
        
        df = pd.concat([df1, df2], ignore_index=True)
        df = df.drop_duplicates(subset=["id"])
        df = df.sort_values("timestamp").reset_index(drop=True)
        
        return self._process_trades(df, token1, token2, market_id)


# =============================================================================
# CLI for testing
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch trades from Goldsky")
    parser.add_argument("market_id", type=int, help="Market ID to fetch")
    parser.add_argument("--days", type=int, default=7, help="Lookback days")
    parser.add_argument("--output", type=str, help="Output CSV file")
    args = parser.parse_args()
    
    fetcher = TradeFetcher()
    trades = fetcher.fetch_recent_trades(
        market_id=args.market_id,
        lookback_days=args.days
    )
    
    if len(trades) > 0:
        print(f"\nFetched {len(trades)} trades")
        print(trades.head(10))
        
        if args.output:
            trades.to_csv(args.output, index=False)
            print(f"Saved to {args.output}")
    else:
        print("No trades found")
