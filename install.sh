#!/bin/bash
set -e

destination=/usr/local/bin/qbittools

while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -o)
    destination="$2"
    shift
    shift
    ;;
esac
done

tag=$(curl -s https://gitlab.com/api/v4/projects/23524151/releases | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['tag_name'])")

if [ -z "$tag" ]; then
    echo "Couldn't find the latest tag!"
    exit 1
fi

arch=$(uname -m)
os=$(uname -s)
url="https://gitlab.com/api/v4/projects/23524151/packages/generic/qbittools/$tag/qbittools_${os,,}_${arch,,}"

http_code=$(curl -L $url -o $destination --write-out "%{http_code}")

if [[ ${http_code} -lt 200 || ${http_code} -gt 299 ]] ; then
    echo "Curl failed with $http_code code, check response at $destination"
    exit 22
fi

chmod +rx $destination
echo "Installed qbittools to $destination!"