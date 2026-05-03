#!/bin/bash
# Deactivate and unmount the Pokemon Next.js frontend environment

MOUNT_POINT="$(dirname "$0")/frontend/node_modules"

if mountpoint -q "$MOUNT_POINT"; then
    echo "Unmounting frontend node_modules container..."
    sudo umount "$MOUNT_POINT"
    echo "✓ Frontend node_modules unmounted"
else
    echo "Frontend node_modules is not mounted."
fi
