#!/bin/bash
# Start script for running Alex Tavern in Docker using the image published on GHCR.

IMAGE_NAME="ghcr.io/al4xdev/alex-tavern:latest"
CONTAINER_NAME="alex-tavern"

# Ensure host .data directory exists with correct permissions
mkdir -p .data

# Pull the latest image
echo "Pulling latest image: $IMAGE_NAME..."
docker pull "$IMAGE_NAME"

# Check if container already exists and stop/remove it
if [ "$(docker ps -aq -f name=^/${CONTAINER_NAME}$)" ]; then
    echo "Stopping and removing existing container..."
    docker stop "$CONTAINER_NAME" >/dev/null 2>&1
    docker rm "$CONTAINER_NAME" >/dev/null 2>&1
fi

# Configure non-root user matching if running on Unix systems with 'id' command
USER_FLAGS=""
if command -v id >/dev/null 2>&1; then
    USER_FLAGS="-u $(id -u):$(id -g)"
fi

# Run the container using host networking
echo "Starting $CONTAINER_NAME in background..."
docker run -d \
  --name "$CONTAINER_NAME" \
  --network host \
  $USER_FLAGS \
  -v "$(pwd)/.data:/app/.data" \
  --restart unless-stopped \
  "$IMAGE_NAME"

echo "Alex Tavern is running in Docker."
