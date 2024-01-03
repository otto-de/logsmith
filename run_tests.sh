#!/usr/bin/env bash
cd tests || exit

if [ -d ../venv ]; then
  echo "Virtual environment found. Using nose2 from virtual environment to run tests"
  ../venv/bin/nosetests
else
  echo "Virtual environment not found. Trying system wide nose2 to run tests"
  nosetests
fi
