#!/bin/bash

# 确保 logsave 目录存在，不存在则创建
mkdir -p logsave

# 设置输出文件
output_file="logsave/vnf_stats.log"
> $output_file  # 清空文件

# 捕获中断信号 (Ctrl+C)
trap 'echo "Script interrupted by user"; exit 0' INT

# 无限循环
while true; do
  # 获取当前时间戳
  timestamp=$(date "+%Y-%m-%d %H:%M:%S")
  
  # 执行docker stats并将输出通过管道传递给while循环
  docker stats --no-stream --format "{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | while IFS=$'\t' read -r name cpu mem; do
    # 打印到终端并追加到文件
    echo -e "$timestamp\t$name\t$cpu\t$mem"
    echo -e "$timestamp\t$name\t$cpu\t$mem" >> $output_file
  done
  
done