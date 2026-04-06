#!/bin/bash

datetime_iso=$(date +'%Y-%m-%dT%H:%M:%S')
datetime_slug=$(date +'%Y-%m-%d_%H-%M-%S')
note="./content/notes/${datetime_slug}.md"

cat > "$note" << EOF
---
date: "$datetime_iso"
---

EOF

if [[ -n "$1" ]]; then
    echo "$1" >> "$note"
else
    $EDITOR "$note"
fi