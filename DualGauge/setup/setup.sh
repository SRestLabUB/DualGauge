#!/usr/bin/env bash
set -e

# Detect OS and install Docker + Bash if needed
if [[ "$OSTYPE" == "darwin"* ]]; then
  echo "Detected macOS..."
  # Ensure Homebrew is installed
  if ! command -v brew &>/dev/null; then
    echo "Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  fi

  brew install --cask docker
  brew install bash

elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
  echo "Detected Linux..."
  sudo apt-get update -y
  sudo apt-get install -y docker.io bash
  sudo systemctl enable docker
  sudo systemctl start docker
else
  echo "Unsupported OS: $OSTYPE"
  exit 1
fi

# Run your build script
bash Docker/build.sh
