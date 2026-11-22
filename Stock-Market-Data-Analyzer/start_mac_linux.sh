#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
printf '\nLaunch dashboard: source .venv/bin/activate && streamlit run dashboard.py\n'
