#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:-$HOME/active_wind_wall_8X8}"

echo "[1/6] Installing system dependencies"
sudo apt update
sudo apt install -y git python3-venv python3-pip python3-spidev python3-libgpiod

echo "[2/6] Enabling SPI (non-interactive)"
if ! grep -q "^dtparam=spi=on" /boot/firmware/config.txt; then
  echo "dtparam=spi=on" | sudo tee -a /boot/firmware/config.txt >/dev/null
fi

echo "[3/6] Creating project dir: ${PROJECT_DIR}"
mkdir -p "${PROJECT_DIR}"
cd "${PROJECT_DIR}"

if [ ! -d .git ]; then
  echo "[4/6] Cloning repository"
  git clone https://github.com/watsj2/active_wind_wall_8X8.git .
else
  echo "[4/6] Repository already exists, pulling latest"
  git pull --ff-only
fi

echo "[5/6] Creating virtual environment"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-pi-headless.txt

echo "[6/6] Setup complete"
echo "Reboot required once to apply SPI enable:"
echo "  sudo reboot"
echo "After reboot:"
echo "  cd ${PROJECT_DIR}"
echo "  source venv/bin/activate"
echo "  python main.py"
