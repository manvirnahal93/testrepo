#!/usr/bin/env bash
# One-time install for macOS and Linux: ffmpeg, edge-tts, SadTalker + its models.
# Needs ~6 GB of disk. Re-running is safe; finished steps are skipped.
set -euo pipefail
cd "$(dirname "$0")"

# 1. System tools: ffmpeg, git, Python 3.10 (SadTalker does not support newer Pythons).
if [[ "$(uname)" == "Darwin" ]]; then
  command -v brew >/dev/null || { echo "Install Homebrew first: https://brew.sh"; exit 1; }
  brew install ffmpeg git python@3.10
  PY310="$(brew --prefix python@3.10)/bin/python3.10"
else
  if command -v apt-get >/dev/null; then
    sudo apt-get update
    sudo apt-get install -y ffmpeg git python3-pip software-properties-common
    if ! command -v python3.10 >/dev/null; then
      sudo add-apt-repository -y ppa:deadsnakes/ppa && sudo apt-get update
    fi
    sudo apt-get install -y python3.10 python3.10-venv
  fi
  PY310="$(command -v python3.10 || true)"
fi
[[ -x "$PY310" ]] || { echo "Python 3.10 not found; install it and re-run."; exit 1; }

# 2. SadTalker (photo -> talking head).
mkdir -p tools
if [[ ! -d tools/SadTalker ]]; then
  git clone --depth 1 https://github.com/OpenTalker/SadTalker.git tools/SadTalker
fi
cd tools/SadTalker
[[ -d venv ]] || "$PY310" -m venv venv
VPY=venv/bin/python
$VPY -m pip install --upgrade pip
if command -v nvidia-smi >/dev/null; then
  $VPY -m pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
else
  $VPY -m pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2
fi
$VPY -m pip install -r requirements.txt "edge-tts>=7"

# 3. Model weights (~2.5 GB).
fetch() { [[ -s "$2" ]] || { echo "Downloading $(basename "$2")"; curl -L --fail -o "$2" "$1"; }; }
mkdir -p checkpoints gfpgan/weights
R=https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc
for f in mapping_00109-model.pth.tar mapping_00229-model.pth.tar SadTalker_V0.0.2_256.safetensors SadTalker_V0.0.2_512.safetensors; do
  fetch "$R/$f" "checkpoints/$f"
done
fetch https://github.com/xinntao/facexlib/releases/download/v0.1.0/alignment_WFLW_4HG.pth gfpgan/weights/alignment_WFLW_4HG.pth
fetch https://github.com/xinntao/facexlib/releases/download/v0.1.0/detection_Resnet50_Final.pth gfpgan/weights/detection_Resnet50_Final.pth
fetch https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth gfpgan/weights/GFPGANv1.4.pth
fetch https://github.com/xinntao/facexlib/releases/download/v0.2.2/parsing_parsenet.pth gfpgan/weights/parsing_parsenet.pth

echo
echo "Setup complete. Try:"
echo "  python3 make_video.py --photo your_photo.jpg --script script.example.txt --captions"
