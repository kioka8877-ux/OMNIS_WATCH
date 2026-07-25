"""
omnis_f02b_oracle.py — F02B V2 : Synchronisateur Voix Off
==========================================================
Lit timing.json (de F01B Whisper) et genere codex.json avec:
  - Sous-titres synchronises sur les timestamps Whisper
  - Zooms automatiques sur les mots forts (is_strong: true)
  - SFX synchronises sur les transitions de sous-titres
  - Colorimetrie selon le mode emotionnel

Usage:
  # Etape 1: Preparer le prompt
  python omnis_f02b_oracle.py --input /path/IN/ --output /path/OUT/ \
    --emotion-mode WHOLESOME --prepare

  # Etape 2: L'Oracle (sandbox AI) genere le codex base sur le prompt
  #           (se fait via le chat, pas en CLI)

  # Etape 3: Valider et ecrire le codex
  python omnis_f02b_oracle.py --input /path/IN/ --output /path/OUT/ \
    --emotion-mode WHOLESOME --validate /path/to/generated_codex.json

  # Mode auto: genere le codex automatiquement sans Oracle (groupage simple)
  python omnis_f02b_oracle.py --input /path/IN/ --output /path/OUT/ \
    --emotion-mode WHOLESOME --auto

  # Generer le script voix off (Oracle sandbox AI)
  python omnis_f02b_oracle.py --input /path/IN/ --output /path/OUT/ \
    --emotion-mode WHOLESOME --generate-script

Entree V2: timing.json + narrative.txt (optionnel) + f01_manifest.json
Sortie: codex.json (ou script_voix_off.txt si --generate-script)
"""

import argparse
import json
import os
import sys
from pathlib import Path

# ── Constantes ────────────────────────────────────────────────────────────────

TIMING_FILENAME = "timing.json"
NARRATIVE_FILENAME = "narrative.txt"
MANIFEST_FILENAME = "f01_manifest.json"
OUTPUT_FILENAME = "codex.json"
METAPROMPT_PATH = "../../METAPROMPTS/META_F02B_EMOTION.md"

# Presets de colorimetrie par mode emotionnel
COLOR_PRESETS = {
    "TRISTE": {
        "name": "cold_desaturated",
        "css_filter": "contrast(0.9) saturate(0.7) brightness(0.95)",
    },
    "WHOLESOME": {
        "name": "warm_vibrant",
        "css_filter": "contrast(1.3) saturate(1.4) brightness(1.05)",
    },
    "TENSION": {
        "name": "dark_contrast",
        "css_filter": "contrast(1.5) saturate(0.8) brightness(0.9)",
    },
    "SURPRISE": {
        "name": "hyper_vibrant",
        "css_filter": "contrast(1.4) saturate(1.6) brightness(1.1)",
    },
}

# Parametres de zoom par mode
ZOOM_PARAMS = {
    "TRISTE": {"min_scale": 1.1, "max_scale": 1.3, "ramp_frames": 10},
    "WHOLESOME": {"min_scale": 1.1, "max_scale": 1.4, "ramp_frames": 6},
    "TENSION": {"min_scale": 1.2, "max_scale": 1.5, "ramp_frames": 4},
    "SURPRISE": {"min_scale": 1.3, "max_scale": 1.6, "ramp_frames": 3},
}

# Volume SFX par mode
SFX_VOLUME = {
    "TRISTE": {"keyboard": 0.2, "whoosh": 0.15},
    "WHOLESOME": {"keyboard": 0.4, "whoosh": 0.3},
    "TENSION": {"keyboard": 0.5, "whoosh": 0.4},
    "SURPRISE": {"keyboard": 0.5, "whoosh": 0.5},
}

# ── Logging ───────────────────────────────────────────────────────────────────

def log_ok(msg): print(f"  [OK] {msg}")
def log_fail(msg): print(f"  [FAIL] {msg}")
def log_info(msg): print(f"  [...] {msg}")
def log_warn(msg): print(f"  [WARN] {msg}")

def section(title):
    bar = "─" * max(0, 50 - len(title))
    print(f"\n── {title} {bar}")

# ── Auto-generate codex from timing.json ──────────────────────────────────────

