"""
WebSocket 数据采集配置
"""
from pathlib import Path

# ============== 路径 ==============
PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / "data"
LOG_DIR = PROJECT_DIR / "logs"

# 确保目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ============== Polymarket WebSocket ==============
WS_MARKET_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

# ============== Gamma API (用于获取市场元数据) ==============
GAMMA_API_URL = "https://gamma-api.polymarket.com"

# ============== 上游项目的市场字典（复用） ==============
POLY_DATA_ROOT = PROJECT_DIR.parent / "polymarket_data" / "Polymarket_data"
MARKETS_FILE = POLY_DATA_ROOT / "polymarket" / "data" / "dataset" / "markets.parquet"

# ============== 运行参数 ==============
# WebSocket 断线后的重连等待时间（秒）
RECONNECT_DELAY = 3
# 最大重连次数（0 = 无限重连）
MAX_RECONNECT_ATTEMPTS = 0
# 数据落盘间隔（每收到 N 条消息后写入一次 Parquet）
FLUSH_INTERVAL = 50
# 心跳间隔（秒）- 用于检测连接是否存活
HEARTBEAT_INTERVAL = 30

# ============== 本地分发配置 (方案 A) ==============
# 本地 WebSocket 服务地址
LOCAL_WS_HOST = "0.0.0.0"
LOCAL_WS_PORT = 8081

# ============== NBA 市场过滤 ==============
# 模式: "all_nba" = 全部 NBA 市场（基于 event_title 自动分组，推荐）
#       "season" = 仅赛季级别市场（旧模式，已弃用）
#       "all" = 全部 NBA 市场（无过滤）
MARKET_FILTER_MODE = "all_nba"

# 黑名单：event_title 中包含这些关键词的市场将被排除
# （用于过滤因 question 中含 NBA 而被误匹配的非 NBA 市场）
EXCLUDED_EVENT_TITLES = [
    "Coinbase",
    "WNBA",
    "Latvian",
    "Parliamentary",
    "Netherlands",
]
