# 🎯 Polymarket Smart Trader & Copier (专业级多路跟单系统)

![Landing Page](images/landing_page.png)

这是一个专为 **Polymarket** 深度玩家打造的“雷达式”交易员分析与同步执行系统。它不仅能帮助你快速审计市场上明星交易员的往期战绩，还能让你实时开启单路或“多路聚合”的跟随交易。

---

## 🔥 全新升级 (Pro Features)

本系统已升级为 **V2.0 专业版**，新增了以下重磅功能：

### 1. 🖥️ 全能实盘仪表盘 (Dashboard)
![Dashboard Overview](images/dashboard_full.png)
- **实时监控**: 可以在一个页面同时看到 **我的持仓**、**我的成交历史**、**目标交易员的实时订单流**。
- **动态图表**: 自动绘制本金收益曲线 (PnL Chart)，盈亏趋势一目了然。
- **智能刷新**: 仅在余额变动或有新订单时才刷新数据，极低资源占用。

### 2. ⚡️ 策略与目标热更新 (Hot-Swap)
![Strategy Edit](images/dashboard_strategy.png) ![Tracking Management](images/dashboard_tracking.png)
- **策略热修改**: 在仪表盘点击 **"✎ 编辑" (Edit Strategy)**，即可在**不停止程序**的情况下，实时调整跟单金额（如从 $5 改为 $50）或切换模式。
- **目标热管理**: 点击 **"✎ 管理" (Manage Addresses)**，可以随时添加新的监控大神或移除表现不佳的地址，系统会自动平滑重启监听进程。

