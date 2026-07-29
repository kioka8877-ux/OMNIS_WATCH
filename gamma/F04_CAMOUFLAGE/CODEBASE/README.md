# F04 — CAMOUFLAGE
## Nettoyage de Surface

## Role
Nettoyage de base : wipe des metadonnees, normalisation du volume pour YouTube.

## Entree
- `video_complete.mp4` (depuis F03B OUT/)

## Action
1. Re-encode avec FFmpeg (CRF18, H264/AAC)
2. Loudnorm -14 LUFS (standard YouTube)
3. `-metadata encoder=` pour neutraliser le tag Lavf
4. +faststart pour streaming
5. Rapport de QA

## Sortie
- `youtube_final.mp4` — video prete pour YouTube (metadonnees propres, son normalise)

## Techno
- FFmpeg (GitHub Actions)

## Runner
GitHub Actions (CPU gratuit)

## Heritage
**Adapte directement de F04_HELBRECHT (CRUSADER).**
Le script `crs_f04_helbrecht.py` de CRUSADER est la base de `omnis_f04.py`.
Fonctionnalites reprises :
- Re-encode CRF18 H264/AAC
- Loudnorm -14 LUFS
- Neutralisation du tag encoder Lavf
- Rapport HTML de QA
- Chapters YouTube (si applicable)

## Difference avec CRUSADER
- Entree : `video_complete.mp4` (avec SFX) au lieu de `short_render.mp4`
- Pas de timing.json (les metadonnees viennent du codex.json si besoin)
