"""
omnis_f04.py — Fregate F04 CAMOUFLAGE
=====================================
Nettoyage de surface : wipe metadonnees + loudnorm pour YouTube.
Adapte de crs_f04_helbrecht.py (CRUSADER).

Usage:
  python omnis_f04.py --input /path/IN/ --output /path/OUT/

Entree: video_complete.mp4 (dans IN/)
Sortie: youtube_final.mp4 + rapport_f04.html (dans OUT/)
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

# ── Constantes ──────────────────────────────────────────────────────────────

INPUT_VIDEO = "video_complete.mp4"
OUTPUT_VIDEO = "youtube_final.mp4"
RAPPORT_HTML = "rapport_f04.html"

# ── Logging ─────────────────────────────────────────────────────────────────

def log_ok(msg): print(f"  [OK] {msg}")
def log_fail(msg): print(f"  [FAIL] {msg}")
def log_info(msg): print(f"  [...] {msg}")
def log_warn(msg): print(f"  [WARN] {msg}")

def section(title):
    bar = "─" * max(0, 50 - len(title))
    print(f"\n── {title} {bar}")

# ── Helpers ────────────────────────────────────────────────────────────────

def probe_video(path):
    """Retourne les metadonnees de la video via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")
    data = json.loads(result.stdout)

    video_stream = next(
        (s for s in data["streams"] if s["codec_type"] == "video"), None
    )
    audio_stream = next(
        (s for s in data["streams"] if s["codec_type"] == "audio"), None
    )

    info = {
        "duration": float(data["format"].get("duration", 0)),
        "size_mb": os.path.getsize(path) / 1_000_000,
        "format": data["format"].get("format_name", "unknown"),
        "bit_rate": int(data["format"].get("bit_rate", 0)),
    }

    if video_stream:
        info["video_codec"] = video_stream.get("codec_name", "unknown")
        info["width"] = int(video_stream.get("width", 0))
        info["height"] = int(video_stream.get("height", 0))
        info["fps"] = eval(video_stream.get("r_frame_rate", "30/1"))

    if audio_stream:
        info["audio_codec"] = audio_stream.get("codec_name", "unknown")
        info["sample_rate"] = int(audio_stream.get("sample_rate", 0))
        info["channels"] = int(audio_stream.get("channels", 0))

    # Metadonnees container
    info["tags"] = data["format"].get("tags", {})

    return info

def check_suspicious_tags(tags):
    """Verifie la presence de tags suspects."""
    SUSPICIOUS = ["remotion", "manim", "ffmpeg", "lavf", "lavc", "libav",
                  "python", "claude", "encoder"]
    found = []
    for key, value in tags.items():
        value_lower = str(value).lower()
        for sus in SUSPICIOUS:
            if sus in value_lower or sus in key.lower():
                found.append(f"{key}={value}")
    return found

# ── Camouflage ──────────────────────────────────────────────────────────────

