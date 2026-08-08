#!/usr/bin/env bash
set -euo pipefail
python3 -m pip install -e '.[dev]'
python3 -m PyInstaller --noconfirm --clean --windowed --name 'Zip Part Maker' \
  --icon assets/app-icon.icns --add-data 'assets/app-icon.png:assets' main.py

staging_dir="$(mktemp -d)"
trap 'rm -rf "$staging_dir"' EXIT
cp -R 'dist/Zip Part Maker.app' "$staging_dir/"
ln -s /Applications "$staging_dir/Applications"
rm -f 'dist/ZipPartMaker.dmg'
hdiutil create \
  -volname 'Zip Part Maker' \
  -srcfolder "$staging_dir" \
  -ov \
  -format UDZO \
  'dist/ZipPartMaker.dmg'

echo 'Built dist/Zip Part Maker.app and dist/ZipPartMaker.dmg'
