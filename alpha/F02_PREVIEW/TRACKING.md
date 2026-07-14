# F02 PREVIEW — Tracking

## Etat
- **Statut :** CODE COMPLETE (placeholder)
- **Version :** alpha
- **Date de completion :** 2026-07-14

## Historique
| Date | Action | Resultat |
|------|--------|----------|
| 2026-07-14 | Structure creee | En attente de developpement |
| 2026-07-14 | App.jsx + main.jsx developpes | Player @remotion/player integre |
| 2026-07-14 | OmniComposition.jsx copie | Composant identique a F03A |

## Tests
| # | Date | Codex | Build | Preview | Statut |
|---|------|-------|-------|---------|--------|
| — | — | — | — | — | EN ATTENTE (npm install + build) |

## Notes techniques
- Techno : @remotion/player + Vite + React
- Runner : Sandbox (build + export HTML)
- Composants : copies exactes de F03A/CODEBASE/src/components/
- Entree : codex.json + video_coupee.mp4 + sfx/
- Sortie : Build HTML (artifact exportable)

## Composants
| Fichier | Role | Statut |
|---------|------|--------|
| main.jsx | Entry point React | CODE COMPLETE |
| App.jsx | Charge codex + video, rend <Player> | PLACEHOLDER (a connecter au runtime) |
| preview/OmniComposition.jsx | Copie exacte de F03A | CODE COMPLETE |

## A developper
- [ ] Chargement dynamique du codex.json (fetch)
- [ ] Chargement dynamique de la video
- [ ] Bouton "Valider et rendre" → trigger GitHub Actions
- [ ] SFX playback dans le preview
