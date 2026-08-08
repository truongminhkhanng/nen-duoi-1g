$ErrorActionPreference = "Stop"
python -m pip install -e ".[dev]"
python -m PyInstaller --noconfirm --clean --windowed --onefile --name ZipPartMaker `
  --icon assets/app-icon.ico --add-data "assets/app-icon.png;assets" main.py
Write-Host "Built dist/ZipPartMaker.exe"
