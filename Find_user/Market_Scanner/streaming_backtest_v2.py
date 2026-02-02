"""
Streaming Backtest Engine V2 - Using Polygon RPC for Complete Historical Data

This version uses direct blockchain queries to get complete trade history,
bypassing the Data API's limited retention for closed markets.
"""
import os
import sys
import json
import time
import requests
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

sys.stdout.reconfigure(encoding='utf-8')

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# Polygon RPC Configuration
# ============================================================

# Working public RPC endpoints (tested 2026-02-02)
RPC_ENDPOINTS = [
    "https://polygon-bor-rpc.publicnode.com",
    "https://polygon.drpc.org",
]

# Polymarket Contract Addresses
CTF_EXCHANGE = "0x4bFb41d5B3570DeFd03C39a9A4D8dE6BD8B8982E"
NEG_RISK_CTF_EXCHANGE = "0xC5d563A36AE78145C45a50134d48A1215220f80a"

# OrderFilled event signature
ORDER_FILLED_TOPIC = "0xd0a08e8c493f9c94f29311604c9de1b4e8c8d4c06bd0c789af57f2d65bfec0f6"

# Max blocks per RPC request (public RPC limit)
MAX_BLOCKS_PER_REQUEST = 10

# Polygon block rate (~2 seconds per block)
BLOCKS_PER_DAY = 43200

# ============================================================
# Known Insiders for Validation
# ============================================================

KNOWN_INSIDERS = [
    "0x56687bf447db6ffa42ffe2204a05edaa20f55839",  # Theo4
    "0x2bf64b86b64c315d879571b07a3b76629e467cd0",  # BabaTrump
    "0x8119010a6e589062aa03583bb3f39ca632d9f887",  # PrincessCaro
]

# Thresholds for noise filtering
MIN_VOLUME_USD = 1000
MM_BALANCE_THRESHOLD = 0.2

# ============================================================
# Polygon RPC Client
# ============================================================

class PolygonRPCClient:
    """Client for querying Polygon blockchain."""
    
    def __init__(self):
        self.rpc_url = self._find_working_rpc()
        print(f"[RPC] Connected to: {self.rpc_url}")
    
    def _find_working_rpc(self) -> str:
        for rpc in RPC_ENDPOINTS:
            try:
                r = requests.post(
                    rpc,
                    json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1},
                    timeout=5
                )
                if r.status_code == 200 and "result" in r.json():
                    return rpc
            except:
                continue
        raise Exception("No working RPC endpoint found")
    
    def get_current_block(self) -> int:
        r = requests.post(
            self.rpc_url,
            json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}
        )
        return int(r.json()["result"], 16)
    
    def get_block_by_timestamp(self, target_timestamp: int) -> int:
        """Estimate block number for a given timestamp."""
        current_block = self.get_current_block()
        current_time = int(time.time())
        
        # Polygon: ~2 second block time
        blocks_diff = (current_time - target_timestamp) // 2
        estimated_block = current_block - blocks_diff
        
        return max(1, estimated_block)
    
    def get_logs(self, from_block: int, to_block: int, contract: str, topics: List[str]) -> List[dict]:
        params = [{
            "fromBlock": hex(from_block),
            "toBlock": hex(to_block),
            "address": contract,
            "topics": topics
        }]
        
        try:
            r = requests.post(
                self.rpc_url,
                json={"jsonrpc": "2.0", "method": "eth_getLogs", "params": params, "id": 1},
                timeout=30
            )
            data = r.json()
            if "error" in data:
                return []
            return data.get("result", [])
        except:
            return []


# ============================================================
# Trade Parser
# ============================================================

