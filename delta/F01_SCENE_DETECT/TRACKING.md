# D-F01 SCENE DETECT + TRANSCRIPTION - Tracking

## Statut
- **Statut :** CODE COMPLETE
- **Version :** delta
- **Priorit :** tape 3

## Rle
Les yeux de la flotte. Dcoupe la vido en scenes (PySceneDetect) et transcrit l'audio mot par mot (faster-whisper).

## Flow
```
video_source.mp4 de D-F00
    ↓
D-F01 mode detect: PySceneDetect → scenes.json
D-F01 mode transcribe: faster-whisper → transcript.json
    ↓
OUT/scenes.json (bornes IN/OUT par scene)
OUT/transcript.json (mots + timestamps word-level)
    ↓
D-F02 prend le relais
```

## Entres
- `IN/video_source.mp4` (de D-F00)
- `IN/d00_manifest.json` (mtadonnes)

## Sorties
- `OUT/scenes.json` : tableau des scenes avec start_sec, end_sec, duration_sec
- `OUT/transcript.json` : transcription mot par mot (word, start, end, confidence)

## Code
- Script 1 : `CODEBASE/omnis_d01_scenedetect.py` (non cr) — mode detect
- Script 2 : `CODEBASE/omnis_d01_transcribe.py` (non cr) — mode transcribe
- Techno : PySceneDetect + faster-whisper + FFmpeg
- Runner : GitHub Actions (ubuntu-latest, GPU optionnel)

## PERTURABO Bridge
Aucun (scne detection = pure technique, pas de rgle virale).
La virulence intervient D-F02.

## Tests de validation (T2)
| # | Entre | Attendu | Statut |
|---|-------|---------|--------|
| T2.1 | video_source.mp4 8min | scenes.json avec ≥5 scnes | EN ATTENTE CODE |
| T2.2 | video_source.mp4 8min | transcript.json complet, >95% mots | EN ATTENTE CODE |
