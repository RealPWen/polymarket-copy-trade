# Polymarket API 问题记录

## py-clob-client 已知问题

### 1. `get_balance_allowance()` 方法 Bug

**错误信息**:
```
AttributeError: 'NoneType' object has no attribute 'signature_type'
```

**原因**: 
- 方法签名允许 `params=None`
- 但代码内部直接访问 `params.signature_type`

**解决方案**: 必须传入 `BalanceAllowanceParams` 对象

```python
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import BalanceAllowanceParams

client = ClobClient(
    host='https://clob.polymarket.com',
    key='0x...',
    chain_id=137,
    signature_type=1,  # POLY_PROXY
    funder='0x...'  # 你的钱包地址
)

creds = client.create_or_derive_api_creds()
client.set_api_creds(creds)

# ✅ 正确用法 - 必须传入 params
params = BalanceAllowanceParams(asset_type='COLLATERAL')
balance = client.get_balance_allowance(params=params)
print(balance)  # {'balance': '0', 'allowances': {...}}
```

**注意**: 
- 返回的是 **Polymarket 交易账户** 余额，不是 Proxy Wallet 显示的余额
- 网站显示的余额可能包含未结算的持仓价值

**可能原因**:
- EOA 钱包未在 Polymarket 激活
- 需要先进行一次交易才能激活账户
- 或使用 Email/Magic 登录的账户需要不同的认证方式

---

## 工作的 API 端点

以下端点正常工作：

| 端点 | 状态 | 说明 |
|------|------|------|
| `GET /book?token_id=xxx` | ✅ | 获取 orderbook |
| `GET /markets` (Gamma API) | ✅ | 获取市场列表 |
| `GET /events/slug/{slug}` (Gamma API) | ✅ | 按 slug 获取事件 |
| `POST /order` | ❓ | 未在 Live 模式测试 |

---

## 建议

1. 升级 py-clob-client 到最新版本
2. 如果问题持续，考虑使用原生 HTTP 请求
3. 余额查询可以从网站手动确认
