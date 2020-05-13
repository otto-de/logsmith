#!/usr/bin/env bash
DIR=$(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)

cd ${DIR} || exit

if [[ ! -d ./venv/ ]]; then
    ./setup.sh
fi
export PYTHONPATH=${PYTHONPATH}:${DIR}
./venv/bin/python ./app/run.py