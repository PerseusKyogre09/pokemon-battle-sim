#!/bin/bash
# Unmount the venv container when you're done

VENV_PATH="$(dirname "$0")/venv"

if mountpoint -q "$VENV_PATH"; then
    echo "Unmounting venv container..."
    sudo umount "$VENV_PATH"
    echo "✓ Venv container unmounted"
else
    echo "Venv container is not mounted"
fi
