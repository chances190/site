#!/bin/bash

# Get title from argument or ask interactively
if [[ -z "$1" ]]; then
    read -p "Title: " title
    if [[ -z "$title" ]]; then
        echo "Title required"
        exit 1
    fi
else
    title="$1"
fi

slug=$(echo "$title" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-+/-/g' | sed 's/^-\|-$//')
blog="./content/blog/${slug}.md"

datetime_iso=$(date +'%Y-%m-%dT%H:%M:%S')
cat > "$blog" << EOF
---
title: "$title"
date: "$datetime_iso"
---

EOF

$VISUAL "$blog"