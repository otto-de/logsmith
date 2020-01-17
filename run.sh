#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [[ ! -d ./venv/ ]]; then
    ./setup.sh
fi
export PYTHONPATH=${PYTHONPATH}:${DIR}
./venv/bin/python ./app/run.py
