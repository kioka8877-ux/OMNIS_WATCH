# F02 — PREVIEW
## Le Filet de Securite

## Role
Apercu temps reel de la video avec tous les effets (texte, zooms, tracking, couleurs, SFX) avant de declencher le rendu GitHub Actions.

## Pourquoi
On ne declenche pas un rendu GitHub Actions (qui coute des minutes) sans etre surs a 100% du resultat. Le preview montre **exactement** ce que F03A produira.

## Entree
- `codex.json` (depuis F02B)
- `video_coupee.mp4` (depuis F01)
- `sfx/` (depuis SHARED/IN/sfx/)

## Action
1. Le sandbox copie codex.json + video_coupee.mp4 + SFX dans public/
2. Le sandbox lance : `npm install && npm run build`
3. Le sandbox exporte le build HTML → l'operateur ouvre dans son navigateur
4. L'operateur voit la video EN TEMPS REEL avec tous les effets
5. Il clique Play → la video joue (texte anime, zooms, couleurs, SFX)
6. Il valide → on trigger F03A sur GitHub Actions
7. Il n'est pas content → on ajuste le codex.json, on rebuild, on re-export

## Sortie
- Build HTML statique (artifact exportable)
- Validation operateur (Gate 2)

## Techno
- `@remotion/player` — rend les compositions React en temps reel dans le navigateur
- Vite + React
- Composants **identiques** a F03A (meme code, meme rendu)

## Runner
Sandbox (build + export HTML)

## Composants partages avec F03A
Les composants dans `src/preview/` sont des copies exactes de `F03A/CODEBASE/src/components/`.
Ce que tu vois dans le preview = ce que GitHub Actions rendra. Zero ecart.

| Composant | Role |
|-----------|------|
| OmniComposition.jsx | Composition principale (lit codex.json) |
| VideoLayer.jsx | Affiche la video F01 |
| TextOverlay.jsx | Texte anime (typewriter, fade, slide, pop) |
| ZoomLayer.jsx | Interpolation des zoom keyframes |
| ColorGrade.jsx | Filtres CSS (presets colorimetrie) |
| Enhance4K.jsx | Sharpen/contrast via CSS filter |
