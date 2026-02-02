# -*- coding: utf-8 -*-
"""
Polymarket 跟单启动脚本

使用方法:
    python run_copy_trader.py --target 0x目标地址 --dry-run
    
参数:
    --target, -t    目标钱包地址
    --dry-run, -d   模拟模式 (不实际下单)
    --ratio, -r     跟单比例 (默认 0.1)
    --max-usd, -m   单笔最大金额 (默认 $50)
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from copy_trader.copy_trader import CopyTrader
from copy_trader.copy_trader_config import CONFIG


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Polymarket 跟单引擎',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 模拟模式测试
  python run_copy_trader.py -t 0xdb27bf2ac5d428a9c63dbc914611036855a6c56e -d

  # 实盘跟单 (需要先配置私钥)
  python run_copy_trader.py -t 0x目标地址 -r 0.2 -m 30
        """
    )
    
    parser.add_argument('--target', '-t', 
                        help='目标钱包地址 (要跟单的用户)')
    parser.add_argument('--dry-run', '-d', 
                        action='store_true', 
                        help='模拟模式 (推荐先用此模式测试)')
    parser.add_argument('--ratio', '-r', 
                        type=float, 
                        help='跟单比例, 如 0.1 表示跟 10%% 仓位')
    parser.add_argument('--max-usd', '-m', 
                        type=float, 
                        help='单笔最大金额 ($)')
    parser.add_argument('--interval', '-i', 
                        type=int, 
                        help='轮询间隔 (秒)')
    
    args = parser.parse_args()
    
    # 命令行参数覆盖配置
    config = CONFIG.copy()
    
    if args.target:
        config['target_wallet'] = args.target
    if args.dry_run:
        config['dry_run'] = True
    if args.ratio is not None:
        config['position_ratio'] = args.ratio
    if args.max_usd is not None:
        config['max_position_usd'] = args.max_usd
    if args.interval is not None:
        config['poll_interval'] = args.interval
        
    # 检查必需参数
    if not config['target_wallet']:
        print("❌ 错误: 必须指定目标钱包地址")
        print("   使用 --target 或 -t 参数，或在 copy_trader_config.py 中配置")
        parser.print_help()
        sys.exit(1)
        
    # 启动跟单引擎
    try:
        engine = CopyTrader(config)
        engine.start()
    except KeyboardInterrupt:
        print("\n🛑 用户中断")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
