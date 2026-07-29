# F02 PREVIEW — Tracking

## Etat
- **Statut :** CODE COMPLETE
- **Version :** alpha
- **Date de completion :** 2026-07-14

## Historique
| Date | Action | Resultat |
|------|--------|----------|
| 2026-07-14 | Structure creee | En attente de developpement |
| 2026-07-14 | App.jsx + main.jsx developpes | Player @remotion/player integre |
| 2026-07-14 | OmniComposition.jsx copie | Composant identique a F03A |
| 2026-07-14 | App.jsx rewrite | Chargement dynamique codex + video via fetch |

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
| App.jsx | Charge codex + video dynamiquement, rend <Player> | CODE COMPLETE |
| preview/OmniComposition.jsx | Copie exacte de F03A | CODE COMPLETE |

## Fonctionnalites
- [x] Chargement dynamique du codex.json (fetch)
- [x] Chargement dynamique de la video
- [x] Cadre telephone 9:16
- [x] Bouton "Valider et rendre"
- [x] Affichage infos codex (textes, zooms, SFX, duree)
- [x] Liste des textes (debug)
- [x] Ecran de chargement
- [x] Ecran d'erreur avec instructions
