#!/usr/bin/env bash
set -euo pipefail

# ---- Ensure prerequisites ----
install_zstd() {
  if command -v zstd >/dev/null 2>&1; then
    echo "zstd already installed"
    return
  fi

  echo "Installing zstd..."

  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -y
    sudo apt-get install -y zstd curl ca-certificates
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y zstd curl ca-certificates
  elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y zstd curl ca-certificates
  elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -Sy --noconfirm zstd curl ca-certificates
  else
    echo "ERROR: Unsupported package manager. Install 'zstd' manually and rerun."
    exit 1
  fi
}

install_zstd

curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
pid=$!

while ! pgrep -f "ollama"; do
  sleep 0.1
done

sleep 15
ollama pull llama3.2
ollama list


# Warmup the model for faster first responses
echo "Warming up llama3.2 model..."
bash "$(dirname "$0")/warmup.sh" || echo "Model warmup failed, but continuing anyway"

# kill ollama process here since it runs in a separate shell
# startup command will restart it
pkill -9 "ollama"
