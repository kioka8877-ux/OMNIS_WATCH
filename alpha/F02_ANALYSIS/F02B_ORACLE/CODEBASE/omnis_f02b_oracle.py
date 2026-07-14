"""
omnis_f02b_oracle.py — F02B : Createur d'Emotion
=================================================
Transforme la description factuelle de F02A en recit emotionnel.
Genere le codex.json qui dirige toute la video.

L'Oracle est le modele IA du sandbox. Ce script:
  1. Lit les entrees (narrative.txt, tracking_data.json, f01_manifest.json)
  2. Prepare le prompt pour l'Oracle (en utilisant le metaprompt)
  3. L'Oracle genere le codex.json (texte + timing + zooms + SFX + couleurs)
  4. Le script valide le schema du codex.json
  5. Ecrit le codex.json dans OUT/

Usage:
  # Etape 1: Preparer les entrees
  python omnis_f02b_oracle.py --input /path/IN/ --output /path/OUT/ \
    --emotion-mode TRISTE --prepare

  # Etape 2: L'Oracle (sandbox AI) genere le codex base sur le prompt prepare
  #           (se fait via le chat, pas en CLI)

  # Etape 3: Valider et ecrire le codex
  python omnis_f02b_oracle.py --input /path/IN/ --output /path/OUT/ \
    --emotion-mode TRISTE --validate /path/to/generated_codex.json

Entree: narrative.txt + tracking_data.json + f01_manifest.json
Sortie: codex.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

# ── Constantes ──────────────────────────────────────────────────────────────

NARRATIVE_FILENAME = "narrative.txt"
TRACKING_FILENAME = "tracking_data.json"
MANIFEST_FILENAME = "f01_manifest.json"
OUTPUT_FILENAME = "codex.json"
METAPROMPT_PATH = "../../METAPROMPTS/META_F02B_EMOTION.md"

# Presets de colorimetrie par mode emotionnel
COLOR_PRESETS = {
    "TRISTE": {
        "name": "cold_desaturated",
        "css_filter": "contrast(0.95) saturate(0.6) brightness(0.9) hue-rotate(-5deg)"
    },
    "WHOLESOME": {
        "name": "warm_vibrant",
        "css_filter": "contrast(1.1) saturate(1.3) brightness(1.05) hue-rotate(5deg)"
    },
    "TENSION": {
        "name": "high_contrast",
        "css_filter": "contrast(1.3) saturate(0.8) brightness(0.95)"
    },
    "SURPRISE": {
        "name": "punchy",
        "css_filter": "contrast(1.2) saturate(1.4) brightness(1.1)"
    },
    "NOSTALGIA": {
        "name": "sepia_soft",
        "css_filter": "sepia(0.3) contrast(1.05) saturate(0.9) brightness(1.0)"
    },
}

# ── Logging ─────────────────────────────────────────────────────────────────

def log_ok(msg): print(f"  [OK] {msg}")
def log_fail(msg): print(f"  [FAIL] {msg}")
def log_info(msg): print(f"  [...] {msg}")
def log_warn(msg): print(f"  [WARN] {msg}")

def section(title):
    bar = "─" * max(0, 50 - len(title))
    print(f"\n── {title} {bar}")

# ── Lecture des entrees ─────────────────────────────────────────────────────

def read_inputs(input_dir):
    """Lit tous les fichiers d'entree et retourne un dict."""
    inputs = {}

    # narrative.txt
    narrative_path = input_dir / NARRATIVE_FILENAME
    if narrative_path.exists():
        with open(narrative_path, "r", encoding="utf-8") as f:
            inputs["narrative"] = f.read().strip()
        log_ok(f"narrative.txt lu ({len(inputs['narrative'])} chars)")
    else:
        log_fail(f"narrative.txt introuvable: {narrative_path}")
        sys.exit(1)

    # tracking_data.json
    tracking_path = input_dir / TRACKING_FILENAME
    if tracking_path.exists():
        with open(tracking_path, "r", encoding="utf-8") as f:
            inputs["tracking"] = json.load(f)
        log_ok(f"tracking_data.json lu ({len(inputs['tracking']['tracks'])} tracks)")
    else:
        log_warn("tracking_data.json non trouve — tracking desactive")
        inputs["tracking"] = None

    # f01_manifest.json
    manifest_path = input_dir / MANIFEST_FILENAME
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            inputs["manifest"] = json.load(f)
        meta = inputs["manifest"]["meta"]
        log_ok(f"f01_manifest.json lu ({meta['fps']}fps, {meta['total_frames']} frames)")
    else:
        log_fail(f"f01_manifest.json introuvable: {manifest_path}")
        sys.exit(1)

    return inputs

# ── Preparation du prompt ───────────────────────────────────────────────────

