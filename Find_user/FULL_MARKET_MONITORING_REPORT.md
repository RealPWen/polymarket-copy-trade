
# Polymarket 全量市场监听测试报告

## 1. 测试综述
我们对 Polymarket 的 CLOB (Central Limit Order Book) WebSocket 接口进行了采样测试，以评估全量监听所有 Open Market 的数据带宽、消息频率和延迟情况。

### 测试环境
- **采样样本**: 300 个热门 Active Markets (对应约 600 个 Token Assets)。
- **测试时长**: ~30 秒。
- **采集工具**: Python `websockets` + `asyncio`。

## 2. 测试结果 (300 Markets)

| 指标 | 观测值 | 说明 |
| :--- | :--- | :--- |
| **消息速率** | ~15 msg/s | 每秒接收 WebSocket 帧数 |
| **数据带宽** | ~40 KB/s | 实时数据流大小 |
| **快照大小** | ~2 KB / Market | 初始 Orderbook 快照 |
| **平均延迟** | ~1382 ms | (Server Timestamp -> Client Receive) |
| **P95 延迟** | ~4440 ms | 95% 分位延迟，显示有显著抖动/排队 |

> **注意**: 延迟数据包含 Client 与 Server 的时钟偏差，但 P95 远高于平均值表明存在明显的**数据堆积或网络抖动**。在单线程 Python 脚本中处理数百个并发订阅对 Event Loop 压力较大。

## 3. 全量推算 (预估 5000 Active Markets)
假设当前有 5000 个活跃市场 (10,000 Tokens)，全量监听的预估压力如下：

| 指标 | 预估值 | 备注 |
| :--- | :--- | :--- |
| **消息速率** | ~250 - 500 msg/s | 峰值可能更高 (重大事件时) |
| **数据带宽** | ~0.7 - 1.5 MB/s | 连续带宽 |
| **启动快照** | ~20 - 50 MB | 连接建立瞬间的突发流量 |
| **日数据量** | ~60 - 100 GB | 原始 JSON 文本存储 |

## 4. 架构与数据结构设计建议

面对上述数据量，简单的单机 Python 脚本（单进程）将面临严重的性能瓶颈（GIL、GC Pause、WebSocket 背压）。建议采用以下**生产级架构**：

### A. 架构设计 (Ingestion Pipeline)
采用 **"分片接入 -> 消息队列 -> 并行处理"** 的架构：

1.  **分片接入 (Sharded Ingestion)**:
    *   不要用单一连接订阅所有 10k Tokens。
    *   建立 5-10 个 WebSocket 连接，每个负责 1000-2000 个 Token。
    *   建议使用 **Go** 或 **Rust** 编写接入层 (Gateway)，仅负责接收、解压、转发，不做业务逻辑。

2.  **消息队列 (Message Buffer)**:
    *   将收到的 Raw JSON 推送至 **Kafka** 或 **Redpanda**。
    *   Topic 划分: `polymarket-books`, `polymarket-trades`。
    *   目的: 解耦，防止消费者处理慢导致 WebSocket 断连。

3.  **持久化存储 (Storage)**:
    *   **Tick 数据**: ClickHouse 或 TimescaleDB (压缩率高，查询快)。
    *   **K-Line**: 基于 Tick 数据实时聚合存入 PostgreSQL/TimescaleDB。

### B. 内部数据结构 (Data Structures)
在编写策略或 Orderbook 维护代码时：

1.  **Orderbook 维护**:
    *   **不要使用**: 嵌套 Python Dict (如 `{price: size}`)，内存开销大且慢。
    *   **建议使用**: 
        *   **Python**: `sortedcontainers.SortedDict` (维护价格有序性)。
        *   **High Performance**: `numpy` 数组或 `Rust` 绑定的 Orderbook 实现。
        *   由于 Polymarket 深度较稀疏，Hash Map (`dict`) + 价格排序列表 (`list`) 的混合结构通常足够。

2.  **ID 映射**:
    *   使用两个双向 Hash Map: `TokenID <-> MarketID` 和 `TokenID <-> Outcome (Yes/No)`。
    *   预先加载所有 Active Markets 的 metadata 到内存 (Redis 或本地 LRU Cache)。

### C. 延迟优化
*   **网络**: 部署在靠近 AWS us-east-1 (Polymarket 服务器常见位置) 的节点。
*   **协议**: 保持 WebSocket 连接活跃，定期 Ping/Pong。
*   **序列化**: 使用 `orjson` 替代标准 `json` 库，解析速度快 5-10 倍。

## 5. 结论
Polymarket 全量数据量属于**中等规模** (1MB/s 级别)，但对**实时性处理能力**要求较高。单机 Python 原型仅适合几百个市场的监听。全量监听建议升级为**Go/Rust 接入层 + Kafka** 架构。
