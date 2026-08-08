#!/usr/bin/env bash
set -euo pipefail
python3 -m pip install -e '.[dev]'
python3 -m PyInstaller --noconfirm --clean --onefile --name ZipPartMaker \
  --icon assets/app-icon.png --add-data 'assets/app-icon.png:assets' main.py
echo 'Built dist/ZipPartMaker'
