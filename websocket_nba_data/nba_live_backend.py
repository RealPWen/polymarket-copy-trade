#!/usr/bin/env python3
"""
NBA 实时看板后端 - 方案 A
1. 连接 Polymarket WebSocket 抓取 NBA 数据
2. 启动本地 WebSocket 服务，将数据秒级推送到浏览器
3. 同时保持数据落盘功能
"""
import asyncio
import json
import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
import websockets

import pandas as pd
from config import (
    DATA_DIR, LOG_DIR, FLUSH_INTERVAL, 
    LOCAL_WS_HOST, LOCAL_WS_PORT
)
from ws_client import PolymarketWSClient
from nba_ws_monitor import get_nba_tokens_from_local, get_nba_tokens_from_api, NBADataCollector

# ============== 日志配置 ==============
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("NBA_Live_Backend")

class LiveRelayServer:
    """本地 WebSocket 分发服务器 - 增加历史记录持久化"""
    def __init__(self, initial_history=None):
        self.clients = set()
        self.market_history = initial_history or {} # asset_id -> list of history events
        self.max_history = 2000   # 每个市场保留最近 2000 个成交点（约支持 1-2 天的高频成交）

    async def register(self, websocket):
        self.clients.add(websocket)
        logger.info(f"🌐 新网页已连接 (当前共 {len(self.clients)} 个连接)")
        
        # 将缓存的所有市场的历史数据发给新连接
        if self.market_history:
            # 展平所有历史点，按时间排序
            all_history = []
            for asset_id in self.market_history:
                all_history.extend(self.market_history[asset_id])
            
            await websocket.send(json.dumps({
                "type": "init",
                "data": all_history
            }))
            
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)
            logger.info(f"👋 网页已断开 (剩余 {len(self.clients)} 个连接)")

    async def broadcast(self, message: dict):
        """将数据广播给所有已连接的浏览器并缓存成交历史"""
        if not self.clients and not message.get("event_type") == "last_trade_price":
            # 如果没有客户端且不是成交，没必要处理（暂不缓存非成交报价以节省内存）
            pass
            
        # 更新历史缓存 (仅缓存成交点以供折线图绘制)
        asset_id = message.get("asset_id")
        event_type = message.get("event_type")
        is_trade = event_type == "last_trade_price" or (event_type == "book" and message.get("price", 0) > 0)

        if asset_id:
            if asset_id not in self.market_history:
                self.market_history[asset_id] = []
            
            # 如果是成交，记录到历史
            if is_trade:
                self.market_history[asset_id].append(message)
                if len(self.market_history[asset_id]) > self.max_history:
                    self.market_history[asset_id].pop(0)
            else:
                # 如果是报价，只更新最后一条成交记录的最新盘口信息（可选，这里为了简化，报价暂不进入 history）
                pass

        if not self.clients:
            return

        payload = json.dumps({"type": "update", "data": message})
        await asyncio.gather(
            *[client.send(payload) for client in self.clients],
            return_exceptions=True
        )

def load_recent_history_from_parquet(hours=24):
    """
    从本地 Parquet 文件加载过去 N 小时的成交历史
    """
    logger.info(f"💾 正在从磁盘加载过去 {hours} 小时的成交历史...")
    history = {}
    now_ts = time.time()
    cutoff_ts = now_ts - (hours * 3600)
    
    try:
        all_files = list(DATA_DIR.glob("nba_ws_*.parquet"))
        if not all_files:
            return history
            
        # 按修改时间排序，优先读取最新的
        all_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        for f in all_files:
            # 如果文件修改时间早于截止时间很久，可以跳过（简单优化）
            if f.stat().st_mtime < cutoff_ts:
                continue
                
            df = pd.read_parquet(f)
            # 过滤成交记录且在时间范围内
            mask = (df["event_type"] == "last_trade_price") & (df["timestamp"] >= cutoff_ts)
            trades = df[mask]
            
            if trades.empty:
                continue
                
            # 转换为字典列表注入
            for _, row in trades.iterrows():
                asset_id = row["asset_id"]
                if asset_id not in history:
                    history[asset_id] = []
                
                # 转换回字典格式
                record = row.to_dict()
                # 处理 numpy/pandas 类型转换以便 json 序列化
                for k, v in record.items():
                    if hasattr(v, "item"): record[k] = v.item()
                
                # 兼容旧 Parquet（可能缺少 event_title/event_id）
                if "event_title" not in record or pd.isna(record.get("event_title")):
                    record["event_title"] = "未分类 (历史数据)"
                if "event_id" not in record or pd.isna(record.get("event_id")):
                    record["event_id"] = ""
                
                history[asset_id].append(record)
                
        # 排序每个市场的历史并截断
        total_points = 0
        for asset_id in history:
            history[asset_id].sort(key=lambda x: x["timestamp"])
            history[asset_id] = history[asset_id][-2000:] # 保持上限
            total_points += len(history[asset_id])
            
        logger.info(f"✅ 历史数据加载完成: 共从磁盘恢复了 {total_points} 个成交点")
    except Exception as e:
        logger.error(f"❌ 加载历史数据失败: {e}")
        
    return history

async def main():
    logger.info("=" * 60)
    logger.info("🚀 NBA 方案 A 实时系统 启动中...")
    logger.info("=" * 60)

    # 1. 准备市场数据
    token_map = get_nba_tokens_from_local()
    if not token_map:
        token_map = get_nba_tokens_from_api()
        
    if not token_map:
        logger.error("❌ 无法获取 NBA 市场数据，退出。")
        return

    # 2. 从本地 Parquet 恢复 24h 历史
    historical_data = load_recent_history_from_parquet(hours=24)

    # 3. 初始化中继服务器
    relay = LiveRelayServer(initial_history=historical_data)

    # 3. 数据收集器（封装广播逻辑）
    collector = NBADataCollector(token_map)
    
    # 重写回调用法，加入广播
    orig_on_message = collector.on_message
    def message_with_broadcast(event):
        # 原有的落盘逻辑（同步）
        orig_on_message(event)
        # 获取最新的 record (在 buffer 最后一个)
        if collector.buffer:
            record = collector.buffer[-1]
            # 放入异步任务广播
            asyncio.create_task(relay.broadcast(record))

    # 4. 初始化 WebSocket 客户端
    asset_ids = list(token_map.keys())
    ws_client = PolymarketWSClient(
        asset_ids=asset_ids,
        on_message=message_with_broadcast
    )

    # 5. 启动本地服务
    server = await websockets.serve(relay.register, LOCAL_WS_HOST, LOCAL_WS_PORT)
    logger.info(f"📡 本地分发服务器已运行在: ws://{LOCAL_WS_HOST}:{LOCAL_WS_PORT}")

    # 6. 优雅退出处理
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _shutdown():
        logger.info("🛑 收到停止信号...")
        ws_client.stop()
        collector.final_flush()
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _shutdown)

    # 7. 连接 Polymarket
    await ws_client.connect()
    
    # 等待停止信号
    await stop_event.wait()
    server.close()
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
