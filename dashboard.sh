#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1
source .venv/bin/activate
docker compose up -d db
streamlit run src/birthdays/web.py
