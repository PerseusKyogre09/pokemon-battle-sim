#!/bin/bash
# Activate the Pokemon project virtual environment
# The venv is stored in an ext4 container on the external SSD

# Mount the venv container if not already mounted
if ! mountpoint -q "$(dirname "$0")/venv"; then
    echo "Mounting venv container..."
    sudo mount -o loop "$(dirname "$0")/venv.img" "$(dirname "$0")/venv"
fi

source "$(dirname "$0")/venv/bin/activate"
echo "✓ Pokemon environment activated"
echo "Python: $(python --version)"
echo "Pip: $(pip --version)"