def auto_generate_codex(timing, emotion_mode, video_info):
    """
    Genere le codex.json automatiquement a partir de timing.json.
    Groupage simple: regroupe les mots par segments Whisper.
    Zooms sur mots forts. SFX sur transitions.
    """
    fps = timing["meta"]["fps"]
    total_frames = timing["meta"]["total_frames"]
    words = timing.get("words", [])
    segments = timing.get("segments", [])

    color_preset = COLOR_PRESETS.get(emotion_mode, COLOR_PRESETS["WHOLESOME"])
    zoom_config = ZOOM_PARAMS.get(emotion_mode, ZOOM_PARAMS["WHOLESOME"])
    sfx_vol = SFX_VOLUME.get(emotion_mode, SFX_VOLUME["WHOLESOME"])

    # ── Sous-titres: utiliser les segments comme blocs ──
    text_overlays = []
    for seg in segments:
        text = seg["text"].strip()
        if not text:
            continue

        # Limiter a 5 mots par bloc (diviser si necessaire)
        seg_words = text.split()
        if len(seg_words) <= 5:
            text_overlays.append({
                "id": f"txt_{len(text_overlays):02d}",
                "content": text,
                "start_frame": seg["start_frame"],
                "end_frame": seg["end_frame"],
                "animation": "word_by_word",
                "emotion_weight": "neutral",
                "font": "Anton, Arial Black, sans-serif",
                "size": 96,
                "color": "#FFFFFF",
                "stroke_color": "#000000",
                "stroke_width": 3,
                "shadow": "2px 4px 8px rgba(0,0,0,0.8)",
                "position": "center_bottom",
                "letter_spacing": "0em",
                "glow_intensity": 0,
                "depth_3d": 0,
            })
        else:
            # Diviser en sous-blocs de 3-5 mots
            chunk_size = 4
            seg_word_list = seg.get("words", [])
            for i in range(0, len(seg_word_list), chunk_size):
                chunk_words = seg_word_list[i:i+chunk_size]
                if not chunk_words:
                    continue
                chunk_text = " ".join(w["word"] for w in chunk_words)
                start_f = chunk_words[0]["start_frame"]
                end_f = chunk_words[-1]["end_frame"]
                text_overlays.append({
                    "id": f"txt_{len(text_overlays):02d}",
                    "content": chunk_text,
                    "start_frame": start_f,
                    "end_frame": end_f,
                    "animation": "word_by_word",
                    "emotion_weight": "neutral",
                    "font": "Anton, Arial Black, sans-serif",
                    "size": 96,
                    "color": "#FFFFFF",
                    "stroke_color": "#000000",
                    "stroke_width": 3,
                    "shadow": "2px 4px 8px rgba(0,0,0,0.8)",
                    "position": "center_bottom",
                    "letter_spacing": "0em",
                    "glow_intensity": 0,
                    "depth_3d": 0,
                })

    # ── Zooms: sur chaque mot fort ──
    zoom_keyframes = []
    strong_words = [w for w in words if w.get("is_strong", False)]

    for sw in strong_words:
        start_f = sw["start_frame"]
        end_f = sw["end_frame"]
        ramp = zoom_config["ramp_frames"]
        peak_scale = zoom_config["max_scale"]

        # Zoom progressif: start → peak → retour
        zoom_keyframes.append({
            "frame": start_f,
            "scale": 1.0,
            "target_x": 0.5,
            "target_y": 0.5,
        })
        zoom_keyframes.append({
            "frame": start_f + ramp,
            "scale": peak_scale,
            "target_x": 0.5,
            "target_y": 0.4,
        })
        if end_f > start_f + ramp:
            zoom_keyframes.append({
                "frame": end_f,
                "scale": 1.0,
                "target_x": 0.5,
                "target_y": 0.5,
            })

    # Trier par frame
    zoom_keyframes.sort(key=lambda z: z["frame"])

    # ── SFX: keyboard sur chaque sous-titre, whoosh sur chaque zoom ──
    sfx_timeline = []

    for overlay in text_overlays:
        sfx_timeline.append({
            "frame": overlay["start_frame"],
            "type": "keyboard",
            "volume": sfx_vol["keyboard"],
        })

    for zoom in zoom_keyframes:
        if zoom["scale"] > 1.1:  # seulement sur les pics de zoom
            sfx_timeline.append({
                "frame": zoom["frame"],
                "type": "whoosh",
                "volume": sfx_vol["whoosh"],
            })

    # ── Construction du codex ──
    codex = {
        "version": "2.0",
        "emotion_mode": emotion_mode,
        "narrative_arc": "voice_off_driven",
        "audio_source": "audio_clean.mp3",
        "video": {
            "source": video_info.get("source", "video_coupee.mp4"),
            "fps": fps,
            "total_frames": total_frames,
            "width": video_info.get("width", 1080),
            "height": video_info.get("height", 1920),
        },
        "text_overlays": text_overlays,
        "zoom_keyframes": zoom_keyframes,
        "color_preset": color_preset["name"],
        "color_css_filter": color_preset["css_filter"],
        "enhance_4k": True,
        "vignette": 0.35,
        "sharpening": 70,
        "denoising": 30,
        "sfx_timeline": sfx_timeline,
        "tracking_source": "tracking_data.json",
        "grain_intensity": 0.2,
    }

    return codex

