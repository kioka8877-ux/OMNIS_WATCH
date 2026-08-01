"""
omnis_d05_camouflage.py - D-F05 CAMOUFLAGE
===========================================
Adapte de F04 Camouflage (CRUSADER) pour la flotte delta (multi-clips).
Re-encode chaque clip final en H264 CRF18 + AAC 192k + loudnorm -14 LUFS + wipe metadonnees.

Usage:
  python omnis_d05_camouflage.py --input /path/IN/ --output /path/OUT/

Entree: IN/clips_finaux/ (issus de D-F04) + IN/assembly_manifest.json
Sortie: OUT/clips_camoufles/ + OUT/camouflage_manifest.json
"""

import argparse
import glob
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

INPUT_CLIPS_DIR = "clips_finaux"
INPUT_MANIFEST = "assembly_manifest.json"
OUTPUT_CLIPS_DIR = "clips_camoufles"
OUTPUT_MANIFEST = "camouflage_manifest.json"

SUSPICIOUS = ["remotion", "manim", "ffmpeg", "lavf", "lavc", "libav",
              "python", "claude", "encoder"]


def log_ok(msg): print(f"  [OK] {msg}")
def log_fail(msg): print(f"  [FAIL] {msg}")
def log_info(msg): print(f"  [...] {msg}")
def log_warn(msg): print(f"  [WARN] {msg}")

def section(title):
    bar = "-" * max(0, 50 - len(title))
    print(f"\n-- {title} {bar}")


def probe_video(path):
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json",
           "-show_format", "-show_streams", str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {}
    data = json.loads(result.stdout)
    video_stream = next((s for s in data.get("streams", []) if s["codec_type"] == "video"), None)
    audio_stream = next((s for s in data.get("streams", []) if s["codec_type"] == "audio"), None)
    info = {"size_mb": os.path.getsize(path) / 1_000_000}
    if video_stream:
        info["video_codec"] = video_stream.get("codec_name", "?")
        info["width"] = int(video_stream.get("width", 0))
        info["height"] = int(video_stream.get("height", 0))
        info["fps"] = eval(video_stream.get("r_frame_rate", "30/1"))
        info["duration"] = float(video_stream.get("duration", 0))
    if audio_stream:
        info["audio_codec"] = audio_stream.get("codec_name", "?")
    info["tags"] = data.get("format", {}).get("tags", {})
    return info


def check_suspicious_tags(tags):
    found = []
    for key, value in tags.items():
        val = str(value).lower()
        for sus in SUSPICIOUS:
            if sus in val or sus in key.lower():
                found.append(f"{key}={value}")
    return found


def run_camouflage(input_path, output_path):
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
        "-map_metadata", "-1",
        "-metadata", "encoder=",
        "-movflags", "+faststart",
        str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log_fail(f"FFmpeg camouflage echoue: {result.stderr[-500:]}")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="D-F05 CAMOUFLAGE - Nettoyage + Loudnorm")
    parser.add_argument("--input", required=True, help="Dossier IN/")
    parser.add_argument("--output", required=True, help="Dossier OUT/")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    clips_in = input_dir / INPUT_CLIPS_DIR
    clips_out = output_dir / OUTPUT_CLIPS_DIR
    clips_out.mkdir(parents=True, exist_ok=True)

    if not clips_in.exists():
        log_fail(f"Dossier clips introuvable: {clips_in}")
        sys.exit(1)

    mp4_files = sorted(glob.glob(str(clips_in / "*.mp4")))
    if not mp4_files:
        log_fail(f"Aucun .mp4 dans {clips_in}")
        sys.exit(1)

    section(f"D-F05 CAMOUFLAGE - {len(mp4_files)} clips a traiter")

    results = []
    for mp4 in mp4_files:
        name = Path(mp4).name
        section(f"Traitement: {name}")

        info_pre = probe_video(mp4)
        suspicious_pre = check_suspicious_tags(info_pre.get("tags", {}))
        log_info(f"Source: {info_pre.get('width', '?')}x{info_pre.get('height', '?')}, "
                 f"{info_pre.get('size_mb', 0):.1f} MB")
        if suspicious_pre:
            log_warn(f"Tags suspects: {suspicious_pre}")

        out_path = clips_out / name
        if run_camouflage(mp4, str(out_path)):
            info_post = probe_video(str(out_path))
            suspicious_post = check_suspicious_tags(info_post.get("tags", {}))
            size_mb = info_post.get("size_mb", 0)
            log_ok(f"Camoufle: {name} ({size_mb:.1f} MB)")
            qa = "PASS" if not suspicious_post else "FAIL"
            results.append({
                "file": name,
                "size_mb_pre": round(info_pre.get("size_mb", 0), 1),
                "size_mb_post": round(size_mb, 1),
                "tags_suspects_pre": suspicious_pre,
                "tags_suspects_post": suspicious_post,
                "qa": qa,
            })
        else:
            results.append({"file": name, "qa": "FAIL"})

    manifest = {
        "clips_camoufles": len(results),
        "qa_pass": sum(1 for r in results if r.get("qa") == "PASS"),
        "qa_fail": sum(1 for r in results if r.get("qa") == "FAIL"),
        "clips": results,
    }
    with open(output_dir / OUTPUT_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 52)
    print(" D-F05 CAMOUFLAGE - MISSION ACCOMPLIE")
    print(f"  Traites     : {len(results)}")
    print(f"  QA PASS     : {manifest['qa_pass']}")
    print(f"  QA FAIL     : {manifest['qa_fail']}")
    print(f"  Dossier     : {OUTPUT_CLIPS_DIR}/")
    print("=" * 52)


if __name__ == "__main__":
    main()
