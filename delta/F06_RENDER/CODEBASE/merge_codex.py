#!/usr/bin/env python3
"""
merge_codex.py — D-F06 RENDER
=============================
Fusionne codex_STYLE.json + timing_XXX.json → codex_clip_XXX.json

Usage:
  python merge_codex.py \
    --style ../IN/codex_STYLE.json \
    --timing ../IN/timing_003.json \
    --clip-id 3 \
    --output ../OUT/codex_clip_003.json
"""

import argparse
import json
from pathlib import Path


def log(msg): print(f"  {msg}")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_segments(words, max_words=8):
    """Regroupe les mots du timing en segments de sous-titres.

    Même logique que la preview D-F05 : chaque segment contient au plus
    max_words mots, et se coupe après une ponctuation de fin de phrase.
    Un segment est "strong" dès qu'un de ses mots est fort.
    """
    segments = []
    current = None
    for w in words:
        word = (w.get("word") or "").strip()
        if not word:
            continue
        if current is None:
            current = {
                "start": w.get("start", 0),
                "end": w.get("end", w.get("start", 0)),
                "text": word,
                "is_strong": bool(w.get("is_strong", False)),
            }
            continue
        current["text"] += " " + word
        current["end"] = w.get("end", w.get("start", 0))
        current["is_strong"] = current["is_strong"] or bool(w.get("is_strong", False))
        ends_sentence = bool(word[-1] in ".!?…»")
        word_count = len(current["text"].split(" "))
        if ends_sentence or word_count >= max_words:
            segments.append(current)
            current = None
    if current is not None:
        segments.append(current)
    return segments


def select_zoom_targets(words, gap_sec=3.0):
    """Choisit les mots forts à zoomer, avec un gap minimum entre deux zooms.

    Découpe le temps en fenêtres de gap_sec. Dans chaque fenêtre, on garde
    le mot fort le plus porteur (la durée la plus longue). Résultat :
    au plus 1 zoom par fenêtre, donc plus de saccades.
    """
    strong_words = [w for w in words if w.get("is_strong", False)]
    if not strong_words:
        return []
    strong_words.sort(key=lambda w: w.get("start", 0))

    targets = []
    window_start = strong_words[0].get("start", 0)
    best = strong_words[0]

    for w in strong_words[1:]:
        start = w.get("start", 0)
        if start - window_start >= gap_sec:
            targets.append(best)
            window_start = start
            best = w
        else:
            dur = w.get("end", start) - start
            best_dur = best.get("end", best.get("start", 0)) - best.get("start", 0)
            if dur > best_dur:
                best = w
    targets.append(best)
    return targets


