---
description: 如何运行跟单引擎
---

# 跟单引擎使用说明

## 快速开始

// turbo
1. **模拟模式测试** (推荐先用此模式):
   ```bash
   cd d:\Ideas\polymarket-smart-trader
   python run_copy_trader.py -t 0xdb27bf2ac5d428a9c63dbc914611036855a6c56e -d
   ```

2. **自定义参数运行**:
   ```bash
   python run_copy_trader.py -t 0x目标地址 -r 0.2 -m 30 -d
   ```
   - `-t`: 目标钱包地址
   - `-r`: 跟单比例 (0.2 = 20%)
   - `-m`: 单笔最大金额 ($30)
   - `-d`: 模拟模式

// turbo-all
## 实盘运行 (需先配置)

3. **编辑配置文件**:
   打开 `copy_trader/copy_trader_config.py`，填写:
   - `my_private_key`: 从 reveal.polymarket.com 导出
   - `my_funder_address`: Polymarket 显示的钱包地址

4. **关闭模拟模式运行**:
   ```bash
   python run_copy_trader.py -t 0x目标地址
   ```

## 停止运行
按 `Ctrl + C` 停止跟单引擎。