### 3. 🛡️ macOS 专属防休眠 (Anti-Sleep)
- **自动唤醒**: 内置 `caffeinate -dimsu` 机制，程序启动后会自动阻止 macOS 进入因闲置导致的休眠。
- **合盖运行**: 配合 [Amphetamine](https://apps.apple.com/us/app/amphetamine/id937984704) 工具（需开启无限期模式），可完美实现 MacBook **合盖挂机**。
- **心跳日志**: 通过 `monitored_trades/heartbeat.log` 文件，您可以随时查岗，确认程序是否在后台稳定运行。

---

## 🌟 核心功能演示

### 1. 📊 深度战绩审计
![Configuration Page](images/config_page.png)
输入地址（或逗号分隔的多个地址），系统将并行抓取 Polymarket 链上数据：
- **对比收益曲线**：在同一坐标系下对比多人的累计盈亏。
- **三维数据视图**：Current Positions (当前持仓)、Performance (绩效榜)、Order History (订单流) 全新圆角卡片化展示。

### 2. 🚀 一键开启监控
在分析结果页面点击 **“Start Live Monitor”**，设定好参数（如每单跟 $10），即可开启全自动跟单。

### 3. 🛡️ 稳健跟单逻辑
- **按比例 (Ratio)**：根据目标下单额的倍数进行跟随。
- **恒定金额 (Fixed Amount)**：每次下单固定投入 USD。
- **安全过滤**：自动识别并跳过极低额度（不足 5 股）的无意义成交或灰尘攻击。

---

## 🛠️ 快速部署指南

### 1. 环境准备
项目基于 **Python 3.9+**。
```bash
# 推荐使用虚拟环境
pip install flask pandas requests py-clob-client python-dotenv plotly
```

### 2. 获取 API 凭证 (关键)
你需要准备一个存有一定 USDC 的 Polymarket 钱包作为“执行钱包”：
1. 访问 [reveal.polymarket.com](https://reveal.polymarket.com) 导出你的**私钥 (Private Key)**。
2. 找到你的 **Funder Address** (Proxy 钱包地址)。

### 3. 配置核心变量
在项目根目录创建 `.env` 文件：
```env
POLYMARKET_PRIVATE_KEY=你的私钥
POLYMARKET_FUNDER_ADDRESS=你的Proxy地址
POLYMARKET_SIGNATURE_TYPE=1
MIN_REQUIRED_USDC=5.0
```

---

## 🚀 使用指南

### 第一步：启动主服务器
执行以下命令启动 Web 控制台：
```bash
# 请确保使用 python3.9 或更高版本
python3.9 user_listener/app.py
```
> **提示**: 程序会自动尝试在端口 `5005` 启动。如果端口被占用，请先杀掉旧进程。

访问地址：[http://127.0.0.1:5005](http://127.0.0.1:5005)

### 第二步：分析与对比
1. 在首页输入你想观察的高手地址（支持多个，用逗号分隔）。
2. 点击 **“Analyze Now”** 生成深度报告。

### 第三步：配置策略
1. 点击报表页面的 **“🚀 Start Live Monitor”**。
2. 选择 **“恒定金额”** 或 **“按比例”**，设定参数（例如 50 U）。
3. 选择订单类型：
   - **FOK (市价)**: 推荐，确保成交。
   - **GTC (限价)**: 挂单不一定成交。

### 第四步：看板监控
启动后会自动跳转至 **Dashboard**。
- **资金去向**: 实时查看每一笔跟单的消耗。
- **调整参数**: 觉得跟少了？直接在右上角编辑参数，下一单立即生效！

## 📁 数据存储与系统逻辑 (Data Storage & Logic)

为了保证系统的稳定运行与多端同步，本项目采用了“文件数据库”式的轻量化存储方案。

### 1. 核心存储分布
- **📂 配置与同步 (`user_listener/sync_data/`)**
  - `strategies.json`: 存储所有预设的策略配置。
  - `targets.json`: 存储你关注（正在监听）的交易员地址列表。
  - `wallets.json`: 存储你绑定的执行钱包信息。
- **📂 运行配置与状态 (`user_listener/monitored_trades/`)**
  - `strategy_config.json`: **策略热更新文件**。监听器每单下单前都会读取此文件，确保网页端修改参数后即刻生效。
  - `heartbeat.log`: 监听器心跳，用于确认后台进程存活。
  - `multi_session/`: 以哈希命名的独立 JSON 文件，保存捕捉到的每一笔交易详情。
- **📂 交易审计与缓存**
  - `my_executions.jsonl`: **实盘成交总账**。记录你自己钱包的所有成交历史，是 Dashboard “成交历史”的数据源。
  - `market_cooldown_cache.json`: **方向去重缓存**。记录每个市场已执行过的交易方向（BUY/SELL），防止针对同一市场进行重复的方向性操作（例如：买入过则不再重复买入，但允许卖出）。
- **📂 系统日志 (`user_listener/logs/`)**
  - `copy_trade.log`: 监听进程的完整终端输出，排查下单失败、API 报错的首要入口。

### 2. 重启说明 (Lifecycle)
| 类别 | 状态 | 说明 |
| :--- | :--- | :--- |
| **持久化保留** | ✅ | 所有配置、钱包、监听目标、实盘成交历史、市场冷却缓存。重启不丢失。 |
| **重置/过期** | ❌ | **登录 Session**: 每次重启 Web 程序，浏览器登录状态会失效，需重新输入密码。<br>**后台进程**: 系统重启后，监听进程不会自动启动，需在仪表盘手动点击“启动”。 |

---

## ⚠️ 风险提示与声明
*   **资金风险**：跟单交易具有高度的不确定性。请始终设置你能够承受损失的金额。
*   **网络延迟**：虽然监听为秒级，但在某些极端行情下，跟单价格可能与目标产生一定滑点。
*   **仅供技术研究**：本项目旨在展示如何利用 Polymarket API 进行自动化套利与跟随，不构成任何投资建议。

**Happy Profiting! 💹**

---

## 🗒️ 任务逻辑存储 (Task Logic Archive)

### 2026-02-08 | 存储路径优化与方向去重
1. **方向性去重**: 废弃了 24 小时冷却逻辑，改为记录每个市场的操作方向（BUY/SELL），防止同市场同方向重复下单，但允许反向平仓。
2. **根目录清理**: 将原本散落在根目录的 `market_cooldown_cache.json` 和 `my_executions.jsonl` 统一收纳进 `user_listener/monitored_trades/` 文件夹中。
3. **文件更名**: 冷却缓存文件正式更名为 `market_direction_cache.json` 以匹配其逻辑。
