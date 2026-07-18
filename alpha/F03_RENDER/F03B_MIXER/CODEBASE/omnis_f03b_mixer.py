"""
omnis_f03b_mixer.py — F03B : Mixeur Audio
==========================================
Prend la video muette de F03A et lui greffe les SFX aux bonnes frames.
Les SFX sont synchronises avec les text_overlays du codex.

Usage:
  python omnis_f03b_mixer.py --input /path/IN/ --output /path/OUT/ \
    --sfx-dir /path/to/sfx/

Entree: video_visuelle.mp4 + codex.json (sfx_timeline + text_overlays) + sfx/
Sortie: video_complete.mp4

Le script:
  1. Lit le codex.json (section sfx_timeline + text_overlays)
  2. Pour chaque SFX, calcule le timestamp (frame / fps)
  3. Croise les SFX avec les text_overlays pour determiner la duree exacte
     - keyboard: joue pendant toute la duree du texte, s'arrete quand le texte disparait
     - whoosh/pop/ding: duree naturelle (impacts courts)
  4. Cree un fichier audio mix avec tous les SFX aux bons timestamps
  5. FFmpeg mixe le SFX audio sur la video
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# ── Constantes ────────────────────────────────────────────────────────────────

INPUT_VIDEO = "video_visuelle.mp4"
INPUT_CODEX = "codex.json"
OUTPUT_VIDEO = "video_complete.mp4"

# SFX types qui sont des impacts courts (duree naturelle, pas de troncature)
SHORT_SFX_TYPES = {"whoosh", "pop", "ding", "impact", "swish", "thump"}

# ── Logging ───────────────────────────────────────────────────────────────────

def log_ok(msg): print(f"  [OK] {msg}")
def log_fail(msg): print(f"  [FAIL] {msg}")
def log_info(msg): print(f"  [...] {msg}")
def log_warn(msg): print(f"  [WARN] {msg}")

def section(title):
    bar = "─" * max(0, 50 - len(title))
    print(f"\n── {title} {bar}")

# ── Helpers ───────────────────────────────────────────────────────────────────

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

def find_text_duration(sfx_frame, text_overlays, fps):
    """
    Trouve la duree du texte correspondant a un SFX donne.
    Match par start_frame: si un text_overlay commence a la meme frame que le SFX,
    on retourne la duree (end_frame - start_frame) / fps.
    Si aucun texte ne correspond, retourne 0 (duree naturelle du SFX).
    """
    if not text_overlays:
        return 0

    for text in text_overlays:
        text_start = text.get("start_frame", -1)
        text_end = text.get("end_frame", -1)
        if text_start == sfx_frame and text_end > text_start:
            duration_sec = (text_end - text_start) / fps
            return duration_sec

    return 0

# ── Mixage SFX ────────────────────────────────────────────────────────────────

def create_sfx_mix(sfx_timeline, text_overlays, sfx_dir, fps, total_duration, output_path):
    """
    Cree un fichier audio contenant tous les SFX mixes aux bons timestamps.
    Les SFX 'keyboard' sont tronques a la duree du texte correspondant.
    Les SFX courts (whoosh, pop, ding) gardent leur duree naturelle.
    """
    if not sfx_timeline:
        log_info("Aucun SFX dans le codex — copie de la video sans modification")
        return False

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

        # ── SYNCHRO TEXTE ────────────────────────────────────────────────────
        # Trouver la duree du texte correspondant a ce SFX
        text_duration = find_text_duration(sfx["frame"], text_overlays, fps)

        # Determiner la duree du SFX:
        # - keyboard: tronque a la duree du texte (joue pendant tout le texte)
        # - whoosh/pop/ding: duree naturelle (impacts courts)
        if sfx_type in SHORT_SFX_TYPES:
            # SFX court: duree naturelle, pas de troncature
            sfx_duration = 0  # 0 = pas de troncature
            log_info(f"SFX: {sfx_type} a {timestamp:.3f}s (frame {sfx['frame']}), volume={volume} [impact court]")
        else:
            # SFX long (keyboard, etc.): tronque a la duree du texte
            if text_duration > 0:
                sfx_duration = text_duration
                log_info(f"SFX: {sfx_type} a {timestamp:.3f}s (frame {sfx['frame']}), volume={volume}, duree={sfx_duration:.2f}s [synchro texte]")
            else:
                # Pas de texte correspondant: duree naturelle
                sfx_duration = 0
                log_info(f"SFX: {sfx_type} a {timestamp:.3f}s (frame {sfx['frame']}), volume={volume} [pas de texte correspondant]")

        valid_sfx.append({
            "file": sfx_file,
            "timestamp": timestamp,
            "volume": volume,
            "type": sfx_type,
            "duration": sfx_duration
        })

    if not valid_sfx:
        log_warn("Aucun SFX valide trouve — video sans son ajoute")
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        # Etape 1: Pour chaque SFX, creer un fichier audio avec delay + volume + troncature
        delayed_files = []

        for i, sfx in enumerate(valid_sfx):
            delayed_path = os.path.join(tmpdir, f"sfx_{i:02d}.mp3")

            delay_ms = int(sfx["timestamp"] * 1000)

            # Construire le filtre audio: delay + volume
            audio_filter = f"adelay={delay_ms}|{delay_ms},volume={sfx['volume']}"

            # Commande FFmpeg de base
            cmd = [
                "ffmpeg", "-y",
                "-i", sfx["file"],
                "-af", audio_filter,
            ]

            # Si le SFX a une duree definie (keyboard synchro texte), tronquer
            if sfx["duration"] > 0:
                # Tronquer le SFX a sa duree + le delay initial
                # La duree totale = delay + duree du SFX
                total_sfx_duration = sfx["timestamp"] + sfx["duration"]
                cmd.extend(["-t", str(total_sfx_duration)])
            else:
                # Duree naturelle, mais on limite a la duree totale de la video
                cmd.extend(["-t", str(total_duration)])

            cmd.append(delayed_path)

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
            cmd = [
                "ffmpeg", "-y",
                "-i", delayed_files[0],
                "-t", str(total_duration),
                output_path
            ]
        else:
            cmd = ["ffmpeg", "-y"]
            for f in delayed_files:
                cmd.extend(["-i", f])

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

# ── Main ──────────────────────────────────────────────────────────────────────

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

    sfx_timeline = codex.get("sfx_timeline", [])
    text_overlays = codex.get("text_overlays", [])

    log_ok(f"Codex lu: {len(sfx_timeline)} SFX, {len(text_overlays)} textes")

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

    # ── Afficher la synchro texte/SFX ──
    section("Synchro SFX ↔ Textes")
    for sfx in sfx_timeline:
        sfx_type = sfx["type"]
        sfx_frame = sfx["frame"]
        matched_text = None
        for text in text_overlays:
            if text.get("start_frame") == sfx_frame:
                matched_text = text
                break

        if matched_text:
            text_dur = (matched_text["end_frame"] - matched_text["start_frame"]) / fps
            log_info(f"  {sfx_type}@frame{sfx_frame} → texte '{matched_text.get('content','')[:30]}' ({text_dur:.1f}s)")
        else:
            log_info(f"  {sfx_type}@frame{sfx_frame} → aucun texte correspondant")

    # ── Creation du mix SFX ──
    section("Creation du mix SFX")

    with tempfile.TemporaryDirectory() as tmpdir:
        sfx_mix_path = os.path.join(tmpdir, "sfx_mix.mp3")

        has_sfx = create_sfx_mix(
            sfx_timeline,
            text_overlays,
            str(sfx_dir),
            fps,
            total_duration,
            sfx_mix_path
        )

        # ── Mixage final ──
        section("Mixage final video + SFX")

        output_path = output_dir / OUTPUT_VIDEO

        if has_sfx:
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
    print(f" SFX       : {len(sfx_timeline)} dans le codex")
    print(f" Textes    : {len(text_overlays)} dans le codex")
    print(f" SFX mix   : {'oui' if has_sfx else 'aucun'}")
    print(f" Duree     : {out_duration:.2f}s")
    print(f" Taille    : {out_size:.1f} MB")
    print(f" Fichier   : {OUTPUT_VIDEO}")
    print("═" * 52)
    print()

if __name__ == "__main__":
    main()
