#!/usr/bin/env bash
set -e

if [ ! -d ${dir}/venv ]; then
  pip3 install --user virtualenv
  python3 -m virtualenv -p python3 venv
fi

./venv/bin/pip3 install -r requirements.txt
