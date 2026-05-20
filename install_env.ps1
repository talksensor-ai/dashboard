$ErrorActionPreference = 'Stop'

Write-Host "1. Downloading Python 3.12 installer..."
$url = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"
$installer = "e:\talk\python-3.12.8.exe"
Invoke-WebRequest -Uri $url -OutFile $installer

Write-Host "2. Silent installing Python 3.12 for Current User..."
Start-Process -FilePath $installer -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1 Include_test=0" -Wait

Write-Host "3. Verifying installation..."
$py312 = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
if (-Not (Test-Path $py312)) {
    Write-Error "Python 3.12 not found. Installation failed."
    exit 1
}

Write-Host "4. Creating venv .venv312..."
& $py312 -m venv e:\talk\.venv312

$venvPy = "e:\talk\.venv312\Scripts\python.exe"
$venvPip = "e:\talk\.venv312\Scripts\pip.exe"

Write-Host "5. Upgrading pip..."
& $venvPy -m pip install --upgrade pip

Write-Host "6. Installing PyTorch CUDA 12.1..."
& $venvPip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

Write-Host "7. Installing ML packages..."
& $venvPip install transformers accelerate bitsandbytes soundfile python-dotenv yadisk

Write-Host "8. Cleanup..."
Remove-Item $installer -Force

Write-Host "INFRASTRUCTURE COMPLETELY UPDATED AND READY!"
