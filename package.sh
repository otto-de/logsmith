#!/usr/bin/env bash
dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
usage() {
  echo "Usage: package.sh [-a]"
  echo "    packages logsmith into a executable"
  echo ""
  echo "Options:"
  echo "    -l  build for linux"
  echo "    -w  build for windows"
  echo "    -g  use system python"
  echo "    -z  zip after build"
  exit 1
}
global_mode=false
zip_mode=false
ignore_mode=false
while getopts "lwgzih" opt; do
  case ${opt} in
  l)
    mode="linux"
    ;;
  w)
    mode="windows"
    ;;
  g)
    global_mode=true
    ;;
  z)
    zip_mode=true
    ;;
  i)
    ignore_mode=true
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

local_changes=$(git status --porcelain -uno)
untracked_files=$(git ls-files --others --exclude-standar)
if ! ${ignore_mode} && [ "${local_changes}" != "" ]; then
  echo -e " local changes found."
  echo "${local_changes}"
  exit 1
fi
if ! ${ignore_mode} && [ "${untracked_files}" != "" ]; then
  echo -e " untracked files found."
  echo "${untracked_files}"
  exit 1
fi

if [[ ! -d ./venv/ ]] && [[ "${global_mode}" == "false" ]]; then
  ./setup.sh
fi
if [[ -d ./dist/ ]]; then
  rm -rf dist
fi
if [[ -d ./build/ ]]; then
  rm -rf build
fi

if [[ "${global_mode}" == "false" ]]; then
  bundler=${dir}/venv/bin/pyinstaller
else
  bundler="python3.8 -m PyInstaller"
fi

dist=$(uname)
dist=$(echo "${dist}" | tr '[:upper:]' '[:lower:]')
dist_path=${dir}/dist/${dist}
${bundler} \
  --distpath "${dist_path}" \
  ./logsmith.spec

if [[ "${dist}" == "darwin" ]] && [[ "${mode}" == "linux" ]]; then
  docker run \
    -v "$(pwd):/src/" \
    cdrx/pyinstaller-linux \
    "pyinstaller --onefile --hidden-import PyQt6.sip --distpath ${dist_path} ./logsmith.spec"
fi

if [[ "${mode}" == "windows" ]]; then
  docker run \
    -v "$(pwd):/src/" \
    cdrx/pyinstaller-windows \
    "pyinstaller --onefile --hidden-import PyQt6.sip ./logsmith.spec"
fi

if ${zip_mode}; then
  version=$(python3 -c "from app.__version__ import __version__; print('.'.join(str(i) for i in __version__))")
  cd "${dist_path}" || exit
  zip -r logsmith_${dist}_${version}.zip ./logsmith*
fi
