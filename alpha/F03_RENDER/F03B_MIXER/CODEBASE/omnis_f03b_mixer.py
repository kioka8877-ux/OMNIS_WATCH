"""
omnis_f03b_mixer.py — F03B : Mixeur Audio
==========================================
Prend la video muette de F03A et lui greffe les SFX aux bonnes frames.

Usage:
  python omnis_f03b_mixer.py --input /path/IN/ --output /path/OUT/ \
    --sfx-dir /path/to/sfx/

Entree: video_visuelle.mp4 + codex.json (sfx_timeline) + sfx/
Sortie: video_complete.mp4

Le script:
  1. Lit le codex.json (section sfx_timeline)
  2. Pour chaque SFX, calcule le timestamp (frame / fps)
  3. Cree un fichier audio mix avec tous les SFX aux bons timestamps
  4. FFmpeg mixe le SFX audio sur la video
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# ── Constantes ──────────────────────────────────────────────────────────────

INPUT_VIDEO = "video_visuelle.mp4"
INPUT_CODEX = "codex.json"
OUTPUT_VIDEO = "video_complete.mp4"

# ── Logging ─────────────────────────────────────────────────────────────────

def log_ok(msg): print(f"  [OK] {msg}")
def log_fail(msg): print(f"  [FAIL] {msg}")
def log_info(msg): print(f"  [...] {msg}")
def log_warn(msg): print(f"  [WARN] {msg}")

def section(title):
    bar = "─" * max(0, 50 - len(title))
    print(f"\n── {title} {bar}")

# ── Helpers ────────────────────────────────────────────────────────────────

def probe_duration(path):
    """Retourne la duree de la video en secondes."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", str(path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])

# ── Mixage SFX ──────────────────────────────────────────────────────────────

