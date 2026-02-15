#!/usr/bin/env python3
"""
NBA 专项 WebSocket 实时监控主程序

功能：
1. 从 Gamma API / 本地 markets.parquet 获取所有 NBA 市场的 token ID
2. 通过 WebSocket 订阅这些 token 的实时价格变动
3. 将实时数据落盘为 Parquet 文件 + 控制台打印
"""
import asyncio
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

# 本项目模块
from config import (
    DATA_DIR, LOG_DIR, GAMMA_API_URL, MARKETS_FILE, FLUSH_INTERVAL,
    MARKET_FILTER_MODE, EXCLUDED_EVENT_TITLES,
)
from ws_client import PolymarketWSClient

# ============== 日志配置 ==============
log_file = LOG_DIR / f"nba_ws_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8"),
    ],
)
logger = logging.getLogger("NBA_WS")


# ============== NBA 市场发现 ==============

def get_nba_tokens_from_local() -> dict:
    """
    从本地 markets.parquet 中提取 NBA 市场的 token IDs
    返回: {token_id: {"market_id": ..., "question": ..., "answer": ...}}
    """
    if not MARKETS_FILE.exists():
        logger.warning(f"本地市场文件不存在: {MARKETS_FILE}")
        return {}

    try:
        df = pd.read_parquet(MARKETS_FILE)
        nba_mask = (
            df["question"].str.contains(r"\bNBA\b", case=False, na=False, regex=True)
            | df["slug"].str.contains(r"\bNBA\b", case=False, na=False, regex=True)
        )
        nba_markets = df[nba_mask]
        logger.info(f"🏀 从本地文件发现 {len(nba_markets)} 个 NBA 市场（未过滤）")

        # 排除已关闭/结算的市场
        if "closed" in nba_markets.columns:
            open_count_before = len(nba_markets)
            nba_markets = nba_markets[nba_markets["closed"] == False]
            logger.info(f"📂 排除已关闭市场后剩余 {len(nba_markets)} 个（排除了 {open_count_before - len(nba_markets)} 个）")

        # 根据配置进行过滤
        if MARKET_FILTER_MODE == "all_nba":
            # 基于 event_title 黑名单排除误匹配
            def is_excluded(event_title):
                title_upper = str(event_title).upper()
                return any(ex.upper() in title_upper for ex in EXCLUDED_EVENT_TITLES)
            
            exclude_mask = nba_markets["event_title"].apply(is_excluded)
            nba_markets = nba_markets[~exclude_mask]
            logger.info(
                f"🎯 all_nba 模式: 保留 {len(nba_markets)} 个市场 "
                f"(排除了 {exclude_mask.sum()} 个误匹配)"
            )
        elif MARKET_FILTER_MODE == "all":
            logger.info(f"📦 模式=all，订阅全部 {len(nba_markets)} 个 NBA 市场")

        token_map = {}
        for _, row in nba_markets.iterrows():
            question = row.get("question", "")
            market_id = str(row.get("id", ""))
            event_title = str(row.get("event_title", ""))
            event_id = str(row.get("event_id", ""))
            end_date = str(row.get("end_date", ""))
            
            # token1 和 token2 分别对应 Yes/No
            for token_col, answer_col in [("token1", "answer1"), ("token2", "answer2")]:
                token_id = str(row.get(token_col, ""))
                answer = str(row.get(answer_col, ""))
                if token_id and token_id != "nan" and token_id != "":
                    token_map[token_id] = {
                        "market_id": market_id,
                        "question": question,
                        "answer": answer,
                        "event_title": event_title,
                        "event_id": event_id,
                        "end_date": end_date,
                    }

        logger.info(f"📋 共提取 {len(token_map)} 个 NBA token IDs")
        # 打印分组摘要
        event_titles = set(v["event_title"] for v in token_map.values())
        logger.info(f"📂 共 {len(event_titles)} 个市场大类")
        return token_map

    except Exception as e:
        logger.error(f"读取本地市场文件失败: {e}")
        return {}