def run_camouflage(input_path, output_path):
    """
    Re-encode avec:
    - H264 CRF18 (qualite elevee)
    - AAC 192k
    - loudnorm -14 LUFS (standard YouTube)
    - +faststart pour streaming
    - Wipe du tag encoder Lavf
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        # Video: re-encode H264 CRF18
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        # Audio: re-encode AAC + loudnorm
        "-c:a", "aac",
        "-b:a", "192k",
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
        # Wipe metadonnees
        "-map_metadata", "-1",
        "-metadata", "encoder=",
        # +faststart pour streaming
        "-movflags", "+faststart",
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log_fail("FFmpeg camouflage a echoue")
        print(result.stderr[-2000:])
        sys.exit(1)

    log_ok(f"Camouflage applique: {output_path}")

# ── Rapport HTML ────────────────────────────────────────────────────────────

def generate_rapport(output_dir, info_pre, info_post, suspicious_pre, suspicious_post):
    """Genere un rapport HTML de QA."""
    rapport_path = os.path.join(output_dir, RAPPORT_HTML)

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>F04 Camouflage — Rapport QA</title>
<style>
body {{ font-family: monospace; background: #1a1a2e; color: #eee; padding: 20px; }}
h1 {{ color: #e94560; }}
h2 {{ color: #0f3460; background: #16213e; padding: 8px; border-radius: 4px; }}
table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
td, th {{ border: 1px solid #333; padding: 8px; }}
th {{ background: #0f3460; }}
.ok {{ color: #4ecca3; }}
.fail {{ color: #e94560; }}
.warn {{ color: #f5a623; }}
</style>
</head>
<body>
<h1>F04 CAMOUFLAGE — Rapport QA</h1>
<p>Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

<h2>Avant camouflage</h2>
<table>
<tr><th>Parametre</th><th>Valeur</th></tr>
<tr><td>Codec video</td><td>{info_pre.get('video_codec', 'N/A')}</td></tr>
<tr><td>Resolution</td><td>{info_pre.get('width', 0)}x{info_pre.get('height', 0)}</td></tr>
<tr><td>Duree</td><td>{info_pre.get('duration', 0):.2f}s</td></tr>
<tr><td>Taille</td><td>{info_pre.get('size_mb', 0):.1f} MB</td></tr>
<tr><td>Codec audio</td><td>{info_pre.get('audio_codec', 'N/A')}</td></tr>
<tr><td>Tags suspects</td><td class="{'fail' if suspicious_pre else 'ok'}">{', '.join(suspicious_pre) if suspicious_pre else 'AUCUN'}</td></tr>
</table>

<h2>Apres camouflage</h2>
<table>
<tr><th>Parametre</th><th>Valeur</th></tr>
<tr><td>Codec video</td><td>{info_post.get('video_codec', 'N/A')}</td></tr>
<tr><td>Resolution</td><td>{info_post.get('width', 0)}x{info_post.get('height', 0)}</td></tr>
<tr><td>Duree</td><td>{info_post.get('duration', 0):.2f}s</td></tr>
<tr><td>Taille</td><td>{info_post.get('size_mb', 0):.1f} MB</td></tr>
<tr><td>Codec audio</td><td>{info_post.get('audio_codec', 'N/A')}</td></tr>
<tr><td>Loudnorm</td><td>-14 LUFS (YouTube standard)</td></tr>
<tr><td>Tags suspects</td><td class="{'fail' if suspicious_post else 'ok'}">{', '.join(suspicious_post) if suspicious_post else 'AUCUN'}</td></tr>
<tr><td>+faststart</td><td class="ok">OUI</td></tr>
</table>

<h2>Verdict</h2>
<p class="{'ok' if not suspicious_post else 'fail'}">
{'QA PASS — Video prete pour YouTube' if not suspicious_post else 'QA FAIL — Tags suspects restants'}
</p>
</body>
</html>"""

    with open(rapport_path, "w", encoding="utf-8") as f:
        f.write(html)

    log_ok(f"Rapport QA: {rapport_path}")

# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="F04 CAMOUFLAGE — Nettoyage + Loudnorm"
    )
    parser.add_argument("--input", required=True, help="Dossier IN/")
    parser.add_argument("--output", required=True, help="Dossier OUT/")

    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    input_path = input_dir / INPUT_VIDEO
    output_path = output_dir / OUTPUT_VIDEO

    # ── Verifications ──
    section("Verification des entrees")

    if not input_path.exists():
        log_fail(f"Video introuvable: {input_path}")
        sys.exit(1)
    log_ok(f"Video: {input_path}")

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    # ── Probe avant ──
    section("Analyse avant camouflage")
    info_pre = probe_video(input_path)
    log_ok(f"Source: {info_pre['width']}x{info_pre['height']}, "
           f"{info_pre['duration']:.1f}s, {info_pre['size_mb']:.1f} MB, "
           f"codec={info_pre.get('video_codec', '?')}")

    suspicious_pre = check_suspicious_tags(info_pre.get("tags", {}))
    if suspicious_pre:
        log_warn(f"Tags suspects avant: {suspicious_pre}")
    else:
        log_ok("Aucun tag suspect avant camouflage")

    # ── Camouflage ──
    section("Application du camouflage")
    run_camouflage(input_path, output_path)

    # ── Probe apres ──
    section("Analyse apres camouflage")
    info_post = probe_video(output_path)
    log_ok(f"Sortie: {info_post['width']}x{info_post['height']}, "
           f"{info_post['duration']:.1f}s, {info_post['size_mb']:.1f} MB, "
           f"codec={info_post.get('video_codec', '?')}")

    suspicious_post = check_suspicious_tags(info_post.get("tags", {}))
    if suspicious_post:
        log_warn(f"Tags suspects apres: {suspicious_post}")
    else:
        log_ok("Aucun tag suspect apres camouflage")

    # ── Rapport ──
    section("Rapport QA")
    generate_rapport(output_dir, info_pre, info_post, suspicious_pre, suspicious_post)

    # ── Resume ──
    print()
    print("═" * 52)
    print(" F04 CAMOUFLAGE — MISSION ACCOMPLIE")
    print(f" Fichier   : {OUTPUT_VIDEO}")
    print(f" Codec     : {info_post.get('video_codec', '?')} + {info_post.get('audio_codec', '?')}")
    print(f" Taille    : {info_post['size_mb']:.1f} MB")
    print(f" Duree     : {info_post['duration']:.1f}s")
    print(f" Loudnorm  : -14 LUFS")
    print(f" Rapport   : {RAPPORT_HTML}")
    qa_status = "PASS" if not suspicious_post else "FAIL"
    print(f" QA        : {qa_status}")
    print("═" * 52)
    print()

if __name__ == "__main__":
    main()