def parse_order_filled_log(log: dict) -> Optional[dict]:
    """Parse OrderFilled event into trade data."""
    topics = log.get("topics", [])
    data = log.get("data", "0x")
    
    if len(topics) < 4:
        return None
    
    # Extract addresses
    maker = "0x" + topics[2][-40:]
    taker = "0x" + topics[3][-40:]
    
    # Parse data fields
    data_hex = data[2:] if data.startswith("0x") else data
    
    if len(data_hex) >= 320:
        maker_asset_id = int(data_hex[0:64], 16)
        taker_asset_id = int(data_hex[64:128], 16)
        maker_amount = int(data_hex[128:192], 16)
        taker_amount = int(data_hex[192:256], 16)
        fee = int(data_hex[256:320], 16)
    else:
        return None
    
    # Determine trade direction
    # If maker_asset_id is 0, maker is selling USDC (buying outcome tokens)
    # If taker_asset_id is 0, taker is selling USDC (buying outcome tokens)
    
    # For our analysis, we care about the non-zero asset ID (the outcome token)
    if maker_asset_id == 0:
        # Maker is the buyer (paying USDC)
        asset_id = str(taker_asset_id)
        buyer = maker.lower()
        seller = taker.lower()
        usdc_amount = maker_amount  # USDC paid by maker
        shares = taker_amount       # Shares received
    else:
        # Taker is the buyer (paying USDC)
        asset_id = str(maker_asset_id)
        buyer = taker.lower()
        seller = maker.lower()
        usdc_amount = taker_amount  # USDC paid by taker
        shares = maker_amount       # Shares received
    
    # USDC has 6 decimals
    usdc_value = usdc_amount / 1e6
    share_count = shares / 1e6  # Outcome tokens also have 6 decimals
    
    block_timestamp = log.get("blockTimestamp")
    if block_timestamp:
        timestamp = int(block_timestamp, 16)
    else:
        timestamp = 0
    
    return {
        "block_number": int(log.get("blockNumber", "0x0"), 16),
        "tx_hash": log.get("transactionHash"),
        "timestamp": timestamp,
        "asset_id": asset_id,
        "buyer": buyer,
        "seller": seller,
        "usdc_value": usdc_value,
        "shares": share_count,
        "fee": fee / 1e6
    }


# ============================================================
# Wallet Profile
# ============================================================

