#!/bin/bash
# ==========================================================
# Polymarket Trading Bot - 服务器启动脚本 (精简版)
# ==========================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ⚙️ 服务器配置 - 修改为你的服务器公网 IP
SERVER_IP="47.80.70.38"
SERVER_PORT="5005"

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}    Polymarket Trading Bot - 服务器启动工具    ${NC}"
echo -e "${BLUE}=================================================${NC}"
echo ""

# 切换到项目根目录
cd "$PROJECT_ROOT"
echo -e "${BLUE}📁 项目目录: $PROJECT_ROOT${NC}"

# 创建日志目录
mkdir -p user_listener/logs
mkdir -p monitored_trades

echo ""
echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}    选择启动模式                                  ${NC}"
echo -e "${BLUE}=================================================${NC}"
echo ""
echo "1) 启动 Web 控制面板 (Flask App)"
echo "2) 直接启动跟单监听器 (无 Web)"
echo "3) 同时启动 Web + 监听器"
echo "4) 查看运行状态"
echo "5) 停止所有进程"
echo ""
read -p "请选择 [1-5]: " choice

case $choice in
    1)
        echo -e "${YELLOW}⏳ 启动 Web 控制面板...${NC}"
        cd user_listener
        nohup python3 app.py > logs/flask_server.log 2>&1 &
        FLASK_PID=$!
        echo $FLASK_PID > logs/flask.pid
        sleep 2
        echo -e "${GREEN}✅ Web 服务已启动 (PID: $FLASK_PID)${NC}"
        echo -e "${BLUE}📡 访问地址: http://${SERVER_IP}:${SERVER_PORT}${NC}"
        echo "日志文件: user_listener/logs/flask_server.log"
        ;;
    2)
        echo ""
        read -p "请输入要监听的钱包地址 (多个用逗号分隔): " addresses
        if [ -z "$addresses" ]; then
            echo -e "${RED}[错误] 必须提供监听地址${NC}"
            exit 1
        fi
        echo -e "${YELLOW}⏳ 启动跟单监听器...${NC}"
        nohup python3 user_listener/account_listener.py "$addresses" > user_listener/logs/listener_nohup.log 2>&1 &
        LISTENER_PID=$!
        echo $LISTENER_PID > user_listener/logs/listener.pid
        sleep 2
        echo -e "${GREEN}✅ 监听器已启动 (PID: $LISTENER_PID)${NC}"
        echo "日志文件: user_listener/logs/listener_nohup.log"
        echo "使用 'tail -f user_listener/logs/listener_nohup.log' 查看实时日志"
        ;;
    3)
        # 先启动 Flask
        echo -e "${YELLOW}⏳ 启动 Web 控制面板...${NC}"
        cd "$PROJECT_ROOT/user_listener"
        nohup python3 app.py > logs/flask_server.log 2>&1 &
        FLASK_PID=$!
        echo $FLASK_PID > logs/flask.pid
        sleep 2
        echo -e "${GREEN}✅ Web 服务已启动 (PID: $FLASK_PID)${NC}"
        
        # 再启动监听器
        echo ""
        read -p "请输入要监听的钱包地址 (多个用逗号分隔): " addresses
        if [ -n "$addresses" ]; then
            cd "$PROJECT_ROOT"
            nohup python3 user_listener/account_listener.py "$addresses" > user_listener/logs/listener_nohup.log 2>&1 &
            LISTENER_PID=$!
            echo $LISTENER_PID > user_listener/logs/listener.pid
            echo -e "${GREEN}✅ 监听器已启动 (PID: $LISTENER_PID)${NC}"
        fi
        
        echo ""
        echo -e "${BLUE}=================================================${NC}"
        echo -e "${GREEN}    所有服务已启动                               ${NC}"
        echo -e "${BLUE}=================================================${NC}"
        echo -e "Web 控制面板: http://${SERVER_IP}:${SERVER_PORT}"
        if [ -n "$LISTENER_PID" ]; then
            echo -e "监听器 PID: $LISTENER_PID"
        fi
        ;;
    4)
        echo -e "${BLUE}当前运行的相关进程:${NC}"
        echo ""
        ps aux | grep -E "(app.py|account_listener.py)" | grep -v grep || echo "无运行中的进程"
        ;;
    5)
        echo -e "${YELLOW}⏳ 停止所有进程...${NC}"
        pkill -f "account_listener.py" 2>/dev/null || true
        pkill -f "user_listener/app.py" 2>/dev/null || true
        echo -e "${GREEN}✅ 所有进程已停止${NC}"
        ;;
    *)
        echo -e "${RED}无效选项${NC}"
        exit 1
        ;;
esac

echo ""
