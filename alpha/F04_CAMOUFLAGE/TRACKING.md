# F04 CAMOUFLAGE — Tracking

## Etat
- **Statut :** CODE COMPLETE
- **Version :** alpha
- **Date de completion :** 2026-07-14

## Historique
| Date | Action | Resultat |
|------|--------|----------|
| 2026-07-14 | Structure creee | En attente de developpement |
| 2026-07-14 | omnis_f04.py developpe | Adapte de crs_f04_helbrecht.py (CRUSADER) |

## Tests
| # | Date | Entree | Sortie | QA | Statut |
|---|------|--------|--------|-----|--------|
| — | — | — | — | — | EN ATTENTE GH ACTIONS |

## Notes techniques
- Script : omnis_f04.py (FONCTIONNEL)
- Runner : GitHub Actions (CPU gratuit)
- Techno : FFmpeg (libx264 CRF18, AAC 192k, loudnorm -14 LUFS)
- Entree : video_complete.mp4
- Sortie : youtube_final.mp4 + rapport_f04.html

## Fonctionnalites
- [x] Re-encode H264 CRF18 (qualite elevee)
- [x] AAC 192k
- [x] Loudnorm -14 LUFS (standard YouTube)
- [x] Wipe metadonnees (-map_metadata -1)
- [x] Neutralisation tag encoder (-metadata encoder=)
- [x] +faststart pour streaming
- [x] Rapport HTML de QA (avant/apres)
- [x] Detection tags suspects (remotion, ffmpeg, lavf, etc.)

## Heritage CRUSADER
- Source : gamma/F04_HELBRECHT/CODEBASE/crs_f04_helbrecht.py
- Fonctionnalites reprises : re-encode, loudnorm, wipe encoder tag, QA HTML
- Difference : entree video_complete.mp4 (avec SFX) au lieu de short_render.mp4
- Simplifie : pas de chapters YouTube (a ajouter plus tard si besoin)
