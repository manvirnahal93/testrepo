#!/usr/bin/env python3
"""Turn one still photo + a written script into a talking-head clinic video.

Pipeline:
  1. Text -> speech with edge-tts (free neural voices), or use your own recording.
  2. Photo + speech -> lip-synced talking head with SadTalker.
  3. ffmpeg -> final MP4 sized for YouTube / Reels / WhatsApp, with optional
     clinic logo and burned-in captions.

Run setup.sh (macOS/Linux) or setup.ps1 (Windows) once before using this.

Example:
  python make_video.py --photo doctor.jpg --script script.txt --logo logo.png \
      --format portrait --captions
"""
import argparse
import asyncio
import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SADTALKER_DIR = HERE / "tools" / "SadTalker"
SADTALKER_PY = (
    SADTALKER_DIR / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
)

SIZES = {
    "landscape": (1920, 1080),  # YouTube, website
    "portrait": (1080, 1920),   # Instagram Reels, Shorts, WhatsApp status
    "square": (1080, 1080),     # Facebook / Instagram feed
}


def run(cmd, **kwargs):
    print("+", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], check=True, **kwargs)


async def synthesize(text, voice, rate, mp3_path, srt_path):
    import edge_tts

    communicate = edge_tts.Communicate(text, voice, rate=rate)
    submaker = edge_tts.SubMaker()
    with open(mp3_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                submaker.feed(chunk)
    Path(srt_path).write_text(submaker.get_srt(), encoding="utf-8")


def make_audio(args, work):
    wav = work / "speech.wav"
    srt = None
    if args.audio:
        src = Path(args.audio)
    else:
        text = Path(args.script).read_text(encoding="utf-8").strip()
        if not text:
            sys.exit(f"Script file {args.script} is empty.")
        src = work / "speech.mp3"
        srt = work / "captions.srt"
        print(f"Generating voice ({args.voice})...")
        asyncio.run(synthesize(text, args.voice, args.rate, src, srt))
    # SadTalker expects 16 kHz mono WAV.
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ac", "1", "-ar", "16000", wav])
    return wav, srt


def animate(photo, wav, work, args):
    if not SADTALKER_PY.exists():
        sys.exit("SadTalker is not installed. Run setup.sh / setup.ps1 first.")
    out_dir = work / "sadtalker"
    cmd = [
        SADTALKER_PY, "inference.py",
        "--driven_audio", wav.resolve(),
        "--source_image", Path(photo).resolve(),
        "--result_dir", out_dir.resolve(),
        "--preprocess", "full",   # keep the whole photo, not just a face crop
        "--still",                # natural, limited head movement
        "--size", str(args.quality),
    ]
    if args.enhance:
        cmd += ["--enhancer", "gfpgan"]
    if args.cpu:
        cmd += ["--cpu"]
    run(cmd, cwd=SADTALKER_DIR)
    videos = sorted(glob.glob(str(out_dir / "**" / "*.mp4"), recursive=True), key=os.path.getmtime)
    if not videos:
        sys.exit("SadTalker finished but produced no video; check the log above.")
    return Path(videos[-1])


def finalize(talking, wav, srt, args):
    w, h = SIZES[args.format]
    # Fit the talking head into the frame and fill the rest with a blurred copy.
    filters = [
        f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=20[bg]",
        f"[0:v]scale={w}:{h}:force_original_aspect_ratio=decrease[fg]",
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[v0]",
    ]
    inputs = ["-i", talking.resolve(), "-i", wav.resolve()]
    last = "v0"
    if args.logo:
        inputs += ["-i", Path(args.logo).resolve()]
        logo_w = w // 5
        filters.append(f"[2:v]scale={logo_w}:-1[logo]")
        filters.append(f"[{last}][logo]overlay=W-w-40:40[v1]")
        last = "v1"
    if args.captions and srt:
        # Use a bare file name with cwd set to its folder: avoids path escaping
        # problems in the subtitles filter (especially on Windows).
        style = "FontName=Arial,FontSize=14,PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,BorderStyle=3,MarginV=40"
        filters.append(f"[{last}]subtitles={srt.name}:force_style='{style}'[v2]")
        last = "v2"
    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           *inputs,
           "-filter_complex", ";".join(filters),
           "-map", f"[{last}]", "-map", "1:a",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out]
    run(cmd, cwd=srt.parent if srt else None)
    return out


def main():
    # Dependencies live in SadTalker's venv; re-launch there if started elsewhere.
    if SADTALKER_PY.exists() and Path(sys.executable).resolve() != SADTALKER_PY.resolve():
        sys.exit(subprocess.call([str(SADTALKER_PY), __file__, *sys.argv[1:]]))

    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--photo", required=True, help="Front-facing photo of the presenter (JPG/PNG)")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--script", help="Text file with what the presenter should say")
    src.add_argument("--audio", help="Use your own voice recording (mp3/wav/m4a) instead of a generated voice")
    p.add_argument("--voice", default="en-US-JennyNeural",
                   help="edge-tts voice; list them with: edge-tts --list-voices")
    p.add_argument("--rate", default="-5%", help="Speaking speed, e.g. -10%%, +0%%, +10%%")
    p.add_argument("--format", choices=SIZES, default="landscape")
    p.add_argument("--logo", help="Clinic logo (PNG with transparency works best)")
    p.add_argument("--captions", action="store_true", help="Burn subtitles into the video (generated voice only)")
    p.add_argument("--quality", type=int, choices=[256, 512], default=256,
                   help="Face model resolution; 512 is sharper but slower")
    p.add_argument("--no-enhance", dest="enhance", action="store_false", help="Skip GFPGAN face enhancement (faster)")
    p.add_argument("--cpu", action="store_true", help="Force CPU (no NVIDIA GPU); slow but works")
    p.add_argument("--output", default="output/clinic_video.mp4")
    args = p.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found. Run setup.sh / setup.ps1 first.")

    work = HERE / "work"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir()

    wav, srt = make_audio(args, work)
    print("Animating photo (this can take several minutes on CPU)...")
    talking = animate(args.photo, wav, work, args)
    out = finalize(talking, wav, srt, args)
    print(f"\nDone: {out}")


if __name__ == "__main__":
    main()