def merge_codex(style, timing, clip_id):
    """Fusionne le style avec le timing pour creer un codex complet."""
    
    fps = timing.get("fps", style.get("video", {}).get("fps", 30))
    
    codex = {
        "version": style.get("version", "2.0"),
        "emotion_mode": style.get("emotion_mode", "WHOLESOME"),
        "narrative_arc": style.get("narrative_arc", ""),
        "title": timing.get("title"),
        "video": {
            "source": f"clip_{clip_id:03d}.mp4",
            "fps": fps,
            "total_frames": 0,
            "width": style.get("video", {}).get("width", 1080),
            "height": style.get("video", {}).get("height", 1920)
        },
        "text_overlays": [],
        "zoom_keyframes": [],
        "color_preset": style.get("color_preset", "warm_vibrant"),
        "color_css_filter": style.get("color_css_filter", ""),
        "enhance_4k": style.get("enhance_4k", True),
        "sharpening": style.get("sharpening", 80),
        "vignette": style.get("vignette", 0.25),
        "grain_intensity": style.get("grain_intensity", 0.2),
        "sfx_timeline": []
    }
    
    text_defaults = style.get("text_defaults", {})
    title_defaults = style.get("title_defaults", {})
    zoom_config = style.get("zoom", {})
    sfx_defaults = style.get("sfx_defaults", {})
    
    words = timing.get("words", [])
    log(f"Generation text_overlays: {len(words)} mots")
    
    # ── TITRE ─────────────────────────────────────────────────────────────────
    # Le titre n'existe que si le timing JSON contient un champ "title",
    # ou si le style (codex_STYLE) en définit un (saisi dans la preview D-F05).
    # Style: title_defaults. Fond bande optionnel. Si fond actif → glow annulé.
    title_text = timing.get("title") or (style.get("title") or "").strip() or None
    if title_text:
        t_color = title_defaults.get("color", "#FFFFFF")
        t_color_strong = title_defaults.get("color_strong", t_color)
        t_bg = title_defaults.get("background", {"enabled": False})
        title_style = {
            "font": title_defaults.get("font", "Anton, Arial Black, sans-serif"),
            "size": title_defaults.get("size", 96),
            "color": t_color,
            "color_strong": t_color_strong,
            "stroke_color": title_defaults.get("stroke_color", "#000000"),
            "stroke_width": title_defaults.get("stroke_width", 4),
            "shadow": title_defaults.get("shadow", "2px 4px 8px rgba(0,0,0,0.9)"),
            "position": title_defaults.get("position", "center"),
            "letter_spacing": title_defaults.get("letter_spacing", "0em"),
            "glow_intensity": 0 if t_bg.get("enabled") else title_defaults.get("glow_intensity", 0),
            "depth_3d": 0 if t_bg.get("enabled") else title_defaults.get("depth_3d", 0),
            "animation": title_defaults.get("animation", "fade_in"),
            "role": "title",
            "background": t_bg
        }
        # Titre affiché sur les 2 premières secondes
        title_dur = min(2.0, (words[0]["start"] if words else 2.0))
        codex["text_overlays"].append({
            "id": "txt_title",
            "content": title_text,
            "start_frame": 0,
            "end_frame": max(int(title_dur * fps), int(1 * fps)),
            "emotion_weight": "title",
            **title_style
        })
        log(f"  + titre: {title_text!r}")
    
    # Regrouper les mots en segments de sous-titres (comme la preview D-F05):
    # max 8 mots ou coupure de phrase, pour un vrai rendu "mot par mot" visible.
    text_color = text_defaults.get("color", "#FFFFFF")
    color_strong = text_defaults.get("color_strong", text_color)
    
    for segment in build_segments(words):
        content = segment["text"]
        start_sec = segment["start"]
        end_sec = segment["end"]
        is_strong = segment["is_strong"]
        
        start_frame = int(start_sec * fps)
        end_frame = int(end_sec * fps)
        
        text_style = {
            "font": text_defaults.get("font", "Anton, Arial Black, sans-serif"),
            "size": text_defaults.get("size", 96),
            "color": color_strong if is_strong else text_color,
            "stroke_color": text_defaults.get("stroke_color", "#000000"),
            "stroke_width": text_defaults.get("stroke_width", 4),
            "shadow": text_defaults.get("shadow", "2px 4px 8px rgba(0,0,0,0.9)"),
            "position": text_defaults.get("position", "center"),
            "letter_spacing": text_defaults.get("letter_spacing", "0em"),
            "glow_intensity": text_defaults.get("glow_intensity", 0),
            "depth_3d": text_defaults.get("depth_3d", 0),
            "background": {"enabled": False}  # sous-titres sans fond
        }
        
        codex["text_overlays"].append({
            "id": f"txt_{len(codex['text_overlays']):02d}",
            "content": content,
            "start_frame": start_frame,
            "end_frame": end_frame,
            "animation": text_defaults.get("animation", "word_by_word"),
            "emotion_weight": "strong" if is_strong else "normal",
            **text_style
        })
    
    # Zoom sur mots forts — 1 zoom max toutes les gap_sec secondes,
    # en gardant le mot fort le plus porteur (durée la plus longue) de la fenêtre.
    if zoom_config.get("on_strong_word", True):
        min_scale = zoom_config.get("min_scale", 1.0)
        max_scale = zoom_config.get("max_scale", 1.3)
        zoom_gap_sec = zoom_config.get("gap_sec", 3.0)
        
        codex["zoom_keyframes"].append({
            "frame": 0, "scale": min_scale, "target_x": 0.5, "target_y": 0.5
        })
        
        targets = select_zoom_targets(words, zoom_gap_sec)
        log(f"Generation zoom_keyframes: {len(targets)} cibles (gap {zoom_gap_sec}s)")
        
        for word_data in targets:
            start_frame = int(word_data.get("start", 0) * fps)
            codex["zoom_keyframes"].append({
                "frame": start_frame, "scale": max_scale, "target_x": 0.5, "target_y": 0.4
            })
            codex["zoom_keyframes"].append({
                "frame": start_frame + int(0.5 * fps), "scale": min_scale, "target_x": 0.5, "target_y": 0.5
            })
    
    # SFX sur mots forts
    if sfx_defaults.get("on_strong_word", True):
        log("Generation sfx_timeline sur mots forts")
        sfx_types = sfx_defaults.get("types", ["whoosh", "pop", "ding"])
        sfx_idx = 0
        
        for word_data in words:
            if word_data.get("is_strong", False):
                start_frame = int(word_data.get("start", 0) * fps)
                sfx_type = sfx_types[sfx_idx % len(sfx_types)]
                sfx_idx += 1
                codex["sfx_timeline"].append({
                    "frame": start_frame, "type": sfx_type, "volume": 0.5
                })
    
    # Calculer total_frames
    if words:
        last = words[-1]
        codex["video"]["total_frames"] = int(last.get("end", 0) * fps) + int(0.5 * fps)
    
    return codex


def main():
    parser = argparse.ArgumentParser(description="Merge codex_STYLE + timing")
    parser.add_argument("--style", required=True)
    parser.add_argument("--timing", required=True)
    parser.add_argument("--clip-id", required=True, type=int)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    print(f"\n=== MERGE CODEX - Clip {args.clip_id:03d} ===")
    
    style = load_json(args.style)
    timing = load_json(args.timing)
    
    codex = merge_codex(style, timing, args.clip_id)
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_json(output_path, codex)
    
    print(f"  text_overlays: {len(codex['text_overlays'])}")
    print(f"  zoom_keyframes: {len(codex['zoom_keyframes'])}")
    print(f"  sfx_timeline: {len(codex['sfx_timeline'])}")
    print(f"  Output: {output_path}\n")


if __name__ == "__main__":
    main()