def prepare_prompt(inputs, emotion_mode):
    """
    Prepare le prompt complet pour l'Oracle en combinant:
    - Le metaprompt (META_F02B_EMOTION.md)
    - La description factuelle (narrative.txt)
    - Les donnees de tracking
    - Les metadonnees video (fps, frames, duree)
    - Le mode emotionnel choisi
    """
    meta = inputs["manifest"]["meta"]
    fps = meta["fps"]
    total_frames = meta["total_frames"]
    duration = meta["duration_seconds"]

    # Informations de tracking
    tracking_info = "Aucun tracking disponible."
    if inputs["tracking"]:
        tracks = inputs["tracking"]["tracks"]
        target_type = inputs["tracking"]["target_type"]
        # Extraire quelques positions cles
        key_positions = []
        for t in tracks[::max(1, len(tracks)//5)]:  # ~5 positions cles
            key_positions.append(f"  Frame {t['frame']}: ({t['x']:.2f}, {t['y']:.2f}) conf={t['confidence']:.2f}")
        tracking_info = f"Cible trackee: {target_type}\nPositions cles:\n" + "\n".join(key_positions)

    # Preset de couleur pour ce mode
    color_preset = COLOR_PRESETS.get(emotion_mode, COLOR_PRESETS["TRISTE"])

    prompt = f"""# MISSION F02B — CREATEUR D'EMOTION

## MODE EMOTIONNEL: {emotion_mode}

## DESCRIPTION FACTUELLE DE LA VIDEO (F02A):
{inputs['narrative']}

## METADONNEES VIDEO:
- FPS: {fps}
- Frames totales: {total_frames}
- Duree: {duration}s
- Resolution: {meta['width']}x{meta['height']}
- Format: {meta['format']}

## DONNEES DE TRACKING:
{tracking_info}

## PRESET COULEUR RECOMMANDE:
- Nom: {color_preset['name']}
- CSS filter: {color_preset['css_filter']}

## INSTRUCTIONS:
Tu es un CREATEUR D'EMOTION pour YouTube Shorts.
Transforme cette realite banale en un REcit EMOTIONNAL via le texte a l'ecran.

REGLES:
- Chaque texte fait 2-6 mots (court, percutant)
- 4-6 textes maximum pour ce Short de {duration}s
- Structure narrative: setup → twist/context → emotional_peak → resolution
- Le timing (start_frame/end_frame) cree l'emotion:
  * Un texte qui reste longtemps = poids emotionnel
  * Un texte qui claque vite = tension
- Les zooms suivent les textes (pas l'inverse)
- Les SFX suivent les textes (keyboard a chaque apparition, whoosh sur les zooms)
- La colorimetrie: {color_preset['name']}

## FORMAT DE SORTIE ATTENDU:
Genere un JSON valide avec cette structure exacte:

```json
{{
  "version": "1.0",
  "emotion_mode": "{emotion_mode}",
  "narrative_arc": "setup → twist → emotional_peak → resolution",
  "video": {{
    "source": "video_coupee.mp4",
    "fps": {fps},
    "total_frames": {total_frames},
    "width": {meta['width']},
    "height": {meta['height']}
  }},
  "text_overlays": [
    {{
      "id": "txt_01",
      "content": "TEXTE COURT ICI",
      "start_frame": 0,
      "end_frame": 45,
      "animation": "fade_in|typewriter|slide_left|pop",
      "emotion_weight": "neutral|twist|emotional_peak|resolution",
      "font": "Arial Black",
      "size": 64,
      "color": "#FFFFFF",
      "stroke_color": "#000000",
      "stroke_width": 3,
      "position": "center_bottom|center|top"
    }}
  ],
  "zoom_keyframes": [
    {{"frame": 0, "scale": 1.0, "target_x": 0.5, "target_y": 0.5}}
  ],
  "color_preset": "{color_preset['name']}",
  "color_css_filter": "{color_preset['css_filter']}",
  "enhance_4k": true,
  "sfx_timeline": [
    {{"frame": 0, "type": "keyboard", "volume": 0.3}}
  ],
  "tracking_source": "tracking_data.json"
}}
```

Genere UNIQUEMENT le JSON. Pas d'explication, pas de texte avant ou apres.
"""

    return prompt

# ── Validation du codex ─────────────────────────────────────────────────────

def validate_codex(codex, inputs, emotion_mode):
    """Valide la structure du codex.json genere par l'Oracle."""
    errors = []

    # Champs obligatoires
    required_top = ["version", "emotion_mode", "narrative_arc", "video",
                    "text_overlays", "zoom_keyframes", "color_preset",
                    "enhance_4k", "sfx_timeline"]
    for field in required_top:
        if field not in codex:
            errors.append(f"Champ manquant: {field}")

    # emotion_mode
    if codex.get("emotion_mode") != emotion_mode:
        errors.append(f"emotion_mode incorrect: {codex.get('emotion_mode')} != {emotion_mode}")

    # video
    video = codex.get("video", {})
    meta = inputs["manifest"]["meta"]
    if video.get("fps") != meta["fps"]:
        errors.append(f"fps incorrect: {video.get('fps')} != {meta['fps']}")
    if video.get("total_frames") != meta["total_frames"]:
        errors.append(f"total_frames incorrect: {video.get('total_frames')} != {meta['total_frames']}")

    # text_overlays
    overlays = codex.get("text_overlays", [])
    if not overlays:
        errors.append("Aucun text_overlay")
    if len(overlays) > 8:
        errors.append(f"Trop de text_overlays: {len(overlays)} (max 8)")

    for i, overlay in enumerate(overlays):
        if "content" not in overlay:
            errors.append(f"text_overlay[{i}] sans content")
        if "start_frame" not in overlay or "end_frame" not in overlay:
            errors.append(f"text_overlay[{i}] sans timing")
        else:
            if overlay["start_frame"] >= overlay["end_frame"]:
                errors.append(f"text_overlay[{i}] timing invalide")
            if overlay["end_frame"] > meta["total_frames"]:
                errors.append(f"text_overlay[{i}] end_frame > total_frames")
        valid_animations = ["fade_in", "fade_in_slow", "typewriter", "slide_left", "slide_right", "pop"]
        if overlay.get("animation") not in valid_animations:
            errors.append(f"text_overlay[{i}] animation invalide: {overlay.get('animation')}")

    # zoom_keyframes
    keyframes = codex.get("zoom_keyframes", [])
    for i, kf in enumerate(keyframes):
        if "frame" not in kf or "scale" not in kf:
            errors.append(f"zoom_keyframe[{i}] incomplet")
        if kf.get("scale", 1.0) < 1.0 or kf.get("scale", 1.0) > 3.0:
            errors.append(f"zoom_keyframe[{i}] scale hors range: {kf.get('scale')}")

    # sfx_timeline
    sfx = codex.get("sfx_timeline", [])
    for i, s in enumerate(sfx):
        if "frame" not in s or "type" not in s:
            errors.append(f"sfx_timeline[{i}] incomplet")
        valid_sfx = ["whoosh", "keyboard", "impact", "heartbeat"]
        if s.get("type") not in valid_sfx:
            errors.append(f"sfx_timeline[{i}] type invalide: {s.get('type')}")

    return errors

# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="F02B ORACLE — Createur d'Emotion"
    )
    parser.add_argument("--input", required=True, help="Dossier IN/")
    parser.add_argument("--output", required=True, help="Dossier OUT/")
    parser.add_argument("--emotion-mode", required=True,
                        choices=list(COLOR_PRESETS.keys()),
                        help="Mode emotionnel (TRISTE, WHOLESOME, TENSION, SURPRISE, NOSTALGIA)")
    parser.add_argument("--prepare", action="store_true",
                        help="Prepare le prompt pour l'Oracle et l'affiche")
    parser.add_argument("--validate", metavar="CODEX_PATH",
                        help="Valide et ecrit un codex.json genere par l'Oracle")

    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)

    # ── Lecture des entrees ──
    section("Lecture des entrees")
    inputs = read_inputs(input_dir)

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    # ── Mode prepare ──
    if args.prepare:
        section("Preparation du prompt Oracle")
        prompt = prepare_prompt(inputs, args.emotion_mode)

        # Sauvegarder le prompt
        prompt_path = output_dir / "oracle_prompt.txt"
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(prompt)

        log_ok(f"Prompt prepare: {prompt_path}")
        log_info(f"Longueur: {len(prompt)} chars")
        log_info("L'Oracle (sandbox AI) doit maintenant generer le codex.json")
        log_info("base sur ce prompt. Le resultat sera valide avec --validate.")
        print()
        print("─" * 52)
        print(" PROMPT POUR L'ORACLE:")
        print("─" * 52)
        print(prompt)
        return

    # ── Mode validate ──
    if args.validate:
        section("Validation du codex.json")

        codex_path = Path(args.validate)
        if not codex_path.exists():
            log_fail(f"Codex introuvable: {codex_path}")
            sys.exit(1)

        with open(codex_path, "r", encoding="utf-8") as f:
            codex = json.load(f)

        errors = validate_codex(codex, inputs, args.emotion_mode)

        if errors:
            log_fail(f"{len(errors)} erreur(s) de validation:")
            for e in errors:
                print(f"  • {e}")
            sys.exit(1)

        log_ok("Validation OK — codex conforme")

        # Ecrire le codex valide
        output_path = output_dir / OUTPUT_FILENAME
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(codex, f, ensure_ascii=False, indent=2)

        log_ok(f"codex.json ecrit: {output_path}")

        # Resume
        print()
        print("═" * 52)
        print(" F02B ORACLE — MISSION ACCOMPLIE")
        print(f" Mode      : {args.emotion_mode}")
        print(f" Textes    : {len(codex['text_overlays'])}")
        print(f" Zooms     : {len(codex['zoom_keyframes'])}")
        print(f" SFX       : {len(codex['sfx_timeline'])}")
        print(f" Couleurs  : {codex['color_preset']}")
        print(f" Fichier   : {OUTPUT_FILENAME}")
        print("═" * 52)
        print()
        return

    # Si ni --prepare ni --validate
    log_fail("Usage: --prepare ou --validate <codex_path> requis")
    sys.exit(1)

if __name__ == "__main__":
    main()