# ── Prepare prompt for Oracle ─────────────────────────────────────────────────

def prepare_prompt(input_dir, output_dir, emotion_mode, timing):
    """Prepare le prompt pour l'Oracle (sandbox AI)."""
    metaprompt_path = input_dir.parent.parent.parent / "METAPROMPTS" / "META_F02B_EMOTION.md"

    metaprompt = ""
    if metaprompt_path.exists():
        with open(metaprompt_path, "r", encoding="utf-8") as f:
            metaprompt = f.read()

    # Extraire un echantillon de timing.json pour le prompt
    words_sample = timing.get("words", [])[:50]
    segments_sample = timing.get("segments", [])[:10]

    prompt = f"""{metaprompt}

---

## DONNEES D'ENTREE

### Mode emotionnel: {emotion_mode}

### timing.json (extrait — {timing['meta']['word_count']} mots, {timing['meta']['strong_word_count']} mots forts):

```json
{{
  "meta": {json.dumps(timing["meta"], indent=2)},
  "words_sample": {json.dumps(words_sample, indent=2, ensure_ascii=False)},
  "segments_sample": {json.dumps(segments_sample, indent=2, ensure_ascii=False)}
}}
```

### Informations video:
- FPS: {timing['meta']['fps']}
- Total frames: {timing['meta']['total_frames']}
- Duree: {timing['meta']['duration_seconds']}s

---

## TA SORTIE

Genere un codex.json valide avec:
- text_overlays: sous-titres groupes (2-5 mots) synchronises sur timing.json
- zoom_keyframes: zooms sur les mots forts (is_strong: true)
- sfx_timeline: keyboard sur chaque sous-titre, whoosh sur chaque zoom
- color_preset + color_css_filter selon le mode {emotion_mode}

Format de sortie: JSON valide uniquement (pas de markdown, pas de commentaires).
"""

    prompt_path = output_dir / "oracle_prompt.txt"
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(prompt)

    return prompt_path

# ── Validate codex ────────────────────────────────────────────────────────────

