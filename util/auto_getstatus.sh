#!/bin/bash

echo "Auto-getting status from containers..."

mkdir -p logsave

output_file="logsave/vnf_stats.log"
> $output_file  # clear the file

trap 'echo "Script interrupted by user"; exit 0' INT

while true; do
  timestamp=$(date "+%Y-%m-%d %H:%M:%S")
  container_found=false
  
  docker stats --no-stream --format "{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | while IFS=$'\t' read -r name cpu mem; do
    container_found=true
    echo -e "$timestamp\t$name\t$cpu\t$mem"
    echo -e "$timestamp\t$name\t$cpu\t$mem" >> $output_file
  done

  if ! $container_found; then
    echo "No containers found. Waiting for containers to become available..., or press ctrl+c to stop the script."
  fi
  
  sleep 1
done