$ErrorActionPreference = 'Stop'

Write-Host "=== Discord Voice Proxy Manager Build ==="

# Create virtual environment
if (Test-Path "venv") {
    Write-Host "Using existing virtual environment..."
} else {
    Write-Host "Creating virtual environment..."
    python -m venv venv
}

$Python = ".\venv\Scripts\python.exe"

# Upgrade pip
Write-Host "Updating pip..."
& $Python -m pip install --upgrade pip

# Install dependencies
Write-Host "Installing dependencies..."
& $Python -m pip install -r requirements.txt
& $Python -m pip install --upgrade pyinstaller

# Clean previous build
if (Test-Path "build") {
    Remove-Item "build" -Recurse -Force
}

if (Test-Path "dist") {
    Remove-Item "dist" -Recurse -Force
}

# Build single EXE
Write-Host "Building single executable..."

& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name "DiscordVoiceProxyManager" `
    --icon "assets\icon.ico" `
    --add-data "assets;assets" `
    "app\main.py"

if (-not (Test-Path "dist\DiscordVoiceProxyManager.exe")) {
    throw "Build failed: executable was not created."
}

Write-Host ""
Write-Host "============================================"
Write-Host "Build complete!"
Write-Host "Output:"
Write-Host "dist\DiscordVoiceProxyManager.exe"
Write-Host "============================================"
