# D-F05 PREVIEW - Tracking

## Statut
- **Statut :** À COPIER depuis gamma
- **Version :** delta (from gamma/F02_PREVIEW)
- **Priorité :** Étape 3-4

## Rôle
Interface React pour prévisualiser et configurer les presets, sous-titres et SFX.
Génère le codex.json qui sera utilisé par D-F06 RENDER.

## ⚠️ IMPORTANT - Mode manuel
Cette frégate est **manuelle**. Tu ouvres F02_PREVIEW sur GitHub Pages,
tu configures les paramètres, et tu télécharges le codex.json.

## Flow
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

## Entrées (dans l'interface web)
- Clip vidéo (clip_001.mp4 de D-F03)
- Timing JSON (timing_001.json de D-F04)

## Sorties (après téléchargement manuel)
- `codex_001.json` : configuration pour le clip 1
- `codex_002.json` : configuration pour le clip 2
- etc.

## Codex.json format

```json
{
  "version": "2.0",
  "emotion_mode": "WHOLESOME",
  "video": {
    "source": "clip_001.mp4",
    "fps": 30,
    "total_frames": 300,
    "width": 1080,
    "height": 1920
  },
  "text_overlays": [
    {
      "id": "txt_00",
      "content": "Hello",
      "start_frame": 0,
      "end_frame": 15,
      "animation": "word_by_word"
    }
  ],
  "sfx_timeline": [
    {
      "frame": 0,
      "type": "whoosh",
      "volume": 0.8
    }
  ]
}
```

## Code
- Source : `gamma/F02_PREVIEW/` (copié ici)
- Techno : React, Vite, JavaScript
- Deploy : GitHub Pages via `d05_preview.yml`

## Todo
- [x] Créer structure dossiers
- [ ] Copier gamma/F02_PREVIEW → delta/F05_PREVIEW
- [ ] Créer `d05_preview.yml` (deploy to GitHub Pages)
- [ ] Configurer GitHub Pages pour F05_PREVIEW
- [ ] Tester le workflow de déploiement