def validate_codex(codex_path, output_dir, emotion_mode):
    """Valide et ecrit le codex.json."""
    with open(codex_path, "r", encoding="utf-8") as f:
        codex = json.load(f)

    required_keys = ["version", "text_overlays", "zoom_keyframes", "sfx_timeline", "color_preset"]
    for key in required_keys:
        if key not in codex:
            log_fail(f"Cle manquante dans le codex: {key}")
            sys.exit(1)

    output_path = output_dir / OUTPUT_FILENAME
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(codex, f, ensure_ascii=False, indent=2)

    log_ok(f"codex.json ecrit: {output_path}")

    print()
    print("═" * 52)
    print(" F02B ORACLE V2 — MISSION ACCOMPLIE")
    print(f" Mode      : {emotion_mode}")
    print(f" Textes    : {len(codex['text_overlays'])}")
    print(f" Zooms     : {len(codex['zoom_keyframes'])}")
    print(f" SFX       : {len(codex['sfx_timeline'])}")
    print(f" Couleurs  : {codex['color_preset']}")
    print(f" Audio     : {codex.get('audio_source', 'N/A')}")
    print(f" Fichier   : {OUTPUT_FILENAME}")
    print("═" * 52)
    print()

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="F02B ORACLE V2 — Synchronisateur voix off")
    parser.add_argument("--input", required=True, help="Dossier IN/")
    parser.add_argument("--output", required=True, help="Dossier OUT/")
    parser.add_argument("--emotion-mode", default="WHOLESOME",
                        choices=list(COLOR_PRESETS.keys()))
    parser.add_argument("--prepare", action="store_true", help="Preparer le prompt pour l'Oracle")
    parser.add_argument("--validate", metavar="CODEX_PATH", help="Valider un codex genere")
    parser.add_argument("--auto", action="store_true", help="Generation automatique (sans Oracle)")
    parser.add_argument("--generate-script", action="store_true", help="Generer le script voix off (pour Oracle sandbox)")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    # ── Lire timing.json ──
    section("Lecture de timing.json")

    timing_path = input_dir / TIMING_FILENAME
    if not timing_path.exists():
        log_fail(f"timing.json introuvable: {timing_path}")
        sys.exit(1)

    with open(timing_path, "r", encoding="utf-8") as f:
        timing = json.load(f)

    log_ok(f"timing.json lu: {timing['meta']['word_count']} mots, {timing['meta']['strong_word_count']} mots forts")
    log_ok(f"Langue: {timing['meta']['language']}, Duree: {timing['meta']['duration_seconds']}s")

    # Lire f01_manifest.json pour les infos video
    video_info = {}
    manifest_path = input_dir / MANIFEST_FILENAME
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            video_info = json.load(f)

    # ── Mode auto ──
    if args.auto:
        section("Generation automatique du codex")
        codex = auto_generate_codex(timing, args.emotion_mode, video_info)

        output_path = output_dir / OUTPUT_FILENAME
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(codex, f, ensure_ascii=False, indent=2)

        log_ok(f"codex.json genere: {output_path}")

        print()
        print("═" * 52)
        print(" F02B ORACLE V2 — MISSION ACCOMPLIE (AUTO)")
        print(f" Mode      : {args.emotion_mode}")
        print(f" Textes    : {len(codex['text_overlays'])}")
        print(f" Zooms     : {len(codex['zoom_keyframes'])}")
        print(f" SFX       : {len(codex['sfx_timeline'])}")
        print(f" Couleurs  : {codex['color_preset']}")
        print(f" Audio     : {codex.get('audio_source', 'N/A')}")
        print("═" * 52)
        print()
        return

    # ── Mode prepare ──
    if args.prepare:
        section("Preparation du prompt Oracle")
        prompt_path = prepare_prompt(input_dir, output_dir, args.emotion_mode, timing)
        log_ok(f"Prompt prepare: {prompt_path}")
        log_info("Colle le contenu de oracle_prompt.txt dans le chat pour que l'Oracle genere le codex")
        return

    # ── Mode validate ──
    if args.validate:
        section("Validation du codex")
        validate_codex(args.validate, output_dir, args.emotion_mode)
        return

    # ── Mode generate-script ──
    if args.generate_script:
        section("Preparation du script voix off")

        # Lire la brouillie (narrative.txt de F02A)
        narrative_path = input_dir / "narrative.txt"
        if not narrative_path.exists():
            # Essayer F02A OUT
            narrative_path = input_dir.parent / "F02A_VISION" / "OUT" / "narrative.txt"

        narrative = ""
        if narrative_path.exists():
            with open(narrative_path, "r", encoding="utf-8") as f:
                narrative = f.read()
            log_ok(f"Brouillie lue: {len(narrative)} chars")
        else:
            log_warn("Pas de narrative.txt — l'Oracle devra improviser")

        # Lire le metaprompt
        metaprompt_path = input_dir.parent.parent.parent / "METAPROMPTS" / "META_F02B_EMOTION.md"
        metaprompt = ""
        if metaprompt_path.exists():
            with open(metaprompt_path, "r", encoding="utf-8") as f:
                metaprompt = f.read()

        # Infos video
        fps = timing["meta"]["fps"]
        total_frames = timing["meta"]["total_frames"]
        duration = timing["meta"]["duration_seconds"]

        # Construire le prompt pour l'Oracle
        prompt = f"""{metaprompt}

---

## DONNEES D'ENTREE

### Mode emotionnel: {args.emotion_mode}

### Description F02A (brouillie):
{narrative}

### Informations video:
- FPS: {fps}
- Total frames: {total_frames}
- Duree: {duration}s

---

## TA SORTIE

Genere un SCRIPT VOIX OFF pour cette video en mode {args.emotion_mode}.
Le script doit durer environ {duration:.0f} secondes a l'oral.
Texte brut uniquement, pas de JSON, pas de markdown.
"""

        prompt_path = output_dir / "oracle_script_prompt.txt"
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(prompt)

        log_ok(f"Prompt prepare: {prompt_path}")
        log_info("L'Oracle (sandbox AI) va generer le script voix off")
        return

    log_fail("Usage: --prepare, --auto, --generate-script, ou --validate <codex_path> requis")
    sys.exit(1)

if __name__ == "__main__":
    main()
