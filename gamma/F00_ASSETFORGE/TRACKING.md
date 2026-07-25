# F00 ASSETFORGE — Pipeline de préparation multi-clips

## Statut
🆕 Créé pour GAMMA (commentary niche)

## Rôle
F00 prend plusieurs clips bruts, sélectionne des séquences (IN/OUT par séquence), ajuste les vitesses, et concatène le tout en **un seul clip** calibré sur la durée de la voix off.

## Flow
```
clips bruts + sequences.json + voiceoff_duration
    ↓
F00 coupe chaque séquence (FFmpeg)
F00 applique la vitesse par séquence (setpts + atempo)
F00 concatène les séquences (concat demuxer)
    ↓
clip_unique.mp4 + f00_manifest.json
    ↓
Pipeline beta prend le relais (F02 Preview → F03 → F04 → F05)
```

## Entrées
- `IN/` : clips bruts uploadés par l'opérateur
- `IN/sequences.json` : JSON décrivant les séquences (clip, in, out, speed, position)
- `--voiceoff-duration` : durée de la voix off en secondes (budget temporel)

## Sorties
- `OUT/clip_unique.mp4` : le clip unique concaténé
- `OUT/f00_manifest.json` : manifeste détaillant les séquences et durées

## Format sequences.json
```json
{
  "voiceoff_duration": 45.0,
  "segments": [
    {"clip": "clip_01.mp4", "in": 5.2, "out": 12.8, "speed": 1.0, "position": 1},
    {"clip": "clip_02.mp4", "in": 0.0, "out": 8.5, "speed": 0.95, "position": 2},
    {"clip": "clip_01.mp4", "in": 20.0, "out": 25.3, "speed": 1.0, "position": 3},
    {"clip": "clip_03.mp4", "in": 3.0, "out": 10.0, "speed": 1.0, "position": 4}
  ]
}
```

## Viewer F00
- Hébergé sur GitHub Pages (f00/)
- Upload clips bruts
- Sélection séquences par clip (IN/OUT par séquence, pas global)
- Vitesse ajustable par séquence
- Indicateur sync (total séquences vs durée voix off)
- Génère sequences.json

## Workflow
- `.github/workflows/f00_assetforge.yml` — workflow_dispatch manuel
