# F03A — REMOTION
## L'Usine a Effets

## Role
Rendu visuel de la video finale (sans son). Lit le codex.json et dessine l'image frame par frame.

## Entree
- `codex.json` (depuis F02B)
- `video_coupee.mp4` (depuis F01)
- `tracking_data.json` (depuis F02A, reference dans le codex)

## Action
1. Remotion lit le codex.json
2. La video F01 est lue via `<Video>`
3. Les textes apparaissent selon leur timing (start_frame / end_frame)
4. Les animations jouent (typewriter, fade, slide, pop)
5. Les zooms interpolent selon les keyframes
6. Le tracking suit les coordonnees de la cible
7. La colorimetrie s'applique via CSS filters
8. L'enhance 4K s'applique (sharpen, contrast)
9. Rendu en .mp4 (sans piste audio)

## Sortie
- `video_visuelle.mp4` — video visuellement finale, sans son

## Ce que F03A NE fait PAS
- ❌ Son (→ F03B Mixer)
- ❌ Nettoyage metadonnees (→ F04 Camouflage)

## Techno
- Remotion (React/Node.js)
- Docker custom `omnis-remotion:latest`
- GitHub Actions (CPU gratuit, rendu en 2-3 min pour un Short)

## Runner
GitHub Actions (Docker custom)

## Composants
| Composant | Role |
|-----------|------|
| OmniComposition.jsx | Composition principale (lit codex.json) |
| VideoLayer.jsx | Affiche la video F01 via `<Video>` |
| TextOverlay.jsx | Texte anime (typewriter, fade, slide, pop) |
| ZoomLayer.jsx | Interpolation des zoom keyframes |
| ColorGrade.jsx | Filtres CSS (presets colorimetrie) |
| Enhance4K.jsx | Sharpen/contrast via CSS filter |

## Heritage
Inspire de F03_SIGISMUND (CRUSADER) mais fondamentalement different :
- CRUSADER : images statiques + sous-titres voix off
- OMNIS-WATCH : video en mouvement + texte narratif + zooms + tracking + couleurs
