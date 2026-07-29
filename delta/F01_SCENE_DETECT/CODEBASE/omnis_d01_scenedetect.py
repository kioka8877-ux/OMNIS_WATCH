"""
omnis_d01_scenedetect.py - D-F01 SCENE DETECT
=============================================
Detecte les bornes de scenes dans la video source via PySceneDetect.

Usage:
  python omnis_d01_scenedetect.py --input /path/IN/ --output /path/OUT/

Entree: IN/video_source.mp4 + IN/d00_manifest.json
Sortie: OUT/scenes.json (tableau de scenes avec start_sec, end_sec, duration_sec)
"""
import argparse
import json
import os
import sys
from pathlib import Path

INPUT_FILENAME = "video_source.mp4"
MANIFEST_FILENAME = "d00_manifest.json"
OUTPUT_FILENAME = "scenes.json"


def log_ok(msg): print(f"  [OK] {msg}")
def log_fail(msg): print(f"  [FAIL] {msg}")
def log_info(msg): print(f"  [...] {msg}")

def section(title):
    bar = "-" * max(0, 50 - len(title))
    print(f"\n-- {title} {bar}")


def detect_scenes(video_path, threshold=27.0, min_scene_len_sec=2.0):
    """Detecte les scenes via PySceneDetect."""
    from scenedetect import detect, ContentDetector

    section(f"Detection de scenes: {os.path.basename(video_path)}")
    log_info(f"Seuil: {threshold}, scene min: {min_scene_len_sec}s")

    scene_list = detect(
        str(video_path),
        ContentDetector(threshold=threshold),
        min_scene_len=int(min_scene_len_sec * 30),
        show_progress=True,
    )

    scenes = []
    for i, (start, end) in enumerate(scene_list):
        start_sec = start.get_seconds()
        end_sec = end.get_seconds()
        scenes.append({
            "scene_index": i,
            "start_sec": round(start_sec, 3),
            "end_sec": round(end_sec, 3),
            "duration_sec": round(end_sec - start_sec, 3),
            "start_frame": start.get_frames(),
            "end_frame": end.get_frames(),
        })

    if not scenes:
        log_warn("Aucune scene detectee - creation d'une scene unique")
        scenes.append({
            "scene_index": 0,
            "start_sec": 0,
            "end_sec": 0,
            "duration_sec": 0,
            "start_frame": 0,
            "end_frame": 0,
        })

    log_ok(f"{len(scenes)} scenes detectees")
    return scenes


log_warn = log_info


def main():
    parser = argparse.ArgumentParser(
        description="D-F01 SCENE DETECT - Detection de bornes"
    )
    parser.add_argument("--input", required=True, help="Dossier IN/")
    parser.add_argument("--output", required=True, help="Dossier OUT/")
    parser.add_argument("--threshold", type=float, default=27.0,
                        help="Seuil de detection (defaut 27.0)")
    parser.add_argument("--min-scene-len", type=float, default=2.0,
                        help="Duree minimale d'une scene en secondes (defaut 2.0)")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    video_path = input_dir / INPUT_FILENAME
    if not video_path.exists():
        log_fail(f"Video introuvable: {video_path}")
        sys.exit(1)

    section("D-F01 SCENE DETECT - Demarrage")

    scenes = detect_scenes(video_path, args.threshold, args.min_scene_len)

    output_path = output_dir / OUTPUT_FILENAME
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"scenes": scenes, "scene_count": len(scenes)}, f,
                  ensure_ascii=False, indent=2)

    total_duration = sum(s["duration_sec"] for s in scenes)
    avg_duration = total_duration / len(scenes) if scenes else 0

    print()
    print("=" * 52)
    print(" D-F01 SCENE DETECT - MISSION ACCOMPLIE")
    print(f"  Scenes   : {len(scenes)}")
    print(f"  Duree totale : {total_duration:.1f}s")
    print(f"  Duree moyenne: {avg_duration:.1f}s")
    print(f"  Fichier  : {OUTPUT_FILENAME}")
    print("=" * 52)


if __name__ == "__main__":
    main()
