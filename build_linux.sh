#!/usr/bin/env bash
set -euo pipefail

ENTRY="src/workproof/main.py"

python3 -m pip install --upgrade pip
pip3 install -r requirements.txt pyinstaller
pyinstaller \
  --noconfirm \
  --onefile \
  --name workproof \
  --icon assets/icon.png \
  --add-data "assets/templates:assets/templates" \
  "$ENTRY"

echo "Build complete. See dist/workproof"



