---
description: 如何运行账户交易监听器
---

如果要监听某个 Polymarket 账户的实时交易，可以运行以下命令：

1. 打开终端并进入项目根目录：
   `/Users/panwen/Desktop/polymarket`

2. 运行监听脚本（将 `[WALLET_ADDRESS]` 替换为你要监听的地址）：
   ```bash
   python3.9 user_listener/account_listener.py [WALLET_ADDRESS]
   ```

// turbo
3. **示例运行（监听 0xdb27... 地址）**:
   ```bash
   /opt/homebrew/bin/python3.9 user_listener/account_listener.py 0xdb27bf2ac5d428a9c63dbc914611036855a6c56e
   ```

监听器将每 5 秒轮询一次 API，并在发现新交易时实时打印出来。
按 `Ctrl + C` 可以停止监听。
