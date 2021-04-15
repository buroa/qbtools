#!/bin/bash
set -e

destination=/usr/local/bin/qbittools

while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -o)
    destination="$2"
    shift # past argument
    shift # past value
    ;;
esac
done

temp_dir=$(mktemp -d)
tag=$(git ls-remote --exit-code --tags --refs https://gitlab.com/AlexKM/qbittools.git | awk '{sub("refs/tags/", ""); print $2 }' | sort -r | head -n1)

curl -L https://gitlab.com/AlexKM/qbittools/-/jobs/artifacts/$tag/download?job=release -o $temp_dir/qbittools.zip
unzip $temp_dir/qbittools.zip -d $temp_dir
mv $temp_dir/qbittools $destination
chmod +x $destination
rm -rf $temp_dir
