#!/usr/bin/env bash
c="\x1b[1m"
co="${c}\x1b[38;5;208m"
cb="${c}\x1b[34m"
cr="${c}\x1b[31m"
cg="${c}\x1b[32m"
cy="${c}\x1b[93m"
cc="\x1b[0m"
set -euo pipefail

version_file="app/version.py"

if ! current_version="$(awk '
  BEGIN { found = 0 }
  /^[[:space:]]*version[[:space:]]*=/ && found == 0 {
    line = $0
    sub(/^[[:space:]]*version[[:space:]]*=[[:space:]]*/, "", line)
    gsub(/^[[:space:]]*"/, "", line)
    gsub(/"[[:space:]]*$/, "", line)
    print line
    found = 1
  }
  END { if (found == 0) exit 1 }
' "$version_file")"; then
  echo "Could not find version in $version_file" >&2
  exit 1
fi

read -e -i "$current_version" -p "New version: " new_version || true

if [ -z "${new_version}" ]; then
  new_version="$current_version"
fi

new_version="version = \"${new_version}\""
echo "$new_version" > $version_file

echo "Updated to: $new_version"

git add ./CHANGELOG.md
git add app/version.py
git tag "$new_version"
git commit -m "$new_version"

read -p "$(echo -e "${c} Push? ${cg}[Y/n]${cc}") " response
response=${response:-y}
# Convert to lowercase
response="${response,,}"
if [[ "$response" != "y" ]]; then
    echo -e "${cy} Abort! ${cc}"
    exit 1    
fi

git push
