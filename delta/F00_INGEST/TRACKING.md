# D-F00 INGEST - Tracking

## Statut
- **Statut :** CODE COMPLETE
- **Version :** delta
- **Priorit :** tape 2

## Rle
Porte d'entre de la flotte delta. Accepte une vido longue (URL YouTube ou fichier local)
et produit une vido source standardise pour le pipeline.

## Flow
```
URL YouTube ou upload fichier
    ↓
D-F00 tlcharge/copie la vido
D-F00 probe les mtadonnes (dure, fps, rsolution, codec)
D-F00 crit le manifeste
    ↓
OUT/video_source.mp4 + OUT/d00_manifest.json
    ↓
D-F01 prend le relais
```

## Entres
- `--url` : URL YouTube (via yt-dlp)
- OU fichier dpos dans `IN/` par l'oprateur

## Sorties
- `OUT/video_source.mp4` : vido source standardise
- `OUT/d00_manifest.json` : mtadonnes (dure, fps, resolution, codec, source)

## Code
- Script : `CODEBASE/omnis_d00_ingest.py` (non cr)
- Techno : yt-dlp + ffprobe
- Runner : GitHub Actions (ubuntu-latest)

## Tests de validation (T1)
| # | Entre | Attendu | Statut |
|---|-------|---------|--------|
| T1.1 | URL YouTube (8min) | video_source.mp4 + manifest | EN ATTENTE CODE |
| T1.2 | Fichier local upload | video_source.mp4 + manifest | EN ATTENTE CODE |
