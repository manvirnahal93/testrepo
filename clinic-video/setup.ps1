# One-time install for Windows 10/11: ffmpeg, edge-tts, SadTalker + its models.
# Run in PowerShell:  powershell -ExecutionPolicy Bypass -File setup.ps1
# Needs ~6 GB of disk. Re-running is safe; finished steps are skipped.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# 1. System tools via winget (built into Windows 10/11).
winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements
winget install --id Python.Python.3.10 -e --accept-source-agreements --accept-package-agreements
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")

# 2. SadTalker (photo -> talking head).
New-Item -ItemType Directory -Force tools | Out-Null
if (-not (Test-Path tools\SadTalker)) {
  git clone --depth 1 https://github.com/OpenTalker/SadTalker.git tools\SadTalker
}
Set-Location tools\SadTalker
if (-not (Test-Path venv)) { py -3.10 -m venv venv }
$vpy = ".\venv\Scripts\python.exe"
& $vpy -m pip install --upgrade pip
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
  & $vpy -m pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
} else {
  & $vpy -m pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2
}
& $vpy -m pip install -r requirements.txt "edge-tts>=7"

# 3. Model weights (~2.5 GB).
function Fetch($url, $dest) {
  if (-not (Test-Path $dest) -or (Get-Item $dest).Length -eq 0) {
    Write-Host "Downloading $(Split-Path $dest -Leaf)"
    curl.exe -L --fail -o $dest $url
  }
}
New-Item -ItemType Directory -Force checkpoints, gfpgan\weights | Out-Null
$R = "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc"
foreach ($f in "mapping_00109-model.pth.tar", "mapping_00229-model.pth.tar", "SadTalker_V0.0.2_256.safetensors", "SadTalker_V0.0.2_512.safetensors") {
  Fetch "$R/$f" "checkpoints\$f"
}
Fetch "https://github.com/xinntao/facexlib/releases/download/v0.1.0/alignment_WFLW_4HG.pth" "gfpgan\weights\alignment_WFLW_4HG.pth"
Fetch "https://github.com/xinntao/facexlib/releases/download/v0.1.0/detection_Resnet50_Final.pth" "gfpgan\weights\detection_Resnet50_Final.pth"
Fetch "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth" "gfpgan\weights\GFPGANv1.4.pth"
Fetch "https://github.com/xinntao/facexlib/releases/download/v0.2.2/parsing_parsenet.pth" "gfpgan\weights\parsing_parsenet.pth"

Write-Host ""
Write-Host "Setup complete. Try:"
Write-Host "  python make_video.py --photo your_photo.jpg --script script.example.txt --captions"
