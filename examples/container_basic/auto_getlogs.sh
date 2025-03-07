#!/bin/bash

# 确保 logsave 目录存在，不存在则创建
mkdir -p logsave

# 捕获中断信号 (Ctrl+C)
trap 'echo "Script interrupted by user"; exit 0' INT

while true; do

  # 获取所有运行中的容器及其名称
  CONTAINERS=$(sudo docker ps --format '{{.Names}}')

  for CONTAINER_NAME in $CONTAINERS; do
    if [[ "$CONTAINER_NAME" =~ ^mn\.ue_ ]]; then
      # 这是一个UE容器
      UE=${CONTAINER_NAME#mn.}  # 提取UE名称
      SOURCE_FILE="/home/mini_ue/instance/${UE}.log"
      DESTINATION_FILE="logsave/${UE}.log"

      # 检查容器是否存在并且正在运行或已停止但存在
      if [ "$(sudo docker inspect -f '{{.State.Status}}' "$CONTAINER_NAME")" == "running" ] || \
        [ "$(sudo docker inspect -f '{{.State.Status}}' "$CONTAINER_NAME")" == "exited" ]; then
        # 复制日志文件到宿主机
        sudo docker cp "$CONTAINER_NAME:$SOURCE_FILE" "$DESTINATION_FILE"
        echo "Copied $SOURCE_FILE from container $CONTAINER_NAME to $DESTINATION_FILE"
      else
        echo "Warning: Container $CONTAINER_NAME is not in a running or exited state."
      fi

    elif [[ "$CONTAINER_NAME" =~ ^mn\.vnf_ ]]; then
      # 这是一个VNF容器
      VNF=${CONTAINER_NAME#mn.}  # 提取VNF名称
      SOURCE_FILE="/home/mini_vnf/instance/${VNF}.log"
      DESTINATION_FILE="logsave/${VNF}.log"

      # 检查容器是否存在并且正在运行或已停止但存在
      if [ "$(sudo docker inspect -f '{{.State.Status}}' "$CONTAINER_NAME")" == "running" ] || \
        [ "$(sudo docker inspect -f '{{.State.Status}}' "$CONTAINER_NAME")" == "exited" ]; then
        # 复制日志文件到宿主机
        sudo docker cp "$CONTAINER_NAME:$SOURCE_FILE" "$DESTINATION_FILE"
        echo "Copied $SOURCE_FILE from container $CONTAINER_NAME to $DESTINATION_FILE"
      else
        echo "Warning: Container $CONTAINER_NAME is not in a running or exited state."
      fi
    fi
  done

  # 等待 1 秒后再次检查
  sleep 1
done