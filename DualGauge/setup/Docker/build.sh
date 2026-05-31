#!/usr/bin/env bash
set -euo pipefail

# Build the custom Python image with pre-installed packages.
# Path-stable so this script works whether called from setup/, repo root, or Docker/.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
docker build -t python-preloaded:3.11 -f "$SCRIPT_DIR/Dockerfile" "$SCRIPT_DIR"

echo "Custom image built successfully: python-preloaded:3.11"
echo "You can now use this image in your DockerManager"
