# Polymarket API 经验文档

本文档记录了在开发 Smart Trader Discovery 和 Insider Detection 功能时，尝试过的各种 API 及其优缺点。

---

## 官方 API

### 1. Data API (`data-api.polymarket.com`)

**用途**: 获取用户活动、交易、仓位等数据

#### 已测试端点

| 端点 | 用途 | 限制 | 评价 |
|------|------|------|------|
| `/activity` | 用户交易历史 | 最多 ~1000 条，按时间排序 | 适合分析单个用户近期活动 |
| `/trades` | 市场交易流 | **已关闭市场只返回最近 ~1000 条** | 无法获取完整历史 |
| `/closed-positions` | 已平仓头寸 | 返回聚合数据，非原始交易 | 适合计算 PnL，不适合时序分析 |
| `/leaderboard` | PnL 排行榜 | 最多 50 条/请求，支持分页 | 滞后指标，Insider 已赚钱才上榜 |
| `/positions` | 当前持仓 | - | 适合实时监控 |

#### 数据结构 (trades)
```json
{
  "proxyWallet": "0x...",
  "side": "BUY",
  "size": 1000,
  "price": 0.55,
  "timestamp": 1730916140,
  "outcome": "Yes",
  "eventSlug": "presidential-election-winner-2024",
  "conditionId": "0x..."
}
```

**重要发现**:
- `trades` 端点对**已关闭市场**的数据保留有限，只返回最近 1000 条交易（结算后的交易）
- 无法通过时间范围过滤获取更早的历史数据
- 每条 trade 记录代表**单方**交易，不包含对手方

---

### 2. Gamma API (`gamma-api.polymarket.com`)

**用途**: 获取市场元数据、事件信息

#### 已测试端点

| 端点 | 用途 | 限制 | 评价 |
|------|------|------|------|
| `/markets` | 市场列表 | 支持过滤 active/closed | 适合发现市场 |
| `/events` | 事件列表 | - | 包含关联的多个市场 |

#### 数据结构 (markets)
```json
{
  "id": "123",
  "question": "Will X happen?",
  "conditionId": "0x...",
  "slug": "market-slug",
  "volume": "999999.99",
  "outcomes": "[\"Yes\", \"No\"]",
  "outcomePrices": "[\"0.55\", \"0.45\"]"
}
```

**重要发现**:
- `conditionId` 是 Data API 交易查询的关键参数
- 已关闭市场可能不在默认列表中，需要用 `closed=true` 过滤
- `slug` 用于用户友好的 URL，`conditionId` 用于 API 查询

---

### 3. CLOB API (`clob.polymarket.com`)

**用途**: 订单簿、下单、WebSocket 实时数据

**未深入测试**，但已知：
- 需要认证才能下单
- WebSocket 可订阅实时交易流
- 对历史数据查询能力有限

---

## 第三方数据源

### 4. Dune Analytics

**状态**: 需要 API Key

**优势**:
- 直接查询区块链数据
- 可获取完整历史交易
- 支持复杂 SQL 查询
- 有现成的 Polymarket Dashboard 可以参考

**已知 Dashboard**:
- `dune.com/rchen8/polymarket` - Activity and Volume
- `dune.com/polymarket/historical-accuracy-and-bias` - Market Accuracy

**使用方法**:
1. 注册 Dune 账户
2. 从 Settings > API 获取 API Key
3. 设置环境变量: `$env:DUNE_API_KEY = 'your-key'`
4. 使用 Dune API 执行查询

### 5. The Graph (Subgraph)

**状态**: 需要 API Key

**已知端点 (需 API Key)**:
- Decentralized: `https://gateway.thegraph.com/api/{api-key}/subgraphs/id/Bx1W4S7kDVxs9gC3s2G6DS8kdNBJNVhMviCtin2DiBp`

**可用 Subgraph**:
- Polymarket Activity Polygon
- Polymarket PnL (Profit & Loss)
- Polymarket Open Interest
- Polymarket Orderbook

**注意**: 免费托管服务 (api.thegraph.com) 已不再可用，需使用去中心化网络。

### 6. Polygon RPC (直接区块链查询) ✅

**状态**: 可用，无需 API Key！

**测试结果** (2026-02-02):

| RPC 端点 | 状态 | 最大 Block Range |
|----------|------|------------------|
| `polygon-bor-rpc.publicnode.com` | ✅ SUCCESS | 10 blocks |
| `polygon.drpc.org` | ✅ SUCCESS | 10 blocks |
| `polygon-rpc.com` | ❌ 限制太严格 | - |
| `polygon.llamarpc.com` | ❌ 连接问题 | - |

**Polymarket 合约地址**:
- CTF Exchange: `0x4bFb41d5B3570DeFd03C39a9A4D8dE6BD8B8982E`
- Neg Risk CTF Exchange: `0xC5d563A36AE78145C45a50134d48A1215220f80a`

