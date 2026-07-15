#!/usr/bin/env bash
set -euo pipefail

cd /home/jwatson/active_wind_wall_8X8

export PYTHONPATH="/home/jwatson/active_wind_wall_8X8/venv/lib/python3.11/site-packages:/usr/lib/python3/dist-packages:/usr/lib/python3.11/dist-packages${PYTHONPATH:+:$PYTHONPATH}"
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-xcb}"

exec python3 gui_interface.py
