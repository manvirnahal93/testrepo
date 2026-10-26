# Clinic talking-photo video maker

Turn **one still photo** of a person (for example, your doctor or receptionist) into a
video where they **speak and explain your clinic**, with lip-sync, voice, logo and captions.

```
photo.jpg + script.txt ──► voice (edge-tts) ──► talking head (SadTalker) ──► final MP4 (ffmpeg)
```

All tools are free and open source and run on your own computer.

| Tool | What it does |
|------|--------------|
| [ffmpeg](https://ffmpeg.org) | Video/audio processing, logo and captions |
| [edge-tts](https://github.com/rany2/edge-tts) | Natural AI voices in 70+ languages (needs internet) |
| [SadTalker](https://github.com/OpenTalker/SadTalker) | Animates the photo's face and lips to match the voice |
| GFPGAN | Sharpens the animated face |

## 1. Install (one time, about 6 GB)

**Windows 10/11:** right-click `setup.ps1` and choose *Run with PowerShell*, or run:
```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
```

**macOS / Linux:**
```bash
./setup.sh
```

An NVIDIA graphics card makes this much faster (about 1 minute per 30 s of video).
Without one it still works on CPU; expect 10–30 minutes. Add `--cpu` in that case.

## 2. Make a video

1. Put the person's photo in this folder, e.g. `doctor.jpg`.
2. Copy `script.example.txt` to `script.txt` and write what they should say.
3. Run:

```bash
python make_video.py --photo doctor.jpg --script script.txt --logo logo.png --captions
```

The video is saved to `output/clinic_video.mp4`.

### Useful options

| Option | Example | Meaning |
|--------|---------|---------|
| `--format` | `portrait` | `landscape` (YouTube/website), `portrait` (Reels/Shorts/WhatsApp), `square` |
| `--voice` | `en-IN-NeerjaNeural` | Pick a voice. List all: `edge-tts --list-voices` |
| `--rate` | `-10%` | Speak slower or faster |
| `--audio` | `my_voice.m4a` | Use a real recording instead of an AI voice |
| `--quality` | `512` | Sharper face (slower) |
| `--no-enhance` | | Skip face sharpening (faster) |
| `--cpu` | | No NVIDIA GPU |
| `--output` | `output/reel.mp4` | Where to save |

Some voices: `en-US-JennyNeural`, `en-US-GuyNeural`, `en-GB-SoniaNeural`,
`en-IN-NeerjaNeural`, `en-IN-PrabhatNeural`, `hi-IN-SwaraNeural`, `hi-IN-MadhurNeural`,
`es-ES-ElviraNeural`, `ar-AE-FatimaNeural`.

## Tips for a good result

- **Photo:** face looking at the camera, mouth closed, good light, no sunglasses or
  hands near the face, at least 512 px across the face. A plain background looks best.
- **Script:** short sentences; 30–60 seconds (≈ 80–150 words) works best for social media.
- **Consent:** get written permission from the person in the photo, and state that the
  video is AI-generated where your platform or local rules require it.
- **Health claims:** avoid promising cures or outcomes; local advertising rules for
  clinics usually apply.

## No-install alternative (paid apps)

If you would rather not install anything, these websites/apps do the same thing from a
photo and a script, with a free trial: **HeyGen** (heygen.com), **D-ID** (d-id.com),
**Hedra** (hedra.com), and **CapCut** (desktop/mobile) for editing and adding music.
