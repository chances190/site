#!/bin/bash

datetime=$(date +%Y-%m-%d-%H%M)
note="./content/notes/${datetime}.txt"

if [[ -n "$1" ]]; then
    echo "$1" >> "$note"
else
    $EDITOR "$note"
fi