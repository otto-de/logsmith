#!/usr/bin/env bash
set -e
dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -d ${dir}/.venv ]; then
  rm -rf ${dir}/.venv
fi

if [ ! -d ${dir}/.venv ]; then
  python3 -m venv .venv
fi

./.venv/bin/pip3 install -r requirements.txt
