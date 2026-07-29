"""
omnis_f00.py — F00 ASSETFORGE : Pipeline de préparation multi-clips
Prend plusieurs clips bruts + un JSON de séquences → sort UN clip unique concaténé.

Mode GAMMA (commentary niche) :
- L'opérateur upload plusieurs clips bruts
- L'opérateur sélectionne des séquences (IN/OUT) par clip via le viewer F00
- F00 coupe chaque séquence, ajuste la vitesse, concatène → un seul clip
- Le clip unique est calibré sur la durée de la voix off (budget temporel)

Flow :
  clips bruts + sequences.json + voiceoff_duration
    ↓
  F00 coupe chaque séquence (FFmpeg)
  F00 applique la vitesse par séquence (setpts + atempo)
  F00 concatène les séquences en un seul clip (concat demuxer)
    ↓
  clip_unique.mp4 + f00_manifest.json

Le clip unique passe ensuite dans le pipeline beta (F02 Preview → F03 → F04 → F05)
"""
import argparse, json, os, sys, subprocess, tempfile


def cut_segment(input_video, start, end, speed, output_path):
    """Coupe un segment et applique la vitesse."""
    duration = end - start
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", input_video,
        "-t", str(duration),
        "-vf", f"setpts={1/speed}*PTS",
        "-af", f"atempo={speed}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-r", "30",
        output_path
    ]
    print(f"  [F00] Coupe {os.path.basename(input_video)} [{start}s-{end}s] speed={speed}x")
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


def concat_segments(segment_paths, output_path):
    """Concatène les segments en un seul clip."""
    concat_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    for p in segment_paths:
        concat_file.write(f"file '{os.path.abspath(p)}'\n")
    concat_file.close()

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_file.name,
        "-c", "copy",
        output_path
    ]
    print(f"  [F00] Concaténation de {len(segment_paths)} segments")
    subprocess.run(cmd, check=True, capture_output=True)
    os.unlink(concat_file.name)
    return output_path


def get_duration(video_path):
    """Retourne la durée d'une vidéo en secondes."""
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", video_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--sequences', required=True, help='Path to sequences.json')
    p.add_argument('--clips-dir', required=True, help='Directory containing raw clips')
    p.add_argument('--output', required=True, help='Output directory')
    p.add_argument('--voiceoff-duration', type=float, default=0,
                   help='Durée voix off en secondes (budget temporel)')
    args = p.parse_args()

    os.makedirs(args.output, exist_ok=True)

    with open(args.sequences) as f:
        data = json.load(f)

    segments = data.get('segments', [])
    if not segments:
        print("[F00] ERREUR: Aucune séquence définie", file=sys.stderr)
        sys.exit(1)

    print(f"[F00] {len(segments)} séquences à traiter")
    if args.voiceoff_duration > 0:
        print(f"[F00] Budget voix off: {args.voiceoff_duration}s")

    # Couper chaque séquence
    temp_dir = tempfile.mkdtemp()
    segment_paths = []
    total_duration = 0

    for i, seg in enumerate(segments):
        clip_name = seg['clip']
        clip_path = os.path.join(args.clips_dir, clip_name)
        if not os.path.exists(clip_path):
            print(f"[F00] ERREUR: Clip {clip_name} introuvable", file=sys.stderr)
            sys.exit(1)

        start = seg['in']
        end = seg['out']
        speed = seg.get('speed', 1.0)

        seg_path = os.path.join(temp_dir, f"seg_{i:03d}.mp4")
        cut_segment(clip_path, start, end, speed, seg_path)
        segment_paths.append(seg_path)

        seg_dur = (end - start) / speed
        total_duration += seg_dur
        print(f"  → Durée: {seg_dur:.1f}s")

    print(f"[F00] Durée totale assemblée: {total_duration:.1f}s")

    # Vérification budget voix off
    if args.voiceoff_duration > 0:
        diff = total_duration - args.voiceoff_duration
        if diff > 0.5:
            print(f"[F00] ⚠️  Trop long de {diff:.1f}s vs voix off ({args.voiceoff_duration}s)")
        elif diff < -0.5:
            print(f"[F00] ⚠️  Trop court de {abs(diff):.1f}s vs voix off ({args.voiceoff_duration}s)")
        else:
            print(f"[F00] ✅ Sync parfait avec voix off (écart: {diff:.1f}s)")

    # Concaténer
    output_video = os.path.join(args.output, 'clip_unique.mp4')
    concat_segments(segment_paths, output_video)

    # Manifest
    manifest = {
        "source_clips": list(set(s['clip'] for s in segments)),
        "segment_count": len(segments),
        "total_duration_sec": round(total_duration, 2),
        "voiceoff_duration_sec": args.voiceoff_duration,
        "output": "clip_unique.mp4",
        "segments": segments
    }
    manifest_path = os.path.join(args.output, 'f00_manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    # Cleanup
    for p in segment_paths:
        os.unlink(p)
    os.rmdir(temp_dir)

    final_dur = get_duration(output_video)
    size_mb = os.path.getsize(output_video) // (1024 * 1024)
    print(f"\n[F00] TERMINE")
    print(f"  Clip unique: {output_video} ({size_mb} MB, {final_dur:.1f}s)")
    print(f"  Manifest: {manifest_path}")


if __name__ == '__main__':
    main()
