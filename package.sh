#!/usr/bin/env bash
usage() { echo "Usage: package.sh [-a]"
          echo "    packages logsmith into a executable"
          echo ""
          echo "Options:"
          echo "    -l  build for linux"
          echo "    -w  build for windows"
          exit 1; }

while getopts "lw" opt; do
  case ${opt} in
    l)
      mode="linux"
      ;;
    w)
      mode="windows"
      ;;
    h)
      usage
      ;;
    *)
      echo -e "Invalid option: -${OPTARG}"
      usage
      ;;
  esac
done

if [[ ! -d ./venv/ ]]; then
    ./setup.sh
fi
if [[ -d ./dist/ ]]; then
    rm -rf dist
fi
if [[ -d ./build/ ]]; then
    rm -rf build
fi

dist_path=./dist/$(uname)
./venv/bin/pyinstaller \
    --onefile \
    --distpath ${dist_path} \
    ./logsmith.spec

if [[ "$(uname)" == "Darwin" ]] && [[ "${mode}" == "linux" ]]; then
    docker run \
        -v "$(pwd):/src/" \
        cdrx/pyinstaller-linux \
        "pyinstaller --onefile --hidden-import PyQt5.sip --distpath ./dist/linux ./logsmith.spec"
fi

if [[ "${mode}" == "windows" ]]; then
    docker run \
        -v "$(pwd):/src/" \
        cdrx/pyinstaller-windows \
        "pyinstaller --onefile --hidden-import PyQt5.sip ./logsmith.spec"
fi
