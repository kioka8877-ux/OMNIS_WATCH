# F01A — CASTELLAN AUDIO
## Nettoyage Audio Automatique

## Rôle
Détecte et supprime les silences de l'audio brut (voix off) via FFmpeg.

## Entrée
- `audio_raw.mp3` — Audio brut fourni par l'opérateur

## Action
1. FFmpeg `silencedetect` — détecte les silences (< -40dB, > 0.5s)
2. FFmpeg `silenceremove` — supprime les silences automatiquement
3. Sauvegarde le mapping des silences dans `silence_map.json`

## Sortie
- `audio_clean.mp3` — Audio sans silences
- `silence_map.json` — Mapping des silences détectés/supprimés

## Workflow GitHub Actions
```yaml
f01a_audio.yml — workflow_dispatch (manuel)
```

## Techno
- FFmpeg (silencedetect + silenceremove)
- Python 3
- GitHub Actions (CPU gratuit)

## Adapté de
CRUSADER `crs_f01a.py` — version sans Flask/viewer (automatisée pour CI)
