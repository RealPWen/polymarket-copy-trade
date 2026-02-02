# -*- coding: utf-8 -*-
"""
跟单交易配置文件
请在启动跟单器之前填写此配置

敏感信息通过环境变量配置:
  $env:POLYMARKET_PRIVATE_KEY = "0x..."
  $env:POLYMARKET_FUNDER_ADDRESS = "0x..."
"""

import os

CONFIG = {
    # === 账户配置 (从环境变量读取) ===
    "target_wallet": "",              # 跟单目标钱包地址
    "my_private_key": os.environ.get("POLYMARKET_PRIVATE_KEY", ""),
    "my_funder_address": os.environ.get("POLYMARKET_FUNDER_ADDRESS", ""),
    "signature_type": 1,              # 1=Google/Email, 2=MetaMask
    
    # === 仓位管理 (核心安全) ===
    "position_ratio": 0.1,            # 跟单比例 (推荐: 0.1~0.5)
    "max_position_usd": 50.0,         # 单笔最大金额 ($)
    "min_position_usd": 1.0,          # 最小跟单金额 ($)
    
    # === 风险控制 ===
    "daily_loss_limit": 200.0,        # 每日亏损上限 ($)
    "max_open_positions": 10,         # 最大同时持仓数
    "max_slippage_pct": 2.0,          # 最大滑点容忍度 (%)
    
    # === 过滤条件 ===
    "min_liquidity": 5000.0,          # 只跟流动性 > $5k 的市场
    "max_trade_age_seconds": 30,      # 只跟 30 秒内的交易
    "excluded_markets": [],           # 排除的市场 slug 列表
    "copy_maker_trades": False,       # 是否跟单 Maker 挂单交易 (False=只跟 Taker 吃单)
    
    # === 运行模式 ===
    "dry_run": True,                  # 模拟模式 (强烈建议先开启)
    "poll_interval": 3,               # 轮询间隔 (秒)
    "log_file": "copy_trades.log",    # 日志文件路径
}


def validate_config():
    """验证配置是否完整"""
    errors = []
    
    if not CONFIG["target_wallet"]:
        errors.append("target_wallet 未配置")
    if not CONFIG["my_private_key"] and not CONFIG["dry_run"]:
        errors.append("my_private_key 未配置 (非 dry_run 模式必须)")
    if not CONFIG["my_funder_address"] and not CONFIG["dry_run"]:
        errors.append("my_funder_address 未配置 (非 dry_run 模式必须)")
    
    if CONFIG["position_ratio"] <= 0 or CONFIG["position_ratio"] > 1:
        errors.append("position_ratio 必须在 (0, 1] 范围内")
    if CONFIG["max_position_usd"] <= 0:
        errors.append("max_position_usd 必须 > 0")
        
    return errors


if __name__ == "__main__":
    errors = validate_config()
    if errors:
        print("❌ 配置验证失败:")
        for e in errors:
            print(f"   - {e}")
    else:
        print("✅ 配置验证通过")
        print(f"   目标钱包: {CONFIG['target_wallet'][:10]}...")
        print(f"   跟单比例: {CONFIG['position_ratio']}")
        print(f"   单笔上限: ${CONFIG['max_position_usd']}")
        print(f"   模拟模式: {CONFIG['dry_run']}")
