#!/bin/bash

# === Directories containing JARs ===
LIB_DIR="./libs"
CONNECTORS_DIR="./connectors"

# === Optional restart flag ===
RESTART_CONTAINERS=true

# === Container names ===
CONTAINERS=("seatunnel_master" "seatunnel_worker_1" "seatunnel_worker_2")

# === Temporary error log file ===
ERROR_LOG=$(mktemp)

# === Function to ensure target directory exists in container ===
ensure_target_dir() {
  local container="$1"
  local target_dir="$2"
  echo "Checking if $target_dir exists in $container..."
  # Use sh instead of bash for broader compatibility
  docker exec "$container" sh -c "[ -d '$target_dir' ] || mkdir -p '$target_dir' && chmod 755 '$target_dir'"
  if [ $? -eq 0 ]; then
    echo "Directory $target_dir ensured in $container"
  else
    echo "Failed to ensure directory $target_dir in $container"
    return 1
  fi
}

# === Function to process JAR files from a directory ===
process_jar_files() {
  local dir="$1"
  local target_folder="$2"
  local jar_files=("$dir"/*.jar)

  if [ ${#jar_files[@]} -eq 0 ] || [ "${jar_files[0]}" = "$dir/*.jar" ]; then
    echo "No .jar files found in $dir"
    return
  fi

  for jar_path in "${jar_files[@]}"; do
    jar_filename=$(basename "$jar_path")
    echo "Processing $jar_filename from $dir..."

    # Check if JAR file is readable
    if [ ! -r "$jar_path" ]; then
      echo "Error: $jar_path is not readable. Check permissions."
      continue
    fi

    for container in "${CONTAINERS[@]}"; do
      if docker ps -q -f name="^/${container}$" | grep -q .; then
        # Ensure target directory exists
        ensure_target_dir "$container" "/opt/seatunnel/$target_folder"
        if [ $? -ne 0 ]; then
          echo "Skipping $container due to directory creation failure"
          continue
        fi

        echo "Copying to $container:/opt/seatunnel/$target_folder/$jar_filename..."
        docker cp "$jar_path" "$container:/opt/seatunnel/$target_folder/$jar_filename" 2>> "$ERROR_LOG"
        if [ $? -eq 0 ]; then
          echo "Copied to $container"
        else
          echo "Failed to copy to $container. Check $ERROR_LOG for details."
        fi
      else
        echo "$container is not running, skipping..."
      fi
    done
  done
}

# === Check if directories exist ===
if [ ! -d "$LIB_DIR" ]; then
  echo "Directory '$LIB_DIR' not found!"
  exit 1
fi

if [ ! -d "$CONNECTORS_DIR" ]; then
  echo "Directory '$CONNECTORS_DIR' not found!"
  exit 1
fi

# === Process JAR files from both directories ===
process_jar_files "$LIB_DIR" "lib"
process_jar_files "$CONNECTORS_DIR" "connectors"

# === Restart containers if needed ===
if [ "$RESTART_CONTAINERS" = true ]; then
  echo "Restarting containers..."
  for container in "${CONTAINERS[@]}"; do
    if docker ps -q -f name="^/${container}$" | grep -q .; then
      docker restart "$container"
      if [ $? -eq 0 ]; then
        echo "Restarted $container"
      else
        echo "Failed to restart $container"
      fi
    fi
  done
fi

# === Display errors if any ===
if [ -s "$ERROR_LOG" ]; then
  echo "Errors occurred during the process. See details below:"
  cat "$ERROR_LOG"
else
  echo "No errors detected."
fi

# === Clean up ===
rm -f "$ERROR_LOG"

echo "JAR injection process completed."