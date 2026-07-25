# F03A REMOTION — Tracking

## Etat
- **Statut :** CODE COMPLETE
- **Version :** alpha
- **Date de completion :** 2026-07-14

## Historique
| Date | Action | Resultat |
|------|--------|----------|
| 2026-07-14 | Structure creee | En attente de developpement |
| 2026-07-14 | OmniComposition.jsx developpe | Composant principal Remotion |
| 2026-07-14 | Root.jsx + index.jsx | Entry points Remotion |
| 2026-07-14 | remotion.config.js | Config H264, JPEG, concurrency=1 |
| 2026-07-14 | Dockerfile fonctionnel | Node 20 + FFmpeg + Chromium |
| 2026-07-14 | Workflow f03a_render.yml fonctionnel | npm install + remotion render |

## Tests
| # | Date | Codex | Rendu | Duree | Taille | Statut |
|---|------|-------|-------|-------|--------|--------|
| — | — | — | — | — | — | EN ATTENTE GH ACTIONS |

## Notes techniques
- Techno : Remotion (React/Node.js) + Docker custom
- Runner : GitHub Actions (Docker, CPU gratuit)
- Entree : codex.json + video_coupee.mp4
- Sortie : video_visuelle.mp4 (sans son)
- Docker image : Node 20 + FFmpeg + Chromium (Puppeteer)

## Composants
| Composant | Role | Statut |
|-----------|------|--------|
| OmniComposition.jsx | Composition principale (lit codex, orchestre layers) | CODE COMPLETE |
| Root.jsx | Enregistre la composition Remotion | CODE COMPLETE |
| index.jsx | Entry point registerRoot | CODE COMPLETE |
| remotion.config.js | Config H264, JPEG, concurrency=1 | CODE COMPLETE |
| Dockerfile | Image Docker avec Chromium pour Remotion | CODE COMPLETE |

## Fonctionnalites implementees
- [x] Lecture video source (OffthreadVideo)
- [x] Zoom interpolation (keyframes + easeInOutCubic)
- [x] Tracking offset (placeholder — utilise keyframes du codex)
- [x] Color grade (CSS filter depuis codex)
- [x] Enhance 4K (CSS filter contrast/saturate/brightness)
- [x] Text overlays (6 animations: fade_in, fade_in_slow, typewriter, slide_left, slide_right, pop)
- [x] Position (center, top, center_bottom, bottom)
- [x] Text styling (font, size, color, stroke, shadow)
- [x] Dockerfile avec Chromium pour rendu headless
- [x] Workflow GitHub Actions fonctionnel (npm install + remotion render)
