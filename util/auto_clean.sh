#!/bin/bash

echo "正在停止并移除所有Docker容器..."
docker stop $(docker ps -q)
docker rm $(docker ps -a -q)

echo "正在清理未使用的Docker数据..."
docker system prune --force

echo "正在清理container所创建的网络接口..."
# 获取所有符合条件的网络接口名称
interfaces=$(ip link show | grep -o 's[0-9]\+-eth[0-9]\+')

# 循环遍历每个找到的接口并删除它
for interface in $interfaces; do
    # 去除可能的冒号
    interface=${interface%:*}
    echo "正在删除接口: $interface"
    sudo ip link delete $interface
done

echo "正在清理日志文件..."
rm -rf logsave

echo "清理完成..."

echo "正在检查端口占用情况..."
# 指定要检查的端口号
PORT=6653

# 使用lsof查找占用指定端口的进程
PID=$(sudo lsof -t -i :$PORT)

if [ -z "$PID" ]; then
  echo "没有找到占用端口 $PORT 的进程。"
else
  echo "找到占用端口 $PORT 的进程 PID: $PID"
  
  # 尝试正常终止进程
  if sudo kill -15 $PID; then
    echo "已发送终止信号给进程 $PID。等待进程正常退出..."
    
    # 等待一段时间确保进程已经退出
    sleep 2
    
    # 再次检查进程是否还存在
    if ! ps -p $PID > /dev/null; then
      echo "进程 $PID 已成功终止。"
    else
      echo "进程 $PID 未能正常终止，现在强制终止..."
      
      # 强制终止进程
      if sudo kill -9 $PID; then
        echo "进程 $PID 已被强制终止。"
      else
        echo "无法终止进程 $PID。请手动处理。"
      fi
    fi
  else
    echo "无法发送终止信号给进程 $PID。尝试强制终止..."
    
    # 如果正常终止失败，则强制终止
    if sudo kill -9 $PID; then
      echo "进程 $PID 已被强制终止。"
    else
      echo "无法终止进程 $PID。请手动处理。"
    fi
  fi
fi