**Event Signature**:
- OrderFilled: `0xd0a08e8c493f9c94f29311604c9de1b4e8c8d4c06bd0c789af57f2d65bfec0f6`

**使用示例**:
```python
import requests

RPC = "https://polygon-bor-rpc.publicnode.com"
CTF_EXCHANGE = "0x4bFb41d5B3570DeFd03C39a9A4D8dE6BD8B8982E"
ORDER_FILLED_TOPIC = "0xd0a08e8c493f9c94f29311604c9de1b4e8c8d4c06bd0c789af57f2d65bfec0f6"

# Get current block
r = requests.post(RPC, json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1})
current_block = int(r.json()["result"], 16)

# Fetch logs (max 10 blocks per request)
params = [{
    "fromBlock": hex(current_block - 10),
    "toBlock": hex(current_block),
    "address": CTF_EXCHANGE,
    "topics": [ORDER_FILLED_TOPIC]
}]

r = requests.post(RPC, json={"jsonrpc": "2.0", "method": "eth_getLogs", "params": params, "id": 1})
logs = r.json()["result"]
print(f"Found {len(logs)} OrderFilled events")
```

**优势**:
- 无需 API Key
- 完整历史数据（从合约部署到现在）
- 直接区块链数据，不可篡改

**劣势**:
- 每次请求只能查询 10 个 blocks
- 需要手动解析 event data
- 没有市场元数据（需要额外查询）
- 查询大时间范围需要循环多次

**重要限制 (2026-02-02 发现)**:
```
ERROR: {'code': -32701, 'message': 'History has been pruned'}
```
公共 RPC 节点 **不保留历史日志**！只能查询最近几小时到几天的数据。

要获取历史数据（如 2024 大选），需要：
1. **Alchemy/Infura** (免费层有限制) - 提供归档节点访问
2. **Dune Analytics** (需要 API Key) - 已索引完整历史
3. **自建归档节点** - 成本高，需要 TB 级存储

### 7. Local Archive / Goldsky (历史回测首选) ✅✅✅

**状态**: **强烈推荐**

**来源**: [warproxxx/poly_data](https://github.com/warproxxx/poly_data) provided archive.

**包含数据**:
- `markets.csv` (~50MB): 完整的市场元数据
- `trades.csv` (~34GB+): 完整的历史交易记录 (包含 `maker`, `taker` 地址！)

**优势**:
- **零网络延迟**: 本地读取，无需 RPC 请求。
- **无速率限制**: 可以全速处理数据。
- **包含 Maker/Taker**: 如果没有这个，无法做 Smart Money 追踪。
- **完整历史**: 包含所有已关闭市场的数据（如 2024 大选）。

**使用工具 (Market_Scanner 目录)**:
- `fast_filter_trades.py`: **核心工具**。使用**二分查找**在几秒钟内从 34GB 文件中定位特定时间段（如 2024-10-01），并提取相关市场的交易。
- `analyze_trump_market.py`: 读取提取出的 CSV，进行 Insider 回测分析。

**工作流**:
1. 下载 `archive.tar.xz` 并解压。
2. 确定目标市场 ID (如 Trump Win: `253591`)。
3. 运行 `fast_filter_trades.py` 提取目标时间段的小文件 (e.g. `trump_trades.csv`)。
4. 运行 Python 脚本分析小文件。

---

## 使用建议

### 场景 1: 分析单个已知用户
**推荐**: Data API `/activity` + `/closed-positions`

### 场景 2: 发现排行榜上的用户
**推荐**: Data API `/leaderboard`

### 场景 3: 实时监控活跃市场
**推荐**: Data API `/trades` (对活跃市场有效)

### 场景 4: 历史回测 (已关闭市场)
### 场景 4: 历史回测 (已关闭市场)
**推荐**: **Local Archive (poly_data)** - 只有它能提供包含钱包地址的完整历史数据。Dune 需要付费 Key，RPC 没有历史记录。

### 场景 5: 检测"未发生"的 Insider
**挑战**: 需要完整的历史交易流 + 实时监控能力
**推荐**: 组合使用 Data API (实时) + Dune/The Graph (历史)

---

## 更新日志

| 日期 | 更新内容 |
|------|----------|
| 2026-02-02 | 初始版本，记录 Data API 和 Gamma API 经验 |
| 2026-02-02 | 发现 trades 端点对已关闭市场的数据保留限制 |
| 2026-02-02 | **Polygon RPC 测试成功！** 使用 `polygon-bor-rpc.publicnode.com` 在 10 分钟内获取 35,000+ 条交易 |
| 2026-02-02 | 确认 The Graph 需要 API Key，Dune Analytics 也需要 API Key |
| 2026-02-02 | **突破**: 集成 `poly_data` 本地数据归档。成功通过 `fast_filter_trades.py` 提取 2024 大选完整交易数据，无需 RPC。 |
