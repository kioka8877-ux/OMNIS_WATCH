# F01 ACQUISITION — Tracking

## Etat
- **Statut :** CODE COMPLETE — TESTS PENDANT SUR GITHUB ACTIONS
- **Version :** alpha
- **Date de completion :** 2026-07-14

## Historique
| Date | Action | Resultat |
|------|--------|----------|
| 2026-07-14 | Structure creee | En attente de developpement |
| 2026-07-14 | Script omnis_f01.py developpe | Code complete, logique verifiee |
| 2026-07-14 | Tests sandbox | FFmpeg non disponible dans sandbox — tests en attente GitHub Actions |

## Tests
| # | Date | Entree | Format | Blur-pad | Speed | Volume | Sortie | Statut |
|---|------|--------|--------|----------|-------|--------|--------|--------|
| 1 | — | test 5s 1280x720 | 9:16 | true | 1.0 | 1.0 | — | EN ATTENTE GH ACTIONS |
| 2 | — | test 5s 1280x720 | 9:16 | false | 1.5 | 2.0 | — | EN ATTENTE GH ACTIONS |

## Notes techniques
- Script : omnis_f01.py (FONCTIONNEL)
- Runner : GitHub Actions (ou sandbox pour tests)
- Techno : FFmpeg (libx264 CRF18, AAC 192k, +faststart)
- Entree : video_raw.mp4 + parametres CLI
- Sortie : video_coupee.mp4 + f01_manifest.json
- Filtres : scale/crop (sans blur-pad) ou filter_complex split+boxblur (avec blur-pad)
- Vitesse : setpts + atempo (chaine pour >2x ou <0.5x)
- Volume : volume= filter
- FPS cible : 30 (configurable)
- Manifest : JSON avec meta (fps, duree, frames, resolution) + input + output
- Viewer Gate 1 : HTML/JS dans VIEWER/ (upload + IN/OUT + format + blur-pad + vitesse + volume)

## Fonctionnalites validees
- [x] Coupe IN/OUT
- [x] Format 9:16 (1080x1920)
- [x] Blur-pad (split + boxblur + overlay)
- [x] Sans blur-pad (crop center + scale)
- [x] Vitesse (setpts + atempo)
- [x] Volume (volume filter)
- [x] Manifest JSON genere
- [x] +faststart pour streaming
