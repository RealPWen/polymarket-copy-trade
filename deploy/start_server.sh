#!/bin/bash
# ==========================================================
# Polymarket Trading Bot - 服务器启动脚本
# 用于在 Linux 服务器上部署和运行此项目
# ==========================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}    Polymarket Trading Bot - 服务器部署工具    ${NC}"
echo -e "${BLUE}=================================================${NC}"
echo ""

# 检测 Python 版本
detect_python() {
    for cmd in python3.9 python3.10 python3.11 python3; do
        if command -v $cmd &> /dev/null; then
            version=$($cmd --version 2>&1 | awk '{print $2}')
            major=$(echo $version | cut -d. -f1)
            minor=$(echo $version | cut -d. -f2)
            if [ "$major" -ge 3 ] && [ "$minor" -ge 9 ]; then
                echo $cmd
                return 0
            fi
        fi
    done
    echo ""
    return 1
}

PYTHON_CMD=$(detect_python)

if [ -z "$PYTHON_CMD" ]; then
    echo -e "${RED}[错误] 未找到 Python 3.9+，请先安装${NC}"
    echo "推荐使用: sudo apt install python3.9 python3.9-venv"
    exit 1
fi

echo -e "${GREEN}✅ 检测到 Python: $($PYTHON_CMD --version)${NC}"

# 切换到项目根目录
cd "$PROJECT_ROOT"
echo -e "${BLUE}📁 项目目录: $PROJECT_ROOT${NC}"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⏳ 创建虚拟环境...${NC}"
    $PYTHON_CMD -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate
echo -e "${GREEN}✅ 虚拟环境已激活${NC}"

# 安装依赖
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}⏳ 安装依赖...${NC}"
    pip install -q -r requirements.txt
    echo -e "${GREEN}✅ 依赖安装完成${NC}"
fi

# 检查 .env 文件
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}⚠️  未找到 .env 文件，从模板复制${NC}"
        cp .env.example .env
        echo -e "${RED}请编辑 .env 文件并填入您的配置后重新运行${NC}"
        exit 1
    else
        echo -e "${RED}[错误] 未找到 .env 或 .env.example 文件${NC}"
        exit 1
    fi
fi

# 创建必要的目录
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
        # 使用 nohup 后台运行 Flask
        nohup python app.py > logs/flask_server.log 2>&1 &
        FLASK_PID=$!
        echo $FLASK_PID > logs/flask.pid
        sleep 2
        echo -e "${GREEN}✅ Web 服务已启动 (PID: $FLASK_PID)${NC}"
        echo -e "${BLUE}📡 访问地址: http://$(hostname -I | awk '{print $1}'):5005${NC}"
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
        cd "$PROJECT_ROOT"
        nohup python user_listener/account_listener.py "$addresses" > user_listener/logs/listener_nohup.log 2>&1 &
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
        nohup python app.py > logs/flask_server.log 2>&1 &
        FLASK_PID=$!
        echo $FLASK_PID > logs/flask.pid
        sleep 2
        echo -e "${GREEN}✅ Web 服务已启动 (PID: $FLASK_PID)${NC}"
        
        # 再启动监听器
        echo ""
        read -p "请输入要监听的钱包地址 (多个用逗号分隔): " addresses
        if [ -n "$addresses" ]; then
            cd "$PROJECT_ROOT"
            nohup python user_listener/account_listener.py "$addresses" > user_listener/logs/listener_nohup.log 2>&1 &
            LISTENER_PID=$!
            echo $LISTENER_PID > user_listener/logs/listener.pid
            echo -e "${GREEN}✅ 监听器已启动 (PID: $LISTENER_PID)${NC}"
        fi
        
        echo ""
        echo -e "${BLUE}=================================================${NC}"
        echo -e "${GREEN}    所有服务已启动                               ${NC}"
        echo -e "${BLUE}=================================================${NC}"
        echo -e "Web 控制面板: http://$(hostname -I | awk '{print $1}'):5005"
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
