# F04 CAMOUFLAGE — Tracking

## Etat
- **Statut :** EN DEVELOPPEMENT (heritage CRUSADER)
- **Version :** alpha
- **Date d'initialisation :** 2026-07-14

## Historique
| Date | Action | Resultat |
|------|--------|----------|
| 2026-07-14 | Structure creee | En attente d'adaptation depuis CRUSADER |

## Tests
| # | Date | Entree | Sortie | QA | Statut |
|---|------|--------|--------|-----|--------|
| — | — | — | — | — | EN ATTENTE |

## Notes techniques
- Script : omnis_f04.py (a adapter depuis crs_f04_helbrecht.py de CRUSADER)
- Runner : GitHub Actions (CPU gratuit)
- Techno : FFmpeg (CRF18, H264/AAC, loudnorm -14 LUFS)
- Entree : video_complete.mp4
- Sortie : youtube_final.mp4 + rapport_f04.html

## Heritage CRUSADER
- Source : gamma/F04_HELBRECHT/CODEBASE/crs_f04_helbrecht.py
- Fonctionnalites reprises : re-encode, loudnorm, wipe encoder tag, QA HTML
- Adaptation necessaire : entree video_complete.mp4 au lieu de short_render.mp4
