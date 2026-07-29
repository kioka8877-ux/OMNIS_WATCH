"""
omnis_d04_assembly.py - D-F04 ASSEMBLY
=====================================
Monteur final: sous-titres styles + SFX viraux (PERTURABO) + loop hook.

Usage:
  python omnis_d04_assembly.py --input /path/IN/ --output /path/OUT/ \\
      --sfx-dir /path/to/sfx/

Entree: clips_reframes/ + transcript.json + cutlist.json
Sortie: clips_finaux/clip_final_001.mp4 ... + assembly_manifest.json
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

INPUT_CLIPS_DIR = "clips_reframes"
INPUT_TRANSCRIPT = "transcript.json"
INPUT_CUTLIST = "cutlist.json"
OUTPUT_DIR_CLIPS = "clips_finaux"
OUTPUT_MANIFEST = "assembly_manifest.json"

SHORT_SFX = {"whoosh", "pop", "ding", "impact"}


def log_ok(msg): print(f"  [OK] {msg}")
def log_fail(msg): print(f"  [FAIL] {msg}")
def log_info(msg): print(f"  [...] {msg}")

def section(title):
    bar = "-" * max(0, 50 - len(title))
    print(f"\n-- {title} {bar}")


def get_duration(video_path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def get_fps(video_path):
    cmd = ["ffprobe", "-v", "error", "-select_streams", "v",
           "-show_entries", "stream=r_frame_rate",
           "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return eval(result.stdout.strip())


def extract_clip_words(transcript_data, start_sec, end_sec):
    """Extrait les mots du transcript pour une plage temporelle."""
    words = transcript_data.get("words", [])
    clip_words = []
    clip_start = start_sec
    for w in words:
        if w["start"] >= start_sec and w["end"] <= end_sec:
            clip_words.append({
                "word": w["word"],
                "start": round(w["start"] - clip_start, 3),
                "end": round(w["end"] - clip_start, 3),
            })
    return clip_words


def generate_srt(clip_words, output_path):
    """Genere un fichier SRT depuis les mots."""
    def format_time(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    lines = []
    group_size = 3
    for i in range(0, len(clip_words), group_size):
        group = clip_words[i:i+group_size]
        start = group[0]["start"]
        end = group[-1]["end"]
        text = " ".join(g["word"] for g in group)
        lines.append(f"{i // group_size + 1}")
        lines.append(f"{format_time(start)} --> {format_time(end)}")
        lines.append(text)
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def create_sfx_mix(cutlist_moment, sfx_dir, fps, total_duration, output_path):
    """Cree un mix SFX selon les regles PERTURABO."""
    vtype = cutlist_moment.get("viral_type", "")

    sfx_entries = []
    if vtype == "hook":
        sfx_entries.append({"type": "whoosh", "delay_ms": 0, "volume": 0.9})
        sfx_entries.append({"type": "pop", "delay_ms": 200, "volume": 0.7})
    elif vtype == "payoff":
        sfx_entries.append({"type": "whoosh", "delay_ms": 0, "volume": 0.9})
        sfx_entries.append({"type": "ding", "delay_ms": 300, "volume": 0.7})
    elif vtype == "foreshadow":
        sfx_entries.append({"type": "whoosh", "delay_ms": 0, "volume": 0.6})

    valid = []
    for sfx in sfx_entries:
        sfx_file = os.path.join(sfx_dir, f"{sfx['type']}.mp3")
        if os.path.exists(sfx_file):
            valid.append({**sfx, "file": sfx_file})
        else:
            log_info(f"SFX manquant: {sfx['type']}")

    if not valid:
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        delayed = []
        for i, sfx in enumerate(valid):
            path = os.path.join(tmpdir, f"sfx_{i:02d}.mp3")
            delay = sfx["delay_ms"]
            vol = sfx["volume"]
            cmd = [
                "ffmpeg", "-y", "-i", sfx["file"],
                "-af", f"adelay={delay}|{delay},volume={vol}",
                "-t", str(total_duration),
                path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                delayed.append(path)

        if not delayed:
            return False

        if len(delayed) == 1:
            cmd = ["ffmpeg", "-y", "-i", delayed[0], "-t", str(total_duration), output_path]
        else:
            cmd = ["ffmpeg", "-y"]
            for f in delayed:
                cmd.extend(["-i", f])
            cmd.extend([
                "-filter_complex",
                f"amix=inputs={len(delayed)}:normalize=0",
                "-t", str(total_duration),
                output_path
            ])
        subprocess.run(cmd, check=True, capture_output=True)
    return True


def main():
    parser = argparse.ArgumentParser(
        description="D-F04 ASSEMBLY - Sous-titres + SFX + loop"
    )
    parser.add_argument("--input", required=True, help="Dossier IN/")
    parser.add_argument("--output", required=True, help="Dossier OUT/")
    parser.add_argument("--sfx-dir", required=True, help="Dossier SFX")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    final_dir = output_dir / OUTPUT_DIR_CLIPS
    final_dir.mkdir(parents=True, exist_ok=True)
    sfx_dir = Path(args.sfx_dir)

    clips_dir = input_dir / INPUT_CLIPS_DIR
    transcript_path = input_dir / INPUT_TRANSCRIPT
    cutlist_path = input_dir / INPUT_CUTLIST

    if not clips_dir.exists():
        log_fail(f"Dossier clips introuvable: {clips_dir}")
        sys.exit(1)
    if not transcript_path.exists():
        log_fail(f"Transcript introuvable: {transcript_path}")
        sys.exit(1)

    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript_data = json.load(f)
    with open(cutlist_path, "r", encoding="utf-8") as f:
        cutlist = json.load(f)

    moments = cutlist.get("moments", [])
    section(f"D-F04 ASSEMBLY - {len(moments)} clips a assembler")

    results = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for moment in moments:
            idx = moment["index"]
            start = moment["start_sec"]
            end = moment["end_sec"]
            vtype = moment.get("viral_type", "unknown")
            emotion = moment.get("emotion_mode", "wholesome")

            clip_path = clips_dir / f"clip_{idx:03d}.mp4"
            if not clip_path.exists():
                log_fail(f"Clip introuvable: {clip_path}")
                continue

            section(f"Clip {idx}: {vtype} ({emotion})")

            clip_duration = get_duration(clip_path)
            fps = get_fps(clip_path)
            log_ok(f"Duree: {clip_duration:.1f}s, {fps:.1f}fps")

            subtitle_path = os.path.join(tmpdir, f"sub_{idx:03d}.srt")
            clip_words = extract_clip_words(transcript_data, start, end)
            generate_srt(clip_words, subtitle_path)
            log_ok(f"Sous-titres: {len(clip_words)} mots")

            sfx_path = os.path.join(tmpdir, f"sfx_{idx:03d}.mp3")
            has_sfx = create_sfx_mix(moment, str(sfx_dir), fps, clip_duration, sfx_path)

            final_path = final_dir / f"clip_final_{idx:03d}.mp4"

            subs_filter = f"subtitles='{subtitle_path}':force_style='FontSize=24,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,BorderStyle=1,Outline=2'"

            if has_sfx:
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(clip_path),
                    "-i", sfx_path,
                    "-vf", subs_filter,
                    "-map", "0:v",
                    "-map", "0:a",
                    "-map", "1:a",
                    "-filter_complex", "[0:a]volume=1.0[va];[1:a]volume=0.8[sa];[va][sa]amix=inputs=2:normalize=0[aout]",
                    "-map", "[aout]",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                    "-c:a", "aac", "-b:a", "192k",
                    "-shortest",
                    "-movflags", "+faststart",
                    str(final_path)
                ]
            else:
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(clip_path),
                    "-vf", subs_filter,
                    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                    "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart",
                    str(final_path)
                ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                log_fail(f"Erreur assembly clip {idx}: {result.stderr[-300:]}")
                continue

            size_mb = final_path.stat().st_size // (1024 * 1024)
            log_ok(f"Clip final: {final_path.name} ({size_mb} MB)")

            results.append({
                "index": idx,
                "start_sec": start,
                "end_sec": end,
                "duration_sec": clip_duration,
                "viral_type": vtype,
                "emotion_mode": emotion,
                "subtitles_words": len(clip_words),
                "has_sfx": has_sfx,
                "output": f"{OUTPUT_DIR_CLIPS}/clip_final_{idx:03d}.mp4",
                "size_mb": size_mb,
            })

    manifest = {
        "clips_assembled": len(results),
        "clips": results,
    }
    manifest_path = output_dir / OUTPUT_MANIFEST
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 52)
    print(" D-F04 ASSEMBLY - MISSION ACCOMPLIE")
    print(f"  Clips finaux  : {len(results)}")
    print(f"  Avec SFX      : {sum(1 for r in results if r['has_sfx'])}")
    print(f"  Avec sous-titres: {sum(1 for r in results if r['subtitles_words'] > 0)}")
    print(f"  Dossier       : {OUTPUT_DIR_CLIPS}/")
    print("=" * 52)


if __name__ == "__main__":
    main()
