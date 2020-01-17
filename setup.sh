#!/usr/bin/env bash
set -ex

pip install --user virtualenv
python -m virtualenv -p python3 venv

./venv/bin/pip3 install -r requirements.txt