def get_nba_tokens_from_api() -> dict:
    """
    从 Gamma API 在线获取 NBA 市场的 token IDs（备用方案）
    """
    token_map = {}
    offset = 0
    batch_size = 100

    logger.info("🌐 从 Gamma API 获取 NBA 市场...")

    while True:
        try:
            resp = requests.get(
                f"{GAMMA_API_URL}/markets",
                params={
                    "limit": batch_size,
                    "offset": offset,
                    "tag": "nba",  # Gamma API 支持 tag 过滤
                    "active": "true",
                    "closed": "false",
                },
                timeout=30,
            )
            if resp.status_code != 200:
                logger.warning(f"API 返回 {resp.status_code}，停止获取")
                break

            markets = resp.json()
            if not markets:
                break

            for m in markets:
                question = m.get("question", "")
                market_id = str(m.get("id", ""))
                
                # 检查是否真的是 NBA 相关
                if not any(kw in question.upper() for kw in ["NBA", "BASKETBALL"]):
                    if not any(kw in m.get("slug", "").upper() for kw in ["NBA"]):
                        continue

                outcomes = m.get("outcomes", "[]")
                if isinstance(outcomes, str):
                    try:
                        outcomes = json.loads(outcomes)
                    except:
                        outcomes = []

                clob_tokens = m.get("clobTokenIds", "[]")
                if isinstance(clob_tokens, str):
                    try:
                        clob_tokens = json.loads(clob_tokens)
                    except:
                        clob_tokens = []

                for i, token_id in enumerate(clob_tokens):
                    if token_id:
                        token_map[token_id] = {
                            "market_id": market_id,
                            "question": question,
                            "answer": outcomes[i] if i < len(outcomes) else f"outcome_{i}",
                            "event_title": m.get("groupItemTitle", m.get("question", "")),
                            "event_id": str(m.get("id", "")),
                            "end_date": m.get("endDate", ""),
                        }

            if len(markets) < batch_size:
                break
            offset += batch_size
            time.sleep(0.3)  # 避免 API 限流

        except Exception as e:
            logger.error(f"API 请求出错: {e}")
            break

    logger.info(f"📋 从 API 获取到 {len(token_map)} 个 NBA token IDs")
    return token_map


# ============== 数据收集器 ==============

