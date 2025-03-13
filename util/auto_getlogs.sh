#!/bin/bash

echo "Auto-getting logs from containers..."

mkdir -p logsave

trap 'echo "Script interrupted by user"; exit 0' INT

while true; do

  CONTAINERS=$(sudo docker ps --format '{{.Names}}')

  if [ -z "$CONTAINERS" ]; then
    echo "No containers found. Waiting for containers to become available..., or press ctrl+c to stop the script."
  else
    for CONTAINER_NAME in $CONTAINERS; do
      if [[ "$CONTAINER_NAME" =~ ^mn\.f[0-9]+u[0-9]+$ ]]; then
        UE=${CONTAINER_NAME#mn.}
        SOURCE_FILE="/home/mini_ue/instance/${UE}.log"
        DESTINATION_FILE="logsave/${UE}.log"

        if [ "$(sudo docker inspect -f '{{.State.Status}}' "$CONTAINER_NAME")" == "running" ] || \
          [ "$(sudo docker inspect -f '{{.State.Status}}' "$CONTAINER_NAME")" == "exited" ]; then
            
            sudo docker cp "$CONTAINER_NAME:$SOURCE_FILE" "$DESTINATION_FILE"
            echo "Copied $SOURCE_FILE from container $CONTAINER_NAME to $DESTINATION_FILE"
        else
          echo "Warning: Container $CONTAINER_NAME is not in a running or exited state."
        fi

      elif [[ "$CONTAINER_NAME" =~ ^mn\.f[0-9]+v[0-9]+$ ]]; then
        VNF=${CONTAINER_NAME#mn.}
        SOURCE_FILE="/home/mini_vnf/instance/${VNF}.log"
        DESTINATION_FILE="logsave/${VNF}.log"

        if [ "$(sudo docker inspect -f '{{.State.Status}}' "$CONTAINER_NAME")" == "running" ] || \
          [ "$(sudo docker inspect -f '{{.State.Status}}' "$CONTAINER_NAME")" == "exited" ]; then

          sudo docker cp "$CONTAINER_NAME:$SOURCE_FILE" "$DESTINATION_FILE"
          echo "Copied $SOURCE_FILE from container $CONTAINER_NAME to $DESTINATION_FILE"
        else
          echo "Warning: Container $CONTAINER_NAME is not in a running or exited state."
        fi
      fi
    done
  fi

  sleep 1
done