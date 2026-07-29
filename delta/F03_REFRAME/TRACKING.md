# D-F03 REFRAME - Tracking

## Statut
- **Statut :** PLANIFI
- **Version :** delta
- **Priorit :** tape 5

## Rle
Le sniper de la flotte. Pour chaque moment de la cutlist, extrait le segment,
dtecte le sujet (MediaPipe / YOLOv8) et crop en 9:16 dynamique qui suit le sujet.

## Flow
```
video_source.mp4 de D-F00 + cutlist.json de D-F02
    ↓
D-F03 extrait chaque segment (FFmpeg)
D-F03 dtecte le sujet frame par frame (MediaPipe face / YOLOv8 object)
D-F03 crop 9:16 dynamique qui suit le sujet (TRACK mode)
D-F03 fallback blur-pad si aucun sujet dtect (GENERAL mode)
D-F03 applique le mode motionnel (zoom, colorimtrie)
    ↓
OUT/clips_reframes/ (clip_001.mp4 ... clip_N.mp4)
OUT/reframe_manifest.json
    ↓
D-F04 prend le relais
```

## Entres
- `IN/video_source.mp4`
- `IN/cutlist.json`
- `IN/d00_manifest.json`

## Sorties
- `OUT/clips_reframes/clip_{idx:03d}.mp4` : un mp4 9:16 par moment viral
- `OUT/reframe_manifest.json` : mapping de chaque clip (scene source, dure, tait tracking)

## Modes de reframe
| Mode | Dtection | Comportement | Usage |
|------|----------|-------------|-------|
| TRACK | MediaPipe face + YOLOv8 person | Crop qui suit le sujet | Sujet humain visible |
| GENERAL | Aucun | Blur-pad centr + crop 9:16 | Pas de sujet, paysage/B-roll |

## PERTURABO influence
Le `emotion_mode` dans la cutlist influence le reframe :
- **TRISTE** : zoom lent sur le visage, desaturation
- **WHOLESOME** : zoom doux, saturation chaude
- **TENSION** : zoom rapide, contraste lev
- **SURPRISE** : pop zoom, couleurs vives

## Code
- Script : `CODEBASE/omnis_d03_reframe.py` (non cr)
- Techno : MediaPipe (face), ultralytics (YOLOv8), FFmpeg, OpenCV
- Runner : GitHub Actions (ubuntu-latest, 30 min timeout)

## Tests de validation (T4)
| # | Entre | Attendu | Statut |
|---|-------|---------|--------|
| T4.1 | video_source + cutlist 3 moments | 3 clips 9:16 (1080x1920) produits | EN ATTENTE CODE |
| T4.2 | Squence avec visage visible | Face suivie, crop centr sur le visage | EN ATTENTE CODE |
| T4.3 | Squence sans visage (paysage) | Fallback blur-pad, crop centr | EN ATTENTE CODE |
