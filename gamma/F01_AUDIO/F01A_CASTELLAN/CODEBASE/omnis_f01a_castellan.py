"""
omnis_f01a_castellan.py — F01A : Nettoyage Audio
=================================================
Détecte et supprime les silences de l'audio brut via FFmpeg.
Version automatisée (pas de viewer interactif — tourne sur GitHub Actions).

Usage:
    python omnis_f01a_castellan.py --input /path/IN/ --output /path/OUT/

IN  : audio_raw.mp3
OUT : audio_clean.mp3 + silence_map.json

Adapté de CRUSADER crs_f01a.py — sans Flask, sans viewer.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# ── Constantes ────────────────────────────────────────────────────────────────

AUDIO_IN = "audio_raw.mp3"
AUDIO_OUT = "audio_clean.mp3"
SILENCE_MAP = "silence_map.json"

# ── Logging ───────────────────────────────────────────────────────────────────

def log_ok(msg): print(f"  [OK] {msg}")
def log_fail(msg): print(f"  [FAIL] {msg}")
def log_info(msg): print(f"  [...] {msg}")
def log_warn(msg): print(f"  [WARN] {msg}")

def section(title):
    bar = "─" * max(0, 50 - len(title))
    print(f"\n── {title} {bar}")

# ── FFmpeg helpers ────────────────────────────────────────────────────────────

def ffmpeg(*args):
    cmd = ["ffmpeg", "-y"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode

def get_duration(audio_path: str) -> float:
    _, stderr, _ = ffmpeg("-i", audio_path, "-f", "null", "-")
    for line in stderr.splitlines():
        if "Duration:" in line:
            try:
                ts = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = ts.split(":")
                return round(float(h) * 3600 + float(m) * 60 + float(s), 4)
            except Exception:
                pass
    return 0.0

def detect_silences(audio_path: str, threshold_db: float = -40.0, min_duration: float = 0.5) -> list:
    _, stderr, _ = ffmpeg(
        "-i", audio_path,
        "-af", f"silencedetect=noise={threshold_db}dB:d={min_duration}",
        "-f", "null", "-"
    )
    silences = []
    current_start = None
    for line in stderr.splitlines():
        if "silence_start" in line:
            try:
                current_start = float(line.split("silence_start:")[1].strip())
            except Exception:
                pass
        elif "silence_end" in line and current_start is not None:
            try:
                parts = line.split("silence_end:")[1].split("|")
                end = float(parts[0].strip())
                dur = float(parts[1].split(":")[1].strip()) if len(parts) > 1 else end - current_start
                silences.append({
                    "start": round(current_start, 4),
                    "end": round(end, 4),
                    "duration": round(dur, 4),
                })
                current_start = None
            except Exception:
                pass
    return silences

def remove_silences(input_path: str, output_path: str, threshold_db: float, min_duration: float):
    _, stderr, rc = ffmpeg(
        "-i", input_path,
        "-af", (
            f"silenceremove=stop_periods=-1"
            f":stop_duration={min_duration}"
            f":stop_threshold={threshold_db}dB"
        ),
        "-c:a", "libmp3lame", "-q:a", "2",
        output_path
    )
    if rc != 0:
        raise RuntimeError(f"FFmpeg silenceremove échoué :\n{stderr[-800:]}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="F01A CASTELLAN — Nettoyage audio automatique")
    parser.add_argument("--input", required=True, help="Dossier IN/")
    parser.add_argument("--output", required=True, help="Dossier OUT/")
    parser.add_argument("--threshold-db", type=float, default=-40.0, help="Seuil de silence (dB)")
    parser.add_argument("--min-duration", type=float, default=0.5, help="Durée min de silence (s)")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    audio_in = input_dir / AUDIO_IN
    audio_out = output_dir / AUDIO_OUT
    silence_map_path = output_dir / SILENCE_MAP

    # ── Vérifications ──
    section("Vérification des entrées")

    if not audio_in.exists():
        log_fail(f"Audio introuvable: {audio_in}")
        sys.exit(1)
    log_ok(f"Audio: {audio_in}")

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    # ── Durée originale ──
    original_duration = get_duration(str(audio_in))
    log_ok(f"Durée originale: {original_duration:.2f}s")

    # ── Détection des silences ──
    section("Détection des silences")
    silences = detect_silences(str(audio_in), args.threshold_db, args.min_duration)
    silence_total = sum(s["duration"] for s in silences)
    log_info(f"Silences détectés: {len(silences)} ({silence_total:.2f}s total)")

    # ── Suppression des silences ──
    section("Suppression des silences")
    remove_silences(str(audio_in), str(audio_out), args.threshold_db, args.min_duration)

    if not audio_out.exists():
        log_fail("audio_clean.mp3 non produit")
        sys.exit(1)

    clean_duration = get_duration(str(audio_out))
    log_ok(f"Audio clean: {clean_duration:.2f}s (était {original_duration:.2f}s)")

    # ── Sauvegarde silence_map.json ──
    silence_data = {
        "original_duration": original_duration,
        "clean_duration": clean_duration,
        "silence_count": len(silences),
        "silence_total_seconds": round(silence_total, 4),
        "threshold_db": args.threshold_db,
        "min_duration": args.min_duration,
        "silences": silences,
    }
    with open(silence_map_path, "w", encoding="utf-8") as f:
        json.dump(silence_data, f, ensure_ascii=False, indent=2)
    log_ok(f"silence_map.json sauvegardé")

    # ── Résumé ──
    print()
    print("═" * 52)
    print(" F01A CASTELLAN — MISSION ACCOMPLIE")
    print(f" Durée originale : {original_duration:.2f}s")
    print(f" Durée clean     : {clean_duration:.2f}s")
    print(f" Silences        : {len(silences)} ({silence_total:.2f}s supprimés)")
    print(f" Fichier         : {AUDIO_OUT}")
    print("═" * 52)
    print()

if __name__ == "__main__":
    main()
