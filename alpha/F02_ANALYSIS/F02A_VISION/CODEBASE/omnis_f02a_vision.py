"""
omnis_f02a_vision.py — F02A Phase 1 : Description Narrative
============================================================
Envoie des frames cles de la video a OpenRouter Vision
pour obtenir une description factuelle de l'action.

Usage:
  python omnis_f02a_vision.py --input /path/IN/ --output /path/OUT/ \
    --api-key $OPENROUTER_API_KEY [--model auto]

Entree: video_coupee.mp4 (dans IN/)
Sortie: narrative.txt (dans OUT/)

Dependances:
  requests (pip install requests)
  ffmpeg (system) pour l'extraction de frames

Le script:
  1. Extrait 4 frames cles de la video (debut, 1/3, 2/3, fin)
  2. Les encode en base64
  3. Les envoie a OpenRouter Vision (modele gratuit)
  4. Recupere la description factuelle
  5. Ecrit narrative.txt
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# ── Constantes ──────────────────────────────────────────────────────────────

INPUT_FILENAME = "video_coupee.mp4"
OUTPUT_FILENAME = "narrative.txt"
MANIFEST_FILENAME = "f01_manifest.json"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Modeles vision gratuits sur OpenRouter (par ordre de preference)
VISION_MODELS = [
    "meta-llama/llama-3.2-11b-vision-instruct:free",
    "qwen/qwen-2-vl-7b-instruct:free",
    "google/gemini-2.0-flash-exp:free",
]

DEFAULT_MODEL = "auto"  # Essaie les modeles dans l'ordre
NUM_KEYFRAMES = 4  # Nombre de frames cles a extraire

# ── Logging ─────────────────────────────────────────────────────────────────

def log_ok(msg): print(f"  [OK] {msg}")
def log_fail(msg): print(f"  [FAIL] {msg}")
def log_info(msg): print(f"  [...] {msg}")
def log_warn(msg): print(f"  [WARN] {msg}")

def section(title):
    bar = "─" * max(0, 50 - len(title))
    print(f"\n── {title} {bar}")

# ── Extraction de frames ────────────────────────────────────────────────────

def extract_keyframes(video_path, num_frames, output_dir):
    """
    Extrait N frames cles reparties uniformement dans la video.
    Retourne la liste des chemins des frames.
    """
    # Obtenir la duree de la video
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", str(video_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log_fail(f"ffprobe failed: {result.stderr}")
        sys.exit(1)

    data = json.loads(result.stdout)
    duration = float(data["format"]["duration"])

    # Calculer les timestamps des frames cles
    timestamps = []
    for i in range(num_frames):
        t = duration * (i + 0.5) / num_frames
        timestamps.append(t)

    frame_paths = []
    for i, t in enumerate(timestamps):
        frame_path = os.path.join(output_dir, f"keyframe_{i:02d}.jpg")
        cmd = [
            "ffmpeg", "-y", "-ss", str(t),
            "-i", str(video_path),
            "-frames:v", "1",
            "-q:v", "2",
            frame_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log_warn(f"Frame {i} a {t:.2f}s non extraite")
        else:
            frame_paths.append(frame_path)
            log_info(f"Frame {i}: {t:.2f}s → {frame_path}")

    return frame_paths

def encode_frame_base64(frame_path):
    """Encode une image en base64."""
    with open(frame_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")

# ── OpenRouter Vision ───────────────────────────────────────────────────────

def call_openrouter_vision(api_key, frames_b64, model="auto"):
    """
    Envoie les frames a OpenRouter Vision et recupere la description.
    Essaie plusieurs modeles si model='auto'.
    """
    import requests

    # Construire le contenu du message (texte + images)
    content = [
        {
            "type": "text",
            "text": (
                "You are a video analysis assistant. I will show you "
                f"{len(frames_b64)} keyframes from a short video. "
                "Describe what you see in a factual, objective way. "
                "Focus on: who is in the scene, what they are doing, "
                "the setting, and any notable actions or emotions visible. "
                "Write 3-5 sentences. Be factual — do not invent stories. "
                "Write in English."
            )
        }
    ]

    for i, b64 in enumerate(frames_b64):
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{b64}"
            }
        })

    # Selectionner les modeles a essayer
    if model == "auto":
        models_to_try = VISION_MODELS
    else:
        models_to_try = [model]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    for model_name in models_to_try:
        log_info(f"Essai modele: {model_name}")

        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ],
            "max_tokens": 500,
            "temperature": 0.3
        }

        try:
            response = requests.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                description = data["choices"][0]["message"]["content"].strip()
                log_ok(f"Description recue ({len(description)} chars)")
                return description, model_name
            else:
                log_warn(f"HTTP {response.status_code}: {response.text[:200]}")
                continue

        except requests.exceptions.Timeout:
            log_warn(f"Timeout pour {model_name}")
            continue
        except Exception as e:
            log_warn(f"Erreur pour {model_name}: {e}")
            continue

    log_fail("Tous les modeles ont echoue")
    return None, None

# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="F02A VISION — Description narrative via OpenRouter Vision"
    )
    parser.add_argument("--input", required=True, help="Dossier IN/")
    parser.add_argument("--output", required=True, help="Dossier OUT/")
    parser.add_argument("--api-key", required=False,
                        default=os.environ.get("OPENROUTER_API_KEY", ""),
                        help="Cle API OpenRouter (ou env OPENROUTER_API_KEY)")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"Modele vision (auto={DEFAULT_MODEL} ou nom du modele)")
    parser.add_argument("--num-frames", type=int, default=NUM_KEYFRAMES,
                        help=f"Nombre de frames cles (defaut: {NUM_KEYFRAMES})")

    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    video_path = input_dir / INPUT_FILENAME

    # ── Verifications ──
    section("Verification des entrees")

    if not video_path.exists():
        log_fail(f"Video introuvable: {video_path}")
        sys.exit(1)
    log_ok(f"Video: {video_path}")

    if not args.api_key:
        log_fail("Cle API OpenRouter manquante (--api-key ou OPENROUTER_API_KEY)")
        sys.exit(1)
    log_ok("Cle API OpenRouter disponible")

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    # ── Extraction des frames ──
    section(f"Extraction de {args.num_frames} frames cles")

    with tempfile.TemporaryDirectory() as tmpdir:
        frame_paths = extract_keyframes(
            video_path, args.num_frames, tmpdir
        )

        if not frame_paths:
            log_fail("Aucune frame extraite")
            sys.exit(1)

        log_ok(f"{len(frame_paths)} frames extraites")

        # ── Encodage base64 ──
        section("Encodage des frames")
        frames_b64 = []
        for fp in frame_paths:
            b64 = encode_frame_base64(fp)
            frames_b64.append(b64)
            size_kb = len(b64) * 3 / 4 / 1024
            log_info(f"{os.path.basename(fp)}: {size_kb:.1f} KB")

        # ── Appel OpenRouter ──
        section("Appel OpenRouter Vision")
        description, used_model = call_openrouter_vision(
            args.api_key, frames_b64, args.model
        )

        if not description:
            log_fail("Echec de la description")
            sys.exit(1)

        # ── Ecriture du narrative.txt ──
        section("Generation du narrative.txt")

        output_text = f"""# F02A VISION — Description Narrative
# Modele: {used_model}
# Frames: {len(frame_paths)}
# Date: {os.environ.get('GITHUB_RUN_ID', 'local')}

{description}
"""

        output_path = output_dir / OUTPUT_FILENAME
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_text)

        log_ok(f"narrative.txt ecrit ({len(output_text)} chars)")

    # ── Resume ──
    print()
    print("═" * 52)
    print(" F02A VISION — MISSION ACCOMPLIE")
    print(f" Modele    : {used_model}")
    print(f" Frames    : {len(frame_paths)}")
    print(f" Description: {len(description)} chars")
    print(f" Fichier   : {OUTPUT_FILENAME}")
    print("═" * 52)
    print()

if __name__ == "__main__":
    main()
