"""
omnis_d00_ingest.py - D-F00 INGEST : Porte d'entree de la flotte delta
======================================================================
Accepte une video longue (URL YouTube via yt-dlp ou fichier local).
Produit une video source standardisee pour le pipeline delta.

Usage:
  python omnis_d00_ingest.py --url "https://youtube.com/watch?v=XXX" --output /path/OUT/
  python omnis_d00_ingest.py --file /path/IN/video.mp4 --output /path/OUT/

Entree: URL YouTube OU fichier local
Sortie: OUT/video_source.mp4 + OUT/d00_manifest.json
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

OUTPUT_FILENAME = "video_source.mp4"
MANIFEST_FILENAME = "d00_manifest.json"


def log_ok(msg): print(f"  [OK] {msg}")
def log_fail(msg): print(f"  [FAIL] {msg}")
def log_info(msg): print(f"  [...] {msg}")

def section(title):
    bar = "-" * max(0, 50 - len(title))
    print(f"\n-- {title} {bar}")


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
    if not video_stream:
        raise RuntimeError("Aucun stream video trouve")

    return {
        "duration_seconds": float(data["format"].get("duration", 0)),
        "fps": eval(video_stream.get("r_frame_rate", "0/1")),
        "width": int(video_stream["width"]),
        "height": int(video_stream["height"]),
        "codec": video_stream.get("codec_name", "unknown"),
        "bitrate": int(data["format"].get("bit_rate", 0)),
        "size_bytes": int(data["format"].get("size", 0)),
    }


def download_youtube(url, output_path):
    """Telecharge une video YouTube via yt-dlp."""
    section(f"Telechargement YouTube: {url}")
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "--extractor-args", "youtube:player_client=android",
        "-o", str(output_path),
        "--no-playlist",
        url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log_fail(f"yt-dlp failed: {result.stderr[-500:]}")
        sys.exit(1)
    log_ok(f"Video telechargee: {output_path}")


def copy_local(source_path, output_path):
    """Copie un fichier local vers la sortie."""
    import shutil
    section(f"Copie fichier local: {source_path}")
    shutil.copy2(str(source_path), str(output_path))
    log_ok(f"Fichier copie: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="D-F00 INGEST - Porte d'entree flotte delta"
    )
    parser.add_argument("--url", help="URL YouTube a telecharger")
    parser.add_argument("--file", help="Fichier video local a copier")
    parser.add_argument("--output", required=True, help="Dossier OUT/")
    args = parser.parse_args()

    if not args.url and not args.file:
        print("[D-F00] ERREUR: --url ou --file requis", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / OUTPUT_FILENAME

    section("D-F00 INGEST - Demarrage")

    if args.url:
        download_youtube(args.url, output_path)
        source = args.url
        source_type = "youtube"
    else:
        source_path = Path(args.file)
        if not source_path.exists():
            log_fail(f"Fichier introuvable: {source_path}")
            sys.exit(1)
        copy_local(source_path, output_path)
        source = str(source_path)
        source_type = "local"

    if not output_path.exists():
        log_fail(f"Video source non creee: {output_path}")
        sys.exit(1)

    section("Probe metadonnees")
    meta = probe_video(str(output_path))

    manifest = {
        "source_type": source_type,
        "source": source,
        "output": OUTPUT_FILENAME,
        "meta": meta,
    }
    manifest_path = output_dir / MANIFEST_FILENAME
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    size_mb = output_path.stat().st_size // (1024 * 1024)

    print()
    print("=" * 52)
    print(" D-F00 INGEST - MISSION ACCOMPLIE")
    print(f"  Source  : {source_type}")
    print(f"  Duree   : {meta['duration_seconds']:.1f}s")
    print(f"  FPS     : {meta['fps']}")
    print(f"  Resolution: {meta['width']}x{meta['height']}")
    print(f"  Codec   : {meta['codec']}")
    print(f"  Taille  : {size_mb} MB")
    print(f"  Fichier : {OUTPUT_FILENAME}")
    print("=" * 52)


if __name__ == "__main__":
    main()
