# F01 — ACQUISITION

## Role
Decoupe et formatage de la video brute. Point.

## Entree
- `video_raw.mp4` (depuis SHARED/IN/)
- JSON de configuration (IN, OUT, format, blur_pad, vitesse, volume)

## Action
1. FFmpeg coupe la video aux timestamps IN/OUT
2. Redimensionne au format demande (9:16, 16:9, 1:1)
3. Applique le blur-pad si demande
4. Applique la vitesse (setpts + atempo)
5. Applique le volume (volume=...)

## Sortie
- `video_coupee.mp4` — video propre, coupee, au bon format, bonne vitesse, bon volume
- `f01_manifest.json` — metadonnees (duree, fps, frames, resolution)

## Ce que F01 NE fait PAS
- ❌ Texte a l'ecran (→ F03A Remotion)
- ❌ Tracking (→ F02A Vision)
- ❌ SFX (→ F03B Mixer)
- ❌ Colorimetrie (→ F03A Remotion)
- ❌ Nettoyage metadonnees (→ F04 Camouflage)

## Techno
- FFmpeg (GitHub Actions)

## Runner
GitHub Actions (CPU gratuit)

## Heritage
Adapte du script `clip.py` de la V1 OMNIS-WATCH (epure : coupe + format + vitesse + volume uniquement).
