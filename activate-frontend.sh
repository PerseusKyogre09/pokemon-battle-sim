#!/bin/bash
# Activate the Pokemon Next.js frontend environment
# node_modules are stored in an ext4 container to support symlinks and binaries

FRONTEND_DIR="$(dirname "$0")/frontend"
IMG_FILE="$(dirname "$0")/frontend.img"
MOUNT_POINT="$FRONTEND_DIR/node_modules"

# Ensure mount point exists
mkdir -p "$MOUNT_POINT"

# Mount the frontend container if not already mounted
if ! mountpoint -q "$MOUNT_POINT"; then
    echo "Mounting frontend node_modules container..."
    sudo mount -o loop "$IMG_FILE" "$MOUNT_POINT"
    # Ensure user has permissions
    sudo chown $USER:$USER "$MOUNT_POINT"
fi

echo "✓ Frontend node_modules mounted"
echo "You can now run 'npm install' inside the frontend directory."
