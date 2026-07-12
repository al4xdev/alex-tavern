#!/bin/sh
set -e

# Test write permissions in the data directory
if ! touch /app/.data/.permissions_test 2>/dev/null; then
    echo "❌ Error: The directory /app/.data is not writable by the container user."
    echo "Container User details: UID=$(id -u), GID=$(id -g)"
    echo "Please ensure the host directory mounted to /app/.data is writable by this user."
    exit 1
fi
rm -f /app/.data/.permissions_test

# Execute the main container command
exec "$@"
