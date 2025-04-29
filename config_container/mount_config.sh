#!/bin/bash

CONFIG_DIR="./seatunnel_config"

if [ ! -f "$CONFIG_DIR/seatunnel.yaml" ]; then
  echo " Cannot find $CONFIG_DIR/seatunnel.yaml"
  echo "Please create the full configuration in the $CONFIG_DIR directory first."
  exit 1
fi

# Run the container and mount the entire config directory
docker run --rm -it \
  -v "$(pwd)/$CONFIG_DIR:/opt/seatunnel/config" \
  apache/seatunnel:latest \
  /bin/sh -c "/opt/seatunnel/bin/seatunnel.sh --config /opt/seatunnel/config/seatunnel.yaml"
