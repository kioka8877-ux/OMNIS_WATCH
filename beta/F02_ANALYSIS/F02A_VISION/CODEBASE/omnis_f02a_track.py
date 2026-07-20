"""
omnis_f02a_track.py — F02A Phase 2 : Tracking de Cible
=======================================================
MediaPipe tracking (visage, main, chien) sur CPU.
Genere tracking_data.json avec coordonnees normalisees [0-1].

Usage:
  python omnis_f02a_track.py --input /path/IN/ --output /path/OUT/ \
    --target face

Entree: video_coupee.mp4 (dans IN/)
Sortie: tracking_data.json (dans OUT/)

Dependances:
  mediapipe, opencv-python (pip install mediapipe opencv-python)
"""

import argparse
import json
import os
import sys
from pathlib import Path

# ── Constantes ──────────────────────────────────────────────────────────────

INPUT_FILENAME = "video_coupee.mp4"
OUTPUT_FILENAME = "tracking_data.json"
MANIFEST_FILENAME = "f01_manifest.json"

# ── Logging ─────────────────────────────────────────────────────────────────

def log_ok(msg): print(f"  [OK] {msg}")
def log_fail(msg): print(f"  [FAIL] {msg}")
def log_info(msg): print(f"  [...] {msg}")
def log_warn(msg): print(f"  [WARN] {msg}")

def section(title):
    bar = "─" * max(0, 50 - len(title))
    print(f"\n── {title} {bar}")

# ── Tracking MediaPipe ──────────────────────────────────────────────────────

def track_face(video_path, fps, total_frames):
    """Tracking de visage avec MediaPipe Face Detection."""
    import cv2
    import mediapipe as mp

    mp_detection = mp.solutions.face_detection
    tracks = []
    frames_processed = 0

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        log_fail(f"Impossible d'ouvrir la video: {video_path}")
        sys.exit(1)

    with mp_detection.FaceDetection(
        model_selection=1, min_detection_confidence=0.5
    ) as detector:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = detector.process(rgb)

            if results.detections:
                # Prendre la detection avec la plus haute confiance
                best = max(results.detections, key=lambda d: d.score[0])
                bbox = best.location_data.relative_bounding_box
                # Centre de la bounding box en coordonnees normalisees
                cx = bbox.xmin + bbox.width / 2
                cy = bbox.ymin + bbox.height / 2
                tracks.append({
                    "frame": frames_processed,
                    "x": round(max(0.0, min(1.0, cx)), 4),
                    "y": round(max(0.0, min(1.0, cy)), 4),
                    "confidence": round(best.score[0], 3),
                    "bbox_width": round(bbox.width, 4),
                    "bbox_height": round(bbox.height, 4)
                })
            else:
                # Pas de detection — on garde la derniere position connue
                if tracks:
                    last = tracks[-1].copy()
                    last["frame"] = frames_processed
                    last["confidence"] = 0.0
                    tracks.append(last)
                else:
                    tracks.append({
                        "frame": frames_processed,
                        "x": 0.5, "y": 0.5,
                        "confidence": 0.0
                    })

            frames_processed += 1

    cap.release()
    return tracks, frames_processed

def track_hand(video_path, fps, total_frames):
    """Tracking de main avec MediaPipe Hand Tracking."""
    import cv2
    import mediapipe as mp

    mp_hands = mp.solutions.hands
    tracks = []
    frames_processed = 0

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        log_fail(f"Impossible d'ouvrir la video: {video_path}")
        sys.exit(1)

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as hands:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            if results.multi_hand_landmarks:
                # Prendre la premiere main
                hand = results.multi_hand_landmarks[0]
                # Centre de la paume (landmark 0 = wrist)
                cx = hand.landmark[0].x
                cy = hand.landmark[0].y
                tracks.append({
                    "frame": frames_processed,
                    "x": round(max(0.0, min(1.0, cx)), 4),
                    "y": round(max(0.0, min(1.0, cy)), 4),
                    "confidence": 0.9  # MediaPipe hands ne retourne pas de score direct
                })
            else:
                if tracks:
                    last = tracks[-1].copy()
                    last["frame"] = frames_processed
                    last["confidence"] = 0.0
                    tracks.append(last)
                else:
                    tracks.append({
                        "frame": frames_processed,
                        "x": 0.5, "y": 0.5,
                        "confidence": 0.0
                    })

            frames_processed += 1

    cap.release()
    return tracks, frames_processed

def track_object(video_path, target_label, fps, total_frames):
    """
    Tracking d'objet (chien, etc.) avec MediaPipe Object Detection.
    Utilise EfficientDet-Lite0 (COCO labels).
    """
    import cv2
    import mediapipe as mp

    mp_objectron = mp.solutions.objectron
    # Note: MediaPipe Object Detection via solutions.object_detection
    mp_detection = mp.solutions.object_detection

    tracks = []
    frames_processed = 0

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        log_fail(f"Impossible d'ouvrir la video: {video_path}")
        sys.exit(1)

    with mp_detection.ObjectDetection(
        model_selection=0,  # 0 = low-latency, 1 = high accuracy
        min_detection_confidence=0.5
    ) as detector:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = detector.process(rgb)

            if results.detections:
                # Filtrer par label (ex: "dog")
                best = None
                best_score = 0
                for det in results.detections:
                    label = det.categories[0].category_name
                    if label == target_label:
                        if det.score[0] > best_score:
                            best = det
                            best_score = det.score[0]

                if best:
                    bbox = best.location_data.relative_bounding_box
                    cx = bbox.xmin + bbox.width / 2
                    cy = bbox.ymin + bbox.height / 2
                    tracks.append({
                        "frame": frames_processed,
                        "x": round(max(0.0, min(1.0, cx)), 4),
                        "y": round(max(0.0, min(1.0, cy)), 4),
                        "confidence": round(best.score[0], 3),
                        "bbox_width": round(bbox.width, 4),
                        "bbox_height": round(bbox.height, 4),
                        "label": target_label
                    })
                else:
                    # Detection trouvee mais pas le bon label
                    if tracks:
                        last = tracks[-1].copy()
                        last["frame"] = frames_processed
                        last["confidence"] = 0.0
                        tracks.append(last)
                    else:
                        tracks.append({
                            "frame": frames_processed,
                            "x": 0.5, "y": 0.5,
                            "confidence": 0.0
                        })
            else:
                if tracks:
                    last = tracks[-1].copy()
                    last["frame"] = frames_processed
                    last["confidence"] = 0.0
                    tracks.append(last)
                else:
                    tracks.append({
                        "frame": frames_processed,
                        "x": 0.5, "y": 0.5,
                        "confidence": 0.0
                    })

            frames_processed += 1

    cap.release()
    return tracks, frames_processed

