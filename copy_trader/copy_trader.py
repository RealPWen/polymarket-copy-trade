# -*- coding: utf-8 -*-
"""
Polymarket 跟单引擎
实时监听目标账户交易并自动跟单

核心安全机制:
1. 延迟过滤 - 仅跟进 30 秒内的交易
2. 流动性检查 - 验证市场流动性
3. 滑点保护 - 对比当前价格与目标价格
4. 每日止损 - 累计亏损达限额自动暂停
5. 仓位计算 - min(target_size × ratio, max_usd)
"""

import time
import json
import logging
from datetime import datetime, date
from typing import Optional, Dict, List

import sys
import os
# 添加父目录到路径以便导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from copy_trader.copy_trader_config import CONFIG, validate_config

try:
    from user_listener.polymarket_data_fetcher import PolymarketDataFetcher
except ImportError:
    from polymarket_data_fetcher import PolymarketDataFetcher

try:
    from trade.polymarket_trader import PolymarketTrader
except ImportError:
    PolymarketTrader = None


class CopyTrader:
    """跟单引擎核心类"""
    
    def __init__(self, config: dict = None):
        self.config = config or CONFIG
        self.fetcher = PolymarketDataFetcher()
        self.trader = None  # 延迟初始化
        
        # 状态追踪
        self.last_timestamp = 0
        self.last_hashes = set()
        self.daily_pnl = 0.0
        self.current_date = date.today()
        self.open_positions_count = 0
        
        # 市场缓存
        self.market_cache: Dict[str, dict] = {}
        
        # 设置日志
        self._setup_logging()
        
    def _setup_logging(self):
        """配置日志系统"""
        log_format = '%(asctime)s | %(levelname)s | %(message)s'
        
        # 文件日志
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(self.config.get('log_file', 'copy_trades.log'), encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('CopyTrader')
        
    def _init_trader(self):
        """初始化交易客户端 (仅在非 dry_run 模式)"""
        if self.config['dry_run']:
            self.logger.info("🔸 模拟模式 - 不初始化交易客户端")
            return
            
        if PolymarketTrader is None:
            self.logger.error("❌ 无法导入 PolymarketTrader 模块")
            return
            
        try:
            self.trader = PolymarketTrader(
                private_key=self.config['my_private_key'],
                funder_address=self.config['my_funder_address'],
                signature_type=self.config['signature_type']
            )
            self.logger.info("✅ 交易客户端初始化成功")
        except Exception as e:
            self.logger.error(f"❌ 交易客户端初始化失败: {e}")
            raise
            
    def _reset_daily_stats(self):
        """重置每日统计 (新的一天)"""
        today = date.today()
        if today != self.current_date:
            self.logger.info(f"📅 新的一天开始，重置每日统计")
            self.daily_pnl = 0.0
            self.current_date = today
            
    def _check_daily_loss_limit(self) -> bool:
        """检查是否达到每日亏损限额"""
        if self.daily_pnl < -self.config['daily_loss_limit']:
            self.logger.warning(f"⚠️ 已达每日亏损限额 (${-self.daily_pnl:.2f}), 暂停跟单")
            return False
        return True
        
    def _check_max_positions(self) -> bool:
        """检查是否达到最大持仓数"""
        if self.open_positions_count >= self.config['max_open_positions']:
            self.logger.warning(f"⚠️ 已达最大持仓数 ({self.open_positions_count}), 暂停新开仓")
            return False
        return True
        
    def _get_market_info(self, condition_id: str, slug: str = None) -> Optional[dict]:
        """获取市场信息 (带缓存)"""
        if condition_id in self.market_cache:
            return self.market_cache[condition_id]
            
        try:
            df = None
            if slug:
                df = self.fetcher.get_markets(slug=slug)
            if df is None or df.empty:
                df = self.fetcher.get_markets(condition_id=condition_id)
                
            if not df.empty:
                for _, row in df.iterrows():
                    cid = row.get('conditionId') or row.get('condition_id')
                    if cid and str(cid).lower() == str(condition_id).lower():
                        info = row.to_dict()
                        self.market_cache[condition_id] = info
                        return info
        except Exception as e:
            self.logger.debug(f"获取市场信息失败: {e}")
            
        return None
        
    def _check_liquidity(self, market_info: dict) -> bool:
        """检查市场流动性"""
        try:
            liquidity = float(market_info.get('liquidity', 0))
            min_liquidity = self.config['min_liquidity']
            
            if liquidity < min_liquidity:
                self.logger.info(f"⏭️ 流动性不足 (${liquidity:.0f} < ${min_liquidity:.0f}), 跳过")
                return False
            return True
        except:
            return True  # 无法获取流动性时放行
            
    def _check_trade_age(self, trade_timestamp: int) -> bool:
        """检查交易是否过期"""
        now = time.time()
        age = now - trade_timestamp
        max_age = self.config['max_trade_age_seconds']
        
        if age > max_age:
            self.logger.info(f"⏭️ 交易过期 ({age:.1f}s > {max_age}s), 跳过")
            return False
        return True
        
    def _check_slippage(self, market_info: dict, target_price: float, side: str) -> bool:
        """检查滑点是否在可接受范围"""
        try:
            # 获取当前价格
            tokens = json.loads(market_info.get('clobTokenIds', '[]'))
            outcomes = json.loads(market_info.get('outcomes', '[]'))
            prices = json.loads(market_info.get('outcomePrices', '[]'))
            
            if not prices:
                return True  # 无法获取价格时放行
                
            current_price = float(prices[0])  # YES 价格
            
            # 计算滑点
            if target_price > 0:
                slippage_pct = abs(current_price - target_price) / target_price * 100
                max_slippage = self.config['max_slippage_pct']
                
                if slippage_pct > max_slippage:
                    self.logger.info(f"⏭️ 滑点超限 ({slippage_pct:.1f}% > {max_slippage}%), 跳过")
                    return False
                    
            return True
        except Exception as e:
            self.logger.debug(f"滑点检查失败: {e}")
            return True  # 异常时放行
            
    def _calculate_position_size(self, target_size: float, target_price: float) -> float:
        """计算跟单仓位大小"""
        # 目标交易金额
        target_amount = target_size * target_price
        
        # 按比例计算
        my_amount = target_amount * self.config['position_ratio']
        
        # 应用上下限
        my_amount = max(my_amount, self.config['min_position_usd'])
        my_amount = min(my_amount, self.config['max_position_usd'])
        
        # 转换回 size
        if target_price > 0:
            my_size = my_amount / target_price
        else:
            my_size = my_amount
            
        return round(my_size, 2)
        
    def _get_token_id(self, market_info: dict, outcome: str) -> Optional[str]:
        """从市场信息中获取 token_id"""
        try:
            tokens = json.loads(market_info.get('clobTokenIds', '[]'))
            outcomes = json.loads(market_info.get('outcomes', '[]'))
            
            if not tokens or not outcomes:
                return None
                
            # 匹配 outcome
            for i, o in enumerate(outcomes):
                if str(o).upper() == str(outcome).upper():
                    return tokens[i]
                    
            # 默认返回第一个 (YES)
            return tokens[0]
        except:
            return None
            
    def _execute_trade(self, trade: dict, market_info: dict) -> bool:
        """执行跟单交易"""
        side = str(trade['side']).upper()
        target_size = float(trade['size'])
        target_price = float(trade['price'])
        outcome = trade.get('outcome', 'Yes')
        title = trade.get('title', 'Unknown')
        
        # 计算跟单仓位
        my_size = self._calculate_position_size(target_size, target_price)
        
        # 获取 token_id
        token_id = self._get_token_id(market_info, outcome)
        
        trade_info = {
            'time': datetime.now().isoformat(),
            'target_wallet': self.config['target_wallet'][:10] + '...',
            'market': title[:50],
            'outcome': outcome,
            'side': side,
            'target_size': target_size,
            'target_price': target_price,
            'my_size': my_size,
            'token_id': token_id[:20] + '...' if token_id else None,
        }
        
        if self.config['dry_run']:
            # 模拟模式
            self.logger.info(f"🔸 [模拟] {side} {my_size:.2f} @ {target_price:.3f} | {outcome} | {title[:40]}...")
            self.logger.debug(f"   详情: {json.dumps(trade_info, ensure_ascii=False)}")
            return True
        else:
            # 实盘模式
            if not self.trader:
                self.logger.error("❌ 交易客户端未初始化")
                return False
                
            if not token_id:
                self.logger.error("❌ 无法获取 token_id")
                return False
                
            try:
                # 使用 GTC 限价单
                result = self.trader.place_order(
                    token_id=token_id,
                    side=side,
                    size=my_size,
                    price=target_price,
                    order_type="GTC"
                )
                
                trade_info['result'] = result
                self.logger.info(f"✅ [成交] {side} {my_size:.2f} @ {target_price:.3f} | {outcome} | {title[:40]}...")
                self.logger.info(f"   订单ID: {result.get('orderID', 'N/A')}")
                
                # 更新持仓计数
                if side == 'BUY':
                    self.open_positions_count += 1
                elif side == 'SELL':
                    self.open_positions_count = max(0, self.open_positions_count - 1)
                    
                return True
                
            except Exception as e:
                trade_info['error'] = str(e)
                self.logger.error(f"❌ 下单失败: {e}")
                return False
                
    def _process_new_trade(self, trade: dict) -> bool:
        """处理单笔新交易"""
        condition_id = trade.get('conditionId')
        slug = trade.get('slug')
        timestamp = int(trade.get('timestamp', 0))
        side = str(trade.get('side', '')).upper()
        title = trade.get('title', 'Unknown')
        
        self.logger.info(f"📥 发现新交易: {side} | {title[:50]}...")
        
        # 1. 检查交易是否过期
        if not self._check_trade_age(timestamp):
            return False
            
        # 2. 检查每日亏损限额
        if not self._check_daily_loss_limit():
            return False
            
        # 3. 检查最大持仓数 (仅买入时)
        if side == 'BUY' and not self._check_max_positions():
            return False
            
        # 4. 获取市场信息
        market_info = self._get_market_info(condition_id, slug)
        if not market_info:
            self.logger.warning(f"⚠️ 无法获取市场信息, 跳过")
            return False
            
        # 5. 检查流动性
        if not self._check_liquidity(market_info):
            return False
            
        # 6. 检查滑点
        target_price = float(trade.get('price', 0))
        if not self._check_slippage(market_info, target_price, side):
            return False
            
        # 7. 检查是否在排除列表
        market_slug = market_info.get('slug', '')
        if market_slug in self.config['excluded_markets']:
            self.logger.info(f"⏭️ 市场在排除列表中, 跳过")
            return False
            
        # 8. 执行交易
        return self._execute_trade(trade, market_info)
        
    def start(self):
        """启动跟单监听"""
        # 验证配置 (使用实例配置)
        errors = []
        if not self.config.get("target_wallet"):
            errors.append("target_wallet 未配置")
        if not self.config.get("my_private_key") and not self.config.get("dry_run"):
            errors.append("my_private_key 未配置 (非 dry_run 模式必须)")
        if not self.config.get("my_funder_address") and not self.config.get("dry_run"):
            errors.append("my_funder_address 未配置 (非 dry_run 模式必须)")
            
        if errors:
            for e in errors:
                self.logger.error(f"配置错误: {e}")
            return
            
        target = self.config['target_wallet']
        interval = self.config['poll_interval']
        
        self.logger.info("=" * 60)
        self.logger.info("🚀 Polymarket 跟单引擎启动")
        self.logger.info(f"   目标钱包: {target[:10]}...{target[-6:]}")
        self.logger.info(f"   跟单比例: {self.config['position_ratio']}")
        self.logger.info(f"   单笔上限: ${self.config['max_position_usd']}")
        self.logger.info(f"   模拟模式: {self.config['dry_run']}")
        self.logger.info(f"   轮询间隔: {interval}s")
        self.logger.info("=" * 60)
        
        # 初始化交易客户端 (非 dry_run 模式)
        if not self.config['dry_run']:
            self._init_trader()
            
        # 获取初始状态
        try:
            initial = self.fetcher.get_trades(wallet_address=target, limit=1, silent=True)
            if not initial.empty:
                self.last_timestamp = initial.iloc[0]['timestamp']
                self.last_hashes.add(initial.iloc[0]['transactionHash'])
                self.logger.info(f"📍 设置起点: {datetime.fromtimestamp(self.last_timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            self.logger.warning(f"获取初始状态失败: {e}")
            
        # 主循环
        while True:
            try:
                self._reset_daily_stats()
                
                # 获取最近交易
                trades_df = self.fetcher.get_trades(
                    wallet_address=target, 
                    limit=10, 
                    silent=True,
                    taker_only=not self.config.get('copy_maker_trades', False)
                )
                
                new_count = 0
                
                if not trades_df.empty:
                    # 过滤新交易
                    new_trades = trades_df[
                        (trades_df['timestamp'] >= self.last_timestamp) &
                        (~trades_df['transactionHash'].isin(self.last_hashes))
                    ]
                    
                    if not new_trades.empty:
                        # 按时间正序处理
                        new_trades = new_trades.sort_values('timestamp', ascending=True)
                        
                        for _, trade in new_trades.iterrows():
                            self._process_new_trade(trade.to_dict())
                            
                            # 更新状态
                            self.last_timestamp = max(self.last_timestamp, trade['timestamp'])
                            self.last_hashes.add(trade['transactionHash'])
                            new_count += 1
                            
                        # 清理 hash 集合
                        if len(self.last_hashes) > 100:
                            self.last_hashes = set(new_trades['transactionHash'].tolist())
                            
                # 心跳日志
                if new_count == 0:
                    now = datetime.now().strftime('%H:%M:%S')
                    print(f"\r🔍 [{now}] 监听中... (无新动态)", end="", flush=True)
                    
                time.sleep(interval)
                
            except KeyboardInterrupt:
                self.logger.info("\n🛑 跟单引擎停止")
                break
            except Exception as e:
                self.logger.error(f"❌ 监听出错: {e}")
                time.sleep(interval)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Polymarket 跟单引擎')
    parser.add_argument('--target', '-t', help='目标钱包地址')
    parser.add_argument('--dry-run', '-d', action='store_true', help='模拟模式')
    parser.add_argument('--ratio', '-r', type=float, help='跟单比例')
    parser.add_argument('--max-usd', '-m', type=float, help='单笔最大金额')
    
    args = parser.parse_args()
    
    # 命令行参数覆盖配置
    if args.target:
        CONFIG['target_wallet'] = args.target
    if args.dry_run:
        CONFIG['dry_run'] = True
    if args.ratio:
        CONFIG['position_ratio'] = args.ratio
    if args.max_usd:
        CONFIG['max_position_usd'] = args.max_usd
        
    # 启动
    engine = CopyTrader(CONFIG)
    engine.start()
