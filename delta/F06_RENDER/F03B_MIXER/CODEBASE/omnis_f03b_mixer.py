"""
omnis_f03b_mixer.py — F03B : Mixeur Audio V2 (Voix Off)
========================================================
Prend la video de F03A et lui greffe:
  1. La voix off (audio_clean.mp3 de F01A)
  2. Les SFX (whoosh, keyboard, etc.) du codex

Usage:
  python omnis_f03b_mixer.py --input /path/IN/ --output /path/OUT/ \
    --sfx-dir /path/to/sfx/ --voiceover /path/to/audio_clean.mp3

Entree: video_visuelle.mp4 + codex.json + sfx/ + audio_clean.mp3
Sortie: video_complete.mp4
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

INPUT_VIDEO = "video_visuelle.mp4"
INPUT_CODEX = "codex.json"
OUTPUT_VIDEO = "video_complete.mp4"

SHORT_SFX_TYPES = {"whoosh", "pop", "ding", "impact", "swish", "thump"}

def log_ok(msg): print(f"  [OK] {msg}")
def log_fail(msg): print(f"  [FAIL] {msg}")
def log_info(msg): print(f"  [...] {msg}")
def log_warn(msg): print(f"  [WARN] {msg}")

def section(title):
    bar = "─" * max(0, 50 - len(title))
    print(f"\n── {title} {bar}")

def probe_duration(path):
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])

def find_text_duration(sfx_frame, text_overlays, fps):
    if not text_overlays:
        return 0
    for text in text_overlays:
        text_start = text.get("start_frame", -1)
        text_end = text.get("end_frame", -1)
        if text_start == sfx_frame and text_end > text_start:
            return (text_end - text_start) / fps
    return 0

def create_sfx_mix(sfx_timeline, text_overlays, sfx_dir, fps, total_duration, output_path):
    if not sfx_timeline:
        log_info("Aucun SFX dans le codex")
        return False

    valid_sfx = []

    for sfx in sfx_timeline:
        sfx_type = sfx["type"]
        sfx_file = os.path.join(sfx_dir, f"{sfx_type}.mp3")

        if not os.path.exists(sfx_file):
            sfx_file = os.path.join(sfx_dir, f"{sfx_type}.wav")
            if not os.path.exists(sfx_file):
                log_warn(f"SFX introuvable: {sfx_type}")
                continue

        timestamp = sfx["frame"] / fps
        volume = sfx.get("volume", 0.8)
        text_duration = find_text_duration(sfx["frame"], text_overlays, fps)

        if sfx_type in SHORT_SFX_TYPES:
            sfx_duration = 0
            log_info(f"SFX: {sfx_type} @ {timestamp:.3f}s, vol={volume} [impact]")
        else:
            sfx_duration = text_duration if text_duration > 0 else 0
            if sfx_duration > 0:
                log_info(f"SFX: {sfx_type} @ {timestamp:.3f}s, vol={volume}, dur={sfx_duration:.2f}s [synchro texte]")
            else:
                log_info(f"SFX: {sfx_type} @ {timestamp:.3f}s, vol={volume} [libre]")

        valid_sfx.append({
            "file": sfx_file,
            "timestamp": timestamp,
            "volume": volume,
            "type": sfx_type,
            "duration": sfx_duration
        })

    if not valid_sfx:
        log_warn("Aucun SFX valide")
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        delayed_files = []

        for i, sfx in enumerate(valid_sfx):
            delayed_path = os.path.join(tmpdir, f"sfx_{i:02d}.mp3")
            delay_ms = int(sfx["timestamp"] * 1000)
            audio_filter = f"adelay={delay_ms}|{delay_ms},volume={sfx['volume']}"

            cmd = ["ffmpeg", "-y", "-i", sfx["file"], "-af", audio_filter]

            if sfx["duration"] > 0:
                total_sfx_duration = sfx["timestamp"] + sfx["duration"]
                cmd.extend(["-t", str(total_sfx_duration)])
            else:
                cmd.extend(["-t", str(total_duration)])

            cmd.append(delayed_path)

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                log_warn(f"Erreur delay SFX {i}")
                continue
            delayed_files.append(delayed_path)

        if not delayed_files:
            log_warn("Aucun SFX traité")
            return False

        if len(delayed_files) == 1:
            cmd = ["ffmpeg", "-y", "-i", delayed_files[0], "-t", str(total_duration), output_path]
        else:
            cmd = ["ffmpeg", "-y"]
            for f in delayed_files:
                cmd.extend(["-i", f])
            cmd.extend([
                "-filter_complex",
                f"amix=inputs={len(delayed_files)}:normalize=0",
                "-t", str(total_duration),
                output_path
            ])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log_fail(f"Erreur mix SFX: {result.stderr[-500:]}")
            return False

        log_ok(f"Mix SFX créé")
        return True

def main():
    parser = argparse.ArgumentParser(description="F03B MIXER V2 — Mixage voix off + SFX")
    parser.add_argument("--input", required=True, help="Dossier IN/")
    parser.add_argument("--output", required=True, help="Dossier OUT/")
    parser.add_argument("--sfx-dir", required=True, help="Dossier SFX")
    parser.add_argument("--voiceover", required=False, help="audio_clean.mp3 (voix off)")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    video_path = input_dir / INPUT_VIDEO
    codex_path = input_dir / INPUT_CODEX
    sfx_dir = Path(args.sfx_dir)
    voiceover_path = Path(args.voiceover) if args.voiceover else None

    section("Vérification des entrées")

    if not video_path.exists():
        log_fail(f"Video introuvable: {video_path}")
        sys.exit(1)
    log_ok(f"Video: {video_path}")

    if not codex_path.exists():
        log_fail(f"Codex introuvable: {codex_path}")
        sys.exit(1)

    with open(codex_path, "r", encoding="utf-8") as f:
        codex = json.load(f)

    sfx_timeline = codex.get("sfx_timeline", [])
    text_overlays = codex.get("text_overlays", [])
    log_ok(f"Codex: {len(sfx_timeline)} SFX, {len(text_overlays)} textes")

    if not sfx_dir.exists():
        log_fail(f"Dossier SFX introuvable: {sfx_dir}")
        sys.exit(1)
    log_ok(f"Dossier SFX: {sfx_dir}")

    if voiceover_path and voiceover_path.exists():
        log_ok(f"Voix off: {voiceover_path}")
    else:
        log_warn("Pas de voix off — SFX seulement")
        voiceover_path = None

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    total_duration = probe_duration(str(video_path))
    fps = codex["video"]["fps"]
    log_ok(f"Video: {total_duration:.2f}s, {fps}fps")

    # ── Création du mix SFX ──
    section("Création du mix SFX")

    with tempfile.TemporaryDirectory() as tmpdir:
        sfx_mix_path = os.path.join(tmpdir, "sfx_mix.mp3")

        has_sfx = create_sfx_mix(sfx_timeline, text_overlays, str(sfx_dir), fps, total_duration, sfx_mix_path)

        # ── Mixage final ──
        section("Mixage final")

        output_path = output_dir / OUTPUT_VIDEO

        if has_sfx and voiceover_path:
            # Cas V2: voix off + SFX
            # Input 0: video (muette), Input 1: voix off, Input 2: SFX mix
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-i", str(voiceover_path),
                "-i", sfx_mix_path,
                "-map", "0:v",
                "-filter_complex",
                f"[1:a]volume=1.0[voice];[2:a]volume=0.8[sfx];[voice][sfx]amix=inputs=2:normalize=0[aout]",
                "-map", "[aout]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                str(output_path)
            ]
        elif has_sfx and not voiceover_path:
            # Cas V1: SFX seulement
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-i", sfx_mix_path,
                "-map", "0:v",
                "-map", "1:a",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                str(output_path)
            ]
        elif voiceover_path and not has_sfx:
            # Voix off seulement, pas de SFX
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-i", str(voiceover_path),
                "-map", "0:v",
                "-map", "1:a",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                str(output_path)
            ]
        else:
            # Rien — copier la video
            cmd = ["ffmpeg", "-y", "-i", str(video_path), "-c", "copy", str(output_path)]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log_fail(f"Erreur mixage final: {result.stderr[-500:]}")
            sys.exit(1)

        log_ok(f"Video finale: {output_path}")

    # ── Vérification ──
    out_duration = probe_duration(str(output_path))
    out_size = os.path.getsize(output_path) / 1_000_000

    print()
    print("═" * 52)
    print(" F03B MIXER V2 — MISSION ACCOMPLIE")
    print(f" SFX       : {len(sfx_timeline)} dans le codex")
    print(f" Voix off  : {'oui' if voiceover_path else 'non'}")
    print(f" SFX mix   : {'oui' if has_sfx else 'aucun'}")
    print(f" Durée     : {out_duration:.2f}s")
    print(f" Taille    : {out_size:.1f} MB")
    print(f" Fichier   : {OUTPUT_VIDEO}")
    print("═" * 52)
    print()

if __name__ == "__main__":
    main()
