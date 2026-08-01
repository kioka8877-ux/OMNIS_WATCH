"""
omnis_d06_luther.py - D-F06 LUTHER
===================================
Adapte de F05 Luther (CRUSADER) pour la flotte delta (multi-clips).
Effacement complet de l'empreinte numerique : stream copy, strip metadonnees,
normalisation timestamp.

Usage:
  python omnis_d06_luther.py --input /path/IN/ --output /path/OUT/ [--date YYYY-MM-DD]

Entree: IN/clips_camoufles/ (issus de D-F05) + IN/camouflage_manifest.json
Sortie: OUT/clips_finaux/ + OUT/luther_manifest.json
"""

import argparse
import glob
import json
import os
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

INPUT_CLIPS_DIR = "clips_camoufles"
INPUT_MANIFEST = "camouflage_manifest.json"
OUTPUT_CLIPS_DIR = "clips_finaux"
OUTPUT_MANIFEST = "luther_manifest.json"

SUSPICIOUS_TAGS = ["remotion", "manim", "ffmpeg", "lavf", "lavc", "libav", "python", "claude"]


def log_ok(msg):   print(f"  [OK]   {msg}")
def log_fail(msg): print(f"  [FAIL] {msg}")
def log_info(msg): print(f"  [...]  {msg}")
def log_warn(msg): print(f"  [WARN] {msg}")

def section(title):
    bar = "-" * max(0, 50 - len(title))
    print(f"\n-- {title} {bar}")


def probe(path):
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json",
           "-show_format", "-show_streams", path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def extract_tags(probe_data):
    fmt_tags = probe_data.get("format", {}).get("tags", {})
    stream_tags = {}
    for s in probe_data.get("streams", []):
        stream_tags.update(s.get("tags", {}))
    all_tags = {}
    all_tags.update(stream_tags)
    all_tags.update(fmt_tags)
    return {k.lower(): v for k, v in all_tags.items()}


def has_suspicious_tags(tags):
    found = []
    for key, val in tags.items():
        combined = f"{key} {val}".lower()
        for s in SUSPICIOUS_TAGS:
            if s in combined:
                found.append(f"{key}={val!r}")
    return found


def strip(input_path, output_path):
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-c", "copy",
        "-map_metadata", "-1",
        "-fflags", "+bitexact",
        "-flags:v", "+bitexact",
        "-flags:a", "+bitexact",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log_fail(f"ffmpeg strip echoue: {result.stderr[-500:]}")
        return False
    return True


def normalize_timestamp(path, date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(hour=12, minute=0, second=0)
        ts = time.mktime(dt.timetuple())
        os.utime(path, (ts, ts))
        log_ok(f"Timestamp normalise -> {date_str}")
    except (ValueError, OSError) as e:
        log_warn(f"Timestamp ignore: {e}")


def main():
    parser = argparse.ArgumentParser(description="D-F06 LUTHER - Effacement empreinte")
    parser.add_argument("--input", required=True, help="Dossier IN/")
    parser.add_argument("--output", required=True, help="Dossier OUT/")
    parser.add_argument("--date", default=date.today().isoformat(), help="Date production YYYY-MM-DD")
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

    section(f"D-F06 LUTHER - {len(mp4_files)} clips a nettoyer")

    results = []
    for mp4 in mp4_files:
        name = Path(mp4).name
        section(f"Nettoyage: {name}")

        pre_data = probe(mp4)
        pre_tags = extract_tags(pre_data)
        suspicious_pre = has_suspicious_tags(pre_tags)
        if suspicious_pre:
            for s in suspicious_pre:
                log_warn(f"  Suspect: {s}")

        out_path = clips_out / name
        if not strip(mp4, str(out_path)):
            results.append({"file": name, "qa": "FAIL"})
            continue

        normalize_timestamp(str(out_path), args.date)

        post_data = probe(str(out_path))
        post_tags = extract_tags(post_data)
        suspicious_post = has_suspicious_tags(post_tags)

        size_mb = os.path.getsize(out_path) / 1_000_000
        qa = "PASS" if not suspicious_post else "FAIL"
        log_ok(f"{name} -> {size_mb:.1f} MB, QA={qa}")

        results.append({
            "file": name,
            "size_mb": round(size_mb, 1),
            "tags_stripped": len(pre_tags),
            "tags_residuels": len(post_tags),
            "suspicious_pre": suspicious_pre,
            "suspicious_post": suspicious_post,
            "qa": qa,
        })

    manifest = {
        "date": args.date,
        "clips_nettoyes": len(results),
        "qa_pass": sum(1 for r in results if r.get("qa") == "PASS"),
        "qa_fail": sum(1 for r in results if r.get("qa") == "FAIL"),
        "clips": results,
    }
    with open(output_dir / OUTPUT_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 52)
    print(" D-F06 LUTHER - MISSION ACCOMPLIE")
    print(f"  Nettoyes    : {len(results)}")
    print(f"  QA PASS     : {manifest['qa_pass']}")
    print(f"  QA FAIL     : {manifest['qa_fail']}")
    print(f"  Dossier     : {OUTPUT_CLIPS_DIR}/")
    print("=" * 52)


if __name__ == "__main__":
    main()
