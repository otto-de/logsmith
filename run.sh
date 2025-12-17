#!/usr/bin/env bash

### This resolves the current path of this script, also if it is called through symlinks etc.
SCRIPT="${BASH_SOURCE[0]}"
while [ -h "$SCRIPT" ]; do
  DIR="$( cd -P "$( dirname "$SCRIPT" )" >/dev/null 2>&1 && pwd )"
  SCRIPT="$(readlink "$SCRIPT")"
  [[ $SCRIPT != /* ]] && SCRIPT="$DIR/$SCRIPT"
done
DIR="$( cd -P "$( dirname "$SCRIPT" )" >/dev/null 2>&1 && pwd )"

cd ${DIR} || exit

if [[ ! -d ./venv/ ]]; then
    ./setup.sh
fi
export PYTHONPATH=${PYTHONPATH}:${DIR}
./.venv/bin/python ./app/run.py "${@}"