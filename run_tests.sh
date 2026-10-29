#!/usr/bin/env bash
dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${dir}" || exit

if [ -d ./.venv ]; then
  echo "Virtual environment found. Using pytest from virtual environment to run tests"
  ./.venv/bin/pytest "$@"
else
  echo "Virtual environment not found. Trying system wide pytest to run tests"
  pytest "$@"
fi
