# F02A VISION — Tracking

## Etat
- **Statut :** CODE COMPLETE — TESTS PENDANT
- **Version :** alpha
- **Date de completion :** 2026-07-14

## Historique
| Date | Action | Resultat |
|------|--------|----------|
| 2026-07-14 | Structure creee | En attente de developpement |
| 2026-07-14 | omnis_f02a_track.py developpe | MediaPipe face/hand/object tracking |
| 2026-07-14 | omnis_f02a_vision.py developpe | OpenRouter Vision description |

## Tests
| # | Date | Script | Entree | Sortie | Statut |
|---|------|--------|--------|--------|--------|
| — | — | track.py | — | — | EN ATTENTE GH ACTIONS |
| — | — | vision.py | — | — | EN ATTENTE (cle OpenRouter) |

## Notes techniques
### omnis_f02a_track.py
- MediaPipe Face Detection (model_selection=1, min_confidence=0.5)
- MediaPipe Hand Tracking (max_num_hands=1)
- MediaPipe Object Detection (model_selection=0, COCO labels)
- Coordonnees normalisees [0-1]
- Lissage par moyenne mobile ponderee par confiance (fenetre=5)
- Fallback: derniere position connue si perte de detection
- Runner: GitHub Actions (CPU)

### omnis_f02a_vision.py
- Extraction de 4 frames cles via FFmpeg (debut, 1/3, 2/3, fin)
- Encodage base64 des frames
- Envoi a OpenRouter Vision (modeles gratuits en fallback)
- Modeles: llama-3.2-11b-vision, qwen-2-vl-7b, gemini-2.0-flash-exp
- Prompt: description factuelle, 3-5 phrases, anglais
- Runner: Sandbox (API call)

## Cibles MediaPipe supportees
| Cible | Modele | Statut |
|-------|--------|--------|
| face | Face Detection | CODE COMPLETE |
| hand | Hand Tracking | CODE COMPLETE |
| dog | Object Detection (COCO) | CODE COMPLETE |
| cat | Object Detection (COCO) | CODE COMPLETE |
| person | Object Detection (COCO) | CODE COMPLETE |

## Modeles OpenRouter testes
| Modele | Type | Gratuit | Statut |
|--------|------|---------|--------|
| llama-3.2-11b-vision-instruct:free | Vision | Oui | NON TESTE |
| qwen-2-vl-7b-instruct:free | Vision | Oui | NON TESTE |
| gemini-2.0-flash-exp:free | Vision | Oui | NON TESTE |
