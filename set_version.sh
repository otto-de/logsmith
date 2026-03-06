#!/usr/bin/env bash
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
c="\x1b[1m"
co="${c}\x1b[38;5;208m"
cb="${c}\x1b[34m"
cr="${c}\x1b[31m"
cg="${c}\x1b[32m"
cy="${c}\x1b[93m"
cc="\x1b[0m"
set -euo pipefail

get_version(){
    uv version --output-format json | jq -r .version
}

usage() {
    name="$(basename $0)"
  cat <<EOF
$name — set of bump version.

Usage:
  $name [OPTIONS] <input> [output]

Options:
  -j, --major
  -i, --minor
  -p, --patch
  -r, --rc
  -h, --help

EOF
    exit 0
}

mode_major=false
mode_minor=false
mode_patch=false
mode_rc=false
mode_dev=false
mode_edit=true
positional=()

while (( "$#" )); do
    case "$1" in
        -h|--help)
            usage
        ;;
        
        -j|--major)
            mode_major=true
            mode_edit=false
            shift
        ;;
        
        -i|--minor)
            mode_minor=true
            mode_edit=false
            shift
        ;;
        -p|--patch)
            mode_patch=true
            mode_edit=false
            shift
        ;;
        -r|--rc)
            mode_rc=true
            mode_edit=false
            shift
        ;;
        -d|--dev)
            mode_dev=true
            mode_edit=false
            shift
        ;;
        
        ##### STANDARD OPTIONS #####
        --) # end of options
            shift
            positional+=("$@")
            break
        ;;
        
        -*) # unknown option
            echo "Error: unknown option: $1" >&2
            exit 2
        ;;
        
        *)  # positional
            positional+=("$1")
            shift
        ;;
    esac
done

if git diff --quiet -- CHANGELOG.md && git diff --cached --quiet -- CHANGELOG.md; then
    echo -e "${cy}WARNING: CHANGELOG.md has no changes${cc}"
fi

current_version=$(get_version)

if [[ $mode_edit == true ]]; then
    read -e -i "$current_version" -p "New version: " new_version || true
    if [ -z "${new_version}" ]; then
        new_version="$current_version"
    fi
    uv version "${new_version}"
else
    if [[ $mode_major == true ]]; then
        uv version --bump major
    fi
    
    if [[ $mode_minor == true ]]; then
        uv version --bump minor
    fi
    
    if [[ $mode_patch == true ]]; then
        uv version --bump patch
    fi
    
    if [[ $mode_rc == true ]]; then
        uv version --bump rc
    fi
    
    if [[ $mode_dev == true ]]; then
        uv version --bump dev
    fi
fi

new_version=$(get_version)

new_version_file_content="version = \"${new_version}\""
echo "$new_version_file_content" > ${script_dir}/app/version.py

echo "Updated to: $new_version"

git add CHANGELOG.md
git add app/version.py
git add pyproject.toml
git add uv.lock

git commit -m "$new_version"

read -p "$(echo -e "${c} Push? ${cg}[Y/n]${cc}") " response
response=${response:-y}
# Convert to lowercase
response="${response,,}"
if [[ "$response" != "y" ]]; then
    echo -e "${cy} Abort! ${cc}"
    exit 0
fi

git push
