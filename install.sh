#!/bin/bash
set -e

if ! [ -x "$(command -v git)" ]; then
  echo 'Error: git is not installed. Install git and unzip or download a binary manually from https://gitlab.com/AlexKM/qbittools/-/releases' >&2
  exit 1
fi

if ! [ -x "$(command -v unzip)" ]; then
  echo 'Error: unzip is not installed. Install git and unzip or download a binary manually from https://gitlab.com/AlexKM/qbittools/-/releases' >&2
  exit 1
fi

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

temp_dir=$(mktemp -d)
tag=$(git ls-remote --exit-code --tags --refs https://gitlab.com/AlexKM/qbittools.git | awk '{sub("refs/tags/", ""); print $2 }' | sort -r | head -n1)

curl -L https://gitlab.com/AlexKM/qbittools/-/jobs/artifacts/$tag/download?job=release -o $temp_dir/qbittools.zip
unzip $temp_dir/qbittools.zip -d $temp_dir
mv $temp_dir/qbittools $destination
chmod +rx $destination
rm -rf $temp_dir
