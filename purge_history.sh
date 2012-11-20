#!/bin/bash

if [ "$1" == "" ]; then
    echo "usage: $0 dirs_to_purge"
    exit 1
fi

while true; do
    [ "$1" == "" ] && break
    echo "processing $1"
    find "$1" \( -iname "*.txt" -or -iname "radius.log*" \) -mtime +29 -print0 | xargs -0 rm -f
    shift
done

echo "finished."