@dataclass
class WalletProfile:
    """Track wallet activity in the market."""
    address: str
    total_buy_volume_usd: float = 0.0
    total_sell_volume_usd: float = 0.0
    total_buy_shares: float = 0.0
    total_sell_shares: float = 0.0
    trade_count: int = 0
    max_trade_size_usd: float = 0.0
    trade_sizes: List[float] = field(default_factory=list)
    first_seen_ts: float = 0.0
    last_seen_ts: float = 0.0
    asset_ids: Set[str] = field(default_factory=set)
    
    @property
    def total_volume_usd(self) -> float:
        return self.total_buy_volume_usd + self.total_sell_volume_usd
    
    @property
    def net_flow_usd(self) -> float:
        return self.total_buy_volume_usd - self.total_sell_volume_usd
    
    @property
    def directional_ratio(self) -> float:
        if self.total_volume_usd == 0:
            return 0
        return abs(self.net_flow_usd) / self.total_volume_usd
    
    @property
    def size_anomaly_ratio(self) -> float:
        if len(self.trade_sizes) < 3:
            return 1.0
        sorted_sizes = sorted(self.trade_sizes)
        median = sorted_sizes[len(sorted_sizes) // 2]
        if median == 0:
            return 1.0
        return self.max_trade_size_usd / median
    
    @property
    def activity_days(self) -> float:
        if self.first_seen_ts == 0 or self.last_seen_ts == 0:
            return 0
        return (self.last_seen_ts - self.first_seen_ts) / 86400


# ============================================================
# Wallet Profiler
# ============================================================

class WalletProfiler:
    """Build profiles from trade stream."""
    
    def __init__(self, target_asset_ids: Set[str] = None):
        self.profiles: Dict[str, WalletProfile] = {}
        self.target_asset_ids = target_asset_ids  # Filter for specific market
    
    def process_trade(self, trade: dict):
        """Process a single trade."""
        asset_id = trade.get("asset_id")
        
        # If target assets specified, filter
        if self.target_asset_ids and asset_id not in self.target_asset_ids:
            return
        
        buyer = trade.get("buyer")
        seller = trade.get("seller")
        usdc = trade.get("usdc_value", 0)
        shares = trade.get("shares", 0)
        ts = trade.get("timestamp", 0)
        
        if usdc <= 0:
            return
        
        # Update buyer profile
        if buyer and not buyer.startswith(CTF_EXCHANGE.lower()[:10]):
            self._update(buyer, "BUY", usdc, shares, ts, asset_id)
        
        # Update seller profile
        if seller and not seller.startswith(CTF_EXCHANGE.lower()[:10]):
            self._update(seller, "SELL", usdc, shares, ts, asset_id)
    
    def _update(self, addr: str, side: str, usd: float, shares: float, ts: float, asset_id: str):
        if addr not in self.profiles:
            self.profiles[addr] = WalletProfile(address=addr, first_seen_ts=ts)
        
        p = self.profiles[addr]
        p.trade_count += 1
        p.last_seen_ts = max(p.last_seen_ts, ts)
        p.trade_sizes.append(usd)
        p.asset_ids.add(asset_id)
        
        if usd > p.max_trade_size_usd:
            p.max_trade_size_usd = usd
        
        if side == "BUY":
            p.total_buy_volume_usd += usd
            p.total_buy_shares += shares
        else:
            p.total_sell_volume_usd += usd
            p.total_sell_shares += shares
    
    def get_profiles(self) -> List[WalletProfile]:
        return list(self.profiles.values())


# ============================================================
# Noise Filter & Insider Detector (same as before)
# ============================================================

class NoiseFilter:
    def __init__(self, min_volume: float = MIN_VOLUME_USD, mm_threshold: float = MM_BALANCE_THRESHOLD):
        self.min_volume = min_volume
        self.mm_threshold = mm_threshold
    
    def filter(self, profiles: List[WalletProfile]) -> List[WalletProfile]:
        filtered = []
        for p in profiles:
            if p.total_volume_usd < self.min_volume:
                continue
            if p.directional_ratio < self.mm_threshold:
                continue
            filtered.append(p)
        return filtered


class InsiderDetector:
    def calculate_score(self, profile: WalletProfile) -> dict:
        score = 0
        signals = []
        
        # 1. Directional Bias
        dir_ratio = profile.directional_ratio
        if dir_ratio > 0.95:
            score += 50
            signals.append("EXTREME_DIRECTIONAL")
        elif dir_ratio > 0.85:
            score += 35
            signals.append("HIGH_DIRECTIONAL")
        elif dir_ratio > 0.70:
            score += 20
            signals.append("MODERATE_DIRECTIONAL")
        
        # 2. Size Anomaly
        size_ratio = profile.size_anomaly_ratio
        if size_ratio > 50:
            score += 40
            signals.append("EXTREME_SIZE_ANOMALY")
        elif size_ratio > 20:
            score += 25
            signals.append("HIGH_SIZE_ANOMALY")
        elif size_ratio > 10:
            score += 15
            signals.append("MODERATE_SIZE_ANOMALY")
        
        # 3. Volume
        vol = profile.total_volume_usd
        if vol > 500000:
            score += 30
            signals.append("WHALE_VOLUME")
        elif vol > 100000:
            score += 20
            signals.append("HIGH_VOLUME")
        elif vol > 50000:
            score += 10
            signals.append("MODERATE_VOLUME")
        
        # 4. One-shot trader
        if 0 < profile.activity_days < 7 and profile.total_volume_usd > 10000:
            score += 25
            signals.append("ONE_SHOT_TRADER")
        
        return {
            "address": profile.address,
            "score": score,
            "signals": signals,
            "details": {
                "total_volume_usd": round(profile.total_volume_usd, 2),
                "net_flow_usd": round(profile.net_flow_usd, 2),
                "directional_ratio": round(dir_ratio, 3),
                "size_anomaly_ratio": round(size_ratio, 1),
                "trade_count": profile.trade_count,
                "max_trade_usd": round(profile.max_trade_size_usd, 2),
                "activity_days": round(profile.activity_days, 1),
                "num_assets": len(profile.asset_ids)
            }
        }


# ============================================================
# Main Backtest Function
# ============================================================

def fetch_trades_for_period(
    start_timestamp: int,
    end_timestamp: int,
    progress_callback=None
) -> List[dict]:
    """
    Fetch all Polymarket trades for a time period using Polygon RPC.
    """
    client = PolygonRPCClient()
    
    # Convert timestamps to block numbers
    start_block = client.get_block_by_timestamp(start_timestamp)
    end_block = client.get_block_by_timestamp(end_timestamp)
    
    # Ensure end_block is not in the future
    current_block = client.get_current_block()
    end_block = min(end_block, current_block)
    
    print(f"[FETCH] Block range: {start_block:,} to {end_block:,}")
    print(f"[FETCH] Total blocks: {end_block - start_block:,}")
    
    all_trades = []
    current = start_block
    batch_count = 0
    
    while current < end_block:
        batch_end = min(current + MAX_BLOCKS_PER_REQUEST, end_block)
        
        for contract in [CTF_EXCHANGE, NEG_RISK_CTF_EXCHANGE]:
            logs = client.get_logs(current, batch_end, contract, [ORDER_FILLED_TOPIC])
            
            for log in logs:
                trade = parse_order_filled_log(log)
                if trade:
                    all_trades.append(trade)
        
        batch_count += 1
        if batch_count % 50 == 0:
            print(f"[FETCH] Processed {batch_count} batches, {len(all_trades):,} trades...")
        
        current = batch_end + 1
        time.sleep(0.3)  # Rate limiting
    
    print(f"[FETCH] Complete: {len(all_trades):,} trades fetched")
    return all_trades


def run_backtest(
    trades: List[dict],
    target_asset_ids: Set[str] = None,
    known_insiders: List[str] = None
) -> dict:
    """
    Run the streaming backtest on a set of trades.
    """
    print("\n" + "="*70)
    print("STREAMING BACKTEST ENGINE V2 - Polygon RPC Data")
    print("="*70)
    
    if target_asset_ids:
        print(f"Filtering for {len(target_asset_ids)} target asset IDs")
    
    # 1. Profile wallets
    profiler = WalletProfiler(target_asset_ids)
    
    for trade in trades:
        profiler.process_trade(trade)
    
    all_profiles = profiler.get_profiles()
    print(f"\nTotal wallets profiled: {len(all_profiles)}")
    
    # 2. Filter noise
    noise_filter = NoiseFilter()
    filtered = noise_filter.filter(all_profiles)
    print(f"After noise filtering: {len(filtered)} wallets")
    
    # 3. Score
    detector = InsiderDetector()
    results = [detector.calculate_score(p) for p in filtered]
    results.sort(key=lambda x: x["score"], reverse=True)
    
    # 4. Display top suspects
    print("\n" + "="*70)
    print("TOP 20 SUSPECTED INSIDERS")
    print("="*70)
    
    known_lower = [k.lower() for k in (known_insiders or [])]
    
    for i, r in enumerate(results[:20]):
        addr = r["address"]
        is_known = addr.lower() in known_lower
        marker = " [KNOWN INSIDER]" if is_known else ""
        
        print(f"\n#{i+1} [Score: {r['score']}] {addr[:12]}...{addr[-6:]}{marker}")
        print(f"   Volume: ${r['details']['total_volume_usd']:,.0f} | Net: ${r['details']['net_flow_usd']:,.0f}")
        print(f"   Directional: {r['details']['directional_ratio']:.0%} | Size Anomaly: {r['details']['size_anomaly_ratio']:.1f}x")
        print(f"   Signals: {', '.join(r['signals']) if r['signals'] else 'None'}")
    
    # 5. Validation
    if known_insiders:
        print("\n" + "="*70)
        print("VALIDATION")
        print("="*70)
        
        top_20_addrs = [r["address"].lower() for r in results[:20]]
        detected = []
        missed = []
        
        for insider in known_insiders:
            if insider.lower() in top_20_addrs:
                rank = top_20_addrs.index(insider.lower()) + 1
                detected.append((insider, rank))
            elif insider.lower() in [p.address.lower() for p in all_profiles]:
                missed.append(insider)
        
        print(f"\nDetected in Top 20: {len(detected)} / {len(known_insiders)}")
        for addr, rank in detected:
            print(f"  [SUCCESS] {addr[:16]}... at Rank #{rank}")
        
        if missed:
            print(f"\nMissed (but traded):")
            for addr in missed:
                for i, r in enumerate(results):
                    if r["address"].lower() == addr.lower():
                        print(f"  [MISSED] {addr[:16]}... Actual Rank: #{i+1}, Score: {r['score']}")
                        break
    
    return {
        "total_trades": len(trades),
        "total_wallets": len(all_profiles),
        "filtered_wallets": len(filtered),
        "top_suspects": results[:50],
        "validation": {
            "known_insiders": known_insiders or [],
            "detected": [addr for addr, _ in detected] if known_insiders else [],
            "missed": missed if known_insiders else []
        }
    }


# ============================================================
# Quick Test
# ============================================================

def quick_test():
    """Quick test with recent trades (last 30 minutes)."""
    print("="*70)
    print("QUICK TEST - Last 30 minutes of all Polymarket trades")
    print("="*70)
    
    # Fetch last 30 minutes
    end_ts = int(time.time())
    start_ts = end_ts - 1800  # 30 minutes
    
    trades = fetch_trades_for_period(start_ts, end_ts)
    
    if not trades:
        print("[ERROR] No trades fetched")
        return
    
    # Run backtest on all trades (no market filter)
    results = run_backtest(trades, target_asset_ids=None, known_insiders=KNOWN_INSIDERS)
    
    # Save results
    output_file = os.path.join(OUTPUT_DIR, "backtest_v2_quick.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    quick_test()
