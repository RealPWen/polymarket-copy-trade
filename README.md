# 🎯 Polymarket Smart Trader & Copy-Trading System

这是一个专为 **Polymarket** 打造的专业级交易员分析工具与自动化跟单系统。它集成了深度数据分析、多策略执行监控以及全方位的可视化仪表盘，助你发现并跟随市场上的明星交易员。

---

## 🌟 核心功能

### 1. 📊 深度交易员分析 (Trader Analysis)
利用 Polymarket Data API，对任意地址进行深度审计，生成专业的可视化报告：
- **收益曲线 (Equity Curve)**：实时计算并展示累计 PnL 走势。
- **市场表现 (Win/Loss Rank)**：自动统计该交易员在各个市场的盈亏排名。
- **当前持仓 (Live Positions)**：透视交易员当前持有的所有份额及价值。
- **历史订单流 (Order History)**：完整还原所有的买入与卖出细节。

![Trader Analysis](docs/assets/analysis.png)

### 2. 🛡️ 智能跟单策略 (Smart Copy-Trade)
系统提供三种灵活的跟单模式，满足不同资金规模的玩家需求：
- **按金额比例 (Amount Ratio)**：跟随交易员的下单金额按固定比例缩放。
- **仓位占比 (Portfolio Ratio)**：根据双方余额比例自动计算仓位，实现真正的“复制”交易。
- **恒定金额 (Constant Amount)**：无论对方下多少，你始终以固定的 USD 金额投入。

![Strategy Setup](docs/assets/setup.png)

### 3. 🚀 实时跟单仪表盘 (Live Dashboard)
三栏布局的专业监控台，让你实时掌握全局：
- **左栏 (我的账户)**：实时显示你的 USDC 余额以及通过系统下达的跟单记录。
- **中栏 (实时收益)**：通过可视化图表监控跟单后的即时回报。
- **右栏 (目标流)**：实时同步目标交易员的每一个链上动作。

![Live Dashboard](docs/assets/dashboard.png)

---

## 🛠️ 安装与配置

### 1. 安装依赖
确保你使用的是 Python 3.9+ 环境：
```bash
pip install flask pandas requests py-clob-client python-dotenv plotly
```

### 2. 配置环境变量
在项目根目录创建 `.env` 文件，填入你的 Polymarket 凭证：
```env
POLYMARKET_PRIVATE_KEY=你的私钥 (从 reveal.polymarket.com 导出)
POLYMARKET_FUNDER_ADDRESS=你的代理钱包地址
POLYMARKET_SIGNATURE_TYPE=1
MIN_REQUIRED_USDC=5.0
```

---

## 🚀 启动与使用

### 1. 运行 Web 服务器
```bash
python user_listener/app.py
```
启动成功后，浏览器访问 `http://127.0.0.1:5005`。

### 2. 开始跟单流程
1. **输入地址**：在主页输入你想分析的交易员地址。
2. **分析报告**：查看分析报告，双击 “Order History” 或点击开关进入跟单配置。
3. **选择策略**：根据你的资金量选择合适的比例或模式。
4. **即时监控**：跳转至 Dashboard，坐享自动化跟单体验。

---

## 📂 项目结构
- `user_listener/app.py`: Flask Web 服务器核心，处理路由与 API。
- `user_listener/account_listener.py`: 核心监听器，捕获链上交易。
- `user_listener/trade_handlers.py`: 策略执行层，负责计算金额并调用 API 下单。
- `user_listener/trader_analyzer.py`: 数据分析模块，负责 PnL 计算。
- `user_listener/visualize_trader.py`: 报告生成引擎。
- `user_listener/polymarket_trader.py`: CLOB 下单协议集成。

---

## ⚠️ 免责声明
本项目仅供学习和技术研究使用。加密货币交易涉及极高风险，**过往业绩不代表未来表现**。请确保在使用前充分理解代码逻辑，并注意资金安全。

**Happy Trading! 💸**
