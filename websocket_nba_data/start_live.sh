#!/bin/bash
# NBA 方案 A 实时系统一键启动脚本

# 获取当前脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"
POLY_VENV="$PROJECT_ROOT/../venv"

cd "$PROJECT_ROOT"

# 检查虚拟环境
if [ ! -d "$POLY_VENV" ]; then
    echo "❌ 错误: 未找到虚拟环境，请确保在 $POLY_VENV 存在。"
    exit 1
fi

echo "🏀 正在启动 NBA 毫秒级数据分发后端..."
# 在后台启动后端
"$POLY_VENV/bin/python" nba_live_backend.py &
BACKEND_PID=$!

# 等待后端启动
sleep 2

echo "🌐 正在打开前端看板..."
# 使用默认浏览器打开 index.html
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "index.html"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open "index.html"
fi

echo "✨ 系统已就绪！"
echo "👉 浏览器应已自动打开 index.html"
echo "👉 后端 PID: $BACKEND_PID"
echo "按 Ctrl+C 停止所有服务..."

# 捕捉退出信号，同时杀掉后端
trap "kill $BACKEND_PID; exit" INT TERM
wait
