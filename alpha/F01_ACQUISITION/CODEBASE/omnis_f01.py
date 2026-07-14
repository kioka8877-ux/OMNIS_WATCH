"""
omnis_f01.py — Fregate F01 ACQUISITION
======================================
Decoupe et formatage de la video brute.
FFmpeg coupe, redimensionne, applique blur-pad, vitesse et volume.

Usage:
  python omnis_f01.py --input /path/IN/ --output /path/OUT/ \
    --in-timestamp 00:02 --out-timestamp 00:15 \
    --format 9:16 --blur-pad true --speed 1.0 --volume 1.0

Entree: video_raw.mp4 (dans IN/)
Sortie: video_coupee.mp4 + f01_manifest.json (dans OUT/)

Aucun texte, aucun tracking, aucun SFX. Juste la coupe et le format.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# ── Constantes ──────────────────────────────────────────────────────────────

INPUT_FILENAME = "video_raw.mp4"
OUTPUT_FILENAME = "video_coupee.mp4"
MANIFEST_FILENAME = "f01_manifest.json"
DEFAULT_FPS = 30

# Resolutions cibles par format
FORMAT_RESOLUTIONS = {
    "9:16": {"width": 1080, "height": 1920},
    "16:9": {"width": 1920, "height": 1080},
    "1:1": {"width": 1080, "height": 1080},
}

# ── Logging ─────────────────────────────────────────────────────────────────

def log_ok(msg): print(f"  [OK] {msg}")
def log_fail(msg): print(f"  [FAIL] {msg}")
def log_info(msg): print(f"  [...] {msg}")
def log_warn(msg): print(f"  [WARN] {msg}")

def section(title):
    bar = "─" * max(0, 50 - len(title))
    print(f"\n── {title} {bar}")

# ── Helpers FFmpeg ──────────────────────────────────────────────────────────

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
        s for s in data["streams"] if s["codec_type"] == "video"
    )
    return {
        "width": int(video_stream["width"]),
        "height": int(video_stream["height"]),
        "fps": eval(video_stream.get("r_frame_rate", "30/1")),
        "duration": float(data["format"].get("duration", 0)),
        "codec": video_stream.get("codec_name", "unknown"),
    }

def timestamp_to_seconds(ts):
    """Convertit 'MM:SS' ou 'HH:MM:SS' en secondes float."""
    parts = ts.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    return float(ts)

# ── Construction du filtre FFmpeg ───────────────────────────────────────────

def build_scale_filter(src_w, src_h, dst_w, dst_h, blur_pad):
    """
    Construit le filtre de redimensionnement.
    - Sans blur-pad: scale simple + crop center
    - Avec blur-pad: scale + pad avec fond flou
    """
    src_ratio = src_w / src_h
    dst_ratio = dst_w / dst_h

    if blur_pad:
        # Blur-pad: la video est mise a l'echelle pour rentrer dans le format,
        # le reste est rempli par une version floue de la video elle-meme
        if src_ratio > dst_ratio:
            # Source plus large: fit par largeur
            scaled_w = dst_w
            scaled_h = int(dst_w / src_ratio)
        else:
            # Source plus haute: fit par hauteur
            scaled_h = dst_h
            scaled_w = int(dst_h * src_ratio)

        offset_x = (dst_w - scaled_w) // 2
        offset_y = (dst_h - scaled_h) // 2

        # Filter complex: split -> blur -> scale to fill -> overlay scaled video
        filter_complex = (
            f"[0:v]split=2[bg][fg];"
            f"[bg]scale={dst_w}:{dst_h}:force_original_aspect_ratio=increase,"
            f"crop={dst_w}:{dst_h},boxblur=20:5[bg];"
            f"[fg]scale={scaled_w}:{scaled_h}[fg];"
            f"[bg][fg]overlay={offset_x}:{offset_y}[v]"
        )
        return filter_complex, "[v]"
    else:
        # Sans blur-pad: crop center puis scale
        if src_ratio > dst_ratio:
            # Source plus large: crop horizontalement
            crop_w = int(src_h * dst_ratio)
            crop_h = src_h
            crop_x = (src_w - crop_w) // 2
            crop_y = 0
        else:
            # Source plus haute: crop verticalement
            crop_w = src_w
            crop_h = int(src_w / dst_ratio)
            crop_x = 0
            crop_y = (src_h - crop_h) // 2

        vf = (
            f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y},"
            f"scale={dst_w}:{dst_h}"
        )
        return vf, None

def build_speed_filter(speed):
    """
    Construit le filtre de vitesse.
    setpts pour la video, atempo pour l'audio (limite 0.5x-2.0x par passe).
    """
    if speed == 1.0:
        return None, None

    video_filter = f"setpts={1.0/speed}*PTS"

    # atempo supporte 0.5x a 2.0x par passe. On chaine si necessaire.
    audio_filters = []
    remaining = speed
    while remaining > 2.0:
        audio_filters.append("atempo=2.0")
        remaining /= 2.0
    while remaining < 0.5:
        audio_filters.append("atempo=0.5")
        remaining /= 0.5
    audio_filters.append(f"atempo={remaining}")

    audio_filter = ",".join(audio_filters)
    return video_filter, audio_filter

def build_volume_filter(volume):
    """Construit le filtre de volume."""
    if volume == 1.0:
        return None
    return f"volume={volume}"

# ── Execution FFmpeg ────────────────────────────────────────────────────────

def run_ffmpeg(input_path, output_path, in_ts, out_ts, fmt, blur_pad,
               speed, volume, src_info):
    """Execute la commande FFmpeg complete."""
    dst = FORMAT_RESOLUTIONS[fmt]
    dst_w, dst_h = dst["width"], dst["height"]

    # Duree de la sequence
    in_sec = timestamp_to_seconds(in_ts)
    out_sec = timestamp_to_seconds(out_ts)
    duration = out_sec - in_sec

    if duration <= 0:
        log_fail(f"Duree negative ou nulle: {in_ts} -> {out_ts}")
        sys.exit(1)

    # ── Construction des filtres ──
    section("Construction des filtres")

    # 1. Scale + blur-pad
    scale_filter, video_label = build_scale_filter(
        src_info["width"], src_info["height"],
        dst_w, dst_h, blur_pad
    )
    log_info(f"Format: {fmt} ({dst_w}x{dst_h}), blur-pad: {blur_pad}")

    # 2. Vitesse
    speed_vf, speed_af = build_speed_filter(speed)
    if speed_vf:
        log_info(f"Vitesse: {speed}x (setpts + atempo)")

    # 3. Volume
    volume_af = build_volume_filter(volume)
    if volume_af:
        log_info(f"Volume: {volume}x")

    # ── Assemblage du filter_complex ou -vf ──
    # Si on a du blur-pad, on doit utiliser -filter_complex
    # Sinon on peut utiliser -vf / -af

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(in_sec),
        "-i", str(input_path),
        "-t", str(duration),
    ]

    if blur_pad:
        # Mode filter_complex (blur-pad necessite split)
        # On insere les filtres video dans le filter_complex
        fc_parts = []

        # Recuperer le filter_complex du blur-pad
        # Il finit par [v] pour la video
        fc_parts.append(scale_filter)

        # Ajouter setpts si vitesse
        if speed_vf:
            # Remplacer [v] par [v] -> setpts -> [v2]
            fc_parts[0] = fc_parts[0].replace("[v]", f"setpts={1.0/speed}*PTS[v]")
            video_label = "[v]"

        cmd.extend(["-filter_complex", ";".join(fc_parts)])
        cmd.extend(["-map", video_label])

        # Audio filters
        audio_afs = []
        if speed_af:
            audio_afs.append(speed_af)
        if volume_af:
            audio_afs.append(volume_af)

        if audio_afs:
            cmd.extend(["-map", "0:a"])
            cmd.extend(["-af", ",".join(audio_afs)])
        else:
            cmd.extend(["-map", "0:a?"])  # audio optionnel
    else:
        # Mode -vf / -af simple
        vf_parts = [scale_filter]
        if speed_vf:
            vf_parts.append(speed_vf)

        cmd.extend(["-vf", ",".join(vf_parts)])

        audio_afs = []
        if speed_af:
            audio_afs.append(speed_af)
        if volume_af:
            audio_afs.append(volume_af)

        if audio_afs:
            cmd.extend(["-af", ",".join(audio_afs)])

    # Encoding settings
    cmd.extend([
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-r", str(DEFAULT_FPS),
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        str(output_path)
    ])

    # ── Execution ──
    section("Execution FFmpeg")
    log_info(f"Commande: {' '.join(cmd[:6])}... {output_path}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        log_fail("FFmpeg a echoue")
        print(result.stderr[-2000:])
        sys.exit(1)

    log_ok(f"Video generee: {output_path}")

    # ── Verification ──
    out_info = probe_video(output_path)
    actual_duration = out_info["duration"]
    actual_fps = out_info["fps"]
    total_frames = int(actual_duration * actual_fps)

    log_ok(f"Resolution: {out_info['width']}x{out_info['height']}")
    log_ok(f"Duree: {actual_duration:.2f}s")
    log_ok(f"FPS: {actual_fps}")
    log_ok(f"Frames totales: {total_frames}")

    return out_info, actual_duration, total_frames

# ── Manifest ────────────────────────────────────────────────────────────────

def generate_manifest(output_dir, out_info, actual_duration, total_frames,
                       fmt, blur_pad, speed, volume, in_ts, out_ts):
    """Genere le fichier f01_manifest.json."""
    manifest = {
        "meta": {
            "fps": int(out_info["fps"]),
            "duration_seconds": round(actual_duration, 2),
            "total_frames": total_frames,
            "width": out_info["width"],
            "height": out_info["height"],
            "format": fmt,
            "blur_pad": blur_pad,
            "speed": speed,
            "volume": volume,
            "codec": out_info["codec"]
        },
        "input": {
            "source_file": INPUT_FILENAME,
            "in_timestamp": in_ts,
            "out_timestamp": out_ts
        },
        "output": {
            "file": OUTPUT_FILENAME,
            "size_mb": round(
                os.path.getsize(os.path.join(output_dir, OUTPUT_FILENAME)) / 1_000_000, 2
            )
        }
    }

    manifest_path = os.path.join(output_dir, MANIFEST_FILENAME)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    log_ok(f"Manifest ecrit: {manifest_path}")
    return manifest

# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="F01 ACQUISITION — Decoupe et formatage video"
    )
    parser.add_argument("--input", required=True, help="Dossier IN/")
    parser.add_argument("--output", required=True, help="Dossier OUT/")
    parser.add_argument("--in-timestamp", required=True, help="Timestamp IN (ex: 00:02)")
    parser.add_argument("--out-timestamp", required=True, help="Timestamp OUT (ex: 00:15)")
    parser.add_argument("--format", default="9:16",
                        choices=["9:16", "16:9", "1:1"],
                        help="Format cible")
    parser.add_argument("--blur-pad", default="true",
                        choices=["true", "false"],
                        help="Activer le blur-pad")
    parser.add_argument("--speed", type=float, default=1.0,
                        help="Vitesse (ex: 1.0, 1.5, 0.5)")
    parser.add_argument("--volume", type=float, default=1.0,
                        help="Volume (ex: 1.0, 1.5, 0.5)")
    parser.add_argument("--fps", type=int, default=DEFAULT_FPS,
                        help="FPS cible")

    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    input_path = input_dir / INPUT_FILENAME
    output_path = output_dir / OUTPUT_FILENAME

    # ── Verifications ──
    section("Verification des entrees")

    if not input_path.exists():
        log_fail(f"Video source introuvable: {input_path}")
        sys.exit(1)
    log_ok(f"Video source: {input_path}")

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        log_info(f"Dossier OUT cree: {output_dir}")

    # Verifier FFmpeg
    ffmpeg_check = subprocess.run(
        ["ffmpeg", "-version"], capture_output=True, text=True
    )
    if ffmpeg_check.returncode != 0:
        log_fail("FFmpeg non installe")
        sys.exit(1)
    log_ok("FFmpeg disponible")

    # ── Probe de la source ──
    section("Analyse de la video source")
    src_info = probe_video(input_path)
    log_ok(f"Source: {src_info['width']}x{src_info['height']}, "
           f"{src_info['fps']:.1f}fps, {src_info['duration']:.1f}s, "
           f"codec={src_info['codec']}")

    # ── Execution ──
    blur_pad = args.blur_pad == "true"

    out_info, actual_duration, total_frames = run_ffmpeg(
        input_path, output_path,
        args.in_timestamp, args.out_timestamp,
        args.format, blur_pad,
        args.speed, args.volume,
        src_info
    )

    # ── Manifest ──
    section("Generation du manifest")
    manifest = generate_manifest(
        output_dir, out_info, actual_duration, total_frames,
        args.format, blur_pad, args.speed, args.volume,
        args.in_timestamp, args.out_timestamp
    )

    # ── Resume ──
    print()
    print("═" * 52)
    print(" F01 ACQUISITION — MISSION ACCOMPLIE")
    print(f" Fichier   : {OUTPUT_FILENAME}")
    print(f" Format    : {args.format} ({out_info['width']}x{out_info['height']})")
    print(f" Duree     : {actual_duration:.2f}s ({total_frames} frames)")
    print(f" Blur-pad  : {blur_pad}")
    print(f" Vitesse   : {args.speed}x")
    print(f" Volume    : {args.volume}x")
    print(f" Manifest  : {MANIFEST_FILENAME}")
    print("═" * 52)
    print()

if __name__ == "__main__":
    main()
