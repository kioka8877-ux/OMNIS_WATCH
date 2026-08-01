#!/usr/bin/env python3
"""
generate_test_data.py — Génère les données de test pour D04 TIMING
"""
import json
import subprocess
import sys
from pathlib import Path

def create_transcript_json(output_path):
    """Crée transcript.json avec mots + timestamps pour 3 clips."""
    # Clip 1: 0-10s, Clip 2: 15-30s, Clip 3: 35-55s
    words = []
    
    # Clip 1: "Bonjour et bienvenue sur Omnis Watch"
    clip1_words = [
        ("Bonjour", 0.0, 0.5),
        ("et", 0.5, 0.6),
        ("bienvenue", 0.6, 1.2),
        ("sur", 1.2, 1.4),
        ("Omnis", 1.4, 1.8),
        ("Watch", 1.8, 2.2),
        ("aujourd'hui", 2.5, 3.2),
        ("on", 3.2, 3.3),
        ("va", 3.3, 3.5),
        ("découvrir", 3.5, 4.0),
        ("les", 4.0, 4.2),
        ("nouveautés", 4.2, 5.0),
    ]
    
    # Clip 2: "Ce produit révolutionne l'expérience utilisateur"
    clip2_words = [
        ("Ce", 15.0, 15.2),
        ("produit", 15.2, 15.8),
        ("révolutionne", 15.8, 16.6),
        ("l'expérience", 17.0, 17.8),
        ("utilisateur", 17.8, 18.6),
        ("avec", 19.0, 19.2),
        ("son", 19.2, 19.5),
        ("design", 19.5, 20.2),
        ("innovant", 20.2, 21.0),
    ]
    
    # Clip 3: "La qualité est exceptionnelle et le prix imbattable"
    clip3_words = [
        ("La", 35.0, 35.2),
        ("qualité", 35.2, 35.9),
        ("est", 35.9, 36.1),
        ("exceptionnelle", 36.1, 37.0),
        ("et", 37.5, 37.7),
        ("le", 37.7, 37.9),
        ("prix", 37.9, 38.4),
        ("est", 38.4, 38.6),
        ("imbattable", 38.6, 39.5),
    ]
    
    for word, start, end in clip1_words:
        words.append({"word": word, "start": start, "end": end, "is_strong": False})
    for word, start, end in clip2_words:
        words.append({"word": word, "start": start, "end": end, "is_strong": False})
    for word, start, end in clip3_words:
        words.append({"word": word, "start": start, "end": end, "is_strong": False})
    
    transcript = {
        "word_count": len(words),
        "words": words
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(transcript, f, ensure_ascii=False, indent=2)
    
    print(f"  Created: {output_path} ({len(words)} words)")
    return transcript


def create_cutlist_json(output_path):
    """Crée cutlist.json avec 3 clips."""
    cutlist = {
        "clips": [
            {
                "index": 1,
                "start_sec": 0.0,
                "end_sec": 10.0,
                "description": "Introduction"
            },
            {
                "index": 2,
                "start_sec": 15.0,
                "end_sec": 30.0,
                "description": "Produit révolutionnaire"
            },
            {
                "index": 3,
                "start_sec": 35.0,
                "end_sec": 55.0,
                "description": "Qualité et prix"
            }
        ]
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cutlist, f, ensure_ascii=False, indent=2)
    
    print(f"  Created: {output_path} ({len(cutlist['clips'])} clips)")
    return cutlist


def create_test_videos(input_dir):
    """Crée 3 vidéos de test avec FFmpeg (1 frame chaque)."""
    # Utiliser une vidéo de test simple ou créer avec FFmpeg
    for i in range(1, 4):
        output_path = input_dir / f"clip_{i:03d}.mp4"
        if output_path.exists():
            print(f"  Skipping: {output_path} (exists)")
            continue
        
        # Créer une vidéo de test de 5 secondes
        # Utiliser le pattern testsrc2 pour générer une vidéo de test
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"testsrc2=size=1080x1920:rate=30:duration=5",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-t", "5",
            str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"  Created: {output_path}")
            else:
                print(f"  ERROR creating {output_path}: {result.stderr[:100]}")
        except Exception as e:
            print(f"  ERROR: {e}")
            # Créer un fichier vide si FFmpeg échoue
            output_path.write_text("placeholder")


def main():
    print("=== GÉNÉRATION DONNÉES DE TEST ===\n")
    
    # Répertoires
    timing_in = Path("delta/F04_TIMING/IN")
    timing_in.mkdir(parents=True, exist_ok=True)
    
    # Créer transcript.json et cutlist.json
    print("Creating JSON files...")
    create_transcript_json(timing_in / "transcript.json")
    create_cutlist_json(timing_in / "cutlist.json")
    
    # Créer les vidéos de test
    print("\nCreating test videos...")
    create_test_videos(timing_in)
    
    print("\n=== DONNÉES DE TEST CRÉÉES ===")


if __name__ == "__main__":
    main()
