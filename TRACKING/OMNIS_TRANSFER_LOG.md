# OMNIS-WATCH — TRANSFER LOG
## Registre des Transferts Inter-Fregates

---

## Procedure Standard de Transit

1. python OMNIS_CUSTOS.py --frigate <FXX> --mode check-out
2. Copier les fichiers (source OUT/ → destination IN/)
3. python OMNIS_CUSTOS.py --frigate <FXX> --mode check-in
4. Logger le transfert dans ce fichier

**Regle absolue :** Aucun transfert sans validation CUSTOS aux deux extremites.

---

## Schemas JSON — Contrats de Donnees

### f01_manifest.json (produit par F01 ACQUISITION)
```json
{
  "meta": {
    "fps": 30,
    "duration_seconds": 13.0,
    "total_frames": 390,
    "width": 1080,
    "height": 1920,
    "format": "9:16",
    "blur_pad": true,
    "speed": 1.0,
    "volume": 1.0
  },
  "input": {
    "source_file": "video_raw.mp4",
    "in_timestamp": "00:02",
    "out_timestamp": "00:15"
  },
  "output": {
    "file": "video_coupee.mp4",
    "size_mb": 8.5
  }
}
```

### narrative.txt (produit par F02A VISION)
```
Description factuelle de la video, generee par OpenRouter Vision.
Ex: "Un homme lance une balle a son chien dans un parc. Le chien court,
saisit la balle et la rapporte. L'homme caresse le chien."
```

### tracking_data.json (produit par F02A VISION)
```json
{
  "target_type": "face",
  "fps": 30,
  "total_frames": 390,
  "tracks": [
    {"frame": 0, "x": 0.52, "y": 0.35, "confidence": 0.95},
    {"frame": 1, "x": 0.53, "y": 0.36, "confidence": 0.94},
    {"frame": 2, "x": 0.54, "y": 0.36, "confidence": 0.96}
  ]
}
```

### codex.json (produit par F02B ORACLE)
```json
{
  "version": "1.0",
  "emotion_mode": "TRISTE",
  "narrative_arc": "setup → twist → emotional_peak → resolution",
  "video": {
    "source": "video_coupee.mp4",
    "fps": 30,
    "total_frames": 390,
    "width": 1080,
    "height": 1920
  },
  "text_overlays": [
    {
      "id": "txt_01",
      "content": "This is Max.",
      "start_frame": 0,
      "end_frame": 45,
      "animation": "fade_in",
      "emotion_weight": "neutral",
      "font": "Arial Black",
      "size": 64,
      "color": "#FFFFFF",
      "stroke_color": "#000000",
      "stroke_width": 3,
      "position": "center_bottom"
    }
  ],
  "zoom_keyframes": [
    {"frame": 0, "scale": 1.0, "target_x": 0.5, "target_y": 0.5},
    {"frame": 45, "scale": 1.3, "target_x": 0.65, "target_y": 0.30}
  ],
  "color_preset": "cold_desaturated",
  "enhance_4k": true,
  "sfx_timeline": [
    {"frame": 45, "type": "whoosh", "volume": 0.8},
    {"frame": 0, "type": "keyboard", "volume": 0.3}
  ],
  "tracking_source": "tracking_data.json"
}
```

---

## Matrice des Routes Legales

| Source | Destination | Fichiers transferes |
|--------|-------------|--------------------------------------------------|
| SHARED | F01 IN | video_raw.mp4 |
| F01 OUT | F02A IN | video_coupee.mp4, f01_manifest.json |
| F02A OUT | F02B IN | narrative.txt, tracking_data.json |
| F02B OUT | F02 PREVIEW | codex.json |
| F02B OUT | F03A IN | codex.json |
| F01 OUT | F03A IN | video_coupee.mp4 |
| SHARED | F03A IN | sfx/ |
| F03A OUT | F03B IN | video_visuelle.mp4, codex.json |
| SHARED | F03B IN | sfx/ |
| F03B OUT | F04 IN | video_complete.mp4 |
| F04 OUT | F05 IN | youtube_final.mp4 |
| F05 OUT | OPERATEUR | clean_final.mp4 |

---

## Registre des Transferts

| # | Date | Campagne | Source | Destination | Fichiers | CUSTOS Out | CUSTOS In | Statut |
|---|------|----------|--------|-------------|----------|------------|-----------|--------|
| — | — | CAMP_01 | — | — | — | — | — | EN ATTENTE |

---

*Tout transfert non logge ici est considere comme non valide.*
