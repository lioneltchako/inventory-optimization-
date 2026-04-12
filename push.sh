#!/bin/bash
# Usage: ./push.sh "your commit message"
MSG=${1:-"demo update"}
git add -A
git commit -m "$MSG"
git push -u origin claude/inventory-simulator-demo-vdyFx
echo "✓ Pushed: $MSG"