class NBADataCollector:
    """收集 WebSocket 推送的实时数据并落盘"""

    def __init__(self, token_map: dict):
        self.token_map = token_map
        self.buffer = []  # 内存缓冲区
        self.session_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = DATA_DIR / f"nba_ws_{self.session_ts}.parquet"
        self.total_events = 0
        self.total_flushed = 0

    def on_message(self, event: dict):
        """
        WebSocket 消息回调 - 处理三种事件类型

        1. book: 完整订单簿快照
           {event_type: "book", asset_id, market, bids, asks, last_trade_price, ...}
        2. price_change: 价格变动
           {event_type: "price_change", market, price_changes: [{asset_id, price, ...}], ...}
        3. last_trade_price: 最新成交价
           {event_type: "last_trade_price", asset_id, price, ...}
        """
        event_type = event.get("event_type", "unknown")

        if event_type == "book":
            self._handle_book(event)
        elif event_type == "price_change":
            self._handle_price_change(event)
        elif event_type == "last_trade_price":
            self._handle_last_trade(event)
        else:
            # 未知类型，记录但减少日志噪声
            self._append_record(event_type, event.get("asset_id", ""), 0, event)

        # 定期落盘
        if len(self.buffer) >= FLUSH_INTERVAL:
            self.flush()

    def _normalize_record(self, record, original_answer):
        """
        数据归一化：如果原始是 No，则 1-Price 转换为 Yes 视角
        """
        if str(original_answer).strip().lower() == "no":
            # 价格翻转
            record["price"] = 1.0 - record["price"] if record["price"] > 0 else 0
            
            # 盘口翻转：No 的 Best Bid -> Yes 的 Best Ask
            # No 的 Best Ask -> Yes 的 Best Bid
            orig_bid = record.get("best_bid", 0)
            orig_ask = record.get("best_ask", 0)
            
            record["best_bid"] = 1.0 - orig_ask if orig_ask > 0 else 0
            record["best_ask"] = 1.0 - orig_bid if orig_bid > 0 else 0
            
            # 标记归一化
            record["answer"] = "Yes (Normalized)"
        else:
            record["answer"] = "Yes"
        return record

    def _handle_book(self, event: dict):
        """处理 book 事件：提取最优买卖价和最新成交价"""
        asset_id = event.get("asset_id", "")
        market_info = self.token_map.get(asset_id, {})
        original_answer = market_info.get("answer", "Yes")

        # 最新成交价
        try:
            last_trade = float(event.get("last_trade_price", 0) or 0)
        except (ValueError, TypeError):
            last_trade = 0
        
        # 最优买卖价
        bids = event.get("bids", [])
        asks = event.get("asks", [])
        try:
            best_bid = float(bids[0]["price"]) if bids else 0
        except (ValueError, TypeError, KeyError, IndexError):
            best_bid = 0
        try:
            best_ask = float(asks[0]["price"]) if asks else 0
        except (ValueError, TypeError, KeyError, IndexError):
            best_ask = 0

        record = {
            "timestamp": time.time(),
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "event_type": "book",
            "asset_id": asset_id,
            "market_id": market_info.get("market_id", ""),
            "question": market_info.get("question", "未知市场"),
            "event_title": market_info.get("event_title", ""),
            "event_id": market_info.get("event_id", ""),
            "price": last_trade,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "bid_depth": len(bids),
            "ask_depth": len(asks),
        }
        
        # 归一化处理
        record = self._normalize_record(record, original_answer)
        
        self.buffer.append(record)
        self.total_events += 1

        q_short = record["question"][:40]
        logger.debug(
            f"📖 盘口 | {q_short} [归一化] "
            f"买={record['best_bid']:.3f} 卖={record['best_ask']:.3f} 最新成交={record['price']:.3f}"
        )

    def _handle_price_change(self, event: dict):
        """处理 price_change 事件：包含 price_changes 数组"""
        changes = event.get("price_changes", [])
        for change in changes:
            asset_id = change.get("asset_id", "")
            market_info = self.token_map.get(asset_id, {})
            original_answer = market_info.get("answer", "Yes")
            try:
                price = float(change.get("price", 0) or 0)
            except (ValueError, TypeError):
                price = 0

            record = {
                "timestamp": time.time(),
                "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                "event_type": "price_change",
                "asset_id": asset_id,
                "market_id": market_info.get("market_id", ""),
                "question": market_info.get("question", "未知市场"),
                "event_title": market_info.get("event_title", ""),
                "event_id": market_info.get("event_id", ""),
                "price": price,
                "best_bid": 0,
                "best_ask": 0,
                "bid_depth": 0,
                "ask_depth": 0,
            }
            
            record = self._normalize_record(record, original_answer)
            
            self.buffer.append(record)
            self.total_events += 1

            q_short = record["question"][:40]
            logger.debug(
                f"📊 报价 | {q_short} [归一化] "
                f"价格={record['price']:.4f}"
            )

    def _handle_last_trade(self, event: dict):
        """处理 last_trade_price 事件"""
        asset_id = event.get("asset_id", "")
        market_info = self.token_map.get(asset_id, {})
        original_answer = market_info.get("answer", "Yes")
        try:
            price = float(event.get("price", 0) or 0)
        except (ValueError, TypeError):
            price = 0

        record = {
            "timestamp": time.time(),
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "event_type": "last_trade_price",
            "asset_id": asset_id,
            "market_id": market_info.get("market_id", ""),
            "question": market_info.get("question", "未知市场"),
            "event_title": market_info.get("event_title", ""),
            "event_id": market_info.get("event_id", ""),
            "price": price,
            "best_bid": 0,
            "best_ask": 0,
            "bid_depth": 0,
            "ask_depth": 0,
        }
        
        record = self._normalize_record(record, original_answer)
        
        self.buffer.append(record)
        self.total_events += 1

        q_short = record["question"][:40]
        logger.info(
            f"💹 成交 | {q_short} [归一化] "
            f"价格={record['price']:.4f}"
        )


    def _append_record(self, event_type, asset_id, price, event):
        """通用记录追加"""
        market_info = self.token_map.get(asset_id, {})
        record = {
            "timestamp": time.time(),
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "event_type": event_type,
            "asset_id": asset_id,
            "market_id": market_info.get("market_id", ""),
            "question": market_info.get("question", "未知市场"),
            "event_title": market_info.get("event_title", ""),
            "event_id": market_info.get("event_id", ""),
            "answer": market_info.get("answer", ""),
            "price": float(price),
            "best_bid": 0,
            "best_ask": 0,
            "bid_depth": 0,
            "ask_depth": 0,
        }
        self.buffer.append(record)
        self.total_events += 1

    def flush(self):
        """将缓冲区数据写入 Parquet 文件"""
        if not self.buffer:
            return

        try:
            df_new = pd.DataFrame(self.buffer)

            if self.output_file.exists():
                df_old = pd.read_parquet(self.output_file)
                df_combined = pd.concat([df_old, df_new], ignore_index=True)
            else:
                df_combined = df_new

            df_combined.to_parquet(self.output_file, index=False, compression="snappy")
            flushed_count = len(self.buffer)
            self.total_flushed += flushed_count
            self.buffer = []
            logger.info(
                f"💾 已落盘 {flushed_count} 条 → {self.output_file.name} "
                f"(累计 {self.total_flushed} 条)"
            )
        except Exception as e:
            logger.error(f"落盘失败: {e}")

    def final_flush(self):
        """程序退出前的最终落盘"""
        if self.buffer:
            logger.info(f"📦 正在执行最终落盘（剩余 {len(self.buffer)} 条）...")
            self.flush()
        logger.info(
            f"✨ 本次会话共收到 {self.total_events} 条事件，"
            f"落盘 {self.total_flushed} 条"
        )


