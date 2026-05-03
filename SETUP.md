# External SSD Setup Guide

Your Python virtual environment is stored in an **ext4 filesystem container** on the external SSD to support symlinks (exFAT doesn't support them).

## Files Created
- `venv.img` - 2GB ext4 filesystem image containing the venv
- `activate-env.sh` - Script to mount and activate the environment
- `deactivate-env.sh` - Script to unmount the venv container

## Usage

### Activate the environment (do this once per session)
```bash
cd /run/media/perseuskyogre/T7/Projects/Pokemon
source activate-env.sh
```

The first time you run it, it will prompt for your sudo password to mount the container. This is normal and only happens once per reboot.

### Use your project
```bash
# Run the Flask server
python web_server.py

# Run tests
python test_priority_messaging.py

# Install new packages
pip install package-name
```

### Unmount when done (optional)
```bash
source deactivate-env.sh
```

## Why this setup?
- **exFAT limitation**: External drives are typically exFAT (Windows compatible), which doesn't support symlinks
- **Solution**: ext4 container image stores the venv with full symlink support
- **Persistence**: Unlike `/tmp`, this survives reboots and everything stays on your external SSD

## Notes
- All 90+ npm packages are already installed (`--no-bin-links` workaround for exFAT)
- All Python dependencies from `requirements.txt` are installed
- The venv takes ~500MB of the 2GB container space
- Everything is on your external SSD, no internal storage needed
