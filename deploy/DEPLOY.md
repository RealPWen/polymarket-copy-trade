# Polymarket Trading Bot - 服务器部署指南

## 📋 前提条件

- **操作系统**: Linux (推荐 Ubuntu 20.04+ / CentOS 8+)
- **Python**: 3.9 或更高版本
- **网络**: 能够访问 Polymarket API (clob.polymarket.com)

## 🚀 快速部署

### 1. 上传项目到服务器

```bash
# 使用 scp 上传整个项目
scp -r /path/to/polymarket user@your-server:/home/user/
```

### 2. 安装系统依赖

```bash
# Ubuntu / Debian
sudo apt update
sudo apt install python3.9 python3.9-venv python3-pip git -y

# CentOS / RHEL
sudo yum install python39 python39-pip git -y
```

### 3. 配置环境变量

```bash
cd /home/user/polymarket
cp .env.example .env
nano .env  # 编辑并填入您的私钥和钱包地址
```

**重要配置项**:
```env
POLYMARKET_PRIVATE_KEY=0x您的私钥
POLYMARKET_FUNDER_ADDRESS=0x您的钱包地址
POLYMARKET_SIGNATURE_TYPE=1
```

### 4. 运行部署脚本

```bash
chmod +x deploy/start_server.sh
./deploy/start_server.sh
```

选择启动模式：
- 选项 1: 仅启动 Web 控制面板
- 选项 2: 仅启动跟单监听器
- 选项 3: 同时启动

## 📁 重要文件说明

| 路径 | 说明 |
|------|------|
| `user_listener/logs/flask_server.log` | Web 服务日志 |
| `user_listener/logs/listener_nohup.log` | 监听器日志 |
| `user_listener/logs/copy_trade.log` | 跟单执行日志 |
| `monitored_trades/` | 交易记录存储 |

## 🔍 常用命令

### 查看运行状态

```bash
# 查看所有相关进程
ps aux | grep -E "(app.py|account_listener.py)" | grep -v grep

# 实时查看监听器日志
tail -f user_listener/logs/listener_nohup.log

# 实时查看 Flask 日志
tail -f user_listener/logs/flask_server.log
```

### 停止服务

```bash
# 停止所有监听器
pkill -f "account_listener.py"

# 停止 Web 服务
pkill -f "user_listener/app.py"
```

### 重启服务

```bash
# 先停止
pkill -f "account_listener.py"
pkill -f "user_listener/app.py"

# 再启动
./deploy/start_server.sh
```

## 🔧 API 端点

部署后可通过以下 API 检查状态：

| 端点 | 说明 |
|------|------|
| `GET /api/health` | 后端健康检查 |
| `GET /api/server-info` | **服务器环境诊断** (新增) |
| `GET /api/copy-trade/status/<address>` | 跟单状态 |

示例:
```bash
curl http://your-server:5005/api/server-info
```

## 🐛 常见问题

### Q: 进程启动后立即退出

检查日志文件:
```bash
cat user_listener/logs/listener_nohup.log
```

常见原因:
- .env 配置错误
- Python 依赖未安装
- 网络无法访问 API

### Q: 如何使用 systemd 管理服务

创建 `/etc/systemd/system/polymarket.service`:

```ini
[Unit]
Description=Polymarket Trading Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/home/your-user/polymarket/user_listener
ExecStart=/home/your-user/polymarket/venv/bin/python app.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

启用服务:
```bash
sudo systemctl daemon-reload
sudo systemctl enable polymarket
sudo systemctl start polymarket
```

### Q: 如何配置 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5005;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📞 获取帮助

如遇问题，请访问 `/api/server-info` 获取诊断信息后再求助。
