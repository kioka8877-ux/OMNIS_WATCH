# D-F05 PREVIEW - Tracking

## Statut
- **Statut :** COPIÉ depuis gamma
- **Version :** delta (from gamma/F02_PREVIEW)
- **Priorité :** Étape 3-4

## Rôle
Interface React pour prévisualiser et configurer les presets, sous-titres et SFX.
Génère le codex.json qui sera utilisé par D-F06 RENDER.

## ⚠️ IMPORTANT - Mode manuel
Cette frégate est **manuelle**. Tu ouvres F05_PREVIEW sur GitHub Pages,
tu configures les paramètres, et tu télécharges le codex.json.

## Flux
```
D-F04 (timing_001.json, timing_002.json...)
    ↓
TU ouvres F05_PREVIEW sur GitHub Pages
TU uploades le clip.mp4 + timing.json
TU configures : preset, subtitles, SFX
TU télécharges codex_001.json, codex_002.json...
    ↓
TU places les codex.json dans le sandbox
DELTA orchestrator les utilise pour D-F06
```

## Structure (copiée de gamma/F02_PREVIEW)
```
delta/F05_PREVIEW/
├── index.html
├── package.json
├── vite.config.js
├── src/
│   ├── main.jsx
│   ├── App.jsx
│   └── preview/
│       ├── OmniComposition.jsx
│       └── BloomText.jsx
├── public/
└── IN/, OUT/
```

## Codex.json format
```json
{
  "version": "2.0",
  "emotion_mode": "WHOLESOME",
  "video": {...},
  "text_overlays": [...],
  "sfx_timeline": [...]
}
```

## Todo
- [x] Créer structure dossiers
- [x] Copier gamma/F02_PREVIEW → delta/F05_PREVIEW
- [ ] Créer `d05_preview.yml` (deploy to GitHub Pages)
- [ ] Configurer GitHub Pages pour F05_PREVIEW
- [ ] Tester le workflow de déploiement
