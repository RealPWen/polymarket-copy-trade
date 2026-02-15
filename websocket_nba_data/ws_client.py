"""
Polymarket CLOB WebSocket 客户端
负责连接、订阅、心跳、断线重连
"""
import asyncio
import json
import logging
import time
from typing import Callable, List, Optional

import websockets
from websockets.exceptions import ConnectionClosed

from config import WS_MARKET_URL, RECONNECT_DELAY, MAX_RECONNECT_ATTEMPTS, HEARTBEAT_INTERVAL

logger = logging.getLogger("WS_Client")


class PolymarketWSClient:
    """
    Polymarket Market Channel WebSocket 客户端
    
    订阅指定 asset_ids 的实时价格变动和成交数据。
    所有消息通过回调函数 on_message 传递给上层处理。
    """

    def __init__(self, asset_ids: List[str], on_message: Callable):
        """
        Args:
            asset_ids: 要订阅的 token ID 列表（即 clob_token_id）
            on_message: 收到消息时的回调函数，签名为 on_message(data: dict)
        """
        self.asset_ids = asset_ids
        self.on_message = on_message
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self._running = False
        self._reconnect_count = 0
        self._msg_count = 0
        self._last_msg_time = 0

    async def _subscribe(self):
        """发送订阅消息到 Market Channel（支持分批）"""
        batch_size = 100
        total = len(self.asset_ids)
        
        if total <= batch_size:
            # 小规模一次性订阅
            subscribe_msg = {
                "type": "market",
                "assets_ids": self.asset_ids,
            }
            await self.ws.send(json.dumps(subscribe_msg))
            logger.info(f"📡 已发送订阅请求，共 {total} 个 asset_ids")
        else:
            # 大规模分批订阅
            logger.info(f"📡 开始分批订阅，共 {total} 个 asset_ids，每批 {batch_size} 个")
            for i in range(0, total, batch_size):
                batch = self.asset_ids[i:i + batch_size]
                subscribe_msg = {
                    "type": "market",
                    "assets_ids": batch,
                }
                await self.ws.send(json.dumps(subscribe_msg))
                batch_num = i // batch_size + 1
                total_batches = (total + batch_size - 1) // batch_size
                logger.info(f"   📦 批次 {batch_num}/{total_batches}: 已订阅 {len(batch)} 个 token")
                if i + batch_size < total:
                    await asyncio.sleep(0.5)  # 批间间隔，避免冲击服务器
            logger.info(f"✅ 全部 {total} 个 token 订阅完成")

    async def _heartbeat(self):
        """定期发送 ping 保持连接存活"""
        while self._running and self.ws:
            try:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                if self.ws and self.ws.open:
                    pong = await self.ws.ping()
                    await asyncio.wait_for(pong, timeout=10)
            except asyncio.TimeoutError:
                logger.warning("💔 心跳超时，连接可能已断开")
                break
            except Exception:
                break

    async def _listen(self):
        """监听 WebSocket 消息"""
        async for raw_msg in self.ws:
            try:
                data = json.loads(raw_msg)
                self._msg_count += 1
                self._last_msg_time = time.time()

                if isinstance(data, list):
                    # 初始快照：数组中每个元素是一个 book 事件
                    for event in data:
                        self._dispatch(event)
                elif isinstance(data, dict):
                    self._dispatch(data)

            except json.JSONDecodeError:
                logger.debug(f"⚠️ 收到非 JSON 消息: {raw_msg[:100]}")
            except Exception as e:
                logger.error(f"⚠️ 处理消息出错: {e}")

    def _dispatch(self, event: dict):
        """分发单个事件到回调"""
        event_type = event.get("event_type", "unknown")

        if event_type == "book":
            # 完整订单簿快照，包含 last_trade_price
            self.on_message(event)
        elif event_type == "price_change":
            # 价格变动，包含 price_changes 数组
            self.on_message(event)
        elif event_type == "last_trade_price":
            # 最新成交价推送
            self.on_message(event)
        elif event_type == "tick_size_change":
            pass  # 忽略 tick_size 变化
        elif "asset_id" in event:
            # 未知类型但包含 asset_id 的有效数据
            self.on_message(event)

    async def connect(self):
        """主连接循环：连接 -> 订阅 -> 监听 -> 断线重连"""
        self._running = True
        
        while self._running:
            try:
                logger.info(f"🔌 正在连接 Polymarket WebSocket...")
                
                async with websockets.connect(
                    WS_MARKET_URL,
                    ping_interval=None,  # 我们自己管理心跳
                    ping_timeout=None,
                    close_timeout=10,
                    max_size=10 * 1024 * 1024,  # 10MB max message size
                ) as ws:
                    self.ws = ws
                    self._reconnect_count = 0
                    logger.info("✅ WebSocket 连接成功!")

                    # 发送订阅
                    await self._subscribe()

                    # 同时运行心跳和消息监听
                    heartbeat_task = asyncio.create_task(self._heartbeat())
                    try:
                        await self._listen()
                    finally:
                        heartbeat_task.cancel()

            except ConnectionClosed as e:
                logger.warning(f"🔌 连接关闭: code={e.code}, reason={e.reason}")
            except ConnectionRefusedError:
                logger.error("❌ 连接被拒绝，服务器可能不可用")
            except Exception as e:
                logger.error(f"❌ 连接异常: {type(e).__name__}: {e}")

            # 重连逻辑
            if not self._running:
                break

            self._reconnect_count += 1
            if MAX_RECONNECT_ATTEMPTS > 0 and self._reconnect_count > MAX_RECONNECT_ATTEMPTS:
                logger.error(f"❌ 已达到最大重连次数 ({MAX_RECONNECT_ATTEMPTS})，停止重连")
                break

            wait = min(RECONNECT_DELAY * self._reconnect_count, 30)  # 指数退避，最长 30s
            logger.info(f"⏳ {wait} 秒后尝试第 {self._reconnect_count} 次重连...")
            await asyncio.sleep(wait)

        self._running = False
        logger.info("🛑 WebSocket 客户端已停止")

    def stop(self):
        """优雅停止"""
        self._running = False
        if self.ws:
            asyncio.ensure_future(self.ws.close())

    @property
    def stats(self) -> dict:
        """获取运行统计"""
        return {
            "total_messages": self._msg_count,
            "reconnect_count": self._reconnect_count,
            "last_msg_time": self._last_msg_time,
            "connected": self.ws is not None and self.ws.open if self.ws else False,
        }
