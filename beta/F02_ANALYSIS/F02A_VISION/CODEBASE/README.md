# F02A — VISION
## Les Yeux de la Flotte

## Role
Analyse visuelle de la video coupee. Produit une description factuelle et les donnees de tracking.

## Entree
- `video_coupee.mp4` (depuis F01 OUT/)
- `f01_manifest.json` (metadonnees : fps, duree, frames)

## Phase 1 : Description Narrative (OpenRouter Vision)
1. FFmpeg extrait 3-4 frames cles de la video
2. Les frames sont envoyees a un modele vision gratuit d'OpenRouter
3. Le modele decrit l'action de facon factuelle (sans inventer d'histoire)
4. Sortie : `narrative.txt`

## Phase 2 : Tracking de Cible (MediaPipe)
1. MediaPipe analyse chaque frame de la video
2. Detection de la cible : visage, main, chien, tete, objet
3. Centre de la bounding box en coordonnees normalisees [0-1]
4. Sortie : `tracking_data.json`

## Sortie
- `narrative.txt` — description factuelle de l'action
- `tracking_data.json` — coordonnees de la cible frame par frame

## Ce que F02A NE fait PAS
- ❌ Invente une histoire (→ F02B Oracle)
- ❌ Genere du texte d'ecran (→ F02B Oracle)
- ❌ Decide des zooms ou SFX (→ F02B Oracle)

## Techno
- OpenRouter Vision (modeles gratuits : Llama-3.2-11B-Vision, Qwen-VL)
- MediaPipe (Face Detection, Hand Tracking, Object Detection)
- FFmpeg (extraction de frames)

## Runner
- Description : Sandbox Oracle (via API OpenRouter)
- Tracking : GitHub Actions (MediaPipe sur CPU)

## Cibles supportees
| Cible | Modele MediaPipe |
|-------|-----------------|
| Visage / Tete | Face Detection / Face Mesh |
| Main | Hand Tracking |
| Chien / Objet | Object Detection (EfficientDet-Lite0, classe COCO "dog") |
