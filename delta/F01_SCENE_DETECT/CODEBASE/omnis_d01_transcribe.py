"""
omnis_d01_transcribe.py - D-F01 TRANSCRIPTION
=============================================
Transcrit l'audio de la video source mot par mot via faster-whisper.

Usage:
  python omnis_d01_transcribe.py --input /path/IN/ --output /path/OUT/

Entree: IN/video_source.mp4
Sortie: OUT/transcript.json (mots avec timestamps word-level)
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

INPUT_FILENAME = "video_source.mp4"
OUTPUT_FILENAME = "transcript.json"


def log_ok(msg): print(f"  [OK] {msg}")
def log_fail(msg): print(f"  [FAIL] {msg}")
def log_info(msg): print(f"  [...] {msg}")

def section(title):
    bar = "-" * max(0, 50 - len(title))
    print(f"\n-- {title} {bar}")


def extract_audio(video_path, output_audio_path):
    """Extrait l'audio de la video en WAV 16kHz mono."""
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(output_audio_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def transcribe_audio(audio_path, model_size="base"):
    """Transcrit l'audio via faster-whisper avec timestamps word-level."""
    from faster_whisper import WhisperModel

    log_info(f"Chargement du modele Whisper ({model_size})...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    log_info("Transcription en cours...")
    segments, info = model.transcribe(
        str(audio_path),
        word_timestamps=True,
        vad_filter=True,
        beam_size=5,
    )

    words = []
    for segment in segments:
        if segment.words:
            for word in segment.words:
                words.append({
                    "word": word.word.strip(),
                    "start": round(word.start, 3),
                    "end": round(word.end, 3),
                    "confidence": round(word.probability, 3),
                })

    log_ok(f"Transcription: {len(words)} mots, langue={info.language}")
    return words, info.language


def main():
    parser = argparse.ArgumentParser(
        description="D-F01 TRANSCRIPTION - faster-whisper word-level"
    )
    parser.add_argument("--input", required=True, help="Dossier IN/")
    parser.add_argument("--output", required=True, help="Dossier OUT/")
    parser.add_argument("--model", default="base",
                        choices=["tiny", "base", "small", "medium", "large"],
                        help="Taille du modele Whisper (defaut base)")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    video_path = input_dir / INPUT_FILENAME
    if not video_path.exists():
        log_fail(f"Video introuvable: {video_path}")
        sys.exit(1)

    section("D-F01 TRANSCRIPTION - Demarrage")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio_path = Path(tmp.name)

    try:
        section("Extraction audio")
        extract_audio(video_path, audio_path)
        log_ok(f"Audio extrait: {audio_path}")

        section("Transcription faster-whisper")
        words, language = transcribe_audio(audio_path, args.model)

    finally:
        if audio_path.exists():
            audio_path.unlink()

    output = {
        "language": language,
        "word_count": len(words),
        "words": words,
    }
    output_path = output_dir / OUTPUT_FILENAME
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    total_duration = words[-1]["end"] if words else 0

    print()
    print("=" * 52)
    print(" D-F01 TRANSCRIPTION - MISSION ACCOMPLIE")
    print(f"  Mots  : {len(words)}")
    print(f"  Langue: {language}")
    print(f"  Duree : {total_duration:.1f}s")
    print(f"  Fichier: {OUTPUT_FILENAME}")
    print("=" * 52)


if __name__ == "__main__":
    main()