# ── Lissage ─────────────────────────────────────────────────────────────────

def smooth_tracks(tracks, window=5):
    """
    Lissage des coordonnees avec une moyenne mobile.
    Reduit le jitter du tracking.
    """
    if len(tracks) < window:
        return tracks

    smoothed = []
    half = window // 2
    for i, track in enumerate(tracks):
        start = max(0, i - half)
        end = min(len(tracks), i + half + 1)
        window_tracks = tracks[start:end]

        # Moyenne ponderee par confiance
        total_weight = sum(t["confidence"] for t in window_tracks)
        if total_weight == 0:
            sx, sy = track["x"], track["y"]
        else:
            sx = sum(t["x"] * t["confidence"] for t in window_tracks) / total_weight
            sy = sum(t["y"] * t["confidence"] for t in window_tracks) / total_weight

        new_track = track.copy()
        new_track["x"] = round(sx, 4)
        new_track["y"] = round(sy, 4)
        smoothed.append(new_track)

    return smoothed

# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="F02A TRACKING — MediaPipe tracking de cible"
    )
    parser.add_argument("--input", required=True, help="Dossier IN/")
    parser.add_argument("--output", required=True, help="Dossier OUT/")
    parser.add_argument("--target", required=True,
                        choices=["face", "hand", "dog", "cat", "person"],
                        help="Type de cible a tracker")
    parser.add_argument("--smooth", type=int, default=5,
                        help="Fenetre de lissage (0 = pas de lissage)")

    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    video_path = input_dir / INPUT_FILENAME
    manifest_path = input_dir / MANIFEST_FILENAME

    # ── Verifications ──
    section("Verification des entrees")

    if not video_path.exists():
        log_fail(f"Video introuvable: {video_path}")
        sys.exit(1)
    log_ok(f"Video: {video_path}")

    # Lire le manifest de F01
    fps = 30
    total_frames = 0
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)
        fps = manifest["meta"]["fps"]
        total_frames = manifest["meta"]["total_frames"]
        log_ok(f"Manifest F01: {fps}fps, {total_frames} frames")
    else:
        log_warn("Manifest F01 non trouve — utilisation des valeurs par defaut")

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    # ── Tracking ──
    section(f"Tracking MediaPipe — cible: {args.target}")

    target_label = None
    if args.target == "face":
        tracks, frames_processed = track_face(video_path, fps, total_frames)
    elif args.target == "hand":
        tracks, frames_processed = track_hand(video_path, fps, total_frames)
    elif args.target in ("dog", "cat", "person"):
        target_label = args.target
        tracks, frames_processed = track_object(
            video_path, target_label, fps, total_frames
        )
    else:
        log_fail(f"Cible non supportee: {args.target}")
        sys.exit(1)

    log_ok(f"Frames traitees: {frames_processed}")
    log_ok(f"Tracks generes: {len(tracks)}")

    # Stats de confiance
    confidences = [t["confidence"] for t in tracks if t["confidence"] > 0]
    if confidences:
        avg_conf = sum(confidences) / len(confidences)
        detection_rate = len(confidences) / len(tracks)
        log_ok(f"Confiance moyenne: {avg_conf:.3f}")
        log_ok(f"Taux de detection: {detection_rate:.1%}")
    else:
        log_warn("Aucune detection avec confiance > 0")

    # ── Lissage ──
    if args.smooth > 0 and len(tracks) > 0:
        section("Lissage des tracks")
        tracks = smooth_tracks(tracks, window=args.smooth)
        log_ok(f"Lissage applique (fenetre={args.smooth})")

    # ── Output ──
    section("Generation du tracking_data.json")

    output_data = {
        "target_type": args.target,
        "target_label": target_label,
        "fps": fps,
        "total_frames": frames_processed,
        "smooth_window": args.smooth,
        "tracks": tracks
    }

    output_path = output_dir / OUTPUT_FILENAME
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    size_kb = os.path.getsize(output_path) / 1024
    log_ok(f"tracking_data.json ecrit ({size_kb:.1f} KB)")

    # ── Resume ──
    print()
    print("═" * 52)
    print(" F02A TRACKING — MISSION ACCOMPLIE")
    print(f" Cible     : {args.target}")
    print(f" Frames    : {frames_processed}")
    print(f" Tracks    : {len(tracks)}")
    if confidences:
        print(f" Confiance : {avg_conf:.3f} (moyenne)")
        print(f" Detection : {detection_rate:.1%}")
    print(f" Lissage   : {args.smooth if args.smooth > 0 else 'non'}")
    print(f" Fichier   : {OUTPUT_FILENAME}")
    print("═" * 52)
    print()

if __name__ == "__main__":
    main()