def create_sfx_mix(sfx_timeline, sfx_dir, fps, total_duration, output_path):
    """
    Cree un fichier audio contenant tous les SFX mixes aux bons timestamps.
    Utilise FFmpeg amix pour combiner les pistes.
    """
    if not sfx_timeline:
        log_info("Aucun SFX dans le codex — copie de la video sans modification")
        return False

    # Verifier que tous les fichiers SFX existent
    sfx_inputs = []
    sfx_delays = []
    valid_sfx = []

    for sfx in sfx_timeline:
        sfx_type = sfx["type"]
        sfx_file = os.path.join(sfx_dir, f"{sfx_type}.mp3")

        if not os.path.exists(sfx_file):
            # Essayer .wav
            sfx_file = os.path.join(sfx_dir, f"{sfx_type}.wav")
            if not os.path.exists(sfx_file):
                log_warn(f"SFX introuvable: {sfx_type} (cherche dans {sfx_dir})")
                continue

        # Calculer le timestamp en secondes
        timestamp = sfx["frame"] / fps
        volume = sfx.get("volume", 0.8)

        valid_sfx.append({
            "file": sfx_file,
            "timestamp": timestamp,
            "volume": volume,
            "type": sfx_type
        })
        log_info(f"SFX: {sfx_type} a {timestamp:.3f}s (frame {sfx['frame']}), volume={volume}")

    if not valid_sfx:
        log_warn("Aucun SFX valide trouve — video sans son ajoute")
        return False

    # Construire la commande FFmpeg
    # Strategie: pour chaque SFX, on crée une entrée avec un delay
    # puis on mixe tout avec amix

    with tempfile.TemporaryDirectory() as tmpdir:
        # Etape 1: Pour chaque SFX, creer un fichier audio avec le bon delay et volume
        delayed_files = []

        for i, sfx in enumerate(valid_sfx):
            delayed_path = os.path.join(tmpdir, f"sfx_{i:02d}.mp3")

            # FFmpeg: ajouter du silence au debut (delay) + ajuster le volume
            delay_ms = int(sfx["timestamp"] * 1000)

            cmd = [
                "ffmpeg", "-y",
                "-i", sfx["file"],
                "-af", f"adelay={delay_ms}|{delay_ms},volume={sfx['volume']}",
                "-t", str(total_duration),
                delayed_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                log_warn(f"Erreur delay SFX {i}: {result.stderr[-200:]}")
                continue

            delayed_files.append(delayed_path)

        if not delayed_files:
            log_warn("Aucun SFX traite avec succes")
            return False

        # Etape 2: Mixer tous les SFX ensemble
        if len(delayed_files) == 1:
            # Un seul SFX — pas besoin de amix
            cmd = [
                "ffmpeg", "-y",
                "-i", delayed_files[0],
                "-t", str(total_duration),
                output_path
            ]
        else:
            # Multiple SFX — utiliser amix
            cmd = ["ffmpeg", "-y"]
            for f in delayed_files:
                cmd.extend(["-i", f])

            # amix avec normalize=0 pour ne pas reduire le volume
            inputs_count = len(delayed_files)
            cmd.extend([
                "-filter_complex",
                f"amix=inputs={inputs_count}:normalize=0",
                "-t", str(total_duration),
                output_path
            ])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log_fail(f"Erreur mix SFX: {result.stderr[-500:]}")
            return False

        log_ok(f"Mix SFX cree: {output_path}")
        return True

# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="F03B MIXER — Mixage SFX sur video"
    )
    parser.add_argument("--input", required=True, help="Dossier IN/")
    parser.add_argument("--output", required=True, help="Dossier OUT/")
    parser.add_argument("--sfx-dir", required=True,
                        help="Dossier contenant les fichiers SFX")

    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    video_path = input_dir / INPUT_VIDEO
    codex_path = input_dir / INPUT_CODEX
    sfx_dir = Path(args.sfx_dir)

    # ── Verifications ──
    section("Verification des entrees")

    if not video_path.exists():
        log_fail(f"Video introuvable: {video_path}")
        sys.exit(1)
    log_ok(f"Video: {video_path}")

    if not codex_path.exists():
        log_fail(f"Codex introuvable: {codex_path}")
        sys.exit(1)

    with open(codex_path, "r", encoding="utf-8") as f:
        codex = json.load(f)
    log_ok(f"Codex lu: {len(codex.get('sfx_timeline', []))} SFX")

    if not sfx_dir.exists():
        log_fail(f"Dossier SFX introuvable: {sfx_dir}")
        sys.exit(1)
    log_ok(f"Dossier SFX: {sfx_dir}")

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    # ── Duree de la video ──
    total_duration = probe_duration(video_path)
    fps = codex["video"]["fps"]
    log_ok(f"Video: {total_duration:.2f}s, {fps}fps")

    # ── Creation du mix SFX ──
    section("Creation du mix SFX")

    with tempfile.TemporaryDirectory() as tmpdir:
        sfx_mix_path = os.path.join(tmpdir, "sfx_mix.mp3")

        has_sfx = create_sfx_mix(
            codex.get("sfx_timeline", []),
            str(sfx_dir),
            fps,
            total_duration,
            sfx_mix_path
        )

        # ── Mixage final ──
        section("Mixage final video + SFX")

        output_path = output_dir / OUTPUT_VIDEO

        if has_sfx:
            # Mixer la video avec le mix SFX
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
        else:
            # Pas de SFX — copier la video telle quelle
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-c", "copy",
                str(output_path)
            ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log_fail(f"Erreur mixage final: {result.stderr[-500:]}")
            sys.exit(1)

        log_ok(f"Video finale: {output_path}")

    # ── Verification ──
    out_duration = probe_duration(output_path)
    out_size = os.path.getsize(output_path) / 1_000_000

    # ── Resume ──
    print()
    print("═" * 52)
    print(" F03B MIXER — MISSION ACCOMPLIE")
    print(f" SFX       : {len(codex.get('sfx_timeline', []))} dans le codex")
    print(f" SFX mix   : {'oui' if has_sfx else 'aucun'}")
    print(f" Duree     : {out_duration:.2f}s")
    print(f" Taille    : {out_size:.1f} MB")
    print(f" Fichier   : {OUTPUT_VIDEO}")
    print("═" * 52)
    print()

if __name__ == "__main__":
    main()
