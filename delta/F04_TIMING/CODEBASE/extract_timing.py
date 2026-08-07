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


EMOTION_KEYWORDS = {
    "surprise": ["impossible", "incroyable", "quoi", "comment", "bluff", "jamais", "100", "toutes", "exactement", "sans"],
    "wholesome": ["amour", "vie", "merci", "heureux", "maman", "papa", "enfant", "coeur", "doux", "gentil"],
    "tension": ["danger", "erreur", "faux", "risque", "jamais", "pire", "humain", "machine", "limite"],
    "comedy": ["rire", "rigolo", "drôle", "blague", "lol", "ha", "oups"],
    "motivation": ["toujours", "jamais", "vaincre", "réussir", "force", "croire", "possible"],
    "default": []
}

PUNCTUATION_STRONG = "?!"


def build_strong_windows(clip, start_sec):
    """Construit les fenêtres temporelles (sec absolues) où les mots sont forts."""
    windows = []
    structure = clip.get("structure", {})

    for key in ("verbal_text_hook", "payoff", "loop_hook", "foreshadow"):
        moment = structure.get(key)
        if not moment:
            continue
        w_start = moment.get("relative_start_sec")
        w_end = moment.get("relative_end_sec")
        if w_start is None or w_end is None:
            continue
        windows.append((start_sec + w_start, start_sec + w_end))

    return windows


def is_word_in_windows(word_start, word_end, windows):
    for w_start, w_end in windows:
        if word_end > w_start and word_start < w_end:
            return True
    return False


def extract_timing_for_clip(clip, words, clip_index):
    """Extrait les mots d'un clip et convertit en timestamps relatifs."""
    start_sec = clip["start_sec"]
    end_sec = clip["end_sec"]

    emotion_mode = clip.get("emotion_mode", "default")
    keywords = EMOTION_KEYWORDS.get(emotion_mode, EMOTION_KEYWORDS["default"])
    strong_windows = build_strong_windows(clip, start_sec)

    # Filtrer les mots dans la plage du clip
    clip_words = []
    for word in words:
        word_start = word["start"]
        word_end = word["end"]

        # Le mot doit être dans la plage (au moins partiellement)
        if word_end > start_sec and word_start < end_sec:
            raw_word = (word.get("word") or "").strip()
            lowered = raw_word.lower().strip(".,;:…\"'")

            # Mot fort si: déjà marqué, dans une fenêtre clé, mot-clé émotion, ou ponctuation forte
            is_strong = word.get("is_strong", False)
            if not is_strong:
                if is_word_in_windows(word_start, word_end, strong_windows):
                    is_strong = True
                elif lowered in keywords:
                    is_strong = True
                elif raw_word and raw_word[-1] in PUNCTUATION_STRONG:
                    is_strong = True

            # Convertir en timestamps relatifs au clip
            clip_words.append({
                "word": word["word"],
                "start": round(word_start - start_sec, 3),
                "end": round(word_end - start_sec, 3),
                "is_strong": is_strong
            })

    return {
        "clip_index": clip_index,
        "source_start_sec": start_sec,
        "source_end_sec": end_sec,
        "word_count": len(clip_words),
        "strong_word_count": sum(1 for w in clip_words if w["is_strong"]),
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
