$ErrorActionPreference = "Stop"
python -m pip install -e ".[dev]"
python -m PyInstaller --noconfirm --clean --windowed --onefile --name ZipPartMaker main.py
Write-Host "Built dist/ZipPartMaker.exe"
