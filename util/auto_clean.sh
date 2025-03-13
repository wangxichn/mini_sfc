#!/bin/bash

echo "Stopping and removing all Docker containers..."

if [ -n "$(docker ps -q)" ]; then
  docker stop $(docker ps -q)
fi

if [ -n "$(docker ps -a -q)" ]; then
  docker rm $(docker ps -a -q)
fi

docker system prune --force

echo "Cleaning up network interfaces created by containers..."
# Fetch names of all matching network interfaces
interfaces=$(ip link show | grep -o 's[0-9]\+-eth[0-9]\+')

# Loop through each found interface and delete it
for interface in $interfaces; do
    # Remove possible colon at the end
    interface=${interface%:*}
    echo "Deleting interface: $interface"
    sudo ip link delete $interface
done

echo "Cleaning up log files..."
rm -rf logsave

echo "Cleanup completed..."