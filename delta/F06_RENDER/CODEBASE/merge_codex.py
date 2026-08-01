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


def merge_codex(style, timing, clip_id):
    """Fusionne le style avec le timing pour creer un codex complet."""
    
    fps = timing.get("fps", style.get("video", {}).get("fps", 30))
    
    codex = {
        "version": style.get("version", "2.0"),
        "emotion_mode": style.get("emotion_mode", "WHOLESOME"),
        "narrative_arc": style.get("narrative_arc", ""),
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
    zoom_config = style.get("zoom", {})
    sfx_defaults = style.get("sfx_defaults", {})
    
    words = timing.get("words", [])
    log(f"Generation text_overlays: {len(words)} mots")
    
    for word_data in words:
        word = word_data.get("word", "")
        start_sec = word_data.get("start", 0)
        end_sec = word_data.get("end", start_sec + 0.5)
        is_strong = word_data.get("is_strong", False)
        
        start_frame = int(start_sec * fps)
        end_frame = int(end_sec * fps)
        
        text_style = {
            "font": text_defaults.get("font", "Anton, Arial Black, sans-serif"),
            "size": text_defaults.get("size", 96),
            "color": "#FFFF00" if is_strong else text_defaults.get("color", "#FFFFFF"),
            "stroke_color": text_defaults.get("stroke_color", "#000000"),
            "stroke_width": text_defaults.get("stroke_width", 4),
            "shadow": text_defaults.get("shadow", "2px 4px 8px rgba(0,0,0,0.9)"),
            "position": text_defaults.get("position", "center"),
            "letter_spacing": text_defaults.get("letter_spacing", "0em"),
            "glow_intensity": text_defaults.get("glow_intensity", 0) + (40 if is_strong else 0),
            "depth_3d": text_defaults.get("depth_3d", 0)
        }
        
        codex["text_overlays"].append({
            "id": f"txt_{len(codex['text_overlays']):02d}",
            "content": word,
            "start_frame": start_frame,
            "end_frame": end_frame,
            "animation": "word_by_word",
            "emotion_weight": "strong" if is_strong else "normal",
            **text_style
        })
    
    # Zoom sur mots forts
    if zoom_config.get("on_strong_word", True):
        log("Generation zoom_keyframes sur mots forts")
        min_scale = zoom_config.get("min_scale", 1.0)
        max_scale = zoom_config.get("max_scale", 1.3)
        
        codex["zoom_keyframes"].append({
            "frame": 0, "scale": min_scale, "target_x": 0.5, "target_y": 0.5
        })
        
        for word_data in words:
            if word_data.get("is_strong", False):
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
