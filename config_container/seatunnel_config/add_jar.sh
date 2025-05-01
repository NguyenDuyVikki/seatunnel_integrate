#!/bin/bash

# === Directory containing JARs ===
JAR_DIR="./libs"

# === Optional restart flag ===
RESTART_CONTAINERS=true

# === Container names ===
CONTAINERS=("seatunnel_master" "seatunnel_worker_1" "seatunnel_worker_2")

# === Check if directory exists ===
if [ ! -d "$JAR_DIR" ]; then
  echo "Directory '$JAR_DIR' not found!"
  exit 1
fi

# === Find JAR files ===
JAR_FILES=("$JAR_DIR"/*.jar)

if [ ${#JAR_FILES[@]} -eq 0 ]; then
  echo "No .jar files found in $JAR_DIR"
  exit 0
fi

# === Copy each JAR to each container ===
for JAR_PATH in "${JAR_FILES[@]}"; do
  JAR_FILENAME=$(basename "$JAR_PATH")
  echo "Processing $JAR_FILENAME..."

  for container in "${CONTAINERS[@]}"; do
    if docker ps -q -f name="^/${container}$" | grep -q .; then
      echo "Copying to $container..."
      docker cp "$JAR_PATH" "$container:/opt/seatunnel/lib/$JAR_FILENAME"
      if [ $? -eq 0 ]; then
        echo "Copied to $container"
      else
        echo "Failed to copy to $container"
      fi
    else
      echo "$container is not running, skipping..."
    fi
  done
done

# === Restart containers if needed ===
if [ "$RESTART_CONTAINERS" = true ]; then
  echo "Restarting containers..."
  for container in "${CONTAINERS[@]}"; do
    if docker ps -q -f name="^/${container}$" | grep -q .; then
      docker restart "$container"
    fi
  done
fi

echo "JAR injection process completed."
