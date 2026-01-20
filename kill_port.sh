#!/bin/bash
PORT=5005
PID=$(lsof -ti:$PORT)

if [ -z "$PID" ]; then
  echo "🍀 没有发现在端口 $PORT 运行的程序。"
else
  echo "🔥 正在关闭端口 $PORT 上的进程 (PID: $PID)..."
  kill -9 $PID
  if [ $? -eq 0 ]; then
    echo "✅ 成功关闭！你现在可以重新运行 app.py 了。"
  else
    echo "❌ 关闭失败，请尝试使用 sudo 运行此脚本。"
  fi
fi
