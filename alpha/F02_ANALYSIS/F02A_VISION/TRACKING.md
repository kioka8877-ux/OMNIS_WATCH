# F02A VISION — Tracking

## Etat
- **Statut :** EN DEVELOPPEMENT
- **Version :** alpha
- **Date d'initialisation :** 2026-07-14

## Historique
| Date | Action | Resultat |
|------|--------|----------|
| 2026-07-14 | Structure creee | En attente de developpement |

## Tests
| # | Date | Entree | Sortie | Statut |
|---|------|--------|--------|--------|
| — | — | — | — | EN ATTENTE |

## Notes techniques
- Scripts : omnis_f02a_vision.py (OpenRouter) + omnis_f02a_track.py (MediaPipe)
- Runner vision : Sandbox (API OpenRouter)
- Runner tracking : GitHub Actions (MediaPipe CPU)
- Entree : video_coupee.mp4 + f01_manifest.json
- Sortie : narrative.txt + tracking_data.json

## Modeles OpenRouter testes
| Modele | Type | Gratuit | Statut |
|--------|------|---------|--------|
| — | — | — | NON TESTE |

## Cibles MediaPipe
| Cible | Modele | Statut |
|-------|--------|--------|
| Visage | Face Detection | NON TESTE |
| Main | Hand Tracking | NON TESTE |
| Chien | Object Detection | NON TESTE |
