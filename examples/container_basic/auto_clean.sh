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