# ============== 主程序 ==============

async def main():
    # 1. 获取 NBA 市场 token 列表
    logger.info("=" * 60)
    logger.info("🏀 NBA WebSocket 实时监控 启动中...")
    logger.info("=" * 60)

    token_map = get_nba_tokens_from_local()
    if not token_map:
        logger.info("本地文件未找到，尝试从 API 获取...")
        token_map = get_nba_tokens_from_api()

    if not token_map:
        logger.error("❌ 无法获取任何 NBA 市场的 token ID，请检查数据源")
        sys.exit(1)

    # 打印发现的市场摘要
    questions = set(v["question"] for v in token_map.values())
    logger.info(f"\n📋 将订阅以下 {len(questions)} 个 NBA 市场:")
    for i, q in enumerate(sorted(questions), 1):
        logger.info(f"   {i}. {q}")
    logger.info("")

    # 2. 初始化数据收集器
    collector = NBADataCollector(token_map)

    # 3. 初始化 WebSocket 客户端
    asset_ids = list(token_map.keys())
    ws_client = PolymarketWSClient(
        asset_ids=asset_ids,
        on_message=collector.on_message,
    )

    # 4. 注册信号处理（优雅退出）
    loop = asyncio.get_event_loop()

    def _shutdown(sig):
        logger.info(f"🛑 收到信号 {sig.name}，正在优雅退出...")
        ws_client.stop()
        collector.final_flush()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _shutdown, sig)

    # 5. 启动 WebSocket 连接
    logger.info(f"🔌 准备连接 WebSocket，订阅 {len(asset_ids)} 个 token...")
    await ws_client.connect()

    # 确保退出时落盘
    collector.final_flush()


if __name__ == "__main__":
    asyncio.run(main())
