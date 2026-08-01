#!/usr/bin/env python3
"""
extract_timing.py — D-F04 TIMING
================================
Extrait le timing.json pour chaque clip depuis le transcript.json.

Usage:
  python extract_timing.py --input ../IN/ --output ../OUT/

Entrée:
  - IN/transcript.json (timestamps globaux de D-F01)
  - IN/cutlist.json (bornes des clips de D-F02)

Sortie:
  - OUT/timing_001.json
  - OUT/timing_002.json
  - OUT/timing_manifest.json
"""

import argparse
import json
from pathlib import Path

INPUT_TRANSCRIPT = "transcript.json"
INPUT_CUTLIST = "cutlist.json"
OUTPUT_MANIFEST = "timing_manifest.json"


def log_ok(msg): print(f"  [OK] {msg}")
def log_fail(msg): print(f"  [FAIL] {msg}")
def log_info(msg): print(f"  [...] {msg}")

def section(title):
    bar = "-" * max(0, 50 - len(title))
    print(f"\n-- {title} {bar}")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def extract_timing_for_clip(clip, words, clip_index):
    """Extrait les mots d'un clip et convertit en timestamps relatifs."""
    start_sec = clip["start_sec"]
    end_sec = clip["end_sec"]

    # Filtrer les mots dans la plage du clip
    clip_words = []
    for word in words:
        word_start = word["start"]
        word_end = word["end"]

        # Le mot doit être dans la plage (au moins partiellement)
        if word_end > start_sec and word_start < end_sec:
            # Convertir en timestamps relatifs au clip
            clip_words.append({
                "word": word["word"],
                "start": round(word_start - start_sec, 3),
                "end": round(word_end - start_sec, 3),
                "is_strong": word.get("is_strong", False)
            })

    return {
        "clip_index": clip_index,
        "source_start_sec": start_sec,
        "source_end_sec": end_sec,
        "word_count": len(clip_words),
        "words": clip_words
    }


def main():
    parser = argparse.ArgumentParser(description="D-F04 TIMING: Extract timing.json per clip")
    parser.add_argument("--input", required=True, help="Dossier IN/ (transcript.json + cutlist.json)")
    parser.add_argument("--output", required=True, help="Dossier OUT/ (timing_*.json)")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    section("D-F04 TIMING")

    # Charger transcript.json
    transcript_path = input_dir / INPUT_TRANSCRIPT
    if not transcript_path.exists():
        log_fail(f"transcript.json non trouvé: {transcript_path}")
        return 1

    transcript = load_json(transcript_path)
    words = transcript.get("words", [])
    log_ok(f"Transcript chargé: {len(words)} mots")

    # Charger cutlist.json
    cutlist_path = input_dir / INPUT_CUTLIST
    if not cutlist_path.exists():
        log_fail(f"cutlist.json non trouvé: {cutlist_path}")
        return 1

    cutlist = load_json(cutlist_path)
    clips = cutlist.get("clips", [])
    log_ok(f"Cutlist chargée: {len(clips)} clips")

    # Extraire timing pour chaque clip
    section("Extraction")
    manifest = {"clips": []}

    for i, clip in enumerate(clips, start=1):
        clip_index = clip.get("index", i)
        start_sec = clip.get("start_sec", 0)
        end_sec = clip.get("end_sec", 0)
        duration = end_sec - start_sec

        timing = extract_timing_for_clip(clip, words, clip_index)
        timing_filename = f"timing_{clip_index:03d}.json"
        timing_path = output_dir / timing_filename

        save_json(timing_path, timing)
        log_ok(f"Clip {clip_index}: {timing['word_count']} mots, {duration:.1f}s → {timing_filename}")

        manifest["clips"].append({
            "index": clip_index,
            "filename": timing_filename,
            "word_count": timing["word_count"],
            "duration_sec": round(duration, 3)
        })

    # Sauvegarder manifest
    manifest_path = output_dir / OUTPUT_MANIFEST
    save_json(manifest_path, manifest)
    log_ok(f"Manifest: {manifest_path}")

    section("D-F04 TIMING - MISSION ACCOMPLIE")
    print(f"  Clips traités: {len(clips)}")
    print(f"  Fichiers: {OUTPUT_MANIFEST} + timing_*.json")
    print(f"  Output: {output_dir}")

    return 0


if __name__ == "__main__":
    exit(main())
