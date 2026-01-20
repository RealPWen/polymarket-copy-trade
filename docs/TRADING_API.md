# Polymarket 下单功能文档

## 概述

`polymarket_trader.py` 提供了一个简洁的 Python 接口，用于在 Polymarket 上进行交易。

## 功能特点

- ✅ 支持 Google/Email 登录用户 (Magic Link)
- ✅ 支持浏览器钱包用户 (MetaMask)
- ✅ 限价单 (GTC) 和市价单 (FOK)
- ✅ 获取订单簿和最佳价格
- ✅ 取消订单

## 快速开始

### 1. 获取私钥和钱包地址

1. 登录 [reveal.polymarket.com](https://reveal.polymarket.com) (使用与 Polymarket 相同的账户)
2. 导出您的私钥
3. 在 [polymarket.com/settings](https://polymarket.com/settings) 查看您的钱包地址

### 2. 使用示例

```python
from polymarket_trader import PolymarketTrader

# 初始化 (Google/Email 登录用户使用 signature_type=1)
trader = PolymarketTrader(
    private_key="0x...",  # 从 reveal.polymarket.com 导出
    funder_address="0x...",  # Polymarket 显示的钱包地址
    signature_type=1  # 1=Google/Email, 2=MetaMask
)

# 获取市场价格
token_id = "2276778..."  # 从市场页面获取
best_bid, best_ask = trader.get_best_prices(token_id)

# 下限价单
result = trader.place_order(
    token_id=token_id,
    side="BUY",
    size=5.0,
    price=0.50,
    order_type="GTC"
)

# 检查结果
if result.get('success'):
    print(f"Order placed! ID: {result.get('orderId')}")
```

## 订单类型

| 类型 | 说明 |
|------|------|
| GTC | Good-Til-Cancelled - 限价单，直到成交或取消 |
| FOK | Fill-Or-Kill - 市价单，必须全部成交否则取消 |
| GTD | Good-Til-Date - 指定时间前有效 |

## 签名类型

| 值 | 登录方式 |
|----|----------|
| 1 | Google / Email / Magic Link |
| 2 | MetaMask / Coinbase Wallet / 浏览器钱包 |
| 0 | EOA 直接交易 (需要钱包自己支付 gas) |

## 获取 Token ID

1. 访问 Polymarket 市场页面
2. 使用浏览器开发者工具 (F12)
3. 在 Network 标签中搜索 `clobTokenIds`
4. YES token 是数组的第一个元素，NO token 是第二个

## 错误处理

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `invalid signature` | signature_type 不匹配 | 确认登录方式并使用正确的 signature_type |
| `not enough balance` | USDC 余额不足 | 充值 USDC 到 Polymarket |
| `FOK order not filled` | 市场流动性不足 | 使用 GTC 限价单代替 |

## 依赖

```
pip install py-clob-client requests
```

## 测试完成状态

- [x] API 认证
- [x] 订单签名
- [x] 订单提交
- [x] GTC 限价单
- [x] 获取订单簿

---

*文档创建于 2026-01-20*
