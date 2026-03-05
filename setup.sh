#!/usr/bin/env bash
set -e
dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -d ${dir}/.venv ]; then
  rm -rf ${dir}/.venv
fi


if command -v uv >/dev/null 2>&1; then
  uv venv
  uv sync

else
  echo "This project is build with uv, which could not be found."
  echo "Using pip as fallback"
  python3 -m venv .venv
  ./.venv/bin/python -m pip install -r requirements.txt
fi
