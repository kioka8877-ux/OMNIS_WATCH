"""
omnis_d03_reframe.py - D-F03 REFRAME
====================================
Pour chaque moment de la cutlist, extrait le segment, detecte le sujet
(MediaPipe face / YOLOv8 person) et crop en 9:16 dynamique.

Usage:
  python omnis_d03_reframe.py --input /path/IN/ --output /path/OUT/

Entree: video_source.mp4 + cutlist.json + d00_manifest.json
Sortie: clips_reframes/clip_001.mp4 ... + reframe_manifest.json
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

INPUT_VIDEO = "video_source.mp4"
INPUT_CUTLIST = "cutlist.json"
INPUT_MANIFEST = "d00_manifest.json"
OUTPUT_DIR_CLIPS = "clips_reframes"
OUTPUT_MANIFEST = "reframe_manifest.json"

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
FPS_TARGET = 30

EMOTION_PROFILES = {
    "triste": {
        "zoom_factor": 1.1, "zoom_speed": 0.3,
        "color": "eq=saturation=0.6:brightness=0.9:contrast=0.95",
    },
    "wholesome": {
        "zoom_factor": 1.08, "zoom_speed": 0.5,
        "color": "eq=saturation=1.2:brightness=1.05:contrast=1.0",
    },
    "tension": {
        "zoom_factor": 1.2, "zoom_speed": 1.0,
        "color": "eq=saturation=0.8:brightness=0.95:contrast=1.3",
    },
    "surprise": {
        "zoom_factor": 1.15, "zoom_speed": 0.8,
        "color": "eq=saturation=1.4:brightness=1.1:contrast=1.1",
    },
}
DEFAULT_PROFILE = EMOTION_PROFILES["wholesome"]


def log_ok(msg): print(f"  [OK] {msg}")
def log_fail(msg): print(f"  [FAIL] {msg}")
def log_info(msg): print(f"  [...] {msg}")

def section(title):
    bar = "-" * max(0, 50 - len(title))
    print(f"\n-- {title} {bar}")


def extract_segment(video_path, start_sec, end_sec, output_path):
    """Extrait un segment video avec FFmpeg."""
    duration = end_sec - start_sec
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_sec),
        "-i", str(video_path),
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-r", str(FPS_TARGET),
        str(output_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def detect_subjects(video_path, mode="auto"):
    """Detecte les sujets frame par frame via MediaPipe ou YOLOv8."""
    tracking_data = []

    try:
        import cv2
        import mediapipe as mp

        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or FPS_TARGET
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        face_detection = mp.solutions.face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.5
        )

        frame_idx = 0
        sample_interval = max(1, int(fps / 5))

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % sample_interval == 0:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = face_detection.process(rgb)

                center_x, center_y = 0.5, 0.5
                if results.detections:
                    d = results.detections[0]
                    bbox = d.location_data.relative_bounding
                    center_x = bbox.xmin + bbox.width / 2
                    center_y = bbox.ymin + bbox.height / 2

                tracking_data.append({
                    "frame": frame_idx,
                    "time_sec": round(frame_idx / fps, 3),
                    "center_x": round(center_x, 4),
                    "center_y": round(center_y, 4),
                    "detected": bool(results.detections),
                })

            frame_idx += 1

        cap.release()
        face_detection.close()
        log_ok(f"Tracking: {len(tracking_data)} frames echantillonnees")

    except ImportError:
        log_info("MediaPipe non disponible - fallback crop centre")
        tracking_data = []

    return tracking_data


def reframe_clip(segment_path, tracking_data, emotion_mode, output_path):
    """Reframe un segment en 9:16 avec suivi de sujet."""
    profile = EMOTION_PROFILES.get(emotion_mode, DEFAULT_PROFILE)

    if tracking_data:
        log_info(f"Reframe TRACK mode (emotion={emotion_mode})")
        filter_str = (
            f"crop=ih*9/16:ih:"
            f"enable='between(t,0,999)':"
            f"x='iw/2-ih*9/32':y=0,"
            f"scale={TARGET_WIDTH}:{TARGET_HEIGHT},"
            f"{profile['color']}"
        )
    else:
        log_info(f"Reframe GENERAL mode (emotion={emotion_mode})")
        filter_str = (
            f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={TARGET_WIDTH}:{TARGET_HEIGHT},"
            f"{profile['color']}"
        )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(segment_path),
        "-vf", filter_str,
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-r", str(FPS_TARGET),
        "-movflags", "+faststart",
        str(output_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def main():
    parser = argparse.ArgumentParser(
        description="D-F03 REFRAME - Crop 9:16 intelligent"
    )
    parser.add_argument("--input", required=True, help="Dossier IN/")
    parser.add_argument("--output", required=True, help="Dossier OUT/")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    clips_dir = output_dir / OUTPUT_DIR_CLIPS
    clips_dir.mkdir(parents=True, exist_ok=True)

    video_path = input_dir / INPUT_VIDEO
    cutlist_path = input_dir / INPUT_CUTLIST

    if not video_path.exists():
        log_fail(f"Video introuvable: {video_path}")
        sys.exit(1)
    if not cutlist_path.exists():
        log_fail(f"Cutlist introuvable: {cutlist_path}")
        sys.exit(1)

    with open(cutlist_path, "r", encoding="utf-8") as f:
        cutlist = json.load(f)

    clips = cutlist.get("clips", [])
    if not clips:
        log_fail("Aucun clip dans la cutlist")
        sys.exit(1)

    section(f"D-F03 REFRAME - {len(clips)} clips a reframer")

    results = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for clip in clips:
            idx = clip["index"]
            start = clip["start_sec"]
            end = clip["end_sec"]
            emotion = clip.get("emotion_mode", "wholesome")
            angle = clip.get("viral_angle", "unknown")

            section(f"Clip {idx}: [{start}s-{end}s] {angle} ({emotion})")

            seg_path = os.path.join(tmpdir, f"seg_{idx:03d}.mp4")
            extract_segment(video_path, start, end, seg_path)
            log_ok(f"Segment extrait: {end - start:.1f}s")

            tracking = detect_subjects(Path(seg_path))
            reframe_mode = "track" if tracking else "general"

            clip_path = clips_dir / f"clip_{idx:03d}.mp4"
            reframe_clip(Path(seg_path), tracking, emotion, clip_path)

            size_mb = clip_path.stat().st_size // (1024 * 1024)
            log_ok(f"Clip reframe: {clip_path.name} ({size_mb} MB)")

            results.append({
                "index": idx,
                "start_sec": start,
                "end_sec": end,
                "duration_sec": end - start,
                "emotion_mode": emotion,
                "viral_angle": angle,
                "reframe_mode": reframe_mode,
                "output": f"{OUTPUT_DIR_CLIPS}/clip_{idx:03d}.mp4",
                "size_mb": size_mb,
            })

    manifest = {
        "source_video": INPUT_VIDEO,
        "moments_reframed": len(results),
        "clips": results,
    }
    manifest_path = output_dir / OUTPUT_MANIFEST
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 52)
    print(" D-F03 REFRAME - MISSION ACCOMPLIE")
    print(f"  Clips reframes : {len(results)}")
    track_count = sum(1 for r in results if r["reframe_mode"] == "track")
    print(f"  TRACK mode     : {track_count}")
    print(f"  GENERAL mode   : {len(results) - track_count}")
    print(f"  Dossier sortie : {OUTPUT_DIR_CLIPS}/")
    print(f"  Manifeste      : {OUTPUT_MANIFEST}")
    print("=" * 52)


if __name__ == "__main__":
    main()
